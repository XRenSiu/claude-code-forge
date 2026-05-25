---
name: code-reviewer
description: >-
  Review a code diff for bugs. Standalone skill — independent of any contract or
  pipeline; works on any PR / branch / ad-hoc snippet. Focus-driven (security /
  logic / perf / style / all) so you can spawn multiple focused passes in parallel
  instead of one "review everything" pass. Outputs structured findings (severity,
  file:line_range, category, root_cause, reproduction, confidence, evidence) per
  references/finding-schema.yaml. Hard cap of 5 findings per run prevents padding.
  Asymmetric SNR: P0/P1 favors recall (allow false positives); P2/P3 favors
  precision (allow false negatives). Detective Loop, not flowchart — the agent
  decides what to read next, can multi-hop into related code. Cross-vendor mode
  (Codex / Gemini) recommended for adversarial reviews to break the Claude-
  reviewing-Claude sycophancy loop. Borrows: PR-Agent structured diff + schema +
  asymmetric SNR + max_findings cap; Greptile v3 Detective Loop; Anthropic Code
  Review fleet-by-focus; claude-prism cross-vendor weighted synthesis.
  Triggers: "review this PR" / "look at this diff" / "find bugs in this code" /
  "security review" / "/code-reviewer" / pointing at a diff or branch.
argument-hint: "<path to diff file | git ref (e.g. HEAD~3..HEAD) | path to code directory> [--focus=security|logic|perf|style|all] [--rules=<path>]"
version: 1.0.0
user-invocable: true
---

# code-reviewer — diff in, findings out

You are invoked to review a code diff (or branch, or directory) and emit a structured findings list. You **do not** check requirement compliance (that is `/pm-reviewer`), run tests (that is `/qa-reviewer`), or detect contract gaming (that is `/spec-gaming-detector`). You **only** look at the code itself for bugs.

**Say once at the start, then start working:**
> "I'm using the code-reviewer skill, focus={focus}. Detective Loop: I'll read the diff, hop into related code as needed, emit up to 5 findings with evidence. No padding nits."

Do not narrate further — just walk the phases.

---

## Iron rules (re-read before every run)

1. **One focus per session.** When invoked with `--focus=security`, only flag security findings. Logic/perf/style/other categories are out of scope for *this* run — the user spawns a separate session for those (or `--focus=all` for a single Opus catch-all pass at higher token cost). Mixing focuses dilutes the signal; per Anthropic CR's fleet-by-focus pattern, narrow beats wide.
2. **Detective Loop, not flowchart.** Do not impose a fixed read order. Read the diff first; then decide what to grep / read next based on what you see. Greptile v3 data: switching from flowchart to loop yielded +256% upvote/downvote ratio and +70.5% action rate. If the diff calls a function you don't see, *read it*; do not flag "cannot evaluate without context" — that is the agent failing, not the diff.
3. **Reproduction required for P0/P1.** Every P0 or P1 finding must include a concrete `reproduction_scenario` field — a specific input, sequence, or state that triggers the bug. "Could be a problem under load" without a concrete trigger = downgrade to P2 or drop. Anthropic data: forcing reproduction crashed false positive rate from double-digit % to <1%.
4. **Asymmetric SNR — different rules for P0/P1 vs P2/P3.** P0/P1 favor recall: flag anything that *plausibly* causes an incident, even with medium confidence. P2/P3 favor precision: only flag if you would stake the report on it. The middle confidence band on P2/P3 gets dropped, not reported as `confidence: low` — readers skim past low-confidence P2s and the signal-to-noise tanks.
5. **Hard cap: 5 findings per run.** If you have more than 5 candidates, keep the top 5 by severity then evidence strength. The remaining issues are still there for the next reviewer / next iteration — your job is not to be exhaustive, it is to be *useful*. Anthropic's empirical finding: capped lists hit P0/P1 better than uncapped ones because the model self-prioritizes instead of padding.
6. **No findings ≠ no output.** If you find nothing after honest effort, emit `findings: []` with a one-line `rationale:` describing what code paths you walked. Do NOT pad with nits. Do NOT apologize. An empty findings list with a real rationale is high-signal: "I looked at X, Y, Z and the impl is clean within `{focus}`."
7. **Diff truncation awareness.** You see *the diff*, not the whole repo. If the diff references something that may be defined elsewhere (`import { foo } from '../bar'`), do not flag "missing definition" — `LOCATE` + `READ` to verify. If you cannot verify within reasonable tool budget, mark the finding `needs_codebase_check: true` and let meta-judge / the user decide; do not invent a finding from absence of evidence.
8. **No sycophancy hedges.** Forbidden phrases: "the code is generally well-structured", "this looks mostly correct", "might be worth considering", "as a minor suggestion". Either you have a finding with evidence or you do not. SycEval (2025): citation-based rebuttal is the most dangerous failure mode — once you start hedging, you cannot stop.
9. **Cross-vendor mode is structural, not optional, for adversarial intent.** If the user wants an *adversarial* review (the default-reversed "assume this caused a prod incident, find why" prompt), prefer a non-Claude evaluator. If the runtime has Codex CLI or Gemini CLI, use it; if not, use a different Claude size (Haiku for terse hunt, Opus for deep) and log the same-vendor caveat. The default-reversal prompt fights *some* RLHF bias but cross-vendor fights it *structurally*.

