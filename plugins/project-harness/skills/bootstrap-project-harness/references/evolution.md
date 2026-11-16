# Evolution from verified failure

Confirm the actual root cause and a reproducer. Ask whether this is recurring or has sufficiently irreversible impact to merit a persistent constraint, respecting project policy. Prefer the cheapest effective form: existing regression test or native lint, then current coding standard or concise learning. Merge or correct prior material when it already owns the subject.

For a reproduced operation sequence, use [learning.md](learning.md): collect the original raw failure, qualify on the failing and repaired candidates, promote an additive regression under scoped authorization, run it on the next candidate and retain observations/rollback history. This is executable regression data; rules and acceptance predicates do not rewrite themselves.

Record the source decision/incident, intended scope, legitimate counterexample and rejection fixture. Use survey and a minimal proposal for the existing configuration, apply the reviewed plan, then verify positive/negative behavior and current-tree impact. A check that rejects valid existing usage is not ready to block new work.

Do not invent a second feature tracker, task runtime, acceptance authority or general knowledge corpus. The calling agent owns task orchestration and retry budget. The project owns its architecture, exceptions, business expectations and native checks. Factory evolution changes the reusable manufacturing behavior only when evidence supports a broader pattern.
