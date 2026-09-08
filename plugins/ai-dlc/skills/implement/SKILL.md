---
name: implement
description: >-
  补引擎自己给不出的缺口：按一张卡实现时的隔离与纪律——实现者只看到卡 + 状态摘要 + AC 子集
  （不看评审判据、不看隐藏集、不看其他卡），改动落地前过白名单执行器与 G2 锁，复现测试先红后绿，
  每张卡一个或多个原子 commit 并登记到状态机；单卡预算 3、同指纹失败立即升级到方案层而不是原地重试。
  效果：卡进、diff + commit + 卡状态出。Use when: "按卡实现" / "做 CARD-03" / "implement this card" /
  "开始写代码" 且已有卡与冻结契约时。NOT for: 拆卡（/plan-cards）、修 review 评论（/review-loop 的
  comment-fixer）、跑到达标为止的优化循环（/ratchet）、整体验收（/acceptance-fleet）。
argument-hint: "<cards/CARD-xx.yaml> [--executor self|agent|ratchet|forge-teams] [--lock .done_when.lock]"
version: 0.2.1
user-invocable: true
---

# implement — 一张卡，一个看不见评审的实现者

产物是限定在卡白名单内的 diff、按 `/commit` 规则落地的 commit（footer `Card: CARD-xx`）、以及状态机里
该卡的 `done` 状态。本文件写：实现者能看到什么、什么算做完、原语与门、失败怎么走。怎么写代码是引擎的份额。

## 缺口（Control + Judgment）

deletion 测试：撤掉本 skill，引擎会把整个对话历史、评审 skill 的判据、其他卡的改动一起塞给实现者，
改动溢出白名单、顺手改掉一个测试断言让它变绿、失败后在同一处重试到上下文耗尽。缺的是隔离（γ）、
落地前的闸（已编译在 `verify_commit.py`）、"做完"的判据与升级规则（γ）。

## 世界（Σ）

- **实现者看到的全部输入**：一张卡（`assets/card_context.md` 形状）+ `aidlc_state.py show` 的摘要 + 该卡的 AC
  子集 + `allowed_files` 内的源码。**看不到**：评审 skill 的提示与判据、隐藏变体集、`spec-robustness.md`、
  其他卡、账本里评审者的发现。这是训练期信息隔离的实现形态（干活的不许看日志）。
- **执行器可换**：`self`（当前会话，仍遵守隔离——只读卡）、`agent`（`agents/card-implementer.md`，全新上下文）、
  `ratchet`（需要跑到达标为止的卡）、`forge-teams`（并行多卡，邻居）。隔离规则对所有执行器相同。
- **红-绿**：卡的 AC 子集对应的测试由 `/test-suite-generator` 事先写好并锁；实现前它们必须是红的（基线上跑
  一次记录），实现后变绿。测试文件在 `forbidden_files` 里——实现者改不了。
- **一卡多 commit 合法**（按关注点），但每个 commit 都过 `verify_commit.py --card --lock`。
- **失败指纹**：同一张卡同一失败摘要第二次出现 = 无进展，`aidlc_state.py fail` 会判 escalate（方案层：重拆或改卡），
  不是"再试一次"。
- **关于用户的 Σ**："先把功能做出来再说"= 仍然只在白名单内做；"测试写得不对"= 走变更提案，不是改测试。

## 判据（φ）

- 卡的 `ac_ids` 对应测试全绿（`/qa-reviewer` 或直接跑测试入口）；全套件无回归；lint / 类型 / 构建绿（存在则跑）。
- 每个 commit `verify_commit.py --card <卡> --lock .done_when.lock` exit 0。
- diff 内没有卡 `forbidden_files` 的文件；没有新增依赖（有则记 `notes` 并进 A 档检查）。
- 残差：实现是否走捷径满足测试（`/spec-gaming-detector` 在整体验收时看）；本 skill 不自评。

## 原语（Π）

- `assets/card_context.md` —— 交给实现者的输入形状（卡 + 状态摘要 + AC 子集 + 红基线记录）。
- `../../agents/card-implementer.md` —— 全新上下文的实现者定义。
- `../commit/scripts/verify_commit.py` —— 落地前的闸；`../ai-dlc/scripts/aidlc_state.py card / fail` —— 登记与升级。
- `references/executors.md` —— 四种执行器的接法与隔离检查表。

## 门（γ）

- **前置**：`cards.lint_passed=true`；`.done_when.lock` 存在；该卡 AC 的测试存在且在基线上为红（无测试则 `notes`
  写明 `no-tests-for: AC-xxx` 并在整体验收时补——不许实现者自己写验收测试）。
- **done_when**（本卡）：AC 子集绿 ∧ 全套件无回归 ∧ 每个 commit 过闸 ∧ `aidlc_state.py card CARD-xx --status done --commit <sha>`。
- **升级**：`fail --signal card_test_fail --card CARD-xx --fingerprint <摘要>`；返回 `escalate: true` → 停，写失败报告，
  回 `/plan-cards` 或交人。绝不绕过。

## 失败机制

- 白名单溢出（需要改卡外文件）→ 停；`fail --signal whitelist_overflow`；回 `/plan-cards` 调整归属。
- 需要改契约 / 测试才能通过 → 契约类 → 变更提案 + G2 重签，不在实现里改。
- 测试在基线上就是绿的 → 测试没打中行为，回 `/test-suite-generator`，不继续实现。
- 依赖缺失（另一张卡未完成）→ `card --status blocked`，做别的卡。

## 高危黑名单（不可豁免）

- 绝不给实现者评审提示、隐藏集、spec-robustness。
- 绝不改 `tests/**`、`done_when.yaml`、`dos.yaml`、锁文件；绝不放宽断言。
- 绝不 `--no-verify`；绝不在预算耗尽后"再试一次"。
- 绝不让实现者自评 `meets_done_when`。

## 接线

上游：`/plan-cards`（卡）、`/test-suite-generator`（红测试）。下游：`/commit`、`/acceptance-fleet`（整体验收）、
`/pr`。状态：`aidlc_state.py card` / `fail`。

## 环契约

本 skill 是 `../ai-dlc/assets/loops.yaml#card_retry` 的 generator（verifier = acceptance-fleet；level agent；trigger turn_end；
memory = state.json#cards.items · ledger.md · trace.jsonl）。停止四键：success = AC 子集绿 ∧ 每 commit 过闸 ∧ card done；
convergence = 同指纹 ×2 / 周期 2–3 震荡（`fail` 自动派生 `oscillation_detected` → plan 层）；budget = routing `card_retries`；
impossible = `impossible_under_contract`（只能由评估者报，实现者报被拒）。触发绑定见 `../ai-dlc/assets/triggers.yaml#card_retry`
（`/goal` 条件里每轮回显测试与 verify_commit 输出）。图上：`graph.yaml` 节点 `implement` / `agent.card-implementer`，
`must_not_read` 里列的东西就是隔离的编译态。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——本 skill 无独立脚本，其闸由 `verify_commit.py` 与 `aidlc_state.py` 承担（已冒烟）。行为层未跑。
