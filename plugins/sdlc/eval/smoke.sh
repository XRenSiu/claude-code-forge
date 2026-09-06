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
# dogfood 2026-09-05 (I-07): one-line Links (template shape) with a G1 path must not flag "without a G1 record path"
PSLI="$TMP/psl_issue.md"; sed -e 's/- track: task/- track: psl/' -e 's|G1: none|G1: g1-record.md|' "$FX/good_issue.md" > "$PSLI"
expect "psl-track issue with G1 path on the one-line Links carries no G1 flag (I-07)" 0 bash -c "python3 '$S/issue/scripts/verify_issue.py' '$PSLI' --dos '$FX/dos.yaml' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['verdict']=='PASS' and not any('G1 record path' in f for f in d['flags']), d['flags']\""

echo "== plan-cards / lint_cards.py"
FX="$S/sdlc/eval/fixtures"
expect "bad cards rejected (dup REQ, overlap, missing REQ-003, ac_ids, dos closure, context)" 1 py "$S/plan-cards/scripts/lint_cards.py" "$S/plan-cards/eval/fixtures/cards_bad" --spec "$FX/spec.md" --done-when "$FX/done_when.yaml" --dos "$FX/dos.yaml"
expect "good cards pass" 0 py "$S/plan-cards/scripts/lint_cards.py" "$S/plan-cards/eval/fixtures/cards_good" --spec "$FX/spec.md" --done-when "$FX/done_when.yaml" --dos "$FX/dos.yaml"

