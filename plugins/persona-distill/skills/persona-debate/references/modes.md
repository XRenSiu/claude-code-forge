# Debate Modes — Turn Mechanics

> 本文件是 `persona-debate` 三种模式的**权威定义**。SKILL.md 引用本文件，`agents/moderator.md` 按本文件实现状态机。
> Authoritative definition of the three debate modes. SKILL.md references this; `agents/moderator.md` implements the state machines described below.

---

## 0. Shared Conventions

1. **命名**：`P1..PN` = 参与 persona skill；`M` = moderator agent。
2. **字数**：每类发言有硬上限，moderator 在 prompt 里写明 `max_chars: X, overflow will be truncated`。
3. **全局停止条件**（任一满足即停）：round cap / token_budget 已耗 ≥ 90% / 最近一轮 token-overlap ≥ 0.85 (convergence) / 连续 2 轮 fact-free (drift)。

---

## 1. Round-robin Mode

**适用**：默认模式；视角均衡；节奏清晰。

### 1.1 参数

| 参数 | 范围 | 说明 |
|------|------|------|
| 参与者数 N | 2 ≤ N ≤ 5 | 用户指定顺序 (`P1, P2, ..., PN`) |
| 轮次数 | 固定 3 | Opening / Rebuttal / Synthesis |
| 每轮每人发言数 | 1 | 严格单发言 |

### 1.2 每轮字数与任务

| 轮次 | 任务 | 字数上限 | 传给 persona 的上下文 |
|------|------|---------|---------------------|
| Opening | 亮出立场（140 char） | 140 | 原始问题 |
| Rebuttal | 回应**上一位**的 opening（280 char） | 280 | 原始问题 + 上一位 opening |
| Synthesis | "如果必须选" 一句话（140 char） | 140 | 原始问题 + 本人 opening + 本人 rebuttal |

### 1.3 状态机 (State Machine)

```
START → init(N, order)
  → OPENING: for P_i in (P1..PN): speak(140c, ctx=Q)
  → REBUTTAL: for P_i in (P1..PN): speak(280c, ctx=Q + prev_P's_opening)
  → SYNTHESIS: for P_i in (P1..PN): speak(140c, ctx=Q + own_opening + own_rebuttal)
  → MODERATOR_SUMMARY (divergences / convergences / verdict)
  → FINAL
```

### 1.4 持续时间

`3N + 1` invocations（N=3 → 10；N=5 → 16）。

### 1.5 Example (condensed)

```
Q: "小型 SaaS 团队要不要自研 CI/CD 流水线？"
P1=Jobs, P2=Munger, P3=Naval

[Opening]
Jobs:    产品即品味的体现，CI/CD 是产品体验的一部分——能自研就自研。(121c)
Munger:  Inversion: 先问自建会失败在哪里——maintenance tax。默认买。(108c)
Naval:   杠杆思维：自动化 > 人力。但你要的是杠杆工具，不是再造一个。(92c)

[Rebuttal]
Jobs → Naval:  "再造"和"打磨"不同。标准货 ≠ 体验 ≠ 差异化。(54c)
Munger → Jobs: 体验是副产品，稳定是前提。先活下去再谈品味。(48c)
Naval → Munger: 同意维护税存在，但 GitHub Actions 已是 80 分方案。(62c)

[Synthesis]
Jobs: 先用 GHA，但在部署体验上做一层自己的包装。
Munger: 买现成，省下的时间做客户。
Naval: GHA + 少量胶水脚本，别盖 CI 宫殿。

[Moderator Summary]
分歧：是否值得在 CI 上做差异化投入。
收敛：全员反对"从零自研"。
Verdict：买 GHA，只在与产品耦合处做薄包装。
```

---

## 2. Position-based Mode

**适用**：决策类问题（"要不要做 X？"），需要立场对抗。

### 2.1 参数

| 参数 | 范围 | 说明 |
|------|------|------|
| 参与者数 N | 2 ≤ N ≤ 5 | 预先分派立场 |
| 立场枚举 | `支持` / `反对` / `中立` (support / oppose / neutral) | 每位一个 |
| 轮次数 | 固定 2 | Position-defense / Cross-examination |

**立场约束**：至少 1 个支持 + 1 个反对；中立可选。全员同立场 → 拒绝开辩。

### 2.2 每轮字数与任务

| 轮次 | 任务 | 字数上限 | 上下文 |
|------|------|---------|--------|
| Position-defense | 从分派立场论证 | 420 | 问题 + 本人立场标签 |
| Cross-examination | 每人挑一个**对立立场**发言中的具体论点反驳 | 280 | 问题 + 所有 defense 的 transcript |
| (final) Cross-matrix | Moderator 合成：谁挑战了谁、谁的挑战最有效 | — | 全部 transcripts |

### 2.3 状态机

