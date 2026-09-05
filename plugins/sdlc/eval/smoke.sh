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

echo "== plan-cards / lint_cards.py"
FX="$S/sdlc/eval/fixtures"
expect "bad cards rejected (dup REQ, overlap, missing REQ-003, ac_ids, dos closure, context)" 1 py "$S/plan-cards/scripts/lint_cards.py" "$S/plan-cards/eval/fixtures/cards_bad" --spec "$FX/spec.md" --done-when "$FX/done_when.yaml" --dos "$FX/dos.yaml"
expect "good cards pass" 0 py "$S/plan-cards/scripts/lint_cards.py" "$S/plan-cards/eval/fixtures/cards_good" --spec "$FX/spec.md" --done-when "$FX/done_when.yaml" --dos "$FX/dos.yaml"

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
cp "$S/donewhen-extract/eval/fixtures/v2_bad_v1shape.yaml" dw_v1.yaml
expect "advance g2 refused when contract is v1-shaped (C1 compiled)" 1 bash -c "python3 '$SS' set contract.done_when=dw_v1.yaml >/dev/null && python3 '$SS' advance g2"
py "$SS" set contract.done_when=done_when.yaml >/dev/null
expect "advance g2 (v2 contract validates)" 0 py "$SS" advance g2
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
expect "set pr/review/merge → advance to merge" 0 bash -c "python3 '$SS' set pr.number=7 >/dev/null && python3 '$SS' advance review >/dev/null && python3 '$SS' set review.done=true gates.g3.required=false >/dev/null && python3 '$SS' advance merge >/dev/null && python3 '$SS' set merge.sha=deadbeef >/dev/null"
expect "advance release" 0 py "$SS" advance release
expect "advance archive refused (release not done)" 1 py "$SS" advance archive
expect "set release.done → advance archive" 0 bash -c "python3 '$SS' set release.version=0.1.0 release.tag=v0.1.0 release.done=true >/dev/null && python3 '$SS' advance archive"
expect "ledger has waiver row" 0 bash -c "grep -q '| waiver |' .sdlc/demo/ledger.md"
expect "state.json never hand-edited: json valid" 0 python3 -c "import json;json.load(open('.sdlc/demo/state.json'))"
popd >/dev/null

echo "== retro / metrics.py"
expect "metrics export" 0 py "$S/retro/scripts/metrics.py" "$S/retro/eval/fixtures" --md "$TMP/metrics.md"

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
cp "$S/plan-cards/eval/fixtures/cards_good/CARD-01.yaml" card.yaml
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

echo "== psl / verify_psl.py (imported from looper)"
FXD="$S/psl-derive/eval/fixtures"
expect "legal PSL passes" 0 py "$S/psl/scripts/verify_psl.py" "$FXD/PSL-memory-time-search.md"
expect "PSL with Step N in Workflow rejected" 1 py "$S/psl/scripts/verify_psl.py" "$FXD/PSL-bad-steps.md"

echo "== psl-derive / verify_derived.py"
expect "good derived dir passes" 0 py "$S/psl-derive/scripts/verify_derived.py" "$FXD/derived_good" --psl "$FXD/PSL-memory-time-search.md"
expect "bad derived dir rejected (no ref, fake id, Step, invented entity)" 1 py "$S/psl-derive/scripts/verify_derived.py" "$FXD/derived_bad" --psl "$FXD/PSL-memory-time-search.md"
expect "bad derived reports all four breaches" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$FXD/derived_bad' --psl '$FXD/PSL-memory-time-search.md' | grep -c 'without PSL-ID\|does not exist\|named steps\|not in PSL Domain' | grep -q '^4$'"

echo "== dos-extract / verify_dos.py (imported from looper)"
FXO="$S/dos-extract/eval/fixtures"
expect "clean dos passes" 0 py "$S/dos-extract/scripts/verify_dos.py" "$FXO/dos_good.yaml"
expect "UI-suffixed object rejected" 1 py "$S/dos-extract/scripts/verify_dos.py" "$FXO/dos_bad_ui_suffix.yaml"

