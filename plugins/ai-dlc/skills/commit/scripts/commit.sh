#!/usr/bin/env bash
# commit.sh — the pre-gate and `git commit` compiled into ONE command.
#
# 为什么存在：verify_commit.py 只是"检"，落地由调用方自己串。dogfood 2026-09-06（I-50）里编排者
# 把预门接在管道后面读 JSON，管道吞掉了 REJECT 的退出码，`git commit` 照样执行——被拒的提交落了地。
# "exit 0 才 commit"不能靠调用方自觉：本脚本直接捕获退出码（赋值，不经管道），非 0 就不 commit。
#
# Usage:
#   commit.sh --msg-file MSG.txt [verify_commit.py 的任意参数…] [--dry-run]
#   commit.sh --msg "feat(x): y"  [--card C] [--lock L] [--issue N] [--allow-main] …
#   commit.sh --amend --expect-subject "<你上一条提交的 subject>" --msg-file MSG.txt
#
# --dry-run 只跑门，不提交。--amend 必须带 --expect-subject：共享 checkout 里 HEAD 可能是别的
# session 的提交，amend 会把它的消息改成你的（I-53）；主题对不上就拒绝，不猜。
#
# Exit: 0 已提交（或 --dry-run 通过） · 1 预门 REJECT（未提交） · 2 用法/IO/守卫拒绝（未提交）
#       3 预门通过但 `git commit` 自身失败（hook 拒绝 / 无可提交内容）——同样未提交。
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFY="$HERE/verify_commit.py"

MSG_FILE=""; MSG_TEXT=""; DRY=0; AMEND=0; EXPECT=""
PASS=()
while (( $# )); do
  case "$1" in
    --msg-file) MSG_FILE="${2:?--msg-file needs a path}"; PASS+=("$1" "$2"); shift 2;;
    --msg)      MSG_TEXT="${2:?--msg needs text}";        PASS+=("$1" "$2"); shift 2;;
    --dry-run)  DRY=1; shift;;
    --amend)    AMEND=1; shift;;
    --expect-subject) EXPECT="${2:?--expect-subject needs the subject you last committed}"; shift 2;;
    -h|--help)  sed -n '2,20p' "${BASH_SOURCE[0]}"; exit 0;;
    *)          PASS+=("$1"); shift;;
  esac
done

if [[ -z "$MSG_FILE" && -z "$MSG_TEXT" ]]; then
  echo "commit.sh: need --msg-file FILE or --msg TEXT (the gate checks the message too)" >&2; exit 2
fi
if [[ -n "$MSG_FILE" && -n "$MSG_TEXT" ]]; then
  echo "commit.sh: --msg-file and --msg are mutually exclusive" >&2; exit 2
fi

# I-53: HEAD 在共享工作区里不一定是你的提交。amend 前必须声明你以为 HEAD 是什么，对不上就停。
if (( AMEND )); then
  if [[ -z "$EXPECT" ]]; then
    echo "commit.sh: --amend requires --expect-subject '<the subject YOU last committed>'" >&2
    echo "  a checkout shared with another session may carry someone else's commit at HEAD;" >&2
    echo "  amending it rewrites THEIR message. One git worktree per parallel session avoids this." >&2
    exit 2
  fi
  head_subject="$(git log -1 --format=%s 2>/dev/null || true)"
  if [[ "$head_subject" != "$EXPECT" ]]; then
    echo "commit.sh: refusing --amend — HEAD subject is:" >&2
    echo "    $head_subject" >&2
    echo "  you expected:" >&2
    echo "    $EXPECT" >&2
    echo "  HEAD is not the commit you think it is (parallel session?). Commit on top instead." >&2
    exit 2
  fi
fi

# 退出码用赋值捕获，绝不经过管道——管道会把它换成最后一段的退出码，这正是 I-50 的机制。
out="$(python3 "$VERIFY" ${PASS[@]+"${PASS[@]}"} 2>&1)"; rc=$?
printf '%s\n' "$out"
if (( rc != 0 )); then
  echo "commit.sh: NOT COMMITTED — verify_commit.py exited $rc" >&2
  exit "$rc"
fi

if (( DRY )); then
  echo "commit.sh: --dry-run — gate passed, nothing committed" >&2
  exit 0
fi

if [[ -n "$MSG_FILE" ]]; then
  FILE="$MSG_FILE"
else
  FILE="$(mktemp)"; trap 'rm -f "$FILE"' EXIT
  printf '%s\n' "$MSG_TEXT" > "$FILE"
fi

cargs=(commit -F "$FILE")
(( AMEND )) && cargs+=(--amend)
if ! git "${cargs[@]}" >/dev/null; then
  echo "commit.sh: gate passed but \`git commit\` failed — nothing committed (hook? nothing staged?)" >&2
  exit 3
fi

sha="$(git rev-parse HEAD)"
subject="$(git log -1 --format=%s)"
printf '{"committed": true, "sha": "%s", "subject": "%s", "amended": %s}\n' \
  "$sha" "${subject//\"/\\\"}" "$( ((AMEND)) && echo true || echo false )"
