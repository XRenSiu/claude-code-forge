#!/usr/bin/env bash
# pr-poll.sh — blocking PR activity watcher + compiled loop governance for the sdlc review-loop skill.
# Adapted from vana-builder/.claude/skills/pr-review-loop/scripts/pr-poll.sh (v0.4.0); state dir moved
# to .sdlc/pr-watch so it sits next to the lifecycle state.
#
# 设计意图：
#   1. 把"轮询"下沉到脚本内部，模型只在有增量时被唤醒（等待期间零 token）。
#   2. 把循环预算（轮次 / 空轮 / 线程 strike）与终止谓词编译进脚本——预算记账由环境强制，
#      不依赖模型自觉（A′-1/2：跳门、错误终止）。
#
# Usage:
#   pr-poll.sh watch    <pr> [interval_sec] [max_wait_sec]  # 阻塞直到有事发生
#   pr-poll.sh snapshot <pr>                                # 一次性检查，不阻塞
#   pr-poll.sh threads  <pr>                                # review 线程及 resolved 状态
#   pr-poll.sh resolve  <pr> <thread_id>                    # 收束线程（仅限已修复+已回帖的）
#   pr-poll.sh round    <pr>                                # 轮次 += 1（每批修复+push+回帖后调用）
#   pr-poll.sh strike   <pr> <thread_id>                    # 线程往返 += 1
#   pr-poll.sh done     <pr>                                # 编译态终止谓词
#
# 预算（环境变量覆盖，不改脚本）：
#   MAX_ROUNDS=10  MAX_EMPTY_WATCHES=4  MAX_THREAD_STRIKES=3  STATE_DIR=.sdlc/pr-watch
#
# Exit codes:
#   0  = watch/snapshot: 有新活动(stdout delta JSON) | done: 已收敛(APPROVED ∧ 未解决线程=0 ∧ checks 绿)
#   10 = PR 终态 merged/closed
#   20 = watch/snapshot: 本轮无活动 | done: 尚未收敛(stdout 说明缺哪条)
#   21 = watch: 连续空轮询达 MAX_EMPTY_WATCHES(计数已自动清零)
#   22 = resolve: 收束失败但非致命(无写权限/线程已删/id 过期)
#   30 = round: 全局轮次预算耗尽 —— 硬停并汇报
#   31 = strike: 该线程达 MAX_THREAD_STRIKES —— 冻结该线程，交还人类
#   1  = 真实错误 (gh 未登录 / 网络 / 权限 / jq 缺失)
#
# 依赖: jq；watch/snapshot/threads/resolve/done 另需 gh(已 auth) 且在目标 git 仓库内。
# round/strike 只操作本地计数文件，不触网。

set -euo pipefail

CMD="${1:?usage: pr-poll.sh watch|snapshot|threads|resolve|round|strike|done <pr-number>}"
PR="${2:?PR number required}"
INTERVAL="${3:-45}"
MAX_WAIT="${4:-480}"

MAX_ROUNDS="${MAX_ROUNDS:-10}"
MAX_EMPTY_WATCHES="${MAX_EMPTY_WATCHES:-4}"
MAX_THREAD_STRIKES="${MAX_THREAD_STRIKES:-3}"

STATE_DIR="${STATE_DIR:-.sdlc/pr-watch}"
mkdir -p "$STATE_DIR"
WM_FILE="$STATE_DIR/pr-$PR.watermark"
CNT_FILE="$STATE_DIR/pr-$PR.counters.json"

command -v jq >/dev/null 2>&1 || { echo "pr-poll: jq not found" >&2; exit 1; }

# 存在性不等于可用：半截文件照样通过 [[ -f ]]；按「能不能解析」判断，不能就重置。
counters_init() {
  if [[ ! -s "$CNT_FILE" ]] || ! jq -e . "$CNT_FILE" >/dev/null 2>&1; then
    write_counters '{"rounds":0,"empty_watches":0,"strikes":{}}'
  fi
}

# 先写临时文件再 mv——同一文件系统内 mv 是原子的。
write_counters() {
  printf '%s\n' "$1" > "$CNT_FILE.tmp" && mv "$CNT_FILE.tmp" "$CNT_FILE"
}

resolve_repo() {
  REPO_JSON="$(gh repo view --json owner,name)"
  OWNER="$(jq -r .owner.login <<<"$REPO_JSON")"
  REPO="$(jq -r .name <<<"$REPO_JSON")"
  SELF="$(gh api user -q .login)"
}

init_watermark() {
  if [[ ! -f "$WM_FILE" ]]; then
    gh pr view "$PR" --json createdAt -q .createdAt > "$WM_FILE"
  fi
}

pr_state() {
  gh pr view "$PR" --json state,reviewDecision,mergedAt,closedAt,isDraft,url
}