echo "== invariant-extract / verify_card.py (imported from looper)"
FXI="$S/invariant-extract/eval/fixtures"
expect "card with provenance passes" 0 py "$S/invariant-extract/scripts/verify_card.py" "$FXI/card_good.yaml" --dos "$FXO/dos_good.yaml"
expect "card without provenance rejected" 1 py "$S/invariant-extract/scripts/verify_card.py" "$FXI/card_bad_noprov.yaml"

echo "== donewhen-extract / verify_done_when.py (imported from qanat)"
FXW="$S/donewhen-extract/eval/fixtures"
expect "paired, thresholded card passes" 0 py "$S/donewhen-extract/scripts/verify_done_when.py" "$FXW/card_good.yaml"
expect "vague clause without threshold rejected" 1 py "$S/donewhen-extract/scripts/verify_done_when.py" "$FXW/card_bad_vague.yaml"

echo "== spec-compile / verify_compile.py (imported from qanat)"
FXC="$S/spec-compile/eval/fixtures"
expect "manifest routed by decidability passes" 0 py "$S/spec-compile/scripts/verify_compile.py" "$FXC/manifest_good.yaml"
expect "behavioral clause routed up to judgment rejected" 1 py "$S/spec-compile/scripts/verify_compile.py" "$FXC/manifest_bad_up.yaml"

echo "== calibrate / verify_calibration.py (imported from qanat)"
FXA="$S/calibrate/eval/fixtures"
expect "calibrated eval_case set passes meta-gate" 0 py "$S/calibrate/scripts/verify_calibration.py" "$FXA/report_good.yaml"
expect "missing holdout forbids activation" 1 py "$S/calibrate/scripts/verify_calibration.py" "$FXA/report_bad_noholdout.yaml"
expect "loosening alpha below 0.80 rejected" 1 py "$S/calibrate/scripts/verify_calibration.py" "$FXA/report_good.yaml" --min-alpha 0.5

echo "== sdlc / G1 requires derivation products (PSL track)"
ST2="$TMP/state-psl"; mkdir -p "$ST2"; pushd "$ST2" >/dev/null
expect "init psl track" 0 py "$SS" init --slug demo-psl --title "psl feature" --track psl
expect "advance track" 0 py "$SS" advance track
expect "advance issue refused (G1 pending)" 1 py "$SS" advance issue
expect "gate g1 pass refused without world.derived_dir" 1 py "$SS" gate g1 --verdict pass --by human
mkdir -p derived && cp "$FXD/derived_good/"* derived/
expect "set world.* paths" 0 py "$SS" set world.psl=PSL.md world.derived_dir=derived
expect "gate g1 pass with derived products" 0 py "$SS" gate g1 --verdict pass --by human --record g1-record.md
expect "advance issue ok after G1" 0 py "$SS" advance issue
expect "gate g1 reject with attribution bumps world counter" 0 bash -c "python3 '$SS' gate g1 --verdict reject --by human --attribution rule_error >/dev/null && python3 '$SS' show | grep -q '\"world\": 1'"
popd >/dev/null

echo "== acceptance-spec / validate_done_when.py (imported from done-when-pipeline)"
EX="$S/acceptance-spec/references/examples/subscription-cancellation"
expect "example done_when.yaml validates" 0 py "$S/acceptance-spec/scripts/validate_done_when.py" "$EX/done_when.yaml" --spec "$EX/spec.md" --check
DWB="$TMP/dw_bad.yaml"; python3 - "$EX/done_when.yaml" "$DWB" <<'PYEOF'
import sys
s=open(sys.argv[1],encoding="utf-8").read()
s=s.replace("  - file: src/billing/cancel_subscription_use_case.ts\n","  - file: src/billing/cancel_subscription_use_case.ts\n    extra_field: nope\n",1)
open(sys.argv[2],"w",encoding="utf-8").write(s)
PYEOF
expect "existence entry with stray sub-field rejected" 1 py "$S/acceptance-spec/scripts/validate_done_when.py" "$DWB" --check

