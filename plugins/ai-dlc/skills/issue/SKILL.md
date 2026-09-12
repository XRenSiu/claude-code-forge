---
name: issue
description: >-
  补引擎自己给不出的缺口：一条 issue 什么时候算"可证伪的 TASK 雏形"而不是一段愿望（形容词
  换成阈值、每条 happy 路径带 unhappy 孪生、验收写观察边界不写文件路径、范围四项非空、假设进
  台账）；一个需求该走 PSL 轨还是 TASK 轨的双轨判据（含 DOS 词表闭包这个客观触发）；以及
  "先给人看再 gh 建"的确认门。效果：一句需求 / 一个 bug / 一条逃逸缺陷 → 结构化 GitHub issue，
  经 verify_issue.py 机械预门后创建。Use when: "建个 issue" / "把这个需求写成 issue" /
  "开个 bug" / "登记逃逸缺陷" / "create an issue for" / "file a bug" / "write this up as an
  issue" / 引擎准备直接 `gh issue create --body "<一句话>"` 时。NOT for: 写完整 done_when.yaml
  契约（/acceptance-spec）、写产品世界（/psl）、只想看 issue 列表（gh issue list 即可）。
  前置：gh 已认证、在目标仓库内。
argument-hint: "<需求 / bug 一句话或文件路径> [--kind feature|bug|escape] [--track psl|task] [--dos dos.yaml] [--labels a,b] [--yes] [--dry-run]"
version: 0.7.0
user-invocable: true
---

# issue — 愿望变成能判真假的条目

产物是一条 GitHub issue，其 body 按 `assets/issue_template.md` 的段落序呈现（这是产物序——
第 5 格——出口可检，不是流程）。本文件写：issue 在世界里是什么、什么算写对、原语与出口、
建之前的门。怎么问、怎么组织材料是你的份额。

## 缺口（Judgment + Capability + Control）

deletion 测试：撤掉本 skill，引擎会把需求原文当 body 直接建 issue——"让搜索更快""把审核做对"。
这样的 issue 任何实现都能"通过"，下游 done_when 没有源头，review 判"越界"没有基准。缺的是
**判据**（可证伪长什么样）、**原语**（verify_issue.py 把判据的机械半边编译掉）、**门**
（建 issue 是公开动作：先给人看）。

## 世界（Σ）

- **issue 是 TASK 的雏形，不是契约本身。** 契约（done_when.yaml v2）由 `/acceptance-spec`
  或 /ai-dlc 从这里的 AC 内联生成；issue 里的 AC 已经是 v2 形状，所以两边不会漂移。
- **三种入口**，同一模板：`feature`（需求）、`bug`（复现 + 期望 + 实际，AC 就是"复现不再
  发生"+ 回归守卫）、`escape`（合入后发现的缺陷：多一段"归因层 / 为什么该层的门没拦住"，
  建完 issue 后**必须**登记：`aidlc_state.py escape --slug <feature> --layer <归因层> --why "<为什么没拦住>" --issue <N> --by <人>`
  ——它计到归因层、追加 `escape-defects.md`、镜像进 `specs/<slug>/`；运行时目录已清时加 `--root specs`。
  只写 issue 不登记，`/retro` 的逃逸率永远是 0——它是世界层唯一的外部校准源，断在这里等于没有校准）。
- **两条轨道。** 语义份额 × 变化率高、实现原语难度低 → PSL 轨（先 `/psl` 建世界 → G1 人签，
  再回来建 issue）；确定性主导 → TASK 轨直接建。混合需求只对体验性内核走 PSL。速判：把需求
  交给不了解产品的工程师照字面做，会不会做出"技术正确、产品错误"的东西？会 → PSL。
  **客观触发有两条，都不靠自评**（Ambig-SWE：模型分不清任务写没写清楚）：
  ① `--dos dos.yaml` 时 `依赖 DOS:` 出现 dos.yaml 解析不了的概念 → 强制 PSL 轨。
     **前提是闭包真的被算过**：没有 `dos.yaml` 时这条判据不是失败也不是通过，是**没算**，
     而没算过的判据挡不住"自信而错的人绕开 G1"。所以 M / L 档带 `--require-dos`——
     它先在项目目录里自动发现 `dos.yaml`（`../ai-dlc/scripts/repo_assets.py`：仓库根 /
     `docs/` / `ontology/`），找不到才拒，并告诉你去跑 `/dos-extract` 并把它提交进 git
     （全组共用一份，不放 `.aidlc/`）。落地状态看 `aidlc_state.py repo`；
  ② TASK 轨在 issue 之后、G2 之前，对同一个 issue **隔离**起草 2–3 份 done_when，跑
  `../donewhen-extract/scripts/divergence.py`：分歧率超阈值 → 那些分歧就是必须澄清的槽
  （每条自带要问用户的话）。详见 `references/dual-track.md`。
- **范围段四项**（做 / 不做 / 硬约束 / 成功度量）是人写的："做到哪儿为止"agent 推不出来。
  你可以起草，但每项都要让用户确认或改。
- **假设台账**：澄清最多 3 轮；答不上来的承重槽不默认填，写进台账：假设 · 绑定的 REQ/AC ·
  风险 · 到期验证点（哪个 AC 或哪道门验证它）。超时不是失败，是带风险签字继续。
