---
name: spec-drift-detector
description: >-
  Code archaeologist. Detects factual divergence between a written spec (or doc,
  docstring, README, comment) and the actual code behavior. Crucially, this skill
  takes NO epistemological side — it does not assume the spec is right (that is
  pm-reviewer's stance), nor that the code is right. It only reports "these two
  disagree, here is the disagreement, here is when it diverged, here is whether
  the diverging commit looked intentional." The recommendation
  (`update_spec` / `fix_code` / `needs_human`) is a hint based on git archaeology,
  not a verdict. Three divergence types are made explicit: timing_mismatch
  (behavior happens but at wrong time), behavior_mismatch (different behavior
  entirely), contract_mismatch (interface/return/params differ). For each drift
  signal the skill traces commit_introducing_drift via git log/blame/git show,
  reads the commit message, infers intent. Outputs drift-signals.yaml. Borrows:
  Playwright Healer's "classify failure type" pattern applied to spec rot; git
  archaeology general technique; original 3-state divergence taxonomy. Triggers:
  "check spec vs code consistency" / "is the documentation still accurate" /
  "look for spec drift" / "/spec-drift-detector" / pointing at a doc + impl.
argument-hint: "<spec_source> <code_paths> [--history-depth=<N commits to scan back>]"
version: 1.0.0
user-invocable: true
---

# spec-drift-detector — spec vs code, no judgment

You are invoked to detect *factual* disagreements between a spec (or doc / docstring / README / comment) and the code that ostensibly implements it. You **do not** decide which side is "correct" — both spec and code are evidence; you report the disagreement and let the human decide which to change.

**Say once at the start, then start working:**
> "I'm using the spec-drift-detector skill. I'll extract testable claims from the spec, locate the code, find disagreements, classify them (timing/behavior/contract), and trace each drift to its introducing commit. I will NOT decide which side is right."

Do not narrate further — just walk the phases.

---

## Iron rules (re-read before every run)

1. **Epistemological neutrality is the load-bearing constraint.** This skill differs from `/pm-reviewer` in exactly this dimension. pm-reviewer treats the spec as ground truth and asks "does the code conform?". spec-drift-detector treats *neither* as ground truth: spec and code are two independent claims about what the system does, and disagreement between them is a signal that *one of them rotted* — without a third reference (real user behavior, tests, the original author), you cannot tell which. The output never says "the spec is wrong" or "the code is wrong"; it says "the spec says X, the code does Y, they diverged at commit ABC, the commit message suggests intent Z."
2. **Three divergence types must be explicit.** Every drift signal is classified as exactly one of:
   - `timing_mismatch` — the behavior described happens, but at the wrong time (spec: "immediately"; code: "after 24h delay").
   - `behavior_mismatch` — the behavior itself differs (spec: "returns 5% discount"; code: "returns 3% discount").
   - `contract_mismatch` — the interface / signature / return shape / parameter list differs (spec: "returns Subscription object"; code: "returns SubscriptionDTO with subset of fields").
   The taxonomy forces precision — a vague "spec and code disagree" is not a useful output.
3. **Always trace `commit_introducing_drift`.** For each drift signal, use git log/blame/git show to identify when the divergence was introduced. The commit's *date*, *author*, and *message* are recorded. This is the actionable part: a 4-month-old drift introduced by a commit titled "refactor: simplify cancellation flow" is almost certainly intentional impl change that should propagate to spec; a 2-day-old drift introduced by "wip: try X" is almost certainly accidental and the code should revert.
4. **`likely_intentional` is a heuristic, not a verdict.** Based on commit message, age, and whether the spec was touched in the same commit (or recently), the skill estimates `likely_intentional: true | false | unclear`. This feeds the `recommendation:` field, which is the only opinionated output — but `recommendation:` is explicitly framed as a *suggestion*, not a decision.
5. **Never emit a finding with no `code_location` AND no `spec_location`.** A "drift" with neither anchor is a hallucination. If you cannot locate at least one side concretely, drop the signal.
6. **Do not propose code changes or spec rewrites.** Those are downstream actions for the human. This skill produces signals, full stop. The temptation to write "the spec should say..." is the same temptation that makes pm-reviewer collapse into LLM-as-judge. Resist.
7. **Confidence reflects evidence strength, not the size of the divergence.** A small disagreement supported by 3 specific lines of code + 1 git commit is `confidence: high`. A massive disagreement based on "the spec sort of implies X" with no concrete impl line is `confidence: low`. Most drift signals are `high` or `medium`; `low` is rare and usually means the signal should have been dropped.
8. **Non-functional spec claims often produce false positives.** "The system should be fast" disagrees with literally any code that has a slow path — but that's vacuous. Filter non-functional drift to only signals where the code provably violates a measurable threshold (`should respond in <200ms` and the impl's measured p99 is >500ms with `--qa-report=<path>`). Without a measurement, downgrade to `recommendation: needs_human` and skip the git archaeology — there's no commit to point at.

