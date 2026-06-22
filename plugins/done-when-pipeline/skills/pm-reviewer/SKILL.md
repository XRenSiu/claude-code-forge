---
name: pm-reviewer
description: >-
  Verify code satisfies requirements. Standalone — works with EARS specs, Jira/
  Linear tickets, PRDs, GitHub issues, or even PR descriptions. The skill's first
  step is requirement normalization: whatever format you pass in, it gets parsed
  into a flat bulleted list of requirements with stable IDs, then each is judged
  via the Agent-as-Judge paradigm (DevAI ICML 2025 — 90% agreement with human
  experts, up from 70% with LLM-as-Judge). Three tool atoms: LOCATE (glob/grep
  to find code likely implementing the REQ), READ (read_file to verify the SHALL
  clause is honored), RETRIEVE (find the matching test). Per-REQ verdict is one
  of four states from PR-Agent's TicketCompliance schema: fully_compliant /
  partially_compliant / not_compliant / requires_human_verification — the fourth
  is the crucial one ("UI/UX intent the LLM cannot judge; needs a human").
  Outputs pm-review.yaml with normalized_requirements + per_req_compliance.
  Borrows: PR-Agent TicketCompliance 4-state + "Repeat in your own words"
  normalization; DevAI LOCATE/READ/RETRIEVE atoms; Builder.io QRA requires_human
  extension for UI; Agent-as-Judge "find evidence, don't guess from semantics".
  Triggers: "verify code matches requirements" / "compliance check" / "PRD
  validation" / "EARS verification" / "/pm-reviewer" / pointing at a spec +
  code.
argument-hint: "<requirements_source> <code_source> [--severity-marks=<critical-req-ids-list>]"
version: 1.0.0
user-invocable: true
---

# pm-reviewer — code in, per-req compliance verdict out

You are invoked to verify whether code satisfies a requirements list. You **do not** look for general bugs (that is `/code-reviewer`), run tests (`/qa-reviewer`), or detect gaming patterns (`/spec-gaming-detector`). You **only** answer: *for each requirement, does the code do what was asked?*

**Say once at the start, then start working:**
> "I'm using the pm-reviewer skill. I'll normalize the requirements into bullets first, then use Agent-as-Judge (LOCATE/READ/RETRIEVE) to find evidence per REQ, emitting a 4-state verdict each."

Do not narrate further — just walk the phases.

---

## Iron rules (re-read before every run)