echo "== test-suite-generator / derive_counts, gen_existence, check_verbatim_names"
expect "derive_counts on example" 0 py "$S/test-suite-generator/scripts/derive_counts.py" "$EX/done_when.yaml" --json
expect "gen_existence emits a fail-fast script (set -euo pipefail present, no if-wrapped checks)" 0 bash -c "out=\$(python3 '$S/test-suite-generator/scripts/gen_existence.py' '$EX/done_when.yaml' --src src) && grep -q 'set -euo pipefail' <<<\"\$out\" && ! grep -qE '^\\s*if .*\\[ -f' <<<\"\$out\""
TD="$TMP/tests_ok"; mkdir -p "$TD"; python3 - "$EX/done_when.yaml" "$TD/all.test.ts" <<'PYEOF'
import sys, yaml
d=yaml.safe_load(open(sys.argv[1],encoding="utf-8")); names=[]
b=d.get("behavior") or {}
for top in ("unit_tests","integration_tests"):
    g=b.get(top) or {}
    for sub in ("example_based","property_based"): names += [n for n in (g.get(sub) or []) if isinstance(n,str)]
names += [n for n in (b.get("e2e_tests") or []) if isinstance(n,str)]
open(sys.argv[2],"w").write("\n".join(f"test('{n}', () => {{}});" for n in names)+"\n")
PYEOF
expect "verbatim names all present → 0" 0 py "$S/test-suite-generator/scripts/check_verbatim_names.py" "$EX/done_when.yaml" "$TD" --check
TD2="$TMP/tests_missing"; mkdir -p "$TD2"; head -n 2 "$TD/all.test.ts" > "$TD2/some.test.ts"
expect "verbatim names missing → 1" 1 py "$S/test-suite-generator/scripts/check_verbatim_names.py" "$EX/done_when.yaml" "$TD2" --check

echo "== spec-gaming-detector / compute_score.py"
expect "score P0+P1+P3 = 5.5" 0 bash -c "python3 '$S/spec-gaming-detector/scripts/compute_score.py' '$S/spec-gaming-detector/eval/fixtures/findings.json' --json | grep -q '5.5'"
expect "trend warning on steep rise" 0 bash -c "python3 '$S/spec-gaming-detector/scripts/compute_score.py' '$S/spec-gaming-detector/eval/fixtures/findings.json' --baseline 3 --json | grep -q 'trend_warning'"

echo "== meta-judge / compute_confidence.py"
expect "two-source cross-vendor high → 1.0; single low → 0.0" 0 bash -c "python3 '$S/meta-judge/scripts/compute_confidence.py' '$S/meta-judge/eval/fixtures/merged.json' --json | python3 -c \"import json,sys; d=json.load(sys.stdin); m={x['merged_finding_id']:x['confidence'] for x in d}; assert m['mf-001']==1.0 and m['mf-002']==0.0, m\""

echo "== donewhen-extract / validate_done_when_v2.py + convert_v1_to_v2.py"
FXV="$S/donewhen-extract/eval/fixtures"
expect "v2 contract validates" 0 py "$S/donewhen-extract/scripts/validate_done_when_v2.py" "$FXV/v2_good.yaml"
expect "v1-shaped contract rejected" 1 py "$S/donewhen-extract/scripts/validate_done_when_v2.py" "$FXV/v2_bad_v1shape.yaml"
expect "file-path existence rejected (C2)" 1 py "$S/donewhen-extract/scripts/validate_done_when_v2.py" "$FXV/v2_bad_file_existence.yaml"
expect "convert v1 example → v2 skeleton written" 0 py "$S/donewhen-extract/scripts/convert_v1_to_v2.py" "$EX/done_when.yaml" --out "$TMP/converted.v2.yaml" --spec "$EX/spec.md"
expect "converted skeleton fails v2 validation until ACs are completed (honest)" 1 py "$S/donewhen-extract/scripts/validate_done_when_v2.py" "$TMP/converted.v2.yaml"
expect "converted skeleton keeps v1 tests as manifest + moves file existence to cards_hint" 0 bash -c "python3 -c \"import yaml; d=yaml.safe_load(open('$TMP/converted.v2.yaml')); assert d['schema']==2 and d['cards_hint']['allowed_files'] and d['behavior']['unit_tests']['example_based'] and not any('file' in e for e in d['existence'])\""

