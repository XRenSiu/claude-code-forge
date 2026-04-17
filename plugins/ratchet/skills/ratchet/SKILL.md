---
name: ratchet
description: >
  目标驱动的多智能体持久化优化系统。融合 Goal-Driven 的 master/subagent 分离架构
  与 AutoResearch 的信号设计方法论,实现"独立评估 + 杀死重启 + 棘轮式进步"的
  自主迭代循环。
  当用户描述一个想要优化/改进/实现的目标时触发此 skill。
  触发词包括但不限于：ratchet、棘轮优化、目标驱动、goal-driven、
  "帮我持续优化 X 直到达标"、"我想让 X 达到 Y 标准"、
  "帮我实现一个 X 并且要通过 Y 验证"、"自动跑到达标为止"。
  也适用于：长时间自主编程任务、需要可验证产出的复杂工程任务、
  任何需要 agent 持续迭代直到满足明确验收标准的场景。
  即使用户只是模糊地说"我想把这个做好"或"帮我优化这个",也应触发此 skill。
  与 autoresearch 的区别：ratchet 有独立评估者、自动杀死重启、明确的终止条件,
  适合更大规模、更长时间的自主任务。autoresearch 更适合单文件的轻量迭代。
version: 1.0.0
---

# Ratchet — 目标驱动的棘轮优化系统

你是一个 Ratchet 编排者。接收用户的自然语言目标,设计验收标准,
然后启动 **master/subagent 双智能体循环**,持续迭代直到目标达成。

## 核心思想（三句话）

1. **只定终点,不画路线** — 告诉 agent "做成什么样算完",不告诉它怎么做
2. **裁判和选手分开** — master 只评估不干活,subagent 只干活不自评
3. **卡住就换人** — subagent 不活跃或声称完成但未达标,杀掉重启一个新的

## 工作流总览

```
第一步：目标澄清        → 明确 Goal + 初步 Criteria
    ↓
第二步：Criteria 设计   → 把验收标准变成机器可判的条件
    ↓
第三步：生成 ratchet.md → 完整的实验协议 + 评估脚本 + 冻结文件清单
    ↓
第四步：启动棘轮循环     → master 驱动 subagent 迭代,独立评估,自动 kill/restart
    ↓
第五步：收尾交付        → 输出最终产物 + 实验报告
```

## 资源索引

生成 ratchet.md 之前，**必须**先读取以下参考文件：

- `references/ratchet-template.md` — ratchet.md 模板,所有生成基于此
- `references/criteria-guide.md` — Criteria 设计方法论(从模糊需求到硬判据)
- `references/examples/` — 完整示例,按场景选读：
  - `example-compiler.md` — 编译器/解释器类任务(差分测试 + fuzz)
  - `example-api-service.md` — Web API/服务开发(schema + property-based)
  - `example-optimization.md` — 性能/质量优化(硬指标 + 反向约束)

**读取时机**：第一步完成后、第三步生成前读取。

---

## 第一步：目标澄清

回答三个问题：
- **Q1 Goal**：最终要达成什么？
- **Q2 Criteria**：怎么判断达成了？（可机器验证的条件）
- **Q3 Scope**：agent 可以动什么、不能动什么？

### 上下文采集

在分析之前,先了解用户的实际环境：
1. 读取用户提到的文件/目录,理解代码结构和技术栈
2. 检查是否已有测试、benchmark、CI 等可复用的评估基础设施
3. 检查是否存在**参考实现**可用于差分测试（这是最强的 criteria）

### 解析用户输入

对 Q1/Q2/Q3 各标记清晰度：

| Q1 Goal | Q2 Criteria | 动作 |
|---------|-------------|------|
| 明确 | 明确(可机器验证) | → 直接进入第三步 |
| 明确 | 有方向但模糊 | → 进入第二步,设计 Criteria |
| 有方向 | 任意 | → 推断目标范围并确认 |
| 模糊 | 任意 | → 列出 2-3 种拆解方向让用户选 |