```
START → assign {P_i: pos_i}; validate ≥1 support AND ≥1 oppose
  → DEFENSE_ROUND: for P_i: argue from pos_i (420c)
  → CROSS_EXAM: for P_i: pick one opposing-position statement and rebut (280c)
       drift-check → WARN + redo once if rebuttal tone contradicts pos_i
  → CROSS_MATRIX (moderator tabulates who-challenged-whom)
  → MODERATOR_SUMMARY (strongest cross, drift events, verdict)
  → FINAL
```

### 2.4 持续时间

`2N + 2` invocations (N defenses + N cross-exams + 1 cross-matrix + 1 summary)。

### 2.5 Position drift detection

Moderator 在 cross-exam 阶段对每条回应做一次 "position consistency check"：
- 若回应的核心动词与 `supportive_lexicon` / `oppositional_lexicon` 的倾向与分派立场**相反**，标记为 drift。
- 第一次 drift → 警告并要求 persona 重述；第二次 drift → 在最终 summary 中注明 "`{P_i} drifted from assigned position`"。

### 2.6 Example (condensed)

```
Q: "团队应不应该放弃 JIRA 换成轻量工具？"
P1=Kent Beck(支持), P2=Brooks(反对), P3=Dan North(中立)

[Defense]
Beck(支): JIRA 把小团队训练成表格填写员……(320c)
Brooks(反): Tool swap 成本被低估；你换来的是静默数据迁移地狱……(410c)
North(中): 看团队规模与工作流成熟度，<10 人 yes，>30 人 no。(180c)

[Cross-exam]
Beck → Brooks: 你说的迁移地狱来自重度使用，轻度用户换工具零成本。(210c)
Brooks → Beck: "轻度用户"本身就暴露你没用过 JIRA 的真正价值……(240c)
North → Beck: 你把"讨厌表格"和"工具不合适"合并了。(130c)

[Moderator Summary]
Cross-matrix: Beck↔Brooks 最激烈；North 挑战 Beck 的 framing。
Drift: 无。
Verdict：规模 < 15 人可以换；否则先改工作流再谈工具。
```

---

## 3. Free-form Mode

**适用**：探索性问题；参与者专长差异大；没有天然对立。

### 3.1 参数

| 参数 | 范围 | 说明 |
|------|------|------|
| 参与者数 N | 2 ≤ N ≤ 5 | 无预设顺序 |
| 轮次上限 | 3 硬上限 | 超过 → moderator 强制结束 |
| 每轮约束 | 每位 persona 至少发言 1 次 | 否则 moderator 点名 |
| 单次发言字数 | 300 | 统一上限 |

### 3.2 触发与点名机制

**relevance-check**：moderator 每收到一段 transcript，做一次 "谁最相关"判断——对每位 persona 打 0-3 的相关分，最高分者获得下一个发言权。

**forced turn**：若某 persona 连续 **4 turns** 未发言，下一发言权无条件给它（防止独占话筒）。

**round 边界**：当 N 位 persona 在本轮都至少发言 1 次 → 进入下一轮。

### 3.3 状态机

```
START → init speech_count_i = 0 for all P
  → ROUND_k (k = 1..3):
       loop:
         pick_next_speaker():
           if ∃ P silent ≥4 turns → force P
           else → argmax score(P) = relevance(P, transcript)
                                     - 0.5 × (speech_count_i - min_j speech_count_j)
         P speaks (≤300c); speech_count_P += 1
         if all P have spoken in round_k: k += 1; break if k > 3
         check stop conditions (convergence ≥0.85 / budget ≥90% / 2-round drift) → EXIT
  → MODERATOR_SUMMARY (top-2 divergences / convergences / one-sentence verdict)
  → FINAL
```

### 3.4 持续时间

上限 `3N + 1`；实际受 stop conditions 截断。防独占 penalty 见 §3.3 `score()` 公式。

---

## 4. Anti-patterns (applies to all modes)

| 模式通病 | 识别信号 | Moderator 处理 |
|---------|---------|----------------|
| **Monopoly 独占** | 单一 persona 的 speech_count 比 min 多 ≥ 2 | 下一轮强制跳过；summary 中标注 |
| **Echo chamber** | 连续 2 发言的 token-overlap ≥ 0.6 | 打断；要求下一位 "challenge 而非 agree" |
| **Fact-free loop** | 连续 2 轮无任何可验证主张（启发式：无数字、无专有名词、无具体例子） | 整轮标记；若再次出现触发 drift stop |
| **Moderator advocacy** | Moderator 自己的发言包含立场词汇（"我认为"、"应该"） | 自检失败；重写 summary |
| **Position drift**（仅 position-based） | 见 §2.5 | WARN / 重述 / 终局标注 |
| **Round-0 collapse** | Opening 阶段有 persona 回复为空或 <20c | 重试 1 次；仍失败则把该 persona 标为 "failed to engage"，继续剩余 |

---

## 5. Cross-reference

- Moderator 如何把本状态机编码为 prompt → 见 `agents/moderator.md` §Procedure
- Manifest 读取与 persona 信号提取 → 见 `agents/moderator.md` §Inputs
- `--from-router` 集成 → 见 `agents/moderator.md` §Constraints
