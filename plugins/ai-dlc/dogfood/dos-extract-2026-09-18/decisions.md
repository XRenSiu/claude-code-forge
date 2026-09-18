# DOS Extraction — Decision Log (fresh run, dos-extract 0.11.0, `--auto`)

> Generated 2026-09-18 from `plugins/ai-dlc` (v1.9.0). This run exists to answer one question the
> plugin's owner asked after v0.11.0 landed: *does the two-layer skill actually extract the language,
> or did the hand-amended 0.4.0 just paper over the gap?* Product: `dos.yaml` beside this file, compared
> against the shipped `../../dos.yaml`. Every non-trivial call cites Judgment 1–4 by name.

## Naming waivers

- `object_count` — 8 objects. Judgment 2 re-run: RepoAsset merges into nothing (a Contract is per-Run and
  frozen at G2; a RepoAsset outlives every Run and changes by ontology-layer proposal). Judgment 4 re-run:
  its three consumers (issue closure, WorkUnit.dos_slice, the vocabulary sensor) live inside this context.
  Same conclusion as Amendment 0.2.0 of the shipped DOS, reached independently from the roster.

## Inventory summary (code + docs)

### Code-side inventory
- Project root: `plugins/ai-dlc`; languages: Python (48 scripts), YAML/JSON (28 structured files).
- Code channel: **1** class declaration (`Closure`, dos_closure.py) — this repository declares nothing in
  classes; the objects live in `state.schema.json` (29 top-level properties, `$defs/gate`), `graph.yaml`
  (kind-values: skill / handoff / loop_back / stage / sequential / interrupt / human / agent / conditional …),
  `loops.yaml`, `routing.yaml`, `sizing.yaml`, `triggers.yaml`, and in Markdown.
- Structured channel: 504 distinct nouns after the schema fix (see skill-issues.md I-1): `state.schema.json`
  was invalid JSON (a literal `\n` after the closing brace) and had been silently skipped as "unparsable" —
  the first run saw 388 nouns and no `$defs` at all. One file stays unparsable by design:
  `skills/pm-reviewer/references/finding-schema.yaml` is a schema-by-example with `<placeholders>`.