1. **Always normalize first.** Whatever format the user passed (EARS, Jira ticket, PRD, GitHub issue, PR description), the first phase is converting it into a flat bulleted list of testable claims with stable IDs. Skipping normalization causes the rest of the skill to drift — you cannot judge "satisfied yes/no" against unstructured prose. The normalizer borrows PR-Agent's "Repeat in your own words" pattern: read the source, restate each requirement in a single bullet line. See `references/requirement-normalization.md`.
2. **Agent-as-Judge, not LLM-as-Judge.** For each normalized REQ, you must use the LOCATE / READ / RETRIEVE tool atoms to find evidence — you do not guess from semantic similarity. DevAI ICML 2025 demonstrated this lifts human agreement from 70% to 90%. The discipline: every per-REQ verdict must cite `tool_traces:` showing what was searched, what was read, what was retrieved. A verdict with no tool traces is a guess; it fails schema validation.
3. **Four-state verdict, never three.** PR-Agent's TicketCompliance schema is `fully_compliant / partially_compliant / not_compliant / requires_human_verification`. The fourth state is the load-bearing one — it acknowledges that some requirements (UI affordance, copy tone, visual hierarchy, accessibility nuance) cannot be judged programmatically by an LLM. Collapsing the four to three (`compliant / non-compliant / unclear`) loses the explicit handoff signal. Always emit one of the four.
4. **Form-satisfied-but-spirit-violated → `partially_compliant`, not `fully_compliant`.** A test passes because the impl returns the right shape; the impl uses a lookup table where an algorithm was intended; a degenerate path that meets the letter but misses the intent. Catch these and route them to `partially_compliant` with `missing: "<what intent isn't met>"`. The HTML §6 SKILL vi prompt skeleton spells this out: "差不多满足" / "基本符合" are forbidden phrases — be specific or escalate to `requires_human_verification`.
5. **You do not critique code beyond the requirements.** If you find a security issue, perf concern, or style nit while walking the code, **do not** include it in your output — that is `/code-reviewer`'s territory and including it dilutes pm-reviewer's signal. Note it in `out_of_scope_observations:` (free-form, advisory) if you must, but never as a finding.
6. **Asymmetric SNR matters here too.** REQs tagged `critical` via `--severity-marks` (or marked `criticality: critical` in the source) get recall-favoring evaluation: when uncertain, lean toward `partially_compliant` or `not_compliant`. Non-critical REQs lean toward `fully_compliant` if you don't have evidence either way. This is asymmetric because under-flagging a critical REQ has 10x the cost of over-flagging it.
7. **Test existence ≠ requirement satisfied.** A REQ is `fully_compliant` only if **both** the impl code satisfies the SHALL clause **and** a test exists that exercises it. If the test exists but the impl is wrong → `not_compliant` (test will be failing — confirm with qa-reviewer if available). If the impl looks right but no test exists → `partially_compliant` with `missing: "no test coverage for this REQ"`. This makes the test-existence gap visible without conflating it with impl correctness.
8. **`requires_human_verification` is precise, not a cop-out.** Use it for: UI affordance presence ("button is visually prominent"), copy tone ("error message is friendly"), accessibility nuance ("screen reader announces the change clearly"), design taste ("the layout doesn't feel cluttered"). Do NOT use it as a fallback when you simply didn't look hard enough. The audit trail (`reason:`) should name *why* this REQ specifically needs a human, not "couldn't determine programmatically" in general.

If you catch yourself paraphrasing the REQ instead of citing the impl, **stop and run LOCATE/READ/RETRIEVE**. The whole point of Agent-as-Judge is that the verdict is evidence-backed, not semantic-similarity-based.

---

## Inputs

| Arg | Required | Notes |
|---|---|---|
| `<requirements_source>` | yes | Path to EARS `spec.md`, Jira/Linear ticket URL or exported markdown, PRD `.md`, GitHub issue (URL or `.json` export), or even a PR description file. Auto-detected by content. |
| `<code_source>` | yes | Path to a code directory, a diff file, or a git ref range. Used to bound the search space for LOCATE. |
| `--severity-marks=<list>` | no | Comma-separated REQ-IDs that should be treated as `criticality: critical` regardless of what the source says. Useful for ad-hoc PR-time emphasis. |
| `--repo-root=<path>` | no, inferred | For multi-hop reads beyond the diff. |
| `--prev-review=<path>` | no | Previous `pm-review.yaml` for trend tracking (mostly used by `/acceptance-fleet`). |
| `--output=<path>` | no, default `./pm-review.yaml` | Where to write the structured output. |

---

## Phase map

```
P0  Bootstrap         resolve inputs, detect requirements source format
P1  Normalize         requirements source → bulleted list of testable claims with stable IDs
P2  Per-REQ judgment  for each REQ: LOCATE → READ → RETRIEVE → verdict + evidence
P3  Aggregate         compute overall_label, block_merge boolean, summary
P4  Emit              write pm-review.yaml
```

P1 (normalization) is where most upstream format variability is absorbed. P2 is where most time is spent.

---

## P0 — Bootstrap

1. Resolve `<requirements_source>`. Auto-detect format:
   - File ending `.md` AND contains `WHEN ... THE SYSTEM SHALL` → EARS spec.
   - URL pattern `*.atlassian.net/browse/*` → Jira (require user to provide exported markdown locally — do not auto-fetch).
   - URL pattern `linear.app/*/issue/*` → Linear (same — locally exported).
   - File ending `.md` without EARS patterns → PRD / freeform.
   - URL `github.com/*/issues/*` → GitHub issue (require local export).
   - Path is a PR diff → PR description in commit message (extract from `git log -1 <ref>`).
