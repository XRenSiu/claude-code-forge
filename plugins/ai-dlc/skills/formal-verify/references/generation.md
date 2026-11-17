# AI 生成协议：规则与模型

AI 写规则、AI 建模是这条流程的必经阶段。这份文件规定写出来的东西怎么被组织、比较和检查。
**怎么写**不由本文件规定：每一步都执行 `upstream/` 里原样收录的开源流程，步骤与上游原文的对应关系见 [upstream-methods.md](upstream-methods.md)。
本文件只补充上游没有的组织边界，核心是一句话：**生成者不检查自己。** 生成者至少两个且互不可见，比较由脚本做，裁决由人做，审阅由一个全新上下文、只读的审阅者按上游审阅契约做。

## 0. 派发方式

| 宿主 | 怎么做到“互不可见” |
|---|---|
| Claude Code | 用 Agent 工具分别派发 `rule-formalizer` / `model-builder` / `formal-reviewer`（插件 `agents/` 下的定义）。**每次派发一个新实例**，提示里只给允许读的路径和本次的输出目录，不要把别的候选内容贴进提示 |
| 没有子 agent 的宿主（Codex 等） | 每个候选开一个新会话，提示词照抄对应 agent 文件的正文 |
| 有跨供应商模型 | 把两个候选分给不同供应商：同源模型的盲区相同，分歧检测会失灵（同 acceptance-fleet 的跨供应商分配）；分不到就在 notes 里写明是同源模型 |

派发者（运行 `/formal-verify` 的主 Agent）只做三件事：分配目录、跑 `fv` 命令、把议程交给人。它**不改**候选，也不替人裁决。

## 1. 需求清单与 intake（G-1、G-2）

第一个 `rule-formalizer` 以 intake 模式执行 Spec Kit `specify` 第 6 步，写 `requirements.yaml`：

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

规范句的识别是关键词启发式：它保证“带这些词的句子一句不漏”，不保证“没带这些词的承诺都被识别”。后者交给 intake 的歧义扫描和审阅者的 source_fidelity 面。`open_questions` 不空，规则就不能签（`fv trace-rules` 会报）。清单与合同一起签进 G2 锁。

接着它执行 Spec Kit `clarify`（第 3–6 步）和 Quint quint-modeling 的 Step 1、from-requirements，写 `rules-intake.yaml`（字段见示例）：

- `ambiguity_scan`：Spec Kit 的 10 类，逐类标 Clear / Partial / Missing；
- `clarifications`：≤5 个以问号结尾的问题，**答案由人给**（`by` + `signer_kind: human`，委托须附授权原话）。生成者只提问；
- `deferred`：超出配额或影响低的类别，标 Deferred / Outstanding 并给出理由；
- `system_model`：actors / communication / failures / time，每项的 `source` 指向清单的 R/A 编号或某个澄清问题；
- `extraction`：from-requirements 的抽取表（实体 / 操作 / 性质 / 假设 + High / Medium / Low）；
- `granularity`：每个操作一行，写 atomic 或 split，并给出理由。

`fv intake-check rules-intake.yaml --requirements requirements.yaml --upstream upstream/UPSTREAM.json` 核对以上各项。规则候选读的是答完问题的 intake。

## 2. 规则候选（G-3）

派发 N≥2 个 `rule-formalizer`，每个只给：需求原文、`requirements.yaml`、自己的输出目录 `candidates/rules-<k>/`。
每个候选的 `contract.yaml` 写 `requirements: ../../requirements.yaml`，每条 property 带 `source`（R 编号，可以是列表）和 `text`；
无法形式化的需求写进 `dispositions`（`not_formalizable` / `out_of_scope` / `covered_by_tests` / `covered_by_other_module`，并给出理由）。
候选写完必须通过 `fv lint --contract` 和 `fv trace-rules --contract`。intake 里 High 影响的性质类需求，在采纳的合同里必须被某条 property 形式化，不能只给处置。

## 3. 规则分歧（G-4 前半）

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

## 4. 裁决与采纳（G-4 后半）

人对每一项给出裁决：

```bash
fv resolve rules-divergence.json --item D1 --ruling "采用 A：原文同时要求剩余不为负" --by <姓名> --signer-kind human
```

Agent 代签必须用 `--signer-kind delegated_agent --authorization "<人的授权原话>"`，否则拒绝。裁决只增不删。

采纳规则：**最终的 `contract.yaml` 必须是被比较过的候选之一。** 不同位置的副本摘要相同（`requirements` 路径不计入摘要）。如果从几个候选里拼出一个新版本，就把它作为新候选加进去，重新比较、重新裁决。
这样，人裁决过的每一处差别就是最终规则与每个候选之间的全部差别，没有夹带。

## 5. 全新上下文审阅（G-5）

派发 `formal-reviewer`（rules 模式），只给需求原文、清单、最终合同和 `fv trace-rules` 的输出，**不给**候选和分歧报告。它执行 Formal Verification Skills 的 `fc-spec-review` 审阅契约，写 `rules-review.yaml`（schema 2），写完不再修改。作者在旁边写 `rules-triage.yaml`，按 `review-policy` 逐条处置：FIX / DESCOPE / DEFER-WITH-RULING / REJECT-FINDING / ASK-HUMAN。

`fv check-review rules-review.yaml --contract contract.yaml --triage rules-triage.yaml` 要求：

