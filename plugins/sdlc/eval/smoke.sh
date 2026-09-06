#!/usr/bin/env bash
# smoke.sh — run every sdlc script against its fixtures; print PASS/FAIL per expectation.
# This is the L0/structural evidence behind each skill's eval/gate.json (static_only tier).
#
# Usage:
#   bash plugins/sdlc/eval/smoke.sh                      # the whole suite (must end "0 failed")
#   bash plugins/sdlc/eval/smoke.sh --only <ERE>         # only expectations whose label matches
#   bash plugins/sdlc/eval/smoke.sh --mutate <file> <old-string> <new-string>
#
# --mutate is the self-check (I-80): it copies the plugin to a scratch dir TWICE — once unmutated
# as a baseline that must be green, once with the string replacement — and reports the DELTA. An
# expectation already red before the mutation is not evidence of anything (pre-review cr-001).
# Exit 0 killed · 1 survived · 2 the mutation never applied · 3 the baseline was not green.
# It copies the plugin to a scratch dir, applies the string
# mutation there, runs this suite against the copy, and reports which expectations went red.
# Exit 0 = the mutant was killed (at least one expectation caught it); exit 1 = MUTANT SURVIVED.
# A test that passes against both the buggy and the fixed implementation is worse than no test:
# it claims coverage nobody has. Every new expectation for a fail-open fix must come with the
# --mutate output that proves it kills its mutant. <file> is the plugin-relative (or repo-relative,
# or absolute) path of the file to mutate; it must live under plugins/sdlc/.
# Needs python3 + pyyaml, git, jq. Run from the repo root.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
S="$ROOT/skills"
TMP="$(mktemp -d)"
ONLY=""; MUT_FILE=""; MUT_OLD=""; MUT_NEW=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --only) ONLY="${2:-}"; shift 2 ;;
    --mutate) MUT_FILE="${2:-}"; MUT_OLD="${3:-}"; MUT_NEW="${4:-}"; shift 4 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "smoke.sh: unknown argument: $1" >&2; exit 2 ;;
  esac
done
pass=0; fail=0; skipped=0
expect() { # expect <label> <want_exit> <cmd...>
  local label="$1" want="$2"; shift 2
  if [[ -n "$ONLY" ]] && ! [[ "$label" =~ $ONLY ]]; then skipped=$((skipped+1)); return 0; fi
  local out; out="$("$@" 2>&1)"; local rc=$?
  if [[ "$rc" == "$want" ]]; then pass=$((pass+1)); echo "PASS  [$rc] $label"; else fail=$((fail+1)); echo "FAIL  [got $rc want $want] $label"; echo "$out" | head -20 | sed 's/^/      /'; fi
}
py() { python3 "$@"; }

