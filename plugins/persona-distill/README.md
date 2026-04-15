# persona-distill

> 把一个人（或一个领域、一套规则）**蒸馏成一个可对话、可复用的 Claude Code skill**。

---

## 这个插件是干嘛的？

给它一批语料（聊天记录、访谈、书信、公开文章……），它会生成一个**自包含**的 persona skill 目录——文件夹级别的"人格"，其他人可以 `cp -r` 带走、`/plugin install` 用，不依赖本插件。

生成完后你可以：

- **跟它对话**（持续体验"这个人会怎么想"）
- **评估质量**（12 维 rubric + 3 项活体测试，发现"像"或"不像"在哪）
- **在多个 persona 之间智能路由**（有 10 个 persona skill 时，问题自动路给最合适的那个）
- **让多个 persona 辩论同一个问题**（轮流 / 立场对垒 / 自由发言）
- **升级迁移**（组件库更新后，旧 persona skill 可以被 upgrade 而不破坏自包含性）

---

## 一个最小例子

**输入**：100 条和朋友 Alice 的 iMessage

**调用**：

```
"蒸馏 Alice 作为 friend schema 的 persona skill"
```

**产物**（自动生成的目录）：

```
alice-friend-skill/
├── SKILL.md                    # 触发词 + 人格声明
├── manifest.json               # 元数据（schema、components、validation_score）
├── components/
│   ├── identity.md             # 她是谁
│   ├── expression-dna.md       # 她怎么说话（7 轴量化）
│   ├── shared-memories.md      # 共同经历
│   ├── emotional-patterns.md   # 情绪模式
│   └── honest-boundaries.md    # 明确标注哪些问题资料不够
├── knowledge/
│   ├── chats/imessage/alice.md # 清洗+脱敏后的原始语料
│   └── conflicts.md            # 自动检测到的矛盾（保留，不抹平）
└── validation-report.md        # persona-judge 评估结果
```

你现在可以把 `alice-friend-skill/` 塞进任何 Claude Code 项目，它会作为独立 skill 被识别，**不再依赖本插件**。

---

## 5 个 skill

| Skill | 做什么 | 怎么触发 |
|-------|--------|----------|
| [`distill-meta`](./skills/distill-meta/SKILL.md) | 主编排器。**8 阶段工作流**：意图 → schema 决策 → 采集 → 评审 → 提取 → 多轮深化 → 组装 → 冲突检测 → 执行画像（CDM 4-sweep）→ 验证 → 交付。 | `蒸馏乔布斯` / `build a persona skill for 张三` / `distill my own style` |
| [`persona-judge`](./skills/persona-judge/SKILL.md) | 质量评估器。12 维 rubric（raw /110，pass ≥ 82）+ 3 项活体测试（Known / Edge / Voice）+ 密度评分（< 3.0 强制 FAIL）。自动被 Phase 4 调用，也可单跑。 | `评估 naval-skill 的质量` |
| [`distill-collector`](./skills/distill-collector/SKILL.md) | 多模态语料采集 + 脱敏。v0.2.0 **4 条可跑路径**（iMessage / email / twitter / generic），剩余 8 条是规格 + 第三方工具指针（自己导出 → 管到 generic）。 | `import imessage chat history` / `导入我的邮件语料` |
| [`persona-router`](./skills/persona-router/SKILL.md) | 跨 persona 调度器。扫描所有已装 persona skill 的 `manifest.json`，按 schema 相关性 + 领域重叠 + 组件覆盖 + 密度 + 一手来源占比打分，推荐 Top 1-3。 | `哪个 persona 最适合回答这个架构问题` |
| [`persona-debate`](./skills/persona-debate/SKILL.md) | 多 persona 辩论。3 种模式（轮流 / 立场对垒 / 自由），调度 2-5 个 persona，产出合成 transcript。 | `让 Jobs 和 Munger 辩论这件事` |

---

## 快速开始

```bash
# 1. 装插件
/plugin marketplace add XRenSiu/claude-code-forge
/plugin install persona-distill@claude-code-forge

# 2. 蒸馏一个人
蒸馏乔布斯作为产品设计 mentor

# 3. 评估质量
评估刚生成的 steve-jobs-mirror

# 4. 建立你的 persona 库后
用 persona-router 帮我选合适的 persona 来讨论这个架构问题
```

完整的端到端验证步骤（生成 → 评估 → 路由 → 辩论）：见 [`docs/integration.md §7`](./docs/integration.md)。

---

## 它是怎么跑的？

