# PSL-sdlc-ring-audit

> 版本：v2.1（2026-09-05，G1 第一轮否决后按 E-1…E-12 修订为 v2；第二轮非阻塞整理：报告人审即 G3。v1 sha256 `b64f81e8…8a2ad7`、v2 `4d84dcee…85f86a` 见 g1-record.md）。
> 需求原文（用户，2026-09-05）："根据 sdlc 插件的理念，检查每个环节的配件或者 skill，看是否缺少 / 是否需要 / 是否实现 / 是否名字合适。"
>
> 双轨裁决：语义份额主导。把这句话交给一个不了解 sdlc 的工程师照字面做，他会产出一张"skill 文件存在 ✓/✗"的清单——
> 技术正确、产品错误：sdlc 的理念里，一个配件的存在理由不是"文件在"，而是它填了一个引擎自己填不了的缺口、独占一个产物、
> 被一道闸或一道门检着。所以写 PSL。
>
> 来路标注：`[surface]` 通用知识（skillwise / 工程实践）；`[elicit:物料]` 从插件自身文档抽出（ARCHITECTURE §6 与 §7、design-notes、
> lifecycle.md 制品映射表）；`[elicit:用户]` 用户原话；`[elicit:G1]` G1 第一轮裁决回答的承重槽；`[seam]` 承重但无人回答 → Open Questions。

## Vision（愿景）[Σ]

这次审计赌：**一个生命周期插件的配件之所以存在，是因为它填了一个引擎自己填不了的缺口，而不是因为流程图上有一个格子。**
（PSL-002）审计的产物因此不是"有 / 没有"的清单，而是每个配件在"缺口 — 产物 — 闸门 — 环"四个坐标上的位置与它名字的贴合度，
以及每个环上没有配件承载的缺口。（此命题推翻朴素实现：若只求清单，`ls plugins/sdlc/skills` 就够了。）`[surface]` `[elicit:物料 design-notes §写法]`

## Mental Model（心智模型）[Σ]

- **配件不是文件，是缺口的填充物。** 缺口分四原子：Knowledge / Capability / Judgment / Control（PSL-016）。一个配件可以同时填多原子，
  但填零原子的配件是过填（PSL-002）。`[surface skillwise]`
- **"已实现"是三态不是布尔**：声明了（SKILL.md 在）≠ 编译了（有 verify 脚本或被门挡）≠ 验证了（带/不带对比的行为层）。验证了的还可以附
  "已校准"（PSL-007）。sdlc 全部 skill 目前诚实地停在"编译了"这一态（PSL-010）。"空白"不是配件的一个态——空白是环上一个没有配件的缺口。`[elicit:物料 各 gate.json]` `[elicit:G1 E-1]`
- **名字有两条合法来路，来路只决定改不改，不决定合不合适**：新写的配件按产物命名（`plan-cards` 产 cards、`release` 产 release）；从上游
  收编的配件保留上游名，为了不断内部引用与上游同步（PSL-014）。贴合（名字 = 产物名或位置名）对每个配件都要诚实判，收编不是免检。`[elicit:物料 design-notes 命名决定]` `[elicit:G1 P-1]`
- **"缺少"有三种来源**：流水线闭合所需但没有承载的环节（lifecycle.md 制品映射表与 ARCHITECTURE §7 的空白登记：接口契约、红-绿脚本、
  meets_done_when 比对、DOS 对账 / drift）；本次新识别的缺口；以及现状本体 dos.yaml 里 `enforced_by ∈ {user_workflow, not_enforced}` 的
  规则——声明了却没有闸检的宪法条款，是 Control 缺口。三种都要诚实登记并带来源标签，不装作已有（PSL-017）。`[elicit:物料 lifecycle.md 制品映射表、ARCHITECTURE §7]` `[elicit:G1 E-12]`
- **审计者也在这个世界里**：审计本身是一次 sdlc 运行（dogfood），审计的每一步同时是被审对象的一次行为层证据（PSL-010）。运行（Run）
  是上游 sdlc 本体的聚合根，本 PSL 只引用它（slug / state.json / ledger），不重新建模。`[surface]` `[elicit:G1 E-10]`