if [[ -n "$MUT_FILE" ]]; then
  # --- mutation self-check (I-80): does the suite kill this mutant? ---------------------
  COPY="$TMP/mutant/sdlc"; mkdir -p "$TMP/mutant"; cp -R "$ROOT" "$COPY"
  case "$MUT_FILE" in
    /*)            REL="${MUT_FILE#"$ROOT"/}" ;;
    plugins/sdlc/*) REL="${MUT_FILE#plugins/sdlc/}" ;;
    *)             REL="$MUT_FILE" ;;
  esac
  TARGET="$COPY/$REL"
  [[ -f "$TARGET" ]] || { echo "smoke.sh --mutate: no such file under $ROOT: $MUT_FILE" >&2; exit 2; }
  python3 - "$TARGET" "$MUT_OLD" "$MUT_NEW" <<'PYEOF' || exit 2
import sys
p, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(p, encoding="utf-8").read()
n = s.count(old)
if n == 0:
    sys.stderr.write("smoke.sh --mutate: old string not found in %s: %r\n" % (p, old)); sys.exit(2)
open(p, "w", encoding="utf-8").write(s.replace(old, new))
sys.stderr.write("mutation applied: %d occurrence(s) of %r → %r in %s\n" % (n, old, new, p))
PYEOF
  echo "== mutation self-check: $REL"
  # A "killed" verdict means: an expectation that was GREEN before the mutation is RED after it.
  # Grepping the mutant run for any FAIL line does not mean that. The copy comes from the working
  # tree, so an expectation that was already red — a half-finished edit, an unrelated breakage —
  # would make every mutant look killed, and this tool is what every mutation proof in the register
  # rests on (found by PR pre-review, cr-001 against the harness itself).
  BASE_LOG="$TMP/mutant-baseline.log"; LOG="$TMP/mutant-run.log"
  BASE_COPY="$TMP/baseline/sdlc"; mkdir -p "$TMP/baseline"; cp -R "$ROOT" "$BASE_COPY"
  SMOKE_NESTED=1 bash "$BASE_COPY/eval/smoke.sh" ${ONLY:+--only "$ONLY"} >"$BASE_LOG" 2>&1 || true
  BASE_FAIL="$(grep -cE '^FAIL ' "$BASE_LOG" || true)"
  if [[ "${BASE_FAIL:-0}" -gt 0 ]]; then
    echo "BASELINE NOT GREEN — $BASE_FAIL expectation(s) already fail before the mutation:"
    grep -E '^FAIL ' "$BASE_LOG" | sed 's/^/  /'
    echo "A mutation proof over a red baseline proves nothing: every mutant would look killed."
    echo "(baseline log: $BASE_LOG)"
    exit 3
  fi
  SMOKE_NESTED=1 bash "$COPY/eval/smoke.sh" ${ONLY:+--only "$ONLY"} >"$LOG" 2>&1 || true
  tail -1 "$LOG"
  # the delta, not the absolute set: labels red after and green before
  KILLERS="$(python3 - "$BASE_LOG" "$LOG" <<'PYDELTA'
import re, sys
def failed(path):
    out = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"^FAIL\s+\[[^\]]*\]\s+(.*)$", line.rstrip("\n"))
        if m:
            out[m.group(1)] = line.rstrip("\n")
    return out
before, after = failed(sys.argv[1]), failed(sys.argv[2])
for label, line in after.items():
    if label not in before:
        print(line)
PYDELTA
)"
  if [[ -z "$KILLERS" ]]; then
    echo "MUTANT SURVIVED — no expectation went from green to red."
    echo "A test that passes against both implementations claims coverage it does not have (I-80)."
    echo "(baseline: $BASE_LOG · mutant: $LOG)"
    exit 1
  fi
  echo "mutant killed by:"; echo "$KILLERS" | sed 's/^/  /'
  exit 0
fi

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
# dogfood 2026-09-05 (I-45): the negation cross-check only works if the G1 template's documented shape
# is the shape verify_issue.py reads. Derive the record from the template itself so the two cannot drift:
# un-blockquoting the template's worked example is exactly what an author does when filling it in.
G1T="$S/sdlc/assets/g1_record.md"
G1F="$TMP/g1_filled.md"; sed 's|^> - |- |' "$G1T" > "$G1F"
PSLI2="$TMP/psl_issue_banned.md"; sed 's|^- do: |- do: report each finding once; |' "$PSLI" > "$PSLI2"
expect "G1 record written to the template's 明确不做 shape arms the issue cross-check (I-45)" 0 bash -c "python3 '$S/issue/scripts/verify_issue.py' '$PSLI2' --dos '$FX/dos.yaml' --g1 '$G1F' | grep -q 'uses \`finding\`, which the G1 record lists under 明确不做'"
# I-22: the record's primary attribution is what the operator types into `gate --attribution`. If the
# template names a value the script does not accept, the record and the counter disagree silently.
cat > "$TMP/attr_agree.py" <<'ATTREOF'
import re, sys
tpl = open(sys.argv[1], encoding='utf-8').read()
sec = re.search(r'^## 归因.*?(?=^## )', tpl, re.S | re.M).group(0)
named = set(re.findall(r'`([a-z_]+_error)`', sec))
script = open(sys.argv[2], encoding='utf-8').read()
ok = set(re.findall(r'[\x27\x22]([a-z_]+_error)[\x27\x22]',
                    re.search(r'--attribution.{0,12}choices=\[([^\]]*)\]', script).group(1)))
# both directions: nothing named that the script rejects, and nothing the script accepts left
# unoffered — a template that lists only one cause is the single-value design I-22 is about
assert named == ok, (sorted(named), sorted(ok))
ATTREOF
expect "the G1 template and sdlc_state.py name the same attribution values (I-22)" 0 py "$TMP/attr_agree.py" "$S/sdlc/assets/g1_record.md" "$S/sdlc/scripts/sdlc_state.py"
# dogfood 2026-09-06 (I-22, second half): a rejection with two honest causes records both, and the
# world counter still moves by exactly one — counting both would stop it meaning "the world changed".
ATTR="$TMP/attr"; mkdir -p "$ATTR"; pushd "$ATTR" >/dev/null
py "$S/sdlc/scripts/sdlc_state.py" init --slug t --title T --track psl >/dev/null
expect "a reject records a secondary cause beside the primary (I-22)" 0 bash -c "python3 '$S/sdlc/scripts/sdlc_state.py' gate --slug t g1 --verdict reject --signer-kind human --by g1 --attribution rule_error --secondary-attribution derivation_error >/dev/null && python3 -c \"import json; g=json.load(open('.sdlc/t/state.json')); assert g['gates']['g1']['secondary_attribution']==['derivation_error'] and g['counters']['world']==1, g\""
expect "a secondary equal to the primary is refused (I-22)" 1 py "$S/sdlc/scripts/sdlc_state.py" gate --slug t g1 --verdict reject --signer-kind human --by g1 --attribution rule_error --secondary-attribution rule_error
expect "a secondary without a primary is refused (I-22)" 1 py "$S/sdlc/scripts/sdlc_state.py" gate --slug t g2 --verdict reject --signer-kind human --by g2 --secondary-attribution rule_error
popd >/dev/null
expect "an unfilled G1 template yields no terms and says the wording cannot be checked (I-45)" 0 bash -c "python3 '$S/issue/scripts/verify_issue.py' '$PSLI2' --dos '$FX/dos.yaml' --g1 '$G1T' | grep -q 'no machine-readable'"
# dogfood 2026-09-06 (I-60 handover): the enforcement half was closed when the negation check learned
# to read both files; this is the instruction half. An operator reading the record must be able to
# learn where a post-signature clarification goes, and the two templates must not claim the same act.
expect "the G1 record points at the interpretations file (I-60)" 0 bash -c "grep -q 'g1-interpretations' '$S/sdlc/assets/g1_record.md'"
expect "the interpretations template sends re-signatures back to the record (I-60)" 0 bash -c "grep -q '补签' '$S/sdlc/assets/g1_interpretations.md' && grep -q 'g1-record' '$S/sdlc/assets/g1_interpretations.md'"
expect "sign refuses to lock the interpretations file (I-60)" 2 bash -c "cd \"\$(mktemp -d)\" && printf 'x' > g1-interpretations.md && python3 '$S/sdlc/scripts/lock_done_when.py' sign --signer-kind human --by human --stage g2 --out .l g1-interpretations.md"

echo "== plan-cards / lint_cards.py"
FX="$S/sdlc/eval/fixtures"
expect "bad cards rejected (dup REQ, overlap, missing REQ-003, ac_ids, dos closure, context)" 1 py "$S/plan-cards/scripts/lint_cards.py" "$S/plan-cards/eval/fixtures/cards_bad" --spec "$FX/spec.md" --done-when "$FX/done_when.yaml" --dos "$FX/dos.yaml"
expect "good cards pass" 0 py "$S/plan-cards/scripts/lint_cards.py" "$S/plan-cards/eval/fixtures/cards_good" --spec "$FX/spec.md" --done-when "$FX/done_when.yaml" --dos "$FX/dos.yaml"
# I-73: a projection and its data source must not straddle a card seam — no implementer can change both
# sides atomically, and in the ring-audit run 4 of 12 fix-round findings came from exactly that.
PC="$S/plan-cards/eval/fixtures"
expect "cards: projection owning its data (or declaring the seam) passes (I-73)" 0 py "$S/plan-cards/scripts/lint_cards.py" "$PC/cards_projection_good" --spec "$FX/spec.md" --done-when "$FX/done_when.yaml" --dos "$FX/dos.yaml"
expect "cards: projection across a card seam rejected, undeclared reads_from rejected (I-73)" 0 bash -c "python3 '$S/plan-cards/scripts/lint_cards.py' '$PC/cards_projection_bad' --spec '$FX/spec.md' --done-when '$FX/done_when.yaml' --dos '$FX/dos.yaml' > '$TMP/pc_bad.json'; [ \$? = 1 ] || exit 9; python3 -c \"import json; r=json.load(open('$TMP/pc_bad.json'))['rejects']; j=' | '.join(r); assert 'CARD-02 renders' in j and 'audit.yaml' in j and 'CARD-01 owns it' in j and 'does not depends_on CARD-01' in j, j; assert 'CARD-03 owns projection script' in j and 'declares no' in j and 'reads_from' in j, j\""
expect "cards: a declared seam with no note in notes is rejected (I-73)" 1 bash -c "mkdir -p '$TMP/pcnote' && cp '$PC/cards_projection_good/'*.yaml '$TMP/pcnote/' && python3 -c \"import yaml; p='$TMP/pcnote/CARD-02.yaml'; d=yaml.safe_load(open(p)); d.pop('notes', None); yaml.safe_dump(d, open(p,'w'), allow_unicode=True)\" && python3 '$S/plan-cards/scripts/lint_cards.py' '$TMP/pcnote' --spec '$FX/spec.md' --done-when '$FX/done_when.yaml' --dos '$FX/dos.yaml'"
expect "cards: --repo-root reads the script and catches an undeclared source (I-73)" 0 bash -c "python3 '$S/plan-cards/scripts/lint_cards.py' '$PC/cards_projection_bad' --spec '$FX/spec.md' --done-when '$FX/done_when.yaml' --dos '$FX/dos.yaml' --repo-root '$PC/repo' > '$TMP/pc_scan.json'; [ \$? = 1 ] || exit 9; python3 -c \"import json; r=json.load(open('$TMP/pc_scan.json'))['rejects']; j=' | '.join(r); assert 'commit-window.json' in j and 'owned by CARD-01' in j and 'undeclared seam' in j, j\""

echo "== sdlc / lock_done_when.py"
L="$TMP/lock"; mkdir -p "$L"; cp "$FX/done_when.yaml" "$L/"; pushd "$L" >/dev/null
expect "sign writes lock" 0 py "$S/sdlc/scripts/lock_done_when.py" sign --signer-kind human --by tester done_when.yaml
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
expect "gate g2 pass refused without lock.path" 1 py "$SS" gate g2 --verdict pass --signer-kind human --by human
py "$S/sdlc/scripts/lock_done_when.py" sign --signer-kind human --by human done_when.yaml >/dev/null
expect "set lock.path" 0 py "$SS" set lock.path=.done_when.lock lock.signed_by=human
expect "gate g2 pass" 0 py "$SS" gate g2 --verdict pass --signer-kind human --by human
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
expect "gate g1 reject without attribution refused" 1 py "$SS" gate g1 --verdict reject --signer-kind human --by human
expect "set pr/review/merge → advance to merge" 0 bash -c "python3 '$SS' set pr.number=7 >/dev/null && python3 '$SS' advance review >/dev/null && python3 '$SS' set review.done=true gates.g3.required=false >/dev/null && python3 '$SS' advance merge >/dev/null && python3 '$SS' set merge.sha=deadbeef >/dev/null"
expect "advance release" 0 py "$SS" advance release
expect "advance archive refused (release not done)" 1 py "$SS" advance archive
expect "set release.done → advance archive" 0 bash -c "python3 '$SS' set release.version=0.1.0 release.tag=v0.1.0 release.done=true >/dev/null && python3 '$SS' advance archive"
expect "ledger has waiver row" 0 bash -c "grep -q '| waiver |' .sdlc/demo/ledger.md"
# dogfood 2026-09-06 (I-57): state.schema.json defines lock.stage, so the l5 re-sign must be able to record it
expect "set lock.stage=l5 (I-57)" 0 bash -c "python3 '$SS' set lock.stage=l5 >/dev/null && python3 -c \"import json; assert json.load(open('.sdlc/demo/state.json'))['lock']['stage']=='l5'\""
expect "lock.stage outside the g2|l5 enum refused (I-57)" 1 py "$SS" set lock.stage=nope
# dogfood 2026-09-06 (I-67): a waiver needs no stage transition to hang on; `waive` prints the id to cite
expect "waive records a standalone waiver + ledger event (I-67)" 0 bash -c "python3 '$SS' waive --signal hidden_variant_fail --reason 'holdout 6/10 accepted as a ratchet item' --signer-kind human --by g2-judge --fingerprint d1fc8380957b > '$TMP/waive.json' && python3 -c \"
import json
assert json.load(open('$TMP/waive.json'))['event'].startswith('ev-')
w=json.load(open('.sdlc/demo/state.json'))['waivers']
assert any(x.get('signal')=='hidden_variant_fail' and x.get('fingerprint')=='d1fc8380957b' for x in w), w\""
expect "waive by a delegated agent without --authorization refused (I-67)" 1 py "$SS" waive --signal card_test_fail --reason r --signer-kind human --by proxy-bot --signer-kind delegated_agent
# dogfood 2026-09-06 (I-70): a hand-written row must be able to cite the fail it excuses, not describe it in prose
expect "ledger --fingerprint / --card land on the trace event (I-70)" 0 bash -c "python3 '$SS' ledger --kind note --note 'the waiver above excuses this fail' --fingerprint d1fc8380957b --card CARD-01 >/dev/null && python3 -c \"
import json
ev=[json.loads(l) for l in open('.sdlc/demo/trace.jsonl') if l.strip()][-1]
assert ev.get('fingerprint')=='d1fc8380957b' and ev.get('card')=='CARD-01', ev\""
# dogfood 2026-09-06 (I-83): the review exit is a closed enum, and 'waived' / any exit_reason must cite a waiver event
expect "review.done=waived without a waiver_ref refused (I-83)" 1 py "$SS" set review.done=waived
expect "review.done=true beside a free-text exit_reason refused (I-83)" 1 py "$SS" set review.exit_reason="waived by a judge, not passed"
expect "review.waiver_ref must resolve to a trace event (I-83)" 1 py "$SS" set review.done=waived review.waiver_ref=ev-9999
expect "review.done outside the closed enum refused (I-83)" 1 py "$SS" set review.done=maybe
expect "waived review exit citing its waiver event accepted (I-83)" 0 bash -c "WID=\$(python3 '$SS' waive --signal review_non_convergence --reason 'APPROVED unobtainable: the author cannot approve their own PR' --signer-kind human --by human | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"event\"])') && python3 '$SS' set review.done=waived review.waiver_ref=\$WID review.exit_reason='structural non-convergence' >/dev/null && python3 -c \"
import json
r=json.load(open('.sdlc/demo/state.json'))['review']
assert r['done']=='waived' and r['waiver_ref'].startswith('ev-'), r\""
expect "prereqs: a waived review exit still opens g3, an open one does not (I-83)" 0 python3 -c "
import importlib.util; spec=importlib.util.spec_from_file_location('ss','$SS'); ss=importlib.util.module_from_spec(spec); spec.loader.exec_module(ss)
assert ss.prereqs({'stage':'review','review':{'done':'waived','waiver_ref':'ev-0001'},'gates':{}},'g3')==[]
assert ss.prereqs({'stage':'review','review':{'done':True},'gates':{}},'g3')==[]
assert ss.prereqs({'stage':'review','review':{},'gates':{}},'g3'), 'an open review must not open g3'"
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
py "$S/sdlc/scripts/lock_done_when.py" sign --signer-kind human --by human done_when.yaml >/dev/null
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
# dogfood 2026-09-06 (I-61): a card's diff can be clean against the lock while the working tree it
# went green against is not. The green is real but it does not prove the frozen criteria.
UNL="$TMP/unlocked"; mkdir -p "$UNL/tests" "$UNL/cards" "$UNL/src"; pushd "$UNL" >/dev/null
git init -q .; git config user.email t@t; git config user.name t
printf 'acceptance:\n  - id: AC-001-a\n' > done_when.yaml; printf "test('x')\n" > tests/a.test.ts
printf 'id: CARD-01\nallowed_files:\n- src/x.py\nforbidden_files: []\n' > cards/CARD-01.yaml; echo "x=1" > src/x.py
git add -A; git -c user.name=t -c user.email=t@t commit -qm "feat: base"
py "$S/sdlc/scripts/lock_done_when.py" sign --signer-kind human --by human --stage l5 --out .done_when.lock done_when.yaml tests/a.test.ts >/dev/null
printf "test('x'); test('y')\n" > tests/a.test.ts; echo "x=2" > src/x.py; git add src/x.py
expect "a card going green against tests that drifted from the lock is flagged (I-61)" 0 bash -c "python3 '$S/commit/scripts/verify_commit.py' --msg 'feat(x): change' --card cards/CARD-01.yaml --lock .done_when.lock --allow-main | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['verdict']=='PASS' and any('tests_unlocked_at_green' in f for f in d['flags']), d\""
git checkout -q -- tests/a.test.ts
expect "no flag once the tree matches the lock again (I-61)" 0 bash -c "python3 '$S/commit/scripts/verify_commit.py' --msg 'feat(x): change' --card cards/CARD-01.yaml --lock .done_when.lock --allow-main | python3 -c \"import json,sys; d=json.load(sys.stdin); assert not any('tests_unlocked_at_green' in f for f in d['flags']), d['flags']\""
popd >/dev/null
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
# dogfood 2026-09-06 (I-63): changed_with_proposal must print the SET, not just a verdict — which locked
# paths changed, and whether the staged proposal names each one. The human reviewing the proposal was
# computing that intersection by hand across 26 locked paths.
git checkout -q -- done_when.yaml 2>/dev/null; git reset -q .
echo "# tamper" >> done_when.yaml && git add done_when.yaml
echo "we should relax something" > change-proposal-001.md && git add change-proposal-001.md
expect "lock output names the changed locked paths (I-63)" 0 bash -c "python3 '$VC' --msg 'chore(contract): tweak' --lock .done_when.lock | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['lock_detail']['locked_changed']==['done_when.yaml'], d['lock_detail']\""
expect "proposal that never names the path is flagged (I-63)" 0 bash -c "python3 '$VC' --msg 'chore(contract): tweak' --lock .done_when.lock | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['lock_detail']['proposal_missing_path']==['done_when.yaml']; assert any('proposal_missing_path' in f for f in d['flags'])\""
echo "change done_when.yaml threshold to 0.9" > change-proposal-001.md && git add change-proposal-001.md
expect "proposal that names the path clears the flag (I-63)" 0 bash -c "python3 '$VC' --msg 'chore(contract): tweak' --lock .done_when.lock | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['lock_detail']['proposal_missing_path']==[], d['lock_detail']; assert not any('proposal_missing_path' in f for f in d['flags'])\""
git reset -q . && git checkout -q -- done_when.yaml && rm -f change-proposal-001.md
popd >/dev/null

echo "== commit / commit.sh (the gate and the commit as ONE command, I-50)"
CR="$TMP/commitsh"; mkdir -p "$CR"; pushd "$CR" >/dev/null
git init -q -b feat/9-demo . && git -c user.name=t -c user.email=t@t commit -q --allow-empty -m "chore: init"
git config user.name t && git config user.email t@t
CSH="$S/commit/scripts/commit.sh"
echo "export const a = 1;" > a.ts && git add a.ts
# the defect: verify said REJECT, a pipeline swallowed the exit code, and the commit landed anyway
expect "commit.sh: REJECT exits 1" 1 bash -c "bash '$CSH' --msg 'update stuff' >/dev/null 2>&1"
# self-contained: stages its own file, so it stays load-bearing no matter what earlier expectations did
expect "commit.sh: REJECT leaves HEAD where it was (I-50)" 0 bash -c "echo 'export const r = 0;' > r.ts && git add r.ts && b=\$(git rev-parse HEAD); bash '$CSH' --msg 'update stuff' >/dev/null 2>&1; a=\$(git rev-parse HEAD); git reset -q -- r.ts >/dev/null 2>&1; rm -f r.ts; [ \"\$b\" = \"\$a\" ]"
expect "commit.sh: --dry-run passes the gate without committing" 0 bash -c "b=\$(git rev-parse HEAD); bash '$CSH' --msg 'feat(a): add a' --dry-run >/dev/null 2>&1 && [ \"\$b\" = \"\$(git rev-parse HEAD)\" ]"
expect "commit.sh: PASS commits and reports the sha" 0 bash -c "bash '$CSH' --msg 'feat(a): add a' | grep -q '\"committed\": true' && git log -1 --format=%s | grep -qx 'feat(a): add a'"
# dogfood 2026-09-06 (I-53): a shared checkout may carry another session's commit at HEAD; amending it
# rewrote THEIR message. --amend must declare which subject it expects to find.
echo "export const b = 2;" > b.ts && git add b.ts
expect "commit.sh: --amend without --expect-subject refused (I-53)" 2 bash -c "bash '$CSH' --msg 'feat(a): add a and b' --amend >/dev/null 2>&1"
expect "commit.sh: --amend on someone else's HEAD refused (I-53)" 2 bash -c "bash '$CSH' --msg 'feat(a): add a and b' --amend --expect-subject 'docs(report): their commit' >/dev/null 2>&1"
expect "commit.sh: --amend refusal leaves HEAD subject untouched (I-53)" 0 bash -c "bash '$CSH' --msg 'feat(a): mine' --amend --expect-subject 'docs(report): their commit' >/dev/null 2>&1; git log -1 --format=%s | grep -qx 'feat(a): add a'"
expect "commit.sh: --amend with the matching subject rewrites it" 0 bash -c "bash '$CSH' --msg 'feat(a): add a and b' --amend --expect-subject 'feat(a): add a' >/dev/null && git log -1 --format=%s | grep -qx 'feat(a): add a and b'"
popd >/dev/null

echo "== commit / plugin version sync (CLAUDE.md 三处 version, I-76)"
VR="$TMP/versionsync"; mkdir -p "$VR"; pushd "$VR" >/dev/null
git init -q -b feat/9-demo . && git config user.name t && git config user.email t@t
mkdir -p plugins/demo/.claude-plugin plugins/demo/skills/alpha .claude-plugin
printf -- '---\nname: alpha\nversion: 0.1.0\n---\n\n# alpha\n' > plugins/demo/skills/alpha/SKILL.md
printf '{"name":"demo","version":"0.1.0"}\n' > plugins/demo/.claude-plugin/plugin.json
printf '{"plugins":[{"name":"demo","version":"0.1.0"}]}\n' > .claude-plugin/marketplace.json
git add -A && git commit -q -m "chore: init plugin"
echo "a fix to the skill body" >> plugins/demo/skills/alpha/SKILL.md && git add -A && git commit -q -m "fix(alpha): tweak"
# a version-keyed plugin cache serves <marketplace>/<plugin>/<version>/ — an unbumped fix reaches nobody
expect "skills/** changed with plugin.json version frozen → REJECT in a range (I-76)" 1 py "$VC" --msg "fix(alpha): tweak" --range HEAD~1..HEAD --allow-main
expect "…and the reject names the manifest (I-76)" 0 bash -c "python3 '$VC' --msg 'fix(alpha): tweak' --range HEAD~1..HEAD --allow-main | grep -q 'plugins/demo/.claude-plugin/plugin.json version is still 0.1.0'"
expect "--no-version-sync opts out (I-76)" 0 py "$VC" --msg "fix(alpha): tweak" --range HEAD~1..HEAD --allow-main --no-version-sync
# staged mode only flags: CLAUDE.md itself puts the bump in its own `chore:` commit, so rejecting here
# would reject the workflow the rule prescribes
echo "more" >> plugins/demo/skills/alpha/SKILL.md && git add -A
expect "staged mode flags the missing bump but does not reject (I-76)" 0 bash -c "python3 '$VC' --msg 'fix(alpha): more' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['verdict']=='PASS'; assert any('version is still 0.1.0' in f for f in d['flags']), d['flags']\""
git reset -q --hard HEAD >/dev/null
printf -- '---\nname: alpha\nversion: 0.1.1\n---\n\n# alpha\nfixed\n' > plugins/demo/skills/alpha/SKILL.md
printf '{"name":"demo","version":"0.1.1"}\n' > plugins/demo/.claude-plugin/plugin.json
printf '{"plugins":[{"name":"demo","version":"0.1.1"}]}\n' > .claude-plugin/marketplace.json
git add -A && git commit -q -m "chore: bump demo to v0.1.1"
expect "all three locations bumped → passes (I-76)" 0 py "$VC" --msg "chore: bump demo to v0.1.1" --range HEAD~1..HEAD --allow-main
printf '{"plugins":[{"name":"demo","version":"0.1.0"}]}\n' > .claude-plugin/marketplace.json
git add -A && git commit -q -m "chore: registry drifts"
expect "marketplace.json out of sync with plugin.json → REJECT (I-76)" 1 py "$VC" --msg "chore: registry drifts" --range HEAD~2..HEAD --allow-main
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

echo "== pr / merge-commit subjects + version sync (I-74, I-76)"
MR="$TMP/prmerge"; mkdir -p "$MR"; pushd "$MR" >/dev/null
git init -q -b main . && git config user.name t && git config user.email t@t
echo a > a.txt && git add -A && git commit -q -m "chore: init"
git checkout -q -b feat/42-demo && echo b > b.txt && git add -A && git commit -q -m "feat(search): add relative time parser"
git checkout -q main && echo c > c.txt && git add -A && git commit -q -m "chore: base moves on"
git checkout -q feat/42-demo && git merge -q --no-edit main >/dev/null 2>&1
# dogfood 2026-09-06 (I-74): preflight orders "merge origin/<base> first (no rebase)" when behind, then
# judged git's generated merge subject by Conventional Commits — doing what the gate says failed the gate.
expect "git's merge subject is exempt from the Conventional Commits check (I-74)" 0 py "$VP" --body "$FXP/good_body.md" --base main
expect "…and the merge is reported as a flag, not silently (I-74)" 0 bash -c "python3 '$VP' --body '$FXP/good_body.md' --base main | grep -q 'merge commit(s) in range'"
# the exemption must be by parent count, not by loosening the subject check
echo d > d.txt && git add -A && git commit -q -m "just some words"
expect "a non-merge commit with a bad subject is still rejected (I-74 guard)" 1 py "$VP" --body "$FXP/good_body.md" --base main
git reset -q --hard HEAD~1 >/dev/null
mkdir -p plugins/demo/.claude-plugin plugins/demo/skills/alpha
printf -- '---\nname: alpha\nversion: 0.1.0\n---\n\n# alpha\n' > plugins/demo/skills/alpha/SKILL.md
printf '{"name":"demo","version":"0.1.0"}\n' > plugins/demo/.claude-plugin/plugin.json
git add -A && git commit -q -m "feat(demo): add the alpha skill"
git checkout -q main && git merge -q --no-edit feat/42-demo >/dev/null 2>&1 && git checkout -q feat/42-demo
echo "a fix to the skill body" >> plugins/demo/skills/alpha/SKILL.md && git add -A && git commit -q -m "fix(alpha): tweak"
expect "PR range touching skills/** with a frozen plugin version → REJECT (I-76)" 1 py "$VP" --body "$FXP/good_body.md" --base main --skip-preflight
printf '{"name":"demo","version":"0.1.1"}\n' > plugins/demo/.claude-plugin/plugin.json
git add -A && git commit -q -m "chore: bump demo to v0.1.1"
expect "…the same range with the bump passes (I-76)" 0 py "$VP" --body "$FXP/good_body.md" --base main --skip-preflight
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
# dogfood 2026-09-06 (I-82): an empty statusCheckRollup meant "no CI configured", not "all checks green";
# folding both into checks_green=true made the third clause of the termination predicate vacuously true.
expect "checks green → done, reason says green (I-82)" 0 bash -c "bash '$PP' predicate 7 APPROVED 0 green 3 false | grep -q '\"reason\": \"approved_resolved_green\"'"
expect "no CI configured is NOT rendered as green (I-82)" 0 bash -c "bash '$PP' predicate 7 APPROVED 0 none_configured 0 false | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['done'] is True; assert d['checks']=='none_configured'; assert d['checks_green'] is False; assert d['reason']=='approved_resolved_no_checks'; assert 'vacuous' in d['checks_note']\""
expect "red checks block convergence (I-82)" 20 bash -c "bash '$PP' predicate 7 APPROVED 0 red 2 false >/dev/null"
expect "unreadable rollup is not green either (I-82)" 20 bash -c "bash '$PP' predicate 7 APPROVED 0 unknown 0 false >/dev/null"
# dogfood 2026-09-06 (I-69): GitHub forbids a PR author approving their own PR, so a single-maintainer
# repo can never reach APPROVED — the default predicate cannot converge there at all.
expect "default predicate still demands APPROVED (I-69: solo is never the default)" 20 bash -c "bash '$PP' predicate 7 null 0 green 3 false >/dev/null"
expect "solo without a recorded self-review round does not converge (I-69)" 20 bash -c "SELF_REVIEW=1 bash '$PP' predicate 7 null 0 green 3 false | grep -q no_isolated_self_review_round; SELF_REVIEW=1 bash '$PP' predicate 7 null 0 green 3 false >/dev/null"
git init -q -b feat/9-demo . 2>/dev/null; git config user.name t; git config user.email t@t
git commit -q --allow-empty -m "chore: init" 2>/dev/null
printf 'review:\n  target: origin/main..HEAD\n  mergeable: "yes"\n  a_tier_survivors: 0\n  findings: []\n  rationale: walked every changed script; nothing survived\n' > clean-findings.yaml
printf 'review:\n  target: origin/main..HEAD\n  mergeable: "no (A-tier)"\n  a_tier_survivors: 1\n  findings:\n    - id: cr-001\n      tier: A\n      note: real blocker\n' > dirty-findings.yaml
expect "selfreview refuses an empty findings file (I-69)" 1 bash -c ": > empty.yaml && bash '$PP' selfreview 7 empty.yaml >/dev/null 2>&1"
expect "selfreview records the round, its A-tier count and the sha it ran on (I-69)" 0 bash -c "bash '$PP' selfreview 7 clean-findings.yaml pr-reviewer-r1 | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['rounds']==1; assert d['last']['a_tier']==0; assert len(d['last']['head_sha'])==40\""
expect "solo converges once a clean isolated round is on record (I-69)" 0 bash -c "SELF_REVIEW=1 bash '$PP' predicate 7 null 0 green 3 false | grep -q '\"reason\": \"solo_converged_green\"'"
expect "--solo flag is equivalent to SELF_REVIEW=1 (I-69)" 0 bash -c "bash '$PP' predicate 7 null 0 green 3 false --solo >/dev/null"
# the same facts that converge under --solo must NOT converge without it: solo never becomes the default
expect "solo is not the default — same facts, no flag, still not converged (I-69)" 20 bash -c "bash '$PP' predicate 7 null 0 green 3 false >/dev/null"
expect "solo still refuses CHANGES_REQUESTED (I-69)" 20 bash -c "SELF_REVIEW=1 bash '$PP' predicate 7 CHANGES_REQUESTED 0 green 3 false | grep -q '\"changes_requested\"'; SELF_REVIEW=1 bash '$PP' predicate 7 CHANGES_REQUESTED 0 green 3 false >/dev/null"
expect "solo still refuses unresolved threads (I-69)" 20 bash -c "SELF_REVIEW=1 bash '$PP' predicate 7 null 2 green 3 false >/dev/null"
expect "an A-tier survivor blocks solo convergence (I-69)" 20 bash -c "bash '$PP' selfreview 7 dirty-findings.yaml >/dev/null && SELF_REVIEW=1 bash '$PP' predicate 7 null 0 green 3 false | grep -q self_review_a_tier_survivors; SELF_REVIEW=1 bash '$PP' predicate 7 null 0 green 3 false >/dev/null"
# stricter than APPROVED: a GitHub approval survives later pushes, a recorded self-review round does not
expect "a commit after the round makes it stale (I-69)" 20 bash -c "bash '$PP' selfreview 7 clean-findings.yaml >/dev/null && git commit -q --allow-empty -m 'fix(x): later work' && SELF_REVIEW=1 bash '$PP' predicate 7 null 0 green 3 false | grep -q self_review_stale; SELF_REVIEW=1 bash '$PP' predicate 7 null 0 green 3 false >/dev/null"
popd >/dev/null

echo "== psl / verify_psl.py (imported from looper)"
FXD="$S/psl-derive/eval/fixtures"
FXPSL="$S/psl/eval/fixtures"
expect "legal PSL passes" 0 py "$S/psl/scripts/verify_psl.py" "$FXD/PSL-memory-time-search.md"
expect "PSL with Step N in Workflow rejected" 1 py "$S/psl/scripts/verify_psl.py" "$FXD/PSL-bad-steps.md"
# dogfood 2026-09-05 (I-02): verify_derived rejects a PSL with no PSL-NNN ids, so this gate must too —
# otherwise /psl hands on a product its own downstream refuses
expect "PSL with no PSL-NNN rule ids rejected (I-02)" 1 py "$S/psl/scripts/verify_psl.py" "$FXPSL/PSL-no-rule-ids.md"
expect "PSL reusing one rule id for two rules rejected (I-02)" 1 py "$S/psl/scripts/verify_psl.py" "$FXPSL/PSL-dup-rule-id.md"
expect "verify_psl names the duplicated id and both lines (I-02)" 0 bash -c "python3 '$S/psl/scripts/verify_psl.py' '$FXPSL/PSL-dup-rule-id.md' | grep -q 'PSL-004.*被定义了两次'"
# I-20: the rule index carries a layer marker so verify_derived knows which rules a form draft may skip
expect "verify_psl reports the form/content split of the rule index (I-20)" 0 bash -c "python3 '$S/psl/scripts/verify_psl.py' '$FXD/PSL-memory-time-search.md' | grep -q 'form 7 / content 1'"
# I-23: a 来路 citing §N of a material that has no §N is written from memory, not read
expect "verify_psl flags an [elicit:物料 <file> §N] whose section does not exist (I-23)" 0 bash -c "python3 '$S/psl/scripts/verify_psl.py' '$FXPSL/PSL-bad-elicit.md' --material-root '$FXPSL' | grep -q 'material-notes.md §9'"
expect "verify_psl leaves a resolvable [elicit:物料 <file> §N] alone (I-23)" 0 bash -c "python3 '$S/psl/scripts/verify_psl.py' '$FXPSL/PSL-bad-elicit.md' --material-root '$FXPSL' | grep -c '^FLAG' | grep -q '^1$'"
# the reference example is what an author copies; it has to satisfy the gate it teaches (I-02)
python3 -c "
import re, pathlib, sys
s = pathlib.Path('$S/psl/references/EXAMPLE.md').read_text(encoding='utf-8')
b = re.findall(r'\`\`\`markdown\n(.*?)\n\`\`\`', s, re.S)
sys.exit(1) if len(b) != 1 else pathlib.Path('$TMP/example_psl.md').write_text(b[0], encoding='utf-8')"
expect "EXAMPLE.md's reference PSL passes verify_psl (I-02)" 0 py "$S/psl/scripts/verify_psl.py" "$TMP/example_psl.md"
expect "EXAMPLE.md's reference PSL carries a content-layer rule (I-20)" 0 bash -c "python3 '$S/psl/scripts/verify_psl.py' '$TMP/example_psl.md' | grep -q '内容层：'"

echo "== psl-derive / verify_derived.py"
expect "good derived dir passes" 0 py "$S/psl-derive/scripts/verify_derived.py" "$FXD/derived_good" --psl "$FXD/PSL-memory-time-search.md"
expect "bad derived dir rejected (no ref, fake id, Step, invented entity)" 1 py "$S/psl-derive/scripts/verify_derived.py" "$FXD/derived_bad" --psl "$FXD/PSL-memory-time-search.md"
expect "bad derived reports all four breaches" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$FXD/derived_bad' --psl '$FXD/PSL-memory-time-search.md' | grep -c 'without an anchor\|does not exist\|named steps\|not in PSL Domain' | grep -q '^4$'"
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

# --- I-77: the I-04 fix stripped EVERY blockquote, so a workflow written entirely behind `> ` scanned
# clean and the skill's only "write Σ/φ, not a procedure" check went blind. The strip is now bounded to
# the leading preamble; this fixture is the mutant-killer.
DG4="$TMP/derived_quoted_steps"; cp -R "$FXD/derived_good" "$DG4"
cat > "$DG4/workflow.md" <<'WFEOF'
# Workflow — memory-time-search

> Σ 写"用户做 X 时世界里发生了什么"，φ 写"歧义如何裁决、对的结果长什么样"。
> 禁止 Step 1/2/3、步骤 N、阶段 N、首先/然后/接着/最后 串。

## Σ · 发生了什么

> Step 1: 解析 `TimeRef`。
> Step 2: 与 `Era` 集合求交。
> Step 3: 重叠 ≥ 2 时进入 ambiguous。
WFEOF
expect "verify_derived: a workflow whose steps are all blockquoted is still rejected (I-77)" 1 py "$S/psl-derive/scripts/verify_derived.py" "$DG4" --psl "$FXD/PSL-memory-time-search.md"
expect "verify_derived: the quoted-steps rejection names the steps (I-77)" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$DG4' --psl '$FXD/PSL-memory-time-search.md' | grep -q 'named steps'"

# --- I-19: UI Contract / Acceptance / Design Principles items are load-bearing and citable
DG5="$TMP/derived_uianchor"; cp -R "$FXD/derived_good" "$DG5"
sed -i.bak 's|← PSL-007$|← UI-1|' "$DG5/form-draft.md"
expect "verify_derived: a decision anchored on ← UI-1 is legal (I-19)" 0 py "$S/psl-derive/scripts/verify_derived.py" "$DG5" --psl "$FXD/PSL-memory-time-search.md"
DG6="$TMP/derived_badanchor"; cp -R "$FXD/derived_good" "$DG6"
sed -i.bak 's|← PSL-007$|← UI-9|' "$DG6/form-draft.md"
expect "verify_derived: ← UI-9 with no such UI Contract item rejected (I-19)" 1 py "$S/psl-derive/scripts/verify_derived.py" "$DG6" --psl "$FXD/PSL-memory-time-search.md"
DG7="$TMP/derived_viaanchor"; cp -R "$FXD/derived_good" "$DG7"
sed -i.bak 's|不提供日历筛选器 ←|不提供日历筛选器 (via DP-7) ←|' "$DG7/form-draft.md"
expect "verify_derived: a (via DP-7) parenthetical naming no such principle rejected (I-19)" 1 py "$S/psl-derive/scripts/verify_derived.py" "$DG7" --psl "$FXD/PSL-memory-time-search.md"

# --- I-20 / I-06: a content-layer rule absent from the form draft is not an omission, and the flag for
# the ones that ARE omissions has to say what G1 does about it
expect "verify_derived: content-layer rule kept out of the uncited flag (I-20)" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$FXD/derived_good' --psl '$FXD/PSL-memory-time-search.md' | python3 -c \"import json,sys; d=json.load(sys.stdin); u=[f for f in d['flags'] if f.startswith('form-layer')]; assert u and 'PSL-006' not in u[0] and 'PSL-002' in u[0], d['flags']\""
expect "verify_derived: the uncited-rule flag names the G1 agenda (I-06)" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$FXD/derived_good' --psl '$FXD/PSL-memory-time-search.md' | grep -q 'G1 议程：删规律或补决策'"

# --- I-21 / I-32 / I-35 / I-44: a targeted re-derivation is legal, but it must archive the round it
# replaces, ship a decision-level round-diff, and say which round the directory holds
expect "verify_derived: round 2 with round1/ archive + round-diff passes (I-21)" 0 py "$S/psl-derive/scripts/verify_derived.py" "$FXD/derived_round2" --psl "$FXD/PSL-memory-time-search.md" --round 2
R2A="$TMP/r2_noarchive"; cp -R "$FXD/derived_round2" "$R2A"; rm -rf "$R2A/round1"
expect "verify_derived: round 2 without the round1/ archive rejected (I-44)" 1 py "$S/psl-derive/scripts/verify_derived.py" "$R2A" --psl "$FXD/PSL-memory-time-search.md" --round 2
expect "verify_derived: the missing-archive rejection says so (I-44)" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$R2A' --psl '$FXD/PSL-memory-time-search.md' --round 2 | grep -q 'previous round not archived at round1/'"
R2B="$TMP/r2_partialarchive"; cp -R "$FXD/derived_round2" "$R2B"; rm -f "$R2B/round1/workflow.md"
expect "verify_derived: round 2 whose archive is missing a file rejected (I-44)" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$R2B' --psl '$FXD/PSL-memory-time-search.md' --round 2 | grep -q \"round1/ is missing \\['workflow.md'\\]\""
R2C="$TMP/r2_nodiff"; cp -R "$FXD/derived_round2" "$R2C"; rm -f "$R2C/round-diff.md"
expect "verify_derived: round 2 without round-diff.md rejected (I-35)" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$R2C' --psl '$FXD/PSL-memory-time-search.md' --round 2 | grep -q 'missing round-diff.md'"
R2D="$TMP/r2_diff_no_archive_ref"; cp -R "$FXD/derived_round2" "$R2D"; sed -i.bak 's|`round1/form-draft.md`|上一轮|g' "$R2D/round-diff.md"
expect "verify_derived: a round-diff whose left side names no archive rejected (I-35)" 1 py "$S/psl-derive/scripts/verify_derived.py" "$R2D" --psl "$FXD/PSL-memory-time-search.md" --round 2
R2E="$TMP/r2_noround"; cp -R "$FXD/derived_round2" "$R2E"; sed -i.bak '/^round: 2$/d' "$R2E/divergence.md"
expect "verify_derived: round 2 divergence.md not declaring round: 2 rejected (I-32)" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$R2E' --psl '$FXD/PSL-memory-time-search.md' --round 2 | grep -q 'must declare .round: 2.'"
R2G="$TMP/r2_wronground"; cp -R "$FXD/derived_round2" "$R2G"; sed -i.bak 's|^round: 2$|round: 5|' "$R2G/divergence.md"
expect "verify_derived: divergence.md declaring a different round than --round rejected (I-32)" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$R2G' --psl '$FXD/PSL-memory-time-search.md' --round 2 | grep -q 'declares round: 5 — mismatch'"
R2F="$TMP/r2_noruling"; cp -R "$FXD/derived_round2" "$R2F"; sed -i.bak 's|^## G1 裁决 → 落点$|## 备注|' "$R2F/divergence.md"
expect "verify_derived: round 2 divergence.md without a 裁决 → 落点 table rejected (I-32)" 1 py "$S/psl-derive/scripts/verify_derived.py" "$R2F" --psl "$FXD/PSL-memory-time-search.md" --round 2

# --- I-56 / I-58: a predicate nobody worked once, and a record type with no declared landing, are the
# two gaps L5 discovered while encoding fixtures — a round too late
DG8="$TMP/derived_predicate"; cp -R "$FXD/derived_good" "$DG8"
printf '\n- [F-30] 结果合法当且仅当 `eras[]` 非空 ∧ 每条带 `scene_summary` ← PSL-007\n' >> "$DG8/form-draft.md"
expect "verify_derived: a predicate decision with no worked example is flagged (I-56)" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$DG8' --psl '$FXD/PSL-memory-time-search.md' | grep -q 'no worked example.*F-30'"
DG9="$TMP/derived_predicate_ok"; cp -R "$FXD/derived_good" "$DG9"
printf '\n- [F-30] 结果合法当且仅当 `eras[]` 非空 ∧ 每条带 `scene_summary`；例：`{eras:[{id:1}]}` 缺 scene_summary → 非法 ← PSL-007\n' >> "$DG9/form-draft.md"
expect "verify_derived: the same predicate with a worked example is not flagged (I-56)" 0 bash -c "! python3 '$S/psl-derive/scripts/verify_derived.py' '$DG9' --psl '$FXD/PSL-memory-time-search.md' | grep -q 'no worked example'"
expect "verify_derived: good derived carries no worked-example flag (I-56)" 0 bash -c "! python3 '$S/psl-derive/scripts/verify_derived.py' '$FXD/derived_good' --psl '$FXD/PSL-memory-time-search.md' | grep -q 'no worked example'"
DGA="$TMP/derived_noland"; cp -R "$FXD/derived_good" "$DGA"; sed -i.bak 's|；落位：[^←]*←|←|' "$DGA/form-draft.md"
expect "verify_derived: 实体与数据形态 with no landing declared is flagged (I-58)" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$DGA' --psl '$FXD/PSL-memory-time-search.md' | grep -q '没有任何落位说明'"
expect "verify_derived: good derived declares landings and is not flagged (I-58)" 0 bash -c "! python3 '$S/psl-derive/scripts/verify_derived.py' '$FXD/derived_good' --psl '$FXD/PSL-memory-time-search.md' | grep -q '没有任何落位说明'"

# --- I-36: a decision that asserts the shape of a data file needs a line-level locator for that claim
DGB="$TMP/derived_nolocator"; cp -R "$FXD/derived_good" "$DGB"
printf '\n- [F-31] 同阶段替代按 graph.yaml 里从同一 stage 节点出发的 conditional 边判定 ← PSL-005\n' >> "$DGB/form-draft.md"
expect "verify_derived: a claim about graph.yaml structure with no line locator is flagged (I-36)" 0 bash -c "python3 '$S/psl-derive/scripts/verify_derived.py' '$DGB' --psl '$FXD/PSL-memory-time-search.md' | grep -q 'without a line-level locator.*F-31'"
DGC="$TMP/derived_locator"; cp -R "$FXD/derived_good" "$DGC"
printf '\n- [F-31] 同阶段替代按 graph.yaml 里从同一 stage 节点出发的 conditional 边判定（graph.yaml L320–321）← PSL-005\n' >> "$DGC/form-draft.md"
expect "verify_derived: the same claim with graph.yaml L320 is not flagged (I-36)" 0 bash -c "! python3 '$S/psl-derive/scripts/verify_derived.py' '$DGC' --psl '$FXD/PSL-memory-time-search.md' | grep -q 'F-31'"

echo "== dos-extract / verify_dos.py (imported from looper)"
FXO="$S/dos-extract/eval/fixtures"
DXS="$S/dos-extract/scripts"
expect "clean dos passes" 0 py "$DXS/verify_dos.py" "$FXO/dos_good.yaml"
expect "UI-suffixed object rejected" 1 py "$DXS/verify_dos.py" "$FXO/dos_bad_ui_suffix.yaml"
# dogfood 2026-09-05 (I-10): the suffix heuristic aims at `TopicCard`; a whole-word domain
# name is the waivable case, and a compound stays non-waivable however loudly it is waived.
expect "whole-word UI name rejected without a waiver (I-10)" 1 py "$DXS/verify_dos.py" "$FXO/dos_whole_word_card.yaml"
expect "whole-word UI name still rejected when decisions.md has no waiver section (I-10)" 1 py "$DXS/verify_dos.py" "$FXO/dos_whole_word_card.yaml" --decisions "$FXO/decisions_no_waiver.md"
expect "whole-word UI name cleared by a decisions.md waiver, reported under waived (I-10)" 0 bash -c "python3 '$DXS/verify_dos.py' '$FXO/dos_whole_word_card.yaml' --decisions '$FXO/decisions_with_waiver.md' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['exit']=='MECHANICALLY_CLEAN', d['rejects']; assert any(\\\"'Card'\\\" in w for w in d['waived']), d['waived']\""
expect "compound UI suffix is NOT waivable (I-10)" 1 py "$DXS/verify_dos.py" "$FXO/dos_bad_ui_suffix.yaml" --waive DateFilterCard
expect "a relationship naming a synonym resolves and is flagged, not rejected (I-11)" 0 bash -c "python3 '$DXS/verify_dos.py' '$FXO/dos_rel_synonym.yaml' --waive Card | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['exit']=='MECHANICALLY_CLEAN', d['rejects']; assert any('resolves through a synonym' in f for f in d['needs_semantic_review']), d['needs_semantic_review']\""
# dogfood 2026-09-05 (I-37): a materialised derived view must name its source.
expect "empty derived_from rejected (I-37)" 1 py "$DXS/verify_dos.py" "$FXO/dos_derived_empty.yaml"
expect "named derived_from passes and is reported (I-37)" 0 bash -c "python3 '$DXS/verify_dos.py' '$FXO/dos_derived_ok.yaml' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['derived_properties']==['Ring.missing'], d['derived_properties']\""
# dogfood 2026-09-05 (I-14): methodology.md §6's size budget was prose only; nothing measured it.
expect "over-budget dos.yaml warns without changing the exit code (I-14)" 0 bash -c "python3 '$DXS/verify_dos.py' '$FXO/dos_good.yaml' --max-lines 5 | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['exit']=='MECHANICALLY_CLEAN', d['rejects']; assert any('lines >' in w for w in d['warnings']), d['warnings']\""
expect "empty / placeholder / over-long object descriptions each warn (I-14)" 0 bash -c "python3 '$DXS/verify_dos.py' '$FXO/dos_bad_descriptions.yaml' | python3 -c \"import json,sys; w=json.load(sys.stdin)['warnings']; assert any('description empty' in x for x in w), w; assert any('placeholder' in x for x in w), w; assert any('chars >' in x for x in w), w\""

echo "== dos-extract / inventory.py (structured channel)"
INV="$TMP/inv"; mkdir -p "$INV/a/b/schema"
cat > "$INV/a/b/schema/state.schema.json" <<'JSON'
{"type":"object","properties":{"track":{"type":"string","enum":["psl","task"]},
 "cards":{"type":"object"}},"$defs":{"gate":{"type":"object","properties":{"verdict":{"type":"string"}}}}}
JSON
cat > "$INV/graph.yaml" <<'YAML'
nodes:
  - {id: stage.intake, kind: stage}
  - {id: plan-cards, kind: skill}
YAML
cat > "$INV/package.json" <<'JSON'
{"name":"x","scripts":{"testonlymanifestkey":"echo"},"dependencies":{}}
JSON
# dogfood 2026-09-05 (I-09): a plugin/schema-first repo declares nothing in classes, so the
# code-only scan returned 0 nouns and the operator hand-wrote the noun table.
expect "structured channel finds \$defs / enum / kind / property nouns (I-09)" 0 bash -c "python3 '$DXS/inventory.py' '$INV' -o '$TMP/inv.md' >/dev/null 2>&1 && for t in gate verdict track psl task skill stage cards; do grep -q \"\\*\\*\$t\\*\\*\" '$TMP/inv.md' || { echo \"missing \$t\"; exit 1; }; done"
expect "--no-structured reproduces the zero-noun scan (I-09)" 0 bash -c "python3 '$DXS/inventory.py' '$INV' -o '$TMP/inv0.md' --no-structured >/dev/null 2>&1 && grep -q 'Distinct nouns: 0' '$TMP/inv0.md'"
expect "zero-noun report says so instead of printing an empty table (I-13)" 0 bash -c "grep -q 'No nouns found' '$TMP/inv0.md'"
expect "tooling manifests are skipped by the structured channel (I-09)" 0 bash -c "grep -q '\\*\\*gate\\*\\*' '$TMP/inv.md' && ! grep -q 'testonlymanifestkey' '$TMP/inv.md'"
expect "--exclude drops a directory of that name at any depth, not just at the root (I-09)" 0 bash -c "python3 '$DXS/inventory.py' '$INV' -o '$TMP/invx.md' --exclude schema >/dev/null 2>&1 && ! grep -q '\\*\\*gate\\*\\*' '$TMP/invx.md' && grep -q '\\*\\*stage\\*\\*' '$TMP/invx.md'"
expect "--exclude also matches a file name segment, not only directories (I-09)" 0 bash -c "python3 '$DXS/inventory.py' '$INV' -o '$TMP/invf.md' --exclude graph.yaml >/dev/null 2>&1 && ! grep -q '\\*\\*stage\\*\\*' '$TMP/invf.md' && grep -q '\\*\\*gate\\*\\*' '$TMP/invf.md'"

echo "== dos-extract / count_terms.py (docs channel counting primitive)"
printf '%s\n' '# label = variants' 'Gate = gate, G1, G2' 'Ghost = zzznotathing' > "$TMP/terms.txt"
# dogfood 2026-09-05 (I-12): the docs pass asked for "≈47 occurrences" with no way to reproduce it.
expect "count_terms: reproducible per-group counts + file:line evidence (I-12)" 0 bash -c "python3 '$DXS/count_terms.py' --terms '$TMP/terms.txt' --root '$S/dos-extract' --group fixtures='eval/fixtures/*.yaml' --json 2>/dev/null | python3 -c \"import json,sys; d=json.load(sys.stdin); g=d['terms']['Gate']; import re; assert g['total']>0, g; assert g['evidence'] and re.match(r'^\\\`[^\\\`]+:[0-9]+\\\` ', g['evidence'][0]), g['evidence']\""
expect "count_terms: a term matching nothing exits 1, not silently 0 (I-12)" 1 py "$DXS/count_terms.py" --terms "$TMP/terms.txt" --root "$S/dos-extract" --group fixtures='eval/fixtures/*.yaml'
expect "count_terms: word boundaries keep PR out of PROPOSAL (I-12)" 0 bash -c "mkdir -p '$TMP/ct' && printf 'PROPOSAL and PROPRIETARY\n' > '$TMP/ct/a.md' && printf 'PR\n' >> '$TMP/ct/a.md' && printf 'PR\n' > '$TMP/terms2.txt' && python3 '$DXS/count_terms.py' --terms '$TMP/terms2.txt' --root '$TMP/ct' --corpus '*.md' --json | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['terms']['PR']['total']==1, d['terms']['PR']\""

echo "== dos-extract / reconcile_dos.py + dos_closure.py (X1 as-is ↔ to-be)"
# dogfood 2026-09-05 (I-49): the reconciliation existed only as prose in the G1 record, so the
# card linter had to be pointed at a proposal file by hand.
expect "reconcile: unmapped to-be object + rule conflict => INCOMPLETE, nothing written (I-49)" 1 bash -c "python3 '$DXS/reconcile_dos.py' --as-is '$FXO/dos_asis.yaml' --to-be '$FXO/dos_tobe.yaml' --map-file '$FXO/dos_reconcile_map.yaml' --output '$TMP/rec_bad.yaml' > '$TMP/rec_bad.json'; rc=\$?; python3 -c \"
import json
d=json.load(open('$TMP/rec_bad.json'))
assert d['verdict']=='INCOMPLETE' and not d['written'], d
assert d['unmapped_to_be']==['Gap','Ring'], d['unmapped_to_be']
assert d['rule_conflicts'], d\" && test ! -f '$TMP/rec_bad.yaml' && exit \$rc"
expect "reconcile: full mapping folds the to-be name into synonyms and exits 0 (I-49)" 0 bash -c "python3 '$DXS/reconcile_dos.py' --as-is '$FXO/dos_asis.yaml' --to-be '$FXO/dos_tobe_mappable.yaml' --map 'Part=Node' --output '$TMP/rec_ok.yaml' >/dev/null && python3 -c \"
import sys; sys.path.insert(0,'$DXS')
from dos_closure import load_closure
c=load_closure('$TMP/rec_ok.yaml')
assert c.resolve_object('Part')=='Node', c.resolve_object('Part')
assert c.resolve_object('配件')=='Node'
assert c.resolve_object('Ring') is None\""
expect "reconcile: the reconciled DOS still passes verify_dos.py (I-49)" 0 py "$DXS/verify_dos.py" "$TMP/rec_ok.yaml"
expect "reconcile: a mapping onto a name the as-is DOS lacks is a usage error, exit 2 (I-49)" 2 py "$DXS/reconcile_dos.py" --as-is "$FXO/dos_asis.yaml" --to-be "$FXO/dos_tobe_mappable.yaml" --map "Part=Nonexistent"
expect "reconcile: --allow-unmapped writes the file and records the gaps as open questions (I-49)" 1 bash -c "python3 '$DXS/reconcile_dos.py' --as-is '$FXO/dos_asis.yaml' --to-be '$FXO/dos_tobe.yaml' --map-file '$FXO/dos_reconcile_map.yaml' --allow-unmapped --output '$TMP/rec_partial.yaml' >/dev/null; rc=\$?; python3 -c \"
import yaml
d=yaml.safe_load(open('$TMP/rec_partial.yaml'))
q=' '.join(str(x) for x in d['open_questions'])
assert 'Ring' in q and 'Gap' in q, q
assert d['reconciliation']['unmapped_to_be']==['Gap','Ring']\"; exit \$rc"

echo "== dos closure honours synonyms (I-15) — verify_issue.py + lint_cards.py"
SYNI="$TMP/syn_issue.md"; sed -e 's/objects: \[Memory, Era\]/objects: [Memory, Period]/' -e 's/invariants: \[R003\]/invariants: [INV-ERA-1]/' "$S/issue/eval/fixtures/good_issue.md" > "$SYNI"
expect "verify_issue: the team's word closes through a declared synonym (I-15)" 0 py "$S/issue/scripts/verify_issue.py" "$SYNI" --dos "$FXO/dos_with_synonyms.yaml"
expect "verify_issue: the same word fails closure when the synonym is not declared (I-15)" 1 py "$S/issue/scripts/verify_issue.py" "$SYNI" --dos "$FXO/dos_without_synonyms.yaml"
SYNC="$TMP/syn_cards"; cp -R "$S/plan-cards/eval/fixtures/cards_good" "$SYNC"
sed -i.bak -e 's/objects: \[Memory, Era\]/objects: [Memory, Period]/' -e 's/invariants: \[R003\]/invariants: [INV-ERA-1]/' "$SYNC"/CARD-*.yaml && rm -f "$SYNC"/*.bak
expect "lint_cards: a card slice written in the team's word closes through synonyms (I-15/I-49)" 0 py "$S/plan-cards/scripts/lint_cards.py" "$SYNC" --spec "$S/sdlc/eval/fixtures/spec.md" --done-when "$S/sdlc/eval/fixtures/done_when.yaml" --dos "$FXO/dos_with_synonyms.yaml"
expect "lint_cards: the same slice fails closure without the synonyms (I-15/I-49)" 1 py "$S/plan-cards/scripts/lint_cards.py" "$SYNC" --spec "$S/sdlc/eval/fixtures/spec.md" --done-when "$S/sdlc/eval/fixtures/done_when.yaml" --dos "$FXO/dos_without_synonyms.yaml"

echo "== invariant-extract / verify_card.py (imported from looper)"
FXI="$S/invariant-extract/eval/fixtures"
IXV="$S/invariant-extract/scripts/verify_card.py"
expect "card with provenance passes" 0 py "$IXV" "$FXI/card_good.yaml" --dos "$FXO/dos_good.yaml"
expect "card without provenance rejected" 1 py "$IXV" "$FXI/card_bad_noprov.yaml"
# dogfood 2026-09-05 (I-25): the template had no `aspect` slot on overridable_defaults while the
# script hard-rejected entries without one, and no `id` on kicked entries so ◊-leakage ran empty.
expect "overridable entry without aspect rejected — the template now carries the slot (I-25)" 1 py "$IXV" "$FXI/card_no_aspect.yaml"
expect "a ◊ candidate also carded is caught now that kicked entries carry ids (I-25)" 1 py "$IXV" "$FXI/card_diamond_leak.yaml"
expect "a re-wording of an existing DOS rule is flagged, not silently accepted (I-25)" 0 bash -c "python3 '$IXV' '$FXI/card_near_dup.yaml' --dos '$FXO/dos_good.yaml' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert any('similar to dos.yaml R002' in f for f in d['needs_semantic_review']), d['needs_semantic_review']\""
expect "two entries on one card re-stating the same rule are flagged (I-25)" 0 bash -c "python3 '$IXV' '$FXI/card_self_dup.yaml' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert any('statements' in f and 'similar' in f for f in d['needs_semantic_review']), d['needs_semantic_review']\""
expect "the narrowest-rule flag is targeted, not one per entry (I-25)" 0 bash -c "python3 '$IXV' '$FXI/card_good.yaml' --dos '$FXO/dos_good.yaml' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert not any('narrowest' in f for f in d['needs_semantic_review']), d['needs_semantic_review']\""
expect "the report prints projected_out / deduped / suspects / conflicts counts (I-25)" 0 bash -c "python3 '$IXV' '$FXI/card_good.yaml' | python3 -c \"import json,sys; d=json.load(sys.stdin); [d[k] for k in ('projected_out_obstacles','deduped_against_constitution','constitution_promotion_suspects','conflicts_for_legislation','registered_gaps')]\""
# dogfood 2026-09-05 (I-26): abduction.md §5 and the altitude/suspects duplication were unchecked.
expect "low confidence must be proposed even in the overridable column (I-26)" 1 py "$IXV" "$FXI/card_low_conf_carded.yaml"
expect "altitude proposed_to_constitution on a carded entry rejected (I-26)" 1 py "$IXV" "$FXI/card_altitude_promoted.yaml"
# dogfood 2026-09-05 (I-29): a bare failure-memory integer, and gaps with no declared destination.
expect "failure_memory_count with no sources rejected (I-29)" 1 py "$IXV" "$FXI/card_bare_count.yaml"
expect "missing snapshot_at flagged when sources are given (I-29)" 0 bash -c "sed 's/^  snapshot_at:.*/  snapshot_at: \"\"/' '$FXI/card_good.yaml' > '$TMP/card_nosnap.yaml' && python3 '$IXV' '$TMP/card_nosnap.yaml' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert any('snapshot_at' in f for f in d['needs_semantic_review']), d['needs_semantic_review']\""
expect "a registered gap with no destination rejected (I-29)" 1 py "$IXV" "$FXI/card_gap_no_dest.yaml"

