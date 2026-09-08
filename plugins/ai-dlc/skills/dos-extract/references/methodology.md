# DOS Methodology — Extraction-Adapted

This file is a working reference for the `dos-extract` skill. It distills the
parts of the DOS methodology relevant to **reverse-engineering** a DOS from
existing code, as opposed to authoring one from scratch.

---

## The concerns of an extraction, and what each one needs

The DOS methodology defines a 7-step flow originally meant for greenfield design
work. In extraction the same concerns appear, but they aren't a numbered
assembly line — each concern has its own inputs and its own real dependencies.
Here is what each one needs to be filled honestly:

- **`scope`** (fills `meta`, `scope`) — Needs project documentation as the
  primary source: README and `docs/` content read directly; code is the fallback
  when docs are absent.
- **`reuse`** — Needs the import graph and doc mentions: detected from imports of
  standard schemas (Schema.org, ActivityStreams, OpenAPI), and from explicit doc
  mentions of borrowed concepts.
- **nouns** (the raw candidate roster) — Needs both inventories: code via
  `inventory.py`, docs via LLM extraction. Both feed the classification work.
- **classify / converge** (the heart of the work) — Needs the noun roster, then
  applies Judgments 1, 2, and 4. Docs vocabulary takes priority for naming
  (Judgment 2).
- **relations + rules** (fills `relationships`, `rules`) — Needs the converged
  object set plus verbs from both inventories; rules come from code invariants
  AND docs "must"/"never" sentences; Judgment 3 filters policy out.
- **composition + behavior** (fills `composition`, `behaviors`) — Needs the
  object set plus query/aggregation code; docs descriptions provide better
  wording.
- **guidelines + anti-patterns** — Needs the anti-pattern checklist, codebase
  observations, AND team conventions documented in CONTRIBUTING/design docs.

These are dependencies, not a fixed workflow: you can't classify before you have
a noun roster, and you can't write `relationships` before the object set has
converged. But within those constraints the order is yours.

**Key insight**: extraction inverts the natural flow. In greenfield design you
**decide** scope first, then nouns. In extraction you **discover** nouns first,
then back into scope. With docs available, `scope` becomes much less
inferential — the team has often already written it down somewhere, and the
skill's job is to find and lift it accurately.

---

## Code vs. docs signal priority

When the code inventory and the docs inventory produce overlapping or divergent
signals, apply this priority hierarchy. **It is intentional and counterintuitive: docs
generally outrank code for ontology questions, even though code is more
"objective".** The reasoning: code reflects what was *built*, often under
deadline pressure with shortcut naming and partial refactors. Docs reflect
what the team *intends* and *talks about* — which is exactly what an ontology
should encode.

### Rule 1: For canonical naming — docs win

If docs and code use different terms for the same thing (e.g. docs say `Topic`,
code has `Node`), the docs term is canonical. The code is treated as having
drifted from product language and will be aligned in subsequent refactoring.

**Exception**: if the docs are clearly stale (last updated 2 years ago,
contradicted by recent code), code wins by default but flag the divergence
loudly in `decisions.md` and as an `open_question`.

### Rule 2: For object inclusion — agreement boosts confidence; disagreement is signal

| Code | Docs | Verdict |
|------|------|---------|
| ✓ high freq | ✓ high freq | High confidence: include as business object |
| ✓ high freq | ✗ absent | Possible internal-only concept. Include with reduced confidence; consider whether it's actually a value object or composition. |
| ✗ absent | ✓ high freq | High-priority `unclear`. The team talks about it but hasn't built it (yet), or built it under another name. Probably absorbs a code synonym during convergence (Judgment 2). |
| ✓ low freq | ✓ low freq | Low-priority `unclear`. May be a peripheral concept; let user decide. |

### Rule 3: For rules — docs are the constitutional source

Code-derived rules (validation logic, invariants) are often **policy** in
disguise: the current rate limit, the current free-tier ceiling, the current
allowlist. Docs-derived rules (especially from design decision records, ADRs,
RFCs) are far more likely to be **constitution**, because someone deliberately
wrote them down as commitments.

