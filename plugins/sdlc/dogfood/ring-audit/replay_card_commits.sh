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

# the G2 lock, if this tree carries one (a twin repository does not)
LOCK=""
for candidate in "$START_DIR/.done_when.lock" "$SCRIPT_DIR/.done_when.lock"; do
  if [ -f "$candidate" ]; then LOCK="$candidate"; break; fi
done

records=""
card_commits=0
touching=0
rejected=0
overflow=0

while read -r sha; do
  [ -n "$sha" ] || continue
  card="$(git log -1 --format='%B' "$sha" | grep -oE '^Card:[[:space:]]*CARD-[A-Za-z0-9_.-]+' | head -1 |
          sed -E 's/^Card:[[:space:]]*//')"
  [ -n "$card" ] || continue
  card_commits=$((card_commits + 1))

  card_file=""
  for candidate in "$START_DIR/cards/$card.yaml" "$SCRIPT_DIR/cards/$card.yaml" "$REPO_ROOT/cards/$card.yaml"; do
    if [ -f "$candidate" ]; then card_file="$candidate"; break; fi
  done

  if git rev-parse --verify --quiet "$sha^" >/dev/null 2>&1; then range="$sha^..$sha"; else range="$EMPTY_TREE..$sha"; fi

  hits="$(git diff --name-only "$range" 2>/dev/null | grep -cE "$AUDITED_RE")"
  [ -n "$hits" ] || hits=0
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
    [ -n "$LOCK" ] && args+=(--lock "$LOCK")
    out="$("${args[@]}" 2>&1)"
    rc=$?
    if [ "$rc" -ne 0 ]; then
      rejected=$((rejected + 1))
      if printf '%s' "$out" | grep -qi 'whitelist overflow'; then overflow=$((overflow + 1)); fi
    fi
  fi

  [ -n "$records" ] && records="$records,"
  records="$records
    {\"sha\": \"$(json_escape "$sha")\", \"card\": \"$(json_escape "$card")\", \"card_file\": \"$(json_escape "${card_file#$REPO_ROOT/}")\", \"range\": \"$(json_escape "$range")\", \"exit\": $rc, \"touches_audited_dirs\": $([ "$hits" -gt 0 ] && echo true || echo false)}"
done < <(git log --format='%H' $RANGE_SPEC 2>/dev/null)

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
  "ok": $([ "$status" -eq 0 ] && echo true || echo false),
  "errors": [$errors]
}
JSON
exit $status