echo "== R1 templates carry the slots their own verifiers require"
# dogfood 2026-09-05 (I-25/I-29): a card filled from the shipped template used to be rejected for
# fields the template had no slot for, so the operator hand-added them to pass.
expect "invariant_card.yaml declares every field verify_card.py hard-requires (I-25/I-29)" 0 bash -c "python3 -c \"
import yaml
t=yaml.safe_load(open('$S/invariant-extract/assets/invariant_card.yaml'))
need={'statement','aspect','strength','altitude','provenance','confidence','disposition','narrowest_rule_note'}
for col in ('hard_invariants','overridable_defaults'):
    missing=need-set(t[col][0]); assert not missing, (col, missing)
assert 'id' in t['kicked_to_done_when'][0], 'kicked entries need an id for the diamond-leak check'
c2=t['channel_2_input']; assert 'sources' in c2 and 'snapshot_at' in c2, c2
assert t['registered_gaps'][0]['destination'] in ('done_when','issue','backlog')
assert t['hard_invariants'][0]['altitude']=='territory'\""
# dogfood 2026-09-05 (I-27): the template's comments carried another project's rule numbering
# (R001 isolation / R002 gate-signing) beside sdlc's own R001/R002 on the same card.
expect "invariant_card.yaml uses sdlc's G2 wording, not a borrowed R00n gate id (I-27)" 0 bash -c "! grep -qE '\\(R00[0-9]\\)' '$S/invariant-extract/assets/invariant_card.yaml' && grep -q 'G2' '$S/invariant-extract/assets/invariant_card.yaml'"
# dogfood 2026-09-05 (I-11/I-37): the DOS template had nowhere to record a synonym, a downstream
# translation, a rule alias, or a materialised derived view.
expect "dos_template.yaml carries synonyms / aliases / translation_notes / derived_from (I-11/I-37)" 0 bash -c "python3 -c \"
import yaml
t=yaml.safe_load(open('$S/dos-extract/assets/dos_template.yaml'))
o=t['objects']['ExampleObject']
assert 'synonyms' in o, list(o)
assert any('derived_from' in (p or {}) for p in o['properties'].values()), list(o['properties'])
assert 'aliases' in t['rules'][0], t['rules'][0]
assert 'translation_notes' in t['bounded_contexts']['downstream_contexts'][0]\""
# dogfood 2026-09-05 (I-10/I-13): the decisions template presumed a non-empty pruning table and
# had no machine-read waiver channel.
expect "decisions_template.md's waiver section parses and the zero-noun case is written (I-10/I-13)" 0 bash -c "python3 -c \"
import sys; sys.path.insert(0,'$DXS')
import verify_dos as v
w=v.parse_waivers('$S/dos-extract/assets/decisions_template.md')
assert w, 'the ## Naming waivers section did not parse'
text=open('$S/dos-extract/assets/decisions_template.md').read()
assert 'code channel returned zero nouns' in text.lower() or '0 nouns' in text, 'no zero-noun guidance'
assert 'count_terms.py' in text, 'docs counts are not tied to the counting primitive'\""

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
expect "gate g1 pass refused without world.derived_dir" 1 py "$SS" gate g1 --verdict pass --signer-kind human --by human
mkdir -p derived && cp "$FXD/derived_good/"* derived/
expect "set world.* paths" 0 py "$SS" set world.psl=PSL.md world.derived_dir=derived
expect "gate g1 pass with derived products" 0 py "$SS" gate g1 --verdict pass --signer-kind human --by human --record g1-record.md
expect "advance issue ok after G1" 0 py "$SS" advance issue
expect "gate g1 reject with attribution bumps world counter" 0 bash -c "python3 '$SS' gate g1 --verdict reject --signer-kind human --by human --attribution rule_error >/dev/null && python3 '$SS' show | grep -q '\"world\": 1'"
expect "gate g1 reject with derivation_error does NOT bump world (I-34)" 0 bash -c "python3 '$SS' gate g1 --verdict reject --signer-kind human --by human --attribution derivation_error >/dev/null && python3 '$SS' show | grep -q '\"world\": 1'"
expect "gate g1 pass after a reject clears the stale attribution (I-51)" 0 bash -c "python3 '$SS' gate g1 --verdict pass --signer-kind human --by human >/dev/null && ! python3 '$SS' show | grep -q 'derivation_error'"
# re-audit 2026-09-06: --signer-kind used to default to `human`, so an agent that simply omitted the
# flag was recorded as a person. A discipline bypassable by omission is not a discipline, and this
# whole run's honesty rests on delegated signatures being marked as such. It is now required.
expect "gate refuses to sign without saying which kind of signer it is (re-audit)" 2 py "$SS" gate g1 --verdict pass --by someone
expect "lock sign refuses the same way (re-audit)" 2 bash -c "cd \"\$(mktemp -d)\" && printf 'a: 1\n' > c.yaml && python3 '$S/sdlc/scripts/lock_done_when.py' sign --by someone --out .l c.yaml"
# dogfood 2026-09-05 (I-17): a delegated signature needs an authorization on record and is traced as agent:, not human:
expect "gate: delegated_agent without --authorization refused" 1 py "$SS" gate g3 --verdict pass --signer-kind human --by proxy-bot --signer-kind delegated_agent
expect "gate: delegated_agent with authorization recorded as agent:<by> + [delegated]" 0 bash -c "python3 '$SS' gate g3 --verdict pass --signer-kind human --by proxy-bot --signer-kind delegated_agent --authorization 'user said so' >/dev/null && grep -q 'agent:proxy-bot' .sdlc/demo-psl/trace.jsonl && grep -q '\[delegated\]' .sdlc/demo-psl/ledger.md"
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

