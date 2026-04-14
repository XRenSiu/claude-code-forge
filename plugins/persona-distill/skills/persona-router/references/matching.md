# Matching — Scoring Formula

**Owner**: `persona-router`
**Referenced from**: `SKILL.md` §"Step 3 — Score on Matching Dimensions"
**Input contract**: `plugins/persona-distill/contracts/manifest.schema.json`

For each `manifest.json` loaded by `manifest-scanner.md`, router computes a **weighted score
in [0, 1]** and returns a sorted list. This file specifies the formula, weights, lookup
tables, and tie-breaks exactly so router is auditable and reproducible.

---

## 1. Final Score

```
score(persona, question) =
    0.25 * schema_type_relevance
  + 0.30 * domain_overlap
  + 0.20 * component_coverage
  + 0.15 * density_bonus
  + 0.10 * primary_source_bonus
```

Weights sum to **1.00**. Each sub-score is normalized to `[0, 1]`. Therefore `score ∈ [0, 1]`.

**Recommendation threshold**: `score >= 0.30`. Below that, the persona is dropped. If **no**
persona clears the threshold, router returns the empty state (see §7).

**Default cap**: top 3 recommendations. Configurable via `router.config.json → top_k`.

---

## 2. `schema_type_relevance` (weight 0.25)

Router first classifies the user's question into a **category** by keyword and intent. Then
it looks up the relevance of the persona's `manifest.schema_type` (one of the 9 enum values
from `contracts/manifest.schema.json → schema_type`) against that category.

### Question categorization

| Category | Keywords / cues (zh + en) |
|----------|---------------------------|
| `strategic` | "该不该 / 怎么选 / trade-off / strategy / decide / 战略 / 取舍" |
| `tactical-work` | "怎么做 / how to implement / 执行 / 排期 / code review / API / 具体步骤" |
| `personal-life` | "关系 / 家人 / 健康 / 迷茫 / anxious / 纠结 / 我自己" |
| `domain-knowledge` | "原理 / 为什么 / how does X work / 解释 / definition / 历史" |
| `emotional` | "难过 / 压力 / 撑不住 / vent / 倾诉 / 安慰" |
| `creative` | "灵感 / 写一篇 / 想个名字 / brainstorm / style" |

### Relevance lookup (rows = schema_type, cols = category)

|                 | strategic | tactical-work | personal-life | domain-knowledge | emotional | creative |
|-----------------|----------:|--------------:|--------------:|-----------------:|----------:|---------:|
| `self`          | 0.5       | 0.3           | **0.9**       | 0.2              | **0.9**   | 0.6      |
| `collaborator`  | 0.6       | **1.0**       | 0.3           | 0.6              | 0.2       | 0.5      |
| `mentor`        | **0.9**   | 0.7           | 0.7           | 0.5              | 0.5       | 0.5      |
| `loved-one`     | 0.3       | 0.1           | **1.0**       | 0.1              | **1.0**   | 0.4      |
| `friend`        | 0.5       | 0.2           | 0.8           | 0.2              | 0.9       | 0.6      |
| `public-mirror` | **1.0**   | 0.4           | 0.4           | 0.6              | 0.2       | 0.7      |
| `public-domain` | 0.3       | 0.5           | 0.1           | **1.0**          | 0.1       | 0.4      |
| `topic`         | 0.2       | 0.3           | 0.1           | **0.9**          | 0.1       | 0.5      |
| `executor`      | 0.2       | **1.0**       | 0.1           | 0.2              | 0.1       | 0.3      |

Cells are hand-tuned starting points. If the router config provides a user-supplied table,
router prefers it; otherwise it uses the above.

Uncategorizable question → fall back to `0.5` across the board (neutral).

---

## 3. `domain_overlap` (weight 0.30)

Largest signal. Token-level overlap between the question and
`manifest.identity.domains` (see contract §`identity.domains`).

Algorithm:

1. **Question tokens**: lowercase, split on whitespace/punctuation, drop stopwords (both zh
   and en lists), keep tokens of length >= 2.
2. **Persona tokens**: same normalization applied to every string in `identity.domains`
   plus every word in `identity.description` and `identity.display_name`.
3. **Overlap**: `|Q ∩ P| / max(1, |Q|)`.
4. Clamp to `[0, 1]`.

`identity.domains` is weighted 2× in `P` (counted twice in the set union) because it is the
most curated signal. Description tokens are a soft tiebreak.

Edge case: persona has empty `domains` → rely entirely on description tokens; log that this
persona has no domain metadata and the match is weaker by construction.

---

## 4. `component_coverage` (weight 0.20)

How many of the **preferred components** for the question's intent are actually present in
`manifest.components_used` (contract §`components_used`, the 18-slug enum).

### Intent → preferred components table

