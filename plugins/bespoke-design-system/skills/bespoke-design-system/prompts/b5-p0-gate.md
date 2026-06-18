# B5 — P0 闸门（v1.12.0：4 个可计算 check + 2 个 LLM judge）

> 当 SKILL.md 主流程进入 B5 时读取本文件作为执行指引。
> 前置：B4.5 已用 taste-critic（rank 模式）选出 winner direction，B4b 已把它展开成完整 DESIGN.md。B5 对这份成稿把关。

## 你的任务

执行 6 项独立检查（4 个 Python check + 2 个独立 subagent judge：rationale-judge 判论证、taste-critic 判独特性），合并产出 `check-report.json` + verdict（pass / needs_revision / reject）。**限 2 轮迭代**。

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
# v1.13.1: 用 B4.5 WINNER 的 kansei 判覆盖，而非三概念并集（改动4 fix / skill-issue #4）
python3 checks/kansei_coverage_check.py --profile <user_profile.yaml|.json> --provenance <provenance.yaml|.json> \
  --kansei <winner concept kansei_lean + 共享 base，逗号分隔>
```

阈值默认 0.8（**winner kansei** 中至少 80% 被某决策 addressed），且 0 reverse_violation。

- **v1.13.1 改动4**：B0.5 三个发散概念取并集做检索宽度，但单一 winner 天然覆盖不了被否概念的 kansei。所以 B5 必须传 `--kansei`＝winner 概念的 kansei_lean +（三概念共有的 base 词），否则 winner 会因没覆盖被否概念而误扣分。不传 `--kansei` 则回退用 profile.positive（并集，会偏严）。
- **v1.13.1 #5**：输入接受 YAML 或 JSON；无 PyYAML 时若传 JSON 仍能跑，否则优雅降级为 `evaluable:false`（不再 `exit(2)` 崩整条闸门）。干净环境建议 `pip install pyyaml` 或传 JSON。

### 2.4 neighbor_check.py

```bash
python3 checks/neighbor_check.py <draft-tokens.json>
```

**v1.11.0 起这是「独特性带」而非「靠近度奖励」**（语义反转，详见 `references/tacit-knowledge-boundary.md` §4 与 `bespoke-design/skill-issue-2026-06-18.md`）。距离不再是越小越好——它是要**赚来的、有界的**：

- 距离 < 0.05 → **reject**（`derivative_clone`：token 空间里和某个现有系统几乎一模一样。B3 多半收敛到单一密集风格岛、B4 照搬了它）
- 0.05 ≤ d < 0.12 → **needs_review**（`derivative_suspect`：低于 corpus 最近邻中位数，可能只是"某系统换个强调色"，需 taste 复核）
- 0.12 ≤ d ≤ 0.45 → **pass**（`distinctive`：有区分度又有根基。**注意：只证明不是 token clone，不证明有品味**）
- d > 0.45 → **needs_review**（`far_outlier`：比任何真实系统离邻居都远，可能大胆也可能不自洽。本 check 分不清，交给 coherence/archetype/rationale，**不**单凭距离 reject）

阈值是从 corpus 自身距离分布**校准**出来的（corpus 内部最近邻：中位 0.12 / p90 0.20 / 最大 0.26），不是拍脑袋。

**诚实边界（必读）**：这是 44 维 token 统计距离（v1.13.0），只能抓 token 空间的 clone，**看不见概念级平庸**（统领想法 / 签名动作）。一份把 Linear 结构整套抄走、只换强调色的设计会落在 ~0.18 判 pass。"很普通"这种感知层面的平庸由 taste critic 抓，不是这个 check 的职责。

如果 neighbor-corpus.json 不存在，工具会返回 `evaluable: false`，整体 check **不算 fail**——只是缺数据。

## Step 3 — 调用 rationale-judge subagent

通过 Agent 工具调起 `subagent_type=rationale-judge`（agent 注册在 `plugins/bespoke-design-system/agents/rationale-judge.md`）。

**重要的 v4 角色限定**：rationale-judge **只判论证质量**（inheritance 真实性 / adaptation 合理性 / justification 协同性 / confidence 校准）。设计本身的好坏由 Python check + taste-critic 判，不属于 rationale-judge 的职责范围。

调用包内容见 `agents/rationale-judge.md` 的 §输入 部分。

## Step 3.5 — 调用 taste-critic subagent（gate 模式，v1.12.0 新增 / 改动4）

通过 Agent 工具独立调起 `subagent_type=bespoke-design-system:taste-critic`（agent 注册在 `plugins/bespoke-design-system/agents/taste-critic.md`）：

```
Agent(subagent_type="bespoke-design-system:taste-critic",
      prompt=<critic_input: mode=gate, design_md=<成稿全文>, provenance, user_profile, brief,
              neighbor_result=<2.4 的 neighbor_check 输出>,
              references_paths=[anti-slop-blacklist.md, source-design-systems/]>)
