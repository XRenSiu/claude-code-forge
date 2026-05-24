# Step 6 Fixer Patches — iter-1-step6-attempt-1

> Fixer subagent 处理 Auditor 报告 `iter-1-step6-attempt-1-issues.md` 的 P0。
> 范围：plugin 级移交契约文档（INTEGRATION.md / README.md）。
> 不动：设计文档、plugin.json、iter-*.md 审查产物、P1/P2 issues。

---

## 一、处理的 P0 issues

| ID | 描述 | 处理状态 |
|---|---|---|
| P0-1 | `INTEGRATION.md` 的 `spec_drift_threshold` 示例含 `applies_to:`，与 `acceptance-spec/SKILL.md` line 177 严格 schema 冲突 | 已修 |
| P0-2 | `README.md` line 63 表格 "receives the spec-drift escalation signal from PBT" 与 `INTEGRATION.md` line 61 "It does not automatically escalate" 矛盾 | 已修 |

附带修复（与 P0-2 同类、属同一根因）：
- `README.md` line 38-39 pipeline 图："spec-drift bailout: PBT failing >=3 rounds escalates back to clarify" 与 INTEGRATION 同样的"无自动 escalate"立场矛盾。Auditor 把这条记为 P2-1 的旁支（line 38 "consumes" 措辞），但 line 39 "escalates back to clarify" 本身和 line 63 是同类越权宣称——既然要修 P0-2 同义句，line 39 一并校齐避免文档内**两处**还在自相矛盾。

---

## 二、修改的文件清单

| 文件 | 修改点数 |
|---|---|
| `plugins/done-when-pipeline/INTEGRATION.md` | 1（line 67-77 spec_drift_threshold 示例 + 旁注） |
| `plugins/done-when-pipeline/README.md` | 2（line 38-39 pipeline 图 + line 63 ratchet 表格行） |

---

## 三、逐处修改

### 3.1 `plugins/done-when-pipeline/INTEGRATION.md` — P0-1

**修改前**（原 line 67-77）：

```markdown
Our `done_when.yaml` carries a `spec_drift_threshold:` block:

​```yaml
spec_drift_threshold:
  max_fix_loops_before_escalation: 3
  applies_to:
    - mutation_kill_rate
    - property_based_failure
​```

**This is guidance for the human composing the `/ratchet` invocation**, not a contract field anything reads automatically. Concretely, when chaining to ratchet, translate it as:
```

**修改后**：

```markdown
Our `done_when.yaml` carries a `spec_drift_threshold:` block. Per the v1 schema, it has **exactly one** sub-field (see `skills/acceptance-spec/SKILL.md` § "Hard rules for v1 字面" and `references/done-when-schema.yaml`):

​```yaml
spec_drift_threshold:
  max_fix_loops_before_escalation: 3
​```

Do not add `applies_to:` or any other key — strict v1 parsers will reject it. The threshold applies uniformly to *any* test failure category that keeps repeating across fix loops (PBT, mutation, e2e); v1 does not let you scope it per-category.

**This block is guidance for the human composing the `/ratchet` invocation**, not a contract field anything reads automatically. Concretely, when chaining to ratchet, translate it as:
```

**理由**：

- 删掉 `applies_to:` 示例字段，与 `acceptance-spec/SKILL.md` line 177（严格 schema "exactly one sub-field"）、`done-when-schema.yaml` line 131（"Do NOT add `applies_to:`"）、`done-when-schema-validator.md` line 67（"treat as malformed"）三处口径一致。
- 加一句正向 cross-reference 指向 SKILL.md 和 schema 文件，让 INTEGRATION.md 读者知道 schema 的权威出处。
- 加一句解释"为什么 v1 不分类"，避免读者看完后还想"那我哪里可以细分 PBT vs mutation 的阈值？"——明确告诉他 v1 不能，统一阈值。

### 3.2 `plugins/done-when-pipeline/README.md` line 38-39 — 附带（P0-2 同类）

**修改前**：

```text
ratchet  ─── consumes done_when.yaml as the kill/restart/done oracle (Step 5-6)
   spec-drift bailout: PBT failing >=3 rounds escalates back to clarify
```

**修改后**：

```text
ratchet  ─── user hands done_when.yaml to /ratchet as the acceptance contract (Step 5-6)
   spec-drift bailout: after `max_fix_loops_before_escalation` (default 3) rounds
   with no improvement, ratchet's `convergence` stops the loop; the user then
   decides manually whether to re-run /ratchet or go back to /acceptance-spec.
   No auto-escalation in v0.1.
```

**理由**：

- 原文 "consumes done_when.yaml as the kill/restart/done oracle"（"consume" 暧昧）+ "escalates back to clarify"（暗示自动）合并起来比实际能力强。INTEGRATION.md line 21 已澄清 ratchet **不**直接 parse YAML；INTEGRATION.md line 61 已澄清 ratchet **不**自动 escalate。
- 改成 "user hands ... to /ratchet"，明确手工移交。
- 改成 "user then decides manually whether to re-run /ratchet or go back to /acceptance-spec"，与 INTEGRATION.md line 80-82 字面一致。
- 显式 "No auto-escalation in v0.1"，与 INTEGRATION.md line 81-83 立场对齐。

### 3.3 `plugins/done-when-pipeline/README.md` line 63 — P0-2 主项

**修改前**：

```markdown
| `ratchet` | Step 5-6 main controller. Consumes `done_when.yaml` as its acceptance contract; runs the master/subagent kill-and-restart loop; receives the spec-drift escalation signal from PBT. |
```

**修改后**：

