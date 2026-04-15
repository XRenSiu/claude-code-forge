---
name: distill-meta
description: >
  Persona Distillation 主编排器。根据用户输入生成一个**自包含、可独立运行**的 persona skill 产物，
  基于 9 种参数化 schema + 19 个可复用组件 + 8 阶段工作流（含迭代深化、冲突检测、CDM 执行画像提取、dog-food 验证）。
  Use when: (1) 用户请求蒸馏一个人/领域/规则体系, (2) 从聊天记录/公开资料构建 persona skill,
  (3) 想要一个可被其他 Claude Code 项目复用的人格 skill。
  Triggers: "distill 张三", "蒸馏乔布斯", "build a persona skill for X",
  "帮我做一个 xx 的 persona", "distill-meta", "persona distill"
when_to_use: |
  - 用户点名要"蒸馏/distill/clone/复刻"某个人、某位导师、某个朋友
  - 需要把聊天记录/访谈/公开资料提炼成可对话的 persona skill
  - 需要蒸馏一个"领域"（而非单人），例如"投资思维"、"产品方法论"
  - 需要蒸馏一个规则体系（八字/奇门/塔罗等，schema=executor）
  - 已有 persona skill 想迭代升级（自动走 update 分支）
  - 不要用于：单次角色扮演（用 prompt 即可）、不需要产物文件的场景
version: 0.3.0
---

# distill-meta

**把一个人（或领域/规则体系）蒸馏成一个自包含的 persona skill。**

Announce at start: "I'm using the distill-meta skill to orchestrate a 7-phase persona distillation pipeline and produce a self-contained persona skill."

> **前置条件**: 深度蒸馏会并行 spawn 多个 sub-agent（语料侦查、维度提取、张力发现、迭代深化、验证）。
> 如果启用 Agent Teams 实验功能（`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`），
> Phase 1/Phase 2/Phase 2.5 会自动切换到并行团队模式。

## Overview / 概览

distill-meta 的产物是一个**独立的 persona skill**——它可以被复制、移动、分发，**不依赖 distill-meta 自身**即可在任何 Claude Code 环境中运行。

与"一次性蒸馏 prompt"相比，distill-meta 的差异化：

| 维度 | 单次蒸馏 prompt | distill-meta |
|------|---------------|--------------|
| 对象覆盖 | 通常只针对名人/同事一种 | **9 种 schema**（self/collaborator/mentor/loved-one/friend/public-mirror/public-domain/topic/executor） |
| 结构 | 固定模板 | **参数化组件**（19 个组件按 schema 拼装） |
| 深度 | 一次产出 | **迭代深化**（最多 3 轮扫描遗漏维度） |
| 执行层 | 描述即终点 | **CDM 执行画像**（Phase 3.7 把描述编译为 8 类 Macrocognition 指令性条款） |
| 质量保证 | 无 | **dog-food 验证**（调用 persona-judge，三项测试 + 12 维 rubric + 密度评分） |
| 矛盾处理 | 抹平 | **保留并存档**到 `conflicts.md` |
| 进化 | 无 | 通过对话修正层持续校正 |

### 核心原则

1. **Self-Contained 产物**（借鉴 nuwa-skill）：每个生成的 persona skill 都是**可复制/可移动/可独立运行**的独立单元。产出目录没有对 distill-meta 的任何依赖。
2. **Progressive Disclosure**：这份 SKILL.md 只做**入口决策和编排**；深层内容在 `references/` 和 `agents/` 中，按需加载。
3. **No Interrogate**：用户只说"蒸馏张三"时自动兜底（见 §Invocation）。
4. **Preserve Tensions**：人的内在矛盾是信号不是噪音，禁止抹平。

## 8-Phase Workflow（执行流程）

完整流程源自 PRD §3.2，覆盖意图澄清 → schema 决策 → 语料采集 → 维度提取 → 迭代深化 → 组装 → 冲突检测 → 执行画像提取 → 质量验证 → 交付。

