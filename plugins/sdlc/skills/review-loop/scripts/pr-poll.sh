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
#   pr-poll.sh done     <pr> [--solo]                       # 编译态终止谓词
#   pr-poll.sh selfreview <pr> <findings-file> [reviewer]   # 记一轮隔离预审（离线；单人仓库的必要条件）
#   pr-poll.sh predicate <pr> <decision> <unresolved> <checks_state> <checks_count> <truncated> [--solo]
#                                                           # 同一谓词，事实由参数给（离线；done 自己也走它）
#
# 预算（环境变量覆盖，不改脚本）：
#   MAX_ROUNDS=10  MAX_EMPTY_WATCHES=4  MAX_THREAD_STRIKES=3  STATE_DIR=.sdlc/pr-watch
#   SELF_REVIEW=1  单人仓库自审模式（等价于 done --solo）——**必须显式打开，不会自己变成默认**
#
# checks 三态（I-82）：`green`（有 check 且全绿）/ `none_configured`（仓库一个 check 都没配）/
#   `red`（有失败）/ `unknown`（取不到）。旧版把 none_configured 折成 checks_green=true，于是终止
#   谓词的第三项在无 CI 的仓库里恒真且无意义，下游还会把它渲染成"检查通过"。现在 JSON 里
#   `checks` 是三态字符串、`checks_count` 是数量、`checks_green` 只有真绿才为 true，
#   done 的 reason 区分 `approved_resolved_green` 与 `approved_resolved_no_checks`。
#
# 单人仓库（I-69）：GitHub 不允许 PR 作者 approve 自己的 PR，所以 reviewDecision 永远到不了
#   APPROVED，默认谓词在单维护者仓库里**永不收敛**。SELF_REVIEW=1 / --solo 换上一组**更严**的
#   替代条件：无 CHANGES_REQUESTED ∧ 未解决线程=0 ∧ checks 非红非未知 ∧ 线程未截断 ∧
#   至少一轮 selfreview 记录 ∧ 该轮 A 档存活=0 ∧ 该轮记的 head sha == 当前 HEAD（预审必须是对
#   正在收敛的这份代码做的——APPROVED 都不保证这一条）。
#
# Exit codes:
#   0  = watch/snapshot: 有新活动(stdout delta JSON) | done: 已收敛(见 reason)
#   10 = PR 终态 merged/closed
#   20 = watch/snapshot: 本轮无活动 | done: 尚未收敛(stdout 说明缺哪条)
#   21 = watch: 连续空轮询达 MAX_EMPTY_WATCHES(计数已自动清零)
#   22 = resolve: 收束失败但非致命(无写权限/线程已删/id 过期)
#   30 = round: 全局轮次预算耗尽 —— 硬停并汇报
#   31 = strike: 该线程达 MAX_THREAD_STRIKES —— 冻结该线程，交还人类
#   1  = 真实错误 (gh 未登录 / 网络 / 权限 / jq 缺失 / 用法错)
#
# 依赖: jq；watch/snapshot/threads/resolve/done 另需 gh(已 auth) 且在目标 git 仓库内。
# round/strike/selfreview/predicate 只操作本地计数文件，不触网。

set -euo pipefail

CMD="${1:?usage: pr-poll.sh watch|snapshot|threads|resolve|round|strike|selfreview|predicate|done <pr-number>}"
PR="${2:?PR number required}"
INTERVAL="${3:-45}"
MAX_WAIT="${4:-480}"

MAX_ROUNDS="${MAX_ROUNDS:-10}"
MAX_EMPTY_WATCHES="${MAX_EMPTY_WATCHES:-4}"
MAX_THREAD_STRIKES="${MAX_THREAD_STRIKES:-3}"

# 单人仓库自审模式必须被显式打开——默认永远是"要有第二个人 approve"（I-69）。
SOLO=0
if [[ "${SELF_REVIEW:-0}" == "1" ]]; then SOLO=1; fi
for _arg in "$@"; do
  if [[ "$_arg" == "--solo" ]]; then SOLO=1; fi
done

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

checks_state() {
  # 三态 + unknown（I-82）：空 rollup 是"一个 check 都没配"，不是"全绿"。把两者折成同一个布尔，
  # 终止谓词的第三项在无 CI 的仓库里就恒真，下游还会把它渲染成"检查通过"。
  local rollup
  rollup="$(gh pr view "$PR" --json statusCheckRollup -q '.statusCheckRollup | length' 2>/dev/null || echo '?')"
  if [[ -z "$rollup" || "$rollup" == "?" || "$rollup" == "null" ]]; then echo "unknown 0"; return; fi
  if [[ "$rollup" == "0" ]]; then echo "none_configured 0"; return; fi
  if gh pr checks "$PR" >/dev/null 2>&1; then echo "green $rollup"; else echo "red $rollup"; fi
}

