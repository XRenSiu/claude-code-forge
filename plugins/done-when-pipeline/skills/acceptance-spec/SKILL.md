---
name: acceptance-spec
description: >-
  Turn a fuzzy natural-language requirement into a machine-verifiable acceptance contract.
  Drafts EARS-format requirements (five sentence types), runs a strict clarify loop
  (only three question types allowed: ambiguity / missing edge / undefined term;
  2-3 rounds, 3-5 questions per round, max 5 rounds total) to remove every [?] marker,
  then writes five files: proposal.md, spec.md (EARS with stable REQ-IDs),
  tasks.md (decomposed work), done_when.yaml (the contract that test-suite-generator
  and acceptance-fleet will consume), and spec-robustness.md (S2.5 self-adversarial
  pass output — anti-gaming companion that /acceptance-fleet hands to
  /spec-gaming-detector). Covers Steps 1-3 of the done_when pipeline.
  Triggers: "spec this requirement" / "draft EARS" / "done_when for X" /
  "clarify this feature" / "acceptance criteria" / "write the contract" / "/acceptance-spec".
argument-hint: "<natural-language requirement or path to brief>"
version: 1.1.0
user-invocable: true
---

# acceptance-spec — Natural language → EARS spec + done_when contract

You are invoked to turn the user's natural-language requirement (`$ARGUMENTS` or recent user message) into a five-file acceptance contract that downstream agents can mechanically consume.

**Say once at the start, then start working:**
> "I'm using the acceptance-spec skill. I'll draft EARS requirements, run a short clarify loop (only 3 question types, 2-3 rounds), then a quick spec-self-adversarial pass, then write proposal.md / spec.md / tasks.md / done_when.yaml / spec-robustness.md."

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
5. **Borrow OpenSpec's file format, not its CLI.** Output the five files as documented below; do not shell out to `openspec`, do not depend on it.
6. **You do not write tests.** Tests are Step 4 (`test-suite-generator`). Your job ends at `done_when.yaml`.
7. **Verifiable beats judgeable.** Per HTML v2 §3 principle I (and the §3.5 corollary on fitness-check dissolution): in `done_when.yaml`, every claim must land in `existence:` (does the symbol exist) or `behavior:` (does the behavior hold under test) — never in a softer "LLM judges this" layer. The v0.x `fitness:` layer was retired in v1.0.0 because most "needs an LLM judge" entries can be re-designed as programmatic checks ("README quickstart works" → really run it; "type signatures correct" → run `tsc`). Genuinely-unautomatable cases (doc clarity, design taste, tutorial flow) reach evaluation via `/pm-reviewer`'s `requires_human_verification` verdict — they do NOT appear in `done_when.yaml`. The third layer is now `rules:`, a flat condition list consumed by `/meta-judge` for final-verdict synthesis.
8. **REQs must be independently testable — no cross-REQ causal indirection.** Each REQ is the unit a Step 4 test must derive from. **Do not** write things like `THE system SHALL silence the notification produced by REQ-001`; that binds REQ-N's verifiability to REQ-001's runtime artifact and forces Step 4 fixtures to chain. Instead, restate the relevant precondition in REQ-N's own EARS clause (`IF a mention is delivered AND the recipient is in DND, THEN ...`). REQs may *reference* each other for narrative context (e.g. "follow-on from REQ-001" in the heading line) but the SHALL action must be derivable from the REQ's own clauses alone. See `references/ears-syntax.md` "Cross-REQ causal indirection" row.
9. **Worker output ≠ internal decision process.** Each phase's user-visible output is **only the deliverable** for that phase (S1: draft + open questions; S2: a single round's question batch; S3: the five files). Do not interleave skill-internal logs ("clarify-protocol Rule 2 vs Rule 6 weighing", "skill invocation summary", "second-order scan notes") into the output. If something is useful as audit context, put it in a comment inside the deliverable file or omit it. Process narration belongs in your reasoning, not in what the user reads.
10. **Output is single-language per primary surface.** EARS sentence bodies, REQ headings, `[?]` notes, and clarify question text should all use **one** primary language consistently within a single artifact (typically English, since EARS keywords are English). Mixing English EARS bodies with Chinese question lists in the same file fragments the artifact and forces parallel translations. Glossary entries that *define* a Chinese-named domain term are fine — but the EARS body, the question prompts, and the source/log lines stay in one language.
11. **One SHALL clause = one independently-derivable action.** A single EARS REQ's SHALL must commit to exactly **one** observable action. Do NOT bind two distinct actions together with an `AND` compound (e.g. `THE system SHALL transition the subscription to status expired AND deny premium feature access on the next request`). Even when the two actions are causally linked, packing them into the same SHALL fuses two independently-testable behaviors into one REQ — and when the second action overlaps the SHALL of another REQ (e.g. the same denial appears in another `IF ... THEN ...` clause), the contract develops cross-REQ duplication that confuses Step 4 test derivation and breaks one-to-one REQ ↔ test traceability. Split AND-compound SHALLs into separate REQs (each with its own ID, EARS type, and `source:`). Acceptable use of `AND` inside a SHALL is **only** when the two clauses describe *one indivisible atomic effect* of the same trigger (e.g. `SHALL atomically (a) set status to cancelled AND (b) stop next-billing-cycle charge`) and you also state atomicity is the testable contract. If you can derive a test for one half without the other half being involved, they are **two REQs**, not one. See `references/ears-syntax.md` "Common drafting mistakes" → AND-compound SHALL row.

