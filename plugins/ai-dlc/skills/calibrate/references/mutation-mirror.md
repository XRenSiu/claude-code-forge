# 镜面① eval_case → mutation score（任务级命门）

> calibrate 的承重判断面之一。对应 HTML §02-C 镜面①、§03③、§05 ☐1。

---

## 一、为什么需要它（能 pass 的 eval_case ≠ 承重的 eval_case）

一组 eval_case 全绿，可能一个真故障都抓不住——它只覆盖了 happy 路径、断言太松、或测的是无关紧要的东西。
**绿色不等于承重。** mutation score 是 eval_case 的校准指标：

> 往**已知正确**的产物里注入一个小故障（mutant），跑 eval_case：
> **杀得掉**（有用例因此变红）= 断言真咬住了行为；
> **杀不掉**（全绿照旧）= 一道闸门空隙——这个故障能溜过你的整套测试。

杀死率 = 被杀 mutant / 总 mutant。**杀不掉的每一个都是一道空隙，要标出来、不能咽掉**（§四）。

---

## 二、工具表

| 语言 | 变异工具 |
|---|---|
| JVM | `PIT`（pitest） |
| TS/JS | `Stryker` |
| Python | `mutmut` / `cosmic-ray` |

注入的故障类（小而典型）：`== → !=`、`+ → -`、`< → <=`、删一行守卫、漏 null 检查、
边界 off-by-one、`&& → ||`、返回常量、删副作用调用。

---

## 三、failure.memory 里每个坏样本 = 天然 mutant

不必只靠工具自动注入。**`failure.memory` 里每条坏样本，就是一个现成的、真实发生过的 mutant**：

```
一条 failure_memory（"上次这个坏输出溜过了闸门"）
   → 注入回产物 / 构造成"绝不能再过"的反例
   → 跑当前 eval_case：杀得掉吗？
       杀不掉 → 这正是上次翻车的那道空隙还开着 → 必补一条 eval_case
```

这是镜面①与复利回路（HTML §04⑨）的接点：真实失败是最高质量的 mutant，因为它证明过自己能造成损害。
ACH 变异引导（spec-compile 行为线）从"我担心哪类故障"造 mutant 族；calibrate 验收"真杀得掉吗"。

---

## 四、承重纪律：杀不掉的 mutant 必须落账（no silent caps）

每个存活（杀不掉）的 mutant 都是一道闸门空隙。**铁律：逐个落账，禁止静默截断。**

- 落 `calibration_report.yaml` 的 `surviving_mutants[]`：mutant 描述 + 它溜过的位置 + 该补的 eval_case。
- 每个存活 mutant → 一条待写的 eval_case（棘轮：黄金集只增）。
- 若因预算只跑了一部分 mutant，**显式 log 跑了多少、漏了多少**——静默只跑一部分会被读成"全覆盖"，
  而其实没有（HTML §05 ☐1：杀死率不达标 = eval_case 是装饰，不是 agent 弱）。

---

## 五、出闸判据

- `kind: eval_case` 的标准：`mutation_score` 必须存在且 ≥ 阈值（默认 0.7，硬线只许棘轮收紧）。
- 不达标 → **禁止该 eval_case 集上线**（元闸门 fail），把 gap 退回 spec-compile 补电池。
- 达标 → 记入 `MemoryAsset.calibration.mutation_score`，交签字/激活 seam。