```

**角色限定**：taste-critic **只判独特性**——这份成稿有没有自己的 POV，还是又一份能干却没人记得住的通用壁纸。这是 4 个 Python check + rationale-judge **都看不见**的维度（数学协调 / 贴合画像 / token 距离 / 论证质量都可以满分，设计依然"很普通"）。

**重点核验**：B4.5 选中的签名动作，**在展开成完整 9-section 后是否还活着**（常见失败：concept 好，但逐 section 落地全退回安全默认，签名被稀释）。

verdict 映射：`distinctive → pass` / `derivative → needs_revision` / `generic → reject`。**必须独立 spawn，不和主对话或 B4 生成方共享上下文**（同 rationale-judge 纪律）。

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
  "taste_critic_verdict": <taste-critic gate 模式输出>,
  "b4_5_selection": <taste-critic rank 模式输出：winner + 各候选 score + all_generic>,
  "summary": {
    "all_blockers": [...],
    "all_warnings": [...],
    "verdict_reason": "..."
  }
}
```

**整体 verdict 决策**：

- 任一 check 输出 `reject`（含 neighbor `verdict=reject`、rationale-judge `verdict=reject`、或 taste-critic `verdict=generic`） → 整体 `reject`
- 任一 check `needs_revision`（含 neighbor `verdict=needs_review`，rationale-judge `verdict=needs_revision`，taste-critic `verdict=derivative`，或任一 check 有 blocker） → 整体 `needs_revision`
- 全部 `pass`（taste-critic = `distinctive`）或仅 warning → 整体 `pass`

> taste-critic 抓的是**平庸下限**：`generic`（换皮 clone / 通篇默认值）= reject，`derivative`（有点东西但不够尖）= needs_revision 回 B4 磨锐 concept/signature。这是治"很普通"的闸门，**不要因为前 5 项全绿就放它过**。

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
- [ ] taste-critic（gate 模式）通过 Agent 工具独立 spawn（v1.12.0；不和主对话/B4 生成方共享上下文）
- [ ] check-report.json 含 6 项独立结果 + B4.5 选优记录 + 整体 verdict + 决策原因
- [ ] 迭代次数 ≤ 2
- [ ] needs_revision 时的反馈给 B4 是具体的（每条 blocker 指向具体决策 + 修正方向）
- [ ] 失败时已给用户清晰说明而非追问

## v4 / v1.12.0 重要约束

- **rationale-judge 角色限定**：v3 时它要"判设计 + 论证"，v4 起**只判论证**。设计本身的好坏由 Python check + taste-critic 判。
- **neighbor_check 的诚实**：它不能判"有品味"，只判"不是 token clone"（v1.11.0 独特性带）。这是下限保证不是上限。
- **taste-critic 的定位（v1.12.0）**：它把"很普通"从不可判变成可判的**平庸下限**——能判"这没有 POV / 是换皮"，但**不能**判"这有大师级品味"（那仍是 tacit、需人终审）。pass = "有一个能说清的身份"，不是"伟大"。
- **6 项 check 全过 ≠ 有品味**：本 skill 的产物始终是初稿，品味终审由人审（铁律 3）。
