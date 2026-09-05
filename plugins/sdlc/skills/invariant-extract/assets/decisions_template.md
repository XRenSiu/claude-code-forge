# invariant-extract · decisions.md(审计轨)

> 体例与 dos-extract 标准一致。每一处非平凡判断都留痕,供事后审计。
> 这把刀是起草书记员,不是立法者 —— decisions.md 是它向立法者交代"为什么这么草"的账本。

## 运行元信息

- territory_id:
- 模式:interactive | auto
- **目的(取景框)**:name = … ;kpi = … ;主 aspect = … ;dos.scope 引用 = …
- dos_ref(统一语言来源):
- 代码面(work_target / paths):
- failure.memory 计数:    (为 0 时,通道二无输入 —— 见下"通道说明")

## 通道说明

- 通道一(演绎采集)是否跑:
- 通道二(溯因恢复)是否有输入:    (无 → 显式记录,不假装跑过)

## 溯因 — 逐 obstacle 裁断

> 每条:目的投影(aspect / 是否 ∅)、来源 obstacle、取反出的候选、为什么取这条"最窄规则"、置信度、是否走 PROPOSE。

- obstacle <id>:投影 aspect = …(∅ → 跳过,记 why);候选 = "…";最窄性理由 = "…";置信 = high/low;disposition = propose/carded

### 按目的投影为 ∅ 而跳过的 obstacle(非排他,可被别的领地接走)

- obstacle <id>:why_empty = "…"

## 存活测试 — □/◊ 逐候选裁断

> 每条:能否活过揭示它的那次 Run、判 □ 还是 ◊、◊ 的移交去向。

- 候选 "…":存活测试(相对本领地目的) = pass/fail;判定 = □/◊;若 ◊ → 移交 done-when-pipeline,理由 = "…"

### 分层探针(换目的的思想实验)

- purpose-independent 嫌疑(送立法上浮、不复制进卡):候选 "…";why = "代入哪块领地的目的都成立 …"

## 强度分类 — 逐 □

> 每条:任务能否合法违反、判硬 / 可覆盖、authority level、海拔(territory / 提案上升)。

- □ "…":能否合法违反 = 不能/能;栏 = hard/overridable;海拔 = territory;是否提案上升 R00x = 否/是

## 去重与冲突

- 与 dos.yaml.rules 去重(已升宪法、不重复立法)的候选:
- 与现有卡合并的同义条:
- 检出的冲突(两条不能同真 → 立法项):

## 落卡与提案

- 落卡的可覆盖默认(候选):
- 走 NEEDS_HUMAN / 立法的硬不变量与高风险溯因:
- dos 修订提案(Territory.invariants 字段 / MemoryAsset 枚举):已产出 / 不需要(字段已存在)
- 登记为 golden 回归用例的不变量(棘轮):

## Self-review(验收自检)

- [ ] 绑定了恰好一个 Territory,不变量用了它的统一语言
- [ ] 拉了目的(name+kpi+scope)并当透镜贯穿:obstacle 按目的投影(∅ 的已跳过并记录),每条 □ 记了 aspect
- [ ] purpose-independent 嫌疑已标记送立法,未复制进本卡
- [ ] 两条通道都跑了(或显式记录通道二无输入)
- [ ] 每条落卡不变量都有溯源(执行点 / 真实失败)
- [ ] 没有 ◊ 混进卡;◊ 已踢给 done_when 生成器
- [ ] 硬不变量是被提案的,不是自动安装的
- [ ] 与 dos.yaml.rules 去过重
- [ ] 冲突被显式呈现为立法项
- [ ] 无 invariants 字段时,产出了有界 dos 修订提案