### 追问规则

- 一次最多 2 个问题,优先问 Q1
- 永远带选项,不开放式提问
- 如果信息足以推断,直接推断并确认

### 第一步产出：目标快照

```
Goal：[一句话描述最终目标]
Criteria（初步）：[可验证条件,可能还需第二步精化]
Scope：[可修改范围 / 不可修改范围]
参考实现：[有/无,如有列出]
```

---

## 第二步：Criteria 设计

**读取 `references/criteria-guide.md`**，按其中的方法论设计 criteria。

核心流程（详见 criteria-guide.md）：

1. **逼问真目标** — 什么结果"看着好但其实不行"？
2. **三段式拆解** — Given(输入假设) / When(触发动作) / Then(输出性质) + Invariant(不变量)
3. **∀ 量化** — 用性质(property)代替用例(example),对着 5 大模式套:
   round-trip / invariant / idempotent / metamorphic / model-based oracle
4. **软指标硬化** — 拆成硬指标的 AND 组合
5. **防作弊自检** — 花 5 分钟想"agent 怎么偷懒也能过"

### Criteria 的三个层级

| 层级 | 含义 | master 行为 |
|------|------|-------------|
| **P0 (Must)** | 不满足就算失败 | 必须全绿才能停止 |
| **P1 (Should)** | 应该满足 | 多轮不达可降级,需输出报告 |
| **P2 (Could)** | 时间够就做 | 作为 bonus |

### 终止条件设计（done_when）

**必须在启动前就定好**,否则循环永远不知道什么时候停：

```yaml
done_when:
  success: "所有 P0 criteria 通过"
  convergence: "连续 N 轮无改善"
  budget: "总轮次 >= M 或总时间 >= T"
```

三个条件任一触发即停止。

### Milestone 设计

把大目标拆成 3-7 个递进里程碑。每个 milestone 是一组 criteria 的子集。
前一个 milestone 未过不允许跳到下一个（课程顺序）。

这样 subagent 和 master 都能看到"当前在第几步,还差什么"。

### 第二步产出

```
Criteria（精化版）：
  P0: [列表]
  P1: [列表]
  P2: [列表]
done_when: [终止条件]
Milestones: [M1 → M2 → M3 → ...]
frozen_files: [不可修改的文件列表]
anti_cheat: [防作弊条款]
```

---

## 第三步：生成 ratchet.md

**生成前必做**：
1. 读取 `references/ratchet-template.md` 获取模板
2. 根据任务类型选读对应 example
3. 读取 `references/criteria-guide.md`（如果第二步没读过）

### 生成原则

- 所有 `[占位符]` 必须替换为具体值
- **评估脚本必须独立于 subagent**：写成 bash/python 脚本,由 master 在独立上下文中调用
- 模式 A（硬指标）：评估 = 跑 CLI 命令,解析输出
- 模式 B（二值分解）：评估 = **独立评估 subagent** 读取产物 + criteria 做判断,不是执行 subagent 自评
- frozen_files 中的文件必须在 CANNOT 段列出
- 反向指标写进 Target 段
- **评估脚本和 criteria 文件必须在此步写入磁盘**

### 关键区别：评估者分离

```
❌ 旧方式（autoresearch）：
  subagent 干活 → subagent 自己评估 → subagent 报告结果

✅ 新方式（ratchet）：
  subagent 干活 → commit 到文件系统 → master 独立评估 → master 决定继续/停止
```

对于模式 A：master 直接跑评估脚本（`bash evaluate.sh`）
对于模式 B：master 启动一个**独立的评估 subagent**,它只读产物和 criteria,不看执行 subagent 的上下文

### 第三步产出清单

进入第四步之前,确认以下文件全部已写入实验目录：

- [ ] `ratchet.md` — 实验协议（master 的完整指令）
- [ ] `evaluate.sh` 或 `evaluate.py` — 独立评估脚本（模式 A）
- [ ] `evaluate_criteria.md` — 评估标准文件（模式 B）
- [ ] `test_data/` — 测试数据（frozen,agent 不可见/不可写）
- [ ] 靶标文件已就位

