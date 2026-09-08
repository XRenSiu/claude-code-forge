# 失败模式与反模式 —— 校准会先在哪崩

> 对应 HTML §05 四判据 + 三陷阱。出元闸门 verdict 前当 checklist。

---

## 三个自带的失败模式

### ① 把绿色报告当闸门（装饰冒充承重）

最常见、最危险：eval_case 全绿就上线、rubric 出了分就上线，从不问"杀得掉 mutant 吗""复现得出参考解吗"。
这是 HTML §05 陷阱一：把"测试通过"当唯一信号。

→ **对策**：元闸门四判据，缺一不可上线。绿色 ≠ 承重；只有 mutation score / agreement 让尺子真咬住。

### ② 泄漏的 holdout（认证变剧场）

把本该藏起来的 holdout 拿去当 few-shot、注入 prompt、或编译期展示了一眼。一旦泄漏，holdout 认证的
"执行者看不见"前提破了，整套认证失效，却还在报告里显示绿。

→ **对策**：holdout 绝不进任何 executor 通道；`calibration_report.yaml` 显式 `isolation_attested` +
人确认未暴露。泄漏即作废，重切新 holdout。

### ③ 为放一个标准而下调硬线（刷元闸门）

α 差一点就把 0.80 调成 0.75、mutation 阈值差一点就下调——这是对元闸门本身的 reward hacking。

→ **对策**：硬线（α≥0.80 / mutation 阈值）**只许棘轮收紧，绝不下调**。放不过就退回 spec-compile 重编尺子，
不是改尺子的及格线。

---

## 承重铁律：永远不要相信一把没校准的尺子

> 没有 mutation score / 没有 agreement / 没有 holdout / 没有隔离 ⇒ 这把尺子未经校准 ⇒ **禁止上线**。

这是 calibrate 的全部存在理由（HTML §01⑤）。它不判产出，它判"判产出的东西"够不够格——唯一的元闸门。
落卡不是越积越多的绿报告，是越积越多的、被证明杀得掉故障、复现得出参考解、带 holdout、隔离可审计的标准。

---

## 边界 / 越权反模式（别把这把刀做成别的刀）

- **别写规约**：常驻不变量/本次验收 是 invariant-extract / donewhen-extract 的活。本刀校尺子，不立法。
- **别编译**：出 eval_case / rubric 是 spec-compile 的活。本刀**消费**它的产物（calibration_pending 的标准），
  证明它们承重，不自造尺子。
- **别改 rubric/eval_case 内容**：agreement/mutation 指出哪维/哪故障没覆盖，退回 spec-compile 重编；
  calibrate 出证据，不动尺子本身。
- **别替代签字**：rubric 是闸门资产只能人签（R002）；元闸门 verdict 是签字的**前置证据**，不是签字本身。
- **别和运行时 calibration 问句混为一谈**：`calibration.resolved`（evaluator_fault / standard_unclear）是
  运行时事件、本刀的**输入信号**；本刀是离线元闸门，不是那个问句。
- **别静默咽掉存活 mutant**：每个杀不掉的都是一道空隙、一条待写 eval_case，逐个落账（no silent caps）。

---

## 一处理论诚实（引 PIT/Stryker/Krippendorff/CDRRM/SpecBench/RDI 时的措辞）

变异工具、Krippendorff α、CDRRM 丢弃规则、SpecBench/Berkeley RDI 的证据——本刀**借这些方法与对照证据**
做"标准的标准"。写 decisions.md 时诚实表述为"借 X 度量/证据做元闸门校准"，不要说成"本刀=X"。
本刀的独立定位：**两级共用的命门 / 唯一的元闸门**——两面镜子（mutant 校 eval_case、参考解校 rubric）
+ 两条非协商项（holdout、隔离），判一个标准有没有资格上线。