echo "== sdlc / lock_done_when.py"
L="$TMP/lock"; mkdir -p "$L"; cp "$FX/done_when.yaml" "$L/"; pushd "$L" >/dev/null
expect "sign writes lock" 0 py "$S/sdlc/scripts/lock_done_when.py" sign --by tester done_when.yaml
expect "lock sign: delegated_agent without authorization refused (I-39)" 1 py "$S/sdlc/scripts/lock_done_when.py" sign --by proxy --signer-kind delegated_agent --out .dl.lock done_when.yaml
expect "lock sign: delegated_agent with authorization records signer_kind (I-39)" 0 bash -c "python3 '$S/sdlc/scripts/lock_done_when.py' sign --by proxy --signer-kind delegated_agent --authorization 'user said so' --out .dl.lock done_when.yaml >/dev/null && grep -q '\"signer_kind\": \"delegated_agent\"' .dl.lock"
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
echo "# failure report" > .sdlc/demo/failure-report-001.md
expect "report clears pending.failure_report after the escalations above" 0 py "$SS" report --path .sdlc/demo/failure-report-001.md
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
# dogfood 2026-09-05 (I-38): a bare forbidden name and **/dir/** must match at any depth
expect "verify_commit glob: bare done_when.yaml matches nested path (I-38)" 0 python3 -c "
import importlib.util; spec=importlib.util.spec_from_file_location('vc','$VC'); vc=importlib.util.module_from_spec(spec); spec.loader.exec_module(vc)
assert vc.glob_match('plugins/x/dogfood/done_when.yaml','done_when.yaml'); assert vc.glob_match('a/b/tests/c.py','**/tests/**'); assert not vc.glob_match('a/b/src/c.py','**/tests/**'); assert not vc.glob_match('a/done_when.yaml.bak','done_when.yaml')"
git reset -q src/search/ui/oops.ts && rm -rf src/search/ui
cp "$FX/done_when.yaml" done_when.yaml && git add done_when.yaml && git -c user.name=t -c user.email=t@t commit -q -m "chore(contract): add done_when"
py "$S/sdlc/scripts/lock_done_when.py" sign --by human done_when.yaml >/dev/null
echo "# tamper" >> done_when.yaml && git add done_when.yaml
expect "locked file staged without proposal rejected" 1 py "$VC" --msg "chore(contract): tweak" --lock .done_when.lock
echo "p" > change-proposal-001.md && git add change-proposal-001.md
expect "locked file with proposal passes (flag)" 0 py "$VC" --msg "chore(contract): tweak per proposal" --lock .done_when.lock
# dogfood 2026-09-05 (I-52): adding the frozen bytes themselves (content hash == lock) is not a locked-file change
git reset -q . ; git checkout -q -- done_when.yaml; rm -f change-proposal-001.md
git rm -q --cached done_when.yaml && git -c user.name=t -c user.email=t@t commit -q -m "chore(contract): untrack contract for lock test" && git add done_when.yaml
expect "first add of the exact locked content passes the lock check (I-52)" 0 py "$VC" --msg "docs(contract): add frozen contract" --lock .done_when.lock
git -c user.name=t -c user.email=t@t commit -q -m "docs(contract): add frozen contract"
git reset -q . ; git checkout -q -- done_when.yaml; rm -f change-proposal-001.md
# dogfood 2026-09-06 (pre-review cr-001): the landing-content exemption must read the RANGE HEAD, never the base.
# A one-ref --range is legal for `git diff` but ambiguous here, so it is refused instead of silently comparing
# the wrong side (which let a tampered locked file hash equal to its own pre-change blob and pass).
echo "# smuggled" >> done_when.yaml
git add done_when.yaml && git -c user.name=t -c user.email=t@t commit -q -m "chore(contract): smuggle"
expect "tampered locked file in an A..B range is rejected (cr-001 twin)" 1 py "$VC" --msg "chore(contract): smuggle" --lock .done_when.lock --range HEAD~1..HEAD --allow-main
expect "single-ref --range refused, never fail-open (cr-001)" 2 py "$VC" --msg "chore(contract): smuggle" --lock .done_when.lock --range main --allow-main
expect "three-dot range resolves the head side (cr-001)" 1 py "$VC" --msg "chore(contract): smuggle" --lock .done_when.lock --range HEAD~1...HEAD --allow-main
# dogfood 2026-09-06 (pre-review cr-004 + fix-verifier): `A..` / `A...` are legal ranges whose right endpoint
# defaults to HEAD; splitting on the separator yields "" and `git show :path` reads the INDEX — the wrong side.
# The mutant only shows itself when the index differs from the range head, so stage the FROZEN bytes while the
# tamper sits at HEAD. (The first version of these twins committed the tamper, leaving index == HEAD, and passed
# on the buggy resolver too — a decorative test. fix-verifier caught it; this is the shape that kills the mutant.)
git checkout -q HEAD~1 -- done_when.yaml && git add done_when.yaml
expect "open-ended A.. reads the range head, not the index (cr-004)" 1 py "$VC" --msg "chore(contract): smuggle" --lock .done_when.lock --range "HEAD~1.." --allow-main
expect "open-ended A... reads the range head, not the index (cr-004)" 1 py "$VC" --msg "chore(contract): smuggle" --lock .done_when.lock --range "HEAD~1..." --allow-main
expect "empty --range is refused, not treated as staged mode (fix-verifier)" 2 py "$VC" --msg "chore(contract): smuggle" --lock .done_when.lock --range "" --allow-main
git reset -q --hard HEAD~1 >/dev/null
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
# dogfood 2026-09-05 (I-04 / I-05): template guidance in blockquotes must not count as steps; vocab regex must not
# swallow the Domain Model body when the body mentions "Domain Model" again
expect "verify_derived: Domain Model body mentioning 'Domain Model' again still yields vocabulary (I-05)" 0 python3 -c "
import importlib.util,sys
spec=importlib.util.spec_from_file_location('vd','$S/psl-derive/scripts/verify_derived.py'); vd=importlib.util.module_from_spec(spec); spec.loader.exec_module(vd)
psl='# PSL-x\n\n## Domain Model [Σ]\n\n| Ring | x | y |\n| Part | x | y |\n\n（Domain Model 推翻测试：照此建库）\n\n## State Machine\n\n- Era: a → b\n\nPSL-001 rule\n'
ids,vocab=vd.psl_ids_and_vocab(psl); assert 'Ring' in vocab and 'Part' in vocab, vocab"
DG2="$TMP/derived_good_bq"; cp -R "$FXD/derived_good" "$DG2"; printf '%s\n%s\n' '> 禁止 Step 1/2/3、步骤 N、阶段 N、首先/然后/接着/最后 串。' "$(cat "$DG2/workflow.md")" > "$DG2/workflow.md"
expect "verify_derived: template guidance blockquote quoting banned tokens is not a violation (I-04)" 0 py "$S/psl-derive/scripts/verify_derived.py" "$DG2" --psl "$FXD/PSL-memory-time-search.md"
DG3="$TMP/derived_badid"; cp -R "$FXD/derived_good" "$DG3"; printf '\n- [F-13a] a suffixed id that the old regex skipped ← PSL-001\n' >> "$DG3/form-draft.md"
expect "verify_derived: suffixed decision id (F-13a) rejected instead of silently skipped (I-47)" 1 py "$S/psl-derive/scripts/verify_derived.py" "$DG3" --psl "$FXD/PSL-memory-time-search.md"

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
expect "gate g1 reject with derivation_error does NOT bump world (I-34)" 0 bash -c "python3 '$SS' gate g1 --verdict reject --by human --attribution derivation_error >/dev/null && python3 '$SS' show | grep -q '\"world\": 1'"
expect "gate g1 pass after a reject clears the stale attribution (I-51)" 0 bash -c "python3 '$SS' gate g1 --verdict pass --by human >/dev/null && ! python3 '$SS' show | grep -q 'derivation_error'"
# dogfood 2026-09-05 (I-17): a delegated signature needs an authorization on record and is traced as agent:, not human:
expect "gate: delegated_agent without --authorization refused" 1 py "$SS" gate g3 --verdict pass --by proxy-bot --signer-kind delegated_agent
expect "gate: delegated_agent with authorization recorded as agent:<by> + [delegated]" 0 bash -c "python3 '$SS' gate g3 --verdict pass --by proxy-bot --signer-kind delegated_agent --authorization 'user said so' >/dev/null && grep -q 'agent:proxy-bot' .sdlc/demo-psl/trace.jsonl && grep -q '\[delegated\]' .sdlc/demo-psl/ledger.md"
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