```
Phase 0    意图澄清         → 对象 + 目的 + 现有 skill 检测
Phase 0.5  Schema 决策       → 9 选 1 + 组件选定 + 立即建目录（强制 self-contained）
Phase 1    语料采集         → 私有（distill-collector）+ 公开（并行 agent 调研）
Phase 1.5  Research Review   → 覆盖率表格 + 缺口标注 + 用户确认
Phase 2    维度提取         → 并行按组件提取 + 三重验证 + 七轴 DNA + 张力识别 + 密度分类
Phase 2.5  迭代深化         → 最多 3 轮多轮扫描 + Jaccard 收敛 + 高置信度自动回填
Phase 3    Skill 组装       → SKILL.md + manifest.json + 组件文件
Phase 3.5  冲突检测         → 自动 surface 组件/语料/时期间的事实性矛盾到 conflicts.md（不 resolve）
Phase 3.7  执行画像提取（新）→ CDM 4-sweep：从 knowledge/ 事件反推 8 类 Macrocognition 指令条款
Phase 4    质量验证         → 调用 persona-judge：三项测试 + 12 维 rubric + 密度评分
Phase 5    交付与后续       → 告知路径 + 触发词 + 进化方式（debate / router）
```

### Phase 0 — Intent Clarification
- **Goal**: 识别对象 + 蒸馏目的（协作 vs 镜像）+ 检测是否已有同名 skill（更新分支 vs 新建分支）。
- **Artifact**: `intent-note.md`（临时）记录用户给的所有原始信息。
- **Fallback**: 信息不足时不盘问用户，直接走默认路径（见 Invocation）。

### Phase 0.5 — Schema Decision
- **Goal**: 选定 9 种 schema 之一，并决定组件清单。
- **Artifact**: 新 skill 目录骨架立即创建（强制 self-contained，后续 phase 全部写入该目录）。
- **See**: `references/decision-tree.md` 决策树；§Schema Selection 给出摘要。

### Phase 1 — Corpus Collection
- **Goal**: 采集私有语料（聊天记录/文档/访谈）+ 公开语料（网页/视频/播客）。
- **Agents**: `corpus-scout`（并行 3-5 个）。公开对象走 nuwa 的来源白/黑名单。
- **Artifact**: `<skill>/knowledge/` 下按组件归档的原始语料。

### Phase 1.5 — Research Review Checkpoint（借鉴 nuwa）
- **Goal**: 把"语料 × 组件"的覆盖率做成表格让用户肉眼看缺口，防止在稀薄信息上硬蒸馏。
- **Artifact**: `research-review.md`（覆盖率 + 信息矛盾 + 缺口）。
- **Downgrade**: 语料不足时减少组件、加厚 `honest-boundaries`（不造假）。

### Phase 2 — Dimension Extraction
- **Goal**: 并行按组件提取：每个组件一个 sub-agent。三重验证（思维模型）、七轴量化（表达 DNA）、张力识别、密度分类。
- **Artifact**: `<skill>/references/` 下各组件的初稿。

### Phase 2.5 — Iterative Deepening（借鉴 cyber-figures；v0.2.0 multi-round）
- **Goal**: 最多 3 轮全文扫描"上轮错过的 X"；每轮用 Jaccard > 0.8 判定收敛，高置信度候选（score ≥ 0.75 且 verdict ∈ {ACCEPT, AUTO}）自动回填到目标组件。
- **Agents**: `iterative-deepener`（多轮主控）+ `candidate-merger`（每轮 append-only 回填 + bump patch version + 写 merge log）+ 按需 spawn 3 个 ephemeral attribution-vote mini-agent。
- **Stop conditions**: Jaccard > 0.8（早停）/ status = NO_GAPS / round_index = max_rounds（强制停，附 MAX_ROUNDS_REACHED）。
- **Artifact**: 合并进对应组件文件的 `### Added in round N` 块；merge 审计记录到 `knowledge/phase25-merge-log.md`；矛盾写入 `conflicts.md`。
- **Back-compat**: 调用方传 `max_rounds = 1` 即退化为 v0.1.0 single-pass 行为。
- **See**: `references/extraction/iterative-deepening.md`、`references/extraction/convergence-detection.md`、`agents/iterative-deepener.md`、`agents/candidate-merger.md`。

### Phase 3 — Skill Assembly
- **Goal**: 按 schema 的组件清单拼装 SKILL.md、manifest.json、各组件文件、conflicts.md、trigger 说明。
- **Artifact**: 完整的 persona skill 目录（产物对 distill-meta **零依赖**）。
- **See**: `contracts/component-contract.md` 的组件 I/O 契约。

