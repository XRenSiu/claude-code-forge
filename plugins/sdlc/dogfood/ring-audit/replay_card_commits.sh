#!/usr/bin/env bash
# replay_card_commits.sh — REQ-007: the auditor must not have edited what it audits.
#
# Every commit on the current branch whose message carries a `Card: CARD-xx` footer is replayed through
# the /commit pre-gate as a range diff:
#
#   verify_commit.py --range <sha>^..<sha> --card cards/CARD-xx.yaml [--lock .done_when.lock]
#
# Exit 0 iff every replay passes AND no Card commit touched the audited directories (plugins/sdlc/skills,
# plugins/sdlc/agents, plugins/sdlc/docs).  Otherwise exit 1 with `whitelist_overflow`.  The whitelist is
# the card's own allowed_files / forbidden_files, so this replays the card contract that was in force —
# it is not a second, hand-written rule (PSL-003: 审计者不改被审对象; the check is mechanical, not memory).
#
# Runs git from the repository root of the CWD, so the twin repositories the L5 suite builds are inspected
# instead of this one.  cards/<id>.yaml is resolved against the CWD first, then this script's directory.
# stdout is one JSON object; card_commits_touching_audited_dirs is the number REQ-007 reads.
#
# A commit WITHOUT a `Card:` footer is out of that replay's scope by contract, which would make it invisible.
# A second, clearly separated pass therefore walks EVERY footer-less commit on the branch — merge-base(main, HEAD)..HEAD,
# falling back to origin/main and then to the replay range — and reports non_card_commits_touching_audited_dirs
# (count + shas + paths).  Bounding that pass by the first Card commit hid everything that landed before the cards
# began, which is exactly the blind spot it exists to close.  It is recorded, never gated: the exit code still counts
# only the Card range.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_DIR="$PWD"
EMPTY_TREE=4b825dc642cb6eb9a060e54bf8d69288fbee4904
AUDITED_RE='^plugins/sdlc/(skills|agents|docs)/'
VERIFY="$SCRIPT_DIR/../../skills/commit/scripts/verify_commit.py"

json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g'; }

fail_hard() {                                    # unreadable input, not a failed predicate
  printf '{\n  "instrument": "replay_card_commits.sh",\n  "error": "%s"\n}\n' "$(json_escape "$1")"
  exit 2
}

[ -f "$VERIFY" ] || fail_hard "verify_commit.py not found at $VERIFY"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || fail_hard "not inside a git repository: $START_DIR"
cd "$REPO_ROOT" || fail_hard "cannot enter $REPO_ROOT"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"

# the branch's own commits, or every reachable commit where there is no main to compare against
if git rev-parse --verify --quiet main >/dev/null 2>&1; then RANGE_SPEC="main..HEAD"; else RANGE_SPEC="HEAD"; fi

# 锁的**路径**，不是工作区里那个文件。回放要按每条提交的父提交去取锁内容，
# 所以这里只解析"锁应该在哪儿"，不要求它此刻存在：从工作区探测存在性，等于让分支尖
# 决定要不要查锁——把分支尖上的锁删掉，整条锁检查就短路了（I-104 的外层那一半）。
LOCK_REL=""
for candidate in "$START_DIR/.done_when.lock" "$SCRIPT_DIR/.done_when.lock"; do
  case "$candidate" in
    "$REPO_ROOT"/*) rel="${candidate#$REPO_ROOT/}" ;;
    *) continue ;;
  esac
  # 此刻存在，或历史上任何一条被回放的提交的父提交里存在，都算数
  if [ -f "$candidate" ] || git -C "$REPO_ROOT" log --oneline -1 --all -- "$rel" >/dev/null 2>&1 \
     && [ -n "$(git -C "$REPO_ROOT" log --format=%H -1 --all -- "$rel" 2>/dev/null)" ]; then
    LOCK_REL="$rel"; break
  fi
done
LOCK=""
[ -n "$LOCK_REL" ] && [ -f "$REPO_ROOT/$LOCK_REL" ] && LOCK="$REPO_ROOT/$LOCK_REL"

records=""
card_commits=0
touching=0
rejected=0
overflow=0

card_footer_of() {                               # the `Card: CARD-xx` footer of one commit, empty when it has none
  git log -1 --format='%B' "$1" | grep -oE '^Card:[[:space:]]*CARD-[A-Za-z0-9_.-]+' | head -1 |
    sed -E 's/^Card:[[:space:]]*//'
}

