# Distill Skills 完整方案设计

> 一套覆盖所有蒸馏场景的 Claude Code Skill 体系设计。
> 本文档只到**方案与借鉴来源**层面，不包含具体实现代码。

---

## 0. 设计原则

在进入具体设计前，先锚定四个原则——这些原则贯穿整个体系，所有后续决策都服从它们：

1. **Persona 结构参数化**：不做"固定架构"，做"schema 库 + 组件化"。不同对象类型用不同 schema，但共享基础组件。这是对 colleague 5 层/ex 6 层/nuwa 三维/immortal 四维四种不同方案的统一抽象。

2. **生成侧 + 生成后双覆盖**：现有方案 95% 都在卷"如何生成一个 persona skill"，但 persona skill 生成之后的生态位（评估、调度、对抗）同样重要。体系必须覆盖完整生命周期。

3. **消除 LLM 幻觉的地方用 Python**：受 bazi-skill 的启发，凡是"LLM 算不准但 Python 能算准"的环节（排盘、统计、指标计算），都外包给 Python。Computation Layer 是 persona schema 的可选挂件，不是独立 skill 类别。

4. **质量靠迭代，不靠一次性**：cyber-figures 那句"Layer 3 是 405 段全文扫描后才发现的"揭示了真相——好的蒸馏是多轮深挖的结果。体系必须把"迭代深化"作为一等公民，而不是事后补丁。

---

## 1. 体系总览

### 1.1 Skill 阵容（2 核心 + 3 可选）

```
┌─────────────────────────────────────────────────────────┐
│                     生成侧（Creation）                    │
├─────────────────────────────────────────────────────────┤
│  [核心] distill-meta                                     │
│    ├── 主入口，决策树，编排                               │
│    ├── 9 种 persona schema（见第 2 节）                  │
│    ├── 可复用组件（表达 DNA、硬规则、思维模型等）          │
│    ├── 提取框架（三重验证、七轴 DNA、密度分类器等）        │
│    └── 迭代深化机制                                      │
│                                                          │
│  [可选] distill-collector                                │
│    └── 多模态采集（文本/图像/音频/视频）                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    生成后（Post-Creation）                │
├─────────────────────────────────────────────────────────┤
│  [核心] persona-judge                                    │
│    └── 质量评估，8 维 rubric + 三项测试 + 密度评分         │
│                                                          │
│  [可选] persona-router                                   │
│    └── 智能调度：从已装的 N 个 persona skill 中匹配最合适的 │
│                                                          │
│  [可选] persona-debate                                   │
│    └── 编排多个 persona 围绕同一问题结构化辩论             │
└─────────────────────────────────────────────────────────┘
```

**为什么是 2 核心 + 3 可选**：
- meta 和 judge 是**最小可用集合**——能生成、能验证。
- collector 在蒸馏公众人物/长辈需要音视频时才必要。
- router 和 debate 是 persona skill 积累到 10+ 个之后才有价值。

### 1.2 shape Skill 产物的通用目录结构

不管用哪种 schema，产出的 persona skill 都遵守统一骨架：

```
{persona-slug}/
├── SKILL.md              ← 入口，自包含，可独立安装
├── manifest.json         ← 元数据：schema 类型、版本、来源、指纹
├── components/           ← 按激活的组件动态生成
│   ├── {component}.md
│   └── ...
├── knowledge/            ← 原始语料归档（脱敏）
│   ├── chats/
│   ├── articles/
│   ├── transcripts/
│   └── media/
├── versions/             ← 每次更新的快照
├── conflicts.md          ← 来源矛盾（借鉴 immortal-skill）
└── validation-report.md  ← persona-judge 打分报告
```

**关键设计**：
- SKILL.md 永远自包含，**复制整个目录就能独立工作**，不依赖 distill-meta（借鉴 nuwa 的 "self-contained" 原则）
- manifest.json 记录用了哪个 schema 和哪些组件，方便 persona-router 读取做调度决策
- conflicts.md 专门存矛盾（借鉴 immortal-skill）——矛盾不能被抹平，是真实感的关键

---

## 2. Persona Schema 库（9 种）

这是整个体系最核心的设计。不再做"3 个固定架构"，而是**9 种 schema 共享底层组件**。

### 2.1 分类逻辑

按两个正交维度切分：

```
               对象是什么
            ┌────────────────────┐
            │  人（Persona）       │   规则体系（Non-Persona）
            │                     │
 语料       │  你了解 (私有)        │
 可得       │  ├── self            │       —
 性         │  ├── collaborator   │
            │  ├── mentor         │
            │  ├── loved-one      │
            │  └── friend         │
            │                     │
            │  你不了解 (公开)     │   executor
            │  ├── public-mirror  │   ├── bazi
            │  ├── public-domain  │   ├── qimen
            │  └── topic (多人)   │   └── ...
            └────────────────────┘
```

### 2.2 9 种 schema 说明

