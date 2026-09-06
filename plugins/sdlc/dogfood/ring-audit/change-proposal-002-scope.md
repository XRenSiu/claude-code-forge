# change-proposal-002 — 范围登记（尚未开启；本文件是"去处"，不是提案本身）

> 本次 run 所有 **defer** 的项在这里落地，避免"记了没去处"。开启顺序由 g2-judge 在 iteration-002 解码里定死：
> **先开一轮 G1 解释**（下面 A 段的六条读法分歧），G2 冻结 G1 裁定的读法，**再**由 l5-tests 编谓词与测试，**最后新造一份隐藏集**（本次的 4 条未命中已因 failure-report-002 曝光而作废）。
> 在 G1 裁定之前，`known_gaps.yaml` 对仪器现行行为的描述一律标 **de facto，不是已裁**。

## A. 必须先过 G1 解释轮的读法分歧

| id | 分歧 | 现行（de facto） | 出处 |
|---|---|---|---|
| mf-004 / KG-08 | 规则 2e 的"同环"子句是否适用于 `fills[]` | 适用（比 G1 文本严） | G1 签字版解释规则 2(e) 只对 `missing[]` 说同环 |
| mf-010 | `--rings` 是否可以让 `ring_unexpected` 失效 | 失效 | F-17「不改任何既有谓词」 |
| mf-011 / KG-02 | AC-004-b 的 `source` 是"键非空"还是"可解析" | 键非空 | AC-004-b given 措辞；G3 已实测 39/39 可解析 |
| mf-013 / srg-005 | `alternatives_of` 任意非空即豁免，还是须过 F-05 三条件 | 任意非空 | F-05 三条件 |
| mf-020 / 第 2 项 | `disposition` 枚举以 F-16 还是 `audit.schema.md` 为准 | schema | F-16 `fix_list \| issue \| none` |
| ~~**mf-009（G3 已裁）**~~ **已落地** | F-06 封顶按"任一 Artifact"还是"独占 Artifact" | ~~三处记 compiled~~ → **三处已改为 declared** | G3 裁定生效：R6/human_gate.G3、R7/agent.pr-reviewer、R8/tune 各写 `not_reached.compiled` 说明为什么无闸；`AUDIT.md` 重渲染后自算的底线为 **19 declared / 23 compiled / 0 verified**。仍留在本表里的是**读法本身**：F-06 的"任一 vs 独占"要进 G1 解释轮并编成谓词（G3 Open Question 1），否则下次同样的分歧还得再裁一遍 |

G3 的 Open Question 1 同属此段：若接受其裁法，`checked_by == [] ⇒ implemented ≤ declared` 应编进 `check_audit.py`，且需与 F-17 对账。

## B. 谓词 + fixture + 测试（G1 裁定后）

- KG-01 waiver_ref 字段与 token · KG-03 `ring_duplicate`（rings 计数 ≠ 环集合）· KG-04 `signer_kind_outside_enum` · mf-006 `gate_kind_outside_enum`
- KG-05..KG-11：七个存活仪器变体 M03 / M04 / M07 / M14 / M22 / M23 / M28
- mf-012 exit-2 路径恒出 JSON · mf-015 注册表可选性 · mf-017 注册表 6 vs 8（`unenforced_rules[]` / `suspected_duplicate_pairs[]` 入形态）· mf-018 token 命名 · mf-019 / mf-014 `audit.schema.md` 前言过时
- **mf-002（G3 C-2）**：`AUDIT.md:976` 的"自第一个 Card 提交起"错标 + `non_card_range_spec` 与命中清单未渲染
- **g3-input 第 18 项的 adjudication（G3 C-2）**：`agent.pr-reviewer` 的 `implemented` 档位 `resolved_by: pending_G3` → 按 mf-009 的裁法收敛为 declared

## C. nh-004 —— 本次两轮修复无一有锁定测试

golden-file 逐字节比对 `AUDIT.md`；`atoms` / id 含 `|` 的 fixture；`signer_kind` 人签 / agent 变体；含 CJK 路径与"重命名移出被审目录"的孪生仓库；空 `main..HEAD` 范围须 exit 0 且 `card_commits` 0；小写 `card:` footer 的提交须**恰好**出现在一遍里。

## D. harness / 契约规则

- srg-003 → **AC-007-c**：无 footer 提交触碰被审目录作为**记录字段**（不门控；PSL L122-123 的偏差提交合法）
- srg-006 → 实现期间**重签者**规则（本次重签者与实现者同厂商同会话族）
- I-68 → acceptance-fleet S3 在 `3 ≤ gaming_risk_score < 7` 无规则（本次先例已入账本）
- I-69 → `pr-poll.sh` 单协作者模式：更严的谓词（无 CHANGES_REQUESTED ∧ 0 未解决 ∧ checks 绿且"无 checks"与"绿"分开 ∧ 至少一轮记录在案的隔离对抗评审且 0 条 A 档存活）
- I-71 → acceptance-fleet 的无串扰铁律与 dispatch matrix 的 `--qa-report` 冲突
- I-72 → 迭代间参数（baseline / history / prev-review）机械传递
- I-73 → plan-cards：**投影与其数据源必须同卡**
- I-76 → CLAUDE.md 版本同步规则编译成 `/commit` 或 `/pr` 的机械检查
- I-80 → 修 fail-open 的回归孪生必须附变异证明（把旧实现装回去，孪生必须变红）
- cr-003 / I-77 → `verify_derived.py` 的引用行剥离限定在前言
- I-82 → `pr-poll.sh` 的 `checks_green` 拆三态（`green` / `none_configured` / `red`），`done` 不得把「没配 check」判成绿
- **I-83（G3 补裁）→ `review.done` 拆成 `done` / `waived` 封闭枚举，或强制 `waiver_ref` 指向账本事件 id**；与 KG-01（waived 无 waiver_ref）、gate 的 `--authorization` 自由文本是同一个病：布尔字段宣布完成，限定语躲在没人解析的散文里

## E. G3 的 Open Questions（需要人定，不由本提案单独决）

"闸"是否定义为"存在非零退出路径"（写进 `audit.schema.md` 或 PSL）；naming 维（41/42 fits）是留作 advisory 还是补第二谓词；`--authorization` 是否收成"指向一份人写的授权文件并检存在"；**本仓库无任何 CI**（`statusCheckRollup` 为空，所有"绿"都来自本地手跑）——G3 称其为"比任何一条 finding 都更基础的空隙"。
