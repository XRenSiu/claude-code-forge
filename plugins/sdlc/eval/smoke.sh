#!/usr/bin/env bash
# smoke.sh — run every sdlc script against its fixtures; print PASS/FAIL per expectation.
# This is the L0/structural evidence behind each skill's eval/gate.json (static_only tier).
# Usage: bash plugins/sdlc/eval/smoke.sh   (from the repo root; needs python3 + pyyaml, git, jq)
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
S="$ROOT/skills"
TMP="$(mktemp -d)"
pass=0; fail=0
expect() { # expect <label> <want_exit> <cmd...>
  local label="$1" want="$2"; shift 2
  local out; out="$("$@" 2>&1)"; local rc=$?
  if [[ "$rc" == "$want" ]]; then pass=$((pass+1)); echo "PASS  [$rc] $label"; else fail=$((fail+1)); echo "FAIL  [got $rc want $want] $label"; echo "$out" | head -20 | sed 's/^/      /'; fi
}
py() { python3 "$@"; }

echo "== issue / verify_issue.py"
FX="$S/issue/eval/fixtures"
expect "good issue passes" 0 py "$S/issue/scripts/verify_issue.py" "$FX/good_issue.md" --dos "$FX/dos.yaml"
expect "vague expect rejected" 1 py "$S/issue/scripts/verify_issue.py" "$FX/bad_vague.md"
expect "missing unhappy twin rejected" 1 py "$S/issue/scripts/verify_issue.py" "$FX/bad_no_twin.md"
expect "file-path observe rejected" 1 py "$S/issue/scripts/verify_issue.py" "$FX/bad_filepath_observe.md"
expect "DOS closure failure rejected (force psl)" 1 py "$S/issue/scripts/verify_issue.py" "$FX/closure_fail.md" --dos "$FX/dos.yaml"
expect "closure fail output carries force_track psl" 0 bash -c "python3 '$S/issue/scripts/verify_issue.py' '$FX/closure_fail.md' --dos '$FX/dos.yaml' | grep -q '\"force_track\": \"psl\"'"
expect "bug kind good passes" 0 py "$S/issue/scripts/verify_issue.py" "$FX/good_bug.md" --kind bug
expect "bug kind without Repro rejected" 1 py "$S/issue/scripts/verify_issue.py" "$FX/good_issue.md" --kind bug

echo "== sdlc / lint_cards.py"
FX="$S/sdlc/eval/fixtures"
expect "bad cards rejected (dup REQ, overlap, missing REQ-003, ac_ids, dos closure, context)" 1 py "$S/sdlc/scripts/lint_cards.py" "$FX/cards_bad" --spec "$FX/spec.md" --done-when "$FX/done_when.yaml" --dos "$FX/dos.yaml"
expect "good cards pass" 0 py "$S/sdlc/scripts/lint_cards.py" "$FX/cards_good" --spec "$FX/spec.md" --done-when "$FX/done_when.yaml" --dos "$FX/dos.yaml"

echo "== sdlc / lock_done_when.py"
L="$TMP/lock"; mkdir -p "$L"; cp "$FX/done_when.yaml" "$L/"; pushd "$L" >/dev/null
expect "sign writes lock" 0 py "$S/sdlc/scripts/lock_done_when.py" sign --by tester done_when.yaml
expect "verify unchanged ok" 0 py "$S/sdlc/scripts/lock_done_when.py" verify
echo "# tampered" >> done_when.yaml
expect "tampered AC without proposal rejected" 1 py "$S/sdlc/scripts/lock_done_when.py" verify
echo "proposal" > change-proposal-001.md
expect "tampered AC with proposal → exit 2 (changed_with_proposal)" 2 py "$S/sdlc/scripts/lock_done_when.py" verify
popd >/dev/null