echo "== sdlc / lock_done_when.py two-stage"
L2="$TMP/lock2"; mkdir -p "$L2/tests"; cp "$FXV/v2_good.yaml" "$L2/done_when.yaml"; echo "test('x')" > "$L2/tests/a.test.ts"; pushd "$L2" >/dev/null
expect "sign stage g2" 0 py "$S/sdlc/scripts/lock_done_when.py" sign --by human --stage g2 done_when.yaml
expect "re-sign stage l5 with tests" 0 py "$S/sdlc/scripts/lock_done_when.py" sign --by tester --stage l5 done_when.yaml tests/a.test.ts
expect "verify reports stage l5" 0 bash -c "python3 '$S/sdlc/scripts/lock_done_when.py' verify | grep -q '\"stage\": \"l5\"'"
echo "tampered" >> tests/a.test.ts
expect "tampered locked test rejected" 1 py "$S/sdlc/scripts/lock_done_when.py" verify
popd >/dev/null

echo "== release / verify_release.py"
RR="$TMP/rel"; mkdir -p "$RR/releases"; pushd "$RR" >/dev/null
git init -q -b main . && git -c user.name=t -c user.email=t@t commit -q --allow-empty -m "chore: init" && git tag v0.1.0
git -c user.name=t -c user.email=t@t commit -q --allow-empty -m "feat(search): relative time search"
printf '# Changelog\n\n## [0.2.0] - 2026-09-05\n\n### Added\n- feat(search): relative time search\n\n## [0.1.0] - 2026-09-01\n\n- init\n' > CHANGELOG.md
cat > releases/v0.2.0.md <<'NOTES'
# Release v0.2.0

## Changes
- feat(search): relative time search

## Verification
- pre-deploy: npm test → 128 passed
- post-deploy: curl /health → 200 v0.2.0

## Rollback
- how: redeploy previous tag v0.1.0
- data: 无迁移

## Escape
发现问题？/issue --escape 并引用 v0.2.0
NOTES
expect "pre-tag check passes (changelog + notes + bump minor)" 0 py "$S/release/scripts/verify_release.py" --version 0.2.0 --bump auto --pre-tag
expect "post-tag check fails before tag exists" 1 py "$S/release/scripts/verify_release.py" --version 0.2.0
git tag v0.2.0
expect "post-tag check passes with tag on HEAD" 0 py "$S/release/scripts/verify_release.py" --version 0.2.0 --bump auto
expect "pre-tag refuses to overwrite existing tag" 1 py "$S/release/scripts/verify_release.py" --version 0.2.0 --pre-tag
expect "bump mismatch rejected (patch version for a feat)" 1 bash -c "sed -i '' 's/\\[0.2.0\\]/[0.1.1]/' CHANGELOG.md && cp releases/v0.2.0.md releases/v0.1.1.md && python3 '$S/release/scripts/verify_release.py' --version 0.1.1 --bump auto --pre-tag"
sed -i '' 's/- how: redeploy previous tag v0.1.0/- how: <fill>/' releases/v0.2.0.md
expect "empty rollback rejected" 1 py "$S/release/scripts/verify_release.py" --version 0.2.0
popd >/dev/null

echo
echo "smoke: $pass passed, $fail failed  (tmp: $TMP)"
[[ $fail -eq 0 ]]
