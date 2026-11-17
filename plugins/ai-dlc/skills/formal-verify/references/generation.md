# AI 生成协议：规则与模型

AI 写规则、AI 建模是这条流程的必经阶段。这份文件规定 AI 怎么写，以及写出来的东西怎么被检查。
核心只有一句：**生成者不检查自己。** 生成者至少两个且互不可见，比较由脚本做，裁决由人做，审阅由一个全新上下文、只读的审阅者做。

## 0. 派发方式

| 宿主 | 怎么做到“互不可见” |
|---|---|
| Claude Code | 用 Agent 工具分别派发 `rule-formalizer` / `model-builder` / `formal-reviewer`（插件 `agents/` 下的定义）。**每次派发一个新实例**，提示里只给允许读的路径和本次的输出目录，不要把别的候选内容贴进提示 |
| 没有子 agent 的宿主（Codex 等） | 每个候选开一个新会话，提示词照抄对应 agent 文件的正文 |
| 有跨供应商模型 | 把两个候选分给不同供应商：同源模型的盲区相同，分歧检测会失灵（同 acceptance-fleet 的跨供应商分配）；分不到就在 notes 里写明是同源模型 |

派发者（运行 `/formal-verify` 的主 Agent）只做三件事：分配目录、跑 `fv` 命令、把议程交给人。它**不改**候选，也不替人裁决。

## 1. 需求清单（G-1）

第一个 `rule-formalizer` 先写 `requirements.yaml`：

```yaml
schema_version: 1
kind: fv-requirements
id: <feature>
sources: [{id: prd, path: requirements.md}, {id: dw, path: ../../done_when.yaml, kind: done_when}]
requirements:
  - {id: R1, text: "<一句话>", source: {doc: prd, quote: "<原文逐字一段>"}}
  - {id: R4, text: "<…>", source: {doc: dw, ac: AC-003}}
assumptions:
  - {id: A1, text: "<环境前提>", source: {doc: prd, quote: "<原文逐字>"}}
out_of_scope:
  - {text: "<不做的>", reason: "<为什么>", source: {doc: prd, quote: "<原文逐字>"}}
open_questions: [{id: Q1, text: "<还没答案的问题>", owner: "<谁来答>"}]
```

`fv requirements-check --requirements requirements.yaml` 检查三件事：

- 引文必须逐字存在于来源文件（空白归一化后），至少 6 个字。编造的需求找不到可引用的原文。
- 来源里每一句规范性语句都要被某条引文覆盖：含 必须 / 不得 / 不能 / 不会 / 不允许 / 禁止 / 应当 / 应该 / 只能 / 最终 / 永远 / 恰好 / must / shall / never / always 的句子，表头行除外。没覆盖的就是被悄悄漏掉的承诺。
- done_when 来源里的每条 AC，都要么是需求，要么列入 out_of_scope。

规范句的识别是关键词启发式：它保证“带这些词的句子一句不漏”，不保证“没带这些词的承诺都被识别”，后者交给审阅者的 `missing` 类别。`open_questions` 不空，规则就不能签（`fv trace-rules` 会报）。清单与合同一起签进 G2 锁。

## 2. 规则候选（G-2）

派发 N≥2 个 `rule-formalizer`，每个只给：需求原文、`requirements.yaml`、自己的输出目录 `candidates/rules-<k>/`。
每个候选的 `contract.yaml` 写 `requirements: ../../requirements.yaml`，每条 property 带 `source`（R 编号，可以是列表）和 `text`；
无法形式化的需求写进 `dispositions`（`not_formalizable` / `out_of_scope` / `covered_by_tests` / `covered_by_other_module`，并给出理由）。
候选写完必须通过 `fv lint --contract` 和 `fv trace-rules --contract`。

## 3. 规则分歧（G-3）

```bash
fv rules-divergence --requirements requirements.yaml \
   --candidate a=candidates/rules-a/contract.yaml --candidate b=candidates/rules-b/contract.yaml \
   --model <任一能提供参数取值的模型，或 --constants '{"STOCK":1,…}'> --out rules-divergence.json
```

逐条需求比较：

| 分歧类型 | 含义 |
|---|---|
| `coverage` | 有的候选形式化了这条需求，有的没有（或处置不同） |
| `kind` | 性质种类不同：一个写成不变量，一个写成活性 |
| `semantic` | 同一需求下不变量（或 leads_to 的前后条件）的合取在有限域上真值不同；附**见证值**和每个候选的判定 |
| `unverified_equivalence` | 观测量没有有限域（映射、序列），或是迁移性质：只能比文本，交人判断 |
| `vocabulary` | 观测量的名字或类型不同 |
| `assumptions` | 声明的假设不同（每多一条假设，保证就窄一分） |

