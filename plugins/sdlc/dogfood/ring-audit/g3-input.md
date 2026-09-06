# G3 输入 — sdlc-ring-audit（编排者汇集；G3 代签者必读）

> checklist_G3.md 在 l5 锁内，本轮不改；本文件补充 checklist 未列而 G2 裁决（failure-report-002 条件 4）与各卡实现者要求 G3 看的项。变体文件内容不引入此处。

## 必读（failure-report-002 条件 4）
- `.sdlc/sdlc-ring-audit/hidden/ring-audit/holdout_run.json` 与 `holdout_manifest.yaml`（judge 可读，implementer 不可）：holdout 6/10，4 个未命中即 known_gaps KG-01..04。
- `plugins/sdlc/dogfood/ring-audit/calibration/known_gaps.yaml`（11 项）· `calibration_report.yaml` · `failure-report-002-holdout.md`（八项条件）。
- A6（AC-006-a）的 F-14 答案措辞必须是 "instrument mutation 0.767; holdout 6/10 with 4 known gaps"，不得无限定写 calibrated。

## 各卡实现者提请人裁的项（原文见各卡回报；均已编进片段的 adjudications / proposals）
### CARD-02（R0,R1,R2,spine）
1. F-06 封顶粒度：字面执行"checked_by 为空的 Artifact 的 producer 不得高于 declared"会把 dos-extract 压回 declared（dos.yaml 有闸、decisions.md 无闸），与 PSL-010 冲突；片段按"独占 Artifact"判，解释写在文件头。请 G3 裁。
2. F-16 与 audit.schema.md 的 disposition 枚举不一致：形态 F-16 `fix_list | issue | none`；schema `none | issue` 并把 fix_list 移到 Proposal.destination；check_audit.py 两者都不检。片段按 schema。请 G3 裁并进 change-proposal-002 候选。
3. R010 / R017（unenforced_rule 来源）不在 R0–R2/spine：R010 落 R3/R6、R017 落 R3/R8——CARD-06 装配时须核对四条宪法规则 R001/R008/R010/R017 各至少登记一次，否则 PSL-017"三种来源都登记"不成立。
4. naming 维 14/14 fits（F-03 同词干即 fits）——若其他环也零 misfit，这一维是否还有区分度请 G3 一并看。
### CARD-03（R3,R4,R5）
5. `card.allowed_files` 有两个非豁免生产者（implement / agent.comment-fixer；F-05 三条件仅满足 1 条）→ 双方 merge_candidate；提案 P-R5-01（给 comment-fixer 独立产物名，或把 R001 降为文档规则）。
6. agent.comment-fixer 的环有争议：Node.role=implementer → R5；ARCHITECTURE §1 宿主 review-loop → R7；loops.yaml 称其为 review_loop generator 而 graph 节点无 loop 键。记 R5 + 双源 ring_evidence（F-08/F-24）；提案 P-R5-02。
### CARD-05（R7,R8）
7. agent.pr-reviewer 判 `implemented: compiled` 有争议（拒的闸是 verify_pr.py --pre-review 作用于下游 Known issues 段，不是 agent 自己的 findings 文件）；`declared` 的异议记在该 Part 的 adjudications。
8. 上游名 code-reviewer 被收编为 pr-reviewer，与 R6 的 code-reviewer skill 撞名——提案 P-R7-01。
9. graph.yaml 里 human.harness-review 与 pr 的 writes 都是字面 `github:pr`（两个不同 PR，却读作 R001 双生产者）；harness-review 节点无 loop 字段而 loops.yaml#L111 称其为 hill_climb verifier——提案 P-R8-06。
### CARD-04（R6）
10. agent.review-triager / agent.fix-verifier 的环：graph.yaml role=evaluator → R6；ARCHITECTURE §1 把 review-loop 整条线列在 R7。双源写进 ring_sources，未调和。请 G3 裁（与第 6 项同一根因：review-loop 宿主的 agent 归属）。
11. 计算原语算不算闸：meta-judge / spec-gaming-detector 的脚本除 IO 错误外永不非零退出，实现者据此判 `declared` 而非 `compiled`——本片段最可争的判断，请 G3 裁（与 CARD-05 第 7 项、retro metrics.py 的同类问题一并看）。
12. `meets_done_when` 的两个洞登记为两个 Gap（没有脚本去算 / 就算有也拦不住直接 set），而不是一个。请 G3 确认粒度。
13. 实现者审出的 sdlc_state.py 四处：G3 pass 无输入前置；`advance pr` 不检 evaluation_result 路径存在；`acceptance.meets_done_when` 在 SETTABLE 里（R010 落点）；delegated_agent 授权只是自由文本（R008 落点）——这些是本 Run 自己正在用的机制，G3 裁 AC-006-a 时应把"代签授权只是自由文本"这一点读进去。
### CARD-06（装配）
14. 装配者加了形态未命名的顶层 `suspected_duplicate_pairs[]`（AC-005-a 要求 pr-review vs code-reviewer 对照，跨两张卡无法在片段里记）；非承重——render_audit.py 从 artifacts[] 现算并在不一致时打"登记 ≠ 现算"，5 条目前一致。这是 G2 冻结形态之外的键，请 G3 裁：接受为投影辅助，或进 change-proposal-002 入形态。
15. 报告底线（由文档计数而非手写）：42 个 Part 中 16 停在 declared、26 在 compiled、**0 个 verified**；三道门两道是代签、G3 待定；外部证据为 substitute。
16. KG-02（proposal source 解析无闸）：装配者手工核对 39 条 source 全部可解析——这是人读替代，不是机械证据。
17. run_evidence 的 replay 计数是快照（记录时 8 条 Card 提交，现已更多；不漂移的是三个被审目录的 diff --stat = 0）。
18. 一条 adjudication `resolved_by: pending_G3`（agent.pr-reviewer 的 implemented 档位，见第 7 项）。

