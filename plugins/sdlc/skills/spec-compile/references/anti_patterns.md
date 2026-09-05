# 失败模式与反模式 —— 编译会先在哪崩

> 对应 HTML §05 三陷阱。落 manifest 前当 checklist。

---

## 三个自带的失败模式

### ① 往上路由（把便宜的确定性留在桌上）

最隐蔽、最贵的缺陷：一条本可被静态判（①）或测试判（②）**完全**裁死的规约，被放到了更高的概率性线上。

- "core 不许 import node 内置" → 不该跑测试、更不该让模型看，一条 Semgrep/dep-cruiser 规则（①）。
- "p95 < 200ms" → 不该让 LLM 判"快不快"，跑压测断言（②）。

→ **对策**：每条规约先判可判性，**先问"能不能再往下推一格"**，推不动才停。exit 重新核验海拔，不靠自觉。

### ② 例子-only 行为电池（例子之间的缝）

只写例子、不写属性/变形。agent 背下你列的输入，绕过你没列的——HTML §05 陷阱三、§01①。

→ **对策**：每组行为电池配属性（PBT 子层）或变形兜底；表达不出属性时显式记录"为什么此处无属性"。
钉点之间的缝靠属性堵。

### ③ 自由 prose 的 G2（未编译的 LLM-judge）

把残差写成"给模型的一段话：判断这个好不好"。这是把"模型说好"当信号（HTML §05 陷阱一的判断侧变体），
漂移、可刷、不可审计。

→ **对策**：拆正交维度、每维二元 + 证据绑定（RRD）、PAJAMA 编译成程序；让模型只在框死的槽里答，
绝不自由发挥。

---

## 承重铁律：编译 ≠ 认证（calibrate 才承重）

spec-compile 出的每个标准都 `calibration_pending: true`。

> **能 pass 的 eval_case ≠ 承重的 eval_case；写出来的 rubric ≠ 校准过的 rubric。**

直接把未校准的标准挂上闸门 = 一份会被刷绿的装饰报告（HTML §05）。eval_case 的承重由 calibrate 的
mutation score 证明，rubric 的承重由 agreement(α≥0.80) 证明，且要有 holdout。**spec-compile 出尺子，
calibrate 证明尺子对**——这条边不可省。

---

## 边界 / 越权反模式（别把这把刀做成别的刀）

- **别写规约**：常驻不变量 是 invariant-extract、本次验收 是 donewhen-extract 的活。本刀消费它们的输出，不自造规则。
- **别做校准**：mutation score / agreement / holdout 是 calibrate 的活。本刀产尺子，不产"尺子对的证明"。
- **别跑闸门**：verify_g1 / review_g2 的运行时是 daemon 的活。本刀产标准，运行时跑标准。
- **别绕过签字**：G2 rubric 是闸门资产，只能人签（R002）；本刀提案，签字走 seam。
- **别工具先行**：原则先于工具；fitness fn 溯到规则而非 ArchUnit 的功能表；阈值只棘轮收紧不回弹。
- **别让 G2 读执行上下文**：R001 隔离；编出会读执行会话的 G2 标准等于没有评估。

---

## 一处理论诚实（引 Assured / ACH / PAJAMA / RRD 时的措辞）

Assured LLMSE 三过滤、Meta ACH 变异引导、PAJAMA 程序化、RRD 证据绑定——本刀**借这些工业样本的算法形态**
做按可判性的编译。写 decisions.md 时诚实表述为"借 X 的形态做 spec→standard 编译"，不要说成"本刀=X"。
本刀的独立定位：**两级共用的编译器**，把任一规约按可判性下推三产线，止于"出尺子"，把"证明尺子对"交给 calibrate。
