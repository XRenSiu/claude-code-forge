# DOS Decision Log — ai-dlc

Companion audit trail for [`dos.yaml`](dos.yaml). Every non-trivial call traces to one of the
four judgments by name (`skills/dos-extract/references/judgments.md`).

## How to read this document

Two machines read parts of this file, so two sections have a fixed shape:

- `verify_dos.py --decisions` reads **`## Naming waivers`** — a bullet whose first backticked
  token is the waived name clears that name's reject and is reported under `waived`, never
  silently.
- `verify_vocabulary.py` reads **`## Vocabulary waivers`** with the same bullet convention.

Everything else is prose for people.

The 2026-09-05 baseline derivation — the full inventory, the Judgment 1 exclusion buckets, the
seven original merges, the bounded-context splits, the seventeen constitution rules — is **not
repeated here**. It lives at `dogfood/ring-audit/decisions.md` (394 lines) and is still correct
except for the rename. This file records what changed on top of it.

## Naming waivers

- `object_count` — 8 objects, past the ≤7 discipline. Judgment 2 was applied and found nothing
  to merge `RepoAsset` into: a `Contract` is per-Run and frozen by Gate g2, a `RepoAsset`
  outlives every Run and changes only through an ontology-layer proposal — different lifecycle,
  different permission model, first decisive test wins. Judgment 4 was applied and kept it in
  this context rather than splitting it out: all three consumers (issue closure,
  `WorkUnit.dos_slice`, the vocabulary sensor) sit inside R2–R8, so an upstream context would
  have made every card that names the ontology fail closure. Human sign-off: XRenSiu,
  2026-09-10. Revisit if a ninth candidate appears — two waivers in a row means Judgment 2 is
  being skipped, not that the domain grew.

## Vocabulary waivers

_(none yet — add bullets here when `verify_vocabulary.py` near-misses a term that is genuinely
out of domain.)_

---

# Amendment 0.2.0 — 2026-09-10

## Why the file moved out of `dogfood/ring-audit/`

The baseline was a dogfood artifact: produced by one Run, parked beside that Run's records, and
therefore invisible to `repo_assets.py`, which is what makes an ontology load-bearing (issue
closure, `dos_slice` closure, the vocabulary sensor). An ontology nothing can find is an
ontology nothing checks against — see the new anti-pattern in `dos.yaml` §10.

**It moved to `plugins/ai-dlc/`, not to the repository root.** `claude-code-forge` is a monorepo
of twelve plugins and this DOS covers exactly one of them. dos-extract's own edge case says one
bounded context per package; a root-level `dos.yaml` here would claim a scope it does not have.
`repo_assets.py` gained `--scope` for this (search the package first, fall back to the root), so
the repository can hold one shared `agent-map.md` at the root and a `dos.yaml` per plugin —
which is exactly the shape it has.

## The rename (mechanical, recorded because paths stopped resolving)

The plugin was renamed `sdlc` → `ai-dlc` on 2026-09-08. Every `plugins/sdlc/...` path in the
baseline had stopped pointing at anything. Renamed throughout: `plugins/sdlc/` →
`plugins/ai-dlc/`, `sdlc_state.py` → `aidlc_state.py`, `.sdlc/` → `.aidlc/`, `/sdlc` → `/ai-dlc`.
The rename itself is in `evolution_log`; the dogfood records keep their original bytes.

## Judgment 1 — is `RepoAsset` a business object?

| Step | Question | Answer |
|---|---|---|
| 1 | Describable without referring to a screen? | Yes — "the ontology files this repository's team shares". No interaction in the definition. |
| 2 | Infra suffix (`Repository` / `Service` / `Manager` / …)? | No. `Asset` is not on the suffix list, and the name is not compounded on a UI primitive. |
| 3 | A verb-noun describing an action? | No. |
| 4 | Remove it and the product still describes? | **No.** Remove it and the objective PSL-track trigger becomes self-assessment, `dos_slice` closure goes unchecked, and `card_context.md` loses "how this repo works". |

Measured, not asserted: **147 occurrences** across the corpus (24 docs · 95 skills · 28 data),
and the only noun that appeared between 2026-09-05 and now. The count is not cited to a scratch
file — a number nobody can recompute is exactly what `count_terms.py` exists to stop. Rerun it:

```sh
cat > /tmp/terms.txt <<'EOF'
Run = Run, 一次交付, slug, .aidlc/, .sdlc/
Contract = Contract, 契约, 判据契约, done_when
WorkUnit = WorkUnit, 任务卡, /CARD-\d+/, /(?<![通片贺])卡(?!通|片|住|尺)/
Gate = Gate, 门, /\bG1\b/, /\bG2\b/, /\bG3\b/
Event = Event, 账本, ledger, trace
Node = Node, 节点, graph.yaml
Loop = Loop, 环契约, loops.yaml
RepoAsset = 仓库级制品, repo_assets, agent-map, dos.yaml, invariants/
Skill = skill, SKILL.md
Finding = finding, 发现, verdict
Signal = 信号, signal, 指纹, fingerprint
Layer = 回流, /\b层\b/, routing.yaml
Tier = 体量, 档位, sizing, /\b[SML] 档\b/
Waiver = 豁免, waiver, waived
Note = 解释日记, notes.md, interpretation
Territory = Territory, 领地
EOF
python3 skills/dos-extract/scripts/count_terms.py --terms /tmp/terms.txt --root . \
  --group docs='docs/**/*.md' --group skills='skills/*/SKILL.md' --group data='skills/*/assets/*.yaml'
```