| # | Schema | 对象 | 主要组件 | 核心借鉴 |
|---|--------|------|---------|---------|
| 1 | **self** | 自己 | self-memory + persona-5layer + 表达 DNA | notdog1998/yourself-skill |
| 2 | **collaborator** | 同事/下属/合作者 | work-capability + persona-5layer + 表达 DNA | titanwings/colleague-skill |
| 3 | **mentor** | 老板/导师/前辈 | decision-framework + persona-5layer + work-capability + 表达 DNA | 新设计（collaborator + mental-models 混合） |
| 4 | **loved-one** | 家人/伴侣/前任/朋友 | shared-memories + persona-6layer + 表达 DNA + emotional-patterns | titanwings/ex-skill, perkfly/ex-skill, immortal-skill/personas/family |
| 5 | **friend** | 朋友 | shared-memories(light) + persona-5layer + 表达 DNA | loved-one 的轻量版 |
| 6 | **public-mirror** | 思想家/KOL（给视角） | mental-models + decision-heuristics + 表达 DNA + thought-genealogy + honest-boundaries | alchaincyf/nuwa-skill |
| 7 | **public-domain** | 领域专家（给方法论） | domain-framework(N 维) + 表达 DNA + 案例库 | midas.skill (六维财富) |
| 8 | **topic** | 领域而非单人 | consensus-frame + divergences + 操作手册 + 案例对比 | alchaincyf/x-mentor-skill |
| 9 | **executor** | 规则体系 | computation-layer + interpretation-layer + 话术风格 | jinchenma94/bazi-skill |

### 2.3 共享组件库（schema 的积木）

所有 schema 由以下组件拼装而成。组件可跨 schema 复用：

| 组件 | 作用 | 出现在哪些 schema | 借鉴来源 |
|------|------|------------------|---------|
| `hard-rules` | Layer 0 硬规则（最高优先级） | 所有 persona 类 | colleague-skill |
| `identity` | 身份卡片 | 所有 persona 类 | nuwa, colleague |
| `expression-dna` | 七轴表达风格量化 | 所有 persona 类 | nuwa-skill (核心创新) |
| `persona-5layer` / `persona-6layer` | 分层人格结构 | self/colleague/loved-one 等 | colleague 5 层, ex 6 层 |
| `self-memory` | 个人记忆库 | self | yourself-skill |
| `work-capability` | 工作能力（PART A） | collaborator/mentor | colleague-skill |
| `shared-memories` | 共同记忆（你 × TA） | loved-one/friend | ex-skill |
| `emotional-patterns` | 情绪模式/触发器 | loved-one | ex-skill 6 层 |
| `mental-models` | 思维模型（3-7 个，三重验证） | public-mirror/mentor | nuwa-skill |
| `decision-heuristics` | 决策启发式（if-then 5-10 条） | public-mirror/mentor | nuwa-skill |
| `thought-genealogy` | 思想谱系（受谁影响→影响谁） | public-mirror | nuwa-skill |
| `internal-tensions` | 内在张力（至少 2 对矛盾） | public-mirror/mentor | nuwa-skill |
| `honest-boundaries` | 诚实边界（≥3 条局限） | 所有 persona 类 | nuwa-skill |
| `domain-framework` | 领域维度框架（如财富六维） | public-domain | midas.skill |
| `computation-layer` | Python 计算模块（可选挂件） | executor, 可选挂到任何 schema | bazi-skill |
| `interpretation-layer` | 计算结果的解读话术 | executor | bazi-skill |
| `correction-layer` | 对话修正累积层 | 所有 schema | colleague-skill, ex-skill |

**关键设计**：`computation-layer` 可以挂到任何 schema 上。比如 `mentor + computation`（蒸馏一个量化交易员老板，挂上技术指标计算）、`public-domain + computation`（蒸馏一个医生，挂上药物交互查表）。

### 2.4 Schema 组装示例

**示例 A：蒸馏同事张三（collaborator）**
```yaml
schema: collaborator
components:
  - hard-rules
  - identity
  - work-capability        # PART A
  - persona-5layer         # PART B
  - expression-dna
  - honest-boundaries
  - correction-layer
```

**示例 B：蒸馏乔布斯（public-mirror）**
```yaml
schema: public-mirror
components:
  - hard-rules
  - identity
  - mental-models          # 6 个
  - decision-heuristics    # 8 条
  - expression-dna
  - internal-tensions
  - thought-genealogy
  - honest-boundaries
```

**示例 C：蒸馏一个量化交易型导师（mentor + computation）**
```yaml
schema: mentor
components:
  - hard-rules
  - identity
  - work-capability
  - persona-5layer
  - decision-heuristics
  - mental-models
  - expression-dna
  - computation-layer:     # 挂件
      type: "ta-calculations"
      python_module: "ta-lib"
  - honest-boundaries
  - correction-layer
```

这种设计的**核心价值**：新对象类型出现时不用改代码，只需定义新的 schema 组合。比如将来想蒸馏"科研组导师"，组合 `mentor + domain-framework(论文写作五维)` 即可。

---

## 3. distill-meta 详细设计

### 3.1 职责

**单一职责**：根据用户输入，生成一个高质量的 persona skill 产物（产物自包含、可独立运行）。

### 3.2 执行流程（7 Phase）

借鉴 nuwa-skill 的 Phase 模型，扩展为 7 Phase，纳入所有调研发现：

