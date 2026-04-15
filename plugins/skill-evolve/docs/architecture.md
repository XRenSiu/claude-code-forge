---
name: architecture
description: Structural view of skill-evolve — components, phase state machine, per-round data flow, subagent contract, file artifacts, recovery model
version: 0.1.0
---

# skill-evolve — 架构文档（Architecture）

> 组件图、状态机、数据流、文件产物、恢复模型。读 `principles.md` 之后再读本文件。

---

## 1. 组件概览

```
┌──────────────────────────────────────────────────────────────────┐
│  Main Orchestrator (SKILL.md)                                    │
│   Phase 0 Baseline → Phase 1 Loop → Phase 2 Final                │
└───┬───────────────────┬────────────────────┬────────────────────┘
    │ reads             │ spawns             │ writes
    ▼                   ▼                    ▼
┌───────────┐    ┌────────────────┐    ┌─────────────────────┐
│ references│    │ Eval Subagent  │    │ Workspace           │
│  - rubric │    │ (general-      │    │  .skill-evolve/     │
│  - ratchet│    │  purpose)      │    │   baseline.md       │
│  - test   │    │ new context    │    │   experiments.tsv   │
│  - design │    │ reads SKILL    │    │   final-report.md   │
└───────────┘    │ + rubric       │    └─────────────────────┘
    │            │ + prompts      │         │
    │ templates  │ returns JSON   │         │ git history
    ▼            └────────────────┘         ▼
┌───────────┐            │             ┌──────────────────────┐
│ templates │            ▼             │ experiment: baseline │
│  - base   │    ┌────────────────┐    │ evolve: <desc> (+N)  │
│  - exp.tsv│    │ Target SKILL.md│    │ evolve: <desc> (-2)  │
│  - final  │    │ (edited here)  │    │                      │
└───────────┘    └────────────────┘    │ git checkout on      │
                         │             │ REVERT               │
                         ▼             └──────────────────────┘
                    ┌─────────┐
                    │  git    │ ← ratchet enforcement
                    │ commits │
                    └─────────┘
```

**核心洞察**：**主 agent 从不打分**。主 agent 只 diagnose + mutate + decide（依赖 subagent 返回的 JSON）。评分职责**物理隔离**在独立 context 的 subagent。

---

## 2. 目录结构

```
skill-evolve/
├── .claude-plugin/plugin.json
├── README.md
├── docs/
│   ├── principles.md                       # 设计原理
│   └── architecture.md                     # 本文件
└── skills/skill-evolve/
    ├── SKILL.md                            # 入口 + 3 Phase 编排
    ├── references/
    │   ├── rubric.md                       # 8 维评分细则（必读）
    │   ├── ratchet-protocol.md             # git 操作流 + 决策表
    │   ├── test-protocol.md                # 独立 subagent 评估协议
    │   └── design-rationale.md             # 三上游 + 三取舍 + 非目标
    └── templates/
        ├── baseline.md.tmpl                # Phase 0 输出模板
        ├── experiments.tsv.tmpl            # 每轮日志表头
        └── final-report.md.tmpl            # Phase 2 交付模板
```

**分层约定**：
- `SKILL.md` 只做编排（阶段流 + 触发判定），不含评分规则细节
- `references/` 放**静态协议**——rubric / 工作流 / 评估 prompt，本插件 owner 才改
- `templates/` 放**产物骨架**——每次运行时填入数据

这和 Anthropic 的 Progressive Disclosure 约定一致：SKILL.md 应保持 ≤500 行。

---

## 3. 三阶段状态机