range_of() {                                     # the range that shows only this commit's own diff
  if git rev-parse --verify --quiet "$1^" >/dev/null 2>&1; then printf '%s^..%s' "$1" "$1"
  else printf '%s..%s' "$EMPTY_TREE" "$1"; fi
}

audited_files() {                                # the range's paths that sit in the audited directories.
  # --no-renames is load-bearing: a file MOVED OUT of an audited dir must still list its old path, and rename
  # detection would show only the destination.  core.quotePath=false is load-bearing too: git's default C-quotes
  # every path carrying a non-ASCII byte — plugins/sdlc/skills/中文/x.md comes back as
  # "plugins/sdlc/skills/\344\270\255\346\226\207/x.md" — and the leading quote alone stops AUDITED_RE matching.
  git -c core.quotePath=false diff --name-only --no-renames "$1" 2>/dev/null | grep -E "$AUDITED_RE"
}

audited_hits() {                                 # how many of them there are
  local n
  n="$(audited_files "$1" | wc -l | tr -d '[:space:]')"
  [ -n "$n" ] || n=0
  printf '%s' "$n"
}

shas=()
cards=()
while read -r sha; do
  [ -n "$sha" ] || continue
  shas+=("$sha")
  cards+=("$(card_footer_of "$sha")")
done < <(git log --format='%H' $RANGE_SPEC 2>/dev/null)

