# skill-evolve

> Darwin-style autonomous SKILL.md optimizer. Take any Claude Code skill from "1" to "100" via 8-dimension rubric + ratchet hill-climbing.

**v0.1.0** · MIT · Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) and [alchaincyf/darwin-skill](https://github.com/alchaincyf/darwin-skill).

---

## What it does

Most SKILL.md files stop at "it runs". The gap between "runs" and "actually good" is ~30 points on a 100-point rubric: vague triggers, unclear steps, undefined boundaries, no checkpoints. Hand-tuning is expensive and you can't tell if a change made things worse.

`skill-evolve` automates that gap:

- **8-dimension rubric** (60 structural + 40 effectiveness) tells you exactly which dimension is weakest
- **Independent subagent scoring** so the model that *changes* the skill is not the one that *grades* it
- **Git-backed ratchet** — every round either commits the improvement or `git checkout`s it away. Scores only go up.

## Install

This plugin lives in the [claude-code-forge](https://github.com/XRenSiu/claude-code-forge) marketplace. After adding the marketplace, the skill is auto-discovered and triggered by phrases like:

- "优化这个 skill"
- "evolve this skill"
- "skill-evolve"
- "improve skill quality"
- "darwin"

## How a session goes

```
You:  evolve plugins/foo/skills/bar/

Skill-evolve:
  Phase 0 — baseline: 62/100 (weakest: boundary_handling = 4)
  Phase 1 — Round 1: hypothesis "add 3 failure modes to §Boundary"
            re-eval: 67/100 (+5)  → KEEP  commit: a3f1c2
           Round 2: hypothesis "tighten Triggers list with 4 colloquials"
            re-eval: 65/100 (-2)  → REVERT
           Round 3: hypothesis "split monolithic step list into Phase 0/1/2"
            re-eval: 71/100 (+4)  → KEEP  commit: 8b21d4
           ...
  Phase 2 — final: 91/100  (KEEP×9, REVERT×4, SKIP×0)

  → final-report.md written
  → 9 evolve commits in git history
```

## What's inside

```
plugins/skill-evolve/
├── .claude-plugin/plugin.json
├── README.md
└── skills/skill-evolve/
    ├── SKILL.md                      # main loop + Phase 0/1/2 contract
    ├── references/
    │   ├── rubric.md                 # 8-dim scoring detail + JSON schema
    │   ├── ratchet-protocol.md       # git workflow + decision table
    │   ├── test-protocol.md          # subagent eval prompt template
    │   └── design-rationale.md       # why this design, what it's not
    └── templates/
        ├── baseline.md.tmpl
        ├── experiments.tsv.tmpl
        └── final-report.md.tmpl
```

## What it is *not*

- **Not a skill generator** — use `persona-distill` / nuwa for 0→1
- **Not a one-shot quality scorer** — use `persona-judge` if you only need a single rating
- **Not a batch optimizer** (yet) — MVP optimizes one skill at a time

See `references/design-rationale.md` for the full non-goals list.

## Acknowledgments

- **Andrej Karpathy** — autoresearch范式（modify → eval → keep/revert）
- **alchaincyf / 花叔** — darwin-skill 把范式迁移到 SKILL.md 优化领域，本插件直接借鉴其 8 维 rubric 设计与独立 subagent 评分机制
- **Anthropic skill-creator** — 60/40 train/test split 思想（v0.2 计划集成）

## License

MIT. See repository root [LICENSE](https://github.com/XRenSiu/claude-code-forge/blob/main/LICENSE).