```markdown
| `ratchet` | Step 5-6 main controller. The user **manually** translates our `done_when.yaml` into a `/ratchet` invocation (Goal / Criteria / Scope / done_when block) — ratchet does not parse our YAML directly. Ratchet then runs its master/subagent kill-and-restart loop. There is **no auto-escalation** of "PBT failures look like spec bugs" in v0.1; after ratchet's `convergence` stops the loop, the user decides whether to re-invoke `/ratchet` or go back to `/acceptance-spec`. See `INTEGRATION.md` for the handoff recipe. |
```

**理由**：

- 删掉 "receives the spec-drift escalation signal from PBT"——此措辞暗示 ratchet 自己能 detect spec drift。INTEGRATION.md line 61 / 81 / 83 三处明确撤回此能力，README 必须对齐。
- "Consumes done_when.yaml as its acceptance contract" → 改成 "user manually translates ... into a /ratchet invocation"，与 INTEGRATION.md line 21 + line 26-51 一致。
- 显式 "no auto-escalation" + "user decides"，与 INTEGRATION.md line 80-82 一致。
- 末尾指回 INTEGRATION.md 作为权威 handoff 文档。

---

## 四、不修的 issues

### P1（6 条）— 全部不修

| ID | 不修理由 |
|---|---|
| P1-1 两个 SKILL.md 自身不讲 spec drift 兜底 | Fixer 任务只 scope P0；P1 修法（在 SKILL.md 嵌入 spec drift 段）属于内容增量，不在本次范围。 |
| P1-2 §8.3 (a) 达标出口未声明 | 同上；属 ratchet 内部职责，hand-off 文档不强制覆盖。 |
| P1-3 §8.3 (b) 未达标出口细分缺失 | 同上。 |
| P1-4 `budget: max 15 rounds` 出处不明 | 同上。 |
| P1-5 `max_fix_loops_before_escalation` 与 ratchet `convergence` 语义不完全等价 | INTEGRATION.md line 80-84 已 acknowledge 此 gap，不再额外补。 |
| P1-6 "spec wrong vs code wrong" 判别准则缺失 | 同上。 |

### P2（3 条）— 全部不修

| ID | 不修理由 |
|---|---|
| P2-1 README line 38 "consumes" vs INTEGRATION "does not parse" | 已被本次 README line 38 改写顺带消解（新措辞 "user hands ... to /ratchet" 不再暗示自动 parse）。 |
| P2-2 `spec_drift_threshold` 字段名未在 README / plugin.json 出现 | 风格问题，不影响契约。 |
| P2-3 两个 SKILL.md 不引 §12.1 (IV) | 是 P1-1 的子项。 |

---

## 五、验证

修改后 grep 结果：

```bash
$ grep -rn "applies_to" plugins/done-when-pipeline/
SKILL.md:177            — "Do NOT add `applies_to:`"      # 禁止
done-when-schema.yaml:131 — "Do NOT add `applies_to:`"    # 禁止
done-when-schema-validator.md:67 — "treat as malformed"   # 禁止
INTEGRATION.md:74        — "Do not add `applies_to:`"     # 禁止（新）

$ grep -rn "automatically escalate\|escalation signal\|escalates back\|auto-escalation\|auto escalate"
README.md:42            — "No auto-escalation in v0.1"                          # 否定
README.md:66            — "no auto-escalation"                                  # 否定
INTEGRATION.md:61       — "It does not automatically escalate"                  # 否定
INTEGRATION.md:81       — "If you want auto-escalation, that needs to be built"  # 未来工作
INTEGRATION.md:83       — "auto-escalation as a desirable property ... future work"  # 未来工作
```

四处 `applies_to:` 残留 100% 是 "Do NOT" / "malformed" 形式，无冲突。
五处 "escalation" 残留 100% 是 "no / not / future work" 立场，无冲突。

---

## 六、风险评估

| 风险点 | 评估 |
|---|---|
| 改 INTEGRATION.md 示例 yaml 是否破坏下游消费者？ | 无下游程序化消费者。该示例只供人阅读。 |
| 改 README.md ratchet 表格行是否削弱 plugin 卖点？ | 与 plugin.json version `0.1.0` + README line 90 "covers Steps 1-4" 立场一致——v0.1 不卖自动闭环，是 honest disclaimer 而非降级。 |
| 改 README.md pipeline 图是否影响首次读者理解？ | 改后行数增加（2 行 → 5 行），但语义更准确；首次读者读完即知道"手工 hand-off + 无自动升级"，避免后续踩坑。 |
| 修改的文件是否在 SKILL.md 引用链上？ | INTEGRATION.md 被 `acceptance-spec/SKILL.md` line 184 显式引用为 spec_drift_threshold 翻译指南；README 是 plugin 门面。两处都属移交契约对外面，修后**对外契约一致性提升**，不引入新风险。 |
| 版本号是否需要 bump？ | 这是同一 plugin 内自相矛盾文档的对齐，不是新增 skill / 不破坏 API / 不修改 schema。属于 doc patch；按 CLAUDE.md 版本表 = patch 级。**但 Fixer 不主动改 plugin.json / marketplace.json / SKILL.md version**——交给主流程在 step6 attempt-2 通过后批量 bump。 |

---

## 七、铁律遵守自查

- [x] 不动设计文档 `done-when-pipeline.md`
- [x] 不动 `plugins/done-when-pipeline/.claude-plugin/plugin.json`
- [x] 不动 `specs/forge-skill-validation/iter-*.md` 任何审查产物
- [x] 不修 P1（6 条）/ P2（3 条）
- [x] 只修 INTEGRATION.md + README.md（白名单内文件）
- [x] 修后 grep 无冲突残留