echo "== test-suite-generator / v2 contract: cli+ui boundaries, manifest, red baseline"
# The real v2 artefacts from the ring-audit run: `behavior:` is an empty seed, the 34 names live in
# tests-manifest.yaml, and `existence:` carries cli:/ui: observation boundaries instead of file:/function:.
TSG="$S/test-suite-generator/scripts"
DW2="$ROOT/dogfood/ring-audit/done_when.yaml"
MF2="$ROOT/dogfood/ring-audit/tests/ring-audit/tests-manifest.yaml"
TD3="$ROOT/dogfood/ring-audit/tests/ring-audit"
expect "gen_existence: cli: boundary emits a resolver, not a blind rg (I-54)" 0 bash -c "out=\$(python3 '$TSG/gen_existence.py' '$DW2') && grep -q 'cli_entry \"check-audit\"' <<<\"\$out\" && grep -q 'cli_entry \"verify-commit\"' <<<\"\$out\" && ! grep -q 'rg -q \"check-audit\"' <<<\"\$out\""
expect "gen_existence: ui: boundary checks the surface AND its anchor (I-54)" 0 bash -c "out=\$(python3 '$TSG/gen_existence.py' '$DW2') && grep -q 'ui_surface \"AUDIT.md\"' <<<\"\$out\" && grep -c 'ui_anchor \"AUDIT.md\"' <<<\"\$out\" | grep -qx 2"
expect "gen_existence: the generated v2 existence script passes against the real tree (I-54)" 0 bash -c "python3 '$TSG/gen_existence.py' '$DW2' --src '$ROOT' > '$TMP/ex_v2.sh' && bash '$TMP/ex_v2.sh' | grep -q 'All 5 existence checks passed'"
expect "gen_existence: --ui-anchor reproduces the hand-written ring-tables expansion (I-54)" 0 bash -c "python3 '$TSG/gen_existence.py' '$DW2' --cli 'check-audit=$ROOT/dogfood/ring-audit/check_audit.py' --cli 'verify-commit=$S/commit/scripts/verify_commit.py' --ui 'AUDIT.md=$ROOT/dogfood/ring-audit/AUDIT.md' --ui-anchor 'AUDIT.md#ring-tables=^## R0([^0-9]|\$)' --ui-anchor 'AUDIT.md#ring-tables=^## R8([^0-9]|\$)' --ui-anchor 'AUDIT.md#ring-tables=^## .*spine' --ui-anchor 'AUDIT.md#ring-tables=^\\|.*needed.*\\|.*implemented.*\\|.*naming' --ui-anchor 'AUDIT.md#run-evidence=^## .*run[_ -]?evidence' > '$TMP/ex_v2_pinned.sh' && bash '$TMP/ex_v2_pinned.sh' | grep -q 'All 8 existence checks passed'"
expect "gen_existence: v1 kinds still map (file/function/route/db_field/component)" 0 bash -c "out=\$(python3 '$TSG/gen_existence.py' '$EX/done_when.yaml' --src src) && grep -q 'All 12 existence checks passed' <<<\"\$out\" && grep -q 'test -f \"src/billing/cancel_subscription_use_case.ts\"' <<<\"\$out\""
expect "check_verbatim_names: v2 contract alone → empty name set rejected, never 0/0 ✓ (I-59)" 2 py "$TSG/check_verbatim_names.py" "$DW2" "$TD3" --check
expect "check_verbatim_names: the empty-set message points at --manifest (I-59)" 0 bash -c "python3 '$TSG/check_verbatim_names.py' '$DW2' '$TD3' --check 2>&1 | grep -q -- '--manifest tests/<feature>/tests-manifest.yaml'"
expect "check_verbatim_names: every manifest name is present, whatever the suite's size (I-54)" 0 bash -c "python3 '$TSG/check_verbatim_names.py' '$DW2' '$TD3' --manifest '$MF2' --json | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['missing']==[] and d['present']==d['total'] and d['total']>0, d\""
expect "check_verbatim_names: a name missing from the tests dir still → 1 under --manifest" 1 py "$TSG/check_verbatim_names.py" "$DW2" "$TD2" --manifest "$MF2" --check
expect "derive_counts: v2 behavior seed alone → rejected, not '0 unit tests' (I-54)" 2 py "$TSG/derive_counts.py" "$DW2"
expect "derive_counts: the derived counts add up to the methods in the file (I-54)" 0 bash -c "python3 '$TSG/derive_counts.py' '$DW2' --manifest '$MF2' --json | python3 -c \"
import json, re, sys
d = json.load(sys.stdin)
methods = len(re.findall(r'def (test_\\w+)', open('$TD3/test_check_audit.py', encoding='utf-8').read()))
assert d['unit_total'] + d['integration_total'] == methods, (d, methods)
assert d['unit_example'] + d['unit_property'] == d['unit_total'], d
assert d['existence'] > 0, d
\""