```
Phase 0  意图澄清
         ├── 对象识别
         ├── 目的识别（协作 vs 镜像）
         ├── 现有 skill 检测（更新 vs 新建）
         └── 用户最小信息收集（全部可跳过）

Phase 0.5  Schema 决策
         ├── 执行 What/Why 决策树
         ├── 选定 schema（9 种之一）
         ├── 选定组件（自动 + 用户确认）
         └── 立即创建 skill 目录（强制 self-contained）

Phase 1  语料采集
         ├── 私有语料：调用 distill-collector 或引导导入
         ├── 公开语料：多 agent 并行网络调研
         ├── 语料清洗：去重、脱敏、格式归一
         └── 按组件分类归档到 knowledge/

Phase 1.5  Research Review Checkpoint（借鉴 nuwa）
         ├── 展示语料覆盖率表格（按组件维度）
         ├── 标注信息缺口、矛盾、覆盖不足的组件
         ├── 用户确认或追加
         └── 语料不足时降级：减少组件、加厚 honest-boundaries

Phase 2  维度提取
         ├── 多 agent 并行按组件提取（每个组件一个 agent）
         ├── 三重验证（思维模型）
         ├── 七轴 DNA 量化（表达风格）
         ├── 张力识别（内在矛盾）
         ├── 密度分类（借鉴 anti-distill 的 classifier）
         └── 保留矛盾，不抹平

Phase 2.5  迭代深化（新增，借鉴 cyber-figures）
         ├── 全文扫描检测遗漏维度
         ├── 最多 3 轮迭代
         ├── 每轮产出"上轮错过的 X"
         └── 用户确认后合并

Phase 3  Skill 组装
         ├── 按 schema 拼装组件
         ├── 生成 SKILL.md、manifest.json、各组件文件
         ├── 写入 conflicts.md（矛盾存档）
         └── 生成触发词和调用说明

Phase 4  质量验证（调用 persona-judge）
         ├── 三项测试（已知/边界/声音）
         ├── 8 维 rubric 评分
         ├── 密度评分（高价值内容占比）
         └── 生成 validation-report.md，不通过则回 Phase 2

Phase 5  交付与后续
         ├── 告知产出位置和触发词
         ├── 提示进化方式（追加语料/对话修正）
         └── 建议下一步（跑 persona-debate 对比、装 persona-router）
```

### 3.3 决策树（Phase 0.5）

用户输入对象描述后，meta 按以下路径选择 schema：

```
是人还是规则体系？
│
├── 规则体系 → schema = executor
│
└── 是人
    │
    ├── 你有多少关于 TA 的私有语料？
    │
    ├── 没有（只有公开信息） → 
    │   │
    │   ├── 蒸馏来给视角/思维框架 → public-mirror
    │   ├── 蒸馏来用某个专业方法论 → public-domain
    │   └── 蒸馏一个"领域"而非单人 → topic
    │
    └── 有（聊天记录/文档/亲身接触）
        │
        ├── 对象 = 你自己 → self
        │
        ├── 对象 = 工作关系
        │   ├── 平级同事/下属 → collaborator
        │   └── 老板/导师/长辈 → mentor
        │
        └── 对象 = 亲密关系
            ├── 家人/伴侣/前任 → loved-one
            └── 朋友 → friend
```

**兜底规则**（借鉴 nuwa "don't interrogate"）：用户直接说"蒸馏张三"不给任何信息时，默认 = collaborator + 全组件 + 后续通过对话补充。

### 3.4 目录结构

```
distill-meta/
├── SKILL.md                     ← 主入口（<300 行，仅决策+编排）
├── references/
│   ├── decision-tree.md         ← Schema 决策树（第 3.3 节）
│   ├── schemas/                 ← 9 种 schema 定义
│   │   ├── self.md
│   │   ├── collaborator.md
│   │   ├── mentor.md
│   │   ├── loved-one.md
│   │   ├── friend.md
│   │   ├── public-mirror.md
│   │   ├── public-domain.md
│   │   ├── topic.md
│   │   └── executor.md
│   ├── components/              ← 组件定义
│   │   ├── hard-rules.md
│   │   ├── expression-dna.md    ← 七轴量化框架
│   │   ├── persona-5layer.md
│   │   ├── persona-6layer.md
│   │   ├── mental-models.md     ← 三重验证
│   │   ├── decision-heuristics.md
│   │   ├── shared-memories.md
│   │   ├── emotional-patterns.md
│   │   ├── work-capability.md
│   │   ├── self-memory.md
│   │   ├── domain-framework.md
│   │   ├── computation-layer.md
│   │   ├── thought-genealogy.md
│   │   ├── internal-tensions.md
│   │   ├── honest-boundaries.md
│   │   └── correction-layer.md
│   ├── extraction/
│   │   ├── triple-validation.md      ← 抄 nuwa
│   │   ├── seven-axis-dna.md         ← 抄 nuwa
│   │   ├── tension-finder.md         ← 抄 nuwa
│   │   ├── density-classifier.md     ← 抄 anti-distill
│   │   └── iterative-deepening.md    ← 新设计，借鉴 cyber-figures
│   ├── source-policies/
│   │   ├── blacklist.md              ← 抄 nuwa（知乎/公众号/百度百科）
│   │   ├── whitelist.md              ← 抄 nuwa（36氪/晚点/财新等）
│   │   └── primary-vs-secondary.md
│   └── output-spec.md                ← 产出物目录规范（第 1.2 节）
├── agents/                           ← sub-agent 定义
│   ├── corpus-scout.md               ← 借鉴 nuwa 6 agent
│   ├── mental-model-extractor.md
│   ├── expression-analyzer.md
│   ├── tension-finder.md
│   ├── memory-extractor.md           ← 新增，for loved-one/self
│   ├── work-analyzer.md              ← 抄 colleague
│   ├── persona-analyzer.md           ← 抄 colleague
│   ├── iterative-deepener.md         ← 新增
│   └── validator.md                  ← 调用 persona-judge
└── templates/
    ├── skill-md-template.md          ← SKILL.md 骨架（参数化）
    ├── manifest-template.json
    └── reference-file-template.md
```