## g2-judge 对 nh-003 的裁决与对 G3 的额外必读（2026-09-06）
- nh-003：全部无 footer 提交合法——587f371 / ebe270d / c729f76 是 PSL L122-123 允许的偏差提交（账本 deviation 行，含 2026-09-06 补录）；e217d10 是 change-proposal-001 的重锁（合法性来自锁机制）；fafcad7 / 5a6889c 只碰 cards/*.yaml 与 skill-issues.md，**不在** forbidden_paths（评审前提有误）。逐提交表：`commit-table.md`。
- 记录义务：AC-007 回放与 run_evidence 的门/锁签字由**修复后**的验证器版本（587f371 / ebe270d / c729f76）产生；重签者 g2-judge 与实现者同厂商同会话族（用户授权下允许；srg-006 规则进 change-proposal-002）。
- 解码先例（I-68 的 3 ≤ score < 7 带）：iteration-002 若 NEEDS_HUMAN 仅因 human AC、0 blocking、score ≤ 3.5、P1 全修或入 Known issues → PASS-pending-G3；G3 裁的是 iteration-002 的字节，iteration-001 是历史。
- G3 额外必读：`ratchet-log/iteration-002/` 全部；meta-judge 的 14 条 deduplicated_findings 全表（不止 nh 点名的四条：mf-011 tune 的 F-06 封顶；mf-004；mf-010 F-10/F-11 空态措辞；mf-013 "exit 0 可作证据" 来自自报——G3 应自己重跑 check_audit.py、--variant delete-ring:R6、replay_card_commits.sh；mf-002/003；mf-006/008/009/014）；spec-gaming-detector 的 srg-001..007（尤其 srg-005 F-05 三条件未检、srg-006）；pm-reviewer out_of_scope_observations[0..3]；qa caveats；PSL L122-124（偏差豁免与"报告人审即 G3"）；isolation.json 与 calibration_report 的 isolation_evidence（协议级隔离，非 OS 级）；修复后 AUDIT.md 的 checked_by 列与所有 pending_G3 的 adjudication；报告底线 "0 verified / 26 compiled / 16 declared，三门两代签，G3 待定"。
19. （FIX round，impl-fix-002）audit.yaml 又加了一个形态未命名的顶层键 `unenforced_rules[]`（id / name / enforced_by / dos_anchors），用于把四条宪法规则的登记从硬编码改为按 evidence.ref 计算；与 `suspected_duplicate_pairs[]` 同类。请 G3 一并裁：接受为投影辅助，或进 change-proposal-002 入形态。
20. g2-judge 条件（nh-003 (7)）要求修复后回放的 `non_card_commits_touching_audited_dirs` 显示 587f371 / ebe270d / c729f76 / bf3f13e：回放的范围按 AC-007-a 的 given 从首个 Card 提交起算，这四条在范围之前，该字段为 0；四条的分类在 `commit-table.md`（footer / 被审目录 / forbidden 三列）。请 G3 确认这样满足记录义务，或要求把回放范围扩到 origin/main。

## g2-judge 对 iteration-002 的解码（2026-09-06）与对 G3 的再补充
- 解码 C（A 加硬条件）：FIX-003 两条有序 Card 提交（CARD-01 回放脚本先落 shipping 分支；CARD-06 从该 HEAD 分出、在提交前于 base sha 上跑修复后的回放并机械复制 JSON 进 run_evidence），card 预算 2/3 → 第 3、4 次 card fail 的两次升级由本裁决豁免（最后一次授予；之后归用户）。iteration-003 = 受影响评审（security / logic / qa / pm / gaming / drift）+ meta-judge。解码门：NEEDS_HUMAN 仅 rule 3、0 blocking、gaming ≤ 3.5、stale-sha 与 exit/ok 两类缺席、mf-003 关闭、无 fix-pressure-induced。
- 记录更正：先前裁决禁止的是"评审后改写 shipping 分支历史"，不是 cherry-pick；教训是 run_evidence 里的 sha 必须在 shipping 分支上产生。pr-body.md 已改。
- G3 再补充：iteration-003 的 meta-judge 输出；mf-009 作为 G3 tech 裁项（F-06 封顶：R6/human_gate.G3、R7/agent.pr-reviewer、R8/tune 记为 compiled 而其所有 Artifact checked_by 为空；"任一 Artifact"还是"独占 Artifact"的读法）；nh-003 / nh-004 清单；在 shipping 分支上复现 check_audit.py、delete-ring 孪生与 replay_card_commits.sh 的确切命令（见 pr-body.md#Verification）。
- nh-004（无锁定测试覆盖本轮修复）→ change-proposal-002 测试清单：AUDIT.md golden-file 字节比对；atoms/id 含 `|` 的 fixture；signer_kind 人签 / agent 变体；含重命名移出与非 ASCII 路径的孪生仓库；空 main..HEAD 范围 exit 0 + card_commits 0；gates[] kind human_gate 条目。

## g2-judge 对 iteration-003 的终局解码（2026-09-06）与 G3 的最后一批必读
- 裁决：**ship as reviewed**，acceptance.evaluation_result = `ratchet-log/iteration-003`（快照 4ddb362；HEAD 上实现字节与之逐字节相等，见 `impl-equals-head.txt`），推进到 pr。不开 iteration-004。
- **AUDIT.md L976 的行是错标的**：它写"自第一个 Card 提交起"，而 yaml 的窗口是 `merge-base(main,HEAD)..HEAD`（4d3057a..HEAD），且那四条提交（587f371 / ebe270d / c729f76 = PSL L122-123 偏差提交；bf3f13e = peer）**全部早于**第一个 Card 提交。该标签下的真值是 **0**。真相在 `audit.yaml#run_evidence.audited_dirs_diff.non_card_range_spec` 与 `non_card_commits_touching[]`，以及 `commit-table.md`。AUDIT.md 未被手改（字节稳定渲染不变量）。
- mf-009 作为明确的 **G3 tech 裁项**：R6/human_gate.G3、R7/agent.pr-reviewer、R8/tune 记 compiled 而其每一个 Artifact 的 checked_by 都为空（F-06 封顶；"任一 Artifact"还是"独占 Artifact"的读法）。
- mf-011：holdout 见证单元格把 `attested_by_kind` 原样打出（本次值 delegated_agent，渲染正确，但未走封闭映射）。
- **隔离披露**：drift 本轮的 11 条信号是在能看到 qa 报告的情况下产出的（其 `--qa-report` 参数与 fleet 的无串扰铁律冲突，I-71）；g2-judge 裁为有界接受，未打折。
- gaming 轨迹实为 [3.5, 4.0, 4.0]**持平**（检测器被编排者的任务文件错传基线 3.5，I-72）。