## Domain Model（领域模型）[Σ]

| 实体 | 是什么 | 朴素实现里有吗 |
|---|---|---|
| Ring（环） | 生命周期的一段（R0 世界 … R8 学习）+ 脊柱（按 `id=spine` 的一条 Ring 记录处理）；每环有一个 `question`（它回答什么，取 ARCHITECTURE §1 表"问题"列） | 有（作为目录分组） |
| Part（配件） | 环上的一个可命名单元，`kind ∈ {skill, agent, asset, human_gate}`；skill 目录下的脚本是该 skill 的闸或 Capability，不是独立 Part；三道人签门归其所检产物所在的环（G1→R0、G2→R2、G3→R6） | 有（只作为文件） |
| **Gap（缺口）** | 引擎自己给不出的那部分：`atoms ⊆ {Knowledge, Capability, Judgment, Control}`；`source ∈ {lifecycle_blank, newly_identified, unenforced_rule}`；`necessity`；一句 deletion 测试。值对象，不带存储态——"有没有 Part 填它"由关联派生 | **没有** |
| **Artifact（产物）** | 配件独占生产的东西；身份 = graph.yaml `Node.writes` 的路径模式 ∪ ARCHITECTURE §1 产物列（PSL-001） | **没有**（朴素清单不追产物） |
| **Gate（闸/门）** | 检产物的东西：`kind: script`（机械闸，verify 脚本）或 `kind: human`（只能人签的门 G1/G2/G3）；human 门带 `signer / signer_kind ∈ {human, delegated_agent} / authorization_ref`。报告中 script 渲染为"闸"，禁止渲染为"门" | **没有** |
| **Assessment（审计判定）** | 对一个 Part 的三维判定：`needed / implemented（三态 + calibrated 附注）/ naming（来路 + 贴合 + 建议名）`，每维带 ≥ 1 依据 PSL-ID 与 ≥ 1 条 Evidence；不叫 Finding——Finding 是 R6 审查 skill 的产物名（findings.yaml），本次审计要把它列为 Artifact | **没有**（朴素只有 ✓/✗） |
| Loop（环契约） | Part 所属的环（loops.yaml#id），有 generator / verifier / stop；只引用不复述 | 有（v0.6.0 后是数据） |

值类型（不算对象）：**Evidence** `{kind ∈ {file, gate_json, smoke, run_record}, ref}`——State Machine 列的四种证据来源的统一形状，让检查脚本不只检非空。

不建模、只引用：**Run**（上游 sdlc 本体的聚合根）、**skill 源码问题**（Run 账本里的事件，skill-issues.md 是其投影）、**PSL 规律**（元层）。

关联：Ring 含 1..n Part；**Ring 暴露 0..n Gap**；**Part 填 0..n Gap，一个 Gap 可被多个 Part 填（N:N；六个审查 skill 共填一个 Judgment 缺口是常态）**（0 = 过填）；
Part 独占 0..1 Artifact（0 = 它不是生产者，可能是门或编排者；**同阶段的条件替代分支不算第二生产者**）；Artifact 被 0..n Gate 检；
**Gate（kind=human，仅 G3）裁决 0..n Assessment**；Part 属于 0..1 Loop（仅当 Part 是 loop_back 端点或某 Loop 的 generator / verifier 时，`null` 才需要理由）；
Assessment 对 Part 一对一，三维各引用 ≥ 1 条 PSL 规律。

（Domain Model 推翻测试：照此建表得到 Gap / Artifact / Gate / Assessment 四张表；照字面需求只得到 `{skill_name, exists}`。两者不同，这份 PSL 干活了。）

## State Machine（状态流转）[Σ]

领域动力学，不是执行顺序：

- **Part.implemented**：已声明（SKILL.md / agent.md 存在）→ 已编译（有 verify 脚本或被门挡、gate.json static_only）→ 已验证（带/不带对比的行为层跑过）；
  已验证的可附 `calibrated: true`（calibrate 四不可破）。逆向流转合法（脚本被删、门被绕）且要留痕。"空白"不在此机上——它是 Ring 上的 Gap。
