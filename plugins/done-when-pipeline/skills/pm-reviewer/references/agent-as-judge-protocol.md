# agent-as-judge-protocol.md — LOCATE / READ / RETRIEVE atoms

Borrowed from DevAI (Zhuge et al., ICML 2025). The paradigm replaces "LLM-as-Judge reads the code and forms an opinion" with "Agent uses tools to find evidence; the verdict is evidence-backed." Reported empirical gain in DevAI's 365-requirement benchmark: 70% → 90% agreement with human experts.

The three atoms are not "tools the agent might use" — they are the **mandatory** evidence-collection steps. A per-REQ verdict without all three populated `tool_traces:` fields fails schema validation.

---

## LOCATE — find code that *might* implement this REQ

Purpose: convert from the REQ's natural-language form to a concrete set of `file:line` candidates.

Tools used:
- `glob` — filename / path pattern matching
- `grep` — content matching
- (rarely) `find_similar` — semantic search if available

Inputs to LOCATE:
- The REQ's `bulleted:` line.
- Keywords extracted from the bulleted form (verbs, nouns).
- Known repo conventions (the `<code_source>` directory structure, recognized module names).

Output:
- A ranked list of `file:line` candidates.
- Empty list ⇒ strong signal toward `not_compliant`.
- Single high-confidence candidate ⇒ proceed to READ.
- >10 candidates ⇒ tighten the search before proceeding (you'll exhaust the tool budget).

Tool trace format:
```yaml
- { tool: LOCATE, query: "cancel*subscription", matched_files: ["src/billing/cancel.ts", "src/api/subscription.ts"] }
- { tool: LOCATE, query: "function.*cancel|def.*cancel", matched_count: 4 }
- { tool: LOCATE, query: "cancelledAt|cancelled_at", matched_count: 1, matched_files: ["src/billing/cancel.ts"] }
```

LOCATE pitfalls:
- **Over-narrow query** returns 0 matches when the impl uses a synonym. Try 2-3 query variants before concluding.
- **Over-broad query** returns 100+ matches that drown signal. Add a path constraint (`src/billing/**`) or AND-multiple terms.
- **Generated code** (compiled JS, dist/, vendor/) often pollutes results. Exclude common generated-code paths automatically.

LOCATE budget: typically 2-5 queries per REQ. Past 8, the REQ is either not implemented (→ `not_compliant`) or the searches are wrong (→ rethink the query). Do not loop LOCATE past 10 calls per REQ.

---

## READ — verify the SHALL clause is honored

Purpose: confirm or refute that the candidate code, when executed, would produce the behavior the REQ requires.

Tools used:
- `read_file` — with line range, multi-hop into related files as needed

Inputs to READ:
- The candidate file:line from LOCATE.
- The REQ's bulleted form (what should happen).
- The repo's surrounding context (imports, types, call sites).

Output:
- A determination: "the impl does / does not / partially does what the REQ requires."
- Cited line ranges supporting the determination.

Tool trace format:
```yaml
- { tool: READ, file: "src/billing/cancel.ts", lines: [42, 58], observation: "cancelSubscription mutates status to 'cancelled_active' at L47 and writes timestamp via new Date().toString() at L50. toString() returns local time, not UTC." }
- { tool: READ, file: "src/billing/types.ts", lines: [12, 18], observation: "Subscription type has cancelled_at: string — no format constraint enforced by type." }
```

READ pitfalls:
- **Reading too narrowly** misses the upstream check or downstream effect. If the candidate is a function call, also READ the function definition. Multi-hop is the norm, not the exception.
- **Assuming `toString()` does the same as `toISOString()`** etc. Read carefully; runtime behavior often differs from intuitive expectation. Where you cannot verify with confidence, downgrade to `medium` or `low` confidence.
- **Comments are not behavior.** `// returns UTC timestamp` is not evidence that the code returns UTC; the actual call site is. Comments can lie.

READ budget: typically 2-6 reads per REQ. Multi-hop into 3-5 files is common for cross-module REQs. Past 10 reads, you're either over-investing on a single REQ or the REQ spans the whole architecture and should have been split.

---

## RETRIEVE — find the matching test

Purpose: locate a test that exercises this REQ, to confirm there's a regression safety net.

Tools used:
- `glob` over `tests/` (or equivalent)
- `grep` for `based_on: <REQ-ID>` annotations
- `grep` for test names that contain REQ keywords

Inputs:
- The REQ-ID.
- The REQ's bulleted form (for semantic matching when no `based_on:` annotation).

Output:
- A test file:line — or none.
- A determination: "test exists and reasonably covers this REQ" vs "test exists but exercises only part" vs "no test found".

Tool trace format:
```yaml
- { tool: RETRIEVE, query: "based_on:\\s*REQ-001", matched_files: ["tests/subscription-cancellation/unit/test_cancel_records_timestamp.py"] }
- { tool: RETRIEVE, query: "test.*timestamp.*utc", matched_files: ["tests/subscription-cancellation/unit/test_cancel_records_timestamp.py"] }
- { tool: RETRIEVE, observation: "test_cancel_records_timestamp asserts cancelled_at is a valid ISO-8601 UTC string. This covers REQ-001's format requirement; does not cover the boundary semantics (REQ-001 line 'cancel honors UTC boundary')." }
```

RETRIEVE pitfalls:
- **Test name ≠ REQ coverage.** A test named `test_cancel` doesn't automatically cover all cancel-related REQs. Read the test body briefly.
- **A test that exists but skips** (via `@pytest.mark.skip`, `it.skip`) is *not* coverage. Note in tool trace.
- **A property-based test** can cover broad REQ space with one test name. If found, this is usually higher confidence than an example-based test of equivalent name.
- **Tests in different layer** (e.g. REQ implies unit-level invariant but only e2e test exists) is `partially_compliant: missing` rather than `fully_compliant`.

RETRIEVE budget: 1-3 queries per REQ. Cheap.

---

## Putting the atoms together

The atoms are sequenced LOCATE → READ → RETRIEVE in 90% of cases. But the order can vary:

- For a REQ that's "remove behavior X" (no positive impl), start with `LOCATE` for X's absence then RETRIEVE the test that asserts X is gone.
- For a REQ that's a refinement of an existing behavior, start with RETRIEVE to find the existing test, then READ to see if the test's assertion was tightened.
- For non-functional REQs (performance, security posture), READ may not apply directly; the verdict is usually `requires_human_verification` regardless.

The Agent-as-Judge discipline: **whatever order you choose, all three are tracked in the output**. A `tool_traces:` block with only READ calls means you forgot LOCATE — the verdict is unreliable and should be reworked.

---

## Tool budget per REQ

Default: 20 tool calls per REQ across all three atoms. Past 20 per REQ, the agent is over-investing — either the REQ is too broad (should be split upstream) or the search is misaligned (the agent should reconsider).

When budget exhausted without a confident verdict → emit `verdict: requires_human_verification` with `reason: "exceeded LOCATE/READ budget without converging — likely too broad or implementation distributed"`. This is honest; do not paper over with a guess.

---

## What the atoms do NOT cover

- **Runtime verification.** Whether the test *passes* on the current impl is `/qa-reviewer`'s territory. pm-reviewer judges from static reading; qa-reviewer runs.
- **Coverage measurement.** Whether the test exercises 80% of the impl's branches is `/qa-reviewer` + mutation testing's territory.
- **Bug detection beyond the REQ.** If during READ you spot a SQL injection unrelated to the current REQ, do not flag it. Note in `out_of_scope_observations:` and let `/code-reviewer` handle.
- **Gaming detection.** If the impl satisfies the REQ via a lookup table where an algorithm was intended, that's gaming — `/spec-gaming-detector`'s territory. pm-reviewer downgrades to `partially_compliant` and notes "degenerate impl suspected", but the gaming-specific analysis lives elsewhere.

The boundary discipline keeps pm-reviewer's signal clean. Cross-skill synthesis is `/meta-judge`'s job.
