---
name: architecture
description: Structural view of persona-distill — layers, data flow, sub-agent orchestration, produced-skill anatomy, runtime assumptions
version: 0.3.0
---

# persona-distill — 架构文档（Architecture）

> 组件图、数据流、接口契约、产物布局。read-after `principles.md`。

---

## 1. 系统分层

```
┌────────────────────────────────────────────────────────────────────┐
│  Layer 6: Produced Persona Skills (self-contained, zero deps)      │
│           alice-friend-skill/   jobs-mirror/   ziping-executor/    │
└───────────────▲────────────────────────────────────────────────────┘
                │ produces
┌────────────────────────────────────────────────────────────────────┐
│  Layer 5: Orchestrator Skills (5 skills — user-invocable entry)    │
│   distill-meta · persona-judge · distill-collector · router · debate │
└───────────────▲────────────────────────────────────────────────────┘
                │ spawns
┌────────────────────────────────────────────────────────────────────┐
│  Layer 4: Sub-Agents (12 specialized agents under distill-meta)    │
│   corpus-scout · persona-analyzer · expression-analyzer ·          │
│   memory-extractor · mental-model-extractor · tension-finder ·     │
│   iterative-deepener · candidate-merger · conflict-detector ·      │
│   execution-profile-extractor · work-analyzer · validator · migrator│
└───────────────▲────────────────────────────────────────────────────┘
                │ references
┌────────────────────────────────────────────────────────────────────┐
│  Layer 3: Reference Libraries (schemas / components / extraction)  │
│   9+N schemas · 19 components · 8 extraction frameworks (incl.     │
│   cdm-4sweep) · 3 source policies · 1 decision tree · output spec  │
│   · migration                                                      │
└───────────────▲────────────────────────────────────────────────────┘
                │ validates against
┌────────────────────────────────────────────────────────────────────┐
│  Layer 2: Cross-Skill Contracts (4 versioned schemas)              │
│   manifest.schema.json · validation-report.schema.md ·             │
│   component-contract.md · schema-extension-contract.md             │
└───────────────▲────────────────────────────────────────────────────┘
                │ templates
┌────────────────────────────────────────────────────────────────────┐
│  Layer 1: Templates & Runnable Scripts                             │
│   skill-md-template · manifest-template · migration-plan-template ·│
│   4 stdlib-only Python parsers (iMessage/email/twitter/generic)    │
└────────────────────────────────────────────────────────────────────┘
```

**分层规则**：上层引用下层；下层不知道上层存在。下层的 breaking change 需要上层协调（这就是 contracts 的角色）。

---

## 2. 顶层目录结构

```
persona-distill/
├── .claude-plugin/plugin.json                  # 插件清单（version 源头）
├── contracts/                                  # Layer 2 — 跨 skill 契约
│   ├── manifest.schema.json                    # 产物 manifest 的 JSON Schema
│   ├── validation-report.schema.md             # persona-judge 输出格式
│   ├── component-contract.md                   # 19 组件的 I/O 契约
│   └── schema-extension-contract.md            # 社区 schema 必须符合
├── skills/                                     # Layer 5 + 4 + 3
│   ├── distill-meta/                           # 主编排器（Layer 5）
│   │   ├── SKILL.md                            # 触发入口，8 阶段流程
│   │   ├── agents/                             # Layer 4 — 12 子代理
│   │   ├── references/                         # Layer 3
│   │   │   ├── schemas/                        #   9 core + community/
│   │   │   ├── components/                     #   19 可复用组件
│   │   │   ├── extraction/                     #   8 提取框架（incl. cdm-4sweep）
│   │   │   ├── source-policies/                #   中英文源策略
│   │   │   ├── decision-tree.md                #   schema 决策树
│   │   │   ├── output-spec.md                  #   产物目录规格
│   │   │   └── migration.md                    #   升级协议
│   │   └── templates/                          # Layer 1
│   ├── persona-judge/                          # 独立评判器
│   ├── distill-collector/
│   │   ├── references/                         # 12 平台规格 + 脱敏策略
│   │   └── scripts/                            # 4 个 stdlib Python parser
│   ├── persona-router/                         # 跨 persona 调度
│   └── persona-debate/                         # 多 persona 辩论
├── docs/
│   ├── principles.md                           # 设计原理（本文件的上游）
│   ├── architecture.md                         # 本文件
│   ├── integration.md                          # 实现细节 + 已知限制
│   ├── schema-contribution-guide.md            # 如何贡献 schema
│   └── credits.md                              # 借鉴来源
├── LICENSE
└── README.md
```

---

## 3. 核心数据流：一次端到端蒸馏

