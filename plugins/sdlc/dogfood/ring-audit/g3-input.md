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