# I-62: the RED baseline must measure a checkout of HEAD, not the working tree a parallel
# implementer is writing into. Scenario: the suite is committed, the instrument is NOT.
RB="$TMP/redbase"; mkdir -p "$RB/repo/tests"; pushd "$RB/repo" >/dev/null
git init -q -b main .
printf '#!/usr/bin/env bash\ntest -f instrument.py && echo "instrument PRESENT" || echo "instrument ABSENT"\nexit 1\n' > tests/run_tests.sh
git add -A && git -c user.name=t -c user.email=t@t commit -qm "test: suite before the instrument exists"
echo "print(1)" > instrument.py     # the parallel implementer's untracked file
CRB="$TSG/capture_red_baseline.py"
expect "capture_red_baseline: untracked instrument does not vote on the baseline (I-62)" 0 bash -c "python3 '$CRB' tests/run_tests.sh --out '$RB/RED_BASELINE.txt' >/dev/null && grep -q 'instrument ABSENT' '$RB/RED_BASELINE.txt' && grep -q 'git status --porcelain (clean checkout): <empty>' '$RB/RED_BASELINE.txt' && grep -q 'instrument.py' '$RB/RED_BASELINE.txt'"
expect "capture_red_baseline: records the runner's own exit, does not propagate it (I-62)" 0 bash -c "grep -q 'runner exit: 1' '$RB/RED_BASELINE.txt'"
expect "capture_red_baseline --verify: a baseline with the evidence passes (I-62)" 0 py "$CRB" --verify "$RB/RED_BASELINE.txt"
grep -v 'clean_checkout:\|porcelain (clean checkout)' "$RB/RED_BASELINE.txt" > "$RB/NO_EVIDENCE.txt"
expect "capture_red_baseline --verify: a baseline without the evidence is rejected (I-62)" 1 py "$CRB" --verify "$RB/NO_EVIDENCE.txt"
sed 's/porcelain (clean checkout): <empty>/porcelain (clean checkout): ?? instrument.py/' "$RB/RED_BASELINE.txt" > "$RB/DIRTY_EVIDENCE.txt"
expect "capture_red_baseline --verify: evidence that says the tree was dirty is rejected (I-62)" 1 py "$CRB" --verify "$RB/DIRTY_EVIDENCE.txt"
popd >/dev/null

