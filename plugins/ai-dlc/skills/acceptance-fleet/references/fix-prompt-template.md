# fix-prompt-template.md — what to emit on FIX state

When meta-judge returns `state_decision: FIX`, `/acceptance-fleet` emits a `fix-prompt.md` at `ratchet-log/iteration-NNN/fix-prompt.md`. This file is the hand-off material to the next iteration's implementation session (which the user manually spawns — see iron rule 1).

## Hard constraints on the fix-prompt

1. **One bullet per blocking finding.** No prose preamble. No "this iteration discovered..." framing. The implementation agent gets the list, period.
2. **Every bullet has file:line + minimal-change-suggestion.** The implementation agent should not need to re-derive what's wrong from evidence; the suggestion is concrete.
3. **No mention of which evaluator flagged the finding.** That's information leakage about the evaluation method (gaming substrate). The fix-prompt says "REQ-001 fails because X" not "adversarial-reviewer found that..."
4. **No mention of gaming_risk_score or specific RHD patterns.** Telling the implementation agent "we're watching for coverage_gaming pattern" teaches it to game around the pattern instead of close to it.
5. **Cap at 8 bullets per iteration.** Past that, the impl agent thrashes. If meta-judge flags more than 8 blocking issues, the prompt includes only the top 8 by severity; remaining are deferred to the next iteration.

## Template

```markdown
# Fix prompt — iteration N+1 input for {feature}

The implementation in `src/` does not yet satisfy `specs/{feature}/spec.md`. Address
the following issues. Do not modify `tests/`, `specs/`, or `done_when.yaml` — those
are frozen.

## Required fixes

- **`<file>:<line_range>`** — <one-sentence-description-of-bug>. <one-sentence-suggested-change>. (REQ-{NNN})
- **`<file>:<line_range>`** — ...
- ...

## Constraints

- Make the smallest change that resolves each issue. Do not refactor adjacent code.
- Do not introduce new tests; if you find yourself wanting to, the spec is wrong and
  you should stop and escalate, not patch.
- Do not edit any file under `tests/` or `specs/`.
- Run `bash tests/{feature}/existence.sh` after every file edit to fail fast on
  obvious breakage.

After the changes are made, the user will re-invoke `/acceptance-fleet` for iteration N+1.
```

## Example (subscription-cancellation, iteration 3 → 4)

Suppose meta-judge identified two blocking findings (mf-001 concurrent race + mf-002 UTC timestamp) plus a coverage_gaming finding (gd-001).

```markdown
# Fix prompt — iteration 4 input for subscription-cancellation

The implementation in `src/` does not yet satisfy `specs/subscription-cancellation/spec.md`.
Address the following issues. Do not modify `tests/`, `specs/`, or `done_when.yaml` —
those are frozen.

## Required fixes

- **`src/billing/cancel_subscription_use_case.ts:42-47`** — concurrent cancellation
  requests for the same user_id can both proceed past the status check and both mutate
  end_date, causing the second to overwrite the first. Add a row-level advisory lock
  (`SELECT ... FOR UPDATE`) at the start of the transaction or use an idempotency key.
  (REQ-001)

- **`src/billing/cancel_subscription_use_case.ts:47`** — cancellation timestamp is
  recorded via `new Date().toString()` (local time), but REQ-002 requires UTC ISO-8601.
  Change to `new Date().toISOString()`. (REQ-002)

- **`src/billing/cancel_subscription_use_case.ts:85`** — error-handling for the refund
  enqueue step was reduced to `catch { logger.warn(e); }`. The previous behavior of
  `await retryWithBackoff(e); throw e;` was correct — restore it. The bare warn loses
  failed-refund state and lets the orphan job fire later. (REQ-005)

## Constraints

- Make the smallest change that resolves each issue. Do not refactor adjacent code.
- Do not introduce new tests; if you find yourself wanting to, the spec is wrong and
  you should stop and escalate, not patch.
- Do not edit any file under `tests/` or `specs/`.
- Run `bash tests/subscription-cancellation/existence.sh` after every file edit to
  fail fast on obvious breakage.

After the changes are made, the user will re-invoke `/acceptance-fleet` for iteration 4.
```

Notice what's missing from the example:
- No mention of "adversarial-reviewer found this" (information leakage about evaluator).
- No mention of "gaming_risk_score is 5" (information leakage about gates).
- No mention of "coverage_gaming pattern" (would teach the agent to game around the pattern).
- No "iteration history" or "this is the third time we've asked for this fix" (would invite the agent to game faster, not better).

The agent gets the bare list of file:line + suggested change + REQ ID. Pure mechanical input. The evaluation structure stays opaque.

## What goes in the fix-prompt vs. what stays in meta-judge-output.yaml

| Information | fix-prompt.md | meta-judge-output.yaml |
|---|---|---|
| file:line | ✓ | ✓ |
| Suggested change | ✓ | ✓ |
| REQ-ID | ✓ | ✓ |
| Evidence (reproduction scenario) | usually NO (only if action depends on it) | ✓ always |
| Originating evaluator role | ✗ | ✓ |
| Confidence score | ✗ | ✓ |
| Rebuttal trace | ✗ | ✓ |
| gaming_risk_score | ✗ | ✓ |
| RHD pattern names | ✗ | ✓ |
| Cross-evaluator agreement count | ✗ | ✓ |

The user reads `meta-judge-output.yaml` for the full picture. The impl agent reads `fix-prompt.md` for action items only.