```
  用户                      distill-meta (主)          sub-agents              产物目录
   │                              │                       │                      │
   │ "蒸馏 Alice 作为 friend"     │                       │                      │
   ├─────────────────────────────▶│                       │                      │
   │                              │ Phase 0               │                      │
   │                              │  识别对象 + 检测已有  │                      │
   │                              │                       │                      │
   │                              │ Phase 0.5             │                      │
   │                              │  读 decision-tree.md  │                      │
   │                              │  选 friend schema     │                      │
   │                              │  读 schemas/friend.md │                      │
   │                              │  确定 7 个组件        │                      │
   │                              │  建目录骨架 ─────────────────────────────▶│  alice-friend-skill/
   │                              │                       │                      │
   │                              │ Phase 1               │                      │
   │                              │  spawn corpus-scout   │  采集 iMessage ──▶│  knowledge/chats/
   │                              │                       │  采集公开资料 ──▶│  knowledge/public/
   │                              │                       │                      │
   │  [Research Review checkpoint]│                       │                      │
   │◀─────────────────────────────│ 显示覆盖率表 + 缺口   │                      │
   │ "ok / 补采 X"                │                       │                      │
   ├─────────────────────────────▶│                       │                      │
   │                              │ Phase 2（并行）       │                      │
   │                              │  spawn 并行：         │                      │
   │                              │   ├ persona-analyzer  │  识 identity ────▶│  components/identity.md
   │                              │   ├ expression-       │  7 轴 DNA ──────▶│  components/expression-dna.md
   │                              │   │  analyzer         │                      │
   │                              │   ├ memory-extractor  │  shared-memories ▶│  components/shared-memories.md
   │                              │   ├ mental-model-     │  三重验证 ──────▶│  components/mental-models.md
   │                              │   │  extractor        │                      │
   │                              │   └ tension-finder    │  稳定极性 ──────▶│  components/internal-tensions.md
   │                              │                       │                      │
   │                              │ Phase 2.5（迭代）     │                      │
   │                              │  spawn iterative-     │  ≤ 3 轮扫描        │
   │                              │  deepener             │  Jaccard > 0.8 早停│
   │                              │  spawn candidate-     │  高置信度回填 ──▶│  （updates components/）
   │                              │  merger               │                      │
   │                              │                       │                      │
   │                              │ Phase 3               │                      │
   │                              │  读 output-spec.md    │                      │
   │                              │  生成 SKILL.md ──────────────────────────▶│  SKILL.md
   │                              │  生成 manifest.json ─────────────────────▶│  manifest.json
   │                              │                       │                      │
   │                              │ Phase 3.5             │                      │
   │                              │  spawn conflict-      │  4 类冲突扫描 ──▶│  knowledge/conflicts.md
   │                              │  detector             │                      │
   │                              │                       │                      │
   │                              │ Phase 3.7             │                      │
   │                              │  spawn execution-     │  CDM 4-sweep       │
   │                              │  profile-extractor    │  (Incident →       │
   │                              │                       │   Timeline →       │
   │                              │                       │   10-Probe →       │
   │                              │                       │   What-If)       ──▶│  components/execution-profile.md
   │                              │                       │  + Knowledge Audit │  (+ honest-boundaries 追加)
   │                              │                       │                      │
   │                              │ Phase 4（外部验证）   │                      │
   │                              │  Task persona-judge   │                      │
   │                              │   └ 新 context 启动 ─▶  12 维 rubric     │
   │                              │                       │  3 项活体测试      │
   │                              │                       │  密度评分 ─────▶│  validation-report.md
   │                              │  读 validation-       │                      │
   │                              │  report frontmatter   │                      │
   │                              │  verdict 分支：       │                      │
   │                              │   ├ PASS → Phase 5    │                      │
   │                              │   ├ COND → Phase 5+   │                      │
   │                              │   └ FAIL → 回 Phase 2 │                      │
   │                              │     (最多 3 次)       │                      │
   │                              │                       │                      │
   │                              │ Phase 5               │                      │
   │◀─────────────────────────────│ 交付：路径 + 触发词   │                      │
   │                              │  + 后续建议           │                      │
```

---

## 4. 契约中心化（Contracts as the Hub）

`contracts/` 是**4 个 skill 之间唯一稳定的耦合点**。

