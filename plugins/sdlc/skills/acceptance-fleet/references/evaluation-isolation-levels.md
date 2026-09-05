# evaluation-isolation-levels.md — 4 levels of structural separation

The "做和判分离" principle is not satisfied by a prompt that says "you're an evaluator now". It must be structural: the implementation agent cannot read the evaluator's prompt, cannot see the evaluator's outputs from prior iterations, cannot infer the evaluator's gates from session context.

Why this matters: MD §6 lists "let the implementation agent see the evaluation prompt" as a hard-NO. Reason — evaluation method leakage = the substrate that makes gaming possible. Without isolation, every other defense in this skill is window-dressing.

Four levels, in order of increasing strength. Minimum acceptable for `/acceptance-fleet` is **medium**.

---

## Level 0: ❌ Same session (FORBIDDEN)

```
[same Claude session]
   ├─ implementation work
   └─ evaluation work
```

Implementation and evaluation in the same session. Implementation agent has full access to the evaluation prompts and prior verdicts via conversation history. Gaming is trivial: the agent literally reads what it's being graded on.

`/acceptance-fleet` MUST refuse to run in this configuration. If you cannot guarantee a fresh session for the implementation handoff, the skill refuses the run.

---

## Level 1: Weak — different prompts, same model, same session family

```
[Claude session A]                  [Claude session B]
   implementation work                 evaluation work
   (CLAUDE.md visible)                 (different system prompt)
```

Different sessions but same model, same project. The implementation agent does not directly see evaluator prompts, but:
- Both sessions read the same `CLAUDE.md`, which the project may evolve to include hints from prior runs.
- Both sessions have the same RLHF biases → same blind spots.
- "Sycophantic self-review" is structurally not prevented — Claude reviewing Claude's output reads less adversarially than Codex reviewing Claude's output.

**Useful for early prototyping only.** `/acceptance-fleet` accepts this level with a warning logged in `ratchet-log/iteration-NNN/isolation.json`.

---

## Level 2: Medium — different sizes within same vendor (MINIMUM ACCEPTABLE)

```
[Claude Opus 4.7 session]           [Claude Haiku 4.5 session]
   implementation                       test-runner, existence-checker
                                     [Claude Sonnet 4.6 session]
                                        design-reviewer
                                     [Claude Opus 4.7 session — different]
                                        requirement-tracer, edge-case-hunter,
                                        spec-gaming-detector, e2e-explorer
```

Same vendor (Claude), but evaluators use Haiku / Sonnet / Opus mix while implementation uses Opus. Capability distributions differ even though RLHF pipeline is shared.

Caveat: Opus catches things Haiku misses, but Haiku also catches things Opus misses (specifically: Opus over-confidence on near-right answers). Mix size, not just model name.

**`/acceptance-fleet` minimum acceptable level.** Sessions are still separately spawned — no shared state.

---

## Level 3: Strong — cross-vendor (RECOMMENDED)

```
[Claude Opus 4.7 session]           [Claude Opus 4.7 session]
   implementation                       requirement-tracer, edge-case-hunter,
                                        design-reviewer, e2e-explorer
                                     [Claude Haiku 4.5]
                                        test-runner, existence-checker
                                     [Codex GPT-5 OR Gemini Pro 3]
                                        adversarial-reviewer
                                     [Codex OR Gemini — different from above]
                                        spec-gaming-detector
```

At least one evaluator is non-Claude. Crucially, adversarial-reviewer and spec-gaming-detector — the two roles whose value is exactly "catch what Claude misses" — run on a different vendor.

The Milvus benchmark (MD §1.4): Claude + Gemini covered 91% of the bugs found by a 5-vendor ensemble. Single best-pair coverage. Cross-vendor catches concurrency / cloud-API / permission bugs that Claude consistently misses.

**This is what /acceptance-fleet uses by default if a cross-vendor evaluator is available.** Detection at S0:
- `which codex` succeeds → use Codex CLI as cross-vendor evaluator.
- `which gemini` succeeds → use Gemini CLI.
- Neither → fall back to medium with a logged warning.

---

## Level 4: Extreme — sandboxed evaluator (Anthropic Code Review style)

```
[Claude Opus 4.7 session]           [docker-in-docker container]
   implementation                       fresh Claude / Codex session,
                                        no access to project memory,
                                        no access to prior iteration logs,
                                        receives only the impl artifacts
                                        via stdin/files, returns findings
                                        via stdout
```

Evaluator runs in an isolated container with zero shared filesystem / memory / network access except the artifacts piped in and the findings piped out. Implementation agent literally cannot read evaluator prompts or prior verdicts even if the project's CLAUDE.md tried to leak them.

This is what Anthropic's internal code review uses. It's overkill for most projects but matters for:
- Compliance audits (ISO 26262, SOC 2, FedRAMP)
- High-blast-radius features (billing, auth, data deletion)
- Adversarial training-data generation (you need clean labels)

`/acceptance-fleet` supports this level if the runtime has Docker available. Detection: `which docker && docker info` both succeed. Performance hit is ~30s extra per iteration for container spin-up.

---

## Decision matrix

| Scenario | Recommended level | Why |
|---|---|---|
| Prototype / learning the skill | Level 1 (weak) | Get the loop working before paying for cross-vendor |
| Small team feature, low risk | Level 2 (medium) | Catches obvious issues without API key setup |
| Production PR review | Level 3 (strong) | Cross-vendor is the cost-effective sweet spot |
| Billing / auth / regulated code | Level 4 (extreme) | Worth the container overhead |

---

## How `/acceptance-fleet` chooses

At S0, the skill runs this check in order:

```python
if docker_available() and user_requested_extreme:
    isolation = "extreme"
elif codex_available() or gemini_available():
    isolation = "strong"
elif different_claude_sizes_available():
    isolation = "medium"
else:
    isolation = "weak"
    warn_user("running at weak isolation — see evaluation-isolation-levels.md")

if isolation == "level_0":
    refuse("/acceptance-fleet refuses to run in same-session mode (level 0)")
```

The chosen level is written to `ratchet-log/iteration-NNN/isolation.json`:

```json
{
  "level": "strong",
  "evaluator_assignments": {
    "test-runner": "claude-haiku-4-5",
    "existence-checker": "claude-haiku-4-5",
    "requirement-tracer": "claude-opus-4-7",
    "design-reviewer": "claude-sonnet-4-6",
    "adversarial-reviewer": "codex-gpt-5",
    "edge-case-hunter": "claude-opus-4-7",
    "e2e-explorer": "claude-opus-4-7",
    "spec-gaming-detector": "claude-opus-4-7"
  },
  "warnings": []
}
```

If the user wants to force a higher level than what the runtime supports, they should configure the missing tool (install Codex CLI, set up Docker) — `/acceptance-fleet` does NOT silently downgrade above what it detected.
