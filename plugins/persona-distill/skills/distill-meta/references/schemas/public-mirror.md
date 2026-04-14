---
schema: public-mirror
label_zh: 公众镜像（思想家 / KOL）
label_en: public-mirror
version: 0.1.0
required_components:
  - hard-rules
  - identity
  - mental-models
  - decision-heuristics
  - expression-dna
  - internal-tensions
  - thought-genealogy
  - honest-boundaries
  - correction-layer
optional_components:
  - computation-layer
typical_corpus_sources:
  - 著作 / books, essays
  - 访谈 / interviews, podcasts
  - 推文 & 公开博客 / tweets & public blogs
  - 他人评价 / biographies, contemporaries' accounts
  - 决策记录 / public decision records, shareholder letters
  - 时间线 / public timeline of events
produced_files:
  - SKILL.md
  - manifest.json
  - components/hard-rules.md
  - components/identity.md
  - components/mental-models.md
  - components/decision-heuristics.md
  - components/expression-dna.md
  - components/internal-tensions.md
  - components/thought-genealogy.md
  - components/honest-boundaries.md
  - components/correction-layer.md
  - knowledge/
    # also research/ sub-files 01-writings.md .. 06-timeline.md per PRD §7 Schema 6
  - conflicts.md
  - validation-report.md
unvalidated: true
---

# Schema: public-mirror / 公众镜像

> ⚠️ **This schema ships unvalidated — no dog-food persona has been generated yet.** See §Unvalidated Caveats.

## Subject Type

`public-mirror` distills a **public figure as a thinker** — a philosopher, founder, essayist, KOL — whose value to the user is **perspective and thinking frames**, not methodology (that's `public-domain`). The goal: "**how would they see this?**"

Subject type in manifest: `identity.subject_type = "real-person"` (or `"fictional"` for literary figures). This schema is the closest descendant of nuwa-skill's design and the most-validated reference architecture we imitate — but still unvalidated in this pipeline.

## Required Components

- `hard-rules` — refuse to speak as the person on topics post-dating their public record; refuse to fabricate quotes.
- `identity` — public role, era, domains of influence.
- `mental-models` — **3-7 models**, each under **triple validation** (attested in ≥2 independent sources + passes counter-example test). Borrowed from nuwa-skill.
- `decision-heuristics` — **5-10 if-then rules** extracted from public decisions.
- `expression-dna` — 7-axis voice from their written/spoken corpus.
- `internal-tensions` — **≥2 preserved contradictions**; this is a hard floor, not a target. Per nuwa-skill and `Preserve Tensions` principle.
- `thought-genealogy` — who influenced them → who they influenced. A bidirectional citation graph. Nuwa-originated component.
- `honest-boundaries` — ≥3 explicit "I did not engage with X" admissions.
- `correction-layer` — accumulates user corrections, including "they never said that."

## Optional Components

- `computation-layer` — rare; attach when the figure is known for a specific computation they publicized (Buffett intrinsic-value formulas, Knuth algorithms).

## Typical Corpus Sources

| Source | Weight | Purpose |
|--------|--------|---------|
| Books / essays | primary | `mental-models` triple validation |
| Interviews / podcasts | primary | `expression-dna` + heuristics |
| Tweets / short public posts | secondary | `expression-dna` rhythm |
| Biographies / contemporaries' accounts | secondary | `thought-genealogy` |
| Public decisions (shareholder letters, launches) | primary | `decision-heuristics` |
| Timeline of events | tertiary | cross-reference for `internal-tensions` |

Nuwa-skill's whitelist/blacklist (36氪/晚点/财新 vs 知乎/百度百科) applies here. See `references/source-policies/`.

## Produced Skill Structure

Per PRD §7 Schema 6:

```
{figure-slug}/
├── SKILL.md
├── manifest.json
├── components/
│   ├── hard-rules.md
│   ├── identity.md
│   ├── mental-models.md
│   ├── decision-heuristics.md
│   ├── expression-dna.md
│   ├── internal-tensions.md
│   ├── thought-genealogy.md
│   ├── honest-boundaries.md
│   └── correction-layer.md
├── knowledge/
│   └── research/
│       ├── 01-writings.md      ← borrowed naming from nuwa-skill
│       ├── 02-interviews.md
│       ├── 03-decisions.md
│       ├── 04-contemporaries.md
│       ├── 05-genealogy.md
│       └── 06-timeline.md
├── conflicts.md
└── validation-report.md
```

## Runtime Execution Logic

Per PRD §7 Schema 6:

```
question received
  → mental-models: which lens applies? (pick 1-2 relevant models)
  → decision-heuristics: what position would this lens push them to?
  → internal-tensions: does the proposed position contradict a known tension? (if so, surface the tension instead of suppressing it)
  → expression-dna: output in their voice
  → honest-boundaries: if question is post-record, refuse
```

Key design: **internal-tensions is a runtime consistency checker, not just an extraction artifact**. Before answering, the skill asks "am I about to say something that contradicts a documented tension? If yes, say the tension out loud."

## Quality Gate Hints

The `public-mirror` schema is especially sensitive to:

- **Voice Fidelity** — the dead-giveaway for a bad public-mirror is generic-thinker voice. `expression-dna` 7 axes must all be specific.
- **Triple-Validated Models** — each mental model must cite ≥2 corpus sources; single-source models get DILUTE'd.
- **Tension Preservation** — flattening contradictions into a clean answer is the canonical failure mode; `persona-judge` must test for it.
- **Genealogy Accuracy** — influence claims must be source-cited; no assumed "they must have read X."
- **Post-Record Refusal** — boundary test: ask about an event after their death / last public statement, skill must decline.

## Unvalidated Caveats

- No dog-food `public-mirror` persona has been generated yet by this pipeline (though the design borrows heavily from nuwa-skill's validated architecture).
- The "triple validation" routine is documented in `references/extraction/triple-validation.md` — its reproducibility across corpus types has not been tested here.
- `thought-genealogy` can easily hallucinate influence edges; needs a stricter citation gate than currently specified.
- Source-whitelist compliance (36氪 vs 知乎) is inherited from nuwa but not yet enforced by a linter.

## Example

```
Name: "Jobs" (public-mirror sketch, not persona)
Sketch:
  - model: "simplicity as subtraction, not addition" (validated across 2007 iPhone keynote + Stanford speech + biographer's accounts)
  - heuristic: "if you have to explain it, design again"
  - tension: "perfectionist product-maker" vs "ruthless shipper" — both preserved
  - genealogy: influenced by Dieter Rams + Zen Buddhism → influenced Ive, Musk-era Tesla
  - boundary: "I will not comment on AI — I died before the current wave"
```
