---
component: domain-framework
version: 0.1.0
purpose: N-dimensional expertise framework that gives a public-domain persona the mutually-distinct angles through which it reasons about its field.
required_for_schemas: [public-domain, topic]
optional_for_schemas: []
depends_on: []
produces: []
llm_consumption: progressive
---

## Purpose

`domain-framework` encodes *how an expert carves up their domain* — not the facts of the domain, but the **N mutually-distinct axes** along which questions are classified, analyzed, and resolved. A wealth-management expert, for example, might reason through six axes (cashflow, asset allocation, risk, tax, inheritance, psychology); an architecture reviewer might use four (correctness, performance, evolvability, operability). The framework is the skeleton that routes an incoming question to the right sub-frame before any content is applied.

For `public-domain` it is the primary reasoning substrate (the persona's method). For `topic` it serves as the *consensus-frame*: the shared scaffolding under which different practitioners' divergences can be compared. Without this component, a domain persona collapses into a list of opinions with no navigational structure, and extraction quality degrades into a grab-bag of case studies.

## Extraction Prompt

**Input**: curated corpus of the domain's methodology (books, courses, lecture notes, long-form articles from 2-5 seminal practitioners) plus any user-provided framing hints.

**Output**: YAML block listing 3-8 dimensions, each with 3-5 sub-concepts, 1-3 illustrative cases, and 1-3 anti-patterns.

**Prompt** (executable on corpus):

```
You are extracting the N-dimensional reasoning framework for a domain persona.

STEP 1 — Read the corpus and answer:
  "What are the mutually-distinct angles from which this domain is
   typically reasoned about? Two angles are mutually-distinct iff a
   question can load heavily on one and near-zero on another."

STEP 2 — Propose 3-8 candidate dimensions. For each, write:
  - name: short noun phrase (2-4 words)
  - one-sentence definition
  - the class of questions it dominates

STEP 3 — Distinctness check: for every pair (A, B), give a question that
  is ≥70% dimension A and ≤20% dimension B. If you cannot, merge A and B.

STEP 4 — For each surviving dimension, emit:
  - 3-5 sub-concepts (the internal vocabulary of this axis)
  - 1-3 cases from the corpus where reasoning on this axis resolved a
    question
  - 1-3 anti-patterns (common wrong moves on this axis)

ANTI-EXAMPLES (reject):
  - "Four dimensions that overlap 80%" (e.g., quality / excellence /
    rigor / craft — same thing).
  - Dimensions that are really *topics* (e.g., "Python" is not a
    dimension of software engineering).
  - Fewer than 3 dimensions (collapse to a list) or more than 8
    (fragmentation).
```

**Few-shot example** (wealth-management, six-dimension framework):

```yaml
- name: "Cashflow"
  definition: "Money in vs. money out over a time horizon."
  sub_concepts: ["income streams", "fixed obligations", "discretionary burn", "runway"]
  cases: ["evaluating whether a family can sustain a mortgage under income shock"]
  anti_patterns: ["confusing net-worth with cashflow — a house-rich family can be cash-poor"]
- name: "Asset Allocation"
  definition: "Distribution of capital across risk buckets."
  # ...
```

## Output Format

Generated `components/domain-framework.md` emits:

```markdown
# Domain Framework ({N}-dimension)

> The {N} mutually-distinct axes this persona uses to carve up {domain}.

## Dimension 1 — {name}
- **Definition**: ...
- **Sub-concepts**: ...
- **Dominant question class**: ...
- **Cases**: ...
- **Anti-patterns**: ...

## Dimension 2 — {name}
...

## Routing Table
| Question signature | Primary dim | Secondary dim |
|--------------------|-------------|---------------|
| ...                | Dim 3       | Dim 5         |
```

Required fields per dimension: `name`, `definition`, `sub_concepts` (3-5), `cases` (≥1), `anti_patterns` (≥1). The `Routing Table` must have ≥5 example question signatures.

Allowed variability: N ∈ [3, 8]; naming style follows the corpus's own vocabulary (do not translate or re-brand).

## Quality Criteria

1. **3 ≤ N ≤ 8** — fewer than 3 is not a framework, more than 8 fragments.
2. **Pairwise distinctness** — every dimension pair has at least one question that discriminates ≥70/20.
3. **Every dimension has ≥1 corpus-sourced case** — prevents armchair categorization.
4. **Routing table covers ≥5 exemplar questions** — the framework is *usable*, not decorative.
5. **Sub-concepts are corpus-vocabulary**, not invented — preserves the domain's native terminology.

## Failure Modes

- **Arbitrary categorization**: 4 dimensions that overlap 80% (the classic "quality / excellence / rigor / craft" collapse). Fix: apply the distinctness check and merge.
- **Dimension vs. topic confusion**: listing nouns (tools, sub-fields) instead of axes. A dimension is a *way of asking*, not a *thing asked about*.
- **Over-fragmentation**: 12 micro-dimensions borrowed from a textbook table of contents. Collapse siblings to their parent axis.
- **No routing table**: framework defined but never wired to questions — runtime cannot select which dim to invoke.
- **Framework lifted verbatim from one book** without cross-practitioner check — yields a persona of the *book*, not the *domain*.

## Borrowed From

- `midas.skill` — https://github.com/ (URL not findable per PRD §10) — six-dimension wealth-operating-system framework as the canonical exemplar of a domain persona that reasons through N mutually-distinct axes. `[UNVERIFIED-FROM-README]` PRD §5 Tier 4 fragment: *"midas.skill — 领域专家六维框架 — 抄作为 public-domain schema 示例"*. URL unverifiable (PRD §10 self-admits midas.skill has no findable link); component re-derived from first principles.
- Distinctness check (pairwise ≥70/20) is re-derived from the general pattern of mutually-exclusive-collectively-exhaustive (MECE) decomposition, not borrowed from a specific skill.
