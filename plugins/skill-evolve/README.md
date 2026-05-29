# skill-evolve

> Darwin-style autonomous SKILL.md optimizer. Take any Claude Code skill from "1" to "100" via a 9-dimension rubric + no-skill baseline comparison + ratchet hill-climbing.

**v0.2.0** · MIT · Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch), [alchaincyf/darwin-skill](https://github.com/alchaincyf/darwin-skill), and Microsoft **SkillLens** (arXiv 2605.23899) / **SkillOpt** (arXiv 2605.23904).

---

## What it does

Most SKILL.md files stop at "it runs". The gap between "runs" and "actually good" is ~30 points on a 100-point rubric: vague triggers, unclear steps, undefined boundaries, no checkpoints. Hand-tuning is expensive and you can't tell if a change made things worse.

`skill-evolve` automates that gap:

- **9-dimension rubric** (60 structural + 40 effectiveness) tells you exactly which dimension is weakest — structure now elevates the three SkillLens-validated high-signal dimensions (failure-mechanism encoding / executable specificity / high-risk-action blacklist) that lift pairwise judge accuracy 46.4%→73.8%
- **Default multi-judge independent scoring** so the model that *changes* the skill is not the one that *grades* it — and a single judge (the 46.4% coin-flip case) is never the last word
- **No-skill baseline comparison** every round — a skill that makes the agent *worse* than no skill (negative transfer, ~25% of skills per SkillLens) is caught and blocked from shipping
- **SkillOpt stability controls** — rejected-edit buffer (`dead-ends.md`) + slow-update memory (`learnings.md`) + ≤30-line text learning-rate
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
    │   ├── rubric.md                 # 9-dim scoring detail + JSON schema (incl. negative_transfer)
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
- **alchaincyf / 花叔** — darwin-skill 把范式迁移到 SKILL.md 优化领域，本插件借鉴其 rubric 设计、独立 subagent 评分与 with/without-skill 实测对比
- **Microsoft SkillLens / SkillOpt** — v0.2 的三高信号维（46.4%→73.8%）、负迁移检测、多评委、拒绝缓冲/慢更新记忆/文本学习率均源自这两篇
- **Anthropic skill-creator** — 60/40 train/test split 思想

## License

MIT. See repository root [LICENSE](https://github.com/XRenSiu/claude-code-forge/blob/main/LICENSE).
