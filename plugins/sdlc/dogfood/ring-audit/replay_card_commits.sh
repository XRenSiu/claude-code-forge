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