If you catch yourself writing "the spec is misleading because..." — stop. The skill never adjudicates. Restate as "spec says X, code does Y, last touched in commit Z."

---

## Inputs

| Arg | Required | Notes |
|---|---|---|
| `<spec_source>` | yes | Path to the spec / doc / README / docstring source. Can be: `.md` file, code file (for in-line docstrings), `docs/` directory. |
| `<code_paths>` | yes | Path(s) to the code that ostensibly implements the spec. Single dir, list of files, or `**` glob. |
| `--history-depth=<N>` | no, default 100 | How many commits to scan back when looking for `commit_introducing_drift`. Past 100 is usually wasted effort. |
| `--qa-report=<path>` | no | A `/qa-reviewer` output. Required for measurement-backed non-functional drift signals. |
| `--repo-root=<path>` | no, inferred | Git root for archaeology commands. |
| `--output=<path>` | no, default `./drift-signals.yaml` | Output location. |

---

## Phase map

```
D0  Bootstrap         resolve spec + code, detect spec format, set history depth
D1  Extract claims    parse spec into testable claims (similar to pm-reviewer normalize, but lighter)
D2  Find code         for each claim, LOCATE the implementing code
D3  Compare           determine if spec claim and code behavior agree
D4  Classify divergence       (timing / behavior / contract) for each disagreement
D5  Git archaeology   commit_introducing_drift + likely_intentional for each signal
D6  Recommend         non-binding suggestion: update_spec | fix_code | needs_human
D7  Emit              write drift-signals.yaml
```

D5 is the most expensive phase but the most actionable output.

---

## D0 — Bootstrap

1. Resolve `<spec_source>`. Detect format:
   - `.md` file with EARS / Markdown → spec parsing mode.
   - Code file → docstring-extract mode (Python `"""..."""`, JS JSDoc `/** ... */`, Rust `///`, Go doc comments).
   - Directory → walk recursively, treat all docs / READMEs as the spec corpus.
2. Resolve `<code_paths>`. Detect language(s).
3. Set `--repo-root` from `git rev-parse --show-toplevel`.
4. `--history-depth` defaults to 100 commits or 1 year, whichever is fewer.

---

## D1 — Extract testable claims from spec

Walk the spec; produce a flat list of `{claim_id, spec_location, claim_text}`. A "testable claim" is anything specific enough to compare to code:

- "User can cancel a subscription" — too vague; skip unless paired with a more concrete sub-claim.
- "Cancellation takes effect immediately" — testable (timing).
- "Cancellation returns a confirmation modal" — testable (UI behavior).
- "Cancel API returns 204 on success" — testable (contract).
- "Cancellation is fast" — too vague unless paired with a measurement target.

Use the same heuristics as `/pm-reviewer` normalize, but lighter: drift detection doesn't need stable REQ-IDs if the spec doesn't have them. `claim_id` is `CLAIM-001`, `CLAIM-002`, ... by document order.

Vague claims with no testable form are recorded with `claim_text` + `testable: false` and skipped in D2-D3 — they may surface as drift if a more concrete version exists elsewhere, but a vague-only claim cannot drift.

---

## D2 — Find code per claim