for i in "${!shas[@]}"; do                       # "${!a[@]}" expands to nothing for an empty array, while
  sha="${shas[$i]}"                              # `seq 0 -1` printed "0" and "-1" and ${shas[0]} then tripped
  card="${cards[$i]}"                            # `set -u` — a branch with no commits of its own printed no JSON
  [ -n "$card" ] || continue
  card_commits=$((card_commits + 1))

  card_file=""
  for candidate in "$START_DIR/cards/$card.yaml" "$SCRIPT_DIR/cards/$card.yaml" "$REPO_ROOT/cards/$card.yaml"; do
    if [ -f "$candidate" ]; then card_file="$candidate"; break; fi
  done

  range="$(range_of "$sha")"

  hits="$(audited_hits "$range")"
  if [ "$hits" -gt 0 ]; then
    touching=$((touching + 1))
    overflow=$((overflow + 1))
  fi

  if [ -z "$card_file" ]; then                   # a Card footer naming a card this tree does not carry
    rc=2
    rejected=$((rejected + 1))
    overflow=$((overflow + 1))
  else
    args=(python3 "$VERIFY" --range "$range" --card "$card_file")
    # 锁要取**父提交**的：那才是"这条提交动手时生效的规则"。
    #
    # 两个坑，都踩过：
    # (1) 取工作区的锁 → 每次 l5 重签都追溯性地推翻过去每一条判决，一个落地时合法的提交
    #     会因为后来有人把某个文件加进冻结集而变成"改了锁内文件却没带提案"（I-101）。
    # (2) 取**这条提交自己树里**的锁 → 一条在同一个 diff 里删掉 .done_when.lock 的提交，
    #     就因为"该 sha 上没有锁文件"而免检，它在同一次提交里对锁内文件做的任何改动都不再被拒
    #     （I-104，PR #3 预审 round-4 F-7）。判据的来源被交给了受审对象本身。
    # 父提交同时避开两者：仍是历史锁（不受此刻重签影响），且不由被审的那次提交决定。
    commit_lock=""
    if [ -n "$LOCK_REL" ]; then
      if git -C "$REPO_ROOT" cat-file -e "$sha^:$LOCK_REL" 2>/dev/null; then
        commit_lock="$(mktemp)"
        git -C "$REPO_ROOT" show "$sha^:$LOCK_REL" > "$commit_lock" 2>/dev/null || commit_lock=""
      fi
      # 父提交没有锁（真正的早期提交，或首条提交无父）才不传 --lock。
    fi
    [ -n "$commit_lock" ] && args+=(--lock "$commit_lock")
    out="$("${args[@]}" 2>&1)"
    rc=$?
    [ -n "$commit_lock" ] && rm -f "$commit_lock"
    if [ "$rc" -ne 0 ]; then
      rejected=$((rejected + 1))
      if printf '%s' "$out" | grep -qi 'whitelist overflow'; then overflow=$((overflow + 1)); fi
    fi
  fi

  [ -n "$records" ] && records="$records,"
  records="$records
    {\"sha\": \"$(json_escape "$sha")\", \"card\": \"$(json_escape "$card")\", \"card_file\": \"$(json_escape "${card_file#$REPO_ROOT/}")\", \"range\": \"$(json_escape "$range")\", \"exit\": $rc, \"touches_audited_dirs\": $([ "$hits" -gt 0 ] && echo true || echo false)}"
done

# Second pass — RECORDED, NOT GATED.  AC-007-a scopes the replay above to commits carrying a `Card:` footer, so a
# footer-less commit that touched the audited directories would leave no trace at all.  This pass walks EVERY
# footer-less commit on the branch and reports the ones that did touch them.  Its window is the branch, not the Card
# era: bounding it by the oldest Card commit made the commits that landed before the cards began invisible to both
# passes.  It never feeds `touching` / `overflow` / `rejected`, so it cannot move the exit code.
NON_CARD_RANGE_SPEC="$RANGE_SPEC"                # the replay range is the last resort, for a tree with no main at all
for base in main origin/main; do
  if merge_base="$(git merge-base "$base" HEAD 2>/dev/null)" && [ -n "$merge_base" ]; then
    NON_CARD_RANGE_SPEC="$merge_base..HEAD"
    break
  fi
done

has_card_footer() {                              # case-insensitive, so `card: CARD-01` still counts as a footer
  git log -1 --format='%B' "$1" | grep -qiE '^Card:[[:space:]]*CARD-'
}

non_card_records=""
non_card_scanned=0
non_card_touching=0
while read -r sha; do
  [ -n "$sha" ] || continue
  has_card_footer "$sha" && continue
  non_card_scanned=$((non_card_scanned + 1))
  nc_range="$(range_of "$sha")"
  hits="$(audited_hits "$nc_range")"
  [ "$hits" -gt 0 ] || continue
  non_card_touching=$((non_card_touching + 1))
  files_json=""
  while IFS= read -r audited_path; do
    [ -n "$audited_path" ] || continue
    [ -n "$files_json" ] && files_json="$files_json, "
    files_json="$files_json\"$(json_escape "$audited_path")\""
  done < <(audited_files "$nc_range")
  [ -n "$non_card_records" ] && non_card_records="$non_card_records,"
  non_card_records="$non_card_records
    {\"sha\": \"$(json_escape "$sha")\", \"subject\": \"$(json_escape "$(git log -1 --format='%s' "$sha")")\", \"audited_paths\": $hits, \"files\": [$files_json]}"
done < <(git log --format='%H' $NON_CARD_RANGE_SPEC 2>/dev/null)

errors=""
if [ "$overflow" -gt 0 ]; then
  errors="\"whitelist_overflow: $touching of $card_commits Card commit(s) touched plugins/sdlc/skills|agents|docs or overflowed their card whitelist\""
elif [ "$rejected" -gt 0 ]; then
  errors="\"replay_reject: $rejected Card commit(s) were rejected by verify_commit.py\""
fi

status=0
if [ "$rejected" -gt 0 ] || [ "$overflow" -gt 0 ]; then status=1; fi

cat <<JSON
{
  "instrument": "replay_card_commits.sh",
  "repo_root": "$(json_escape "$REPO_ROOT")",
  "branch": "$(json_escape "$BRANCH")",
  "range_spec": "$(json_escape "$RANGE_SPEC")",
  "lock": "$(json_escape "${LOCK#$REPO_ROOT/}")",
  "audited_dirs": ["plugins/sdlc/skills", "plugins/sdlc/agents", "plugins/sdlc/docs"],
  "card_commits": $card_commits,
  "card_commits_touching_audited_dirs": $touching,
  "card_commits_rejected": $rejected,
  "replays": [${records}
  ],
  "non_card_range_spec": "$(json_escape "$NON_CARD_RANGE_SPEC")",
  "non_card_commits_scanned": $non_card_scanned,
  "non_card_commits_touching_audited_dirs": $non_card_touching,
  "non_card_commits_touching": [${non_card_records}
  ],
  "ok": $([ "$status" -eq 0 ] && echo true || echo false),
  "errors": [$errors]
}
JSON
exit $status
