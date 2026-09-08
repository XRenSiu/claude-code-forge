# 行为产线 —— eval_case 的三型 + 两套编译器纪律

> 对应 HTML §01①（eval_case 不该只有例子，要有属性兜底）、§01②（Assured 三过滤 + ACH 变异引导）、§02-B 产线②。

---

## 一、三型 eval_case（例子 / 属性 / 变形）

| 型 | 断言什么 | 工具 | 作用 |
|---|---|---|---|
| **例子** | 固定输入 → 固定期望 | Vitest / pytest / Playwright | 钉住具体点 |
| **属性（PBT 子层）** | 一族随机输入上恒成立的不变式 | Hypothesis(Py) / fast-check(TS) | 堵住**例子之间的缝** |
| **变形** | 无 oracle 时：输入变换 X ⇒ 输出变换 Y | 自写变形关系 | 没有标准答案也能判 |

**承重原则（HTML §01①）**：**eval_case 不该只有例子。** 例子之间的缝就是 agent 钻空子的地方——
它把你列举的输入背下来、绕过你没列的。属性是任务级自己的"fitness function 子层"：

- 排序：`∀ 输入. sort(x) 单调 ∧ 是 x 的排列`
- 编解码：`∀ x. decode(encode(x)) == x`（往返）
- 幂等：`∀ x. f(f(x)) == f(x)`
- 守恒：`∀ 转账. Σ余额 守恒`

一组 eval_case 只有例子、无属性/变形兜底 → exit reject（除非显式记录"此处无可表达的属性，因为…"）。

---

## 二、Assured LLMSE 三过滤（编译器之一）

LLM 生成的 eval_case 不能照单全收。每条候选过三道过滤，**过不了就丢**：

1. **能编译**：语法/类型/导入正确，能被测试框架收集。编译不过 → 丢。
2. **能稳过**：在**已知正确**的产物上稳定通过（不 flaky、不假阴）。在正确产物上红 → 这条断言自己错 → 丢。
3. **能抓新故障**：至少能杀掉一个注入的小故障（见 §三 ACH / 与 calibrate mutation 镜面同源）。
   一个 mutant 都杀不掉 → 它没咬住任何行为，是装饰 → 丢。

三道全过才入集。**注意**：第 3 道的"能抓"在生成期是*目标*；它**真**咬住的证明是 calibrate 的
mutation score 镜面（杀死率达标）。spec-compile 朝这个目标生成，calibrate 验收。

---

## 三、ACH 变异引导生成（编译器之二）

不要等故障发生才补断言。**从"我担心哪类故障"反向造断言**：

```
我担心的故障类 →（造一族 mutant：== → !=、+ → -、漏 null 检查、边界 off-by-one）
            → 生成被证明能杀掉这族 mutant 的断言
            → 这些断言精确覆盖"下一次失败会打到的地方"
```

`failure.memory` 里每个坏样本 = 一个**天然 mutant**（HTML §03 / calibrate 镜面①）：把它转成
"绝不能再让这个坏输出过"的断言 + mutant，电池就长在下一次会翻车的地方。这是复利的行为侧引擎：
一次失败 → 一个 mutant 族 → 一组能杀它的断言 → 电池长大，棘轮收紧。

---

## 四、落点与 calibrate 交接

- 落 dos.yaml `verify_g1` commands（跑测试）+ `MemoryAsset:eval_case`（入集回归 + 评估者上岗考试基准）。
- 每条标 `calibration_pending: true`——**eval_case 是否承重由 calibrate 的 mutation score 证明**
  （能 pass 的 eval_case ≠ 承重的 eval_case，HTML §03）。spec-compile 出电池，calibrate 出杀死率。
- 棘轮：新故障类 → 新属性/新 mutant → 电池只增不减（接 `ratchet`）。