echo "== sdlc / graph + loops as data (P1)"
SSG="$S/sdlc/scripts"
expect "verify_graph: shipped graph passes 5 lints" 0 py "$SSG/verify_graph.py" --stages "intake,track,issue,branch,contract,g2,cards,implement,acceptance,pr,review,g3,merge,release,archive"
GB="$TMP/graph_bad"; mkdir -p "$GB"
python3 - "$S/sdlc/assets/graph.yaml" "$GB" <<'PYEOF'
import sys, yaml, copy
g=yaml.safe_load(open(sys.argv[1])); out=sys.argv[2]
def dump(name,doc): yaml.safe_dump(doc,open(f"{out}/{name}.yaml","w"),allow_unicode=True,sort_keys=False)
b=copy.deepcopy(g); [n.update(writes=["**"]) for n in b["nodes"] if n["id"]=="implement"]; dump("unbounded_writes",b)
b=copy.deepcopy(g); [e.pop("loop",None) for e in b["edges"] if e.get("type")=="loop_back" and e.get("signal")=="card_test_fail"]; dump("loop_without_contract",b)
b=copy.deepcopy(g); b["edges"].append({"from":"acceptance-fleet","to":"stage.implement","type":"handoff","carries":["findings","verdict"]}); dump("evaluator_leaks",b)
b=copy.deepcopy(g); [n.pop("resume_binding",None) for n in b["nodes"] if n["id"]=="human.g2"]; dump("human_no_resume",b)
b=copy.deepcopy(g); [e.pop("merge",None) for e in b["edges"] if e.get("type")=="fan_in"]; dump("fanin_no_merge",b)
b=copy.deepcopy(g); b["edges"].append({"from":"commit","to":"implement","type":"handoff"}); dump("unowned_cycle",b)
PYEOF
expect "verify_graph: unbounded writes rejected" 1 py "$SSG/verify_graph.py" "$GB/unbounded_writes.yaml" --loops "$S/sdlc/assets/loops.yaml"
expect "verify_graph: loop_back without loop id rejected" 1 py "$SSG/verify_graph.py" "$GB/loop_without_contract.yaml" --loops "$S/sdlc/assets/loops.yaml"
expect "verify_graph: evaluator→implementer carrying findings rejected" 1 py "$SSG/verify_graph.py" "$GB/evaluator_leaks.yaml" --loops "$S/sdlc/assets/loops.yaml"
expect "verify_graph: human node without resume_binding rejected" 1 py "$SSG/verify_graph.py" "$GB/human_no_resume.yaml" --loops "$S/sdlc/assets/loops.yaml"
expect "verify_graph: fan_in without merge rejected" 1 py "$SSG/verify_graph.py" "$GB/fanin_no_merge.yaml" --loops "$S/sdlc/assets/loops.yaml"
expect "verify_graph: cycle without loop_back rejected (SCC named)" 0 bash -c "python3 '$SSG/verify_graph.py' '$GB/unowned_cycle.yaml' --loops '$S/sdlc/assets/loops.yaml' | grep -q 'cycle without a loop_back edge'"
expect "verify_loop: shipped loops pass" 0 py "$SSG/verify_loop.py"
LB="$TMP/loops_bad"; mkdir -p "$LB"
python3 - "$S/sdlc/assets/loops.yaml" "$LB" <<'PYEOF'
import sys, yaml, copy
d=yaml.safe_load(open(sys.argv[1])); out=sys.argv[2]
b=copy.deepcopy(d); b["loops"][0]["verifier"]=b["loops"][0]["generator"]; yaml.safe_dump(b,open(f"{out}/self_verify.yaml","w"),allow_unicode=True,sort_keys=False)
b=copy.deepcopy(d); b["loops"][0]["stop"].pop("impossible"); yaml.safe_dump(b,open(f"{out}/missing_stop_key.yaml","w"),allow_unicode=True,sort_keys=False)
b=copy.deepcopy(d); b["loops"][0]["stop"]["budget"]={"ref":"routing:budgets.<track>.nonexistent"}; yaml.safe_dump(b,open(f"{out}/bad_budget_ref.yaml","w"),allow_unicode=True,sort_keys=False)
PYEOF
expect "verify_loop: generator == verifier rejected" 1 py "$SSG/verify_loop.py" "$LB/self_verify.yaml" --routing "$S/sdlc/assets/routing.yaml"
expect "verify_loop: missing stop key rejected" 1 py "$SSG/verify_loop.py" "$LB/missing_stop_key.yaml" --routing "$S/sdlc/assets/routing.yaml"
expect "verify_loop: unresolvable budget.ref rejected" 1 py "$SSG/verify_loop.py" "$LB/bad_budget_ref.yaml" --routing "$S/sdlc/assets/routing.yaml"
expect "graph check: ORDER == graph.yaml stages" 0 py "$SS" graph check
expect "graph render emits mermaid with loop labels" 0 bash -c "python3 '$SS' graph render | grep -q 'flowchart TD' && python3 '$SS' graph render | grep -q 'card_retry'"
expect "triggers.yaml: every trigger names a declared loop" 0 python3 -c "
import yaml,sys
L={l['id'] for l in yaml.safe_load(open('$S/sdlc/assets/loops.yaml'))['loops']}
T=[t['loop'] for t in yaml.safe_load(open('$S/sdlc/assets/triggers.yaml'))['triggers']]
missing=[t for t in T if t not in L]; assert not missing, missing"