12. **Existence completeness vs tasks.md.** Every distinctly-named function / route / db_field / frontend_component that appears in `tasks.md` (the decomposed work list) AND is referenced by any REQ's SHALL clause MUST also appear as an entry in `done_when.yaml.existence:`. The existence layer is the fast-fail surface; if `tasks.md` promises a `RenewalPrompt` UI component or a `checkPremiumAccess` middleware function (because some REQ promises that behavior), the implementer should be told upfront — via existence — that those named artifacts will be checked. Leaving them implicit means the only signal the implementer gets is the test name, which is later in the cycle and slower to fail. **Before solidifying `done_when.yaml`**: walk every named noun in `tasks.md` once and confirm it has a matching `existence:` entry, OR document the deliberate exclusion (e.g. "renamed during decomposition, the canonical name is X which IS listed") inside `proposal.md` "Decisions made during clarify". Silently dropping a tasks-named artifact from existence is a P1 quality bug.

13. **Anti-gaming is part of the contract, not the verifier's afterthought.** Specification-gaming research (Komorebi AI 2025) shows 50-70% of LLM implementations game a vulnerable contract — even when the spec looks unambiguous to a human. The S2.5 self-adversarial pass (see below) is mandatory: before solidifying, ask "if I were the implementer trying to satisfy this contract while doing as little as possible, where are the cracks?" Identified gaming vectors become `spec-robustness.md` entries — either closed by adding a `behavior.thresholds:` value (when v1 schema admits one), or surfaced explicitly so the downstream `/acceptance-fleet` verifier knows to watch for them. **Do not skip S2.5 because "this brief looked clean."** Clean-looking briefs are the most game-able. **Do NOT introduce sub-fields outside Appendix C v1 schema** — the schema is rigid for a reason (downstream strict parsers); v1.5 augmentations live in `spec-robustness.md`, not in `done_when.yaml`.

If you catch yourself asking a question that is not in {ambiguity, missing edge, undefined term}, **delete it before sending**. Asking the wrong type is the most common failure of this skill.

---

## Phase map

```
S0    Bootstrap          read the brief, detect scope, pick the EARS sentence types you'll need
S1    Draft              NL → EARS, every fuzzy spot becomes a [?] marker
S2    Clarify loop       3 question types, 2-3 rounds, every [?] resolves into a sourced decision
S2.5  Self-adversarial   "how would I game this contract?" — surface gaming vectors, close or document each
S3    Solidify           write proposal.md / spec.md / tasks.md / done_when.yaml / spec-robustness.md
```

The user only sees output at end of S1 (the draft + question list), one optional line at end of S2.5 (the gaming-vector summary, only if surprises emerged), and again at end of S3 (the five files). S2 is the interactive part. S0 is silent setup. S2.5 is silent unless the pass produces high-severity vectors the user should sanity-check.

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

