# 变更提案 — change-proposal-003.md

> G2 之后改被锁文件（done_when.yaml / contract.yaml / tests/** / role=gate 的脚本）的唯一合法路径：同一 diff 附带本文件。
> 没有它，锁定检查（A 档）直接拒绝。有它，放行并计入 task_reflows。

**日期**: 2026-09-06　**提案人**: 编排者（重审阶段）　**签字人**: reaudit-orchestrator（delegated_agent；授权：用户 2026-09-06「把所有没有完成的都完成，需要人做的你就帮我做了当做人做的」）

## 改哪条

被锁文件改动四处：

| 文件 | 锁内角色 | 改前 | 改后 |
|---|---|---|---|
| `check_audit.py` | `gate` | `load_psl_index` 接受空索引并返回空集；`psl_id_unknown` 由 `elif psl_ids:` 守卫；不传 `--psl` 时 `psl_ids = set()` | 空索引 `die(..., 2)` 并点名缺的是 `规律索引` 节；守卫改成 `elif psl_ids is not None:`；不传 `--psl` 时 `psl_ids = None`（"没给尺子"），`psl_index_size` 随之为 `null` |
| `replay_card_commits.sh` | `gate` | 回放历史 Card 提交时，把**工作区当前**的 `.done_when.lock` 传给 `verify_commit.py`；锁路径由工作区存在性探测 | 改用**父提交**的锁（`git show <sha>^:<lock 路径>`）；锁路径改为按位置解析、不要求此刻存在 |
| `tests/ring-audit/test_check_audit.py` | `contract` | REQ-002 只有 `test_AC_002_b_empty_psl_ids_exit1_psl_id_missing`（契约侧：某一维的 `psl_ids` 为空） | 追加一对孪生：`test_AC_002_b_empty_psl_file_exit2_not_silently_green`（读取侧：空 PSL 文件必须 exit 2 且 stderr 点名 `规律索引`）与 `test_AC_002_b_no_psl_flag_still_runs`（不传 `--psl` 仍合法，`psl_index_size` 为 `null`）。34 → 54 个方法里新增 2 个 |

| `tests/ring-audit/tests-manifest.yaml` | `contract` | `unit_tests.example_based` 与 `test_to_ac.AC-002-b` 各列 1 个方法 | 各补上新增的两个方法名 |

`done_when.yaml`（20 条 AC）与签字版形态 `derived/form-draft.md` **一个字节不改**。测试数由 `derive_counts.py` 从契约与清单现算，加方法必须同步清单：不同步则 smoke 的 "the derived counts add up to the methods in the file (I-54)" 立刻变红——本次就是这样被抓住的，不是靠记得。

## 为什么

`check_audit.py` 是给整份审计盖章的那道闸。喂它一份**空的** PSL 文件，它 exit 0；喂它一份**写错的** PSL（一条不存在的 PSL-999），它 exit 1 并报出 126 处 `psl_id_unknown`。

也就是说：越没有证据，结果越绿。

根因是 `elif psl_ids:` 这个真值守卫——空集是 falsy，于是"审计引用的每个 PSL id 是否都在那份 PSL 里"这条谓词整条蒸发，而输出里 `psl_index_size: 0` 是唯一的痕迹，没有任何一处把它当成问题。`verify_psl.py` 早就在**写入侧**拒绝"没有任何 PSL-NNN id 的 PSL"（I-02），本提案把同一条规则补在**读取侧**。

区分两件事是这次改动的要点：**没给尺子**（不传 `--psl`，closed-set 检查照旧跳过，合法）与**给了把坏尺子**（传了 `--psl` 但里面一条规律都没有，拒绝）。把它们混为一谈正是这个 fail-open 的形状。

发现路径值得记：PR #3 的隔离预审在自己的报告里更正了一处——它先前说"findings 文件过了校验器，exit 0"，实际是它抽出来的校验器文件是 0 字节，而**空 Python 文件退出 0**。顺着这条"空输入让量具静默通过"去查同类，才撞上 `check_audit.py` 这一处。缺陷登记为 I-99。

证据：
- `python3 check_audit.py audit.yaml --psl <空文件>` → 改前 exit 0 / `ok: true` / `dims_with_unknown_psl_id: 0`
- `python3 check_audit.py audit.yaml --psl <只含一条 PSL-999>` → exit 1 / `dims_with_unknown_psl_id: 126`
- 变异证明：把本提案的改动整体退回，`test_AC_002_b_empty_psl_file_exit2_not_silently_green` 立刻变红（53 passed, 1 failed），装回则 54/54

## 第二处改动：回放的读数不能取决于此刻的锁（I-101）

本提案给 `check_audit.py` 重签锁之后，`test_AC_007_a_replay_card_commits_exit0_touching_zero` 立刻变红：`replay_card_commits.sh` 报 `replay_reject: 1 Card commit(s) were rejected`。

被拒的是 `9b87b95`（"compile G1 解释规则 4-10 into check_audit.py"）。它落地时 `check_audit.py` **还不在冻结集里**——是后来 change-proposal-002 重签时才把它作为 `role=gate` 加进去的。回放拿今天的锁去审判昨天的提交，于是一条当时完全合法的提交，被追溯性地判成"改了锁内文件却没带提案"。

这不是那条提交的问题，是量具的问题：**PSL-003 的读数必须只取决于被审的那次提交，不取决于此刻的锁**。否则每一次 l5 重签都会追溯性地推翻过去每一条判决，而 `run_evidence.audited_dirs_diff` 里记的 `ok: true` 会在没有人改动任何提交的情况下变成 false。

改法：回放每条提交时用 `git show <sha>:<lock 路径>` 取那条提交当时的锁；该提交树里没有锁文件就不传 `--lock`（早期提交本来就没有 G2 锁）。

变异证明：把这一处退回成传工作区的锁，`test_AC_007_a_replay_card_commits_exit0_touching_zero` 立刻变红（53 passed, 1 failed）；装回则 54/54，`replay_card_commits.sh` 自身 `ok: true` / `card_commits_rejected: 0`。

## 第三处改动：锁要取父提交的，不是提交自己的（I-104）

第二处改动最初写成"取**这条提交自己树里**的锁"。隔离预审 round-4 的 F-7 打的正是我请它打的那个点——"改用历史锁之后会不会反而放过本来该拒的东西"——它打中了：

一条在同一个 diff 里**删掉 `.done_when.lock`** 的提交，会因为"该 sha 上没有锁文件"而被免检，它在同一次提交里对锁内文件做的任何改动都不再被拒。判据的来源被交给了受审对象本身，正是本提案给 I-100 写下的那句话的另一次发作。

外层还有一半同样的病：锁**路径**原本由工作区存在性探测（`[ -f "$candidate" ]`），于是把分支尖上的锁删掉，整条锁检查直接短路。

改法（预审给的）：取 `$sha^` 的锁——"这条提交动手时生效的规则"。它仍是历史锁，I-101 要修的"回放不能取决于此刻的锁"完全不受影响；同时锁路径改为按位置解析，不要求此刻存在。父提交没有锁文件才不传 `--lock`（真正的早期提交，本来就没有 G2 锁）。

两臂对照固化成 smoke 期望，附带一次性 git 仓库（`plugins/sdlc/eval/fixtures/replay_lock_arm.sh`）：
- 删锁的 Card 提交必须被拒（`ok: false`）
- 从无锁的历史上的 Card 提交必须放行（`ok: true`）

变异证明：把取锁的 sha 退回 `$sha`，A 臂那条期望立刻变红（`[got 0 want 1]`）。

## 归因层

- [x] task（判据写错 / 写漏）——契约的 AC-002-b 只写了"某一维的 psl_ids 为空"，没写"整份 PSL 为空"；判据漏了读取侧那一半，形态字节不动
- [ ] ontology（DOS 不变量冲突）
- [ ] world（PSL 规律冲突 → 应重开 G1）

X2：本 PR 不是一次被 `sdlc_state.py` 跟踪的 run（PR #2 的 run 已 archive），所以不写 `fail --signal lock_hash_mismatch` 到那份已归档的状态里；回流按 task 层记在本文件与 `skill-issues.md` I-99。

## 重新冻结

- 锁文件项数不变（60），四项内容更新（`replay_card_commits.sh` 因 F-7 二次更新）：`check_audit.py` 与 `replay_card_commits.sh`（均 role=gate）、`tests/ring-audit/test_check_audit.py` 与 `tests/ring-audit/tests-manifest.yaml`（role=contract）
- 重签命令与新 sha 见下方"签字"节；stage 仍为 `l5`，签字人 `reaudit-orchestrator`（delegated_agent，授权同上）

## 一个连带发现，本提案不修

`lock_done_when.py verify` 在被锁文件有改动时判 `changed_with_proposal`，而它认的"提案"是**目录下存在任何 `change-proposal-*.md`**，不核对提案是否针对本次改动。也就是说 001 与 002 这两份历史提案，足以让今后任何一次锁内改动过闸。

这与本提案修的是同一族：一条闸的通过条件写成了"存在某个东西"，而不是"存在**这一次**的那个东西"。登记为 I-100，去处见提案 P-RA-08，**本次不改**——改它要动 `lock_done_when.py` 的判据，而那正是本提案赖以生效的机制，同一个提交里既改判据又用判据放行自己，是把裁判和运动员合一。