# 终止谓词本体：事实进，判决出。done 取完事实调它；predicate 子命令由参数喂事实（离线可测）。
# 两条路径同一份逻辑——谓词是这个 skill 的承重件，不允许存在"只在联网时才跑到"的分支。
done_predicate() {
  local decision="$1" unresolved="$2" checks="$3" ccount="$4" truncated="$5" solo="$6"
  local missing="" checks_ok=false mode="review" reason=""
  local sr_rounds=0 sr_a=0 sr_sha="" cur_sha=""
  case "$checks" in
    green|none_configured) checks_ok=true ;;
  esac
  if [[ "$truncated" == "true" ]]; then missing="$missing threads_truncated"; fi
  if [[ "$unresolved" != "0" ]]; then missing="$missing unresolved_threads"; fi
  if [[ "$checks_ok" != "true" ]]; then missing="$missing checks_${checks}"; fi
  if (( solo )); then
    mode="solo"
    counters_init
    sr_rounds="$(jq -r '.self_review.rounds // 0' "$CNT_FILE")"
    sr_a="$(jq -r '.self_review.last.a_tier // 0' "$CNT_FILE")"
    sr_sha="$(jq -r '.self_review.last.head_sha // ""' "$CNT_FILE")"
    cur_sha="$(git rev-parse HEAD 2>/dev/null || echo "")"
    # APPROVED 拿不到（GitHub 禁止作者 approve 自己的 PR），换一组更严的：不是"没人反对"就算过。
    if [[ "$decision" == "CHANGES_REQUESTED" ]]; then missing="$missing changes_requested"; fi
    if (( sr_rounds < 1 )); then
      missing="$missing no_isolated_self_review_round"
    else
      if (( sr_a > 0 )); then missing="$missing self_review_a_tier_survivors"; fi
      # 预审必须是对**正在收敛的这份代码**做的：之后又推了提交，那一轮就不再承重。
      if [[ -n "$cur_sha" && "$sr_sha" != "$cur_sha" ]]; then missing="$missing self_review_stale"; fi
    fi
  else
    if [[ "$decision" != "APPROVED" ]]; then missing="$missing not_approved"; fi
  fi

  local base_json
  base_json="$(jq -n --arg mo "$mode" --arg d "$decision" --argjson u "$unresolved" \
        --arg c "$checks" --argjson cc "$ccount" --argjson t "$truncated" \
        --argjson srr "$sr_rounds" --argjson sra "$sr_a" --arg srs "$sr_sha" --arg cur "$cur_sha" \
    '{mode: $mo, reviewDecision: $d, unresolved_count: $u,
      checks: $c, checks_count: $cc, checks_green: ($c == "green")}
     + (if $c == "none_configured"
        then {checks_note: "no check is configured on this repository — the checks clause is vacuous, NOT green; never render it as \"checks passed\""}
        else {} end)
     + (if $c == "unknown" then {checks_note: "could not read statusCheckRollup — treated as not satisfied"} else {} end)
     + (if $mo == "solo"
        then {self_review: {rounds: $srr, a_tier_survivors: $sra, head_sha: $srs, current_head: $cur}}
        else {} end)
     + (if $t then {threads_truncated: true,
                    note: "线程超过 100 条，unresolved_count 只是下界；收敛判定已因此拒绝返回 0"}
        else {} end)')"

  if [[ -z "${missing// /}" ]]; then
    if (( solo )); then reason="solo_converged"; else reason="approved_resolved"; fi
    if [[ "$checks" == "none_configured" ]]; then reason="${reason}_no_checks"; else reason="${reason}_green"; fi
    jq -n --argjson b "$base_json" --arg r "$reason" '{done: true, reason: $r} + $b'
    return 0
  fi
  jq -n --argjson b "$base_json" --arg m "$missing" \
    '{done: false, missing: ($m | split(" ") | map(select(. != "")))} + $b'
  return 20
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

  selfreview)
    # 单人仓库收敛的必要条件：一轮**隔离上下文**的对抗式预审留下的机械记录（离线，不触网）。
    # 记的是"这一轮跑过、A 档存活几条、跑在哪个 sha 上"——不是判决，判决在 done_predicate 里。
    FINDINGS="${3:?findings file required: pr-poll.sh selfreview <pr> <findings-file> [reviewer]}"
    REVIEWER="${4:-pr-reviewer}"
    counters_init
    if [[ ! -s "$FINDINGS" ]]; then
      echo "pr-poll: findings file '$FINDINGS' missing or empty — an isolated review round must leave a record" >&2
      exit 1
    fi
    # Non-empty is not a record. `printf 'x' > f` used to satisfy the only condition solo mode has in
    # place of a human APPROVE, which made the substitute weaker than the thing it substitutes for
    # while SKILL.md called it stricter (PR pre-review, B-tier). Demand the shape /pr-review actually
    # emits: a review block naming its target and verdict, and either findings or a stated rationale
    # for having none.
    if ! python3 - "$FINDINGS" <<'PYSR'