等价改写（如 `sold <= STOCK` 与 `not sold > STOCK`）在有限域上判为一致，不进议程。

## 4. 裁决与采纳（G-4）

人对每一项给出裁决：

```bash
fv resolve rules-divergence.json --item D1 --ruling "采用 A：原文同时要求剩余不为负" --by <姓名> --signer-kind human
```

Agent 代签必须用 `--signer-kind delegated_agent --authorization "<人的授权原话>"`，否则拒绝。裁决只增不删。

采纳规则：**最终的 `contract.yaml` 必须是被比较过的候选之一。** 不同位置的副本摘要相同（`requirements` 路径不计入摘要）。如果从几个候选里拼出一个新版本，就把它作为新候选加进去，重新比较、重新裁决。
这样，人裁决过的每一处差别就是最终规则与每个候选之间的全部差别，没有夹带。

## 5. 全新上下文审阅（G-5）

派发 `formal-reviewer`，只给需求原文、清单、最终合同和 `fv trace-rules` 的输出，**不给**候选和分歧报告。它写 `rules-review.yaml`。
`fv check-review` 要求：摘要等于当前合同和清单；`reviewer.context: fresh`；`review_complete.findings_count` 等于实际条数；每条阻断发现都有人的裁决。

## 6. 模型候选、分歧与采纳（G-6 到 G-8）

规则签了之后，派发 N≥2 个 `model-builder`。入口 A 给合同和设计说明，入口 B 给合同和代码范围。每个写 `candidates/model-<k>/model.yaml`（`contract: ../../contract.yaml`），入口 B 另写 source-map 候选。

```bash
fv model-divergence --candidate a=candidates/model-a/model.yaml --candidate b=candidates/model-b/model.yaml --out model-divergence.json
```

比较的是**观察者能看到的东西**：

- `verdict`：同一条规则，一个模型判 PASS，另一个判 FAIL，附反例；
- `reachable`：某个观测值组合只在部分候选里可达，附见证路径；
- `transition`：某个可观测的变化（如“售罄 → 再次提交”）只在部分候选里存在；
- `incomplete`：探索被截断，比较不完整。

内部步数不同而观察不到的（一个有“读库存”步骤，一个没有），不算分歧。裁决、采纳规则同第 4 节：采纳的模型必须在被比较之列。设计被反例推翻后，修正后的模型要重新进入比较。

## 7. 入口 B 的校准

现状模型描述的是**当前代码**。它的反例只有在它像这份代码时才可信：

```bash
python3 <harness> --vectors <由现状模型生成的向量> --out traces/      # 在当前代码上跑
aidlc_state.py formal calibrate --model candidates/model-a/model.yaml --traces traces/*.jsonl
```

CONFORMS 之后，`formal generation --kind model` 才会 READY。校准不一致，说明 AI 建的模型与代码不符，应该先修模型，而不是去分诊反例。

## 8. 收口

```bash
fv gen-evidence rules --contract contract.yaml --divergence rules-divergence.json --review rules-review.yaml --out r/gen-rules.json
fv gen-evidence model --model model.yaml --divergence model-divergence.json [--entrance code-first --calibration r/calibrate.json] --out r/gen-model.json
```

在 AI-DLC 里用 `aidlc_state.py formal generation --kind rules|model`。状态机每次推进都会对当前文件重算一遍：
候选被删、被改，清单变了，合同不在被比较之列，审阅过期，裁决缺失，都会让它重新变成 NOT_READY。

## 这套检查保证什么，不保证什么

| 保证 | 不保证 |
|---|---|
| 每条需求都有原文出处，带关键词的承诺一句不漏 | 不带关键词的隐含承诺都被识别（交给审阅者的 `missing`） |
| 至少两份独立的形式化被逐条比较，差别都经过人 | 两个生成者没有犯同一个错（交给审阅与 G2） |
| 最终规则与模型就是被比较、被裁决过的那份 | 规则“正确”：它只证明规则忠于清单、经过审阅和裁决 |
| 入口 B 的现状模型能解释当前代码的真实轨迹 | 轨迹之外的所有执行都被模型覆盖 |
