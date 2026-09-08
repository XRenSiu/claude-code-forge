# 分歧集 — sdlc-ring-audit

n: 3                       # 独立推导次数（三个全新上下文，只读 PSL + 模板，互不可见）
consistent_decisions: 14   # 全部版本一致的决策点数（= PSL 真正约束住的）
divergent_decisions: 7     # 分歧率 7 / 21 ≈ 33%，< 50%，允许合并；每条分歧是 G1 的一项议程

> 对齐方法（references/derivation.md）：三版 F-nn 编号不同，按语义对齐到 21 个决策点。选择相同且引用相同 → 一致；
> 选择相同引用不同 → 一致但记"多源"；选择不同 → 分歧。**不用多数表决消灭分歧**——合并稿里分歧点带 `[D-n]` 标记与临时取向，最终由 G1 定。

## 一致的决策点（PSL 约束住了）

| 决策点 | v1 | v2 | v3 | 引用 |
|---|---|---|---|---|
| Finding 与 Part 一对一，四维各 {verdict, psl_ids≥1, evidence} | F-03 | F-01 | F-01 | PSL-002/003/010/014/017（多源） |
| implemented 不得是布尔，每已达态带证据，未达态显式写出 | F-04 | F-02 | F-02 | PSL-010 |
| naming = 来路（authored/adopted）+ 贴合 + suggested_name，无重命名动作 | F-05 | F-07/F-17 | F-03 | PSL-014 |
| Gap 原子 ⊆ 四原子；空集 = overfill；needed 必带 deletion 一句话 | F-06 | F-04 | F-04 | PSL-016, PSL-002 |
| Artifact 单生产者；争产物 → 两者都 merge_candidate，审计者不裁 | F-20 | F-03/F-15 | F-05/F-20 | PSL-001 |
| Finding 状态 candidate/evidenced/adjudicated；裁决只追加不改写 | F-07/F-23 | F-09 | F-07 | PSL-005, PSL-006 |
| 报告按 Ring（R0–R8 + 脊柱）分节，一 Ring 一表，一 Part 一行，四列内联 PSL-ID | F-10 | F-10 | F-10 | PSL-011 |
| "缺少"节必存在（可为空），每条带必要性 + deletion 一句话 | F-11 | F-08 | F-11 | PSL-017, PSL-002 |
| 报告与 audit.yaml 同构，报告头给出 yaml 与脚本路径 | F-12 | F-11 | F-10 | PSL-015 |
| 检查脚本 exit 0 ⇔ 九环齐 ∧ 四维齐 ∧ psl_ids 在索引内 ∧ missing 在 ∧ 无双生产者；删任一环 → exit 1 | F-13 | F-12 | F-13 | PSL-004, PSL-015 |
| run_evidence 节：状态路径、每道门 signer + signer_kind + 授权记录 | F-14 | F-14 | F-12 | PSL-006, PSL-010 |
| 提案清单是 Finding 去向字段的投影，不是实体；命名不贴合 → 只能 issue / none | F-15 | F-13 | F-15 | PSL-014, PSL-013 |
| needed 上 deletion 测试与闭合所需冲突 → 并列两句、verdict 待 G1/G3 | F-21 | F-16 | F-21 | PSL-002, PSL-006 |
| 明确不做：布尔勾叉清单 / 重命名 / "环显得单薄"式补件 / 改被审文件 | F-90–92 | F-90–92 | F-90–93 | PSL-010/014/002/003 |

## 分歧（每条是 G1 的一项议程）