When the same rule appears in both forms, prefer the docs wording — it tends
to be at the right level of abstraction. When they disagree, the docs version
is usually constitution and the code version is the current implementation
of that constitutional commitment plus some policy trim.

### Rule 4: For Bounded Context boundaries — docs are decisive

Architecture documentation that names subsystems, modules, or services is
near-definitional evidence for Bounded Contexts. Code can hint at boundaries
through directory structure or service deployment, but those signals are
muddier. When the architecture doc says "Identity owns User; Workspace owns
Person" — that's the answer.

### Rule 5: Definitions trump everything

If `01b_docs_terms.md` has an entry in `Definitions found` for a term, that
definition wins:
- The term IS a business object (no classification doubt).
- The definition's wording IS the `description` field in `dos.yaml`.
- Any code-side variant that contradicts the definition is treated as drift.

### When to override these rules

Override docs in favor of code only when:
- Docs are explicitly marked stale or "draft" or "TODO".
- Recent commit history shows deliberate concept changes that docs haven't
  caught up with.
- The user explicitly tells you to prefer current code state.

In all override cases, document the override and rationale in `decisions.md`.

---

## Evaluation criteria (apply during self-review of the drafted DOS)

Borrowed from NeOn methodology, adapted for DOS:

### 1. Simplicity

> Can the core objects fit on a napkin?

Operationalized: **≤ 7 objects in the `objects` section.** Exceeding this is
allowed only with documented justification in `decisions.md`.

If exceeded, the most common cause is failure of Judgment 2 (synonyms not merged)
or failure of Judgment 4 (multiple contexts forced into one DOS).

### 2. Consistency

> Pick any two rules at random — do they fight?

Mechanical checks the AI can run:
- Every object referenced in `relationships` exists in `objects`. ✓
- Every relationship cardinality has both sides documented. ✓
- Every `rule` references only declared objects. ✓
- `agent_guidelines.must` and `must_not` don't contradict each other. ✓
- `anti_patterns.correct_approach` doesn't violate any `rule`. ✓

### 3. Completeness

> For every core user action, does the DOS describe a corresponding relationship?

Cross-check by listing the top 10 user-facing features (from README or docs)
and verifying each has a corresponding relationship in the DOS. Gaps go into
`open_questions`.

### 4. Evolvability

> Adding a new feature — does it cost a `rule` or a constitutional amendment?

This is hard to check at extraction time, but a useful proxy: **does the DOS
have any open questions?** A DOS with zero open questions is either trivial or
dishonest. Real systems always have unresolved boundaries.

If `open_questions: []` in the drafted DOS, regenerate at least 1-2 by
re-examining the classification and convergence work for items marked "unclear"
that were resolved without strong conviction.

### 5. Executability

> Could a fresh engineer read this DOS and write code that conforms?

Operationalized: every `agent_guidelines.must_not` should be specific enough that
a violation is detectable in a code review. Vague guidelines like "use good naming"
are excluded; concrete ones like "do not introduce `Node` as a class name; use
`Topic`" are required.

### 6. Learnability

> Can a new designer read this in 30 minutes?

Hard to test at generation time. Surrogate metric: total length of `dos.yaml`
should be reasonable. For a system with 6 objects, expect roughly 300-500 lines.
If the draft balloons to >800 lines, sections are likely over-detailed
(properties listed at field-by-field granularity instead of conceptual level).

---

## Versioning rules during extraction

The extracted DOS is **always versioned `0.1.0`**. Reasoning:

- `0.x.x` signals "draft, expect changes" — appropriate for an extracted-but-not-
  yet-team-validated artifact.
- `0.1.0` (not `0.0.1`) reflects that the structure is complete; what's draft
  is the *team consensus*, not the document.
- After the user reviews and edits, they can bump to `0.2.0` or `1.0.0` as
  appropriate.

The `evolution_log` should always include exactly one entry at extraction time:

