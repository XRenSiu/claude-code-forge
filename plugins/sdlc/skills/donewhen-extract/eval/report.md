# donewhen-extract — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-06-24

> **What this is (and is not).** A persistent record of a *structural* (Tier-1) review by independent
> judges **emulating** skillwise's ruler (`docs/THEORY.md §1-4` + `write-skill` construction invariants
> + `shared/effect-gate.md`). It is **NOT** a run of the installed `evaluate-skill` skill (not installed
> here), and **NOT** an official skillwise certification. Machine-readable verdict: `gate.json` beside this file.

## Verdict

- **Tier-1 (structural): PASS** — the one blocking finding is closed.
- **Tier-2 (effect delta): NOT RUN** → `static_only`. No held-out Issue set + executor; per `effect-gate.md`
  a production skill whose required effect layer is unrun is `static_only` (structurally sound, effect unverified).

## How it was reached (2 rounds, measure-after-change)

1. **Round 1** (1 judge): one blocking — `verify_done_when.py` enforced 纪律② ("every happy event/state
   clause carries an unhappy twin") by checking `paired_with` was a non-empty **string**, never resolving the
   reference. A dangling pointer **and** two happy clauses naming each other both passed `MECHANICALLY_CLEAN`
   (exit 0) — defeating the skill's stated #1 non-waivable rule (an overclaim vs the script's docstring).
2. **Fix**: 纪律② now resolves `paired_with` into a `by_id` index — rejects empty, dangling, and a twin that
   is not unhappy (`ears_type != unwanted` AND non-negative polarity). 纪律③-b coverage resolves bidirectionally;
   orphan unwanted clauses (paired_with → nothing) are caught.
3. **Round 2** (1 fresh judge, 4-eyes): blocking **closed**. Ran adversarial cards — dangling → REJECT,
   two-happy-mutual → REJECT, genuine happy+unwanted pair → exit 0, empty template → exit 1. No false positives;
   one acceptable non-blocking redundancy (a fully-orphaned happy clause draws two overlapping rejects, clearly named).

## To upgrade `static_only` → certified `pass`

Run the effect delta: pick ≥1 real Issue with `failure_memory`, run the extraction **with and without** the skill
on a held-out set, assert on the produced done_when card (falsifiability, happy/unhappy pairing, contradiction/coverage
clean) — not the wording — require `delta_exist > 0` with zero regressions. Then update `gate.json`.
