# Claude Code Forge - 项目规范

这是 Claude Code 插件市场项目。结构：`.claude-plugin/marketplace.json` → `plugins/<name>/` → skills / agents / rules。

## 版本管理

使用语义化版本 (SemVer)。三处版本必须同步：

| 文件 | 作用 |
|------|------|
| `plugins/<name>/skills/<skill>/SKILL.md` frontmatter `version` | Skill 自身版本 |
| `plugins/<name>/.claude-plugin/plugin.json` `version` | 插件版本（源头） |
| `.claude-plugin/marketplace.json` 对应插件的 `version` | 市场注册表（与 plugin.json 同步） |

### 什么时候 bump

| 变更类型 | Skill 版本 | Plugin 版本 | 示例 |
|---------|-----------|------------|------|
| 修复 typo / 格式调整 | patch (+0.0.1) | patch (+0.0.1) | 1.0.0 → 1.0.1 |
| 功能增强 / 流程变更 | minor (+0.1.0) | minor (+0.1.0) | 1.0.0 → 1.1.0 |
| 不兼容变更 / 重大重构 | major (+1.0.0) | major (+1.0.0) | 1.0.0 → 2.0.0 |
| 新增 skill / agent | — | minor (+0.1.0) | 1.1.0 → 1.2.0 |

### 修改文件后的同步清单

修改 skill 内容时，必须同时更新：
1. 该 skill 的 `SKILL.md` frontmatter `version`
2. `plugins/<name>/.claude-plugin/plugin.json` 的 `version`
3. `.claude-plugin/marketplace.json` 中对应插件的 `version`

新增 skill / agent 时，更新第 2、3 项。

### 新建插件（plugin）的额外步骤

新增**整个 plugin**（不是给已存在 plugin 加 skill/agent）时，除上面三处外还要做：

4. **本机启用**：在 `~/.claude/settings.json` 的 `enabledPlugins` 字典加一条：
   ```json
   "enabledPlugins": {
     "<plugin-name>@claude-code-forge": true
   }
   ```
5. **重启 Claude Code 会话**——`Skill` 工具的可用列表在 session 启动时定型，运行中改 `settings.json` 不会热加载。

第 4-5 步是**用户级、不入 git** 的本机配置，但它决定了你能不能调用新 plugin 的 skill。漏了它就会得到 `Unknown skill` 报错，且本会话无法补救（必须新开 session）。

> 历史 bug：`bespoke-design-system` v1.8.0 完整注册到 `marketplace.json` 但漏了 `enabledPlugins`，导致用户调 `/bespoke-design-system` 时 Skill 工具找不到。详见 `~/.claude/projects/.../memory/feedback_plugin_enable_required.md`。

## Commit 规范

遵循 Conventional Commits：

- `feat:` 新功能（新 skill / agent）
- `fix:` 修复
- `refactor:` 重构
- `docs:` 文档
- `chore:` 维护（版本 bump、配置变更）

版本 bump 单独提交：`chore: bump <plugin> to v<version> with <description>`

## 项目结构

```
claude-code-forge/
├── .claude-plugin/marketplace.json   # 市场注册表
├── plugins/
│   └── <plugin-name>/
│       ├── .claude-plugin/plugin.json  # 插件清单
│       ├── agents/                     # Agent 定义 (*.md)
│       ├── skills/                     # Skill 定义 (<name>/SKILL.md)，也作为斜杠命令入口
│       ├── rules/                      # 约束规则 (*.md)
│       ├── hooks/hooks.json            # 事件钩子
│       └── docs/                       # 阶段文档
├── CONTRIBUTING.md
└── README.md
```

Agents、skills、rules、hooks 从目录自动发现，不需要在 plugin.json 中列举。
Skill 的 `name` 字段决定斜杠命令名（如 `name: forge-teams` → `/forge-teams`）。

---

## 生成 DESIGN.md 的执行策略（在本仓库下默认跑源码）

**触发**：用户在本仓库下要求"生成 design"、"做调性方案"、"DESIGN.md"、"设计系统"、"调性"、"UI 风格"，目标是产出**视觉/调性**层面的设计系统（不是技术架构文档）。

### 默认路径：直接跑源码，不要调 Skill 工具

这个仓库**就是** `bespoke-design-system` skill 的开发地。skill 是这份源码实现的，所以"调 skill"和"跑源码"逻辑等价——但跑源码有三个本仓库专属优势：

1. **每一步可见**：B0-B6 状态、规则库健康度、闸门 verdict 都直接在主对话里看到，便于排查
2. **dogfooding 检验代码**：每次生成都顺带验证 `tools/*.py`、`checks/*.py`、prompts 文档的真实可用性，发现一个 skill 源码问题立刻记
3. **不受 plugin cache / enabledPlugins 部署状态影响**：那是 Claude Code 内部行为，跟"代码本身工作不工作"无关

所以**不要先判断 skill 是否在可用列表**——在本仓库下，无论 Skill 工具状态如何，一律走下面的源码流程。