```
┌────────────┐      git 不干净？           ┌─────────────┐
│  TRIGGER   │────── → ── 暂停询问 ────▶  │  ABORT /    │
│(user input)│                             │  STASH      │
└─────┬──────┘                             └─────────────┘
      │ git clean ✓
      ▼
┌────────────────────────────────────────────────────────┐
│  Phase 0 — Baseline                                    │
│   1. 创建 .skill-evolve/<skill-name>/ 工作目录         │
│   2. spawn eval subagent #1                            │
│   3. 写入 baseline.md                                  │
│   4. 判断：total >= target → 直接 Phase 2；否则 Phase 1 │
└─────┬──────────────────────────────────────────────────┘
      ▼
┌────────────────────────────────────────────────────────┐
│  Phase 1 — Evolution Loop                              │
│   对每一轮 N ∈ [1, max_rounds]:                        │
│                                                        │
│   ┌──────────────────────────────────────────────┐     │
│   │ Step 1 — Diagnose                            │     │
│   │   读最近评分 → 最弱维 → 段落定位 → 假设     │     │
│   └──────────────────────────────────────────────┘     │
│                      │                                 │
│   ┌──────────────────▼───────────────────────────┐     │
│   │ Step 2 — Mutate                              │     │
│   │   git commit -m "experiment: round-N base"   │     │
│   │   Edit SKILL.md (单点原子修改)               │     │
│   └──────────────────────────────────────────────┘     │
│                      │                                 │
│   ┌──────────────────▼───────────────────────────┐     │
│   │ Step 3 — Re-evaluate                         │     │
│   │   spawn eval subagent #N (new context)       │     │
│   │   不传：diff / 上一版分数 / 目标              │     │
│   │   读返回 JSON                                │     │
│   └──────────────────────────────────────────────┘     │
│                      │                                 │
│   ┌──────────────────▼───────────────────────────┐     │
│   │ Step 4 — Ratchet                             │     │
│   │   决策表：KEEP / REVERT / SKIP               │     │
│   │   KEEP  → git commit -m "evolve: ..."        │     │
│   │   REVERT → git checkout -- <file>            │     │
│   │   SKIP   → git checkout -- <file>            │     │
│   │   → append experiments.tsv                   │     │
│   └──────────────────────────────────────────────┘     │
│                      │                                 │
│                      ▼                                 │
│              终止条件检查                              │
│                │                                       │
│        ┌───────┴───────┐                               │
│        │ 未终止        │ 已终止                        │
│        ▼               ▼                               │
│    下一轮          进 Phase 2                          │
└────────────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│  Phase 2 — Final                                       │
│   1. spawn eval subagent #final                        │
│   2. 与最近 KEEP 分数对比（不一致 → 记录偏差）         │
│   3. 生成 final-report.md                              │
│   4. 列出剩余最弱维度作为下一轮候选                    │
└────────────────────────────────────────────────────────┘
```

### 终止条件（`ratchet-protocol.md` §收敛）

```python
def should_stop(history, target=90, max_rounds=15, plateau=3):
    last = history[-1]
    if last.total >= target:      return True, "TARGET_REACHED"
    if len(history) >= max_rounds: return True, "MAX_ROUNDS"
    if len(history) >= plateau:
        recent_keeps = [h for h in history[-plateau:] if h.decision == "KEEP"]
        if not recent_keeps:       return True, "CONVERGED"
    return False, None
```

任一满足即停。不再做任何 mutation。

---

## 4. 一轮的完整数据流

```
  Main Agent                 Eval Subagent (new ctx)        Git
      │                              │                        │
      │ [Step 1 Diagnose]            │                        │
      │  读 experiments.tsv 最后一行 │                        │
      │  identify weakest dim        │                        │
      │  form hypothesis             │                        │
      │                              │                        │
      │ [Step 2 Mutate]              │                        │
      │  git commit baseline ────────────────────────────────▶│ "experiment: round-N base"
      │  Edit target SKILL.md        │                        │
      │                              │                        │
      │ [Step 3 Re-evaluate]         │                        │
      │  spawn Agent(general-purpose)│                        │
      ├─── SKILL path ──────────────▶│                        │
      ├─── rubric.md full text ─────▶│                        │
      ├─── 3 test prompts ──────────▶│                        │
      │                              │  Read SKILL.md         │
      │                              │  simulate 3 prompts    │
      │                              │  score 8 dims          │
      │◀────── JSON scores ──────────│                        │
      │                              │                        │
      │ [Step 4 Ratchet]             │                        │
      │  parse JSON                  │                        │
      │  compare total vs last KEEP  │                        │
      │  decide                      │                        │
      │                              │                        │
      │   decision = KEEP:           │                        │
      │    git add; git commit ──────────────────────────────▶│ "evolve: <desc> (+N)"
      │    update last_kept_score    │                        │
      │                              │                        │
      │   decision = REVERT:         │                        │
      │    git checkout -- <file> ──────────────────────────▶│ working tree reset
      │                              │                        │
      │   decision = SKIP:           │                        │
      │    git checkout -- <file> ──────────────────────────▶│ working tree reset
      │                              │                        │
      │  append row to experiments.tsv                        │
      │                              │                        │
      │  check should_stop()         │                        │
```

---

## 5. Subagent 接口契约

### Spawn 输入（主 agent 传给评估 agent）

| 参数 | 类型 | 用途 | 来源 |
|------|------|------|------|
| `target_skill_path` | absolute path | subagent 读取目标文件 | 用户 CLI / 推断 |
| `rubric_md` | text | 评分依据（完整粘贴） | `references/rubric.md` |
| `test_prompts[]` | list of { prompt, expected_direction } | 效果维度 7/8 测试集 | 用户 / 自动生成 |