- **Assessment**：候选（审计者提出）→ 有证据（引用 gate.json / smoke 行 / 文件路径 / 运行记录 / PSL-ID）→ 已裁决（G3 接受或推翻——报告人审即 G3 的内容；合入后的推翻是逃逸缺陷，喂下一次审计运行并以 supersedes 关联）。
  无证据的 Assessment 不得进入报告。G1 裁决的是形态草案，不是 Assessment——G1 在 issue 之前，那时一条判定都还不存在。
- **Gap**：未识别 → 已识别（进入某 Ring 的 missing）；有 Part 填它时从 missing 中移出——这一步是派生的，不是状态写入。一个 Gap 长期无 Part = lifecycle 的空白登记。

## Workflow（工作流）[Σ+φ]

**Σ · 审计者读一个环时，世界里发生了什么**：环上的每个 Part 被放到四个坐标上——它填哪个 Gap（引用 SKILL.md 的"缺口"段与 deletion 测试）、
它独占哪个 Artifact（引用 ARCHITECTURE §1 表的产物列与 graph.yaml 的 writes）、哪道 Gate 检它（verify 脚本 / 门）、它在哪个 Loop 里（loops.yaml）；
Part 的 Ring 归属从 graph.yaml 的 `Node.role` 经现状本体的 Ring 映射推出，不手填，证据写 graph.yaml 行号；一个 Assessment 随之成形，三维各带 PSL-ID。
没有 Part 的 Gap 浮现为该 Ring 的"缺少"；两个 Part 独占同一 Artifact 且不是同阶段条件替代时浮现为"合并候选"；没有任何 Gate 检的 Artifact
使其生产者的 implemented 不高于"已声明"，并浮现为一条 Control 缺口。

**φ · 消歧判据**：

- 一个 Part 像是重复了另一个（如 `pr-review` 与 `code-reviewer`）→ 以 Artifact 裁：产物不同（GitHub review vs findings.yaml 进 fleet）则不是重复，
  是同一判据的两个出口；产物相同则合并候选；同阶段的条件替代（`implement` / `card-implementer` / `ratchet`）不是争（PSL-001）。
- 一个 Part 是否"必要"→ 以 deletion 测试裁，且**在生命周期高度上读**："撤掉它，这条流水线会不会产出错的或不可验证的东西"，而不是"引擎会不会拒绝往下走"。
  流水线闭合所需不是第二标准，是 deletion 失败的一种证据（撤掉 `psl-derive`，引擎照样推导，但 G1 无物可裁，世界层错误一路漏到验收——这就是"会做错"，只是延迟）。
  两者读完仍冲突的残余写 `contested`（PSL-002）。
- 一个名字是否"合适"→ 先判来路（新写 / 收编，PSL-014），再对**每个** Part 判贴合：名字 = 产物名或位置名 → 合适；名字 = 动词短语或上游领域词且与产物不符 → 记建议名，
  **不实际重命名**（design-notes 的决定；重命名断内部引用）；收编不是免检。
- "已实现"→ 三态：声明 / 编译 / 验证（PSL-010），报告里禁止写"已实现 ✓"这种布尔。

**φ · "对"的结果长什么样**：一份按环组织的报告，每个 Part 一行、三维判定、PSL-ID 做脚注；每个环表末尾是该环的"缺少"（Gap 行，带来源标签）；
一份机器可读的 `audit.yaml` 与它同构（`rings[]`，每项 `{id, question, parts[].assessment, missing[]}`），能被脚本检"九环 + 脊柱全覆盖、每个 Part 三维齐、
每维有 PSL-ID 与 Evidence、无 Part 的 Gap 在 missing 里、无双生产者（同阶段替代豁免）"；末尾是提案清单（每条有来源 Assessment / Gap 与去向：skill fix_list / 新 issue / 不动）。
一份只有勾叉的清单即使全对也算错。

## Acceptance（验收）[φ-出口]