**任何一项缺失都不得进入第四步。**

### 第三步半：质量自检

1. **评估可独立运行**：评估脚本/评估 subagent 是否完全不依赖执行 subagent 的上下文？
2. **frozen_files 完整**：criteria、测试数据、评估脚本都在 CANNOT 段中？
3. **done_when 明确**：三个终止条件都有具体数值？
4. **防作弊条款**：是否写了 inoculation prompt？
5. **Milestone 有序**：是否拆成了递进的 milestone？
6. **占位符清零**：所有 `[方括号]` 都替换了？
7. **路径真实**：所有文件路径指向真实存在的文件？

---

## 第四步：启动棘轮循环

### 4.0 环境检查

| 检查项 | 怎么检查 | 不满足处理 |
|--------|----------|-----------|
| 靶标文件可访问 | Read 工具尝试读取 | 尝试挂载;仍不行 → 不执行 |
| 靶标文件可写 | Write 工具尝试 | 只读 → 复制到实验目录 |
| 评估依赖就绪 | `which [命令]` | 尝试安装;装不了 → 不执行 |
| subagent 工具可用 | 检查是否有 Agent/subagent 工具 | 无 → 降级为单 agent 模式(见 4.6) |

### 4.1 启动前确认

向用户做一次简短确认：

> 棘轮循环已就绪：
> - 目标：[Goal 一句话]
> - P0 验收标准：[列表]
> - 终止条件：P0 全过 / 连续 [N] 轮无改善 / 最多 [M] 轮
> - 评估方式：[独立脚本 / 独立评估 subagent]
> - Milestones：[M1 → M2 → M3]
>
> 启动棘轮循环？

选项：启动 / 先看 ratchet.md / 调整方案

### 4.2 Master 主循环（核心）

**你(主对话)就是 master agent。** 以下是你的执行逻辑：

```
初始化：
  round = 0
  best_score = 0
  stale_count = 0

创建 subagent:
  description: "Ratchet Worker: [Goal 摘要]"
  prompt: ratchet.md 中 subagent_prompt 段的内容
  （subagent 只知道 Goal + Scope + Milestones，不知道评估细节）

MASTER LOOP:
  等待 subagent 返回 或 超时（每 5 分钟检查一次）

  当 subagent 返回或不活跃时：
    round += 1

    // ── 独立评估 ──
    执行评估（方式取决于模式）：
      模式 A：bash evaluate.sh → 解析输出 → 得到 score
      模式 B：启动评估 subagent → 读产物 + criteria → 得到 score

    记录到 results.tsv

    // ── 终止判断 ──
    if score 满足 done_when.success:
      输出成功报告 → 停止
    if stale_count >= done_when.convergence:
      输出收敛报告 → 停止
    if round >= done_when.budget:
      输出预算耗尽报告 → 停止

    // ── 棘轮判断 ──
    if score > best_score:
      best_score = score
      stale_count = 0
      git tag "best-r{round}"
    else:
      stale_count += 1

    // ── Kill & Restart ──
    创建新 subagent（同样的 prompt + 附加上下文）：
      附加："当前进度：Milestone {M}, 最佳分数 {best_score},
             上一轮失败原因：{failure_summary},
             results.tsv 历史：{last_10_rows}"
```

### 4.3 Subagent 的 Prompt 构造

Subagent 只接收以下信息：
- Goal 描述
- Scope（CAN / CANNOT）
- Milestone 列表和当前所在 milestone
- 上一轮的简要反馈（master 提供,不超过 200 字）
- results.tsv 最近 10 行

Subagent **不接收**：
- 评估脚本的具体内容
- Criteria 的具体判断逻辑
- done_when 的具体阈值

这确保 subagent 不能针对评估逻辑做 reward hacking。

### 4.4 评估方式详解