fetch_delta() {
  local since reviews inline issue
  since="$(cat "$WM_FILE")"
  # 三个评论通道必须都查：PR review、行内 review comment、普通 issue comment。
  reviews="$(gh api "repos/$OWNER/$REPO/pulls/$PR/reviews" --paginate \
    | jq --arg s "$since" --arg me "$SELF" \
      '[.[] | select(.submitted_at > $s and .user.login != $me and .state != "PENDING")
        | {id, author: .user.login, state, body, submitted_at}]')"
  inline="$(gh api "repos/$OWNER/$REPO/pulls/$PR/comments" --paginate \
    | jq --arg s "$since" --arg me "$SELF" \
      '[.[] | select(.created_at > $s and .user.login != $me)
        | {id, author: .user.login, path, line: (.line // .original_line),
           body, created_at, in_reply_to_id, diff_hunk}]')"
  issue="$(gh api "repos/$OWNER/$REPO/issues/$PR/comments" --paginate \
    | jq --arg s "$since" --arg me "$SELF" \
      '[.[] | select(.created_at > $s and .user.login != $me)
        | {id, author: .user.login, body, created_at}]')"
  jq -n --argjson r "$reviews" --argjson i "$inline" --argjson c "$issue" \
    '{event: "activity", reviews: $r, inline_comments: $i, issue_comments: $c,
      count: (($r|length) + ($i|length) + ($c|length))}'
}

advance_watermark() {
  # 水位线 = 本轮取到评论的最大时间戳，而不是本地 now（避免竞态与时钟偏差）。
  local delta="$1" maxts
  maxts="$(jq -r '[.reviews[].submitted_at, .inline_comments[].created_at,
                   .issue_comments[].created_at] | max // empty' <<<"$delta")"
  [[ -n "$maxts" ]] && echo "$maxts" > "$WM_FILE"
}

check_once() {
  local st state delta
  st="$(pr_state 2>/dev/null || true)"
  state="$(jq -r .state <<<"$st" 2>/dev/null || true)"
  # 终态必须白名单判断：网络/认证失败时 state 为空，"!= OPEN" 会把临时错误误报成已关闭。
  if [[ "$state" == "MERGED" || "$state" == "CLOSED" ]]; then
    jq -n --argjson s "$st" '{event: "terminal", pr: $s}'
    return 10
  fi
  if [[ "$state" != "OPEN" ]]; then
    echo "pr-poll: failed to fetch PR state (network/auth?)" >&2
    return 1
  fi
  delta="$(fetch_delta)"
  if [[ "$(jq -r .count <<<"$delta")" -gt 0 ]]; then
    advance_watermark "$delta"
    echo "$delta"
    return 0
  fi
  return 20
}

threads_json() {
  # REST 不暴露线程 resolved 状态，必须走 GraphQL
  gh api graphql \
    -f query='
      query($owner:String!, $repo:String!, $pr:Int!) {
        repository(owner:$owner, name:$repo) {
          pullRequest(number:$pr) {
            reviewThreads(first:100) {
              pageInfo { hasNextPage }
              nodes {
                id isResolved isOutdated path line
                comments(first:100) { nodes { author { login } body createdAt } }
              }
            }
          }
        }
      }' \
    -F owner="$OWNER" -F repo="$REPO" -F pr="$PR" \
  | jq '{
      threads: [.data.repository.pullRequest.reviewThreads.nodes[]
        | {id, isResolved, isOutdated, path, line,
           opened_by: .comments.nodes[0].author.login,
           first_comment: .comments.nodes[0].body,
           reply_count: ((.comments.nodes | length) - 1)}],
      unresolved_count: ([.data.repository.pullRequest.reviewThreads.nodes[]
        | select(.isResolved | not)] | length),
      truncated: .data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage
    }' \
  | jq 'if .truncated
        then del(.truncated) | .warning = "超过 100 条 review 线程，本次仅取前 100 条；未列出的线程不会被本轮处理"
        else del(.truncated) end'
}