### 3.5 借鉴与改造对照

| distill-meta 组件 | 来源 | 改造方式 |
|------------------|------|---------|
| Phase 0→5 主流程 | nuwa-skill/SKILL.md | 扩展 Phase 2.5 迭代，扩展 schema 分支 |
| 决策树 | **原创** | 基于本文第 3.3 节 |
| 9 种 schema | 综合 colleague/ex/yourself/nuwa/midas/bazi | 统一成参数化定义 |
| 组件库 | 拆解各现有 skill 的结构 | 去重、正交化 |
| 三重验证 | nuwa/references/extraction-framework.md | 直接抄 |
| 七轴 DNA | nuwa/references/extraction-framework.md | 直接抄 |
| 密度分类器 | anti-distill/prompts/classifier.md | 反向用作正向筛选 |
| 迭代深化 | cyber-figures 的"5 轮蒸馏"理念 | 新设计具体 prompt |
| Research Review Checkpoint | nuwa Phase 1.5 | 直接抄 |
| 来源黑白名单 | nuwa SKILL.md | 直接抄 |
| 对话修正机制 | colleague/prompts/correction_handler.md | 直接抄 |
| 增量合并 | colleague/prompts/merger.md | 直接抄 |
| 版本管理 | colleague/tools/version_manager.py | 直接抄 |

---

## 4. persona-judge 详细设计

### 4.1 职责

对任何 persona skill 打分，产出可操作的改进建议。

**两种触发**：
- 被 distill-meta 在 Phase 4 自动调用
- 用户主动说"评估 xxx persona skill"

### 4.2 评估维度（综合 4 个来源）

借鉴 skill-judge 8 维 + nuwa 三项测试 + anti-distill 密度 + 本文新增，共 **12 维评分**：

| 维度 | 满分 | 来源 | 评估方式 |
|------|------|------|---------|
| Known Test（已知测试） | 10 | nuwa | 3 个已知问题对比 |
| Edge Test（边界测试） | 10 | nuwa | 1 个未覆盖问题的不确定性表达 |
| Voice Test（声音测试） | 10 | nuwa | 100 字盲测辨识度 |
| Knowledge Delta | 10 | skill-judge | 是否比 Claude 默认知识多出了什么 |
| Mindset Transfer | 10 | skill-judge | 是否传递了思维模式 |
| Anti-Pattern Specificity | 10 | skill-judge | 反模式是否具体非泛化 |
| Specification Quality | 5 | skill-judge | YAML frontmatter 和触发描述质量 |
| Structure | 5 | skill-judge | 行数、层级、loading trigger |
| **Density** | 10 | **anti-distill 反向** | 高价值内容比例（REMOVE/MASK 级） |
| **Internal Tensions** | 10 | **nuwa** | 是否有 ≥2 对内在矛盾 |
| **Honesty Boundaries** | 10 | **nuwa** | 是否 ≥3 条具体局限 |
| **Primary Source Ratio** | 10 | **nuwa** | 一手来源占比 >50% |

总分 110 → 归一化到 100。

**通过门槛**：75 分。低于 75 回 Phase 2 迭代。

### 4.3 密度评分（核心创新）

借鉴 anti-distill，反向使用其分类器：

对 SKILL.md 的每一段内容打 4 种标签：
- `REMOVE`（高价值，具体阈值/反直觉经验/独特判断） → +2 分/段
- `MASK`（中高价值，人际网络/升级路径） → +1 分/段
- `DILUTE`（低价值，正确废话） → -1 分/段
- `SAFE`（通用知识） → 0 分/段

归一化到 0-10。**密度低于 3 分的 skill 不予通过**，要求重新蒸馏。

### 4.4 产出物

每次评估产出 `validation-report.md`：

```markdown
# Persona Skill Validation Report
Skill: steve-jobs-mirror
Date: 2026-04-14
Overall Score: 82/100 ✅ PASS

## Dimension Scores
| Dimension | Score | Notes |
| ... | ... | ... |

## Strengths
- ...

## Weaknesses
- Density only 4/10 — too many "正确废话" in decision-heuristics
- Honesty Boundaries only lists 2 items

## Recommended Actions
1. Rewrite decision-heuristic #3 with specific case
2. Add boundary for "cannot predict reaction to post-2011 events"
```

### 4.5 借鉴与改造

| 组件 | 来源 | 改造方式 |
|------|------|---------|
| 8 维 rubric | softaworks/agent-toolkit/skill-judge | 抄核心 8 维 |
| 三项测试 | nuwa Phase 4 | 抄，提取成独立 agent |
| 密度分类器 | anti-distill/prompts/classifier.md | 反向用于正向评估 |
| persona 专用维度 | 本文新增（张力、边界、来源比） | 原创 |