# I-80: the suite must be able to prove its own expectations kill their mutants. Skipped inside a
# --mutate child run (SMOKE_NESTED) — otherwise the self-check would recurse into itself.
if [[ -z "${SMOKE_NESTED:-}" ]]; then
  expect "smoke --mutate: a killed mutant is reported with the expectations that killed it (I-80)" 0 bash -c "bash '$ROOT/eval/smoke.sh' --only 'I-59' --mutate skills/test-suite-generator/scripts/check_verbatim_names.py 'EMPTY_EXIT = 2' 'EMPTY_EXIT = 0' | grep -q 'mutant killed by'"
  expect "smoke --mutate: a surviving mutant fails the self-check (I-80)" 1 bash -c "bash '$ROOT/eval/smoke.sh' --only 'derive_counts on example' --mutate skills/test-suite-generator/scripts/derive_counts.py 'the count primitive' 'the counting primitive' >/dev/null 2>&1"
  expect "smoke --mutate: an old string that is not in the file is an error, not a pass (I-80)" 2 bash -c "bash '$ROOT/eval/smoke.sh' --only 'derive_counts on example' --mutate skills/test-suite-generator/scripts/derive_counts.py 'no such string in this file' 'x' >/dev/null 2>&1"
  # PR pre-review, A-tier against the harness itself: "killed" used to mean "some FAIL line exists in
  # the mutant run". With the copy taken from the working tree, one already-red expectation made every
  # mutant look killed — and every mutation proof in the register rests on this tool. Now the baseline
  # must be green and the verdict is the delta.
  expect "smoke --mutate: a red baseline is refused, not counted as a kill (harness cr-001)" 3 bash -c "
    POISON=\"\$(mktemp -d)\"; cp -R '$ROOT' \"\$POISON/sdlc\"
    printf 'raise SystemExit(9)\n' | cat - '$ROOT/skills/retro/scripts/metrics.py' > \"\$POISON/sdlc/skills/retro/scripts/metrics.py\"
    bash \"\$POISON/sdlc/eval/smoke.sh\" --mutate skills/test-suite-generator/scripts/derive_counts.py 'the count primitive' 'the counting primitive' >/dev/null 2>&1"
  expect "smoke --mutate: an expectation red both before and after does not count as a kill (harness cr-001)" 1 bash -c "
    POISON=\"\$(mktemp -d)\"; cp -R '$ROOT' \"\$POISON/sdlc\"
    bash \"\$POISON/sdlc/eval/smoke.sh\" --only 'derive_counts on example' --mutate skills/test-suite-generator/scripts/derive_counts.py 'the count primitive' 'the counting primitive' >/dev/null 2>&1"