case "$CMD" in
  snapshot)
    resolve_repo
    init_watermark
    check_once
    ;;

  watch)
    resolve_repo
    init_watermark
    counters_init
    elapsed=0
    errors=0
    while true; do
      set +e
      out="$(check_once)"; rc=$?
      set -e
      if [[ $rc -eq 0 || $rc -eq 10 ]]; then
        tmp="$(jq '.empty_watches = 0' "$CNT_FILE")" && write_counters "$tmp"
        echo "$out"
        exit "$rc"
      fi
      if [[ $rc -ne 20 ]]; then
        errors=$(( errors + 1 ))
        if (( errors >= 3 )); then
          echo "pr-poll: 3 consecutive fetch failures, giving up" >&2
          exit 1
        fi
        # 取数失败 ≠ 无活动：绝不落进空轮记账。
      else
        errors=0
        if (( elapsed >= MAX_WAIT )); then
          tmp="$(jq '.empty_watches += 1' "$CNT_FILE")" && write_counters "$tmp"
          ew="$(jq -r .empty_watches "$CNT_FILE")"
          if (( ew >= MAX_EMPTY_WATCHES )); then
            tmp="$(jq '.empty_watches = 0' "$CNT_FILE")" && write_counters "$tmp"
            exit 21
          fi
          exit 20
        fi
      fi
      sleep "$INTERVAL"
      elapsed=$(( elapsed + INTERVAL ))
    done
    ;;

  threads)
    resolve_repo
    threads_json
    ;;

  resolve)
    # 该不该 resolve 是模型的判据（SKILL.md 安全边界）；脚本只保证用对原语、失败不掀翻循环。
    TID="${3:?thread id required: pr-poll.sh resolve <pr> <thread_id>}"
    ERR_FILE="$(mktemp)"
    trap 'rm -f "$ERR_FILE"' EXIT
    set +e
    out="$(gh api graphql -f query='
      mutation($tid: ID!) {
        resolveReviewThread(input: {threadId: $tid}) {
          thread { id isResolved }
        }
      }' -f tid="$TID" 2>"$ERR_FILE")"; rc=$?
    set -e
    if [[ $rc -eq 0 ]]; then
      # gh 退出 0 只说明 HTTP 通了；GraphQL 会把权限问题放进 errors 并把 data 置 null。
      resolved="$(jq -r '.data.resolveReviewThread.thread.isResolved // empty' <<<"$out" 2>/dev/null || true)"
      if [[ "$resolved" == "true" ]]; then
        jq -c '{resolved: .data.resolveReviewThread.thread.isResolved,
                thread:   .data.resolveReviewThread.thread.id}' <<<"$out"
        exit 0
      fi
      rc=1
    fi
    printf 'pr-poll: resolve failed for %s\n%s\n%s\n' "$TID" "$out" "$(cat "$ERR_FILE")" >&2
    jq -n --arg t "$TID" '{resolved: false, thread: $t, fatal: false}' || true
    exit 22
    ;;

  round)
    counters_init
    tmp="$(jq '.rounds += 1' "$CNT_FILE")" && write_counters "$tmp"
    r="$(jq -r .rounds "$CNT_FILE")"
    jq -n --argjson r "$r" --argjson m "$MAX_ROUNDS" '{rounds: $r, max: $m}'
    if (( r >= MAX_ROUNDS )); then exit 30; fi
    ;;

  strike)
    TID="${3:?thread id required: pr-poll.sh strike <pr> <thread_id>}"
    counters_init
    tmp="$(jq --arg t "$TID" '.strikes[$t] = ((.strikes[$t] // 0) + 1)' "$CNT_FILE")" \
      && write_counters "$tmp"
    s="$(jq -r --arg t "$TID" '.strikes[$t]' "$CNT_FILE")"
    jq -n --arg t "$TID" --argjson s "$s" --argjson m "$MAX_THREAD_STRIKES" \
      '{thread: $t, strikes: $s, max: $m}'
    if (( s >= MAX_THREAD_STRIKES )); then exit 31; fi
    ;;

  done)
    resolve_repo
    st="$(pr_state)"
    state="$(jq -r .state <<<"$st")"
    if [[ "$state" == "MERGED" || "$state" == "CLOSED" ]]; then
      jq -n --argjson s "$st" '{done: true, reason: "terminal", pr: $s}'
      exit 10
    fi
    decision="$(jq -r .reviewDecision <<<"$st")"
    threads_out="$(threads_json)"
    unresolved="$(jq -r .unresolved_count <<<"$threads_out")"
    truncated="$(jq -r 'has("warning")' <<<"$threads_out")"
    rollup="$(gh pr view "$PR" --json statusCheckRollup -q '.statusCheckRollup | length' 2>/dev/null || echo '?')"
    checks_green=false
    if [[ "$rollup" == "0" ]]; then
      checks_green=true
    elif gh pr checks "$PR" >/dev/null 2>&1; then
      checks_green=true
    fi
    if [[ "$decision" == "APPROVED" && "$unresolved" == "0" && "$checks_green" == "true" \
          && "$truncated" != "true" ]]; then
      jq -n '{done: true, reason: "approved_resolved_green"}'
      exit 0
    fi
    jq -n --arg d "$decision" --argjson u "$unresolved" --argjson g "$checks_green" \
          --argjson t "$truncated" \
      '{done: false, reviewDecision: $d, unresolved_count: $u, checks_green: $g}
       + (if $t then {threads_truncated: true,
                      note: "线程超过 100 条，unresolved_count 只是下界；收敛判定已因此拒绝返回 0"}
          else {} end)'
    exit 20
    ;;

  *)
    echo "unknown command: $CMD" >&2
    exit 1
    ;;
esac