- **关于用户的 Σ**："快一点""稳定""大部分"是日常语言，不是判据——把它翻译成数字时，数字
  的来源要么是用户给的、要么是 SLO/KPI、要么是一次真实失败；没有来源就 `needs_threshold_source`
  标出来问，不编。

## 判据（φ）：什么算写对了

- **可证伪或不进**：AC 的 expect / statement 里出现模糊量词（快 / 慢 / 稳定 / 大部分 / 合理 /
  友好 / fast / reliable / most / better…）而没有数字阈值 → 不是验收条件。
- **happy 带 unhappy 孪生**：每条事件型 AC（"当 X 时系统应 Y"）配一条 unwanted（"当 <边界 /
  恶意 / 失败输入> 时系统应 <拒绝 / 降级 / 报错>"）。未定义的失败语义正是被钻的缝。
- **AC v2 形状**：`kind: mechanical` 必有 `observe`（route / cli / ui data-test / db_field / event）
  + `given` + `expect`；`kind: human` 必有 `statement` + `judge ∈ {product, design, tech}` +
  `evidence ∈ {checklist, demo}`。详见 `references/acceptance-shape.md`。
- **observe 是观察边界，不是实现结构**：出现 `src/…`、`.ts/.py/…` 文件名、函数名 → 拒（契约不该
  规定实现结构；文件级存在性下放到任务卡）。
- **范围四项非空**；**轨道已判定**（psl | task）；**依赖 DOS** 字段存在（可为 `none`，但要写）。
- **bug 类**：复现步骤 ≥ 1 条、期望 vs 实际都在、至少一条 AC 是回归守卫。
- **escape 类**：归因层 ∈ {card, plan, task, ontology, world} + "为什么该层的门没拦住"一句。
- 残差（机器不判，路由到人）：这些 AC 是不是**这次**最窄的可证伪条件；阈值是否反映 KPI 而非
  空气；unhappy 孪生盖的是不是**对的**边。脚本给 `needs_semantic_review`，不裁决。

## 原语（Π）

- `scripts/verify_issue.py <issue-body.md> [--dos dos.yaml] [--require-dos] [--kind feature|bug|escape]` —
  机械预门：exit 0 过（可带 flags）、1 拒、2 IO；`--dos` 下闭包失败还会在输出里给
  `force_track: psl`；`--require-dos` 把"闭包未检"从一条 flag 升成 reject，并在没给 `--dos` 时
  自动发现项目里的 `dos.yaml`（输出里 `dos_source: discovered` 说明它是发现来的）。
  **建 issue 前必须跑**。
- `assets/issue_template.md` — 产物的段落序（Intent / Track / Scope / Acceptance / Assumptions /
  Depends on DOS / Repro（bug）/ Attribution（escape）/ Links）。
- `gh issue create --title … --body-file … [--label …]` —— 存在性声明；`gh` 缺席或未认证时，
  产物落盘到 `issues/<slug>.md` 并告诉用户手动建。

## 门（γ）

- **给人看先于建**：body 通过预门后，把标题 + body 展示给用户，得到确认再 `gh issue create`；
  `--yes` 或 /ai-dlc `--autopilot` 才免确认。`--dry-run` 绝不触网。
- **PSL 轨的 issue 在 G1 之后建**：`--track psl` 且没有 G1 记录 → 停下来告诉用户先跑 `/psl`
  并人签 G1；不要用"先建了再说"绕过。
- **澄清有界**：一次一个主题、自带推荐答案、字母选项；三轮到顶，余下进台账。用户不在场 →
  全部承重未知进台账，照常交付 body（"信息不足无法生成"是禁止输出）。
- **done_when（本 skill 的）**：body 过预门 ∧ 用户确认（或 --yes）∧ issue 已建（或 --dry-run
  已落盘）∧ 回报 issue 编号与 URL。

## 失败机制

- 预门拒 → 修 body 再跑，不改脚本、不加 `--force`（本脚本没有 force）。
- 闭包失败但用户坚持 TASK 轨 → 建 issue 但在 Track 段写明 `closure_failed: <词>` 并加
  label `needs-psl`，账本记 waiver；不静默。
- gh 报 403/404（无权限 / 仓库错）→ 落盘 body，回报路径，不重试三次以上。
- 用户给的是现成 issue 编号 → 读它、按判据补全 body、用 `gh issue edit`，同样过门与确认。

## 高危黑名单（不可豁免）

- **绝不编阈值**：没有来源的数字比没有数字更危险（它看起来是判据）。
- **绝不把文件路径 / 函数名写进 AC 的 observe / existence**。
- **绝不无确认建 issue**（除 `--yes` / autopilot）；绝不建重复 issue（先 `gh issue list --search`）。
- **绝不用默认值填承重未知**——进台账。
- **绝不在 body 里放 secrets / 内部 URL 凭证**（预门扫描，命中即拒）。

## 接线

- 上游：`/psl`（PSL 轨）；`/dos-extract`（提供 dos.yaml 给闭包）。
- 下游：`/acceptance-spec`（issue → EARS + done_when.yaml）；`/ai-dlc`（记 `issue.number`；`--kind escape` 时 `aidlc_state.py escape` 登记）；
  `/pr` 的 `Closes #N`；`/review-loop` 用 Scope 段判越界。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`verify_issue.py` 在 fixtures 上冒烟（合法 body 0 拒；模糊量词 /
无孪生 / 文件路径 observe / 闭包失败各被拒或强制 psl）。行为层未跑。
