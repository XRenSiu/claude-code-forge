# 实现输入 — CARD-xx（这是实现者能看到的全部）

## 卡
<粘贴 cards/CARD-xx.yaml 全文>

## 状态摘要
<`python3 <plugin>/skills/sdlc/scripts/sdlc_state.py show` 的 slug / stage / branch / lock.path / cards.items[CARD-xx]>

## AC 子集（来自 done_when.yaml，只含 ac_ids）
<逐条：id / observe / given / expect>

## 红基线
<测试名 → 在 <base-sha> 上失败的一行输出；无测试的 AC 列 `no-tests-for:`>

## 约束
- 只改 allowed_files；forbidden_files 一律不动
- 每个 commit：`python3 <plugin>/skills/commit/scripts/verify_commit.py --msg-file <msg> --card cards/CARD-xx.yaml --lock .done_when.lock`
- 做完：`sdlc_state.py card CARD-xx --status done --commit <sha>`
- 卡外问题：记在回报里，不修
