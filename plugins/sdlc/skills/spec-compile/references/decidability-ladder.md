# 可判性阶梯 —— 三产线按可判性分流（不按层级）

> spec-compile 的承重判断面。对应 HTML §02-B、§03 编译行、§04③、keyline。

---

## 〇、第一性原理（keyline）

> **能静态判就别跑，能跑测试判就别让模型判，能让模型判就别让人判——而 PAJAMA 把"让模型判"也编译成了程序。**

每条规约（常驻不变量 / 本次验收 done_when）都被尽量往**下**推。选哪条产线，看的是**这条怎么可判**，
不是它来自责任级还是任务级。**分流轴 = 可判性，不是层级。**

```
            可判性阶梯（越往下越便宜、越全、越难被 hack）
  ┌─────────────────────────────────────────────────────────┐
  │ ① 结构判  静态读产物即可裁，不跑   → fitness function → G1 │
  │ ② 行为判  跑产物喂输入才可裁       → eval_case        → G1 │
  │ ③ 判断判  前两线吸干后的语义残差   → 评判程序          → G2 │
  └─────────────────────────────────────────────────────────┘
   往上路由（低线能判却放到高线）= 承重缺陷：把便宜的确定性留在桌上，把可被钻空子的面摊大。
```

---

## 一、产线① 结构判 → fitness function（G1）

**何时**：规约能靠**静态读产物**裁断——形状、依赖方向、禁用 API、分层、命名、文件位置。
多为责任级 常驻不变量的主路。

**工具表**：`ArchUnit`(JVM) / `dependency-cruiser`·`ts-arch`(TS) / `OPA-Conftest`(策略/IaC) /
`Semgrep`(跨语言模式)。落 dos.yaml 的 `verify_g1` kind=commands。

**纪律**：
- **原则先于工具**：先从规约里读出"要禁什么/保什么"，再挑能表达它的工具——不是因为 ArchUnit 在手就
  把规约削成 ArchUnit 能跑的形状。工具是末端，规约是源头。
- **容差棘轮**：阈值只能单调收紧，接 `ratchet`。今天允许 3 处依赖倒置、明天就该是 2 —— 不回弹。

**落点**：`verify_g1` commands。`calibration_pending: true`——fitness fn 也要被 calibrate 验证
（注入违例产物，确认它真拦得住），不是写出来就承重。

---

## 二、产线② 行为判 → eval_case（G1）

**何时**：规约要**跑产物喂输入**才可裁——给定输入，断言输出/状态/副作用。多为任务级 本次验收 done_when 主路。
详见 `references/behavioral-line.md`。

**工具表**：`Vitest`·`pytest`(单元) / `Playwright`(e2e) / `Hypothesis`·`fast-check`(属性/PBT)。

**三型（不是只有例子）**：
- **例子**：固定输入→固定期望。钉点。
- **属性（PBT 子层）**：对一族随机输入恒成立的不变式（如"排序后单调"、"编解码往返一致"）。**钉点之间的缝。**
- **变形**：无 oracle 时，断言"输入变换 X ⇒ 输出变换 Y"（如"翻译再翻译回来语义不变"）。

**落点**：`verify_g1` commands + `MemoryAsset:eval_case`。同样 `calibration_pending`——eval_case 是否
承重由 calibrate 的 mutation score 镜面证明。

---

## 三、产线③ 判断判 → 评判程序（G2）

**何时**：**前两线吸干确定性后的语义残差**——只有需要"权衡"的才上 G2，且不是交给自由发挥的 LLM-judge，
而是编译成程序。详见 `references/judgment-line.md`。

**形态**：分析式 per-dimension rubric（每维二元 + 证据绑定，RRD）→ 终态 **PAJAMA 编译成可执行程序**，
让 LLM-judge 退场。落 `MemoryAsset:rubric_version`（人签，R002）+ `Verdict.review_rubric_ref`。

**铁律（R001）**：G2 评判程序独立于执行会话，对 worktree 只读，输入只含产出 + rubric；
领地开 cross_vendor 时换供应商。spec-compile 不得编出会读执行上下文的 G2 标准。

---

## 四、海拔违规（exit 重新核验，不靠自觉）

| 违规 | 例 | 判 |
|---|---|---|
| 结构判放到行为线/判断线 | "禁止 core 引 node 内置模块"写成跑测试 / 让模型看 | reject，下沉到 ①（Semgrep/dep-cruiser 一条规则） |
| 行为判放到判断线 | "p95<200ms"交给 LLM-judge"感觉快不快" | reject，下沉到 ②（跑压测断言） |
| 残差硬塞进 ①② | "这段文案是否得体"硬编码成正则 | 接受它是 ③ 残差，但仍要编译成 rubric 程序，不留自由 prose |

往上路由是最隐蔽的浪费：它让一条本可被静态/测试**完全**判死的规约，落到一个**概率性**的高线上，
既贵又给 reward-hacking 留面（HTML §05 陷阱一）。**先问"能不能再往下推一格"，推不动了才停。**