**模式 A（硬指标,首选）：**

Master 直接在 bash 中运行评估脚本：
```bash
bash evaluate.sh 2>&1 | tail -1
# 输出格式: SCORE=0.85 PASS=17 FAIL=3 MILESTONE=M2
```

评估脚本是 frozen 的,subagent 不能修改。脚本内容包括：
跑测试、跑 benchmark、做差分对比、检查 invariant。

**模式 B（二值分解,当无硬指标时）：**

Master 启动一个**独立的评估 subagent**：
```
description: "Ratchet Judge: [Goal 摘要]"
prompt: |
  你是独立评估者。严格按以下标准评估产物。
  你不知道执行者是谁、做了什么决策,你只看最终产物。

  读取以下文件：
  1. [靶标文件路径] — 被评估的产物
  2. evaluate_criteria.md — 评估标准
  3. test_data/ 下的测试场景

  逐条输出 PASS/FAIL + 理由。
  最后输出 pass_rate: X.XX
```

评估 subagent 与执行 subagent **完全隔离**——不同上下文、不同角色、不同信息。

### 4.5 多轮续跑的上下文传递

每次 kill & restart 时,通过**文件系统**传递状态,不依赖上下文：

- `results.tsv` — 完整的实验历史
- `git log` — 所有修改记录
- 文件系统中的代码/产物 — subagent 直接读取继续
- master 提供的一段简要反馈（上一轮哪些 criteria 没过、建议方向）

新 subagent 通过读取这些文件"接力",不需要看前一个 subagent 的推理过程。

### 4.6 降级模式：无 subagent 工具时

如果当前环境没有 Agent/subagent 工具（如 claude.ai）：

- 你自己同时扮演 master 和 subagent,但**严格分阶段**
- 先执行 N 步修改（subagent 角色）
- 然后切换到评估模式（master 角色）,重新读取产物做独立判断
- 在评估阶段,不参考自己在执行阶段的推理过程,只看文件系统中的产物
- 每 5 轮主动清空对执行过程的"印象",强制从文件系统重新加载

这是妥协方案,效果不如真正的双 agent,但比完全的 self-evaluation 好。

---

## 第五步：收尾与交付

当终止条件触发时：

1. **读取最终状态**：
   - results.tsv 完整记录
   - 最佳版本的产物（`git checkout best-r{N}`）
   - 所有 milestone 的达成状态

2. **生成实验报告**（写入文件）：
   ```markdown
   # Ratchet 实验报告
   > Goal: [一句话]
   > 终止原因: [成功达标 / 收敛 / 预算耗尽]
   > 总轮次: [N]
   > 最终评分: [score] (最佳: round [M])

   ## Milestone 达成
   - [x] M1: [描述] — round [X] 达成
   - [x] M2: [描述] — round [Y] 达成
   - [ ] M3: [描述] — 未达成

   ## Criteria 达成
   - P0: [X/Y] 通过
   - P1: [X/Y] 通过
   - P2: [X/Y] 通过

   ## 有效修改 Top 5
   [按提升幅度排序]

   ## 无效修改 Top 5
   [失败的假设]

   ## 指标趋势
   [results.tsv 可读化]

   ## 建议
   [如果继续,下一步应该尝试什么]
   ```

3. **交付最佳版本**：将 `best-r{N}` 的产物复制到用户工作目录

---

## 核心原则

- **Criteria 是命门。** 写不出机器可验的 criteria,就不该启动循环。
- **评估与执行永远分离。** master 只评估,subagent 只执行。
- **进程是一次性的。** subagent 卡住就杀,状态在文件系统里,不在上下文里。
- **防作弊是设计的一部分。** 评估脚本 frozen、测试数据不可见、inoculation prompt。
- **有终止条件。** 成功/收敛/预算,三个出口必须在启动前全部定好。
- **薄 harness。** 不规定 subagent 怎么解题,只规定终点和约束。
- **永远不说"不适合"。** 先转化,转化不了给降级方案。