---

## 5. 可选 skill 设计

这三个是**扩展**，核心体系不依赖它们。

### 5.1 distill-collector（多模态采集）

**动机**：现有方案 95% 只处理文本。名人播客、长辈视频、访谈音频这些场景需要转写能力。

**职责**：把多模态输入统一成 Markdown 文本进入 knowledge/。

**支持格式**：
- 文本类：微信/QQ/飞书/钉钉/Slack/iMessage/Telegram/邮件/Twitter 导出
- 图像类：OCR + EXIF 元数据
- 音频类：Whisper 转写（支持中英混合）
- 视频类：yt-dlp 下载 + 音轨转写 + 字幕提取
- 文档类：PDF/docx/epub/Notion 导出

**统一 CLI 模式**（借鉴 immortal-skill 的 `immortal_cli.py`）：

```bash
distill-collector platforms          # 列出支持的平台
distill-collector setup wechat       # 配置凭据
distill-collector collect --platform wechat --contact "张三"
distill-collector transcribe ~/video.mp4
distill-collector import ~/chat.txt --format generic
```

**借鉴与改造**：
- 主架构 = immortal-skill/kit/
- 聊天记录解析 = colleague-skill/tools/ + yourself-skill/tools/
- 音视频转写 = anyone-to-skill + Whisper
- 隐私脱敏 = 新增（所有解析器统一调用）

### 5.2 persona-router（智能调度）

**动机**：当你装了 10+ 个 persona skill，每次手动选调用谁很麻烦。

**职责**：读取所有已安装 persona skill 的 manifest.json，根据用户的问题智能推荐最合适的 1-3 个。

**工作流程**：
1. 用户提问："这个架构方案怎么设计"
2. router 扫描所有 persona skill 的 manifest.json
3. 匹配维度：schema 类型、擅长领域（从 identity 提取）、组件覆盖度
4. 输出推荐：
   ```
   建议调用：
   1. colleague-zhangsan（后端架构专家，work-capability 覆盖 API 设计）
   2. steve-jobs-mirror（产品设计视角）
   3. mentor-lisi（你老板，曾做过类似决策）
   ```
5. 用户选择后触发

**借鉴**：`图鉴.skill`

### 5.3 persona-debate（多方辩论）

**动机**：同一个问题，让多个蒸馏出来的 persona 各自表态，可以看到真实的多元视角。

**职责**：编排 2-5 个 persona skill 围绕同一问题做结构化辩论。

**三种模式**：
- **Round-robin**：每人依次发言，共 3 轮
- **Position-based**：每人固定一个立场（支持/反对/中立）
- **Free-form**：自由发言，meta 做裁判总结

**借鉴**：`诸子.skill`

---

## 6. 完整借鉴矩阵

把所有参考库按组件维度汇总，方便你对照：

| 库 | Stars | 核心贡献 | 我们取什么 | 不取什么 |
|----|-------|---------|-----------|---------|
| `alchaincyf/nuwa-skill` | 7.4k | 认知 OS 架构、三重验证、七轴 DNA、6 agent 并行、质量验证 | **几乎全抄**——作为 public-mirror schema 的蓝本 + 提取框架基础 | 一些中文人物专属的来源列表 |
| `titanwings/colleague-skill` | 12.2k | 双层架构（Work+Persona）、5 层人格、采集脚本套件、merger/correction | **几乎全抄**——作为 collaborator schema 的蓝本 + 进化机制 | 仅同事场景的限制（我们泛化了） |
| `titanwings/ex-skill` | N/A | 6 层人格、memories + persona、星盘/MBTI/依恋集成 | 抄 6 层结构 + memories 组件 | 星盘/MBTI 部分过重，作为可选 |
| `notdog1998/yourself-skill` | N/A | 自我蒸馏的双层（self + persona）、WeChat/QQ parser | 抄 self-memory 组件 + 采集脚本 | 无 |
| `agenmod/immortal-skill` | N/A | 7 persona 模板、12+ 平台、conflicts.md、统一 CLI、snapshot | 抄 persona 模板思路（但我们 9 种）、conflicts.md、CLI 模式 | 防蒸馏和授权协议（不在范围内） |
| `jinchenma94/bazi-skill` / `gaoxin492/bazi-skill` | 755 | Python 计算层 + Agent 解读层分离 | 抄架构作为 executor schema + computation-layer 组件 | 八字专属规则 |
| `leilei926524-tech/anti-distill` | 1.4k | 4 级密度分类器、稀释策略 | 抄分类器用于正向密度评分 | 稀释策略本身（我们不做反蒸馏） |
| `alchaincyf/x-mentor-skill` | N/A | Topic skill 变体（蒸馏领域而非单人） | 抄作为 topic schema 蓝本 | 无 |
| `softaworks/agent-toolkit/skill-judge` | N/A | 8 维通用 skill rubric | 抄作为 persona-judge 的评估核心 | 非 persona 专用的维度 |
| `cyber-figures` | N/A | 迭代深化发现隐藏层 | 抄理念到 Phase 2.5 | 单个人物的专属内容 |
| `OpenDemon/anyone-to-skill` | N/A | 多模态（视频/音频） | 抄到 distill-collector | 无 |
| `图鉴.skill` | N/A | 跨 persona 调度 | 抄作为 persona-router 蓝本 | 无 |
| `诸子.skill` | N/A | 多 persona 结构化辩论 | 抄作为 persona-debate 蓝本 | 无 |
| `midas.skill` | N/A | 领域专家六维框架 | 抄作为 public-domain schema 示例 | 财富专属内容 |
| `YIKUAIBANZI/forge-skill` | N/A | 自我蒸馏 vs 他人蒸馏分离 | 借鉴概念（我们的 self 和其他分离） | 多智能体决策部分过重 |
| `wildbyteai/digital-life` | N/A | 5 个考古工具（证据优先） | 借鉴"先证据后追问"的理念到 Phase 2 | 具体的工具 |
| `anthropics/skills` (skill-creator) | 官方 | YAML frontmatter 规范、progressive disclosure | 遵循其规范 | 无 |

