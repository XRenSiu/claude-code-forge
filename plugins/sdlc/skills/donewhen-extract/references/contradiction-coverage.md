# 出口两检：矛盾检查 + 覆盖检查（纪律③展开）

> 对应 HTML §02-A 纪律③「出口跑矛盾检查+覆盖检查（SMT 式，抄 Kiro；退而用 OpenSpec strict 查缺场景）」。
> 一组 done_when 落卡前，必须证明它**自洽**（不互相打架）且**够全**（没漏掉该管的场景）。

---

## 一、矛盾检查（self-consistency）—— 抄 Kiro 的 SMT 式思路

**问题**：两条 done_when 在同一触发下断言相反结果，则这组规约不可满足——任何产出都注定违反其中一条，
闸门要么永远红、要么自相矛盾地放行。

**机械半（`verify_done_when.py` 跑）**：成对扫描。对任意两条共享同一 `when`（或 given+when）的条款，
若 `then` 的极性相反（一条 SHALL X、一条 SHALL NOT X / SHALL 非X），标记为**疑似矛盾 → reject**。
这是廉价的成对极性扫描，抓得住字面打架。

**语义半（judge/tool call，flagged 不自动判）**：真正的可满足性是 SMT 问题——阈值区间是否相交
（`p95 < 200ms` vs `p95 ≥ 150ms 时降级` 在 150–200ms 区间是否定义良好）、状态前提是否互斥。
能接 SMT 求解器（Z3 式）就把阈值/区间编码进去求 UNSAT；接不上就由 judge 按这张表逐对过：

| 矛盾类型 | 例 | 处理 |
|---|---|---|
| 极性对立 | SHALL 合入 / SHALL 拒绝（同触发） | reject，二选一或加 given 区分 |
| 阈值区间空 | p95 < 100ms 且 吞吐 ≥ 10k/s（物理不可同时） | reject 或拆触发 |
| 状态前提重叠未定义 | WHILE 高峰 SHALL A；WHILE 在线 SHALL ¬A（高峰⊂在线） | 加 given 收窄，消除重叠 |

裁断偏向：**疑似矛盾默认 reject，由人/judge 解除**——放过一对真矛盾，下游闸门会以更贵的方式发现它。

---

## 二、覆盖检查（completeness）—— 退而用 OpenSpec strict 查缺场景

**问题**：一组 done_when 只写了想到的场景，没写到的缝就是 agent 钻空子的地方（例子之间的缝，
HTML §05 陷阱三）。覆盖检查问：**该管的场景，每个都有条款管到了吗？**

**机械半（`verify_done_when.py` 跑）**：

- 每条 `ears_type: event` 的 happy 触发，必须有至少一条 `unwanted` 兄弟（纪律②的机械投影）——
  缺则 reject。
- Territory 的每个 `kpi` aspect（correctness/latency/cost/safety…），若零条款投在其上，flag 为缺场景。

**语义半（OpenSpec strict 式探针，flagged）**：逐维过一遍"这个场景写了吗"：

- **输入维**：空 / 超长 / 类型错 / 越权 / 重复 / 恶意构造 —— 各有 unwanted 条款？
- **时序维**：并发 / 重入 / 超时 / 重试耗尽 / 部分成功 —— 各有定义？
- **资源维**：预算耗尽 / 配额超限 / 依赖不可用 —— 各有降级语义？
- **可逆维**：失败后回滚 / 补偿 —— 高风险动作有 on_violation 式承诺？

缺一个就追问一句"这个场景下 SHALL 什么"，补一条 unwanted 条款，或显式记录"本 Run 不覆盖此场景"
（不假装覆盖过）。

---

## 三、为什么两检都在出口、都先 reject 后放松

- **出口而非入口**：采集与加工阶段允许糙；两检是落卡前的最后一道机械网，把"自相矛盾/有大洞"的
   规约挡在签约之前——签约后再发现，代价是一整个 Run 的返工。
- **先 reject 后放松**：机械半误报可由 judge/人用 waiver 解除（记进 decisions.md）；漏报则下游
   以更贵的方式（G1/G2 翻车、failure_memory 累积、模板返工）才发现。错向严，与 dos-extract /
   invariant-extract 的脚本同纪律。