echo "== sdlc / convergence detection + clean state (P2)"
ST3="$TMP/state-conv"; mkdir -p "$ST3"; pushd "$ST3" >/dev/null
git init -q -b main . 2>/dev/null; git -c user.name=t -c user.email=t@t commit -q --allow-empty -m "chore: init"
py "$SS" init --slug conv --title "convergence" --track task >/dev/null
py "$SS" set track=task >/dev/null; py "$SS" card CARD-01 --status doing >/dev/null
RB="$TMP/routing_big.yaml"; python3 -c "
import yaml; d=yaml.safe_load(open('$S/sdlc/assets/routing.yaml'))
for t in d['budgets']: d['budgets'][t]['card_retries']=10
yaml.safe_dump(d,open('$RB','w'),allow_unicode=True,sort_keys=False)"
expect "oscillation: A B A → not yet (budget 10 so convergence, not budget, decides)" 0 bash -c "python3 '$SS' fail --signal card_test_fail --card CARD-01 --fingerprint A --routing '$RB' >/dev/null; python3 '$SS' fail --signal card_test_fail --card CARD-01 --fingerprint B --routing '$RB' >/dev/null; python3 '$SS' fail --signal card_test_fail --card CARD-01 --fingerprint A --routing '$RB' | grep -q '\"escalate\": false'"
expect "oscillation: A B A B → escalate with derived oscillation_detected → plan" 0 bash -c "python3 '$SS' fail --signal card_test_fail --card CARD-01 --fingerprint B --routing '$RB' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['escalate'] and d['derived_signal']=='oscillation_detected' and d['layer']=='plan' and d['convergence']['type']=='oscillation', d\""
expect "pending.failure_report set after escalation" 0 bash -c "python3 '$SS' show | grep -q '\"failure_report\": true'"
expect "check-clean dirty (pending report) → exit 1" 1 py "$SS" check-clean
expect "check-clean --as-hook emits block decision" 0 bash -c "python3 '$SS' check-clean --as-hook | grep -q '\"decision\": \"block\"'"
echo "# report" > .sdlc/conv/failure-report-001.md
expect "report clears pending" 0 py "$SS" report --path .sdlc/conv/failure-report-001.md
expect "check-clean: doing card + dirty tree → exit 1" 1 bash -c "echo x > dirty.txt && python3 '$SS' check-clean"
rm -f dirty.txt
expect "check-clean clean → exit 0" 0 py "$SS" check-clean
py "$SS" card CARD-02 --status doing >/dev/null
expect "plateau: score 3× not above best → derived plateau → plan" 0 bash -c "for i in 1 2 3 4; do python3 '$SS' fail --signal card_test_fail --card CARD-02 --fingerprint p\$i --score 0.5 --routing '$RB' >'$TMP/last.json'; done; python3 -c \"import json; d=json.load(open('$TMP/last.json')); assert d['derived_signal']=='plateau' and d['layer']=='plan' and d['convergence']['type']=='plateau', d\""
py "$SS" report --path .sdlc/conv/failure-report-001.md >/dev/null
expect "impossible_under_contract by implementer rejected" 1 py "$SS" fail --signal impossible_under_contract --by implement
expect "impossible_under_contract by acceptance-fleet → task, human" 0 bash -c "python3 '$SS' fail --signal impossible_under_contract --by acceptance-fleet --evidence 'AC-003 contradicts AC-001' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['layer']=='task' and d['escalate_to']=='human' and d['rule']=='R16', d\""
expect "trace.jsonl written with typed edges" 0 bash -c "test -s .sdlc/conv/trace.jsonl && grep -q '\"caused_by\"' .sdlc/conv/trace.jsonl"
expect "trace lint on live run passes" 0 py "$SSG/trace.py" lint --root .sdlc --slug conv --routing "$S/sdlc/assets/routing.yaml"
expect "trace why CARD-01 walks fail → reflow" 0 bash -c "python3 '$SSG/trace.py' why CARD-01 --root .sdlc --slug conv | grep -q 'reflow'"
expect "loops: six rows with budget consumption" 0 bash -c "python3 '$SS' loops --slug conv --json | python3 -c \"import json,sys; d=json.load(sys.stdin); ids=[l['loop'] for l in d['loops']]; assert len(ids)==6 and 'card_retry' in ids and d['loops'][0]['used'] is not None, d\""
expect "ledger --ref with unknown edge type rejected" 1 py "$SS" ledger --kind note --note x --ref bogus:CARD-01
expect "archive copies trace.jsonl" 0 bash -c "python3 '$SS' archive --to specs/conv >/dev/null && test -f specs/conv/trace.jsonl"
popd >/dev/null

