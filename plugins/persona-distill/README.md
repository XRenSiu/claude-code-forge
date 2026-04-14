# persona-distill

> A parameterized schema library + generation/evaluation/scheduling/debate toolkit for distilling personas into self-contained Claude Code skills.

`persona-distill` is a plugin for [Claude Code](https://claude.com/claude-code) that gives you five cooperating skills for the full persona-distillation lifecycle:

- **Creation** — turn corpus (chat history, interviews, writings) into a self-contained persona skill
- **Evaluation** — quantify skill quality with a 12-dimension rubric + density scoring
- **Collection** — unify multi-modal corpus ingestion (scaffolding-only in v1)
- **Scheduling** — pick the right persona skill from your library for a given question
- **Debate** — orchestrate 2-5 persona skills around a single question

Built on a parameterized **schema × components** design: 9 persona schemas (covering self / collaborator / mentor / loved-one / friend / public-mirror / public-domain / topic / executor) assembled from 18 reusable components.

## The 5 skills

| Skill | Role | Trigger examples |
|-------|------|------------------|
| [`distill-meta`](./skills/distill-meta/SKILL.md) | Main orchestrator. 7-phase workflow: intent clarification → schema decision → corpus collection → review → extraction → iterative deepening → assembly → validation → delivery. | "蒸馏乔布斯", "build a persona skill for 张三", "distill my own communication style" |
| [`persona-judge`](./skills/persona-judge/SKILL.md) | Quality evaluator. 12-dimension rubric (raw /110, pass ≥ 82), 3 live tests (Known / Edge / Voice), density scoring (density < 3.0 forces FAIL). Auto-invoked by `distill-meta` Phase 4; also runnable standalone. | "evaluate my naval-skill", "评估 steve-jobs-mirror 的质量" |
| [`distill-collector`](./skills/distill-collector/SKILL.md) **`(v1: scaffolding-only; bring-your-own parser)`** | Multi-modal corpus collector. **Scaffolding-only in v1**: specifies CLI + parser contracts + third-party tool pointers; does not ship runnable parsers for platform-specific exports or Whisper/yt-dlp. | "import wechat chat history", "transcribe this interview" |
| [`persona-router`](./skills/persona-router/SKILL.md) | Cross-persona scheduler. Reads all installed persona skills' `manifest.json`, scores them on schema relevance + domain overlap + component coverage + density + primary-source ratio. Recommends top 1-3. | "which persona should I ask about this architecture decision", "推荐 persona for this question" |
| [`persona-debate`](./skills/persona-debate/SKILL.md) | Multi-persona debate orchestrator. 3 modes (round-robin / position-based / free-form); moderator agent coordinates 2-5 personas and emits a synthesis transcript. | "debate this with Jobs and Munger", "let multiple personas argue about X" |

## Quick start

```bash
# Install the plugin
/plugin marketplace add XRenSiu/claude-code-forge
/plugin install persona-distill@claude-code-forge

# Distill a persona
"蒸馏乔布斯作为产品设计 mentor"   # or /distill-meta lead your input

# Evaluate quality
"评估我生成的 steve-jobs-mirror skill"

# Ask multiple personas (when you have several installed)
"用 persona-router 帮我选合适的 persona 来讨论这个架构问题"
```

> **How this plugin actually runs**: `persona-distill` is **spec-driven** — Claude executes the 7-phase workflow by reading these reference files at runtime. **No Python or Node runtime ships with v0.1.0**. Generated persona skills are plain Markdown + JSON, self-contained and movable. For an end-to-end verification recipe (generate → evaluate → route → debate), see [`docs/integration.md §7`](./docs/integration.md#7-how-to-verify-v1-end-to-end-recommended-first-test).

## Design

- **Schema-first**: 9 schemas parameterize how components are combined — you pick one, you don't hand-assemble.
- **Self-contained output**: every generated persona skill is copyable / independent of `distill-meta`. No runtime dependency on this plugin.
- **Contracts-first**: `contracts/manifest.schema.json`, `contracts/validation-report.schema.md`, `contracts/component-contract.md` are the 3 authoritative interfaces across the 5 skills. Any change here is a breaking change to all consumers.
- **Cheat-resistant rubric**: `persona-judge` includes anti-gaming heuristics (padded tensions, boilerplate boundaries, Known-Test leakage, density inflation, primary-source mislabel, voice-without-substance, component theater, threshold arbitrage).
- **Honest limitations**: all 9 schemas ship with `unvalidated: true` in v1 (no dog-food persona has been generated yet). Several components are re-derived from README fragments of reference libraries we could not clone; marked `[UNVERIFIED-FROM-README]` throughout.

## Key contracts

| Contract | Purpose |
|----------|---------|
| [`contracts/manifest.schema.json`](./contracts/manifest.schema.json) | Shape of every produced persona skill's `manifest.json`. Consumed by persona-judge, persona-router, persona-debate. |
| [`contracts/validation-report.schema.md`](./contracts/validation-report.schema.md) | Output format persona-judge emits and `distill-meta` Phase 4 gate reads. |
| [`contracts/component-contract.md`](./contracts/component-contract.md) | Interface every one of the 18 shared components conforms to. |

## Status

**v0.1.0** — Initial release. 5 skills, 9 schemas, 18 components, 12-dimension rubric.

Known limitations (see [`docs/integration.md`](./docs/integration.md) for the full list):

- No dog-food persona yet generated — schemas carry `unvalidated: true`.
- `distill-collector` is spec-only; runtime parsing relies on third-party tools users install themselves.
- Reference libraries (nuwa-skill / colleague-skill / anti-distill / immortal-skill / etc.) were not clonable; components re-derived from README fragments quoted in the master plan.
- `persona-router` discovery is environment-dependent; actual filesystem scan paths differ across Claude Code installs.
- Phase 2.5 iterative deepening ships as single-pass scanner; multi-round convergence is a v2 TODO.

## Structure

```
persona-distill/
├── .claude-plugin/plugin.json
├── contracts/
│   ├── manifest.schema.json            # the cross-skill JSON Schema
│   ├── validation-report.schema.md     # persona-judge output contract
│   └── component-contract.md           # 18-component interface contract
├── skills/
│   ├── distill-meta/                   # main orchestrator
│   ├── persona-judge/                  # 12-dim evaluator
│   ├── distill-collector/              # multi-modal (scaffolding)
│   ├── persona-router/                 # cross-persona scheduler
│   └── persona-debate/                 # multi-persona debate
├── docs/
│   └── integration.md                  # how the 5 skills wire together
├── LICENSE
└── README.md
```

## License

MIT. See [LICENSE](./LICENSE).

## Credits

Design synthesizes patterns from (borrowed, marked `[UNVERIFIED-FROM-README]` where we could only read README fragments):

- [alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill) — cognitive-OS, triple-validation, seven-axis DNA
- [titanwings/colleague-skill](https://github.com/titanwings/colleague-skill) — work + persona two-part architecture, correction layer
- [notdog1998/yourself-skill](https://github.com/notdog1998/yourself-skill) — self-memory component
- [leilei926524-tech/anti-distill](https://github.com/leilei926524-tech/anti-distill) — density classifier (reversed for positive scoring)
- [agenmod/immortal-skill](https://github.com/agenmod/immortal-skill) — unified CLI, conflicts.md
- [titanwings/ex-skill](https://github.com/titanwings/ex-skill), [perkfly/ex-skill](https://github.com/perkfly/ex-skill) — 6-layer persona for loved-one schema
- [jinchenma94/bazi-skill](https://github.com/jinchenma94/bazi-skill) — Python computation layer + interpretation layer separation
- [softaworks/agent-toolkit/skill-judge](https://github.com/softaworks/agent-toolkit) — 8-dimension skill rubric core
- cyber-figures — iterative deepening concept
- midas.skill — N-dimensional framework pattern (public-domain schema)
- 图鉴.skill, 诸子.skill — router + debate conceptual blueprints (URLs unresolved)
