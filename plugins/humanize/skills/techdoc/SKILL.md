---
name: techdoc
description: "Use when you need a technical proposal, design doc, ADR, postmortem, or decision memo written from a brief so that it reads the way a senior engineer writes one — opens with the triggering incident and a number, states the decision in one sentence, kills the obvious alternatives with specific reasons, lists consequences including the bad ones, spells out rollout/rollback, ends on open questions — instead of the AI default (background paragraph, bulleted benefits, balanced options, 'comprehensive testing', 综上所述). 写技术方案 / 写设计文档 / 写 ADR / 写复盘 / 出个方案 / design doc / RFC / proposal. Chinese or English. NOT for API reference, README installation sections, or user manuals (those are tables and steps); NOT for polishing an existing draft (use /humanize)."
argument-hint: "<一句到一段的 brief，或 brief 文件路径> [--genre proposal|design|adr|postmortem|memo] [--reader <谁读>] [--materials <路径…>] [--voice <voice.md>] [--lang zh|en] [--out <路径>]"
version: 0.1.1
user-invocable: true
---

# techdoc

输入一个 brief（要解决什么、已知什么、给谁看），输出一份**呈现资深工程师方案形状**的文档，
并且已经过 `/humanize` 的三道闸门（humanlint / factdiff 对 brief / cold-reader）。

## 缺口（deletion 测试）

撤掉本 skill，让引擎"写个缓存优化方案"，它交出的是 `../humanize/fixtures/ai-zh.md` 那种东西：
背景段零事实、四条加粗目标、首先其次最后、"可能面临一定风险"、综上所述。不是引擎不会写方案，
是它的默认形状是**综述**而不是**决定**。缺的是：

- **φ（产物序）**：一份方案必须呈现的顺序与必有件——触发事件、一句话决定、被杀掉的替代、全部后果、
  灰度回滚、未决问题。这是产物性质，`scripts/verify_techdoc.py` 在出口检。
- **Σ（关于读者）**：方案写给两年后接手的新人和今天来挑刺的评审，不是写给审批人；
  读者从不该感到意外——每个反对意见在他想到之前已被回答。
- **γ**：写完必须过 `/humanize` 的闸门，且事实只能来自 brief 与 materials。

## Σ：一份方案的形状

十个动作、体裁变体、语气规则、"AI 默认 → 资深工程师"对照表，全部在 `references/skeleton.md`。
写第一份前先读它和 `../humanize/fixtures/human-zh.md`（或 `human-en.md`）——先见过对的样子。

核心形状（proposal / design）：

1. 触发事件 + 具体痛点，一段，带日期 / 数字 / 专名。
2. 决定，一句话，主动语态；附预算或胃口。
3. 目标 / 非目标（唯一该用 bullet 的地方）。
4. 设计：先全貌后细节，只写影响取舍的部分；一个有名有姓的走查场景。
5. 为什么是它而不是那两个明显的替代——每个死于一个具体原因；再加一段"为什么不该做"。
6. 后果，全部；每个风险有触发条件、负责人、兜底。
7. 灰度、回滚、监控。
8. 未决问题 + 尝试性答案；什么证据会推翻这个决定。

ADR 只要 1 / 2 / 5 / 6；postmortem 是时间线 + 根因 + 为什么防线没拦住 + 带 owner 与日期的行动项；
memo 全散文、目标之外禁 bullet。

**事实的三种来路**（沿用 psl 的诚实公理）：brief 与 materials 里有的 → 用；领域常识（"标准 SQS 不保序"）→ 用并可被查证；
两者都没有但方案必须有的（当前 QPS、故障日期、预算）→ **问，或标 `[需核实：…]`**。没有第四种来路。
一份带 `[需核实]` 的方案比一份数字全是编的方案更像人写的——人不会编自己系统的 QPS。

## φ：什么算写对了

- `verify_techdoc.py` verdict ≠ reject（形状齐全：第一段有锚点、前 3 段有决定句、有被否决的替代、有未决 / 下一步 / 回滚、无总结式收尾）。
- 每个替代方案的死因是具体的（数字、先例、改动面），不是"复杂度较高"。
- 每个风险三件套：触发条件、负责人（或角色）、兜底动作。
- 至少一个非目标是"读者会合理以为你要做"的事。
- 走查场景有具名主体和真实量级的数值（来自 brief / materials，或标 `[需核实]`）。
- `/humanize` 的全部 φ 同时成立（见 `../humanize/SKILL.md`）：文档层 / 段落层 / 句子层 / 事实层 / 语域层。
- factdiff 以 **brief + materials** 为 source：方案里的每个数字在来源里有，或被标 `[需核实]`。

## Π：原语