echo "== pr / --pre-review (P2)"
pushd "$R" >/dev/null
expect "pre-review: Known issues with file:line passes" 0 py "$VP" --body "$FXP/good_body_prereview.md" --base main --skip-preflight --allow-xl --pre-review
expect "pre-review: missing Known issues rejected" 1 py "$VP" --body "$FXP/good_body.md" --base main --skip-preflight --allow-xl --pre-review
expect "pre-review: P0 in Known issues rejected" 1 py "$VP" --body "$FXP/bad_prereview_p0.md" --base main --skip-preflight --allow-xl --pre-review
expect "pre-review: item without file:line rejected" 1 py "$VP" --body "$FXP/bad_prereview_noanchor.md" --base main --skip-preflight --allow-xl --pre-review
expect "without --pre-review the old good body still passes" 0 py "$VP" --body "$FXP/good_body.md" --base main --skip-preflight --allow-xl
popd >/dev/null

echo "== retro / trace metrics (P3)"
expect "metrics: escape chain + contract rework from trace.jsonl" 0 bash -c "python3 '$S/retro/scripts/metrics.py' '$S/retro/eval/fixtures' --json '$TMP/m.json' >/dev/null && python3 -c \"import json; d=json.load(open('$TMP/m.json')); t=d['totals']; assert t['escape_chains']==1 and t['avg_escape_chain_depth']==3.0 and t['escape_root_layers']=={'task':1} and t['contract_rework_ratio']==0.25, t\""
expect "trace why AC-003-a walks 3 hops to hidden_variant_fail" 0 bash -c "python3 '$SSG/trace.py' why AC-003-a --trace '$S/retro/eval/fixtures/feat-a/trace.jsonl' | grep -q 'hidden_variant_fail'"
expect "trace impact AC-003-a reaches the escape" 0 bash -c "python3 '$SSG/trace.py' impact AC-003-a --trace '$S/retro/eval/fixtures/feat-a/trace.jsonl' | grep -q 'escape'"
TB="$TMP/trace_bad.jsonl"; printf '%s\n' '{"id":"ev-0001","at":"t","kind":"fail","refs":[{"type":"related_to","target":"CARD-01"}]}' '{"id":"ev-0002","at":"t","kind":"reflow","refs":[{"type":"caused_by","target":"ev-0099"}]}' > "$TB"
expect "trace lint: unknown edge type + dangling event rejected" 1 py "$SSG/trace.py" lint --trace "$TB"

