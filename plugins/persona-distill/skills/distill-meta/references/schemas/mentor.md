---
schema: mentor
label_zh: 导师 / 老板 / 前辈
label_en: mentor
version: 0.2.0
required_components:
  - hard-rules
  - identity
  - work-capability
  - persona-5layer
  - decision-heuristics
  - mental-models
  - expression-dna
  - honest-boundaries
  - correction-layer
optional_components:
  - computation-layer
  - internal-tensions
  - execution-profile    # recommended for mentors with rich 1-on-1 / post-mortem corpus
typical_corpus_sources:
  - 1-on-1 记录 / one-on-one session notes
  - 决策回顾 / post-mortems & decision reviews
  - 工作方法论分享 / methodology lectures & docs
  - 读书会 / book-club transcripts they led
  - 邮件 / email memos where they teach
produced_files:
  - SKILL.md
  - manifest.json
  - components/hard-rules.md
  - components/identity.md
  - components/work-capability.md
  - components/persona-5layer.md
  - components/decision-heuristics.md
  - components/mental-models.md
  - components/expression-dna.md
  - components/honest-boundaries.md
  - components/correction-layer.md
  - knowledge/
  - conflicts.md
  - validation-report.md
unvalidated: true
---

# Schema: mentor / 导师

> ⚠️ **This schema ships unvalidated — no dog-food persona has been generated yet.** See §Unvalidated Caveats.

## Subject Type

`mentor` distills a **boss, advisor, senior peer, or teacher** — someone the user seeks out for **guidance on decisions and methodology**, not for execution. The output is not "what would they do?" but "**what would they teach me to do, and how would they reason about it?**"

Subject type in manifest: `identity.subject_type = "real-person"`. Distinct from `collaborator` (peer execution) and `public-mirror` (public figure visible only through public artifacts).

## Required Components

- `hard-rules` — refuse impersonation for decisions outside their domain; flag when user is fishing for approval.
- `identity` — role, mentorship history, typical advice domains.
- `work-capability` — the craft they can still teach at the ground level.
- `persona-5layer` — how they deliver guidance (Socratic? directive? storytelling?).
- `decision-heuristics` — **5-10 if-then rules** they apply when advising (borrowed from nuwa-skill).
- `mental-models` — **3-7 mental models** with **triple validation** (borrowed from nuwa-skill): each model must be attested in ≥2 independent corpus sources and pass a counter-example test.
- `expression-dna` — 7-axis voice fingerprint.
- `honest-boundaries` — ≥3 admissions of "I'd refer you elsewhere for X."
- `correction-layer` — accumulates user corrections.

## Optional Components

- `internal-tensions` — add when the mentor is known to hold visible contradictions (e.g., "move fast" vs "sweat the details") that shape different advice in different contexts.
- `computation-layer` — add for mentors with a signature computational ritual (e.g., quant boss → ta-lib indicators; surgeon mentor → triage scoring). Per PRD §2.4 Example C.
- `execution-profile` — **recommended** when the mentor corpus is rich in narrated decisions (1-on-1 transcripts, post-mortems, named calls). Added v0.2.0. Phase 3.7 runs CDM 4-sweep to turn `decision-heuristics` IF-THEN rules + `mental-models` framings into 8 Macrocognition-category instruction-grade "situation → action" pairs. For mentors, this component compensates for the common "mentor describes but skill can't *act*" failure — the Profile tells the runtime *what to do first* when a user brings a problem, not just *how the mentor would reason*. Skip only if the mentor's corpus is sparse on events (e.g., methodology-lecture-only, zero 1-on-1s).

## Typical Corpus Sources

| Source | Weight | Purpose |
|--------|--------|---------|
| 1-on-1 notes | primary | `decision-heuristics` gold |
| Post-mortems / decision reviews | primary | `mental-models` triple-validation evidence |
| Methodology talks / internal docs | primary | `work-capability` |
| Book-club transcripts they led | secondary | `mental-models` cross-check |
| Teaching emails / memos | primary | `expression-dna` + heuristics |

## Produced Skill Structure

Per PRD §7 Schema 3:

```
{mentor-slug}/
├── SKILL.md
├── manifest.json
├── components/
│   ├── hard-rules.md
│   ├── identity.md
│   ├── work-capability.md
│   ├── persona-5layer.md
│   ├── decision-heuristics.md     ← "decision-framework.md" in PRD shorthand
│   ├── mental-models.md
│   ├── expression-dna.md
│   ├── honest-boundaries.md
│   └── correction-layer.md
├── knowledge/
│   ├── one-on-ones/
│   ├── post-mortems/
│   └── talks/
├── conflicts.md
└── validation-report.md
```

## Runtime Execution Logic

Per PRD §7 Schema 3, extended in v0.2.0 with the optional `execution-profile` step:

```
question received
  → decision-heuristics filters: which if-then rules apply?
  → mental-models analyzes through matching lenses (3-7 models, pick relevant ones)
  → persona-5layer decides delivery mode (Socratic question back? direct answer? story?)
  → IF user is asking the mentor to HELP DO a task (not just discuss one)
    AND execution-profile is present:
      → execution-profile: consult the 8 Macrocognition segments for the
        situation→action instructions the mentor applies when guiding
        execution of this kind of task; run Drift Prevention self-check
  → expression-dna shapes voice
  → honest-boundaries shortcuts to "I'd ask X about that" when out-of-domain
```

Key ordering:
- **heuristics filter BEFORE models analyze**. A mentor first checks "is this even a question I engage with?" (heuristic), then reasons deeply (model), then decides how to say it.
- **execution-profile only fires when the user wants hands-on guidance** — "how would you coach me through X?" — not for methodology discussion. For pure advice ("what do you think about Y?"), the flow stops at expression-dna + honest-boundaries. This prevents the Profile's RPD-style terseness from bulldozing the Socratic delivery that defines good mentorship.

## Quality Gate Hints

The `mentor` schema is especially sensitive to:

- **Methodology validity** — `mental-models` must survive triple validation (nuwa-skill framework).
- **Heuristic concreteness** — each if-then rule must be specific enough to produce different advice for different situations. No "it depends."
- **Socratic discipline** — if the real mentor asks back more than answers, the skill must too. `persona-5layer` Layer 2 (interaction style) is load-bearing.
- **Contradiction honesty** — when two heuristics conflict, say so; don't paper over.

## Unvalidated Caveats

- No dog-food `mentor` persona has been generated yet.
- The ordering "heuristics → models → persona" is a design hypothesis; real mentors may reason in reverse.
- `triple validation` (inherited from nuwa-skill) is documented in `references/extraction/triple-validation.md` but hasn't been tested on mentor-scale corpus (usually smaller than public-figure corpus).
- `work-capability` + `mental-models` overlap risk: both can absorb craft content; the split is brittle without worked examples.

## Example

```
Name: "Mr. L" (anonymized startup CEO mentor)
Sketch:
  - heuristic: "if you can't describe the customer in one sentence, stop building"
  - model: "distribution eats product"  (cross-validated in 4 separate talks)
  - delivery: starts answers with a counter-question 70% of the time
  - boundary: "I'm useless on pure research bets, ask Dr. Chen"
  - tension: preaches patience, fires people within 90 days — preserved, not smoothed
```
