---
component: persona-5layer
version: 0.1.0
purpose: Five-layer persona structure — Identity, Values, Work Style, Communication, Relationships — that gives a persona psychological coherence without emotional-wound depth.
required_for_schemas: [self, collaborator, friend, mentor]
optional_for_schemas: [public-domain]
depends_on: [identity]
produces: []
llm_consumption: eager
---

## Purpose

`persona-5layer` is the workhorse psychological model for persona skills that describe **living, currently-functional** subjects whom the user knows operationally: themselves, colleagues, mentors, friends. It is **not** a diagnostic model (no MBTI, no enneagram) and it deliberately omits the emotional-wound / core-tension layer — that layer belongs in `persona-6layer` and is reserved for `loved-one` schemas where emotional depth is the raison d'être.

The five layers are chosen to be **actionable at runtime**: given a user question, the persona consults (a) Identity to know who it is, (b) Values to decide what matters, (c) Work Style to decide how to approach, (d) Communication to decide how to phrase, (e) Relationships to decide how this answer lands with others. Each layer carries 3-7 observations plus 1-2 verbatim corpus quotes per observation, so Phase-4 persona-judge can verify grounding.

## The Five Layers

1. **Identity** — who they are on a name-tag (name, role, credentials, self-description). Overlaps with `identity` component but goes deeper: identity-as-stated vs. identity-as-lived.
2. **Values** — what they care about, prioritize, refuse to compromise on.
3. **Work Style** — how they approach problems: planning horizon, bias-to-action, risk tolerance, preferred collaboration mode.
4. **Communication** — how they convey information (complements `expression-dna`; this layer is about WHAT they say, DNA is about HOW).
5. **Relationships** — how they engage with others: boundaries, reciprocity patterns, alliance-building style.

## Extraction Prompt

**Input**: primary corpus (chat logs / emails / essays) + `identity` component + (optional) 360-degree feedback from known contacts.

**Output**: markdown with five level-2 sections, each with 3-7 observation bullets + verbatim quotes.

**Prompt** (executable):

```
Extract a five-layer persona model. Execute each layer as a separate pass;
do NOT mix layers in a single sweep.

LAYER 1 — IDENTITY
  Probe: how does the subject introduce themselves? What adjectives
  recur in self-description? Is stated-identity congruent with
  observable-identity (their actions)?
  Output: 3-7 bullets, each with ≥1 verbatim quote.

LAYER 2 — VALUES
  Probe: what does the subject refuse to compromise on? What do they
  praise / criticize in others? What patterns of "I would rather X
  than Y" appear?
  Output: 3-7 bullets, each with ≥1 quote. Values MUST be phrased as
  "prioritize X over Y" when possible (values are comparative).

LAYER 3 — WORK STYLE
  Probe: planning horizon (hours vs. years)? Bias to action vs.
  analysis? Preferred work mode (solo / pair / team)? How do they
  handle ambiguity? How do they handle failure?
  Output: 3-7 bullets, each with ≥1 quote from a work context.

LAYER 4 — COMMUNICATION (complement to expression-dna)
  Probe: WHAT topics do they raise unprompted? What do they NEVER
  raise? How much context do they give before asking? Do they confirm
  understanding or assume it?
  Output: 3-7 bullets. NOT about style (that's DNA); about content
  preferences and conversational contract.

LAYER 5 — RELATIONSHIPS
  Probe: who do they name as close? What reciprocity patterns (do
  they offer help unprompted? ask for help?)? How do they manage
  conflict?
  Output: 3-7 bullets, each with ≥1 quote. REDACT names per policy.

CROSS-LAYER CHECK:
  After all 5 layers, verify at least 2 observations from different
  layers are mutually CONSISTENT (e.g., Values-bullet "prioritizes
  craft over speed" should align with Work-Style bullet "prefers
  iteration to shipping"). If all layers are internally consistent
  but NOT cross-consistent, flag a tension for `internal-tensions`
  component or producer review.

ANTI-EXAMPLES:
  - A layer compressed to a single paragraph → reject; must be
    bulleted observations.
  - A bullet without a quote → allowed for ≤1 bullet per layer; any
    more fails extraction.
  - Layer 6 content (emotional wound) appearing here → move to
    persona-6layer (if schema supports) or drop.
```

## Output Format

Generated `components/persona-5layer.md` emits:

```markdown
# Persona — Five Layers

## Layer 1: Identity

- **{observation}** — "{verbatim quote}" ({source-tag})
- **{observation}** — "{verbatim quote}" ({source-tag})
- ...

## Layer 2: Values
... (same shape) ...

## Layer 3: Work Style
...

## Layer 4: Communication
...

## Layer 5: Relationships
...

## Cross-Layer Notes

- {optional — how layers reinforce or tension with each other}
```

Each level-2 heading is one layer. Each layer: 3-7 bullets. Each bullet: one bolded observation + at least one verbatim quote (in-line or as block-quote) with a source tag.

## Quality Criteria

1. **All 5 layers present**, each with 3-7 bullets. A missing layer or layer with <3 bullets fails extraction.
2. **Verbatim quote coverage**: ≥80% of bullets have a verbatim quote; no layer has more than 1 quote-less bullet.
3. **Cross-layer consistency** visible: a reader can point to at least 2 pairs of bullets across different layers that reinforce each other (a coherent subject leaves such traces).
4. **Not merged with persona-6layer**: a sixth layer about emotional wounds is NOT present; if it fits, re-target to `persona-6layer` component.

## Failure Modes

- **Layers collapsed into one big description** — a common DILUTE failure. Layers must be distinct and separately consultable at runtime.
- **Layer content leakage**: Values bullets that read like Work-Style bullets. Layers should be *mostly* orthogonal; re-home misplaced content.
- **Paraphrase over quote** — "he seems to value craft" with no quote. Reject; either find a quote or drop the bullet.
- **Single-source corpus**: all quotes from a single chat thread or a single article. Require at least 2 distinct source contexts per layer.
- **Sterile / neutral persona** — no observations sharp enough to differentiate the subject from a generic professional. Rerun with tighter primary-source filtering.

## Borrowed From

- `titanwings/colleague-skill` — https://github.com/titanwings/colleague-skill — origin of the 5-layer Work+Persona architecture for collaborators. `[UNVERIFIED-FROM-README]` README fragment: *"Persona 块 5 层：Identity / Values / Work Style / Communication / Relationships，每层 3-7 条观察 + 原句佐证"*.
- `notdog1998/yourself-skill` — https://github.com/notdog1998/yourself-skill — adapted the 5-layer model for self-distillation where Layer 1 = Identity-as-lived vs. stated. `[UNVERIFIED-FROM-README]` README fragment: *"双层：self-memory + persona 5 层；Layer 1 需刻意对比 stated vs observed"*.