### Spawn **禁止**传入的上下文

- 上一版分数
- mutation diff
- 目标分数 / 轮次编号
- KEEP / REVERT 历史
- 任何含 "improved" / "new" / "v2" / "updated" 的修饰词

**反作弊 checklist**（`test-protocol.md §反作弊`）必须在 spawn 前跑一遍——任一违反作废重 spawn。

### 评估 Subagent 输出（严格 JSON Schema）

```json
{
  "rubric_version": "1.0",
  "skill_path": "...",
  "scores": {
    "workflow_clarity":        { "score": 0-10, "anchor": "N档", "rationale": "<引用段落>" },
    "boundary_handling":       { "score": 0-10, ... },
    "checkpoint_design":       { "score": 0-10, ... },
    "instruction_specificity": { "score": 0-10, ... },
    "trigger_coverage":        { "score": 0-10, ... },
    "architecture_conciseness":{ "score": 0-10, ... },
    "known_test_pass_rate":    { "score": 0-20, "test_results": [...], "rationale": "..." },
    "edge_voice_test":         { "score": 0-20, "edge_sub_score": 0-10, "voice_sub_score": 0-10, ... }
  },
  "total": 0-100,
  "weakest_dimension": "<dim_key>",
  "weakest_rationale": "<可被下一轮 mutate 直接动手的描述>"
}
```

`weakest_dimension` 是**下一轮 mutate 的输入**——因此不能写"整体不够好"这种没有 actionability 的话。评估 agent 必须给出可动手的维度名。

---

## 6. 棘轮决策表（Ratchet Decision Table）

从 `ratchet-protocol.md`：

| Δ total | 任一维度下降？ | 决策 | git 操作 |
|---------|---------------|------|----------|
| > 0 | 否 | **KEEP** | `git commit -m "evolve: <desc> (+N pts: <old>→<new>) [dim: <dim>]"` |
| > 0 | 是（非用户确认的牺牲） | **REVERT** | `git checkout -- <file>`，记录"局部回退" |
| == 0 | 否 + 至少一弱维提升 | **KEEP (rebalance)** | 同 KEEP，commit 加 `(rebalance)` |
| == 0 | 是 | **REVERT** | 同上 |
| < 0 | 任意 | **REVERT** | 同上 |
| subagent 崩溃 | — | **SKIP** | `git checkout -- <file>`，tsv 标 SKIP |

**硬规则**：永远不用 `git revert HEAD`（会产生反向 commit 污染 history）；只用 `git checkout -- <file>` 丢弃工作区。基线 experiment commit 仍在 git log 里供后续诊断——失败经验是资产。

**隐性约束**（触发即 REVERT，tsv 标 `REVERT(constraint)`）：
1. 删除了历史 KEEP 中明确表扬过的段落（即使总分小涨）
2. 改动了 frontmatter 的 `name` 字段（会破坏 plugin.json 引用）
3. 引入了未声明的外部依赖（MCP / 文件 / agent）

---

## 7. 产物文件

### `.skill-evolve/<skill-name>/baseline.md`（Phase 0 一次性）

包含：
- 基线总分 + 8 维分数表
- 最弱 3 维 + 失分段落引用
- 3 测试 prompt 实际输出 vs 期望对比
- 初步改进路线建议

### `.skill-evolve/<skill-name>/experiments.tsv`（每轮追加一行）

Tab 分隔，字段：

```
round  timestamp  total_old  total_new  delta  dim_old_lowest  dim_new_lowest  hypothesis  decision  commit_hash
```

- `round`：从 1 起递增
- `decision`：KEEP / KEEP(rebalance) / REVERT / REVERT(constraint) / SKIP
- `commit_hash`：KEEP 时 = evolve commit；其它 = baseline experiment commit

TSV 是**后续迭代不重复犯错的索引**。失败比成功更值钱——它告诉下轮 mutate 不要往那个方向走。

### `.skill-evolve/<skill-name>/final-report.md`（Phase 2 一次性）

- 基线 vs 终值对比表（8 维 + 总分）
- 实验统计：KEEP / REVERT / SKIP 各多少
- 关键改进列表：每次 KEEP 的 commit message
- 剩余最弱维度 = 下一次 evolve 的起点

### Git History

每轮至少 1 次 commit（baseline experiment）；KEEP 时额外 1 次（evolve commit）。一个完整循环的典型 git log：