fi

echo "== cross-skill boundaries (PR pre-review, B-tier)"
# Two shared-logic decisions were made in opposite directions in one delivery. The rule now: a skill's
# script is self-contained, and a cross-skill import is OPTIONAL — its absence must not kill a run
# that never asked for it. Duplication is therefore deliberate, so it gets a test rather than a
# "keep in sync" comment, and the optional import gets one proving the degraded path works.
expect "version_sync_issues is code-identical in the commit and pr verifiers (deliberate copy, pinned)" 0 bash -c "python3 -c \"
import re, ast
def code(p):
    s = open(p, encoding='utf-8').read()
    m = re.search(r'^def version_sync_issues\\(.*?(?=^def |\\Z)', s, re.S | re.M)
    assert m, p
    fn = ast.parse(m.group(0)).body[0]
    if fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant):
        fn.body = fn.body[1:]          # each skill explains the same code to its own reader
    return ast.dump(ast.Module(body=[fn], type_ignores=[]))
assert code('$S/commit/scripts/verify_commit.py') == code('$S/pr/scripts/verify_pr.py'), 'the two copies have drifted apart'
\""
expect "verify_issue runs when the dos-extract neighbour is absent (optional import)" 0 bash -c "
  T=\"\$(mktemp -d)\"; cp -R '$ROOT' \"\$T/sdlc\"; rm -rf \"\$T/sdlc/skills/dos-extract\"
  python3 \"\$T/sdlc/skills/issue/scripts/verify_issue.py\" '$S/issue/eval/fixtures/good_issue.md' >/dev/null"
expect "lint_cards runs when the dos-extract neighbour is absent (optional import)" 0 bash -c "
  T=\"\$(mktemp -d)\"; cp -R '$ROOT' \"\$T/sdlc\"; rm -rf \"\$T/sdlc/skills/dos-extract\"
  python3 \"\$T/sdlc/skills/plan-cards/scripts/lint_cards.py\" '$S/plan-cards/eval/fixtures/cards_good' >/dev/null"
expect "a twin whose given is not a mapping is rejected, never skipped (PR pre-review)" 1 bash -c "python3 -c \"
import yaml
d=yaml.safe_load(open('$S/donewhen-extract/eval/fixtures/v2_good.yaml'))
h=next(a for a in d['acceptance'] if a.get('kind')=='mechanical' and a.get('ears_type','event')!='unwanted')
t=next(a for a in d['acceptance'] if a.get('paired_with')==h['id'] or (a.get('ears_type')=='unwanted' and a.get('observe')==h['observe']))
t['given']='empty query'
yaml.safe_dump(d,open('$TMP/v2_given_str.yaml','w'),allow_unicode=True,sort_keys=False)
\"; python3 '$S/donewhen-extract/scripts/validate_done_when_v2.py' '$TMP/v2_given_str.yaml'"
expect "solo selfreview refuses a file that is not a review record (PR pre-review)" 1 bash -c "
  T=\"\$(mktemp -d)\"; cd \"\$T\"; git init -q .; printf 'x' > f.yaml
  bash '$S/review-loop/scripts/pr-poll.sh' selfreview 1 f.yaml >/dev/null 2>&1"
expect "solo selfreview accepts a real /pr-review record (PR pre-review)" 0 bash -c "
  T=\"\$(mktemp -d)\"; cd \"\$T\"; git init -q .
  printf 'review:\n  target: origin/main..HEAD\n  mergeable: \"yes\"\n  findings: []\n  rationale: walked every changed script\n' > g.yaml
  bash '$S/review-loop/scripts/pr-poll.sh' selfreview 1 g.yaml >/dev/null 2>&1"

if [[ -z "${SMOKE_NESTED:-}" ]]; then
  : # placeholder so the following fi still balances
fi

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
# dogfood 2026-09-06 (I-08 / I-40 / I-41 / I-55): G2's own record listed six criteria this validator
# passed over, so the gate did by eye what a script should do. These are those criteria compiled.
V2T="$TMP/v2_twin_not_selfsufficient.yaml"
python3 -c "
import yaml,sys
d=yaml.safe_load(open('$FXV/v2_good.yaml'))
happy=next(a for a in d['acceptance'] if a.get('kind')=='mechanical' and a.get('ears_type','event')!='unwanted')
twin=next(a for a in d['acceptance'] if a.get('paired_with')==happy['id'] or (a.get('ears_type')=='unwanted' and a.get('observe')==happy['observe']))
happy['given']=dict(happy.get('given') or {}); happy['given']['seeded_rows']='120'
twin['given']={'input':'empty query'}
yaml.safe_dump(d,open('$V2T','w'),allow_unicode=True,sort_keys=False)
"
expect "unwanted twin whose given drops its pair's context is rejected (I-55)" 1 py "$S/donewhen-extract/scripts/validate_done_when_v2.py" "$V2T"
V2S="$TMP/v2_vague_statement.yaml"
python3 -c "
import yaml
d=yaml.safe_load(open('$FXV/v2_good.yaml'))
d['acceptance'].append({'id':'AC-900-a','req':d['based_on'][0],'kind':'human','observe':'ui:dashboard#tiles','statement':'the page feels fast and the copy is friendly','judge':'product','evidence':'checklist'})
yaml.safe_dump(d,open('$V2S','w'),allow_unicode=True,sort_keys=False)
"
expect "human AC statement with an adjective and no number is rejected (I-08)" 1 py "$S/donewhen-extract/scripts/validate_done_when_v2.py" "$V2S"
V2F="$TMP/v2_form.md"; printf '# form\n\n- [F-01] the checker prints exit and rings_viewed ← PSL-001\n' > "$V2F"
expect "an expect key the signed form never names is rejected (I-40)" 1 py "$S/donewhen-extract/scripts/validate_done_when_v2.py" "$FXV/v2_good.yaml" --form-draft "$V2F"
expect "human ACs on one boundary with different judges are flagged (I-41)" 0 bash -c "python3 -c \"
import yaml
d=yaml.safe_load(open('$FXV/v2_good.yaml'))
for j in ('product','tech'):
    d['acceptance'].append({'id':'AC-91'+j[0]+'-a','req':d['based_on'][0],'kind':'human','observe':'ui:one#place','statement':'p95 under 200ms on the tile grid','judge':j,'evidence':'checklist'})
yaml.safe_dump(d,open('$TMP/v2_mixed_judges.yaml','w'),allow_unicode=True,sort_keys=False)
\"; python3 '$S/donewhen-extract/scripts/validate_done_when_v2.py' '$TMP/v2_mixed_judges.yaml' | python3 -c \"import json,sys; d=json.load(sys.stdin); assert any('mixed judges' in f for f in d['flags']), d['flags']\""

echo "== sdlc / lock_done_when.py two-stage"
L2="$TMP/lock2"; mkdir -p "$L2/tests"; cp "$FXV/v2_good.yaml" "$L2/done_when.yaml"; echo "test('x')" > "$L2/tests/a.test.ts"; pushd "$L2" >/dev/null
expect "sign stage g2" 0 py "$S/sdlc/scripts/lock_done_when.py" sign --signer-kind human --by human --stage g2 done_when.yaml
expect "re-sign stage l5 with tests" 0 py "$S/sdlc/scripts/lock_done_when.py" sign --signer-kind human --by tester --stage l5 done_when.yaml tests/a.test.ts
expect "verify reports stage l5" 0 bash -c "python3 '$S/sdlc/scripts/lock_done_when.py' verify | grep -q '\"stage\": \"l5\"'"
echo "tampered" >> tests/a.test.ts
expect "tampered locked test rejected" 1 py "$S/sdlc/scripts/lock_done_when.py" verify
# dogfood 2026-09-06 (I-30): a contract whose gate script can be edited mid-run is not frozen (INV-001)
git checkout -q -- tests/a.test.ts 2>/dev/null || printf "test('x')\n" > tests/a.test.ts
printf '#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n' > verify_thing.py
expect "l5 sign --gate records the gate script with role=gate (I-30)" 0 bash -c "python3 '$S/sdlc/scripts/lock_done_when.py' sign --signer-kind human --by tester --stage l5 --gate verify_thing.py --out .gate.lock done_when.yaml tests/a.test.ts | grep -q '\"gates\"' && python3 -c \"
import json
e=[f for f in json.load(open('.gate.lock'))['files'] if f['path']=='verify_thing.py']
assert e and e[0]['role']=='gate', e\""
expect "l5 sign without a gate script warns (I-30)" 0 bash -c "python3 '$S/sdlc/scripts/lock_done_when.py' sign --signer-kind human --by tester --stage l5 --out .nogate.lock done_when.yaml tests/a.test.ts | python3 -c \"import json,sys; d=json.load(sys.stdin); assert 'gate script' in (d.get('warning') or ''), d\""
printf '\n# edited mid-run\n' >> verify_thing.py
expect "changed gate script rejected and named as a deviation, not a criteria change (I-30)" 1 bash -c "python3 '$S/sdlc/scripts/lock_done_when.py' verify --lock .gate.lock > '$TMP/gate-verify.json'; rc=\$?; python3 -c \"
import json
d=json.load(open('$TMP/gate-verify.json'))
assert d['changed_gates']==['verify_thing.py'] and d['changed']==[], d
assert 'deviation' in d['why'], d['why']\" || exit 9; exit \$rc"
# dogfood 2026-09-06 (I-60): interpreting a G1 ruling changes no signed byte and must not need a proposal
printf '# G1 interpretations\n' > g1-interpretations.md
expect "sign refuses to lock a g1-interpretations file (I-60)" 2 py "$S/sdlc/scripts/lock_done_when.py" sign --signer-kind human --by human --out .g1.lock done_when.yaml g1-interpretations.md
printf '# G1 record\n- form draft sha256: deadbeef\n' > g1-record.md
expect "the signed record itself is still lockable (I-60)" 0 py "$S/sdlc/scripts/lock_done_when.py" sign --signer-kind human --by human --out .g1.lock done_when.yaml g1-record.md
popd >/dev/null