---

## 7. 各 schema 的详细数据模型

本节把 9 种 schema 的组件组合一次性列清楚，作为实现时的 spec。

### Schema 1: self
```
必需组件：hard-rules, identity, self-memory, persona-5layer, expression-dna, honest-boundaries, correction-layer
可选组件：computation-layer
典型语料：深夜聊天/情绪对话/日记/决策记录/社交媒体
产出文件：SKILL.md + self-memory.md + persona.md + manifest.json + conflicts.md
执行逻辑：收到问题 → persona-5layer 判断反应模式 → self-memory 提供经历参考 → expression-dna 输出风格
```

### Schema 2: collaborator
```
必需：hard-rules, identity, work-capability, persona-5layer, expression-dna, honest-boundaries, correction-layer
可选：computation-layer
语料：飞书/钉钉/Slack/邮件/PR review/会议纪要
产出：SKILL.md + work.md + persona.md + manifest.json + conflicts.md
执行：收到任务 → persona 判断态度 → work 执行 → persona 风格输出
```

### Schema 3: mentor
```
必需：hard-rules, identity, work-capability, persona-5layer, decision-heuristics, mental-models, expression-dna, honest-boundaries, correction-layer
可选：computation-layer, internal-tensions
语料：一对一记录/决策回顾/工作方法论分享
产出：SKILL.md + work.md + persona.md + decision-framework.md + manifest.json + conflicts.md
执行：收到问题 → decision-heuristics 过滤 → mental-models 分析 → persona 判断表达 → expression-dna 输出
```

### Schema 4: loved-one
```
必需：hard-rules, identity, shared-memories, persona-6layer, emotional-patterns, expression-dna, honest-boundaries, correction-layer
语料：聊天记录（主导）/照片/共同经历回忆
产出：SKILL.md + memories.md + persona.md + emotional-patterns.md + manifest.json + conflicts.md
执行：收到消息 → hard-rules 检查 → emotional-patterns 评估当前情绪 → shared-memories 取回记忆 → expression-dna 输出
```

### Schema 5: friend
```
必需：hard-rules, identity, shared-memories(轻量), persona-5layer, expression-dna, honest-boundaries, correction-layer
产出：SKILL.md + memories.md + persona.md + manifest.json + conflicts.md
```

### Schema 6: public-mirror
```
必需：hard-rules, identity, mental-models(3-7), decision-heuristics(5-10), expression-dna, internal-tensions(≥2), thought-genealogy, honest-boundaries
可选：computation-layer
语料：著作/访谈/推文/他人评价/决策记录/时间线
产出：SKILL.md + 6 个 research 文件（01-writings.md ~ 06-timeline.md，抄 nuwa）
执行：问题 → mental-models 分析视角 → decision-heuristics 推立场 → internal-tensions 检查一致性 → expression-dna 输出
```

### Schema 7: public-domain
```
必需：hard-rules, identity, domain-framework(N 维), expression-dna, honest-boundaries
可选：computation-layer, mental-models
语料：该领域的公开方法论
产出：SKILL.md + N 个维度文件 + cases.md + manifest.json
执行：问题 → domain-framework 定位维度 → 对应框架处理 → expression-dna 输出
```

### Schema 8: topic
```
必需：hard-rules, identity(是主题而非人), consensus-frame, divergences, expression-dna(中性), honest-boundaries
语料：3-5 个该领域顶级实践者的公开材料
产出：SKILL.md + consensus.md + divergences.md + cases.md + manifest.json
执行：问题 → consensus 给基线 → divergences 给不同流派视角 → 不模仿任何具体人的风格
```

### Schema 9: executor
```
必需：hard-rules, identity, computation-layer, interpretation-layer, expression-dna(话术风格)
语料：领域经典典籍/规则表
产出：SKILL.md + references/（规则表）+ tools/（Python 脚本）+ manifest.json
执行：输入 → computation-layer 精确计算 → interpretation-layer 解读 → expression-dna 话术输出
```

---

## 8. 实施路线（建议）

**这不是承诺，只是合理顺序**。你随时可以跳过或调整。

### Stage 1：最小可跑（MVP）
- distill-meta 骨架（Phase 0-3，暂不包含 Phase 2.5 迭代和 Phase 4 验证）
- 3 个 schema：self, collaborator, public-mirror（覆盖最常见场景）
- 直接复用 nuwa-skill 和 colleague-skill 的现有 prompt