| # | 决策点 | v1 | v2 | v3 | 各自引用 | 议程（改 PSL-xxx / 请人定 / 补 Mental Model） |
|---|---|---|---|---|---|---|
| D-1 | implemented 的态数 | 五阶：blank / declared / compiled / verified / calibrated | 三态 + verified 时附 `calibrated: bool` | 三态，可加 calibrated 作第四值 | PSL-010, PSL-007 / PSL-010, PSL-007 / PSL-010 | **改 PSL**：Domain Model 写"三态"、State Machine 写五态（含空白、已校准），PSL 自相矛盾；建议 Mental Model 与 Domain Model 统一为"三态 + 两个边态（空白归 missing，已校准归 PSL-007 的附注）"，请人定 |
| D-2 | Gap 在 audit.yaml 的落位 | 一等顶层列表 `gaps`，带 ring / atom / state / necessity | Part.gaps（原子子集）+ 顶层 `missing:` 装无 Part 的 Gap | Gap 记录带 state，每个 Ring 自己的 `missing` 键 | PSL-017, PSL-002, PSL-016 / PSL-016, PSL-002, PSL-017 / PSL-016, PSL-002 | **补 Domain Model**：PSL 只写 "Part 填 0..n Gap"，没写 Gap 归属于 Ring（三版都自己发明了 Ring HOSTS/EXPOSES Gap）；建议 Domain Model 关联段加 "Ring 暴露 0..n Gap"，落位随之定为"每 Ring 的 missing" |
| D-3 | 没有任何 Gate 检的 Artifact 的后果 | 只记录 gates 为空 | 自动生成一条 Gap 进 `missing:` | producer 的 implemented 不得高于 declared，evidence 写 `no_gate` | PSL-016, PSL-001, PSL-015 / PSL-015, PSL-006 / PSL-015, PSL-006, PSL-010 | **补 Workflow φ**：PSL-015 说"产物要么被脚本检要么被门挡"，没说违反时的判定后果；建议采 v3（无 Gate ⇒ 最高 declared）并把 v2 的"生成 Gap"作为可选，请人定 |
| D-4 | 两类"缺少"（lifecycle 空白 / 本次新识别）是否分标签 | 各带标签不混排 | `source ∈ {lifecycle_blank, newly_identified}` | 同列不分级 | PSL-017, PSL-002 / PSL-017, PSL-002 / PSL-017, PSL-002 | **补 Mental Model 一句**：现文只说"两种都要诚实登记"，未说是否区分；建议区分（来源不同，去向不同：空白已登记在 lifecycle.md，新识别要开 issue） |
| D-5 | 检查脚本的自校准是否是证据的必需项 | 脚本对删环变体 exit 1 是脚本性质 | 同 v1 | 同一运行里没跑过删环变体的 exit 0 标 `uncalibrated`，不算证据 | PSL-004, PSL-015 / PSL-015, PSL-004 / PSL-007, PSL-010 | **请人定**：v3 的读法与 /calibrate（未校准的标准不当证据）一致，代价是每次运行多跑一次变体；建议采 v3 |
| D-7 | audit.yaml 顶层形状 | 按 Ring 键的 mapping（十个键） | 未定，报告是 yaml 的投影、yaml 为准 | `rings[].parts[].finding` 嵌套列表 | PSL-011, PSL-017 / PSL-015 / PSL-011 | **请人定**（实现细节，两种都满足检查脚本谓词）；建议 `rings:` 列表（保序、可加 id/question 字段） |
| D-8 | Gate 与 Part / Finding 的关系 | Gate 只经 Artifact 挂到 Part | 加 Part CARRIES Gate 1:1 | 加 Gate ADJUDICATES Finding 1:N | PSL-015 / PSL-015, PSL-006 / PSL-006, PSL-005 | **补 Domain Model**：关联段只写 "Artifact 被 0..n Gate 检"；Finding 的裁决（G1/G3）是谁做的没写成关系；建议加 "Gate 裁决 0..n Finding（仅 kind=human）"，不加 Part CARRIES Gate（Gate 检产物不检配件） |

## PSL 欠定（推导中出现、PSL 里找不到依据的实体或决策）

- **Proposal（提案）** — 出现在 v1 / v2 / v3；Workflow φ 与 UI Contract 要"提案清单每条有去向"，Domain Model 无此实体。三版都压成 Finding 的去向字段。建议：**进 open_questions**（若提案需要 owner / 状态 / 生命周期则升为实体）。
- **Evidence（证据）** — 出现在 v1 / v3；State Machine 列了四种证据来源但无 schema，机器只能检非空。建议：进 open_questions。
- **Signer / Authorization（签字人 / 代签授权）** — 出现在 v1 / v2 / v3；Acceptance 要求可见，Domain Model 无实体，三版都挂在 Gate / adjudication 字段上。建议：**进 Domain Model**（本次运行恰好是代签，承重）。
- **Run（本次运行）** — 出现在 v1 / v2 / v3；Mental Model 说"审计本身是一次 sdlc 运行"，但没有 Run 实体，v3 的跨运行指纹（F-23）是即兴。建议：进 open_questions；F-23 暂不进合并稿。
- **skill 源码问题** — 出现在 v1；γ 说进 skill-issues.md，但它不是 Finding 维度也不是实体。建议：进 open_questions（是否算 Part 的 implemented 逆向流转证据）。
- **Ring 的"问题"字段** — 出现在 v1；Domain Model 说每环回答一个问题但无字段。建议：进 Domain Model（一个字符串属性）。
- **Gap 的反向基数** — 出现在 v1；一个 Gap 能否被多个 Part 填未写，DOS 按 N:N。建议：补 Domain Model 关联段。
- **脊柱是否是一个 Ring** — 出现在 v3；UI Contract 写 "R0–R8 + 脊柱"，Domain Model 把脊柱与环并列；若脊柱是跨环容器，Ring CONTAINS Part 1:N 不成立。建议：**改 PSL Domain Model**（明确"脊柱按一条 Ring 记录处理，id=spine"）。
- **Gate 与 Loop.verifier 的关系** — 出现在 v3；Loop 有 verifier，与 Gate 重叠但未建关系。建议：进 open_questions。
- **PSL 规律是否是实体** — 出现在 v2；四维都引用 PSL-ID 但规律不是 Domain Model 实体，反向索引做不了。建议：舍弃（规律是元层，不进对象）。
- **F-91（不改被审文件）的验收挂钩弱** — 出现在 v1；只由 γ 约束可达，没有 Acceptance 问它。建议：**补 PSL Acceptance 一条**："问'审计动过被审目录吗' → 返回被审目录 git diff 为空"。
- **未被引用的规律 PSL-008 / PSL-009 / PSL-012** — `verify_derived.py` flag；三条都是关于"运行"（失败归层、合入不是终点、收敛≠正确），与上面的 Run 欠定同源：v3 用它们推出跨运行指纹决策（未进合并稿）。建议：**G1 决定**——删去这三条（对本 feature 是装饰）或补一个 Run 实体并恢复 v3 的 F-23。