echo "== sdlc / .sdlc runtime state is not a deliverable (I-01)"
GI="$TMP/state-gitignore"; mkdir -p "$GI"; pushd "$GI" >/dev/null
git init -q -b main .
expect "init flags a repo whose .gitignore lacks .sdlc/ (I-01)" 0 bash -c "python3 '$SS' init --slug gi --title t | python3 -c \"import json,sys; d=json.load(sys.stdin); assert '.gitignore' in (d.get('warning') or ''), d\""
printf '.sdlc/\n' > .gitignore
expect "init is silent once .sdlc/ is ignored (I-01)" 0 bash -c "python3 '$SS' init --slug gi2 --title t | python3 -c \"import json,sys; d=json.load(sys.stdin); assert not d.get('warning'), d\""
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
# dogfood 2026-09-06 (I-66): a short sha and its full one are one commit; registering both must not count two
expect "card --commit resolves a short sha and dedupes against the full one (I-66)" 0 bash -c "FULL=\$(git rev-parse HEAD) && python3 '$SS' card CARD-03 --status doing --commit \$FULL >/dev/null && python3 '$SS' card CARD-03 --status done --commit \${FULL:0:7} >/dev/null && python3 -c \"
import json, subprocess
full=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()
c=json.load(open('.sdlc/conv/state.json'))['cards']['items']['CARD-03']['commits']
assert c==[full], c\""
cp "$FX/done_when.yaml" done_when.yaml; py "$SS" set contract.done_when=done_when.yaml >/dev/null
expect "archive copies trace.jsonl" 0 bash -c "python3 '$SS' archive --to specs/conv >/dev/null && test -f specs/conv/trace.jsonl"
# dogfood 2026-09-06 (I-85): metrics.py reads done_when.yaml FROM the archive; leaving it behind emptied the metric
expect "archive carries the contract retro reads (I-85)" 0 bash -c "test -f specs/conv/done_when.yaml"
expect "human-AC ratio is computable from a fresh archive (I-85)" 0 bash -c "python3 '$S/retro/scripts/metrics.py' specs --json '$TMP/conv-metrics.json' >/dev/null && python3 -c \"
import json
r=[f for f in json.load(open('$TMP/conv-metrics.json'))['features'] if f['feature']=='conv'][0]
assert r['human_ac_ratio'] is not None and r['contract_rework']['ac_total'], r\""
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
# I-84: the interception metric must count gate REJECT events from the history (ledger.md, else trace.jsonl),
# not state.json's final verdict — feat-b passed G1 in the end after being rejected twice, and the old
# implementation reported 0 interceptions for exactly that shape.
expect "metrics: G1 interceptions counted from gate history, not the final verdict (I-84)" 0 bash -c "python3 '$S/retro/scripts/metrics.py' '$S/retro/eval/fixtures' --json '$TMP/mg.json' >/dev/null && python3 -c \"import json; d=json.load(open('$TMP/mg.json')); t=d['totals']; f={r['feature']: r for r in d['features']}; assert t['g1_interceptions']==3, t; assert t['gate_rejections']=={'g1':3,'g2':1,'g3':0}, t; assert t['gate_decisions']=={'g1':4,'g2':4,'g3':2}, t; assert t['g1_interception_rate']==0.75, t; assert f['feat-b']['g1']=='pass' and f['feat-b']['gate_rejections']=={'g1':2,'g2':1,'g3':0}, f['feat-b']\""
expect "metrics: ledger is primary, trace is the fallback, state-only is labelled (I-84)" 0 bash -c "python3 '$S/retro/scripts/metrics.py' '$S/retro/eval/fixtures' --json '$TMP/mg2.json' >/dev/null && python3 -c \"import json; d=json.load(open('$TMP/mg2.json')); t=d['totals']; f={r['feature']: r for r in d['features']}; assert f['feat-b']['gate_source']=='ledger' and f['feat-a']['gate_source']=='trace' and f['feat-c']['gate_source']=='state(final-verdict-only)', f; assert t['gate_history_unavailable']==['feat-c'], t\""
expect "trace why AC-003-a walks 3 hops to hidden_variant_fail" 0 bash -c "python3 '$SSG/trace.py' why AC-003-a --trace '$S/retro/eval/fixtures/feat-a/trace.jsonl' | grep -q 'hidden_variant_fail'"
expect "trace impact AC-003-a reaches the escape" 0 bash -c "python3 '$SSG/trace.py' impact AC-003-a --trace '$S/retro/eval/fixtures/feat-a/trace.jsonl' | grep -q 'escape'"
TB="$TMP/trace_bad.jsonl"; printf '%s\n' '{"id":"ev-0001","at":"t","kind":"fail","refs":[{"type":"related_to","target":"CARD-01"}]}' '{"id":"ev-0002","at":"t","kind":"reflow","refs":[{"type":"caused_by","target":"ev-0099"}]}' > "$TB"
expect "trace lint: unknown edge type + dangling event rejected" 1 py "$SSG/trace.py" lint --trace "$TB"
# dogfood 2026-09-06 (I-65): sdlc_state.py writes actor refs (agent:/human:/a bare name from the `by` column)
# and git shas; a lint that flags its own writer is permanent noise a real dangling ref would drown in
TA="$TMP/trace_actors.jsonl"; SHA="$(git rev-parse HEAD)"
printf '%s\n' \
  "{\"id\":\"ev-0001\",\"at\":\"t\",\"kind\":\"gate\",\"by\":\"g1-judge\",\"refs\":[{\"type\":\"decided_by\",\"target\":\"agent:g1-judge\"}]}" \
  "{\"id\":\"ev-0002\",\"at\":\"t\",\"kind\":\"gate\",\"by\":\"alice\",\"refs\":[{\"type\":\"decided_by\",\"target\":\"human:alice\"}]}" \
  "{\"id\":\"ev-0003\",\"at\":\"t\",\"kind\":\"fail\",\"by\":\"acceptance-fleet\",\"refs\":[{\"type\":\"decided_by\",\"target\":\"acceptance-fleet\"}]}" \
  "{\"id\":\"ev-0003b\",\"at\":\"t\",\"kind\":\"gate\",\"by\":\"g2-judge\",\"refs\":[{\"type\":\"decided_by\",\"target\":\"g2-judge\"}]}" \
  "{\"id\":\"ev-0004\",\"at\":\"t\",\"kind\":\"card\",\"by\":\"engine\",\"refs\":[{\"type\":\"references\",\"target\":\"$SHA\"},{\"type\":\"references\",\"target\":\"${SHA:0:7}\"}]}" > "$TA"
expect "trace lint: actor refs and resolvable shas are not dangling (I-65)" 0 py "$SSG/trace.py" lint --trace "$TA" --base "$ROOT"
TA2="$TMP/trace_actors_dangling.jsonl"; cat "$TA" > "$TA2"
printf '%s\n' "{\"id\":\"ev-0005\",\"at\":\"t\",\"kind\":\"note\",\"by\":\"engine\",\"refs\":[{\"type\":\"references\",\"target\":\"not-an-actor-or-anything\"}]}" >> "$TA2"
expect "trace lint: a genuinely dangling target is still rejected (I-65)" 1 py "$SSG/trace.py" lint --trace "$TA2" --base "$ROOT"

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

echo "== acceptance-fleet / next_iteration.py + qa_facts.py"
AF="$S/acceptance-fleet/scripts"; FXA="$S/acceptance-fleet/eval/fixtures"; RL="$FXA/ratchet-log"
# I-72: the baseline comes from iteration N-1's own output. The fixture reproduces the real defect —
# iteration-003 recorded baseline_score 3.5 while iteration-002 actually produced 4.0.
expect "next_iteration: baseline derived from iteration N-1, not the task file (I-72)" 0 bash -c "python3 '$AF/next_iteration.py' '$RL' 3 --format json 2>/dev/null | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['PREV_GAMING_SCORE']=='4', d; assert d['PREV_ITER_DIR'].endswith('iteration-002'), d; assert d['GAMING_TRAJECTORY']=='3.5,4', d; assert d['PREV_SNAPSHOT'].endswith('iteration-002/impl-snapshot.tar.gz'), d; assert d['PREV_QA_REPORT'].endswith('iteration-002/fleet-outputs/qa-reviewer.yaml'), d; assert d['PREV_PM_REVIEW'].endswith('iteration-002/fleet-outputs/pm-reviewer.yaml'), d\""
expect "next_iteration: a recorded baseline that disagrees with the log is named (I-72)" 0 bash -c "python3 '$AF/next_iteration.py' '$RL' 3 --format json 2>/dev/null | python3 -c \"import json,sys; d=json.load(sys.stdin); b=d['BASELINE_DISCREPANCY']; assert 'iteration-003' in b and '3.5' in b and 'iteration-002' in b, b\""
expect "next_iteration: iteration 1 carries nothing forward" 0 bash -c "python3 '$AF/next_iteration.py' '$RL' 1 --format json 2>/dev/null | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['PREV_ITER_DIR']=='' and d['PREV_GAMING_SCORE']=='' and d['PREV_GAMING_BAND']=='unknown', d\""
expect "next_iteration: missing predecessor refuses to dispatch" 1 py "$AF/next_iteration.py" "$RL" 9
expect "next_iteration: shell output is eval-able and sets the vars" 0 bash -c "eval \"\$(python3 '$AF/next_iteration.py' '$RL' 3 2>/dev/null)\"; [ \"\$PREV_GAMING_SCORE\" = 4 ] && [ \"\$GAMING_BLOCK_AT\" = 7 ] && [ \"\$PREV_GAMING_BAND\" = elevated ]"
# I-68: the two ratchet-band thresholds are configuration, read from done_when.yaml, not literals in prose.
expect "next_iteration: gaming band read from done_when.yaml (I-68)" 0 bash -c "python3 '$AF/next_iteration.py' '$RL' 3 --done-when '$FXA/done_when_bands.yaml' --format json 2>/dev/null | python3 -c \"import json,sys; d=json.load(sys.stdin); assert d['GAMING_DONE_BELOW']=='5' and d['GAMING_BLOCK_AT']=='6', d; assert d['PREV_GAMING_BAND']=='clean', d; assert d['SPEC_DRIFT_TRIGGER']=='4', d\""
expect "next_iteration: inverted band rejected — it would leave scores with no rule (I-68)" 1 py "$AF/next_iteration.py" "$RL" 3 --done-when "$FXA/done_when_bad_bands.yaml"
# I-71: drift may read qa's measurements, never its findings, severities or decision.
expect "qa_facts: projection keeps measurements, drops findings/decision (I-71)" 0 bash -c "python3 '$AF/qa_facts.py' '$FXA/qa-reviewer-full.yaml' --output '$TMP/qam.yaml' >/dev/null && python3 -c \"import yaml; m=yaml.safe_load(open('$TMP/qam.yaml'))['qa_measurements']; assert m['scope']['tests_executed']==245 and m['mutation']['kill_rate']==0.758 and m['results']['integration']['duration_seconds']==145, m; assert not ({'decision','decision_reasons','findings','num_findings','maintenance_issues','regressions','caveats'} & set(m)), sorted(m); assert 'hint' not in m['mutation']['surviving_mutants'][0], m['mutation']; assert set(m['provenance']['omitted_keys'])>={'decision','findings','caveats'}, m['provenance']\""
expect "qa_facts --check: a clean projection passes" 0 bash -c "python3 '$AF/qa_facts.py' '$FXA/qa-reviewer-full.yaml' --output '$TMP/qam2.yaml' >/dev/null && python3 '$AF/qa_facts.py' --check '$TMP/qam2.yaml'"
expect "qa_facts --check: a smuggled decision/finding is caught (I-71)" 1 py "$AF/qa_facts.py" --check "$FXA/qa-measurements-leaky.yaml"
expect "qa_facts --check: findings buried inside a measurement subtree are caught too" 1 py "$AF/qa_facts.py" --check "$FXA/qa-measurements-nested-leak.yaml"
expect "qa_facts: a non-qa document is refused" 1 bash -c "printf 'gaming_assessment:\\n  gaming_risk_score: 4.0\\n' > '$TMP/notqa.yaml' && python3 '$AF/qa_facts.py' '$TMP/notqa.yaml'"

echo
echo "smoke: $pass passed, $fail failed${ONLY:+, $skipped skipped (--only $ONLY)}  (tmp: $TMP)"
[[ $fail -eq 0 ]]
