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

## 有意不做的

- 不做 hooks：把 `verify_*.py` 挂成 PreToolUse 会拦所有 git commit，对非 sdlc 场景过填；留给用户按仓库决定。
- 不做 rules/：插件级 rules 会注入每个会话，git 约定放 `commit/references/conventions.md` 按需读。
- 不重复实现邻居：acceptance-spec / test-suite-generator / acceptance-fleet / psl / dos-extract 有则用。