### Phase 3.5 — Conflict Detection（v0.2.0 新增，借鉴 immortal-skill）
- **Goal**: 在 Phase 3 组装完成后、Phase 4 验证之前，跨组件与跨语料自动探测**事实性矛盾**（两份来源对同一断言给出 A 与 ¬A），写入产物根目录 `conflicts.md`。与 `internal-tensions`（稳定对立极，A ∧ B 共存）严格正交——前者是不兼容事实，后者是并存两极。
- **Agent**: `conflict-detector`（单实例）。
- **Four kinds**: factual / value-shift / stated-vs-behavioral / component-self。
- **Hard rule**: 本阶段**只 surface，不 resolve**——`suggested_handling` 仅能取 `PRESERVE_BOTH` / `FLAG_FOR_USER` / `TIMEBOUND`；若用户先前手写了 `conflicts.md`，用户条目在 `## User-Appended Conflicts` 段 verbatim 保留，auto-detected 条目在 `## Auto-Detected Conflicts` 段单独归档，互不合并。
- **See**: `references/extraction/conflict-detection.md`、`agents/conflict-detector.md`。

### Phase 3.7 — Execution Profile Extraction（v0.3.0 新增，借鉴 Klein RPD + CDM）
- **Goal**: 把已蒸馏的描述性人格编译成**指令性**的"情境 → 动作"条款。在 Phase 3.5 之后、Phase 4 之前运行，从 `knowledge/` 里的**具体事件**反推 8 类 Macrocognition（Sensemaking / Decision Making / Planning / Adaptation / Problem Detection / Coordination / Managing Uncertainty / Mental Simulation）下的可执行指令。
- **Agent**: `execution-profile-extractor`（单实例，串行于 Phase 3.5 后）。
- **Protocol**: CDM 4-sweep（Incident Identification → Timeline Construction → 10-Probe Deepening → What-If Validation），每条指令可追溯到 `knowledge/` 的具体事件行号。
- **Three Red Lines**（必须零失败才能 PASS）：
  1. 自述 ≠ 行为（Ericsson/Ward）——evidence 不能全是自述。
  2. 80% 专家决策是 RPD 风格——Decision Making 段里"列表对比"句式占比不得 > 50%。
  3. 颗粒度必须是"情境-行动对"——禁用 `注重 / 倾向 / 重视 / prefer / value / focus on` 作谓语。
- **Honest boundary coupling**: Sweep 4 what-if 推不出的条目 + Knowledge Audit 8 项的 gap 项自动追加到 `components/honest-boundaries.md` 的 `## Execution Profile Gaps` 段。
- **Downgrade**: 若 `knowledge/` 的可用 decision point < 10 → 跳过本组件，`honest-boundaries` 追加"事件证据不足"声明；该 persona skill 的 manifest 设 `execution_profile_completeness: skipped`。
- **See**: `references/extraction/cdm-4sweep.md`、`references/components/execution-profile.md`、`agents/execution-profile-extractor.md`。

### Phase 4 — Quality Validation（dog-food）
- **Goal**: 调用 `persona-judge` 跑三项测试（已知 / 边界 / 声音）+ 12 维 rubric + 密度评分。
- **Artifact**: `<skill>/validation-report.md`（schema 见 `contracts/validation-report.schema.md`）。
- **Gate**: 不通过回到 Phase 2；通过则进入 Phase 5。

### Phase 5 — Delivery & Next Steps
- **Goal**: 告诉用户产物路径、触发词、如何对话修正、建议下一步（`persona-debate` 对比 / `persona-router` 智能调度）。
- **Artifact**: delivery 摘要直接回用户。

## Schema Selection（Phase 0.5 决策树）

完整决策树（是人还是规则 → 有无私有语料 → 关系类型）见 **`references/decision-tree.md`**。
摘要：

```
规则体系 → executor
人 + 公开 → public-mirror (视角) / public-domain (方法论) / topic (领域)
人 + 私有 + 自己 → self
人 + 私有 + 工作关系 → collaborator / mentor
人 + 私有 + 亲密关系 → loved-one / friend
```

**Fallback rule**（借鉴 nuwa "don't interrogate"）：用户只说"蒸馏张三"不给任何信息时，默认
`schema = collaborator + 全组件 + 后续通过对话补充`。

## 9 Schemas（一览）