**spec-driven 插件**——Claude Code 在运行时读这些 markdown + json 文件按编排执行，**没有后台 server、没有常驻 runtime**。

唯一的例外：v0.2.0 新加了 4 个 stdlib-only Python 脚本（`skills/distill-collector/scripts/*.py`）用于解析 iMessage / email / twitter / 通用文本，你可以手动跑。

生成的 persona skill 也是一堆 markdown + json，**不依赖本插件就能加载**。

---

## 8 阶段工作流

```
Phase 0    意图澄清            → 对象 + 目的 + 检测是否已有同名 skill
Phase 0.5  Schema 决策          → 9 种之一 + 组件选定 + 立即建目录
Phase 1    语料采集             → 私有（distill-collector）+ 公开（并行 agent 调研）
Phase 1.5  Research Review      → 覆盖率表 + 缺口标注 + 用户确认
Phase 2    维度提取             → 并行按组件提取：三重验证 + 7 轴 DNA + 张力识别
Phase 2.5  迭代深化（v0.2.0）    → ≤ 3 轮 + Jaccard 收敛 + 高置信度自动回填
Phase 3    Skill 组装           → SKILL.md + manifest + 各组件文件
Phase 3.5  冲突检测（v0.2.0）    → 自动 surface 事实性矛盾到 conflicts.md（不 resolve）
Phase 3.7  执行画像（v0.3.0 新） → CDM 4-sweep：从 knowledge/ 事件反推 8 类 Macrocognition 指令条款
Phase 4    质量验证             → persona-judge：3 项测试 + 12 维 rubric + 密度评分
Phase 5    交付 / 升级          → 产出路径 + 触发词；已有 skill 走 migrator
```

---

## 9 种 schema（+ 社区可扩展）

| Schema | 适用 |
|--------|------|
| `self` | 蒸馏自己 |
| `collaborator` | 同事 / 下属 / 合作者 |
| `mentor` | 老板 / 导师 / 前辈 |
| `loved-one` | 家人 / 伴侣 / 前任（6 层人格） |
| `friend` | 朋友（loved-one 的轻量版） |
| `public-mirror` | 思想家 / KOL（给视角） |
| `public-domain` | 领域专家（给方法论） |
| `topic` | 领域而非单人 |
| `executor` | 规则体系（八字 / 塔罗 / 量化策略等） |

**v0.2.0 新增**：社区可通过 PR 提交自己的 schema 到 `references/schemas/community/`——见 [`docs/schema-contribution-guide.md`](./docs/schema-contribution-guide.md)。

---

## 19 个组件

Schema 不是固定模板，是**组件的有序组合**。19 个可复用组件：

```
hard-rules · identity · expression-dna（7 轴量化）· persona-5layer · persona-6layer
self-memory · work-capability · shared-memories · emotional-patterns
mental-models（三重验证）· decision-heuristics · thought-genealogy · internal-tensions
honest-boundaries · domain-framework · computation-layer · interpretation-layer · correction-layer
execution-profile（v0.3.0：CDM 4-sweep 执行画像，把描述编译为 8 类 Macrocognition 指令条款）
```

每个组件有统一的 I/O 契约，定义在 [`contracts/component-contract.md`](./contracts/component-contract.md)。

**execution-profile 是什么**：其它组件描述"他怎么想 / 怎么说"，execution-profile 把这些描述**编译为指令**——加载 persona skill 后执行任务时，Claude 在 8 类决策时刻（Sensemaking / Decision Making / Planning / Adaptation / Problem Detection / Coordination / Managing Uncertainty / Mental Simulation）查询对应的"识别 X → 直接做 Y"条款。基于 Klein 的 Recognition-Primed Decision 理论和 CDM 4-sweep 标准协议，从 `knowledge/` 里的**具体事件**反推，每条指令可追溯到具体行号。详见 [`docs/principles.md`](./docs/principles.md) 和 [`skills/distill-meta/references/extraction/cdm-4sweep.md`](./skills/distill-meta/references/extraction/cdm-4sweep.md)。

---

## 4 份跨 skill 契约

改动这些是 breaking change：

| 契约 | 作用 |
|------|------|
| [`contracts/manifest.schema.json`](./contracts/manifest.schema.json) | 每个产出 persona skill 的 `manifest.json` 字段 schema（v0.2.0 扩展了迁移字段） |
| [`contracts/validation-report.schema.md`](./contracts/validation-report.schema.md) | persona-judge 的输出 schema，也是 distill-meta Phase 4 gate 读取的格式 |
| [`contracts/component-contract.md`](./contracts/component-contract.md) | 19 个共享组件的 I/O 契约 |
| [`contracts/schema-extension-contract.md`](./contracts/schema-extension-contract.md) | v0.2.0 新增：社区 schema 必须满足的协议（frontmatter + 7 个 H2 + 测试语料） |

