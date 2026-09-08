# based_on: REQ-005, REQ-006

# G3 checklist — human ACs of sdlc-ring-audit (no automated test; never auto-passed — done_when.yaml rules)

Judge reads `plugins/sdlc/dogfood/ring-audit/AUDIT.md` (projection of `audit.yaml`; yaml wins on disagreement).
Each box is one clause of the AC statement, verbatim from the frozen contract. Every box must be ticked for the AC to pass;
a signer_kind of `delegated_agent` must be recorded with its authorization_ref in the G3 record.

## AC-005-a — `ui:AUDIT.md#ring-tables` (judge: tech, evidence: checklist)

- [ ] 每个 Part 行给出 Gap 原子集合
- [ ] 每个 Part 行给出独占 Artifact（或 `role gate | orchestrator`）
- [ ] 每个 Part 行给出检它的 Gate，script 写"闸"、human 写"门"（无一处 script Gate 写成"门"）
- [ ] 每个 Part 行给出 Loop（`loops.yaml#<id>` 或 null）
- [ ] needed 判定的 deletion 测试写出撤掉它后流水线会产出的具体错误产物或漏检
- [ ] deletion 测试不接受"流程会断"一类泛语（逐行抽查：没有一条 deletion 只说"会断 / 走不下去"）
- [ ] naming 判定先写来路（authored | adopted）再写贴合（fits | misfit）
- [ ] misfit 时给出建议名，且建议名比原名更贴产物或位置
- [ ] misfit 时标"不重命名"
- [ ] 疑似重复的 Part 对至少含 pr-review vs code-reviewer，带 Artifact 对照与 `distinct_exits | merge_candidate | alternatives_of` 裁决
- [ ] 疑似重复的 Part 对至少含 donewhen-extract vs acceptance-spec，带 Artifact 对照与 `distinct_exits | merge_candidate | alternatives_of` 裁决
- [ ] 每环表末尾的 missing 行带来源标签（lifecycle_blank | newly_identified | unenforced_rule）
- [ ] 每条 missing 行带 necessity
- [ ] 每条 missing 行带 deletion 一句

## AC-006-a — `ui:AUDIT.md#run-evidence` (judge: product, evidence: checklist)

- [ ] run_evidence 节列出 G1 的签字人、signer_kind 与授权引用
- [ ] run_evidence 节列出 G2 的签字人、signer_kind 与授权引用
- [ ] run_evidence 节列出 G3 的签字人、signer_kind 与授权引用
- [ ] signer_kind = delegated_agent 的门不渲染为"人签"
- [ ] 列出 check-audit 对 audit.yaml 的 exit 0 运行记录
- [ ] 列出 check-audit 对删环变体（`--variant delete-ring:<id>`）的 exit 1 运行记录
- [ ] 若缺变体记录，exit 0 标 `uncalibrated`，且 A6 的回答如实带出该标记（无变体记录却未标 → 不通过）
- [ ] 列出 Card-footer 提交对三个被审目录（plugins/sdlc/skills、agents、docs）的 `git diff --stat` 记录，且为空
- [ ] 列出 skill-issues.md 的路径
- [ ] 外部证据的替代品标 `substitute`
- [ ] `substitute` 证据不渲染为用户验证

## Signature slot

| AC | verdict (pass / fail) | signer | signer_kind | authorization_ref |
|---|---|---|---|---|
| AC-005-a | | | | |
| AC-006-a | | | | |