| # | Schema | 对象 | 详细定义 |
|---|--------|------|---------|
| 1 | `self` | 自己 | `references/schemas/self.md` |
| 2 | `collaborator` | 同事/下属/合作者 | `references/schemas/collaborator.md` |
| 3 | `mentor` | 老板/导师/前辈 | `references/schemas/mentor.md` |
| 4 | `loved-one` | 家人/伴侣/前任 | `references/schemas/loved-one.md` |
| 5 | `friend` | 朋友（轻量 loved-one） | `references/schemas/friend.md` |
| 6 | `public-mirror` | 思想家/KOL（给视角） | `references/schemas/public-mirror.md` |
| 7 | `public-domain` | 领域专家（给方法论） | `references/schemas/public-domain.md` |
| 8 | `topic` | 领域而非单人 | `references/schemas/topic.md` |
| 9 | `executor` | 规则体系（八字/奇门/塔罗等） | `references/schemas/executor.md` |

> ⚠️ **Unvalidated schemas**：PRD §10 自述——9 种 schema **尚未经过实际蒸馏验证**。
> 初始版本中所有 schema 在生成 manifest 时会带上 `unvalidated: true` 标记，
> 待 dog-food 跑通一轮（通过 `persona-judge` 验证）后才移除该标记。
> 详见 `contracts/manifest.schema.json` 的 `schema.unvalidated` 字段。

### Community Schemas（v0.2.0 新增）

除 9 种核心 schema 外，`distill-meta` 接受社区贡献的 schema 放置于 `references/schemas/community/`。每份必须符合 `contracts/schema-extension-contract.md`（YAML frontmatter + 7 个 H2 段 + 5-10 份测试语料），并提供自己的 `decision_tree_branch` 谓词。Phase 0.5 在走完 9 个核心分支之后按字母序扫描 community 目录；首个匹配谓词的 schema 胜出，多 match 时阻塞式提问用户。由社区 schema 生成的 persona skill 在 manifest 中标记 `schema_type_origin: community` + `schema_type_author: <handle>`。v0.2.0 社区目录为空——见 `docs/schema-contribution-guide.md` 如何提交首个社区 schema。

## Components（组件库）

Schema 不是固定模板，而是**组件的有序组合**。19 个可复用组件：
`hard-rules` / `identity` / `expression-dna`（七轴量化） / `persona-5layer` / `persona-6layer` /
`self-memory` / `work-capability` / `shared-memories` / `emotional-patterns` /
`mental-models`（三重验证） / `decision-heuristics` / `thought-genealogy` / `internal-tensions` /
`honest-boundaries` / `domain-framework` / `computation-layer` / `interpretation-layer` /
`correction-layer` / `execution-profile`（v0.3.0 新增：CDM 4-sweep 执行画像）。

每个组件都满足统一的 I/O 契约（输入：分类语料；输出：结构化 markdown + 可选数据）——**契约**定义见
**`contracts/component-contract.md`**，**组件文档**在 **`references/components/`**（每组件一个 `.md`）。

**关键设计**：
- `computation-layer` 可以挂到任何 schema（见 PRD §2.4 示例 C：`mentor + computation` = 量化交易型导师挂 ta-lib 指标计算）。
- `execution-profile` 是**跨维度的执行黏合层**：其它组件把人格碎片写出来，execution-profile 把碎片编译成 Claude 运行时查询的"指令表"。推荐用于 public-mirror / mentor，事件密度充足时可挂到任何 persona schema。

## Self-Contained Principle（重要）

**每一个由 distill-meta 生成的 persona skill 产物都是独立的**：

- 产物目录不 `import`、`source` 或引用 distill-meta 的任何文件
- 产物可以被 `cp -r` / `mv` / 打包分发到完全不同的环境
- 产物的 `SKILL.md` 自带触发词、manifest、全部组件内容
- 这个原则**借鉴自 nuwa-skill**：skill 的使用者不应该知道它是被谁生成的

**验收标准**：生成完成后，删除 distill-meta，产物 skill 仍然能正常被 Claude Code 加载并对话。

## Invocation（如何触发）

用户以任一方式触发即可：

- 中文：`蒸馏 张三` / `蒸馏乔布斯` / `帮我把 xxx 蒸馏成 skill` / `做一个 xxx 的 persona`
- 英文：`distill Jobs` / `build a persona skill for X` / `clone <person>` / `persona distill`
- 直接命令（Claude Code 斜杠命令）：`/distill-meta`