import sys
try:
    import yaml
except ImportError:
    sys.stderr.write("pr-poll selfreview: PyYAML needed to validate the findings record\n"); sys.exit(1)
try:
    d = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
except Exception as e:
    sys.stderr.write("pr-poll selfreview: findings file does not parse as YAML: %s\n" % e); sys.exit(1)
r = (d or {}).get("review") if isinstance(d, dict) else None
if not isinstance(r, dict):
    sys.stderr.write("pr-poll selfreview: no `review:` block — this is not a /pr-review output\n"); sys.exit(1)
missing = [k for k in ("target", "mergeable") if not r.get(k)]
if missing:
    sys.stderr.write("pr-poll selfreview: review block lacks %s\n" % ", ".join(missing)); sys.exit(1)
f = r.get("findings")
if f is None:
    sys.stderr.write("pr-poll selfreview: review has no `findings` key (write `findings: []` plus a rationale for an empty round)\n"); sys.exit(1)
if isinstance(f, list) and not f and not (r.get("rationale") or r.get("no_findings_rationale")):
    sys.stderr.write("pr-poll selfreview: an empty findings list needs a rationale saying what was walked\n"); sys.exit(1)
PYSR
    then
      echo "pr-poll: '$FINDINGS' is not an isolated review record — solo mode stands on this file, so it must carry one" >&2
      exit 1
    fi
    a_tier="$(grep -Eo '(^|[[:space:]])a_tier_survivors:[[:space:]]*[0-9]+' "$FINDINGS" \
              | grep -Eo '[0-9]+' | tail -1 || true)"
    if [[ -z "$a_tier" ]]; then
      a_tier="$(grep -Eic '(^|[[:space:]])(tier|severity):[[:space:]]*"?'"'"'?(A|P0)([^A-Za-z0-9]|$)' "$FINDINGS" || true)"
    fi
    [[ "$a_tier" =~ ^[0-9]+$ ]] || a_tier=0
    head_sha="$(git rev-parse HEAD 2>/dev/null || echo "")"
    tmp="$(jq --arg f "$FINDINGS" --argjson a "$a_tier" --arg s "$head_sha" --arg r "$REVIEWER" \
              --arg t "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.self_review = {rounds: ((.self_review.rounds // 0) + 1),
                       last: {findings: $f, a_tier: $a, head_sha: $s, reviewer: $r, at: $t}}' \
      "$CNT_FILE")" && write_counters "$tmp"
    jq -c '.self_review' "$CNT_FILE"
    ;;

  predicate)
    # 同一个终止谓词，事实由参数给——联网取数与判决分离，谓词得以离线验证。
    DEC="${3:?usage: pr-poll.sh predicate <pr> <reviewDecision> <unresolved> <checks_state> <checks_count> <truncated> [--solo]}"
    UNRES="${4:?unresolved count required}"
    CST="${5:?checks state required: green|none_configured|red|unknown}"
    CCNT="${6:?checks count required}"
    TRUNC="${7:-false}"
    set +e
    done_predicate "$DEC" "$UNRES" "$CST" "$CCNT" "$TRUNC" "$SOLO"; rc=$?
    set -e
    exit "$rc"
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
    read -r cst ccnt <<<"$(checks_state)"
    set +e
    done_predicate "$decision" "$unresolved" "$cst" "$ccnt" "$truncated" "$SOLO"; rc=$?
    set -e
    exit "$rc"
    ;;

  *)
    echo "unknown command: $CMD" >&2
    exit 1
    ;;
esac