- 摘要等于审阅时的合同和清单；`reviewer.context: fresh`；`review_complete.findings_count` 等于实际条数；
- 7 个审阅面都有 checked（写明查了什么）或 not_applicable（写明理由）；
- 发现的 ID 为 `F-<n>`，severity 与 class 合法，claim 与 evidence 都有实质内容；
- PASS：审阅的就是当前合同。APPROVE-WITH-EDITS：至少一个发现，每个发现都已处置；`contract_before` 是被审的版本并且保留着，`contract_after` 是当前版本。REVISE / BLOCKED：要再审一轮，最多 3 轮；
- DEFER-WITH-RULING 要有人的裁决（作者不能给自己裁决），REJECT-FINDING 要有源证据，ASK-HUMAN 表示仍在等人。

## 6. 模型候选、分歧、审阅与采纳（G-6 到 G-8）

入口 B 先派一个 `model-builder`（analysis 模式）执行 Specula `code_analysis`，写 `modeling-brief.md` 与 `defect-ledger.json`。brief 是所有模型候选共同的输入，地位和合同一样。

规则签了之后，派发 N≥2 个 `model-builder`（candidate 模式）。入口 A 给合同和设计说明；入口 B 给合同、brief 和代码范围。它们执行 Quint quint-modeling Step 1–7，入口 B 另加 from-code、tlaplus-from-source、Specula spec_generation。每个写 `candidates/model-<k>/model.yaml`（`contract: ../../contract.yaml`）和 `notes.md`（Step 7 handoff 的三节：What it covers / What it does NOT cover / When to update）。入口 B 另写 source-map 候选。

```bash
fv model-divergence --candidate a=candidates/model-a/model.yaml --candidate b=candidates/model-b/model.yaml --out model-divergence.json
```

比较的是**观察者能看到的东西**：

- `verdict`：同一条规则，一个模型判 PASS，另一个判 FAIL，附反例；
- `reachable`：某个观测值组合只在部分候选里可达，附见证路径；
- `transition`：某个可观测的变化（如“售罄 → 再次提交”）只在部分候选里存在；
- `incomplete`：探索被截断，比较不完整。

内部步数不同而观察不到的（一个有“读库存”步骤，一个没有），不算分歧。裁决、采纳规则同第 4 节：采纳的模型必须在被比较之列。设计被反例推翻后，修正后的模型要重新进入比较。

采纳后，派发 `formal-reviewer`（model 模式）。它执行 Quint `review.md` 的 6 项结构检查和 Specula 的粒度审计，写 `model-review.yaml`。`fv model-review-check` 会用检查器重算 C-init、C-step、C-step-complete、R1、R2：审阅者说“见证齐全”而检查器发现死动作，或说“不变量非平凡”而有性质不引用任何观测量，都会被拒绝。结构检查为 fail 时不能采纳；warn 由人决定；按粒度审计该拆而没拆的动作，必须先拆。

入口 B 还要由采纳模型的作者（coverage 模式）执行 Specula 的 brief coverage 自检，写 `brief-coverage.yaml`：brief 的每个 Scenario、第 5 节每条不变量、6.1 每条发现，都要在合同和某个 hunt 模型里找到落点（`fv brief-check`）。

## 7. 入口 B 的校准

现状模型描述的是**当前代码**。它的反例只有在它像这份代码时才可信：

```bash
python3 <harness> --vectors <由现状模型生成的向量> --out traces/      # 在当前代码上跑
aidlc_state.py formal calibrate --model candidates/model-a/model.yaml --traces traces/*.jsonl
```

CONFORMS 之后，`formal generation --kind model` 才会 READY。校准不一致，说明 AI 建的模型与代码不符，应该先修模型，而不是去分诊反例。

## 8. 收口

```bash
UP=upstream/UPSTREAM.json
fv gen-evidence rules --contract contract.yaml --divergence rules-divergence.json --intake rules-intake.yaml \
   --review rules-review.yaml --review-triage rules-triage.yaml --upstream $UP --out r/gen-rules.json
fv gen-evidence model --model model.yaml --divergence model-divergence.json --review model-review.yaml --upstream $UP \
   [--entrance code-first --calibration r/calibrate.json --brief modeling-brief.md --ledger defect-ledger.json \
    --coverage brief-coverage.yaml] --out r/gen-model.json
```

在 AI-DLC 里用 `aidlc_state.py formal generation --kind rules|model`。状态机每次推进都会对当前文件重算一遍：
候选被删或被改、清单变了、合同不在被比较之列、审阅过期、裁决缺失、收录的上游原文被改动、产物引用了别的字节，都会让它重新变成 NOT_READY。

## 这套检查保证什么，不保证什么

| 保证 | 不保证 |
|---|---|
| 每条需求都有原文出处，带关键词的承诺一句不漏 | 不带关键词的隐含承诺都被识别（交给 intake 的歧义扫描与审阅） |
| 上游流程的每一步都做了、记下了，引用的是收录的原文字节 | 每一步做得好（问题问得准、brief 分析得深） |
| 至少两份独立的形式化被逐条比较，差别都经过人 | 两个生成者没有犯同一个错（交给审阅与 G2） |
| 最终规则与模型就是被比较、被裁决过的那份 | 规则“正确”：它只证明规则忠于清单、经过审阅和裁决 |
| 入口 B 的现状模型能解释当前代码的真实轨迹 | 轨迹之外的所有执行都被模型覆盖 |
