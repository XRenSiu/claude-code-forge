---
name: acceptance-spec
description: >-
  Turn a fuzzy natural-language requirement into a machine-verifiable acceptance contract.
  Drafts EARS-format requirements (five sentence types), runs a strict clarify loop
  (only three question types allowed: ambiguity / missing edge / undefined term;
  2-3 rounds, 3-5 questions per round, max 5 rounds total) to remove every [?] marker,
  then writes four files: proposal.md, spec.md (EARS with stable REQ-IDs),
  tasks.md (decomposed work), and done_when.yaml (the contract that ratchet
  and test-suite-generator will consume). Covers Steps 1-3 of the done_when pipeline.
  Triggers: "spec this requirement" / "draft EARS" / "done_when for X" /
  "clarify this feature" / "acceptance criteria" / "write the contract" / "/acceptance-spec".
argument-hint: "<natural-language requirement or path to brief>"
version: 0.1.0
user-invocable: true
---

# acceptance-spec — Natural language → EARS spec + done_when contract

You are invoked to turn the user's natural-language requirement (`$ARGUMENTS` or recent user message) into a four-file acceptance contract that downstream agents can mechanically consume.

**Say once at the start, then start working:**
> "I'm using the acceptance-spec skill. I'll draft EARS requirements, run a short clarify loop (only 3 question types, 2-3 rounds), then write proposal.md / spec.md / tasks.md / done_when.yaml."

Do not narrate further — just walk the phases.

---

## Iron rules (re-read before every phase)

1. **Three question types only — applies from S1 onward.** During clarify, the only legal questions are:
   (a) **`[ambiguity]`** — same wording supports >1 reasonable reading,
   (b) **`[missing edge]`** — exception/extreme/empty/concurrent case undefined,
   (c) **`[undefined term]`** — domain noun lacks a precise definition.
   Anything else (tech stack, library choice, framework preference, deployment) is **out of scope for this skill** — defer it to design/planning skills.
   **You must tag every `[?]` you write at S1 with one of the three tags above** (e.g. `[?] [ambiguity] ...`). The tagging is not a S2-only formality — at S1 it forces you to confirm the question is legal *before* surfacing it. If you cannot tag a `[?]`, do not write it. See `references/clarify-protocol.md` for full taxonomy with examples; you must read that file before S1 alongside `references/ears-syntax.md`.
2. **Convergence budget.** 3-5 questions per round, target convergence in 2-3 rounds, **hard cap at 5 rounds**. If round 5 still has open `[?]`, stop and tell the user the requirement is too large and must be split into multiple features — do not keep asking.
3. **Every REQ has a stable ID.** `REQ-001`, `REQ-002`, ... assigned at S1, never renumbered. If a clarify answer splits a REQ in two, the new one gets the next free ID. Use this same ID later in `based_on:` and in test `based_on:` tags so traceability is real.
4. **Every decision traces to one clarification answer.** Each REQ in the final `spec.md` has a `source:` line citing the user message that fixed it (e.g. `source: "user clarified at S2 round 1 Q3 that cancellation honors UTC boundary"`).
5. **Borrow OpenSpec's file format, not its CLI.** Output the four files as documented below; do not shell out to `openspec`, do not depend on it.
6. **You do not write tests.** Tests are Step 4 (`test-suite-generator`). Your job ends at `done_when.yaml`.
7. **Verifiable beats judgeable.** In `done_when.yaml`, prefer programmatic checks; only fall back to LLM-judge (`fitness:`) for things genuinely outside mechanical reach (doc clarity, agent usability, intent alignment).

If you catch yourself asking a question that is not in {ambiguity, missing edge, undefined term}, **delete it before sending**. Asking the wrong type is the most common failure of this skill.

---

## Phase map

```
S0  Bootstrap        read the brief, detect scope, pick the EARS sentence types you'll need
S1  Draft            NL → EARS, every fuzzy spot becomes a [?] marker
S2  Clarify loop     3 question types, 2-3 rounds, every [?] resolves into a sourced decision
S3  Solidify         write proposal.md / spec.md / tasks.md / done_when.yaml
```