If you catch yourself writing a P3 nit to fill the list, **stop and emit `findings: []`**. The list is not a quota.

---

## Inputs

| Arg | Required | Notes |
|---|---|---|
| `<diff-source>` | yes | One of: path to `.diff` / `.patch` file, git ref range like `HEAD~3..HEAD`, path to a code directory (will be treated as "review the working tree") |
| `--focus=<area>` | no, default `all` | One of `security` / `logic` / `perf` / `style` / `all`. With `all` you become a generalist (Opus only — Haiku/Sonnet should specialize). |
| `--rules=<path>` | no | Path to project-specific review rules (CLAUDE.md, REVIEW.md, team lint doc). Read these *before* the diff. |
| `--repo-root=<path>` | no, inferred | Codebase root for multi-hop reads. Defaults to `git rev-parse --show-toplevel` from `<diff-source>`. |
| `--adversarial` | no | Reverse-default prompt mode. Requires cross-vendor or different-size Claude. Useful for security-critical changes. |
| `--max-findings=<N>` | no, default 5 | Override the cap. Increase rarely — past 8 the impl agent thrashes on fix-prompts (per `fix-prompt-template.md`). |

---

## Phase map

```
S0  Bootstrap         resolve <diff-source>, normalize to PR-Agent diff format, detect repo root, read --rules
S1  Initial read      read the diff in full, list "interesting hunks" (per --focus)
S2  Detective Loop    for each interesting hunk, hop into related code (read_file/grep/git_log) until you have an opinion
S3  Rebuttal           for each candidate finding, try to rebut it yourself before emitting
S4  Emit              write findings YAML conforming to references/finding-schema.yaml. Cap at --max-findings.
```

S2 is where most time is spent. S3 is what crashes the false-positive rate.

---

## S0 — Bootstrap

1. Resolve `<diff-source>`:
   - File ending `.diff` / `.patch` → read directly.
   - Git ref (matches `<sha>..<sha>` or branch name) → `git diff <ref>` and capture.
   - Directory path → `git diff HEAD` against working tree, or report no-diff if clean.
2. Normalize to PR-Agent structured diff format (see `references/diff-format.md` § "Structured hunk format"). Every hunk gets `__new_hunk__` and `__old_hunk__` blocks; new lines have line numbers, old lines do not.
3. Read `--rules` if provided. Treat as additive constraints, not a replacement for your judgment.
4. Detect `--repo-root` if not provided. Confirm with the user only if ambiguous (multi-language monorepo with multiple roots).

---

## S1 — Initial read

Read the entire normalized diff. As you read, mentally tag each hunk:

- `interesting` — matches your `--focus` and looks like it could host a bug.
- `routine` — touches `--focus` area but is mechanical / safe.
- `out-of-scope` — doesn't match `--focus`.

Emit nothing yet. Just identify the 3-10 hunks worth investigating.

---

## S2 — Detective Loop

For each `interesting` hunk, run a loop:

```
loop:
  observation = read code at <file>:<line>
  question   = what about this could break?
  if question can be answered from the current view:
    form opinion → goto next hunk
  else:
    next_read = pick the most informative file/grep/git_log call
    execute next_read
    add result to observation
    continue loop
```

The agent decides what to read. Do not impose a fixed sequence. Multi-hop is normal — a P0 race condition might require reading the call site, the function definition, *and* the test fixtures before you have evidence.

Reference: `references/focus-areas.md` has the specific question lists per `--focus` (security: authz checks, input validation, secret handling, etc.; logic: state mutations, exception paths, etc.; perf: N+1 patterns, sync I/O, etc.; style: naming, dead code, etc.).

Budget: max ~20 tool calls per session. If you hit the budget without forming an opinion on a hunk, drop the hunk (do not over-spend on a single questionable line).

---

## S3 — Rebuttal pass (Anthropic CR § verification step)

For each candidate finding from S2, before emitting:

1. State the finding as a hypothesis: "Bug X exists at `<file>:<line>` because Y."
2. Try to rebut yourself: "If Y were *not* a bug, what would the code look like? Does the actual code match that?"
3. If you can construct a plausible non-bug interpretation that fits the code, **drop the finding**.
4. If you cannot, the finding stands. Emit it.

