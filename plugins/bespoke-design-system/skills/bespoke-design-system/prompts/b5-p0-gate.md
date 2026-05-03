# B5 — P0 闸门（v4：4 个可计算 check + 1 个 LLM judge 并行）

> 当 SKILL.md 主流程进入 B5 时读取本文件作为执行指引。

## 你的任务

执行 5 项独立检查（4 个 Python check + 1 个独立 subagent judge），合并产出 `check-report.json` + verdict（pass / needs_revision / reject）。**限 2 轮迭代**。

---

## Step 1 — 准备 inputs

B4 阶段产出的 4 份内容是 B5 的输入：

1. **DESIGN.md 草稿** — 现已落到 `<output_dir>/DESIGN.md`
2. **provenance.yaml** — `<output_dir>/provenance.yaml`
3. **B4 token snapshot**（可选）— B4 产生的 tokens 视图（如 `<output_dir>/draft-tokens.json`），让 4 个 Python check 能直接吃。如果 B4 没产出这份，从 DESIGN.md 反向解析（少数程序化字段）+ 调性画像合成一份临时 tokens.json
4. **user_profile.yaml** — B1 产出的调性画像（`<output_dir>/inferred-fields.yaml` 或 `<output_dir>/user-profile.yaml`）

## Step 2 — 并行执行 4 个 Python check

逐一调用，**每个独立**（一个 fail 不影响另一个跑）：

### 2.1 coherence_check.py

```bash
python3 checks/coherence_check.py <draft-tokens.json>
```

输出 6 子检查 + score + issues。判据见 `references/color-harmony-math.md` + `references/modular-scale-rhythm.md`。

| 输出字段 | 含义 |
|---|---|
| `passed` | true/false（0 blocker AND score ≥ 0.55） |
| `score` | 0..1，权重平均 |
| `subchecks.{wcag_contrast,oklch_uniformity,hue_harmony,modular_scale,vertical_rhythm,grid_consistency}` | 每个子检查独立结果 |
| `issues` | blocker / warning 列表 |

### 2.2 archetype_check.py

```bash
python3 checks/archetype_check.py <draft-tokens.json> --primary <archetype> [--secondary <archetype>]
```

判据：`checks/_shared/archetype_rules.json` 的 12 archetype 视觉清单（详见 `references/archetype-do-dont-table.md`）。

| 输出 | 含义 |
|---|---|
| `passed` | primary archetype 的 never list 0 blocker |
| `violations[]` | 含 archetype/role/severity/rule/diagnostic |

### 2.3 kansei_coverage_check.py

```bash
python3 checks/kansei_coverage_check.py --profile <user_profile.yaml> --provenance <provenance.yaml>
```

阈值默认 0.8（user kansei.positive 中至少 80% 被某决策 addressed），且 0 reverse_violation。

### 2.4 neighbor_check.py

```bash
python3 checks/neighbor_check.py <draft-tokens.json>
```

距离阈值（详见 `references/tacit-knowledge-boundary.md` §4 关于"下限保证"的诚实声明）：

- 距离 < 0.3 → pass
- 0.3 ≤ d < 0.6 → needs_review（在 corpus 边缘，需检查 rationale）
- d ≥ 0.6 → reject（drifted out of corpus）

如果 neighbor-corpus.json 不存在，工具会返回 `evaluable: false`，整体 check **不算 fail**——只是缺数据。

## Step 3 — 调用 rationale-judge subagent

通过 Agent 工具调起 `subagent_type=rationale-judge`（agent 注册在 `plugins/bespoke-design-system/agents/rationale-judge.md`）。

**重要的 v4 角色限定**：rationale-judge **只判论证质量**（inheritance 真实性 / adaptation 合理性 / justification 协同性 / confidence 校准）。设计本身的好坏由 4 个 Python check 判，不属于 rationale-judge 的职责范围。

调用包内容见 `agents/rationale-judge.md` 的 §输入 部分。

## Step 4 — 合并产出 check-report.json

```json
{
  "verdict": "pass | needs_revision | reject",
  "iteration": 1,
  "checks": {
    "coherence": <coherence_check 输出>,
    "archetype": <archetype_check 输出>,
    "kansei_coverage": <kansei_coverage_check 输出>,
    "neighbor": <neighbor_check 输出>
  },
  "rationale_judge_verdict": <rationale-judge 输出>,
  "summary": {
    "all_blockers": [...],
    "all_warnings": [...],
    "verdict_reason": "..."
  }
}
```

**整体 verdict 决策**：

- 任一 check 输出 `reject`（含 neighbor `verdict=reject` 或 rationale-judge `verdict=reject`） → 整体 `reject`
- 任一 check `needs_revision`（含 neighbor `verdict=needs_review`，rationale-judge `verdict=needs_revision`，或任一 check 有 blocker） → 整体 `needs_revision`
- 全部 `pass` 或仅 warning → 整体 `pass`

写入 `<output_dir>/check-report.json`。

## Step 5 — 分支处理

### verdict == pass

→ 把 `check-report.json` 传给 B6。B6 把 warnings 列表纳入 negotiation-summary 让用户知道"已知限制"。

### verdict == needs_revision（轮次 1）

→ 把所有 blockers + warnings 传回 B4 作为修正指令，**回 B4 重新生成**。修正必须严格只动被指出的决策，不重写整体。第 2 轮 B5 重新跑（rationale-judge 必须独立 spawn 不知道第 1 轮 verdict）。

### verdict == needs_revision（轮次 2）

→ 仍失败说明输入（规则集 + 画像）本身有问题。**不要进第 3 轮**。停下，给用户：

```
P0 闸门 2 轮迭代均未通过。具体卡点：
<列出第 2 轮的所有 blocker issues + 来自哪个 check>

可能原因：
1. 候选规则集与画像的覆盖不足
2. 画像内部矛盾（例如同时要 ancient 和 minimal）
3. archetype rules 的 never 与 kansei 对立
4. neighbor_check 反映 corpus 偏向某种风格

建议：
- 调整画像 kansei / archetype（你告诉我哪些可放弃）
- 或运行维护流程导入更多素材扩 corpus
- 或接受当前版本（不通过闸门，但 negotiation-summary 会标注所有 issues）
```

### verdict == reject

→ 严重违反（如 reality_calibration drifted 距离 ≥ 0.6 / coherence 多 blocker / archetype primary never 触发多条）。处理同 needs_revision 第 2 轮 — 直接停下，不再迭代。

## Step 6 — 检查清单（B5 产出前必过）

- [ ] 4 个 Python check 都跑了（即使有的 evaluable=false 也要记录）
- [ ] rationale-judge 通过 Agent 工具独立 spawn（不和主对话共享上下文）
- [ ] check-report.json 含 5 项独立结果 + 整体 verdict + 决策原因
- [ ] 迭代次数 ≤ 2
- [ ] needs_revision 时的反馈给 B4 是具体的（每条 blocker 指向具体决策 + 修正方向）
- [ ] 失败时已给用户清晰说明而非追问

## v4 重要约束

- **rationale-judge 角色限定**：v3 时它要"判设计 + 论证"，v4 起**只判论证**。设计本身的好坏由 4 个 Python check 判。
- **neighbor_check 的诚实**：它不能判"有品味"，只判"在 corpus 范围内"。这是下限保证不是上限，B6 必须传达给用户。
- **5 项 check 全过 ≠ 有品味**：本 skill 的产物始终是初稿，品味终审由人审。
