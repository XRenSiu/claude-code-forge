# 镜面② rubric → agreement matrix（责任级命门）

> calibrate 的承重判断面之二。对应 HTML §02-C 镜面②、§05 ☐2。

---

## 一、为什么需要它（参考解校 rubric）

一份 rubric 能跑、能出分，不代表它判得对。校准 rubric 的办法：**拿它去复现已知裁决**。

> 准备一组**参考解**：已由人工标定了好/坏裁决的样本（黄金集）。
> 让 rubric 在这组样本上独立跑出裁决，与人工标签比对一致性。
> **不一致的 rubric 集直接丢（CDRRM）**——判出 0% 或忽高忽低，错的是闸门，不是 agent。

---

## 二、部署硬线：Krippendorff α ≥ 0.80

一致性用 **Krippendorff's α** 度量（容缺失、多标注者、可处理二元/序数），部署硬线 **α ≥ 0.80**。

- 这正是 dos.yaml `config.evaluator_exam.min_agreement = 0.8`（+ `min_cases: 5`）那条线——calibrate
  是它的离线起草/验收侧，运行时 evaluator-exam 是上岗考试侧，同一条线两处用。
- α < 0.80 → **禁止该 rubric_version 上线**（元闸门 fail），把不一致的维度退回 spec-compile 重编
  （多半是某维不够二元、或证据绑定太松）。
- 硬线只许棘轮收紧（0.80 → 0.85…），绝不为放一个 rubric 过而下调（下调 = 刷元闸门）。

---

## 三、与运行时 calibration.resolved 的接点

代码里已有的 `calibration.resolved` 事件（人改判后答 `evaluator_fault` vs `standard_unclear`）是镜面②的
**运行时信号源**：

| 运行时答案 | 含义 | 喂给谁 |
|---|---|---|
| `evaluator_fault` | 评估者漏看/判错，但标准本身没问题 | evaluator-exam（上岗考试，重训评估者） |
| `standard_unclear` | 标准本身不清/有歧义 | **calibrate**：把该样本纳入黄金集，重跑 agreement，收紧 rubric |

`standard_unclear` 累积 = "这把尺子该重校了"的最强信号。calibrate 是离线元闸门，运行时问句是它的输入。

---

## 四、证据绑定与二元（与 spec-compile 判断线呼应）

agreement 跑不高，常因 rubric 维度本身不合格：

- **非二元**：连续分让标注者各打各的，α 自然低。→ 退回 spec-compile 拆成二元维。
- **无证据绑定（RRD）**：判定不引可定位证据，复现性差。→ 退回补 `evidence_ref`。

calibrate 不改 rubric（那是 spec-compile 的活），但 agreement 矩阵指出**哪一维**在拉低一致性，
精确导引重编。

---

## 五、出闸判据

- `kind: rubric` 的标准：`agreement_alpha` 必须存在且 ≥ 0.80（硬线，只许棘轮收紧）。
- 达标 → 记入 `MemoryAsset.calibration.agreement_alpha`，交**人签**（R002，rubric 是闸门资产）+ 激活。
- calibrate 出 agreement 证据，签字仍走人——元闸门是签字的**前置**，不是替代。