(run from `plugins/ai-dlc/`; the same terms file over the same corpus gives the same table byte
for byte, which is the only reason the numbers in the next section are arguable.)

## Judgment 2 — measured and **not** promoted

Five high-frequency terms were tested for objecthood and absorbed instead. Recording the
negatives matters more than the positive: a DOS that only lists what it accepted cannot be
argued with.

| Term | Count | Verdict |
|---|---|---|
| `Skill` | 396 | In this context a skill participates as a **`Node`** of kind `skill` (already a declared synonym). The skill-as-authored-artifact belongs to the plugin-authoring context, which is upstream and out of scope. |
| `Finding` / `verdict` | 280 | Belongs to the **acceptance-evaluation** context, already declared downstream in `bounded_contexts`. Not this context's object. |
| `Signal` / `fingerprint` | 228 | No independent lifecycle — it is the payload of a `fail` **`Event`**. Judgment 2 lifecycle test, absorbed. |
| `Layer` | 92 | A closed enum (card · plan · task · ontology · world) that the routing rules range over. A dimension of R011/R012, not a thing. |
| `Tier` / 体量档 | 85 | A property of **`Run`** (`intake.size` + `size_source`), not an object; `size_source` is what makes it auditable. |
| `Waiver` | 61 | An **`Event`** kind — R009 already says "an explicit Waiver Event". Confirms the baseline's merge. |
| `Note` / 解释日记 | 34 | Same skeleton as a ledger row (append-only, typed kind, never deleted) → **`Event`**. |
| `Territory` | 97 | Imported looper vocabulary; maps to `bounded_contexts.current_context`, stays in the 术语映射 table. |

## Judgment 3 — three rules lifted into the constitution

The test is "remove this and is the system still recognizably itself?"

- **R018 未检 ≠ 通过.** Remove it and every missing analyzer reads as a pass — which is exactly
  what had been happening to X1 for five days. Constitution: the plugin's entire claim is that
  a product is either machine-checked or gate-blocked, "no third kind".
- **R019 缺省从严.** Remove it and every gate is bypassable by forgetting. This one was **true
  since v0.10.0 and the baseline missed it** — it is a rule recovered, not a rule added. It is
  stated as a headline in `docs/ARCHITECTURE.md` ("一个靠遗漏就能打开的门不是门") and enforced
  in three independent places in `sizing.yaml`; a principle with three enforcement points and no
  entry in `rules` is the constitution's own drift.
- **R020 本体进版本库.** Remove it and the shared vocabulary degrades to one copy per person,
  which is not a shared vocabulary. Note this is a *constitution* call, not policy: it does not
  say which directory, it says *the bounded context's directory, under version control* — the
  directory is a `canonical_path` property, and properties are allowed to move.

Rejected as policy (Judgment 3, "still recognizably itself" = yes): the specific tier→level
table in `sizing.yaml.repo_assets` (S optional / M recommended / L required). That is tuning,
and tuning in `rules` makes the DOS a moving target.

## Two anti-patterns added — both exhibited, neither invented

1. **X1 declared everywhere, enforced nowhere** (closed v1.3.0). The three silent degradations
   are named in `dos.yaml` §10.
2. **A pre-gate pointing at a waiver nothing reads.** `verify_dos.py`'s >7 reject has always
   said "exceed only with a human waiver in decisions.md", and no code parsed one — so the
   only way past was to ignore a permanently red pre-gate. Found while writing this file;
   fixed the same day by teaching the existing `## Naming waivers` parser the `object_count`
   name. A gate you can only pass by ignoring it is not a gate.

## Known warnings, not fixed

`verify_dos.py` warns at 829 lines (budget 800 = ~100/object). The baseline was already at
103 lines/object; the properties are listed field-by-field rather than conceptually. Left as
is deliberately: three consumers resolve real field names against this file, and conceptual
summaries would break closure to save a page. Recorded here so it is a decision, not a drift.

## What this amendment did **not** do

- It did not re-derive the seven baseline objects. They all still carry weight (measured above)
  and none was re-examined against Judgment 2 — if one of them is wrong, this pass did not
  catch it.
- It did not reconcile against the PSL-derived `dos-proposal.yaml` (X1's as-is ↔ to-be step,
  `reconcile_dos.py`). Q003/Q007 from the baseline remain open and untouched.
- It did not measure whether any of this reduces vocabulary drift. That is Q010, and R017 says
  the claim may not exceed the evidence: the mechanism is smoke-covered, the effect is not.