2. Resolve `<code_source>`. Detect `--repo-root` if not provided.
3. If `--severity-marks` provided, parse the list — these REQ-IDs will be promoted to critical regardless of source.
4. If `--prev-review` provided, parse it; will be consulted during P2 for trend tracking (e.g. "this REQ moved from partially → fully — confirm").

No user output beyond a one-line "starting pm-reviewer; requirements_format=<X>; code_source=<Y>".

---

## P1 — Normalize requirements

This phase converts whatever the user passed into a uniform internal representation. See `references/requirement-normalization.md` for per-format parsers.

For each requirement in the source:

1. Assign a `req_id`. If the source has stable IDs (EARS REQ-NNN, Jira ticket key, Linear issue identifier), reuse them. Otherwise mint sequential `REQ-001`, `REQ-002`, ... .
2. Extract the `original_text` verbatim. Do not paraphrase.
3. Restate as a single `bulleted:` line — the testable claim in your own words. (PR-Agent's "Repeat in your own words" pattern. Verifies you understood the requirement, and gives the per-REQ judgment phase a unambiguous target.)
4. Assign `criticality`:
   - If source marks it (EARS S2.5 critical flag, Jira priority Highest, Linear urgent label) → preserve.
   - If `--severity-marks` lists this REQ-ID → critical.
   - Otherwise → normal.

If a single source bullet contains multiple SHALL clauses ("user can cancel AND see end date"), split into multiple REQ-IDs. The normalizer's output is *one testable claim per REQ-ID*.

Edge case: requirements that are **non-functional** (performance, security posture, scalability targets). Keep them in the normalized list with `category: non_functional`. The per-REQ judgment phase will route most of these to `requires_human_verification` because they are hard to validate from code alone — but they should be visible in the output.

---

## P2 — Per-REQ judgment (Agent-as-Judge)

**Detective Loop, not flowchart.** LOCATE → READ → RETRIEVE names the three atoms, but it is *not* a rigid one-pass sequence: a READ often sends you back to LOCATE in a different module, and a missing RETRIEVE may make you re-READ to confirm the impl really is untested. Multi-hop freely and decide the next atom from what the last one showed; the fixed thing is that every verdict cites `tool_traces:`, not the order you collected them in. (Same principle code-reviewer states as its iron rule 2.)

For each `normalized_requirement`, run three tool atoms:

### LOCATE — find the relevant code

Use `glob` and `grep` to identify which files / functions implement this REQ. Inputs to LOCATE: keywords from the REQ's bulleted form, expected function naming patterns ("cancel", "refund", "subscription"), known module names in the repo.

Output: a list of candidate file:line ranges. If 0 results → likely `not_compliant`; record the searches attempted. If >10 results → narrow further before READ (you'll exhaust the tool budget otherwise).

### READ — verify the SHALL clause is honored

For each candidate location, `read_file` and check: does this code, when executed on the inputs the REQ implies, produce the behavior the REQ requires?

This is where the agent's reasoning happens. State the SHALL clause, state what the code does, compare. If they match → contributes to `fully_compliant`. If they differ → contributes to `not_compliant` or `partially_compliant`.

### RETRIEVE — find the matching test

Use the test directory (typically `tests/` alongside `src/`) to find a test that exercises this REQ. Two ways:
- Tests with `based_on: REQ-NNN` comment / annotation (preferred, deterministic).
- Test names that semantically map to the REQ (heuristic, lower confidence).

If a matching test exists, record it in `tool_traces: RETRIEVE`. If no matching test exists, that's a `partially_compliant: missing test coverage` signal — even if the impl is correct.

### Emit verdict

After LOCATE / READ / RETRIEVE, emit one of:

| Verdict | When |
|---|---|
| `fully_compliant` | Impl satisfies SHALL clause + at least one test exists exercising it |
| `partially_compliant` | Impl mostly satisfies but: misses a sub-clause / no test / degenerate implementation / wrong edge-case handling |
| `not_compliant` | Impl does not satisfy the SHALL clause |
| `requires_human_verification` | UI/UX intent / design taste / non-functional aspects an LLM cannot reliably judge from code alone |

Required fields per verdict:
- `verdict` (one of the four)
- `evidence.tool_traces:` (LOCATE / READ / RETRIEVE calls made — for audit)
- `evidence.code_location: <file>:<line_range>` (if impl was found)
- `evidence.test_location: <file>:<line_range>` (if test was found)
- For `partially_compliant`: `missing: <text>` (specifically what's incomplete)
- For `not_compliant`: `violation: <text>` (specifically what the impl does wrong)
- For `requires_human_verification`: `reason: <text>` (specifically why an LLM can't judge)
- `confidence: high | medium | low`

---

## P3 — Aggregate

After per-REQ judgments are complete:

1. Compute `overall_label`:
   - `fully_compliant` — every REQ is fully_compliant (or `requires_human_verification` with explicit human OK from a prior session).
   - `partially_compliant` — at least one partially_compliant, no not_compliant on critical REQs.
   - `not_compliant` — any not_compliant on a critical REQ, OR many partial on critical REQs.
2. Compute `block_merge`:
   - true if any `not_compliant` on any REQ (critical or normal).
   - true if any `partially_compliant` on a `critical` REQ.
   - true if `requires_human_verification` is unresolved on a critical REQ.
3. Tally per-state counts for the report.

---

## P4 — Emit pm-review.yaml

Write to `--output` per `references/finding-schema.yaml`. User sees a one-line summary: "pm-reviewer: <fully>/<partial>/<not>/<needs-human> verdicts; block_merge=<bool>".

---

## Models

| Sub-component | Model |
|---|---|
| Main (normalize + judge) | `claude-opus-4-7` — reasoning + tool use heavy |
| Format parsers (P1, per-source) | `claude-haiku-4-5` (Jira→bullets, Linear→bullets, etc.; narrow tasks) |

Why Opus for the main pass: per-REQ judgment requires holding the SHALL clause + impl behavior + test pattern in working memory and reasoning carefully about partial-vs-fully distinction. Sonnet often misclassifies the partial-vs-fully boundary.

---

## Tools

- `glob` — LOCATE atom (file search by pattern)
- `grep` — LOCATE atom (content search)
- `read_file` — READ atom (verify impl)
- `git_log` — context on when impl was added (helps with trend tracking)
- `git_diff` — compare current state to `--prev-review` baseline

---

## When to refuse / redirect

- **Requirements source has 0 parseable requirements** — refuse, name the format and what was expected.
- **Code source is a diff but the requirements span across many unrelated changes** — proceed but warn: pm-reviewer is most accurate on cohesive change sets. Output `caveats.scope_mismatch: true`.
- **Source mixes functional and non-functional REQs and the non-functional ones dominate** — proceed but expect ≥50% of verdicts to be `requires_human_verification`. Output `caveats.non_functional_heavy: true`.
- **User asks for "code review" expecting bug-finding** — redirect to `/code-reviewer`. pm-reviewer answers compliance, not correctness in the general sense.
- **EARS spec has open `[?]` markers (incomplete clarify loop)** — refuse and redirect to `/acceptance-spec`. You cannot judge compliance against an ambiguous spec.

---

## Independent use cases

Beyond `/acceptance-fleet`:

- PRD validation pre-merge — pull a PRD, run pm-reviewer, see which REQs your PR actually satisfies.
- Sprint review — batch-run pm-reviewer over all closed Jira tickets in the sprint against the merged PRs.
- Compliance audits — regulatory requirements as the `<requirements_source>`, code as the impl; per-REQ verdict supports the audit trail.
- Customer acceptance — customer's acceptance criteria as `<requirements_source>`, beta build as code; automatic per-criterion sign-off.
- Cross-team handoff — receiving team runs pm-reviewer to verify the handed-off code actually meets the spec, before accepting.

The skill is contract-agnostic — it knows nothing about `done_when.yaml`. EARS specs are one of *many* `requirements_source` formats it handles.

---

## Resource index

- `references/requirement-normalization.md` — per-format parsers (EARS / Jira / Linear / PRD / GitHub issue / PR description)
- `references/agent-as-judge-protocol.md` — LOCATE / READ / RETRIEVE atom semantics + budget management
- `references/finding-schema.yaml` — strict pm-review.yaml output schema