The user only sees output at end of S1 (the draft + question list) and again at end of S3 (the four files). S2 is the interactive part. S0 is silent setup.

---

## S0 — Bootstrap

1. Parse `$ARGUMENTS`. If it points to a file, read it. If it's an inline description, use it directly. If it's neither, ask the user *once* to paste their requirement (this is not a "clarify question" — it's missing input).
2. Detect:
   - the **feature slug** (kebab-case, used as directory name) — derive from the user's nouns, do not invent something fancier;
   - the **likely scope** (single endpoint / multi-module / whole flow);
   - whether the brief already mentions specific UI / API / DB elements you must preserve verbatim later in existence checks.
3. Decide where the output goes:
   - default: `specs/<feature-slug>/` next to the user's working directory;
   - if the brief was pasted inline and no obvious project root exists, use `./specs/<feature-slug>/` and tell the user the path in S3.

Do not produce text output yet.

---

## S1 — Draft EARS

Read **both** `references/ears-syntax.md` and `references/clarify-protocol.md` once before writing. You need the 3-tag taxonomy from clarify-protocol *now* (at S1), not at S2, because every `[?]` you emit must already be a legal question type — see iron rule 1.

For each distinct requirement you can extract from the brief:

1. Pick the EARS sentence type that fits (Ubiquitous / Event-driven / State-driven / Unwanted / Optional). If a requirement needs >1 sentence type, split it into separate REQs.
2. Write it in the strict template. Do not paraphrase into prose — the rigid template is the whole point; it forces hidden assumptions to surface as gaps.
3. Mark every fuzzy spot with `[?]` followed by the question type tag and a short note about what's unclear. Cast a wide net — when in doubt, flag it. If you cannot tag a `[?]` as `[ambiguity]` / `[missing edge]` / `[undefined term]`, drop it.
4. Assign a stable `REQ-NNN` ID.

Output exactly this shape to the user:

````markdown
# <feature-slug> (draft)

## REQ-001 (<EARS type>)
<EARS sentence with [?] [<tag>] markers inline>

## REQ-002 (<EARS type>)
...

## Open questions
- [?] [<tag>] <one-line question, tagged with which REQ it affects>
- ...
````

Then immediately proceed to S2 round 1 in the same response — do not stop and wait for the user to scroll, just send the first batch of 3-5 clarify questions right after.

**Calibration check before sending:** if you produced fewer than 3 open questions for a non-trivial brief, you are under-flagging. Re-read the draft and look for what you *assumed* without the user telling you. Typical things people forget to state: timezones, idempotency, ordering, who-sees-what, error UX, what happens on retry, what happens to in-flight work, exact field formats.

---

## S2 — Clarify loop

Read `references/clarify-protocol.md` once before the first round.

**Per round:**

1. Pick 3-5 questions from the open `[?]` list. Each question must be classifiable as ambiguity / missing edge / undefined term — write the tag in brackets at the start: `[ambiguity]`, `[missing edge]`, `[undefined term]`. If you cannot tag it, do not ask it.
2. Phrase as a closed question with 2-4 options when possible. Closed beats open — open questions invite essays and slow convergence. Use the format:
   ```
   [ambiguity] REQ-001: "current billing period end" means
     (a) user's local timezone midnight on end_date
     (b) UTC 23:59:59 on end_date
     (c) exactly 30 days from cancellation timestamp
   ```
3. After the user answers, immediately apply the answers into the in-progress spec — convert each `[?]` into a normal clause + record a `source:` line citing the round/question number.
4. While applying answers, look for **newly exposed** ambiguities (a clarification often spawns one). Add those to the open list; they may need round 2.

**Stop conditions:**

- All `[?]` resolved → go to S3.
- 5 rounds elapsed but `[?]` remain → stop. Tell the user: "Five rounds in and `<N>` questions still open — this is a sign the requirement should be split into smaller features. Suggested split: …". Then offer to either write a partial spec covering only the resolved REQs, or restart with a narrower brief. Do not silently keep going.

**What you must not do in S2:**

- Do not ask about implementation choices (frameworks, libraries, DB schema specifics beyond what already exists in the brief).
- Do not ask the user to confirm something you already inferred safely — only ask about real uncertainty.
- Do not batch more than 5 questions per round (users disengage).
- Do not skip the tagging step. If a question is hard to tag, the question is bad — rewrite or drop it.

---

## S3 — Solidify

Write four files into `<output_dir>/`:

### 1. `proposal.md` — high-level intent

Sections:
- **Why** (1-3 sentences — the problem this solves)
- **What** (1 paragraph — what changes for the user)
- **Non-goals** (bulleted — what this is explicitly *not* doing)
- **Decisions made during clarify** (bulleted, each with a `source:` reference)

### 2. `spec.md` — the authoritative EARS specification

Same shape as the S1 draft, but with every `[?]` resolved. Each REQ block ends with a `source:` line citing the clarify round/question(s) that fixed it.

Append a final `## Glossary` section if any clarification produced a new domain term — record it precisely.

### 3. `tasks.md` — decomposed work

Plain markdown list. Each task:
- title (imperative)
- which REQs it implements (`implements: REQ-001, REQ-003`)
- rough size (S / M / L — only as a sanity check, do not estimate hours)

Group by layer if natural (data / business / API / UI), otherwise flat.

### 4. `done_when.yaml` — the contract

Read `references/done-when-schema.yaml` once before writing — that's the schema this file must match.

Three top-level blocks:
- `existence:` — every concrete noun the spec promised exists (file path, function, route, DB field, frontend component, env var). These are grep/AST-level checks; downstream `test-suite-generator` will turn them into a script.
- `behavior:` — names of tests that must exist and pass, partitioned by `unit_tests` / `integration_tests` / `e2e_tests` and within each by `example_based` / `property_based`. Plus `thresholds:` (coverage, mutation kill rate, PBT runs per property).
- `fitness:` — anything genuinely outside mechanical reach (max 3 items; if you have more, you are over-using LLM-judge — push it back into `behavior:`).

Add a `spec_drift_threshold:` block:
```yaml
spec_drift_threshold:
  max_fix_loops_before_escalation: 3
  applies_to:
    - mutation_kill_rate
    - property_based_failure
```
This is **guidance for the human chaining to `/ratchet`**, not a contract field anything auto-reads today. When chaining, translate `max_fix_loops_before_escalation` into ratchet's own `convergence` value (see `done-when-pipeline/INTEGRATION.md` for the recipe). Auto-escalation is future work; do not promise the user it happens automatically.

Every entry under `existence:` and `behavior:` is fine to be *aspirational* — they are names of things the implementer will create. They do not have to exist yet. They become the rubric.

### After writing the four files

Tell the user, in three short bullets:

1. The output directory and the four filenames.
2. A one-line count: `N REQs, M existence checks, K test names, J fitness criteria.`
3. Suggested next step: `/test-suite-generator <output_dir>/` (which will turn the contract into the actual test files).

That's the end of this skill. **Do not** generate tests, do not start implementing, do not run anything — those are downstream steps.

---

## When to refuse / redirect

- **"Just give me code"** → tell the user this skill produces specs, and offer to hand off the resulting `done_when.yaml` to ratchet for implementation. Do not skip the spec phase under pressure; that is the failure mode this whole pipeline exists to prevent.
- **Brief is one line, no real domain content** ("build me a SaaS") → ask once for a 2-3 paragraph elaboration, including: what the user does, what changes for the user, what the success scene looks like. If still vague, refuse and explain why — clarify questions need *something* to push against.
- **Brief is actually a design system request** (UI tone, color palette, typography) → suggest `/bespoke-design-system` instead. This skill is for behavioral requirements, not visual design.
- **Brief is a single bug fix** → this is heavyweight overkill. Suggest writing a 1-line failing test instead, and using `/ratchet` directly with that as the criterion.

---

## Resource index

- `references/ears-syntax.md` — five EARS sentence types with examples and selection rules
- `references/clarify-protocol.md` — full rules for the clarify loop, with examples of good vs bad questions
- `references/done-when-schema.yaml` — the schema `done_when.yaml` must conform to
- `references/output-templates/` — boilerplate for the four output files
- `references/examples/subscription-cancellation/` — a worked end-to-end example, all four files