### Stage 2：质量闭环
- 加上 persona-judge（2 核心完整了）
- 接通 Phase 4 回路
- 加上 Phase 2.5 迭代深化
- 补全其余 6 种 schema

### Stage 3：采集增强
- distill-collector（多模态）
- conflicts.md 机制
- version + correction

### Stage 4：生态
- persona-router
- persona-debate
- Schema 扩展机制（社区可提 PR 加新 schema）

---

## 9. 关键设计决策备忘（为什么这么做）

这些是过程中反复讨论的点，记录下来免得将来忘了为什么。

1. **为什么不做"3 个固定架构 skill"**：因为 colleague 5 层/ex 6 层/nuwa 三维/immortal 四维没有任何两个一样，说明架构必须参数化。
2. **为什么 9 种 schema 不合并**：合并后每种的组件组合差异依然存在，不如显式列出。
3. **为什么 executor 不独立成 skill**：它就是 computation-layer 组件+话术，没必要另起炉灶。
4. **为什么 computation-layer 不只属于 executor**：它可以挂到任何 schema 上（蒸馏一个量化交易导师）。
5. **为什么 persona-judge 是核心不是可选**：没有量化评估的蒸馏就是玄学，质量无法改进。
6. **为什么 router 和 debate 是可选**：在 persona skill 数量 <10 之前没价值。
7. **为什么产物必须自包含**：防止生成的 persona skill 依赖 distill-meta。借鉴 nuwa 的核心原则。
8. **为什么保留 conflicts.md**：矛盾是真实感的来源，不能被抹平。借鉴 immortal-skill。
9. **为什么强制 Research Review Checkpoint**：不让 AI 蒙头跑完，人工介入一次可以避免很多错误。借鉴 nuwa。
10. **为什么把 anti-distill 的 classifier 反向用**：正向（密度评分）比反向（防蒸馏）更有价值，而分类器本身是通用的。

---

## 10. 文档自身的局限

诚实地说：

- **我没有真正 clone 并运行任何一个参考库**，所有结构都是基于搜索结果和 README/SKILL.md 片段。具体 prompt 的细节可能和我描述的有偏差。真正实施时需要逐个验证。
- **9 种 schema 没有经过实际蒸馏验证**。可能实施时发现某些组件组合有问题，schema 会增减。
- **Phase 2.5 迭代深化是理念，不是成熟方法**。cyber-figures 的经验说明这件事有价值，但怎么系统化做好还需要探索。
- **computation-layer 作为通用挂件是设想**。实际可能绝大多数 schema 不需要它，只有 executor 和极少数专业 persona 需要。
- **本方案和现有方案（nuwa/colleague/immortal/dot-skill）的差异化点**：主要在"参数化 schema + 生成后生态 + 密度评分"三个点。如果生态继续演进，这些差异可能会被覆盖。

实施过程中这些不确定性都会暴露出来，需要动态调整。


### Tier 1——核心参考（必读）

| 库 | 链接 | Stars | 核心贡献 | 我们取什么 |
|----|------|-------|---------|-----------|
| nuwa-skill | https://github.com/alchaincyf/nuwa-skill | 7.4k | 认知 OS、三重验证、七轴 DNA、6 agent 并行、Phase 0→4 主流程 | **几乎全抄**——public-mirror schema 蓝本 + 提取框架基础 |
| colleague-skill | https://github.com/titanwings/colleague-skill | 12.2k | 双层架构（Work+Persona）、5 层人格、采集脚本套件、merger/correction | **几乎全抄**——collaborator schema 蓝本 + 进化机制 |
| yourself-skill | https://github.com/notdog1998/yourself-skill | N/A | 自我蒸馏双层（self + persona）、WeChat/QQ parser | self-memory 组件 + 采集脚本 |
| anti-distill | https://github.com/leilei926524-tech/anti-distill | 1.4k | 4 级密度分类器（SAFE/DILUTE/REMOVE/MASK）、稀释策略 | classifier 反向用作密度评分 |

### Tier 2——新一代多维蒸馏

| 库 | 链接 | 核心贡献 | 我们取什么 |
|----|------|---------|-----------|
| immortal-skill | https://github.com/agenmod/immortal-skill | 7 persona 模板、12+ 平台、conflicts.md、统一 CLI (`immortal_cli.py`)、snapshot | persona 模板思路、conflicts.md、CLI 模式 |
| immortal-web | https://github.com/agenmod/immortal-web | immortal 的 Web 版本 | 交互参考 |
| ex-skill (titanwings) | https://github.com/titanwings/ex-skill | 6 层人格、memories + persona、星盘/MBTI/依恋集成 | 6 层结构 + memories 组件 |
| ex-skill (therealXiaomanChu) | https://github.com/therealXiaomanChu/ex-skill | 5 层 + 星盘/MBTI 八功能/九型/依恋 | 对比参考 |
| ex-skill (perkfly) | https://github.com/perkfly/ex-skill | memories + persona 5 层 + iMessage/SMS | 对比参考 |
| forge-skill | https://github.com/YIKUAIBANZI/forge-skill | 自我蒸馏与他人蒸馏分离、多智能体决策 | 分离理念 |
| digital-life | https://github.com/wildbyteai/digital-life | 5 个考古工具（前世/社死/AI 替身/遗产/墓志铭），"先证据后追问" | Phase 2 的证据优先原则 |
| anyone-to-skill | https://github.com/OpenDemon/anyone-to-skill | 多模态输入（视频/PDF/聊天/音频） | distill-collector 的多模态思路 |