Output exactly this shape to the user (note the `Feature:` prefix in the header — it is mandatory; downstream artifacts use it as the spec's title):

````markdown
# Feature: <feature-slug> (draft)

## REQ-001 (<EARS type>)
<EARS sentence with [?] [<tag>] markers inline>

## REQ-002 (<EARS type>)
...

## Open questions
- [?] [<tag>] "<noun-or-clause-the-question-targets>": <option-a> or <option-b>? (affects REQ-XXX)
- [?] [<tag>] "<noun>": <option-a>, <option-b>, or <option-c>? (affects REQ-YYY)
- ...
````

**Strict rule — exactly two ambiguity surfaces, not three.** The draft has (a) inline `[?]` markers in the EARS bodies and (b) the single `## Open questions` section above. Do **not** add a third "歧义清单" / "ambiguity list" / per-tag grouped table — it is redundant and visually heavier than helpful. The `[?]` tag taxonomy is enough structure; grouping by tag belongs (if anywhere) in S2 round planning, not in the S1 deliverable.

**Question-line format under `## Open questions`** — each line is `[?] [<tag>] "<noun>": <option-a> or <option-b>?`. The double-quoted noun pins what the question is *about*; the colon introduces the candidate readings; the question mark ends it. Avoid free-form parenthetical asides. See `references/clarify-protocol.md` "Format for a clarify-round message" for the parallel example used at S2.

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
- **Do not include a `## Glossary` section in any S2 output.** Glossary is a S3 artifact (it lives in `spec.md`). If a clarification produces a precisely-defined term, hold it in your reasoning until S3; do not preview it in S2 output, even labeled "(working)".
- **Do not include a "skill invocation log" / "decision-trace table" / "process narration" section in S2 output.** S2 round output is just the round's question batch (per `references/clarify-protocol.md` "Format for a clarify-round message"). The final S3 `spec.md` carries `source:` lines for per-REQ traceability; that is the single authoritative trace. Do not emit a parallel "decision trace" table whose granularity differs from the `source:` lines — picking the right one becomes ambiguous downstream.

**S2 output is exactly two artifacts, nothing more:** (i) the next round's question batch (per `clarify-protocol.md`), and (ii) the updated in-progress EARS body with answered `[?]` markers replaced by `source:`-tagged clauses. No Glossary, no process log, no parallel decision table.

---

## S2.5 — Spec-self-adversarial pass

After S2 closes (all `[?]` resolved) and before S3 writes files, run an internal adversarial pass. Reverse the default sycophantic posture and ask: **"If I were the implementer trying to satisfy this contract while doing as little real work as possible, where are the cracks?"**

This is silent unless it surfaces a high-severity vector. The output is the in-memory list that drives `spec-robustness.md` in S3.

**Why this exists.** *Specification Self-Correction* (Komorebi AI Tech, 2025) reports that, given a vulnerable spec, 50-70% of LLM implementations game it (weaken assertions, hardcode test inputs, cover line not branch, etc.). SSC's fix is exactly this: have an independent agent critique the spec for game-ability *before* implementation, not after. The numbers drop below 10% when this pass is run. Without it, `/acceptance-fleet` is patching downstream what could have been prevented upstream.

**Scan the resolved spec and `done_when.yaml` draft against the six RHD gaming patterns** (from *Benchmarking Reward Hack Detection in Coding Agents*):

1. **Test Modification** — Does any REQ permit silently weakening an assertion? (e.g. a SHALL clause vague enough that `assert result is not None` would satisfy it as much as the intended deep equality.) → If yes, tighten the REQ wording in S3.
2. **Test Case Targeting** — Does any behavior name leak the exact input the test will use? (e.g. `test_cancel_with_user_id_42_returns_403` invites hardcoding.) → Rename to abstract over the specific value.
3. **Coverage Gaming** — Does `behavior.thresholds.unit_coverage` exist *without* a `mutation_kill_rate`? Line coverage alone incentivizes `assert True`. → Ensure `mutation_kill_rate: ">= 0.70"` is present (v1 schema admits this — it's mandatory per iron rule 5 of test-suite-generator).
4. **Degenerate Implementation** — Does any REQ admit a lookup-table or if-else-explosion as a satisfying impl? (e.g. "for the five known input cases, return the expected output" — easily faked.) → Add a PBT property name to `behavior.unit_tests.property_based` that forces generalization.
5. **Style Manipulation** — Are there gameable surface metrics smuggled into thresholds (comment-line count, character count, etc.) that proxy real quality with cheap-to-game numbers? → Convert to programmatic checks of the actual behavior or drop. (Pre-v1.0 this pattern most often landed in the now-retired `fitness:` layer; v1.0+ has no `fitness:` block, but the temptation can resurface in `rules:` or `behavior.thresholds:` — watch.)
6. **Information Leakage** — Does `spec.md` contain example inputs/outputs that would be copy-pasted as the impl? → Move them to glossary entries or remove from spec.

**For each gaming vector identified, decide one of three actions:**

- **(close)** Adjust `spec.md` REQ wording or add a `behavior.thresholds:` value to close it. Note in S3 `proposal.md` under "Decisions made during clarify" with a `(S2.5 self-adversarial)` tag.
- **(document)** Cannot close within v1 schema — record in `spec-robustness.md` as a `surfaced_vector` for `/acceptance-fleet` to watch.
- **(accept)** Theoretically gameable but practically unlikely (e.g. the REQ is about doc text — gaming = writing bad docs, which is its own failure). Record in `spec-robustness.md` as `accepted_risk` with a one-line rationale.

**Hard rule for S2.5:** Do NOT introduce sub-fields into `done_when.yaml` that are outside the Appendix C v1 schema. If you want a check that isn't expressible in v1 (e.g. branch coverage threshold, code complexity limit, cross-PR diff size budget), it goes in `spec-robustness.md` under `verifier_hints:` — `/acceptance-fleet` consumes that block, not `done_when.yaml`. The schema-extension temptation is exactly what iron rule 11 forbids.

**S2.5 user-visible output:** *nothing*, unless step (1) ("close") produced a non-obvious REQ rewrite that the user should sanity-check, in which case emit a one-line note:
> "Spec-self-adversarial surfaced N gaming vectors. Closed K (REQ-NNN rewrites — please sanity-check spec.md before continuing), documented M for /acceptance-fleet, accepted P as practical-non-risk."

Then proceed to S3 without waiting.

---

## S3 — Solidify

Write five files into `<output_dir>/`:

### 1. `proposal.md` — high-level intent

Sections:
- **Why** (1-3 sentences — the problem this solves)
- **What** (1 paragraph — what changes for the user)
- **Non-goals** (bulleted — what this is explicitly *not* doing)
- **Decisions made during clarify** (bulleted, each with a `source:` reference)

### 2. `spec.md` — the authoritative EARS specification

Same shape as the S1 draft, but with every `[?]` resolved. Each REQ block ends with a `source:` line citing the clarify round/question(s) that fixed it.

**Keep REQ bodies tight (target ≤ 25 words per SHALL clause).** When a clarify answer introduces a precisely-defined term, **define it in `## Glossary`** rather than inlining a definition clause inside the REQ body. Long mid-REQ parentheticals (e.g. `WHEN a member is @mentioned (where "@mention" means individual mentions, broadcast mentions @here/@channel/@everyone, and role-or-group mentions) ...`) make the EARS sentence a mini-glossary and lose the rigid template's clarity. Pull such definitions out:

- REQ body: `WHEN a member is @mentioned in a team chat channel, THE system SHALL ...`
- Glossary: `**@mention** — any of: individual mentions, broadcast (@here/@channel/@everyone), or role-or-group mentions. (source: S2 round 1 Q1)`

Append a `## Glossary` section if any clarification produced a new domain term — record it precisely. **Glossary appears only in `spec.md` (S3 output)**, never in S2 round output. Each Glossary entry has its own `source:` reference; you do not need to duplicate the term definition into REQ bodies that use it.

**REQ-block sub-clauses (Extension / Constraint).** It is allowed — but not required — to split a long REQ into a primary EARS sentence plus a sub-clause block under the same REQ heading. Use the precise sub-labels listed below so downstream tools can route them:

```markdown
## REQ-001 (Event-driven)
WHEN <trigger>, THE system SHALL <action>.

### Constraint:
<additional always-applies condition on the SHALL clause — narrows the scope>

### Extension:
<additional case the same REQ also covers — broadens the scope>

source: S2 round 1 Q3 (...)
```

Sub-clause labels `### Constraint:` and `### Extension:` are the only two sanctioned ones. `### Constraint:` narrows (e.g. "applies only to messages with `kind=mention`"); `### Extension:` broadens (e.g. "this REQ also fires on edit-with-new-mention"). Anything else (`### Note:`, `### Example:`, etc.) is not part of the contract and risks being read as a new EARS sentence — do not invent labels.

### 3. `tasks.md` — decomposed work

Plain markdown list. Each task:
- title (imperative)
- which REQs it implements (`implements: REQ-001, REQ-003`)
- rough size (S / M / L — only as a sanity check, do not estimate hours)

Group by layer if natural (data / business / API / UI), otherwise flat.

### 4. `done_when.yaml` — the contract

Read `references/done-when-schema.yaml` once before writing — that's the schema this file must match. That schema is a faithful reproduction of **Appendix C of `done-when-pipeline.md` (schema v1)**, which is the authoritative source. **Emit strict v1 字面 schema — do not invent sub-fields.**

Hard rules for v1 字面:

- `existence:` — every entry is **a single key-value pair, no sub-fields**. Allowed kinds are exactly the five from Appendix C: `file:` / `function:` / `route:` / `db_field:` / `frontend_component:`. Do NOT add `based_on:` / `kind:` / any other key on an existence entry. If you find yourself wanting `based_on:` per entry — push the traceability into the test name and rely on the top-level `based_on:` list + `spec.md` `source:` lines.
- `behavior:` — every test entry under `unit_tests.example_based` / `unit_tests.property_based` / `integration_tests.example_based` / `integration_tests.property_based` / `e2e_tests` is **a bare string** (the test name), not a mapping. No `name:` / `based_on:` / `property_type:` / `dependencies:` / `tool:` sub-fields. Encode the property archetype (invariant / idempotent / reversible / boundary / monotonic / state_machine) in the test name itself so downstream (4-B in test-suite-generator) can route the PBT pattern by name.
- `behavior.thresholds:` — the four keys are fixed: `unit_coverage`, `integration_coverage`, `mutation_kill_rate`, `pbt_runs_per_property`.
- `rules:` — REPLACES the v0.x `fitness:` layer (retired per HTML v2 §3.5). Flat list of conditions consumed by `/meta-judge` during final-verdict synthesis. Each entry is a bare string (e.g. `"any P0 finding blocks merge"`, `"mutation_kill_rate >= 0.7"`) or a mapping with `rule:` + optional `severity:` / `applies_to:` fields. No nested objects. MAY be empty — meta-judge falls back to block-on-P0 default. Do NOT carry over a legacy `fitness:` block; the unautomatable cases now route to `/pm-reviewer`'s `requires_human_verification` instead.
- `spec_drift_threshold:` — exactly one sub-field, `max_fix_loops_before_escalation: <integer>`. Do NOT add `applies_to:` or any other key.
- Top-level `based_on:` — the union of every REQ-ID referenced anywhere in the spec. This is the primary traceability anchor under v1 (combined with `spec.md` `source:` lines).

```yaml
spec_drift_threshold:
  max_fix_loops_before_escalation: 3
```
This is read directly by `/acceptance-fleet` as the four-state ratchet's `PBT-repeat → SPEC_DRIFT` trigger threshold: after N fix loops without progress on the same REQ, the orchestrator escalates to SPEC_DRIFT state and hands control back here (re-invoke `/acceptance-spec` to narrow the REQ — do NOT patch code).

Every entry under `existence:` and `behavior:` is fine to be *aspirational* — they are names of things the implementer will create. They do not have to exist yet. They become the rubric.

> **Why so strict?** Earlier drafts of this skill let the writer scatter `based_on:` and `property_type:` onto leaf entries to make traceability "explicit per row". That looks helpful but violates v1 schema literally; downstream strict parsers will reject it, lenient parsers will drop the extra keys silently — either way the per-row traceability is lost. Until Appendix C grows a v2, keep traceability at the union top-level `based_on:` plus the test-name semantics.

### 5. `spec-robustness.md` — anti-gaming companion to `done_when.yaml`

Produced from the S2.5 self-adversarial pass. This is the carrier for v1.5 augmentations that **cannot live in `done_when.yaml`** under Appendix C v1 schema (iron rule 11). `/acceptance-fleet` reads this file when scoring `gaming_risk`; the human reads it to understand what the spec deliberately accepts as untested.

Three sections, in order:

```markdown
# Spec Robustness — <feature-slug>

(Generated by acceptance-spec S2.5 self-adversarial pass. Consumed by /acceptance-fleet
spec-gaming-detector. Not part of the strict v1 contract — augmentation only.)

## closed_vectors
Gaming vectors that were identified during S2.5 and closed by adjusting spec.md or
done_when.yaml (within v1 schema). Listed for audit — these should NOT need re-checking
by the verifier; they are already structurally prevented.

- rhd_pattern: test_modification        # canonical enum from the six RHD patterns
  rewrote: REQ-003 SHALL clause tightened from "completes successfully" to "returns
           HTTP 200 with body matching CancelResponse schema"
  source: S2.5 (S2 round 1 Q3 surfaced underlying ambiguity)
- ...

## surfaced_vectors
Gaming vectors that COULD NOT be closed inside the v1 schema. /acceptance-fleet's
spec-gaming-detector role MUST watch for these specifically. Each entry tells the
verifier what to grep for / what mutation to inject / what counter-test to derive.

- rhd_pattern: coverage_gaming
  spec_robustness_gap: done_when.yaml requires mutation_kill_rate >= 0.70 but does
                       not require branch coverage; a happy-path-only impl that skips
                       error branches could pass.
  verifier_hint: spec-gaming-detector should check branch coverage on impl; flag if
                 < 0.60 even when mutation_kill_rate >= 0.70.
  affects: REQ-001, REQ-004
- ...

(Use `rhd_pattern:` whenever the entry maps to one of the six RHD patterns; use
`pattern:` only for free-form local sub-classification (e.g. `pattern: branch_coverage_gap`
under `rhd_pattern: coverage_gaming`). NEVER emit both as parallel synonyms — see
`references/spec-robustness-template.md` "Output discipline" for the canonical rule.)

## accepted_risks
Gaming vectors that were considered and consciously NOT defended against. Each
entry is a one-line rationale; absence of a rationale is a S2.5 bug.

- rhd_pattern: style_manipulation        # on README/doc quality threshold
  rationale: gaming this = writing bad docs, which is itself the failure that
             /pm-reviewer's requires_human_verification verdict catches. No
             reinforcement needed in the contract layer.
- ...

## verifier_hints
Optional. Free-form hints to /acceptance-fleet beyond the six RHD patterns above —
e.g. domain-specific gaming vectors only this feature would face.

- when scoring qa-reviewer output for REQ-007, flag if the test list includes any
  selector that matches `_test_only_*` patterns — those endpoints exist for test
  setup, not for product behavior, and shouldn't drive PBT input space.
```

If S2.5 produced no surfaced vectors AND no accepted risks (closed-only), still emit the file with an empty `## surfaced_vectors` block and a single `## accepted_risks` entry: `none — S2.5 closed all identified vectors structurally`. The file's existence is the verifier's signal that S2.5 ran; absence of the file is a contract bug.

### After writing the five files

**First, run the schema exit gate (bundled primitive) before declaring done:**

```
python scripts/validate_done_when.py <output_dir>/done_when.yaml --spec <output_dir>/spec.md --check
```

`scripts/validate_done_when.py` is the v1-schema exit primitive. It mechanically enforces what iron rules 7 / 11 ask you to "walk by hand": existence entries are single-key with no stray sub-fields, behavior leaves are bare strings (no `name:`/`based_on:`/`property_type:`), `mutation_kill_rate` is present, `fitness:` is absent, `spec_drift_threshold` has exactly one sub-field, and `based_on` cross-references real REQs in `spec.md`. Per skillwise THEORY.md §3-4, a strictness rule the author self-enforces by re-reading is not a guarantee; this runnable check of the *product* is. If it reports any hard failure, fix `done_when.yaml` and re-run before handing off — a malformed contract fails downstream slower and more expensively (`/test-suite-generator`'s validator, then the fleet). (The check is schema-only; iron rule 12's tasks.md→existence completeness walk is still yours to do, since it needs the prose intent the schema can't see.)

Then tell the user, in four short bullets:

1. The output directory and the five filenames.
2. A one-line count: `N REQs, M existence checks, K test names, R rules entries, V surfaced gaming vectors.`
3. Immediate next step: `/test-suite-generator <output_dir>/` — turns the contract into the actual test files (Step 4).
4. Subsequent step (Step 5-6): `/acceptance-fleet` consumes `done_when.yaml` + `spec-robustness.md` + the generated tests directly, dispatches the 6 standalone review skills, and runs the 4-state ratchet (DONE / FIX / SPEC_DRIFT / GAMING_RISK).

That's the end of this skill. **Do not** generate tests, do not start implementing, do not run anything — those are downstream steps.

---

## Step 5-6 hand-off — what this skill's outputs feed into

This skill ends at the five files. Downstream:

1. **Step 4 (`/test-suite-generator`)** consumes `spec.md` + `done_when.yaml` automatically — the immediate next slash command.

2. **Step 5-6 (`/acceptance-fleet`)** consumes the full five-file output directly. It dispatches the 6 standalone review skills (`/code-reviewer`, `/qa-reviewer`, `/pm-reviewer`, `/spec-drift-detector`, `/spec-gaming-detector`, `/meta-judge`) — `/spec-gaming-detector` reads `spec-robustness.md` to know what surfaced vectors to hunt for; `/meta-judge` synthesizes findings without inter-agent debate (Dartmouth/Yale 2025 showed debate *amplifies* bias). The four-state ratchet (DONE / FIX / SPEC_DRIFT / GAMING_RISK) decodes the verdict; SPEC_DRIFT and GAMING_RISK both hand control back here (re-invoke `/acceptance-spec` to narrow REQs or close more gaming vectors — do NOT patch code).

If PBT keeps finding counterexamples across multiple fix loops, the **spec** is probably the bug, not the code (cf. design doc §12.1.IV). `/acceptance-fleet` decodes this automatically as SPEC_DRIFT after N stalled iterations on the same REQ (N from `spec_drift_threshold.max_fix_loops_before_escalation`, default 3). If you want to second-guess the auto-decode, the practical rule: a shrunk counterexample *consistent* with the literal REQ text (the REQ as written would also produce a misbehaving impl) = spec wrong, return here; a counterexample that *contradicts* the REQ text (REQ says X, impl does not-X) = code wrong, feed `/acceptance-fleet`'s fix-prompt to a fresh impl session.


---

## When to refuse / redirect

- **"Just give me code"** → tell the user this skill produces specs, not code. Point at the actual code-writing path: chain `/test-suite-generator` → implement in a fresh session → `/acceptance-fleet` to verify. Do not skip the spec phase under pressure; that is the failure mode this whole pipeline exists to prevent.
- **Brief is one line, no real domain content** ("build me a SaaS") → ask once for a 2-3 paragraph elaboration, including: what the user does, what changes for the user, what the success scene looks like. If still vague, refuse and explain why — clarify questions need *something* to push against.
- **Brief is actually a design system request** (UI tone, color palette, typography) → suggest `/bespoke-design-system` instead. This skill is for behavioral requirements, not visual design.
- **Brief is a single bug fix** → this is heavyweight overkill. Suggest writing a 1-line failing test instead and fixing the code against that, without going through the full spec → tests → fleet pipeline.

---

## Bundled primitives (scripts/)

- `scripts/validate_done_when.py` — the v1-schema exit gate (run with `--check` after S3). Seals iron rules 7/11's mechanical strictness so a malformed contract has no slot to slip through (skillwise THEORY.md §3).

## Resource index

- `references/ears-syntax.md` — five EARS sentence types with examples and selection rules
- `references/clarify-protocol.md` — full rules for the clarify loop, with examples of good vs bad questions
- `references/done-when-schema.yaml` — the schema `done_when.yaml` must conform to
- `references/spec-robustness-template.md` — boilerplate + worked patterns for the S2.5 fifth-file output
- `references/output-templates/` — boilerplate for the five output files
- `references/examples/subscription-cancellation/` — a worked end-to-end example