流程：

```bash
# skill 源码位置
SKILL_DIR=plugins/bespoke-design-system/skills/bespoke-design-system

# 必读
$SKILL_DIR/SKILL.md                    # 这是 spec，B0-B6 全流程
$SKILL_DIR/grammar/meta/defaults.yaml  # auto 模式的 product_category 默认推断
$SKILL_DIR/references/anti-slop-blacklist.md   # B4 生成时主动避开的 pattern
$SKILL_DIR/references/design-md-spec.md        # 9-section 输出格式（Dialect A/B）
$SKILL_DIR/agents/rationale-judge.md   # B5 的对抗式审查方角色定义
```

**严格按 SKILL.md 的 B0-B6 步骤跑，不要重新发明流程**：

| 阶段 | 关键产物 | 工具 |
|------|---------|------|
| B0 | 报 Mode + 规则库健康度（N rules / M extracted_systems / K registered） | `tools/check_state.py` + 自己读 `grammar/rules/*.yaml` |
| B1b | auto 模式画像（含 inferred_fields 标注） | 读 `grammar/meta/defaults.yaml` |
| B2 | `_b2-candidates.json`（顶层字段名 `candidate_rules`） | 自己写 archetype/kansei filter |
| B3 | `_b3-self-consistent.json` | `tools/b3_resolve.py --b2 <file> --output <file_path>` |
| B4 | `DESIGN.md` + `provenance.yaml`（每个决策三段式） | 自己写，严格不创造新规则；可拒绝 B3 自洽集中 archetype-mismatch 规则但需写 `rejected_alternative_<id>` |
| B5 | 5 项 P0 闸门并行 | 见下表 |
| B6 | `negotiation-summary.md` + 自演化 stats 更新 | 自己写 |

**B5 的 5 项闸门必须全跑**：

| Check | 命令 | 通过条件 |
|-------|-----|---------|
| coherence | `python3 checks/coherence_check.py <tokens.json>` | score ≥ 0.55, 0 blocker |
| archetype | `python3 checks/archetype_check.py <tokens.json> --primary <X> --secondary <Y>` | primary 0 blocker |
| kansei_coverage | `python3 checks/kansei_coverage_check.py --profile <yaml> --provenance <yaml>` | coverage ≥ 0.8, 0 reverse violation |
| neighbor | `python3 checks/neighbor_check.py <tokens.json>` | distance < 0.3 |
| **rationale-judge** | `Agent(subagent_type="general-purpose", prompt=<完整 rationale-judge.md 角色 + provenance/DESIGN.md/tokens 路径 + grammar/rules 核验源>)` | round 1-2 verdict = pass |

`rationale-judge` 必须用 Agent 工具显式隔离上下文调用，不能在主对话里自评——**这是闸门有效性的关键**。本次实测发现 round 1 抓到了真实 blocker（Linear elevation 规则 +0.02 vs +0.04 误述），是装饰不出来的对抗式审查价值。

闸门 verdict = `needs_revision` 时**自动跑 round 2 修订**（限 2 轮），不要打扰用户。两轮还过不了才输出"持续失败"+ issues 列表。

### 产物路径

默认输出到 `<brief 同目录>/bespoke-design/<slug>/`：

```
<output_dir>/
├── DESIGN.md
├── provenance.yaml          # 含 b5_gate_results 块
├── negotiation-summary.md   # auto 模式必含 inferred_fields 清单
└── tokens.json              # 供 B5 checks 用
```

如 brief 是用户发来的字符串而非文件，用 `~/Documents/Downloads/bespoke-design/<slug>/` 兜底。

### 记录 skill 源码问题（dogfooding 的关键产出）

跑 B0-B6 时遇到的任何 skill 源码异常（schema 不一致、docstring 与代码不符、check 崩溃、流程模糊）记到：

```
bespoke-design/skill-issue-<YYYY-MM-DD>.md
```

格式至少包含：问题清单表、根因定位、修复建议、本次是否影响产物质量。
**不要**等到结束再写——发现一个写一个，避免遗漏。

历史 issue 见仓库根的 `bespoke-design/skill-issue-2026-05-05.md`，**修代码前先看这份**，避免重复发现已知问题。

### 最终告知用户的话

不要长篇大论。说三件事：

1. 5 项 P0 闸门是 pass 还是 needs_revision（连同关键数据，如 neighbor distance、kansei coverage rate）
2. 产物路径 + 三份/四份文件清单
3. 提醒 SKILL.md 铁律 3：**5/5 通过 ≠ 这份 DESIGN.md 有品味**，最终品味关必须由人完成（这一句是 SKILL.md 强制项，不要省）。

> 历史:2026-05-05 首次走完整源码流程为 OPC 工作台生成 DESIGN.md，dogfooding 顺带发现 1 个部署 blocker + 5 个源码 bug，已修复至 v1.9.1。详见 `bespoke-design/skill-issue-2026-05-05.md`。