echo "== sdlc / sdlc_state.py"
ST="$TMP/state"; mkdir -p "$ST"; pushd "$ST" >/dev/null
SS="$S/sdlc/scripts/sdlc_state.py"
expect "init" 0 py "$SS" init --slug demo --title "demo feature"
expect "advance to track" 0 py "$SS" advance track
expect "advance to issue refused (track unset)" 1 py "$SS" advance issue
expect "set track=task" 0 py "$SS" set track=task
expect "advance to issue ok" 0 py "$SS" advance issue
expect "skip to branch refused (issue.number unset)" 1 py "$SS" advance branch
expect "set issue.number" 0 py "$SS" set issue.number=42 issue.url=https://x/42
expect "advance branch" 0 py "$SS" advance branch
expect "set branch" 0 py "$SS" set branch.name=feat/42-demo branch.base=main
expect "advance contract" 0 py "$SS" advance contract
cp "$FX/done_when.yaml" done_when.yaml
expect "set contract.done_when" 0 py "$SS" set contract.done_when=done_when.yaml contract.source=issue-inline
expect "advance g2" 0 py "$SS" advance g2
expect "advance cards refused (G2 not passed)" 1 py "$SS" advance cards
expect "gate g2 pass refused without lock.path" 1 py "$SS" gate g2 --verdict pass --by human
py "$S/sdlc/scripts/lock_done_when.py" sign --by human done_when.yaml >/dev/null
expect "set lock.path" 0 py "$SS" set lock.path=.done_when.lock lock.signed_by=human
expect "gate g2 pass" 0 py "$SS" gate g2 --verdict pass --by human
expect "advance cards" 0 py "$SS" advance cards
expect "advance implement refused (lint not passed)" 1 py "$SS" advance implement
expect "set cards.lint_passed + card" 0 bash -c "python3 '$SS' set cards.lint_passed=true >/dev/null && python3 '$SS' card CARD-01 --status todo"
expect "advance implement" 0 py "$SS" advance implement
expect "fail card_test_fail #1 (no escalate)" 0 bash -c "python3 '$SS' fail --signal card_test_fail --card CARD-01 --fingerprint fp1 | grep -q '\"escalate\": false'"
expect "fail same fingerprint #2 → escalate" 0 bash -c "python3 '$SS' fail --signal card_test_fail --card CARD-01 --fingerprint fp1 | grep -q '\"escalate\": true'"
expect "fail whitelist_overflow → human" 0 bash -c "python3 '$SS' fail --signal whitelist_overflow --evidence 'src/x.ts' | grep -q '\"escalate_to\": \"human\"'"
expect "unknown signal refused" 1 py "$SS" fail --signal nonsense
expect "advance acceptance refused (card not done)" 1 py "$SS" advance acceptance
expect "card done" 0 py "$SS" card CARD-01 --status done --commit abc123
expect "advance acceptance" 0 py "$SS" advance acceptance
expect "advance pr refused (no evaluation/skip reason)" 1 py "$SS" advance pr
expect "force without reason refused" 1 py "$SS" advance pr --force
expect "force with reason → waiver recorded" 0 py "$SS" advance pr --force --reason "task track lightweight"
expect "gate g1 reject without attribution refused" 1 py "$SS" gate g1 --verdict reject --by human
expect "ledger has waiver row" 0 bash -c "grep -q '| waiver |' .sdlc/demo/ledger.md"
expect "state.json never hand-edited: json valid" 0 python3 -c "import json;json.load(open('.sdlc/demo/state.json'))"
popd >/dev/null

echo "== sdlc / metrics.py"
expect "metrics export" 0 py "$S/sdlc/scripts/metrics.py" "$FX/archive" --md "$TMP/metrics.md"

echo "== commit / verify_commit.py"
R="$TMP/repo"; mkdir -p "$R"; pushd "$R" >/dev/null
git init -q -b main . && git -c user.name=t -c user.email=t@t commit -q --allow-empty -m "chore: init"
git checkout -q -b feat/42-demo
mkdir -p src/search/api tests
echo "export const a = 1;" > src/search/api/time.ts && git add src/search/api/time.ts
VC="$S/commit/scripts/verify_commit.py"
expect "good staged + good message passes" 0 py "$VC" --msg "feat(search): add relative time parser" --issue 42
expect "bad message rejected" 1 py "$VC" --msg "update stuff"
expect "subject with period rejected" 1 py "$VC" --msg "feat(search): add parser."
git checkout -q main; expect "commit on main rejected" 1 py "$VC" --msg "feat(search): x"; git checkout -q feat/42-demo
echo "AWS_KEY=AKIAABCDEFGHIJKLMNOP" > src/search/api/cfg.ts && git add src/search/api/cfg.ts
expect "secret in added lines rejected" 1 py "$VC" --msg "feat(search): cfg"
git reset -q src/search/api/cfg.ts && rm src/search/api/cfg.ts
echo "SECRET=1" > .env && git add .env
expect ".env staged rejected" 1 py "$VC" --msg "chore: env"
git reset -q .env && rm .env
echo "  debugger;" >> src/search/api/time.ts && git add src/search/api/time.ts
expect "debugger left rejected" 1 py "$VC" --msg "feat(search): dbg"
echo "export const a = 1;" > src/search/api/time.ts && git add src/search/api/time.ts
cp "$FX/cards_good/CARD-01.yaml" card.yaml
expect "card whitelist: in-list file passes" 0 py "$VC" --msg "feat(search): parser" --card card.yaml
mkdir -p src/search/ui && echo "x" > src/search/ui/oops.ts && git add src/search/ui/oops.ts
expect "card whitelist overflow rejected" 1 py "$VC" --msg "feat(search): parser" --card card.yaml
git reset -q src/search/ui/oops.ts && rm -rf src/search/ui
cp "$FX/done_when.yaml" done_when.yaml && git add done_when.yaml && git -c user.name=t -c user.email=t@t commit -q -m "chore(contract): add done_when"
py "$S/sdlc/scripts/lock_done_when.py" sign --by human done_when.yaml >/dev/null
echo "# tamper" >> done_when.yaml && git add done_when.yaml
expect "locked file staged without proposal rejected" 1 py "$VC" --msg "chore(contract): tweak" --lock .done_when.lock
echo "p" > change-proposal-001.md && git add change-proposal-001.md
expect "locked file with proposal passes (flag)" 0 py "$VC" --msg "chore(contract): tweak per proposal" --lock .done_when.lock
git reset -q . ; git checkout -q -- done_when.yaml; rm -f change-proposal-001.md
popd >/dev/null