- A1 问"R6 验收环有哪些配件、各填什么缺口" → 返回该环每个 Part 的 Gap 原子集合、独占 Artifact、Gate（闸 / 门分清）、Loop，且列出该环 missing 里的 Gap（可为空）。
- A2 问"`pr-review` 和 `code-reviewer` 是不是重复" → 返回两者的 Artifact 对照与裁决（不重复 / 合并候选）及依据 PSL-001。
- A3 问"`donewhen-extract` 这个名字合适吗" → 返回来路（收编自 qanat）、产物（done_when.yaml）、贴合判定、若不贴合给建议名但标"不重命名"（PSL-014）；对收编 skill 同样给出贴合判定。
- A4 问"`implement` 已实现了吗" → 返回三态（声明 / 编译 / 验证）各自的 Evidence（SKILL.md、verify_commit.py + gate.json、L2 未跑），不返回布尔。
- A5 问"哪些环节缺配件" → 返回每个 Ring 的 missing：lifecycle 空白 ∪ 本次新识别 ∪ 未被闸检的宪法规则，每条带来源标签、"必要 / 不必要"及 deletion 测试的一句话理由（PSL-002）。
- A6 问"这份审计能不能被机器检" → 返回 `audit.yaml` 与检查脚本的路径，脚本对报告 exit 0，对删掉任一环的变体 exit 1，且两次运行都记录在 run_evidence（否则标 uncalibrated，PSL-007）。
- A7 问"审计者是谁、用什么身份签的门" → 返回每道门的签字人、signer_kind 与代签授权记录（本次为用户授权的子 agent 代签），代签不渲染为人签。
- A8 问"审计动过被审目录吗" → 返回被审目录（plugins/sdlc/skills、agents、docs）在卡提交里的 git diff 为空，以及 skill-issues.md 的路径（问题记在那里，不改被审文件）。

## Personas / Jobs [Σ·用户]

- **插件作者（本次用户）**：要"每个环节到底缺什么、哪些名字别扭"的结论 + 可直接开 issue 的提案；意图词"缺少"→ Ring.missing，"需要"→ needed，"实现"→ implemented，"名字"→ naming。
- **插件使用者**：读 README 决定用不用；意图词"这个 skill 干嘛的"→ Part 的 Artifact 与 Gap 一句话（留 README 既有表，本报告不另写）。

## UI Contract [φ]

- UI-1 报告必按环组织（R0–R8 + 脊柱），每环一表，每个 Part 一行、三列判定，PSL-ID 做脚注而不挤在格内；每环表末尾是该环的 missing 行（带来源标签）；
- UI-2 报告必与 `audit.yaml` 同构，且附检查脚本路径；机器读的 audit.yaml 才带全字段（Evidence 结构、adjudications）；
- UI-3 报告必有"本次运行的证据"（run_evidence）一节：状态机路径、门的签字人与 signer_kind 与授权引用、外部证据的替代品标 `substitute`、发现的 skill 源码问题的路径。

## Design Principles [φ]

- DP-1 **诚实 > 完整**：宁写"未验证 / 缺少"，不写"已实现 ✓"（PSL-010、PSL-017）。能裁决冲突：某配件有 SKILL.md 但无脚本无门 → 判"已声明"，不是"已实现"。
- DP-2 **缺口 > 数量**：不因某环配件少就建议补；补的理由只能是一个已识别的 Gap（PSL-002）。能裁决冲突："R1 只有两个 skill 显得单薄" → 否决，除非指出 Gap。
- DP-3 **命名建议不重命名**：建议进报告，重命名是另一次 G2/变更提案的事（PSL-014）。

## γ 约束

- done_when：九环 + 脊柱全覆盖 ∧ 每个 Part 三维判定齐 ∧ 每维 ≥ 1 PSL-ID 与 ≥ 1 Evidence ∧ 每环 missing 键存在（可为空）∧ `audit.yaml` 过检查脚本且删环变体 exit 1 有记录 ∧
  G1 / G2 / G3 签字人、signer_kind 与代签授权在报告可见 ∧ 被审目录在卡提交里 git diff 为空。
- 审计者不得修改被审 skill 的 SKILL.md 来让判定变好（评估者与被评估者分离，PSL-003）；发现的问题进 skill-issues.md 与提案，不进被审文件。
  运行中为了过门而修的 verifier bug 记为偏离（账本 kind=deviation），单独提交，不算卡提交。