- `scripts/verify_techdoc.py <doc> [--genre …]`：产物序预门；reject 五条、flag 五条，见脚本 docstring。
- `../humanize/scripts/humanlint.py`、`../humanize/scripts/factdiff.py`、`cold-reader` agent：见 `../humanize/SKILL.md` 的 Π 节，用法相同。
- `references/skeleton.md`：十动作 / 体裁表 / 语气规则 / 对照表。
- `references/example.md`：一个 brief → 方案的完整推导（含 verify / humanlint / cold-reader 输出），先读再写。
- 有证据的生成技巧：先写每段的主张句骨架（一段一句，第一句就是答案），确认骨架顺序符合产物序，再展开成散文；
  开头段生成 5 个候选并丢掉概率最高的；有 `voice.md` 时以 completion 方式续写。

## γ：门

- **形状门**：`verify_techdoc.py` reject → 补缺件后重跑；不交付 reject 的稿。
- **事实门**：`factdiff.py <brief+materials 合并文件> <doc>`；ADDED 的数字必须能在 brief / materials / 领域常识里指出来源，否则改为 `[需核实]`。
  引擎不得给自己 `--allow-add`。
- **冷读门**：cold-reader 隔离调用，只给文档 + reader + genre；needs_revision → 按 worst_three 修 → 再一轮；封顶 2 轮；两轮未过照常交付并明说。
- **提问协议**：需要用户补的承重事实（当前量级、故障日期、预算、谁负责）攒成**一条**消息问完，每问附推荐答案与字母选项；
  用户不在场或答"直接写" → 全部 `[需核实]` 照常交付。不问不承重的槽（例如具体的告警阈值可以先给推荐值标 `[建议值]`）。
- **交付硬契约**：无论闸门结果如何，最终必须交付方案文件 + 报告。"信息不足无法写方案"是禁止输出。

### 失败分支

| 触发 | 征兆 | 分支 |
|---|---|---|
| brief 只有一句话、没有任何数字 | 第一段写不出锚点 | 问一次（攒成一条）；不答 → 第一段用 brief 里的事件描述 + `[需核实：日期/量级]`，verify 会 flag 不会 reject |
| brief 已经给定了方案，没说问题 | 找不到触发事件 | 反推：问"这个方案要解决的那件事是什么"；不答 → 把方案的目标当问题写，并在未决问题里明说"问题陈述是反推的" |
| 需求是确定性的（导出 6 列 CSV） | 没有取舍可写 | 明说"这里不需要方案文档，一段说明 + 验收即可"，交付一段；不硬凑十动作 |
| 替代方案只有一个或没有 | ALTERNATIVE 缺 | 写"考虑过的另一条路是什么都不做 / 保持现状，代价是…"——现状永远是一个替代 |
| verify 与 humanlint 冲突（例如目标节 bullet 让 bullet_ratio 偏高） | 两边都 warn | 目标 / 非目标节的 bullet 合法；其余节展开；报告写明 |
| cold-reader 两轮仍在第 1 段跟丢 | lost_at 在开头 | 通常是触发事件写成了背景；用 brief 里最具体的那个事实重写第一段，再交付 |
| materials 里有互相矛盾的数字 | factdiff 两个都算来源 | 两个都写出来并标"来源冲突：A 说 …，B 说 …，按 A 计算"，进未决问题 |
| 用户要的是英文方案但 voice.md 是中文样文 | 语言不匹配 | 只取节奏数据与忌口，不取正例；报告写明 |

## 交付物

- 方案文件：`--out` 或 `<brief 同目录>/<决定名词短语>.md`；标题是决定，不是话题。
- 报告（附在文末）：verify_techdoc 输出、humanlint 前后指数、factdiff 结果、cold-reader 轮次与判决、`[需核实]` 清单、
  推断值（reader / genre / lang）、问过用户的问题与答案。

## 绝不（不可豁免）

- **绝不编造系统数据**——QPS、延迟、故障日期、成本、人日。不在来源里的数字只能是 `[需核实]` 或明确标注的 `[建议值]`。
- **绝不写没有触发事件的方案**——"随着业务发展"开头的稿不交付。
- **绝不列一排方案"各有优劣"而不推荐**——必须选一个，其余各给一个具体死因。
- **绝不只写正面后果**。
- **绝不用"进行充分测试 / 制定完善的应对策略 / comprehensive testing"代替具体的风险兜底**。
- **绝不写总结段**。
- **绝不在主对话里自评"写得挺像资深工程师的"**——评审只承认 verify / factdiff / 隔离的 cold-reader。
- **绝不因信息不足拒绝交付**——改为 `[需核实]` 后照常交付。

## 接线

- `/humanize`（本插件）：本 skill 的出口闸门就是它的闸门；已有草稿直接用它。
- `/voice-profile`（本插件）：有 `.humanize/voice.md` 时自动加载。
- `looper` 的 `/psl`、`ai-dlc` 的 `/issue`（如果安装了）：体验性需求先写 PSL 再写方案；方案里的验收可直接引用 issue 的 done_when。缺席不阻塞。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`。`verify_techdoc.py` 在四份样本上冒烟（AI 样本 REJECT、人写样本 PASS）；
"带本 skill 写出的方案是否比不带的更常通过 cold-reader"未在留出 brief 上测。