| 契约 | Producer | Consumer | breaking change 的影响 |
|------|----------|----------|------------------------|
| `manifest.schema.json` | distill-meta / migrator | judge · router · debate · 任意下游 | 所有 5 个 skill + 所有已存在的 persona skill |
| `validation-report.schema.md` | persona-judge | distill-meta Phase 4 gate | distill-meta 主流程解析逻辑 |
| `component-contract.md` | distill-meta (components/*) | 9 core + N community schemas | 所有引用该组件的 schema |
| `schema-extension-contract.md` | 社区贡献者 | distill-meta Phase 0.5 发现 | 社区 schema 装载阶段 |

**改契约 = 给所有下游发公告**。因此契约版本化（Semver），在 `integration.md` 中有 breaking / additive 差异说明。

### manifest.json 字段摘要

```json
{
  "persona_distill_version": "0.2.0",           // 生产者版本，router 依此决定兼容
  "schema_type": "friend",                       // 9 core 之一 或 社区扩展
  "schema_type_origin": "core",                  // "core" | "community"
  "schema_type_author": null,                    // community 时填
  "subject_type": "real-living-consented",       // 合规声明
  "components_used": ["identity", "expression-dna", ...],
  "validation_score": 87,                        // 必须有对应 validation-report.md
  "density_score": 4.2,
  "verdict": "PASS",                             // PASS|CONDITIONAL_PASS|FAIL
  "distill_meta_version": "0.2.0",               // 升级判断依据
  "components_fingerprint": "sha256:...",        // 组件库快照
  "last_migrated_at": null,
  "migration_history": [],
  "triggers": [...],
  "fingerprint": "sha256:..."                    // knowledge/ 内容哈希
}
```

router / judge / debate 只通过该 manifest 识别 persona skill——**不解析 SKILL.md body**、不假设目录内部结构。这让任何符合 manifest schema 的 persona skill（包括非本插件生成的）都能被识别。

---

## 5. 产出 persona skill 的内部布局

```
alice-friend-skill/
├── SKILL.md                        # 入口：frontmatter（触发词）+ 人格声明
├── manifest.json                   # 元数据（上节字段）
├── components/                     # 对应 schema 规定的组件子集
│   ├── identity.md                 # 她是谁 + subject_type
│   ├── expression-dna.md           # 7 轴量化 + 代表样本
│   ├── shared-memories.md          # 共同经历（朋友 schema 特有）
│   ├── emotional-patterns.md       # 情绪触发 + 应对
│   ├── hard-rules.md               # 合规+安全边界
│   ├── execution-profile.md        # Phase 3.7 产物（可选）：8 类指令条款
│   └── honest-boundaries.md        # 资料不足之处（含 Execution Profile Gaps 段）
├── knowledge/                      # 原始语料（脱敏后，仅语料；审计件放根目录）
│   ├── chats/imessage/alice.md
│   └── public/...                  # 按来源平台分目录
├── conflicts.md                    # Phase 3.5 产物（根目录，非 knowledge/）
├── execution-profile-trace.md      # Phase 3.7 可选（根目录）：incident+probe 树
└── validation-report.md            # persona-judge 输出（可再跑覆盖）
```

**不变量**：`grep -rE "persona-distill|distill-meta" alice-friend-skill/` 必须返回 0。

**加载模型**：Claude Code 在识别到 `SKILL.md` + `manifest.json` 后自动注册这个 skill；触发词命中时加载 SKILL.md，按需引用 components/ 和 knowledge/。

---

## 6. Sub-Agent 编排模式

### 并行扇出（Phase 2）

`distill-meta` 在 Phase 2 并行 spawn 5 个独立 agent，每个写一个组件。彼此不通信，各自读同一份 `knowledge/`，输出到各自的 components/ 文件。

**为什么并行**：组件正交（原理文件 §「为什么 19 组件」），独立提取不会污染。
**并发上限**：`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 时走 agent teams；默认 5 路并发。
**失败处理**：任一 agent 失败 → 主协调者补跑该路径，其它不回滚。

### 串行依赖（Phase 2.5 → Phase 3.5 → Phase 3.7 → Phase 4）

`iterative-deepener` 必须读 Phase 2 全部输出后才能决定"下一轮问什么"；`candidate-merger` 必须读 deepener 的候选才能决定回填哪些；`conflict-detector` 要所有组件都写完才能跨组件比对；`execution-profile-extractor` 需要 conflicts.md 作为 Sweep 1 的 incident 提示输入（但不作为 evidence 源），因此跟在 3.5 之后；`validator` 要产物完整才能活体测试。

这些不能并行。

### 隔离评判（Phase 4）

`persona-judge` 作为**单独 skill** 被 Task tool 调起，运行在**新 context**。`distill-meta` 只能通过读 `validation-report.md` frontmatter 获知结果——**不能看 judge 的推理过程**。

这是自评偏差的防护（原理文件 §「为什么 Phase 4 不能自评」）。

---

## 7. 可执行脚本接口（distill-collector/scripts）

4 个 stdlib-only Python 脚本，无外部依赖：

| 脚本 | 输入 | 输出 | 脱敏 |
|------|------|------|------|
| `imessage_import.py` | chat.db 路径 | `.md` 对话流 | 电话/邮箱/卡号/API key |
| `email_import.py` | `.mbox` / `.eml` | `.md` 按线程 | 同上 + 签名块 |
| `twitter_import.py` | 官方 archive.zip | `.md` 按时间线 | URL 展开 + @handle |
| `generic_import.py` | 任意 `.txt` / `.csv` | `.md` | 仅正则脱敏 |

`redactor.py` 是共享模块，**内嵌 §6.1/§6.2 测试向量作自检**——脚本启动时先跑自检，失败立即退出。

**为什么 stdlib-only**：自包含规则延伸到 collector——用户不该为运行导入脚本装 pip 包。

剩余 6 平台（WeChat / QQ / Feishu / Slack / Dingtalk / Telegram）+ 音视频 + OCR 是 spec-only：用户自己跑第三方导出 → 管到 `generic_import.py`。

---

## 8. Router & Debate 的读模型

### persona-router 扫描路径

按顺序扫：
```
.claude/skills/                       # 项目局部
~/.claude/skills/                     # 用户全局
~/.claude/plugins/cache/*/skills/     # 插件缓存
```

发现含 `manifest.json` 的目录 → 对照 `manifest.schema.json` 验证 → 进入评分：

```
score = 0.25·schema_type_relevance
      + 0.30·domain_overlap
      + 0.20·component_coverage
      + 0.15·density_bonus
      + 0.10·primary_source_bonus
```

总分 Top 1-3 推荐。evidently 无匹配时显式报告扫描过的路径，辅助调试。

### persona-debate 协调模型

三种模式（全部由 `references/modes.md` 的状态机驱动）：
- **round-robin**：固定顺序轮发言，每人 1 轮 × N 圈
- **position-based**：moderator 分配对立立场，每 persona 守立场发言
- **free-form**：moderator 按上一轮 transcript 决定下一个发言者

硬上限：3 轮 × 5 参与者。产物是合成 transcript，**不改动任何 participant 的 skill 文件**。

---

## 9. 升级路径（Migration Architecture）

```
旧 persona skill                migrator agent              新 persona skill
┌────────────────┐              ┌──────────────┐            ┌────────────────┐
│ manifest.json  │              │ PLAN mode    │            │ manifest.json  │
│   v0.1.0       │──────read────│  - diff 组件 │            │   v0.2.0       │
│ components/    │              │  - 保护编辑  │            │ components/    │
│ knowledge/     │              │ APPLY mode   │──write────▶│ knowledge/     │
└────────────────┘              │  - 写入      │            └────────────────┘
                                │  - grep 不变 │
                                │    量验证    │
                                │  - 失败回滚  │
                                └──────────────┘
```

**保护机制**：
- 用户手改过的组件文件（对比 `components_fingerprint`）→ 拒绝自动迁移，只显示 diff
- `knowledge/` 目录**永不动**
- APPLY 后 `grep -r "distill-meta" .` 必须返回 0；否则整体回滚到 snapshot

快照：APPLY 前 `cp -r` 整个 skill 到 `<skill>.pre-migration-<timestamp>/`。成功后可删；失败自动恢复。

---

## 10. 运行时假设

persona-distill 是 **spec-driven**——没有后台服务、没有常驻进程：
- Claude Code 在需要时读 SKILL.md + references + agents 执行
- 4 个 Python 脚本是**可选**的，用户手动跑
- 所有状态保存在文件系统（生成目录 + git history）

**无状态含义**：
- 可中断恢复（重启 Claude Code 后从最后一个完成的 Phase 续）
- 可多实例（两个终端同时蒸馏不同对象互不影响）
- 可离线调试（把生成目录带走，本地检查）

---

## 11. 扩展点

外部贡献可触达的 4 个接口：

| 接口 | 契约 | 难度 | 审核 |
|------|------|------|------|
| 新 schema | `schema-extension-contract.md` | 中 | PR 人工审 + 测试语料 |
| 新组件 | `component-contract.md` | 高 | 需修改 18 → N 的协议升级 |
| 新 collector | `distill-collector/references/*` 格式 | 中 | stdlib-only + 自检测试向量 |
| 新 rubric 维度 | `validation-report.schema.md` 扩展 | 高 | 破坏性变更，需 major bump |

前两个是 additive，后两个是协议级改动。

---

## 12. 相关文档索引

- `principles.md` — 为什么这么设计
- `integration.md` — 实现细节 / v0.2.0 vs v0.1.0 / 安全限制 / v2 roadmap
- `schema-contribution-guide.md` — 提 schema PR 的手册
- `credits.md` — 借鉴来源

架构图或数据流需要更新时，请同时检查 `integration.md` 的"Integration topology" 与本文件 §3 的数据流图是否仍一致——两者互为双视角（实现细节视角 vs 设计视角）。