- 机器可判到此为止；"这个 Part 的 Gap 归类对不对"是留给 G3 的残差（报告人审即 G3）。

## 规律索引（供推导引用）[Σ]

> 规律分两层：**约束形态**的（推导 form-draft 时引用）与**约束内容**的（审计判定 Assessment.needed 引用，说明某配件填的是哪条规律要求的缺口）。
> PSL-008、PSL-009、PSL-012 属后者，不出现在形态决策里是正常的。

- PSL-001 一个产物只有一个生产者；两个配件争同一产物 = 合并候选；同阶段的条件替代分支不算争。`[elicit:物料 ARCHITECTURE §6.1]` `[elicit:G1 P-3]`
- PSL-002 配件的存在理由是填引擎自己填不了的缺口（deletion 测试，在生命周期高度上读）；填零缺口 = 过填。`[surface skillwise]` `[elicit:G1 Open Q1]`
- PSL-003 判据先于代码；评估者与被评估者分离；审计者不改被审对象。`[elicit:物料 §6.2–6.3]`
- PSL-004 预算与终止由脚本强制，不由引擎记忆维护。`[elicit:物料 §6.4]`
- PSL-005 账本只增；产物可回滚，判据与失败记录不回滚。`[elicit:物料 §6.5]`
- PSL-006 三道门只能人签；代签须有授权记录且不得渲染为人签；`--autopilot` 免逐步确认不免门。`[elicit:物料 §6.6]` `[elicit:G1 E-7]`
- PSL-007 未校准的标准不当证据。`[elicit:物料 §6.7]`
- PSL-008（内容层）失败归层再处理；同指纹重复 = 无进展 = 升级。`[elicit:物料 §6.8]`
- PSL-009（内容层）合入不是终点；release 验证绿才交付。`[elicit:物料 §6.9]`
- PSL-010 静态过审 ≠ 有效；"已实现"是声明 / 编译 / 验证三态，"编译"= 有 verify 脚本或被门挡。`[elicit:物料 §6.10]`
- PSL-011 图与环是数据；每个**圈**有环契约（不要求每个配件属于某个环）。`[elicit:物料 §6.11]` `[elicit:G1 P-4]`
- PSL-012（内容层）收敛 ≠ 正确；repeat / oscillation / plateau 是换层信号。`[elicit:物料 §6.12]`
- PSL-013 harness 改动经人。`[elicit:物料 §6.13]`
- PSL-014 命名两来路：新写按产物或位置命名；收编保留上游名；来路决定改不改，贴合对每个配件都判；建议不等于重命名。`[elicit:物料 design-notes]` `[elicit:G1 P-1]`
- PSL-015 每个环节的产物要么被脚本检，要么被门挡。`[elicit:物料 ARCHITECTURE 一句话]`
- PSL-016 缺口四原子：Knowledge / Capability / Judgment / Control。`[surface skillwise]`
- PSL-017 空白诚实登记（三种来源都登记），不装作已有。`[elicit:物料 lifecycle.md 制品映射表、ARCHITECTURE §7]` `[elicit:G1 E-12]`

## Open Questions（seam）[γ→人]

G1 第一轮已回答（记录在 g1-record.md，作为 `[elicit:G1]` 进入正文）：必要的裁决标准、命名建议是否落地、主读者、缺少是否本次补齐、外部证据的替代品（有条件接受：标 substitute、
删环变体必跑、仅限本次 dogfood）。仍未决：

- **Proposal（提案）要不要成为实体**：本 PSL 把它作为 Assessment.disposition 的投影；若日后提案需要 owner / 状态 / 生命周期（issue 已开 / 已关），需要一个实体。承重：跨 Part 的提案（如合并两个 Part）挂在哪。
- **形态层引用锚**：UI Contract / Acceptance / Design Principles 本版给了 UI-n / A-n / DP-n 编号，但 psl-derive 的 verifier 只认 PSL-NNN；推导者引用这三层时暂借最近的 PSL 规律并在决策末尾注 `(via UI-1)`。承重：装饰性引用能否消失取决于 verifier 是否放开锚格式（skill-issues I-19）。
