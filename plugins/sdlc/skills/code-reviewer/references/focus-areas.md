# focus-areas.md — what to look for per --focus

Each focus narrows the agent's attention. The lists below are the questions the agent should ask while running the Detective Loop (S2 of `SKILL.md`). They are **not** exhaustive — they are anchors. The Detective Loop's strength is multi-hop exploration; the lists prevent it from wandering off into adjacent focuses.

---

## --focus=security

Primary question: **"Can a hostile or buggy caller cause unintended state change or unauthorized access?"**

Hunting list:

1. **Authorization / ownership checks.** Is every `user_id` / `account_id` / `tenant_id` parameter cross-checked against the calling identity? `grep` for `verifyOwnership`, `assertOwner`, `currentUser.id ==`, etc. Missing check on a mutation endpoint is P0.
2. **Input validation.** Are user-supplied strings / numbers / paths validated before use? Specifically: path traversal (`..`), SQL injection (raw string concat), command injection (`exec`/`spawn` with user data), XSS (rendered HTML), prototype pollution (`Object.assign` on user JSON).
3. **Secret handling.** Are secrets logged? Sent to error reporters (Sentry/Datadog)? Returned in error messages? Stored in source? `grep` the diff for `console.log` / `logger.*` near `password|token|secret|api_key`.
4. **Cryptographic missteps.** Weak hashes (`md5`/`sha1` for security), missing salt, `Math.random()` for tokens, hardcoded IVs, `==` instead of constant-time compare for tokens.
5. **CSRF / auth-state.** State-changing endpoints lacking CSRF token check or `SameSite` cookie config. Session-cookie not set `HttpOnly` / `Secure`.
6. **Rate limiting / abuse.** Mutation endpoints with no rate limiting, account-enumeration risk in login error messages, unbounded loops over user-controlled iteration counts.
7. **Dependency trust.** New `import` from a package never used before — verify it is the canonical package (`react`, not `react-script-loader-x`). `grep` for typos / homoglyphs.

Severity guide:
- P0: authz check missing on mutation endpoint, SQL injection vector with concrete trigger, secret in source.
- P1: input validation gap with concrete bypass scenario, weak crypto on user-facing token.
- P2: rate limit absent, secret accidentally in log line (not error path).
- P3: hardening suggestion (e.g. `SameSite=Strict` instead of `Lax`).

---

## --focus=logic

Primary question: **"Does this code do what its name implies, on all inputs the spec allows?"**

Hunting list:

1. **State mutations.** Order-of-operations bugs (check-then-set without lock, write-then-read assuming sync). Race windows: `if (sub.status === 'active') { sub.status = 'cancelled' }` is two operations.
2. **Exception paths.** `try { ... } catch (e) { /* nothing */ }` (silent swallow), `catch (e) { logger.warn(e) }` where retry was needed, broad `except:` clauses.
3. **Boundary conditions.** Off-by-one (`<` vs `<=`), empty input (empty array / null / undefined), max-length input.
4. **Concurrency.** Two callers same flow → both pass guard → both mutate. Idempotency assumed but not enforced (request retry creates duplicates).
5. **Null / undefined / missing keys.** `obj.field.subfield` chain without checking intermediate, `Array.prototype.find()` returning `undefined`, `dict[key]` raising `KeyError`.
6. **Numerical correctness.** Float comparisons (`if (x === 0.3)`), integer overflow on accumulator, division by zero, currency in floating-point.
7. **State machine violations.** Transitions reachable on paper but unhandled in code; reverse transitions allowed when spec implied one-way.
8. **Fallback masks original error.** `catch { return default }` when caller needs to know the real failure mode.

Severity guide:
- P0: silent data corruption, race window with concrete trigger, exception swallowed in money-handling code path.
- P1: off-by-one with reachable input, null pointer dereference with realistic call site.
- P2: float comparison, broad except, fallback that hides a recoverable error.
- P3: minor unreachable branch (`if (false) { ... }`).

---

## --focus=perf

Primary question: **"Will this be slow / expensive at realistic scale?"**

Hunting list:

1. **N+1 patterns.** Loop over collection, inside loop call DB / API. `grep` for `for ... await db.find()` / `forEach(... fetch(...))`.
2. **Sync I/O in hot path.** `readFileSync` in a request handler, `Sleep(n)` blocking event loop.
3. **Unbounded growth.** Accumulator without cap, retry loops without max retries, recursion without base case + depth limit.
4. **Allocations in hot path.** `JSON.parse(JSON.stringify(...))` deep clone in tight loop, regex compiled per iteration, large array `concat` in reducer.
5. **Cache miss / wrong key.** Cache key includes timestamp (always miss), cache key omits a parameter the value depends on (returns wrong value).
6. **Database queries.** Missing index for filter column, `SELECT *` when query needs 2 fields, `OFFSET N` pagination on large tables (use cursor).
7. **Algorithmic.** O(n²) where O(n log n) is standard (e.g. `arr.find()` inside `arr.map()`), repeated sort instead of single sort + scan.

Severity guide:
- P0: rarely — perf issues seldom warrant P0 unless they cause outage (e.g. unbounded retry storm).
- P1: N+1 in request handler with realistic page size, sync I/O blocking event loop in server code.
- P2: algorithmic complexity issue with bounded but slow scaling, missing DB index.
- P3: micro-optimizations (rare to flag).

Do NOT flag perf "because LLM intuition says it's slow." If you cannot estimate the scale (rows / requests / ms), downgrade to P3 with `confidence: low` and note the scale assumption.

---

## --focus=style

Primary question: **"Will future maintainers be confused or misled by this code?"**

Hunting list (be sparing — style findings are the most likely to be padding):

1. **Misleading names.** `cancelSubscription` that also refunds, `isActive` returning a string, function whose name implies pure but has side effects.
2. **Dead code.** Functions never called, imports never used (verify with grep first; tooling sometimes misses re-exports).
3. **Commented-out code.** Should be deleted; git keeps history.
4. **Magic numbers / strings.** Bare `60 * 60 * 24` (use `SECONDS_PER_DAY`), `'cancelled_active'` repeated 5+ times.
5. **Long parameter lists.** >5 positional params usually want a record / dict.
6. **TODO / FIXME / HACK in the diff.** Flag at P3 — not blocking, but tracking.

Severity guide for style:
- P0/P1: never. Style is by definition non-blocking. If a "style" issue is actually a bug, it belongs in logic / security focus instead.
- P2: misleading name on a public API.
- P3: most other style issues.

Style focus should usually emit 0-2 findings. If you emit 5, you are padding.

---

## --focus=all

Run with `claude-opus-4-7` only. Walk all four hunting lists. Apply the same 5-finding cap. The model self-prioritizes which 5 are most worth reporting.

This mode is convenient but loses the parallelism benefit. For PRs >50 lines, prefer running four `--focus=<area>` sessions in parallel (security on Opus, logic on Opus, perf on Sonnet, style on Haiku) and synthesizing via `/meta-judge`.

---

## --adversarial modifier

Stackable with any `--focus`. Replaces the default agent stance with:

> "Assume this code caused a production incident. Your job is to find why. If you say 'looks good', you fail your job."

Effect: shifts severity distribution upward (more P0/P1, fewer P3), bypasses some sycophancy. Requires cross-vendor or different-size Claude per the iron rule. Most useful on `--focus=security` and `--focus=logic`; less useful on `--focus=style`.
