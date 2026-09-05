# 两条非协商项：holdout + 隔离（四不可破判据合一）

> 对应 HTML §05 ☐3、☐4，与三个会让回路被 hack 的陷阱。两面镜子之外，这两条是元闸门的另两根栏杆。

---

## 一、黄金回归集（golden regression set）

calibrate 沉淀一个只增不减的**黄金集**：每条来自一次真实裁决或一个杀不掉的 mutant，带期望态。
它同时 gate 两样东西（HTML §02-C 纪律①）：

- `rubric_version`（用 agreement 度量，镜面②）
- `eval_case_version`（用 mutation score 度量，镜面①）

两级版本升级被**同时**门住——尺子换新版，必须在黄金集上重证承重。

---

## 二、holdout：执行者永远看不见的一块（☐3）

黄金集必须切出一块 **holdout**：**agent 永远看不到、只在 gate 时才跑。**

> 否则任何模型都能刷满可见测试集，而真实合规在绿色报告底下一路下滑（SpecBench 实测，HTML §05 陷阱一）。

holdout 纪律（非协商，`anti_patterns.md` 再述）：

- 绝不注入任何 executor prompt、绝不当 few-shot、绝不在编译期展示。
- 只在元闸门校准时、或线上 G1 跑回归时才触碰。
- 泄漏 holdout = 整个认证变成剧场——所以 `calibration_report.yaml` 要 `isolation_attested` + `holdout_ref`
  显式记录，并由人确认"确实没暴露过"。

---

## 三、G2 隔离：评估者与执行者物理隔离（☐4）

> 除非评估装置与被评估实体**完全隔离**，否则没有评估可信（Berkeley RDI）。隔离不是洁癖，是评估能否成立的前提。

落 dos.yaml R001 三层 + cross-vendor：

- **独立进程/会话**：评估者不与执行者同会话；agreement 跑测也不得复用执行者会话/模型。
- **只读快照**：对执行 worktree 只读；输入只含产出 + rubric，不含执行过程/思维链。
- **cross-vendor**：领地开 `cross_vendor_review` 时，evaluator 与 executor 必须不同供应商。
- **变异测试本身就是对评估装置的对抗压测**——镜面①不只测 eval_case，也在压测"这套评估能不能被骗过"。

---

## 四、四不可破判据（一张 checklist）

一个标准要上线，四条全过，缺任何一条都是"会被刷绿的装饰"（HTML §05）：

| # | 判据 | 度量 | 不达标的含义 |
|---|---|---|---|
| ☐1 | eval_case 杀得掉 mutant | mutation score ≥ 阈值 | eval_case 是装饰，不是 agent 弱 |
| ☐2 | rubric 复现得出参考解 | Krippendorff α ≥ 0.80 | 错的是闸门，不是 agent |
| ☐3 | 有执行者看不见的 holdout | holdout_ref 非空 + 未泄漏 | 可见集会被刷满，真合规下滑 |
| ☐4 | G2 评估者与执行者隔离 | isolation_attested + (领地开则)cross-vendor | 没有隔离就没有评估 |

四条都过 → 得到的不止"一份能跑的规约"，而是**一台带命门、带 holdout、会自校准的编译器** + 一套证明
承重的变异回归集——这三样才复利。eval_case 与 rubric 本身会折旧；那台编译器才是资产（HTML §05 末）。

---

## 三个陷阱 · 一一对策（HTML §05）

- **陷阱一：把"测试通过"当唯一信号。** → holdout + 变异压测，让"通过"不再等于"承重"。
- **陷阱二：评估者顺手复用执行者的上下文/模型。** → G2 物理隔离，证据路径独立可审计。
- **陷阱三：eval_case 只写例子、不写属性。** → spec-compile 补 PBT 子层；calibrate 用 mutation 验收它真堵住了缝。