---

## v0.3.0 相对 v0.2.0 的变化

| 领域 | v0.2.0 | v0.3.0 |
|------|--------|--------|
| 执行层 | 无 | **Phase 3.7 execution-profile**（CDM 4-sweep：Incident → Timeline → 10-Probe → What-If；8 类 Macrocognition 指令；3 条红线校验） |
| 组件数 | 18 | **19**（+ execution-profile） |
| 阶段数 | 7 | **8**（+ Phase 3.7） |
| sub-agent 数 | 11 | **12**（+ execution-profile-extractor） |
| 提取框架数 | 7 | **8**（+ cdm-4sweep） |
| 理论来源 | nuwa / immortal / anti-distill | 上述 + Klein RPD / Hoffman-Crandall-Shadbolt CDM / Crandall Working Minds / Macrocognition |
| persona-judge | 12 维 rubric | 同 + Mindset Transfer 与 execution-profile red-line 联动 + 2 条 anti-gaming 条目 |

## v0.2.0 相对 v0.1.0 的变化

| 领域 | v0.1.0 | v0.2.0 |
|------|--------|--------|
| Phase 2.5 迭代深化 | single-pass | **multi-round**（Jaccard > 0.8 早停，≤ 3 轮，高置信度自动回填） |
| 冲突处理 | 只能用户手动追加 | **Phase 3.5 自动检测**（4 类冲突，只 surface 不 resolve） |
| distill-collector | 全部 scaffolding-only | **4 条 runnable**（iMessage / email / twitter / generic），6 条仍 spec-only |
| 迁移 | 无 | **migrator agent**，PLAN / APPLY 模式，保留自包含不变量 |
| schema | 9 个硬编码 | **9 核心 + 社区可扩展**（contract + contribution guide） |
| 契约数 | 3 | **4**（+ schema-extension-contract） |

完整 change log 和 v2 roadmap 在 [`docs/integration.md`](./docs/integration.md)。

---

## 诚实的边界

- **所有 9 个 schema 都带 `unvalidated: true`**——还没有一个真实 persona 被端到端 dog-food 跑通过。Dog-food 是 v1.0.0 的前置条件。
- **`distill-collector` 剩下 6 个平台（WeChat / QQ / Feishu / Slack / Dingtalk / Telegram）+ 音视频 + OCR 都是 spec-only**——你得自己跑第三方导出工具，然后管到 `generic_import.py`。
- **7 个已知安全 / 信任缺口**：privacy free-text PII、consent bypass、prompt injection from corpus、manifest 字段欠约束、rubric gaming、self-containment escape、schema 误用。**真实使用前**务必看 [`docs/integration.md §6.2`](./docs/integration.md)。
- **不要蒸馏未授权的真人**——`hard-rules` 是政策不是强制执行。

---

## 目录结构

```
persona-distill/
├── .claude-plugin/plugin.json
├── contracts/                               # 4 份跨 skill 契约
│   ├── manifest.schema.json
│   ├── validation-report.schema.md
│   ├── component-contract.md
│   └── schema-extension-contract.md         # v0.2.0
├── skills/
│   ├── distill-meta/                        # 主编排器
│   │   ├── agents/                          # 12 sub-agent
│   │   ├── references/
│   │   │   ├── schemas/                     # 9 core + community/
│   │   │   ├── components/                  # 19 组件（incl. execution-profile）
│   │   │   ├── extraction/                  # 提取框架
│   │   │   └── migration.md                 # v0.2.0
│   │   └── templates/
│   ├── persona-judge/                       # 12 维评估器
│   ├── distill-collector/
│   │   ├── references/                      # 12 平台规格 + 脱敏策略
│   │   └── scripts/                         # v0.2.0 — 4 个 stdlib Python parser
│   ├── persona-router/                      # 跨 persona 调度
│   └── persona-debate/                      # 多 persona 辩论
├── docs/
│   ├── integration.md                       # 如何连接 + 已知限制
│   ├── schema-contribution-guide.md         # v0.2.0 — 如何贡献 schema
│   └── credits.md                           # 参考库与设计决策
├── LICENSE
└── README.md
```

---

## License

MIT. See [LICENSE](./LICENSE).