### Tier 3——名人复刻样本（public-mirror schema 的 golden output）

| 库 | 链接 | 用途 |
|----|------|------|
| steve-jobs-skill | https://github.com/alchaincyf/steve-jobs-skill | public-mirror 最完整样本（6 心智模型+8 启发式+完整 DNA+6 份 research） |
| elon-musk-skill | https://github.com/alchaincyf/elon-musk-skill | 对比样本 |
| munger-skill | https://github.com/alchaincyf/munger-skill | 投资领域样本 |
| feynman-skill | https://github.com/alchaincyf/feynman-skill | 教学方法论样本 |
| naval-skill | https://github.com/alchaincyf/naval-skill | 4 轮实战对话 demo |
| taleb-skill | https://github.com/alchaincyf/taleb-skill | 反脆弱思想样本 |
| paul-graham-skill | https://github.com/alchaincyf/paul-graham-skill | 创业思维样本 |
| karpathy-skill | https://github.com/alchaincyf/karpathy-skill | 技术导师样本 |
| ilya-sutskever-skill | https://github.com/alchaincyf/ilya-sutskever-skill | AI 前沿思维样本 |
| zhang-yiming-skill | https://github.com/alchaincyf/zhang-yiming-skill | 中国企业家样本 |
| zhangxuefeng-skill | https://github.com/alchaincyf/zhangxuefeng-skill | 中国 KOL 样本 |
| mrbeast-skill | https://github.com/alchaincyf/mrbeast-skill | 内容创作样本 |
| trump-skill | https://github.com/alchaincyf/trump-skill | 高辨识度表达 DNA 样本 |
| x-mentor-skill | https://github.com/alchaincyf/x-mentor-skill | **topic schema 蓝本**——蒸馏领域而非单人 |

### Tier 4——执行器类（executor schema）

| 库 | 链接 | Stars | 用途 |
|----|------|-------|------|
| bazi-skill (jinchenma94) | https://github.com/jinchenma94/bazi-skill | 755 | executor schema 蓝本（八字排盘） |
| bazi-skill (gaoxin492) | https://github.com/gaoxin492/bazi-skill | N/A | "Python 计算层 + Agent 解读层"分离架构参考 |
| Numerologist_skills | https://github.com/FANzR-arch/Numerologist_skills | N/A | 奇门/紫微复杂规则体系 |
| yinyuan-skills | https://github.com/Ming-H/yinyuan-skills | N/A | 月老（规则简单+话术重） |

### Tier 5——生成后生态（persona-judge/router/debate 的来源）

| 库 | 链接 | 用途 |
|----|------|------|
| agent-toolkit (skill-judge) | https://github.com/softaworks/agent-toolkit | **persona-judge 核心**——8 维通用 skill rubric |
| 图鉴.skill | 见 awesome list 查询 | **persona-router 蓝本**——跨 persona 调度器 |
| 诸子.skill | 见 awesome list 查询 | **persona-debate 蓝本**——多 persona 结构化辩论 |
| midas.skill | 见 awesome list 查询 | **public-domain schema 示例**——领域六维（财富操作系统） |
| cyber-figures | https://github.com/cyber-immortal/cyber-figures | **Phase 2.5 迭代深化理念来源**——"Layer 3 是 405 段全文扫描后才发现的" |

### Tier 6——官方标准

| 库 | 链接 | 用途 |
|----|------|------|
| anthropics/skills | https://github.com/anthropics/skills | 官方 skill-creator，YAML frontmatter 规范、progressive disclosure |
| openai/skills | https://github.com/openai/skills | OpenAI 的 skill 规范（交叉参考） |

### Tier 7——导航/聚合（了解生态用）

| 库 | 链接 | 用途 |
|----|------|------|
| awesome-human-distillation | https://github.com/mliu98/awesome-human-distillation | 蒸馏 skill 清单 |
| awesome-persona-distill-skills | https://github.com/xixu-me/awesome-persona-distill-skills | 30+ persona skill 汇总（含图鉴/诸子/midas 等链接查询入口） |
| awesome-distillhub-persona-skills | https://github.com/codeman008/awesome-distillhub-persona-skills | DistillHub 聚合 |
| MSB-skills | https://github.com/cytxnyu/MSB-skills | 赛博人物 skill 导航（含 4 种不同风格的"自己.skill"对比） |
| awesome-persona-skills | https://github.com/tmstack/awesome-persona-skills | tmstack 的 persona 清单 |
| colleague-skill-gallery | https://titanwings.github.io/colleague-skill-site/gallery/ | colleague-skill 的官方 Gallery（63+ skill） |
| dot-skill roadmap | https://titanwings.github.io/colleague-skill-site/ | titanwings 的 colleague-skill 继任者路线图 |

---

## 3 个找不到直接链接的说明

`图鉴.skill`、`诸子.skill`、`midas.skill` 在调研中反复出现但没爬到 GitHub 直链——它们都被提到在两个 awesome list 里（`xixu-me/awesome-persona-distill-skills` 和 `mliu98/awesome-human-distillation`），实际动手时去那两个 list 里搜索就能找到。