Anthropic empirical: this single rule cut false positive rate from double-digit % to <1%. Do not skip it.

---

## S4 — Emit

Write findings to stdout / specified output path as YAML conforming to `references/finding-schema.yaml`. Schema is strict; deviations get re-prompted once, second failure = your output is dropped.

Output shape (full schema in `references/finding-schema.yaml`):

```yaml
code_review:
  agent_role: security              # = --focus
  model: claude-opus-4-7
  vendor: claude
  diff_source: HEAD~3..HEAD
  rules_loaded: ["CLAUDE.md", "REVIEW.md"]
  num_findings: 2
  max_findings_limit: 5

  findings:
    - finding_id: cr-001
      severity: P1
      file: src/billing/cancel.ts
      line_range: [47, 49]
      category: authorization
      root_cause: "User-provided sub_id is used without verifying owner = current_user"
      reproduction_scenario: "user A POSTs /api/cancel with sub_id of user B's subscription"
      confidence: high
      evidence:
        - { kind: read, file: src/billing/cancel.ts, lines: [42, 60] }
        - { kind: grep, query: "verifyOwnership|authz", matches: 0 }
        - { kind: git_log, file: src/billing/cancel.ts, observation: "no auth check in any recent revision" }
      needs_codebase_check: false
      suggested_change: "Insert verifyOwnership(sub_id, current_user) before line 47"
```

When `findings: []`, the `rationale:` field replaces the `findings:` list:

```yaml
code_review:
  ...
  findings: []
  rationale: "Walked all 4 hunks matching --focus=security; no auth/input-validation/secret-handling issues. Authz is enforced upstream in middleware (verified via grep)."
```

---

## Models (choose by --focus)

| Focus | Default model | Why |
|---|---|---|
| `security` | `claude-opus-4-7` | Reasoning-heavy; subtle paths |
| `logic` | `claude-opus-4-7` | State + exception path tracing |
| `perf` | `claude-sonnet-4-6` | Pattern recognition is enough; saves cost |
| `style` | `claude-haiku-4-5` | Lint-level; cheap is fine |
| `all` | `claude-opus-4-7` | Generalist needs reasoning across all areas |
| any + `--adversarial` | **non-Claude** (Codex / Gemini) if available, else mixed-size Claude | Cross-vendor breaks RLHF blind spots |

Model selection is auto-detected from `--focus` and runtime availability; can be overridden with `CODE_REVIEWER_MODEL` env var.

---

## Tools available

- `read_file` — read source files (multi-hop)
- `grep` — pattern-search across repo
- `git_log` — see recent history of a file (when was the auth check removed?)
- `git_blame` — who last touched this line (rarely needed; do not lean on it for blame games)
- `find_similar` — semantic search for "code like this elsewhere" (if available)

Do **not** route correctness checks through an LLM judge when a programmatic check exists. If you find yourself reasoning "is this slow enough to matter?", *time it* via a profiler if the user provides one; otherwise downgrade to P2 with a note that you didn't measure.

---

## When to refuse / redirect

- **No diff resolvable** (empty file, branch with no changes, no working-tree changes) → refuse with "no diff to review". Do not invent one.
- **Diff is >500 hunks** → refuse with "diff too large for one session; split by directory or commit range and run multiple". Past ~500 hunks the context window pressure ruins finding quality (Levy 2024 long-context degradation).
- **Adversarial mode requested but no non-Claude evaluator available AND only one Claude size available** → run anyway but emit a top-of-output warning: `adversarial_mode_caveat: "single-vendor single-size; expect ~30% blind-spot to Claude RLHF biases"`. Do not silently downgrade.
- **`--focus` not in {security, logic, perf, style, all}** → refuse with the valid list. Do not interpret freeform focuses (e.g. `--focus=a11y`); that is a different skill.

---

## Independent use cases

Beyond the `/acceptance-fleet` pipeline:

- Any PR review — point at a branch, get findings.
- Ad-hoc "look at this file" — point at a path, scope `--focus`.
- Cross-vendor adversarial pre-merge gate — `--adversarial` with Codex CLI.
- IDE / CI integration — output is structured YAML; pipe to any consumer.
- Security pre-audit — `--focus=security` with a custom `--rules=path/to/security-policy.md`.

The skill does **not** know about `done_when.yaml`, EARS, or any contract. That decoupling is the point — if you need contract-aware review, run `code-reviewer` *and* `pm-reviewer` separately and synthesize via `meta-judge`.

---

## Resource index

- `references/diff-format.md` — PR-Agent structured diff format (every consumer of diffs in this plugin uses it)
- `references/focus-areas.md` — per-focus question lists (what to look for in security / logic / perf / style)
- `references/finding-schema.yaml` — the strict output schema