| Question intent | Preferred components |
|-----------------|----------------------|
| `decision` (strategic, trade-off) | `decision-heuristics`, `mental-models`, `internal-tensions` |
| `memory` ("remember when...", "last time we...") | `self-memory`, `shared-memories`, `thought-genealogy` |
| `capability` ("can you build / review...") | `work-capability`, `computation-layer`, `hard-rules` |
| `feeling` (emotional support) | `emotional-patterns`, `self-memory`, `honest-boundaries` |
| `worldview` ("why do you think X?") | `mental-models`, `thought-genealogy`, `persona-5layer` |
| `domain` (factual / expertise) | `domain-framework`, `interpretation-layer`, `correction-layer` |
| `identity` ("who are you / what's your style") | `identity`, `expression-dna`, `persona-6layer` |

Intent is derived from the same question-categorization as §2, plus phrase detection (e.g.
"last time", "remember" → `memory`). Multiple intents may apply; take the union of
preferred sets.

### Formula

```
component_coverage = |preferred ∩ components_used| / |preferred|
```

If `preferred` is empty (unusual), return `0.5` (neutral — we don't know what to look for).

---

## 5. `density_bonus` (weight 0.15)

From `manifest.density_score` ∈ `[-1, 10]` (contract §`density_score`).

```
density_bonus = max(0, min(1, density_score / 10))
```

- `-1` ("not yet evaluated") → `0`. The persona loses 0.15 of its maximum possible score
  until `persona-judge` has run.
- `10` → `1.0`.

This is intentionally small (0.15): dense does not mean relevant.

---

## 6. `primary_source_bonus` (weight 0.10)

From `manifest.sources.primary_ratio` ∈ `[0, 1]` (contract §`sources.primary_ratio`).

```
primary_source_bonus = min(1, primary_ratio)   // already in [0,1]
```

If `sources` is absent or `primary_ratio` is missing → `0`. A persona built mostly from
secondary sources (interviews about X, not X's own writing) gets less benefit here; the
router still recommends it if other dimensions win, but the nudge favors first-hand
corpora.

---

## 7. Cold-Start / Empty-State

If after scoring **every** persona has `score < 0.30`, router returns an **empty
recommendation list** plus the standard empty-state block defined in
`templates/recommendation-template.md`, including the suggestion:

> "No suitable persona found for this question. Consider running `/distill-meta` to create
> one, or review the discovered skills below to see what you have installed."

Router must not lower the threshold to scrape together three recs. Honesty over chatter
(see SKILL.md §Constraints).

### Unvalidated flag

`manifest.unvalidated == true` (contract §`unvalidated`) does not change the score, but the
recommendation entry carries a visible ⚠ warning. This keeps the score deterministic while
still alerting the user.

---

## 8. Tie-Breaking

If two personas tie on `score` to 3 decimal places:

1. Higher `validation_score` wins (contract §`validation_score`, -1 treated as lower than 0).
2. If still tied, higher `density_score` wins.
3. If still tied, lexicographic `identity.name` (stable, deterministic).

---

## 9. Worked Examples

### Example A — "我该不该跳槽去做 staff eng?" (strategic + personal-life)

Candidate: `mentor-lisi` (schema_type=`mentor`, domains=["career","engineering-leadership"],
components_used includes `decision-heuristics` + `mental-models` + `thought-genealogy`,
density_score=7.2, primary_ratio=0.8, unvalidated=false).

- `schema_type_relevance` (strategic): `0.9`
- `domain_overlap`: question tokens {跳槽, staff, eng} ∩ {career, engineering, leadership} →
  ~0.33 after normalization
- `component_coverage` (intent=decision, preferred={decision-heuristics, mental-models,
  internal-tensions}): 2/3 = `0.667`
- `density_bonus`: 7.2/10 = `0.72`
- `primary_source_bonus`: `0.8`

`score = 0.25*0.9 + 0.30*0.33 + 0.20*0.667 + 0.15*0.72 + 0.10*0.8 ≈ 0.648`. ✅ above 0.30.

### Example B — "解释一下 Paxos" (domain-knowledge)

Candidate: `friend-alice` (schema_type=`friend`, domains=["photography","travel"],
components_used={identity, emotional-patterns, shared-memories}, density=6, primary=1.0).

- `schema_type_relevance` (domain-knowledge, friend): `0.2`
- `domain_overlap`: zero overlap → `0`
- `component_coverage` (intent=domain, preferred={domain-framework, interpretation-layer,
  correction-layer}): 0/3 = `0`
- `density_bonus`: `0.6`
- `primary_source_bonus`: `1.0`

`score = 0.25*0.2 + 0.30*0 + 0.20*0 + 0.15*0.6 + 0.10*1.0 ≈ 0.24`. ❌ below threshold — dropped.

If all candidates look like Alice, router returns the empty-state block.

---

## 10. Progressive Disclosure

- Scan inputs: `references/manifest-scanner.md`.
- Output rendering: `templates/recommendation-template.md`.
- Contract: `contracts/manifest.schema.json`.