echo "== tune / tune.py + apply_proposal.py (P4)"
TU="$S/tune/scripts"; FXT="$S/tune/eval/fixtures"
expect "tune: 2 archives + pr-watch → ≥3 proposals, all fields present" 0 bash -c "python3 '$TU/tune.py' '$FXT/archive' --pr-watch '$FXT/pr-watch' --out '$TMP/tune.yaml' >/dev/null && python3 -c \"
import yaml; d=yaml.safe_load(open('$TMP/tune.yaml')); ps=d['proposals']; assert len(ps)>=3, len(ps)
need={'id','target','current','proposed','evidence','expected_delta','risk','verify_by','delivered_as','apply'}
for p in ps: assert need<=set(p), p; assert p['evidence'], p
assert any(p['target']=='review-loop.MAX_ROUNDS' for p in ps); assert any('audit ACCEPT' in str(p['proposed']) for p in ps)\""
expect "tune: 1 archive → baseline only, insufficient_samples" 0 bash -c "python3 '$TU/tune.py' '$FXT/archive-single' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['proposals']==[] and any('insufficient_samples' in n for n in d['notes']), d['notes']\""
expect "apply_proposal --dry-run: MAX_ROUNDS diff against pr-poll.sh" 0 bash -c "python3 '$TU/apply_proposal.py' '$TMP/tune.yaml' --id P-1 --skills-root '$S' 2>/dev/null | grep -q '^-MAX_ROUNDS=\"\${MAX_ROUNDS:-10}\"'"
expect "apply_proposal --patch writes patch, target untouched" 0 bash -c "before=\$(md5 -q '$S/review-loop/scripts/pr-poll.sh' 2>/dev/null || md5sum '$S/review-loop/scripts/pr-poll.sh' | cut -d' ' -f1); python3 '$TU/apply_proposal.py' '$TMP/tune.yaml' --id P-1 --skills-root '$S' --patch '$TMP/p1.patch' >/dev/null && test -s '$TMP/p1.patch' && after=\$(md5 -q '$S/review-loop/scripts/pr-poll.sh' 2>/dev/null || md5sum '$S/review-loop/scripts/pr-poll.sh' | cut -d' ' -f1) && [ \"\$before\" = \"\$after\" ]"
expect "apply_proposal: gate_fix_list kind produces gate.json diff" 0 bash -c "python3 '$TU/apply_proposal.py' '$TMP/tune.yaml' --id P-2 --skills-root '$S' 2>/dev/null | grep -q 'audit ACCEPT'"
expect "apply_proposal: unknown id rejected" 1 py "$TU/apply_proposal.py" "$TMP/tune.yaml" --id P-99 --skills-root "$S"

echo
echo "smoke: $pass passed, $fail failed  (tmp: $TMP)"
[[ $fail -eq 0 ]]