echo "== pr / verify_pr.py"
pushd "$R" >/dev/null
git add -A >/dev/null 2>&1; git -c user.name=t -c user.email=t@t commit -q -m "feat(search): add relative time parser" || true
VP="$S/pr/scripts/verify_pr.py"
FXP="$S/pr/eval/fixtures"
expect "good body passes (preflight; no remote → flag)" 0 py "$VP" --body "$FXP/good_body.md" --title "feat(search): relative time search" --base main --done-when "$FX/done_when.yaml"
expect "missing Closes rejected" 1 py "$VP" --body "$FXP/bad_no_link.md" --base main --skip-preflight
expect "no verification evidence rejected" 1 py "$VP" --body "$FXP/bad_no_verification.md" --base main --skip-preflight
expect "missing mechanical AC row rejected" 1 py "$VP" --body "$FXP/bad_missing_ac.md" --base main --skip-preflight --done-when "$FX/done_when.yaml"
expect "bad title rejected" 1 py "$VP" --body "$FXP/good_body.md" --title "Update things" --base main --skip-preflight
python3 -c "print('\n'.join('line %d' % i for i in range(1200)))" > big.txt && git add big.txt && git -c user.name=t -c user.email=t@t commit -q -m "chore: big"
expect "XL size rejected" 1 py "$VP" --body "$FXP/good_body.md" --base main --skip-preflight
expect "XL allowed with --allow-xl" 0 py "$VP" --body "$FXP/good_body.md" --base main --skip-preflight --allow-xl
git checkout -q main; expect "head == base rejected" 1 py "$VP" --body "$FXP/good_body.md" --base main; git checkout -q feat/42-demo
popd >/dev/null

echo "== pr-review / post_review.py"
FXR="$S/pr-review/eval/fixtures"
PR="$S/pr-review/scripts/post_review.py"
expect "dry-run: inline on commentable line, degrade other" 0 bash -c "python3 '$PR' '$FXR/findings.yaml' --pr 1 --dry-run --diff-file '$FXR/sample.diff' | grep -q '\"degraded\": 1'"
expect "dry-run: event auto REQUEST_CHANGES on tier A" 0 bash -c "python3 '$PR' '$FXR/findings.yaml' --pr 1 --dry-run --diff-file '$FXR/sample.diff' | grep -q 'REQUEST_CHANGES'"
expect "APPROVE refused" 1 py "$PR" "$FXR/findings.yaml" --pr 1 --dry-run --diff-file "$FXR/sample.diff" --event APPROVE
expect "P0 without reproduction refused" 1 py "$PR" "$FXR/findings_bad_p0.yaml" --pr 1 --dry-run --diff-file "$FXR/sample.diff"

echo "== review-loop / pr-poll.sh (offline subcommands)"
PP="$S/review-loop/scripts/pr-poll.sh"
W="$TMP/watch"; mkdir -p "$W"; pushd "$W" >/dev/null
expect "round 1 ok" 0 bash -c "MAX_ROUNDS=2 bash '$PP' round 7 >/dev/null"
expect "round 2 → exit 30 (budget)" 30 bash -c "MAX_ROUNDS=2 bash '$PP' round 7 >/dev/null"
expect "strike 1 ok" 0 bash -c "MAX_THREAD_STRIKES=2 bash '$PP' strike 7 PRRT_x >/dev/null"
expect "strike 2 → exit 31 (freeze)" 31 bash -c "MAX_THREAD_STRIKES=2 bash '$PP' strike 7 PRRT_x >/dev/null"
expect "counters file valid json" 0 bash -c "jq -e . .sdlc/pr-watch/pr-7.counters.json >/dev/null"
expect "corrupt counters self-heal" 0 bash -c "echo '{bad' > .sdlc/pr-watch/pr-7.counters.json && MAX_ROUNDS=9 bash '$PP' round 7 | grep -q '\"rounds\": 1'"
popd >/dev/null

echo
echo "smoke: $pass passed, $fail failed  (tmp: $TMP)"
[[ $fail -eq 0 ]]