```yaml
evolution_log:
  - version: "0.1.0"
    date: "<extraction date>"
    author: "<inferred from git config or 'unknown'>"
    change_type: "initial"
    summary: "Extracted from <project> via dos-extract skill"
    rationale: "Reverse-engineered baseline; pending team review"
    breaking: false
```

---

## What NOT to do

These are extraction-specific failure modes (separate from the general anti-patterns
in `anti_patterns.md`):

### Failure 1: Trusting the codebase's vocabulary uncritically

If the codebase calls something `Item`, that doesn't mean the DOS should.
Apply Judgment 2's sentence test. The DOS uses the **product team's**
vocabulary, not the **data layer's**.

### Failure 2: Including every detected verb as a relationship

Codebases have hundreds of verbs (`get`, `set`, `update`, `validate`, `format`,
`render`, ...). Most are infrastructure verbs, not domain verbs. Filter to
verbs that:
- Connect two **business** objects (not impl/UI).
- Read naturally as `Subject VERB Object` in plain English.
- Aren't generic CRUD (`create`, `update`, `delete` are usually subsumed by
  the lifecycle and don't need to be relationships).

Domain verbs typically include: `CONTAINS`, `BELONGS_TO`, `AUTHORS`, `FOLLOWS`,
`MENTIONS`, `LIKES`, `EMITS`, `BOUND_TO`, `DERIVES_FROM`, `MODIFIES`, `CONNECTS_TO`.

### Failure 3: Generating generic anti-patterns

The `anti_patterns` section is most valuable when entries are **specific to this
codebase's history**. Generic warnings ("don't use UI words as objects") belong
in `agent_guidelines`. The `anti_patterns` section should record patterns the
codebase **actually exhibited** (e.g. "this project initially had `TopicCard`
as a domain class until refactor 7c3a2f").

If you can't find codebase-specific anti-patterns, leave the section sparse and
note in `decisions.md` that this section requires team input to grow.

### Failure 4: Filling `open_questions` with cosmetic uncertainty

Bad open question: "Should we rename `Topic` to `Concept`?"
(This is bikeshedding, not a real architectural question.)

Good open question: "Should `Conversation` be allowed to span multiple Sheets,
or must it be bound to exactly one? Current code allows both, with inconsistent
behavior."
(This is a real semantic boundary question with downstream consequences.)

---

## Reference: Bounded Context detection heuristics

Useful when applying Judgment 4 during convergence. Signs that you're looking at
**multiple Bounded Contexts smooshed together**:

1. **Same noun, different fields elsewhere.** If `User` in module A has fields
   `{email, password}` and in module B has fields `{display_name, avatar,
   thinking_history}`, those are two contexts.

2. **Translation layer in code.** If you find `mapToUser()`, `userDTO`, or
   `UserAdapter` between modules, the codebase is already implicitly
   acknowledging context boundaries.

3. **Different teams own different parts.** If module A is owned by the Auth
   team and module B by the Product team, they likely have separate ubiquitous
   languages even if the surface vocabulary overlaps.

4. **Different change cadences.** If module A's `User` changes once a year and
   module B's `User` changes monthly, they're not the same `User`.

When 2+ of these signs are present, recommend splitting in `decisions.md`.

---

## Reference: How to read README/docs for `scope`

When filling the `scope` section from project documentation:

- **`in_scope`**: Look for sentences in the README that follow patterns like
  "X is a Y for Z", "We help users do W", or "The product enables...". Compress
  these into 2-3 sentences.

- **`out_of_scope`**: Look for sentences with patterns like "this does not
  handle", "for X, see Y", "this is not a replacement for", or roadmap items
  marked as "future". Also look at the README's "Non-goals" section if present.

- **`audience`**: Default to `[designers, PMs, frontend engineers, AI agents]`
  unless the README signals a different primary user (e.g. CLI tools usually
  add `developers`; data tools add `analysts`).

- **`success_criteria`**: This is the hardest to infer mechanically. If no
  signal exists in docs, leave it as a templated open question for the user.
