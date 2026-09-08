# 判断产线 —— 把"让模型判"编译成程序（G2）

> 对应 HTML §02-B 产线③、keyline 末句「PAJAMA 把『让模型判』也编译成了程序」。

---

## 一、它是残差，不是默认

产线③ 只接**前两线吸干确定性后剩下的语义残差**——真正需要"权衡"的部分。绝大多数规约不该到这里：
能静态判（①）/ 能跑测试判（②）的都被下沉了。**先问"能不能再往下推一格"，推不动才上 G2。**

把本可下沉的东西丢给 G2，是 HTML §05 陷阱一（把"测试通过"当唯一信号的反面：把"模型说好"当信号）。
G2 越窄越好——它只该判机器判不了的那一小撮。

---

## 二、分析式 per-dimension rubric（二元 + 证据绑定，RRD）

不要写"整体打个分 1–10"。把残差**拆成正交维度**，每维：

- **二元**：满足 / 不满足，不要连续分（连续分是 LLM-judge 漂移与被刷的温床）。
- **证据绑定（RRD：Rubric-Referenced Decision）**：判定必须引一条**可定位的证据**（file:line / 测试名 /
  diff 片段）。无证据的判定不算判定——它无法被复利，也无法被审计。

反例 → 正例：

| 自由 prose（坏） | 二元 + 证据（好） |
|---|---|
| "代码质量高吗？" | "函数 F 有断言行为 B 的测试吗？证据：test/foo.test.ts:42" |
| "文档够清楚吗？" | "每个 public 导出在 API.md 有签名条目吗？证据：缺失项列表" |
| "改动安全吗？" | "新增外部输入点都过了校验吗？证据：未校验入口的 file:line 列表" |

---

## 三、终态：PAJAMA 编译成可执行程序

rubric 的终态不是"给 LLM 的一段话"，而是 **PAJAMA 把每维编译成一段可执行程序**，让 LLM-judge 退场：

- 每维 = 一个可跑的判定子程序（grep/AST 查/跑一个针对性断言/查证据是否存在）。
- 程序输出 = 二元 + 它引用的证据路径。
- 残留真需要语言理解的维度（少数），程序把"问什么、看哪段证据、可接受答案是什么"固化下来，
  LLM 只在被框死的槽里回答，而非自由发挥——**让模型判也编译成了程序**。

落 dos.yaml `MemoryAsset:rubric_version`（`signed_by` 人签，R002）+ `Verdict.review_rubric_ref`；
G2 `Verdict.reasons` 按 done_when 的 REQ-ID 逐条对应（dos 0.1.13）。

---

## 四、R001 隔离（G2 标准的硬约束）

spec-compile 编出的 G2 评判程序必须满足 R001，否则它根本不构成评估：

- **独立进程/会话**：评判者不与执行者同会话。
- **只读快照**：对执行 worktree 只读；输入只含**产出 + rubric**，不含执行过程/思维链。
- **cross-vendor**：领地开 `cross_vendor_review` 时，evaluator 与 executor 必须不同供应商。

编出会读执行上下文的 G2 标准 = 评估装置被执行者污染 = 没有评估（Berkeley RDI，HTML §05 ☐4）。

---

## 五、calibrate 交接

rubric 是否承重由 calibrate 的**镜面②**证明：参考解跑出已知裁决，rubric 复现一致性
**Krippendorff α ≥ 0.80**，不一致的 rubric 集直接丢（CDRRM）。spec-compile 出 rubric 程序，
calibrate 出 agreement——`calibration_pending: true` 直到 C 通过。