```
8b21d4 evolve: split monolithic step list into Phase 0/1/2 (+4 pts: 67→71) [dim: workflow_clarity]
b7fa3d experiment: round-3 baseline before mutation
      (round-2 reverted — no evolve commit)
2d1c99 experiment: round-2 baseline before mutation
a3f1c2 evolve: add 3 failure modes to §Boundary (+5 pts: 62→67) [dim: boundary_handling]
f80abc experiment: round-1 baseline before mutation
```

每个 evolve commit 的 diff **可作为微课**：看用户能学到什么样的修改会涨分。

---

## 8. 故障恢复模型

中断场景：Ctrl-C / 进程崩溃 / token 耗尽 / 网络断。

**重启流程**（`ratchet-protocol.md §故障恢复`）：
1. 读 `experiments.tsv` 最后一行
2. `git log --oneline | head -20` 检查最近 commit 是否与 tsv 匹配
3. **不匹配** → 工作区可能脏，**停下**问用户：保留还是丢弃（永远不自动假设）
4. **匹配** → 从下一轮 Phase 1 继续

**核心规则**：**永远不在恢复时假设状态**。问比猜便宜——一次错误的自动恢复可能覆盖用户手改。

---

## 9. 评分稳定性监控

每 5 轮做一次**双盲复评**（`test-protocol.md §评分稳定性检查`）：
- 同一 SKILL.md 同一 rubric 同一测试集
- spawn 两个独立 subagent，比较总分差

| 分差 | 动作 |
|------|------|
| ≤ 5 | 评分稳定，继续 |
| 6-10 | 警告，记录到 tsv 但继续 |
| > 10 | **暂停循环**，让用户检查 rubric 是否太主观 |

成本：等同于多跑一轮。收益：早期发现"分数虚高 / rubric 漂移"。

---

## 10. 运行时假设

skill-evolve 是 **spec-driven**——没有常驻进程，所有状态在：
- 目标 SKILL.md（被修改的对象）
- 工作目录 `.skill-evolve/<skill-name>/`（日志 + 报告）
- git（棘轮 + 历史）

**副作用范围**：
- 只写目标 skill 的 SKILL.md（不改 references/templates/scripts）
- 只写 `.skill-evolve/<skill-name>/`（工作目录，可 gitignore 也可入 git）
- 只产生 git commit（在 mutate skill 所在仓库）

**多实例**：可以同时跑多个 skill-evolve（每个处理不同 target），只要 git 仓库不冲突（不同目标的 SKILL.md 路径不同）。

---

## 11. 扩展点

### 可替换的部分

- **rubric.md**：维度 / 锚点 / 权重——前提是保持 JSON schema 兼容
- **test-protocol.md**：subagent 调用方式（v0.2 计划接入 Haiku 评估 + Sonnet 精评的多模型）
- **测试 prompt 生成规则**：当前基于 description 推断，未来可接 skill-creator 的 60/40 split

### 不可改动的部分（breaking）

- SKILL.md 的 3 阶段编排（Phase 0/1/2 契约）
- 棘轮决策表（改了就不叫 ratchet）
- 独立 subagent 评分（改了就不叫 isolated eval）
- JSON 输出 schema（下游报告依赖）

---

## 12. 与 persona-judge（同仓库姊妹插件）的架构对比

| 方面 | persona-judge | skill-evolve |
|------|---------------|--------------|
| 调用方式 | 被 distill-meta Phase 4 调起 | 用户直接触发 |
| 评分维度 | 12（persona 专用） | 8（通用 skill） |
| 是否迭代 | 否（single-shot） | 是（棘轮循环） |
| 副作用 | 写 validation-report.md | 改 SKILL.md + git commit + 工作目录 |
| 隔离评分 | 已有（新 context 运行） | 已有（每轮独立 subagent） |
| 输出契约 | `validation-report.schema.md` | `experiments.tsv` + `final-report.md` |

可串联：persona-judge 出基线 → skill-evolve 循环 → persona-judge 出终值。两者输出格式不同但可手工对齐。

---

## 13. 文档索引

- `docs/principles.md` — 为什么这么设计
- `docs/architecture.md` — 本文件
- `skills/skill-evolve/references/rubric.md` — 8 维细则 + JSON schema
- `skills/skill-evolve/references/ratchet-protocol.md` — git 操作流 + 决策表
- `skills/skill-evolve/references/test-protocol.md` — subagent spawn 规范
- `skills/skill-evolve/references/design-rationale.md` — 三上游 + 三取舍 + 非目标
- `skills/skill-evolve/SKILL.md` — 触发入口 + 3 Phase 编排

架构图或数据流更新时，请同时检查 SKILL.md 的 Phase 描述与本文件 §3 状态机是否仍一致——两者互为文档与实现的双视角。
