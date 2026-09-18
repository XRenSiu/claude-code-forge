# dos-extract — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural]` · date: 2026-06-24

> **What this is (and is not).** A persistent record of a *structural* (Tier-1) review by
> **2 independent judges emulating** skillwise's ruler (`docs/THEORY.md §1-4` + `write-skill`
> construction invariants + `shared/effect-gate.md`). It is **NOT** a run of the installed
> `evaluate-skill` skill, and **NOT** an official skillwise certification. Machine-readable
> verdict: `gate.json` beside this file.

## Verdict

- **Tier-1 (structural): PASS** — no blocking findings remain.
- **Tier-2 (effect delta): NOT RUN** → `static_only`. No held-out repo set + executor was
  available; per `effect-gate.md` a production skill whose required effect layer is unrun is
  `static_only`, **not** a certified `pass`.

## How it was reached (2 rounds, measure-after-change)

1. **Round 1** (2 judges): three blocking — (DE1) a welded numbered Stage-1a→5 step-march
   embedded across the references/scripts/assets, contradicting the body's "no step order"
   claim (over-fill / skill inertia); (DE3) the SKILL.md listed a `must_not`-trace check as a
   mechanical reject when `verify_dos.py` only flags it; and the exit section overstated the
   script as "the only guarantee."
2. **Fixes**: de-staged all references + `inventory.py` docstring + `decisions_template.md`
   (judgments/criteria content kept intact, scan logic byte-identical); moved the `must_not`
   trace to the semantic/flag section; reworded the exit to "mechanical pre-gate + real
   guarantee."
3. **Round 2** (2 fresh judges, 4-eyes): all blocking **closed** — de-stage verified by grep
   (empty), the 4 judgments + 5 code-vs-docs rules + anti-pattern catalog confirmed intact.
   Both ran `verify_dos.py` and confirmed product-level rejects (UI/impl-suffixed object name,
   undeclared relationship ref, >7 objects, empty open_questions).
4. **Post-re-judge nits fixed**: aligned the ">7 objects" wording (script rejects
   unconditionally; justification is a human waiver) and the section-presence claim
   (only objects/relationships/rules reject on omission; the rest are info).

## To upgrade `static_only` → certified `pass`

Pick ≥1 held-out repo, extract a DOS **with and without** the skill, assert on the produced
`dos.yaml` (ontology cleanliness, ≤7 objects, no UI/impl objects), require `delta_exist > 0`
with zero regressions. Then update `gate.json`.

## 2026-09-18 — the second gap: a clean sliver (v0.11.0)

The plugin's owner asked why the extracted DOS was «没什么用 … 只提取出很少一部分». Measured on the
plugin's own `dos.yaml`: 45 terms classified, 8 kept, **17 / 65** roster labels resolvable, the docs'
own 13-term glossary not lifted. Root cause was structural, not a bad run — the ≤7 discipline was the
only layer, so every Judgment 1 verdict other than «core object» had nowhere to land but `decisions.md`
prose. Industry (DDD Highlighted Core, Ontology 101 / METHONTOLOGY / NeOn glossaries, SKOS / ISO 1087 /
OBO alignment, Palantir / dbt / DataHub semantic layers) caps nothing and layers everything. The fix is a
second layer, `vocabulary`, resolved by the same closure and measured by `verify_dos.py --terms`; details
in `gate.json` (`dogfood_fixes`, 2026-09-18) and `plugins/ai-dlc/decisions.md` Amendment 0.4.0. Tier
stays `static_only`: the structural evidence grew (14 new expectations, 3 mutants killed — see the commit),
the effect layer is still unrun.

