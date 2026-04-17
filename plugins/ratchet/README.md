# ratchet

> Goal-driven master/subagent autonomous loop. Define the finish line, let independent evaluation kill-and-restart workers until they cross it — or the budget runs out.

**v1.0.0** · MIT · Combines [Goal-Driven](https://github.com/disler/goal-driven-framework) master/subagent separation with [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) signal-design discipline.

---

## What it does

Long-running agent loops fail in two ways: the worker silently stalls, or the worker optimizes against its *own* evaluation (reward hacking). Ratchet fixes both by enforcing a strict separation — **the master only judges, the subagent only executes** — and by treating stalled / misaligned workers as disposable.

A session goes:

1. **Clarify the goal.** Goal / Criteria / Scope — three questions, only asked when ambiguous.
2. **Design acceptance criteria.** Property-based (round-trip / invariant / idempotent / metamorphic / model-based oracle), priority-ranked P0 / P1 / P2, anti-cheat clauses, milestone ordering.
3. **Generate `ratchet.md`.** A frozen experiment protocol with its own `evaluate.sh` (Mode A) or `evaluate_criteria.md` (Mode B) + frozen `test_data/`.
4. **Run the master loop.** Worker executes → commits → master evaluates in isolation → `best-r{N}` tag on gain, restart on stale/cheating. Three termination exits defined up front: `done_when.success` / `done_when.convergence` / `done_when.budget`.
5. **Deliver.** Checkout the best tag, write a report (Top-5 effective changes, Top-5 failed hypotheses, remaining gaps).

## Install

This plugin lives in the [claude-code-forge](https://github.com/XRenSiu/claude-code-forge) marketplace. After adding the marketplace, the skill is auto-discovered and triggered by phrases like:

- "ratchet"
- "棘轮优化" / "目标驱动"
- "帮我持续优化 X 直到达标"
- "帮我实现一个 X 并且要通过 Y 验证"
- "自动跑到达标为止"

## How a session goes

```
You:  用 ratchet 把这个 lexer 优化到差分测试 100% 通过

Ratchet:
  Step 1 — Goal: lexer 与参考实现 token stream 完全一致
           Scope: CAN lexer/*.py  ·  CANNOT reference/, tests/, evaluate.sh
  Step 2 — Criteria:
           P0: differential_pass_rate == 1.0 over 500 fuzz inputs
           P0: round_trip(tokenize(s)).detokenize == s  (∀ s ∈ corpus)
           P1: median latency ≤ 1.3× reference
           done_when.budget = 20 rounds, convergence = 4 stale rounds
  Step 3 — Generated ratchet.md + evaluate.sh + test_data/fuzz_500.json (frozen)
  Step 4 — Master loop
           r1: score 0.62  → best-r1
           r2: score 0.78  → best-r2
           r3: score 0.78  (stale 1/4)
           r4: worker claimed success; independent eval says 0.78 → kill, restart
           r5: score 0.91  → best-r5
           ...
           r9: score 1.00 — P0 green → success exit
  Step 5 — Report written  ·  git checkout best-r9
```

## What's inside

```
plugins/ratchet/
├── .claude-plugin/plugin.json
├── README.md
└── skills/ratchet/
    ├── SKILL.md                        # 5-step orchestrator contract + loop logic
    └── references/
        ├── ratchet-template.md         # ratchet.md skeleton (experiment protocol)
        ├── criteria-guide.md           # property-based criteria design methodology
        └── examples/
            ├── example-compiler.md     # compiler / interpreter (differential + fuzz)
            ├── example-api-service.md  # web API / service (schema + property-based)
            └── example-optimization.md # perf / quality (hard metrics + reverse constraints)
```

## When to reach for Ratchet vs. the alternatives

| Situation | Use |
|-----------|-----|
| Long-running task with a machine-verifiable finish line | **Ratchet** |
| Single `SKILL.md` you want to push from ~60 → 90+ | `skill-evolve` |
| Complete feature from idea to production (single agent) | `pdforge` |
| Same as above, but with adversarial multi-agent debate | `forge-teams` |
| Known bug, multiple plausible root causes | `forge-teams /forge-fix` or `adversarial-debugger` |

## Core principles (from SKILL.md)

- **Criteria is everything.** Can't write machine-verifiable criteria? Don't start the loop.
- **Judge and worker never share context.** Mode A: frozen `evaluate.sh`. Mode B: independent judge subagent with its own prompt.
- **Processes are disposable.** State lives in `results.tsv`, git tags, and the filesystem — not in the worker's context.
- **Anti-cheat is a design feature.** Frozen evaluation files, frozen test data, inoculation prompt in the worker instructions.
- **Three explicit exits.** Success, convergence, budget — all must have numbers before starting.

## License

MIT. See repository root [LICENSE](https://github.com/XRenSiu/claude-code-forge/blob/main/LICENSE).