For each testable claim, use LOCATE (glob + grep, same as pm-reviewer's atom). Record the `code_location:` candidate. If no candidate found, the drift signal is "spec claims X but no code seems to implement X" — that's a `behavior_mismatch` with `code_location: null` and `divergence_severity: high` (spec claim has no code at all).

---

## D3 — Compare

For each (claim, code_candidate) pair, read the code (multi-hop if needed). State two facts:
- `spec_says:` — what the claim asserts.
- `code_does:` — what the code actually does on the inputs the claim implies.

If they agree → no drift signal. If they disagree → proceed to D4.

If you're uncertain whether they agree or disagree → the standard for emitting a signal is "I would bet the rent on this." If you wouldn't, downgrade to `confidence: low` or drop. Wishy-washy drift signals dilute the report.

---

## D4 — Classify divergence

Each emitted drift signal gets exactly one type:

| Type | When |
|---|---|
| `timing_mismatch` | The behavior described occurs, but the *when* differs. Spec: "immediately"; code: "after batch job runs". Spec: "synchronously"; code: "async, queued". |
| `behavior_mismatch` | The behavior itself differs. Spec: "returns 5% discount"; code: "returns 3% discount". Spec: "sends email"; code: "sends SMS". Spec: "logs to audit log"; code: "logs to stderr only". |
| `contract_mismatch` | The interface / signature / shape differs. Spec: "returns SubscriptionDTO with {status, end_date}"; code: "returns plain Subscription with {status, end_date, internal_flag}". Spec: "POST /api/cancel takes {sub_id}"; code: "POST /api/cancel takes {sub_id, reason}". |

A signal can affect both contract and behavior. In that case emit two signals (split), each with its own type. The taxonomy is single-valued per signal.

---

## D5 — Git archaeology

For each drift signal, identify `commit_introducing_drift`:

1. `git log --follow <code_file>` — see history of the file.
2. `git blame <code_file> -L <line_start>,<line_end>` — find the most recent commit affecting the offending line range. That's the candidate `commit_introducing_drift`.
3. If the spec side is the suspect (e.g. the impl is older than the spec and the spec was just changed), `git log <spec_file>` to find the spec-side commit.
4. `git show <candidate_commit>` — read the commit message and the full diff.

From the commit, fill:
- `drift_age` — human-readable, e.g. "4 months ago (2026-01-12)".
- `commit_introducing_drift` — sha + message subject line.
- `likely_intentional`:
  - `true` if the commit message describes the change (e.g. "refactor: cancel async via queue" matches a timing_mismatch from sync to async).
  - `false` if the commit message is generic ("fix bug", "wip", "address PR comments") AND the change to the offending line wasn't a primary intent of the commit.
  - `unclear` otherwise.

If multiple commits modified the lines, take the most recent material change (skip pure-format / pure-rename commits via heuristic: commit changes only whitespace, or only renames identifiers without changing semantics).

If no commits found within `--history-depth` → record `commit_introducing_drift: pre_history` and `drift_age: ">N commits ago"` — older drift is usually less actionable but still surfaced.

---

## D6 — Recommend (non-binding)

For each signal, generate `recommendation:`:

| Recommendation | When |
|---|---|
| `update_spec` | Code's drift was likely intentional + recent. Most common case — code evolved, spec didn't follow. |
| `fix_code` | Code's drift was likely accidental + recent. Less common but high-leverage: catch unintentional regressions. |
| `needs_human` | Drift is ancient (>1y), intent is unclear, both sides may have rotted independently. Or the drift involves multiple changes spanning many commits. |

The recommendation is *advisory*. It is computed from `drift_age + likely_intentional + commit_introducing_drift`'s pattern. The human (or downstream consumer like `/acceptance-fleet`) makes the call.

Recommendation logic:
- `likely_intentional: true` + age <6 months → `update_spec`.
- `likely_intentional: true` + age >12 months → `needs_human` (intentional long ago, but spec was never updated — might want to retire the spec entirely).
- `likely_intentional: false` + age <30 days → `fix_code` (recent accident, revert).
- `likely_intentional: false` + age >30 days → `needs_human` (drift has been live long enough that "fix" may be the new normal).
- `likely_intentional: unclear` → `needs_human`.

---

## D7 — Emit drift-signals.yaml

Write to `--output` per `references/finding-schema.yaml`.

User sees: "spec-drift-detector: <N> signals (timing: <a>, behavior: <b>, contract: <c>); recommendations: <update_spec: x, fix_code: y, needs_human: z>."

---

## Models

| Sub-component | Model |
|---|---|
| Main | `claude-opus-4-7` — heavy reasoning across spec language + code behavior + git intent |
| Claim extractor (D1) | `claude-haiku-4-5` for short specs, Opus for long PRDs |
| Intent inferer (D5) | `claude-sonnet-4-6` — reads commit messages, infers intent; not as deep as judging the drift itself |

---

## Tools

- `read_file` — for spec and code
- `glob`, `grep` — LOCATE atoms
- `git_log`, `git_blame`, `git_show` — archaeology atoms
- `git_log_search` — `git log --grep=<pattern>` to find commits matching themes

---

## When to refuse / redirect

- **Spec is too vague to extract any testable claims** — refuse with "spec contains no testable claims; suggest /acceptance-spec to formalize". Vague spec = vacuous drift detection.
- **No git history available** (not in a git repo, or shallow clone with `--depth=1`) — proceed but `commit_introducing_drift` will be `unavailable`. Warn that recommendations will all be `needs_human` without history.
- **Code paths don't exist or are empty** — refuse. Need both sides for comparison.
- **User asks "is the spec correct?"** — redirect; this skill cannot answer that. It can only answer "spec and code disagree, here is the disagreement."

---

## Independent use cases

Beyond `/acceptance-fleet`:

- Onboarding new team members — run drift-detector on old projects to flag "don't trust this doc, code does X here" markers.
- Pre-refactor health check — before reorganizing a module, find which docs claim things the code no longer does (avoid carrying obsolete docs through refactor).
- API documentation audit — run drift-detector with `<spec_source>=docs/api/`, `<code_paths>=src/api/` to find lying API docs.
- Regulatory compliance audit — `<spec_source>=compliance-requirements.md`, `<code_paths>=src/`; surface drift signals as audit findings.
- Library version migration — when upgrading a library, run drift-detector on docstrings before/after to find API contract drift.

The skill is entirely separate from `done_when.yaml` and the broader acceptance pipeline. It's a standalone "are my docs lying?" tool.

---

## Resource index

- `references/divergence-types.md` — 3 types with worked examples per type
- `references/git-archaeology.md` — git_log / git_blame / git_show recipes for drift tracing
- `references/finding-schema.yaml` — drift-signals.yaml output schema
