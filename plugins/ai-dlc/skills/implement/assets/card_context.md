# 实现输入 — CARD-xx（这是实现者能看到的全部）

## 卡
<粘贴 cards/CARD-xx.yaml 全文>

## 状态摘要
<`python3 <plugin>/skills/ai-dlc/scripts/aidlc_state.py show` 的 slug / stage / branch / lock.path / cards.items[CARD-xx]>

## AC 子集（来自 done_when.yaml，只含 ac_ids）
<逐条：id / observe / given / expect>

## 红基线
<测试名 → 在 <base-sha> 上失败的一行输出；无测试的 AC 列 `no-tests-for:`>

## 仓库怎么干活（agent-map 切片）
<`python3 <plugin>/skills/plan-cards/scripts/slice_agent_map.py agent-map.md --card cards/CARD-xx.yaml` 的输出；
 没有 agent-map.md 时写 `无——实现者需要自己找测试入口`，别留空>

## 形式化实现契约（卡有 `formal_ops` 时必填，没有就删掉这一节）
<从实现契约（fv-impl-contract）里摘出本卡 formal_ops 对应的每个操作：
 - derived 里该操作的 guard / reads / writes / atomic_required 与 reasons / contended_by（模型定下的，不能改）
 - code（文件、符号）、atomicity（机制、范围、evidence）、idempotency（键、evidence）
 - failures 的四类（error / timeout / conflict / retry）各自的行为与 model_effect
 - 覆盖这些操作的 acceptance.tests：argv 与 must_fail_with
 以及 state / observables 里本卡会碰到的映射。契约文件本身路径：<impl-contract.yaml>>

## 约束
- 只改 allowed_files；forbidden_files 一律不动
- 有形式化实现契约时：按契约实现，不按自己的理解重新设计；atomicity / idempotency 的 evidence 要逐字出现在代码里；
  覆盖本卡操作的 acceptance.tests 要通过，must_fail_with 要在坏变体上失败。契约、模型、合同都只读——契约做不到就回报
  `CONTRACT_CHANGE_NEEDED`，不改契约（Quint quint-execute-spec：never modify the spec to make a failing verification pass）
- 每个 commit：`python3 <plugin>/skills/commit/scripts/verify_commit.py --msg-file <msg> --card cards/CARD-xx.yaml --lock .done_when.lock`
- 做完：`aidlc_state.py card CARD-xx --status done --commit <sha>`
- 卡外问题：记在回报里，不修
