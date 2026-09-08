# 变更提案 — change-proposal-001.md

> G2 之后改被锁文件（done_when.yaml / contract.yaml / tests/**）的唯一合法路径：同一 diff 附带本文件。
> 没有它，锁定检查（A 档）直接拒绝。有它，放行并计入 task_reflows（X2 的"任务级回流"由此可数）。

**日期**: 2026-09-05　**提案人**: l5-tests（隔离的非实现者测试作者）+ 编排者　**签字人**: g2-judge（delegated_agent；授权同 G2：用户 2026-09-05 "需要人审核的地方，请你弄一个子agent代替我审核一下"）

## 改哪条

被锁文件改动两处：`tests/ring-audit/**`（l5 锁，33 个文件）与 `g1-record.md`（g2 锁；只**追加**一节解释规则）；`done_when.yaml`（20 条 AC，fb5af3f0…）与签字版形态 `derived/form-draft.md`（746c56ef…）**一个字节不改**（签前签后 sha 复核一致）。

| 文件 | AC / REQ | 改前 | 改后 |
|---|---|---|---|
| tests/ring-audit/fixtures/complete.yaml | AC-001-a · AC-004-a · AC-006-a（fixture 形状） | gates[] 含 5 个 human（G1/G2/G3/merge/harness-review）+ `exercised: false`；missing[] 为内联对象；无双生产者 | gates[] 只含 G1/G2/G3 + 脚本闸；signer 三元组移到 `run_evidence.gates[]`（verdict pending/pass/reject/waived）；顶层 `gaps[]` 带确定性 key，`parts[].fills[]` 与 `rings[].missing[]` 放 key；含一对已认领的双生产者（donewhen-extract / acceptance-spec → done_when.yaml，两者 merge_candidate） |
| tests/ring-audit/fixtures/mutant_human_gate_without_signer.yaml | AC-004-b 族 | 在 gates[] 的 G2 上删 signer | 在 `run_evidence.gates[]` 的 G2（verdict pass）上 signer 置空 |
| tests/ring-audit/fixtures/mutant_delegated_without_authorization_ref.yaml | AC-004-b 族 | 在 gates[] 上 | 在 `run_evidence.gates[]` 上 |
| tests/ring-audit/fixtures/mutant_gate_not_declared.yaml（新） | AC-004-b 族 | — | human.merge 列进 gates[] → exit 1 gate_not_declared |
| tests/ring-audit/fixtures/mutant_spurious_merge_candidate.yaml（新） | AC-004-b 族 | — | 单生产者 Part 却标 merge_candidate → exit 1 |
| tests/ring-audit/fixtures/mutant_overfill_unmarked.yaml（新） | AC-004-b 族 | — | fills 为空却未标 overfill → exit 1 |
| tests/ring-audit/fixtures/mutant_unknown_gap_ref.yaml（新） | AC-004-b 族 | — | missing/fills 引用不存在的 gap key → exit 1 |
| tests/ring-audit/fixtures/mutant_orphan_gap.yaml | AC-004-a | 内联对象缺 missing | 注入规则 2b 键 `R5/newly_identified/control/plateau-detection` 且不在其环 missing[] → exit 1 orphan_gap（断言 token） |
| 其余 16 个 mutant_*.yaml | 各自 AC | 旧形状 | 语义不变，仅随 complete.yaml 的规则 1–3 形状再生成 |
| tests/ring-audit/fixtures/MUTANTS.md · mutation.config.yaml · tests-manifest.yaml · test_check_audit.py（INTERFACE PINNED 头列 6 个 G1 token + 形状；4 个新方法；4 处重命名） | 同上 | mutation 20 条（19 文件 + 1 内存变体 delete-ring:R6）；30 个方法 | mutation 24 条（23 文件 + 1 内存变体）；34 个方法（32 单元 + 2 集成），方法名带所属 AC id；未发明 AC id |
| tests/ring-audit/RED_BASELINE.txt | — | 30/30 红，HEAD c729f76 | revision 2：34 方法 19 ok / 15 FAIL at 57ebf2b（check_audit.py 未入库、按裁决前形状实现）；附分歧节逐条归因，无 fixture bug |
| g1-record.md（g2 锁） | — | 至 3b 重签 | 追加 `## 签字版解释规则（2026-09-05）`；形态字节不动 |

## 为什么

L5 作者把签字版形态 F-12 / F-13 编进 fixture 时遇到三处解释空隙，只能先选一种读法；G1（代签）随后在 `g1-record.md ## 签字版解释规则（2026-09-05）` 出了三条解释规则，其中第 3 条**推翻**了测试的读法：

1. 双生产者（确认 + 对称）：F-13 谓词 = "无未认领的双生产者"；不是双生产者却标 merge_candidate 也算错（`spurious_merge_candidate`）。
2. FILLS 边（确认 + 边界）：顶层 `gaps[]` 注册表 + `parts[].fills[]` / `rings[].missing[]` 放 key；`fills == []` ⇒ 必须 overfill（`overfill_unmarked`）；悬空 key → `unknown_gap_ref`。
3. 人签门 signer（**纠正**）：F-06 说 kind=human 的 Gate 只有 G1/G2/G3；merge / harness-review 是 human_gate 类的 Part 而非 Gate 对象（F-08 → Q004 各一条 Assessment）——fixture 把它们列进 gates[] 且加 `exercised: false` 是错读；真正的空隙是"写 audit.yaml 时 G3 还 pending"，所以三元组随 verdict 放在 `run_evidence.gates[]`。

证据：`g1-record.md` 该节；`tests/ring-audit/fixtures/complete.yaml`（改前）第 gates 段；L5 作者的摩擦报告第 4–6 条（`skill-issues.md` I-56 / I-58）。

## 归因层

- [x] task（判据写错 / 写漏）——测试 fixture 对形态的读法错了；契约 AC 与形态字节都不动
- [ ] ontology（DOS 不变量冲突）
- [ ] world（PSL 规律冲突 → 应重开 G1，而不是只改 AC）

X2：`sdlc_state.py fail --signal lock_hash_mismatch`（R04），计入 task_reflows（PSL 轨预算 2）。

## 重新冻结

- 锁文件 39 → 43 项（g2 集 10 + tests/ring-audit 33）
- 新 `.done_when.lock` sha256: `1cb8516711dd1f16301e6a0c423b4a73bfd8596e3d3b9e83fe7515a3764ea0f7`　签字: g2-judge（delegated_agent，同一授权；stage l5）
- 提案复核: `CONFIRM（task 层）— g2-judge，delegated_agent，2026-09-05 15:43Z；9/9 检查通过；复核时提案 sha256 15252edc1129cc695eee596bb5b268e8c70c4fc5d7da15156fc14e51d9be849b、暂存树 e7343c7c…（31 路径）；两处文档级编辑（其余 16 个 mutant；测试头注释 AC-006-a 措辞）在重签前应用，故本文件 sha 与复核 sha 不同；重签是单一事件`
