---
component: honest-boundaries
version: 0.2.0
purpose: Explicit, concrete list of things this persona CANNOT do, predict, or judge; prevents overreach and is a first-class scoring dimension in persona-judge. v0.2.0 adds an optional `## Execution Profile Gaps` section populated by Phase 3.7 execution-profile-extractor for Macrocognition / Knowledge Audit items that lacked event evidence.
required_for_schemas: [self, collaborator, mentor, loved-one, friend, public-mirror, public-domain, topic, executor]
optional_for_schemas: []
depends_on: [identity]
produces: []
llm_consumption: eager
---

<!-- v0.2.0 inbound-write note: `execution-profile` declares `produces: [honest-boundaries]` — the execution-profile-extractor appends to the optional `## Execution Profile Gaps` section below. The frontmatter does not carry a reverse `produced_by` field because the component contract §2 enumerates the allowed frontmatter keys and `produced_by` is not among them. The relationship is discoverable by scanning `produces:` fields across the component library. -->


## Purpose

Every persona has blind spots. `honest-boundaries` is the explicit, **per-persona** list of those blind spots — at least 3 items, each concrete, each with a reason. It is not a generic disclaimer ("I may be wrong sometimes"); it is a **specific inventory** of what this particular persona lacks the data, experience, or standing to answer.

This component exists because the single largest failure mode in persona skills is **overreach** — the persona confidently answers questions it shouldn't, hallucinating expertise it doesn't have. `honest-boundaries` is the runtime firewall: when a user question intersects a boundary, the persona acknowledges the limit, optionally degrades gracefully, and does **not** pretend.

It is also a scored dimension in `persona-judge` (10 points), so weak boundaries directly harm the skill's overall rating.

## Extraction Prompt

**Input**: full corpus + `identity.description` + any corpus meta (date range, platforms, missing categories).

**Output**: markdown list of ≥3 boundary entries, each structured.

**Prompt** (executable):

```
You are extracting honest boundaries for a persona skill.

For EACH of the following probes, try to fill a boundary entry. Ignore
probes that do not apply.

PROBE 1 — Temporal: what events occurred AFTER the corpus's last-dated
entry that this persona cannot have an opinion on?
PROBE 2 — Topical: what domains/topics are ABSENT from corpus or where the
subject explicitly disclaimed expertise?
PROBE 3 — Relational: what people / relationships does the persona not
know (e.g., colleague persona doesn't know subject's family life)?
PROBE 4 — Emotional/experiential: what life events (loss, parenthood,
illness, specific cultures) are missing from corpus?
PROBE 5 — Methodological: what KINDS of reasoning does the subject
explicitly avoid (e.g., "I don't do technical analysis", "I don't predict
markets")?

For each boundary, emit:
  - boundary: one sentence, CONCRETE. Starts with "Cannot ..." or
    "Will not speculate on ...".
  - reason: why (corpus-missing / subject-disclaimed / temporal / by-design).
  - graceful_degradation: what the persona does instead (answer the
    adjacent question / suggest a better source / acknowledge and stop).

Minimum: 3 boundaries. Target: 5-8. Maximum: 12.

ANTI-EXAMPLES (reject):
  - "I have limitations."  → too vague
  - "I may make mistakes." → universal, not persona-specific
  - "I am an AI."          → already in manifest disclaimer
  - "I don't know everything about X."  → reject; needs to be "Cannot
    answer questions about X because Y".
```

**Few-shot** (for a `public-mirror` Steve Jobs persona):

```markdown
- boundary: "Cannot comment on product launches after October 2011."
  reason: temporal — subject deceased; corpus ends 2011-10.
  graceful_degradation: "Suggest consulting contemporary product reviewers or successor executives."
- boundary: "Cannot speculate on Tim Cook's private management decisions."
  reason: corpus-missing — no direct first-hand material on Cook era.
  graceful_degradation: "Reframe to 'based on Jobs's own management heuristics, here is what he might have considered'."
```

## Output Format

Generated `components/honest-boundaries.md` emits:

```markdown
# Honest Boundaries

> This persona is explicit about what it cannot do. Listed below are
> {N} concrete limits with reasons and graceful-degradation strategies.

### 1. {boundary sentence}

- **Reason**: {reason}
- **Instead**: {graceful_degradation}

### 2. ...

## Execution Profile Gaps

<!-- Optional section. Present only when execution-profile component was emitted
     (Phase 3.7). Populated by execution-profile-extractor for Macrocognition /
     Knowledge Audit items that lacked event evidence. Each entry is a gap type,
     not a full boundary — these complement §1..N above rather than replace them.
     Absent entirely when execution-profile was skipped or not applicable. -->

- **{macrocognition_or_knowledge_audit_item}**: {gap | partial} — {one-line note
  explaining which evidence was missing from knowledge/}.
```

Each boundary is a level-3 heading with structured bullets. Numbered 1..N. The
optional `## Execution Profile Gaps` section is flat bullets (not level-3
headings) because each line is a single-fact gap, not a structured boundary.

## Quality Criteria

1. **Count ≥ 3** (contract minimum). Fewer fails the persona-judge Honesty-Boundaries dimension outright (0/10).
2. **Each boundary is CONCRETE** — names a specific topic, date, or method. "I have limitations" fails.
3. **Each boundary has a REASON** from the 5 probe categories, or an explicit fallback of "subject-disclaimed: [quote]".
4. **Each boundary has GRACEFUL DEGRADATION** — what to do instead; never only "I can't answer".
5. **Boundaries do not overlap with `hard-rules`** — boundaries are acknowledge-and-degrade; hard-rules are refuse-and-break.

## Failure Modes

- **Generic disclaimers**: "I may be inaccurate" — does not differentiate this persona from any other. DILUTE-grade content.
- **Under-count**: 1-2 boundaries signals a shallow corpus scan; persona-judge marks it as a Density failure.
- **Over-count as dumping ground**: 15+ items, many speculative. Caps at ~12.
- **Degradation missing**: boundary says "can't answer X" but no suggestion what to do instead — user-hostile.
- **Boundary contradicts `mental-models` / `work-capability`**: the persona claims competence elsewhere it disclaims here. Producer must cross-check.

## Borrowed From

- `alchaincyf/nuwa-skill` — https://github.com/alchaincyf/nuwa-skill — nuwa's Phase 4 "Honesty Boundaries" rubric dimension (10 points) directly motivates this component. `[UNVERIFIED-FROM-README]` README fragment: *"≥3 条具体局限，每条给出原因与降级方式；这是区分蒸馏质量和通用人设的关键"*.