- Pruned framework noise: 8 terms (inventory.py's built-in list). Full table: `.dos-extract/01_inventory.md`.

### Docs-side inventory
- Corpora: `docs/*.md` (6) · `README.md` · `skills/*/SKILL.md` (29) · `skills/*/assets/*.yaml` (15) · `agents/*.md` (5).
- Roster: **108 labels**, every one with ≥ 1 hit. Counting command (rerunnable):
  `python3 skills/dos-extract/scripts/count_terms.py --terms .dos-extract/terms.txt --root . --group docs='docs/*.md'
  --group readme='README.md' --group skills='skills/*/SKILL.md' --group data='skills/*/assets/*.yaml' --group agents='agents/*.md'`
- Definitions found: 13 (ARCHITECTURE §16 术语) + ~10 in-line (§2 旋钮, §5 网格 / 地板, §6 三种再试也没用, §10 日记四格, §4 门的判别标准).
- Cross-references: 13 (`.dos-extract/01b_docs_terms.md`). Bounded-context hints: 脊柱 + 九环; four upstream, two downstream.

### Convergence between code and docs
| Pattern | Count | Notes |
|---|---|---|
| In both | ~60 | the state/graph/loops/routing/sizing vocabulary the docs also speak |
| Code only | ~25 | schema properties (`resume_binding`, `handled_by`, `size_source`…) → properties of objects, not terms |
| Docs only | ~20 | 旋钮 / 闭环 / 记忆通道 / 自治阶梯 / 归因 / 重派 / 完成标记 — concepts the docs name and no YAML declares; all placed |

## Classification (Judgment 1) — `.dos-extract/02_classification.md` (108 rows, every row with a Home)

Highest-value calls:
- **Note (解释日记) vs Event** — different lifecycle (a Note can be promoted into a project rule; an Event
  never is; the docs say they answer different questions) → not one object; but no identity or relations of
  its own → `vocabulary.Note` kind value of Run + `Promotion` kind process. The shipped 0.4.0 had read Note
  as "Event's evidence text" — **fresh-run correction #1**.
- **RoutingRule / SizingRule** — Judgment 3: the sixteen rows and six rules are numbers tune may change;
  the constitution is "routing exists" (R011) and "缺省从严" (R019) → kind policy, not `rules`.
- **Skill / Agent / MetaJudge / the five agents** — Pattern 7 (framework terms) → Node kinds and a role,
  never objects; the 29 skills and 5 agents are Node ids.
- **Slug** — kept a Run synonym, not a term: a `Slug` entry would make `slug` a homonym every card trips over.
- **InterfaceContract** — the docs' own 空白 row; recorded with `status: proposed`, not invented (Pattern 10).

## Convergence (Judgments 2 & 4) — `.dos-extract/03_convergence.md`

Same eight objects as the shipped DOS, reached from the roster. Homonyms declared on both sides: 环 → Loop | Ring,
Tier → SizeTier | CheckTier. **Fresh-run correction #2**: `dos.yaml` / `agent-map.md` were synonyms of both
RepoAsset and the kind terms DOS / AgentMap — the verifier flagged them as homonyms; the file names moved to
the kinds, RepoAsset keeps the generic words.

## Coverage (the exit's number)

| Ontology | Roster | Resolved | Unplaced |
|---|---|---|---|
| shipped **v0.3.0** (before the two-layer skill) | fresh 108 | **19 / 108** | 89 |
| shipped **v0.4.0** (hand-amended when the skill landed) | fresh 108 | **74 / 108** | 34: StateFile · Prereq · Autonomy · Resume · Doctor · ObserveBoundary · InterfaceContract · AllowedFiles · ForbiddenFiles · RedBaseline · RedGreen · Commit · TestStrategy · Floor · MetaJudge · FixPrompt · CompletionMarker · Redispatch · Isolation · Attribution · GateRecord · Promotion · RoutingRule · ClosedLoop · Knob · Breadth · TestVolume · Depth · SizingGrid · SizingRule · SizeExemption · Divergence · Watermark · Release |
| **this run** (0.11.0 `--auto`) | fresh 108 | **108 / 108** | — |

Command: `verify_dos.py dogfood/dos-extract-2026-09-18/dos.yaml --decisions … --terms .dos-extract/terms.txt`.
Resolvable labels: 61 (v0.3.0) → 337 (v0.4.0) → **520** (this run). Drift sensor on README + docs + SKILL.md:
candidates resolved 4 → 27 → **46**; counted findings 4 → 5 → 5 (`Tier` ambiguous by design; four `repo` / `unit` /
`work` / `kill_rate` token near-misses inherited from the objects-layer channel).

What the fresh run found that the hand amendment missed — and why: the hand amendment worked from the
2026-09-05 classification table (45 terms) plus §16. The fresh run re-read the docs with the placement table
in hand and the roster grew to 108: the **three knobs** and the **sizing grid** (§2/§5), the **second memory
channel** and **promotion** (§10), the **prereq-is-a-file** discipline (§3), **isolation / fix prompt /
completion marker / redispatch** (§9, rule 14), **attribution** and **gate records** (§4), **red baseline /
red→green** (§8), and the GitHub-side **commit / release** the lifecycle actually references. None of these
needed a new object; all of them needed a home.

## Self-review

| Criterion | Result | Notes |
|---|---|---|
| Simplicity (≤7 core objects) | pass (waived) | 8 objects, `object_count` waiver; 91 vocabulary terms |
| Consistency | pass | 0 rejects; 18 relationships resolve; 20 rules |
| Completeness (term coverage, `--terms`) | **108 / 108** | unplaced: none |
| Evolvability | pass | 10 open questions carried (Q001 Card vs WorkUnit stands) |
| Executability | pass | every `must_not` cites a rule / anti-pattern |
| Learnability | warn | 881 core-model lines > 800 (inherited: properties listed field-by-field; the 526 vocabulary lines are budgeted separately since 0.11.1) |

## Caveats for the human reviewer

1. This is `--auto`: every Judgment 1/2 call above was made by the machine and logged, not confirmed live.
2. The core sections (objects, relationships, rules, bounded contexts, anti-patterns, open questions) converged on
   the shipped 0.4.0 text and were taken from it verbatim so wording stays reproducible; the run's own work is the
   roster, the placements, the vocabulary, one composition (SizingGrid) and two behaviors (Note channel, sizing).
3. `Release` is modelled as an external of the GitHub surface while `release` is also a Stage — a value of Run.
   The homonym is real in the docs; the stage is the enum member, the tag+notes are the external. Reviewer to confirm.
