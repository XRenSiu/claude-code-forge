# 设计笔记：借鉴来源与取舍

## 写法：skillwise 四原子（`docs/THEORY.md`、`write-skill`）

- 每个 SKILL.md 先说**缺口**（deletion 测试），再说**世界 Σ / 判据 φ / 原语 Π 存在性 / 门 γ**，不写 Step 1/2/3。
- 顺序只在六格之一出现：依赖（没有 issue 就没有 Closes）、不可逆（push / merge）、外部强制（人签的门）、
  认识论（先验证评论再归类）、产物序（issue / PR body 的段落序——出口可检）、编译序（脚本内部）。
- 必须**成立**的正确性编译为原语 / 验证器 / 不可跳过的门：`verify_*.py` 检产物不检过程；`sdlc_state.py advance`
  对着状态检前置条件；`pr-poll.sh` 把预算与终止谓词编译进脚本。
- persona 卸载：agents 不写"你是资深工程师"，写判据。
- description 编码缺口签名（Use when … NOT for …），触发短语中英文口语都有。
- 出口门诚实：全部 `static_only`——脚本在 fixtures 上冒烟，行为层未跑。

## 运行时：SKILL.state（agent-skill-explainer §02）

- `state.json` 是充分统计量：只留状态，不留历史；schema 按领域写一次（生命周期），不按任务写。
- 校验与合并由脚本确定性地做，引擎只提议——坏提案被拒，不污染状态。
- 子 agent 只拿卡 + 状态摘要 + 最新观察，不拿整段历史。
- 失效边界（文档自列）：schema 事先定不下来的探索性工作不适合——所以 /sdlc 只覆盖形态已定或
  已过 G1 的需求；世界怎么建交给 /psl。

## 账本：WikiSkill（agent-skill-explainer §01）

- `ledger.md` 只增不删；产物可回滚，判据 / 失败记录 / 被拒修复 / 路由决定不回滚。
- 干活的不许看日志：实现子 agent 看不到评审判据；review-loop 的 verifier 与 fixer 隔离。
- 被否的也留 diff：review-loop 的证据日志保留被 reviewer 推翻的 verdict。

## 参考文档：Spec Loop v1.2 × done_when Pipeline

- 十个裁决的落点见 `lifecycle.md`；C1（契约装判据不装测试名）是其余九个的前提，issue AC v2 形状由此而来。
- 空白诚实登记：psl-derive、接口契约 schema、红-绿脚本、meets_done_when 比对、DOS 对账 / candidate / drift。

## 直接收编（整 skill 复制进本插件，正文保留，加术语映射 + 接线）

- looper v0.2.0：`psl` / `dos-extract` / `invariant-extract`（原样，末尾加「接线（在 sdlc 里的位置）」）。looper 仍是它们的上游。
- qanat `.claude/skills`：`donewhen-extract` / `spec-compile` / `calibrate`——正文保留 qanat 的领域词（Territory / Run / R001 / R002 /
  MemoryAsset），各加一张「术语映射」表把它们读成 sdlc 的对象，并把「立法收件箱 / daemon」改成 sdlc 的变更提案 / G3 与本地测试 / CI。
  注意 qanat 的 `verify_g1 / review_g2`（机器闸 / 评审闸）与 sdlc 的 G1（世界裁决）/ G2（判据冻结）不是同一对门，映射表里点明。
- 本仓库 done-when-pipeline v1.1.0：九个验收线 skill（acceptance-spec / test-suite-generator / code-reviewer / qa-reviewer /
  pm-reviewer / spec-drift-detector / spec-gaming-detector / meta-judge / acceptance-fleet）与 ratchet v1.1.0——qanat 持有它们的旧副本
  （2026-06-13 引入），本仓库版本更新且带 scripts/ 原语，故取本仓库版；各加 Wiring in sdlc 段。ratchet 原文是步骤式写法（第一步…第五步），
  原样收编，gate.json 登记为「继承的过程式形态，六格归位待做」。
- 新写 `psl-derive`（参考文档 U3 的空白）：四文件产物、决策 ← PSL-ID 硬约束、N 次隔离推导取分歧集、`verify_derived.py` 调用 dos-extract 的 `verify_dos.py`。

## 直接改编

- `review-loop`：vana-builder `pr-review-loop` v0.4.0（SKILL.md 契约与 `pr-poll.sh`），改动：状态目录移到
  `.sdlc/pr-watch`；增加契约类 verdict（命中 G2 锁 → ESCALATE）；bot 线程 strike 减半；与 /commit 预门、
  /sdlc 路由信号接线；可选隔离子 agent。
- `pr-review`：done-when-pipeline `/code-reviewer` v1.0.0 的判据（Detective Loop、复现、5 条上限、反驳、
  禁语），加三档归位与 `post_review.py`。
- `commit` / `pr`：pdforge `rules/git-workflow.md`、`finishing-a-development-branch`、`requesting-code-review`
  的约定，改为判据 + 预门形态。
- `issue`：qanat `donewhen-extract` 的三纪律（形容词→阈值 / happy-unhappy 孪生 / 出口两检）+ looper `psl`
  的双轨判据与诚实公理（不默认填承重未知 → 台账）。
- agents：qanat `issue-fixer` → `comment-fixer`；`quality-sentinel` → `fix-verifier`；`code-reviewer` →
  `pr-reviewer`（去 persona，保留判据）；`review-triager` 新写。
- 断路器 / 指纹：pdforge `/accept` 的问题指纹与断路器 → `sdlc_state.py fail` 的指纹终止；forge-teams
  `fix-bug-loop` 的三层升级 → 分层预算。

## 2026-09-05 第二次整理：按逻辑重拆（用户要求"产研自闭环自洽、覆盖方方面面"）

推演发现三类不自洽，处理如下：
1. **契约有三个生产者、两种 schema**（issue 内联 AC v2 / donewhen-extract 卡 / acceptance-spec v1）→ 定 `done_when.yaml` v2 为唯一契约
   （`donewhen-extract/references/done-when-v2-schema.yaml`），`validate_done_when_v2.py` 编译进 `advance g2`；v1 经 `convert_v1_to_v2.py` 变骨架；
   两段锁（`lock --stage g2|l5`）落实 C1/C6。
2. **四个环节没有承载 skill**（L4 拆卡藏在 /sdlc 里；L6 实现没有隔离契约；L8 只到 merge 没有交付；X3 只有脚本没有学习闭环）→ 新增
   `plan-cards`（lint_cards.py 移入）、`implement`（+ `card-implementer` agent）、`release`（`verify_release.py`）、`retro`（metrics.py 移入）；
   状态机加 `release` 阶段。
3. **命名**：保留导入 skill 的原名（与上游一致、内部互相引用不断），新 skill 按产物命名；用 `docs/ARCHITECTURE.md` 的"九环"组织，不用前缀重命名。

## 有意不做的

- 不做 hooks：把 `verify_*.py` 挂成 PreToolUse 会拦所有 git commit，对非 sdlc 场景过填；留给用户按仓库决定。
- 不做 rules/：插件级 rules 会注入每个会话，git 约定放 `commit/references/conventions.md` 按需读。
- 这条线（Spec Loop × done_when）上的 skill 全部收编，sdlc 自包含；只有实现侧执行器（forge-teams / pdforge）留作邻居——它们是
  执行者，不是这条线自己的零件。同名 skill 与源插件并存时用 `/sdlc:<name>` 命名空间。