**零信息兜底**：用户只说"蒸馏张三"不提供任何资料时：
1. 走 `collaborator` schema + 全组件
2. 立即创建目录
3. Phase 1.5 展示"当前覆盖率为 0" 请求资料
4. 用户仍不提供 → 生成一份"骨架 + honest-boundaries 写满已知缺口"的最小产物

### Update branch — 已存在 persona skill 的升级路径（v0.2.0 新增）

Phase 0 会将目标 slug 对比 `produced/` 与用户提供的路径。发现已存在 persona skill 且满足任一条件——(a) `manifest.distill_meta_version` 与当前插件版本不同；(b) 任一 `components_used[].version` 与 `distill-meta/references/components/<slug>.md` 当前版本不同；(c) `manifest.schema.json` v0.2.0+ 迁移字段缺失——Phase 0 路由到 `agents/migrator.md` `mode: PLAN`，向用户展示生成的 `.migration/plan.md`。用户可选：

- `apply` → 重新调用 migrator `mode: APPLY`（7 步 + snapshot + re-validation，可 rollback）。
- `regenerate` → 走常规 Phase 1-5 全量重新蒸馏。
- `ignore` → 保持 frozen skill（不写入）。

默认 `apply`。Migrator **永远不破坏 self-contained 原则**——迁移完成后 `grep -r "distill-meta" {persona-skill-root}/` 仍返回 0 命中（master plan §9 #7）。详见 `references/migration.md` 与 `agents/migrator.md`。

## Contracts（跨 skill 接口契约）

以下 3 份契约是**权威**的跨 skill 接口定义，distill-meta 与 persona-judge / persona-router /
persona-debate / distill-collector 通过它们解耦：

| 契约 | 位置 | 作用 |
|------|------|------|
| Manifest Schema | `contracts/manifest.schema.json` | 生成的 persona skill 的 `manifest.json` 字段定义（含 schema、components、unvalidated 等） |
| Validation Report Schema | `contracts/validation-report.schema.md` | Phase 4 产出的 `validation-report.md` 结构（12 维评分 + 密度 + 行动项） |
| Component Contract | `contracts/component-contract.md` | 每个组件的输入/输出/元数据约定（distill-meta 与组件 agent 之间） |

**契约不允许在本 SKILL.md 内重复定义**；如果契约需要变更，改这 3 个文件并 bump 版本。

## Progressive Disclosure（内容分布）

| 层级 | 内容 | 位置 |
|------|------|------|
| 入口（本文件） | 编排流程 + 决策路径 + 契约指针 | `SKILL.md`（**必须 < 350 行**） |
| 参考 | 决策树 / 9 schema / 18 组件 / 提取方法 / 来源策略 / 产出规范 | `references/` |
| 代理 | 9 个 sub-agent 定义（corpus-scout / mental-model-extractor / ...） | `agents/` |
| 模板 | SKILL.md 骨架、manifest 模板、reference 模板 | `templates/` |
| 契约 | 跨 skill 接口（3 份） | `../../contracts/` |

## Anti-patterns

| 坏行为 | 为什么失败 | 正确做法 |
|--------|-----------|---------|
| 在本 SKILL.md 内展开 schema/组件细节 | 破坏 progressive disclosure，突破 350 行 | 放到 `references/` 并指针引用 |
| 产物 skill 引用 distill-meta 路径 | 破坏 self-contained | 产物只能引用自己目录内的文件 |
| 跳过 Phase 1.5（语料不足强行蒸馏） | 产出"假装认识"的人格 | 展示覆盖率 → 降级或请用户补料 |
| 跳过 Phase 4 验证 | 无法 dog-food，质量失控 | 必调 `persona-judge`，不过则回 Phase 2 |
| 抹平矛盾 | 丢掉最有信号的维度 | 写入 `conflicts.md`，保留张力 |
| 盘问用户 | 违反 nuwa "don't interrogate" | 零信息时走兜底 |
| 9 schema 不标 unvalidated | 误导下游 | manifest 中保留 `unvalidated: true` 直到 dog-food 通过 |

## Core Principle

> **"一个人不是模板，而是组件的特定组合。蒸馏不是复印，而是让组合活起来。"**
>
> A person is not a template but a specific composition of components.
> Distillation is not photocopying — it's making the composition live again.
