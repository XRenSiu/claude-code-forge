# B5 — P0 闸门

> 当 SKILL.md 主流程进入 B5 时读取本文件作为执行指引。

## 你的任务

通过 Claude Code 的 **Agent 工具**调用 `rationale-judge`（plugin 级 agent）作为**独立 subagent**评判 B4 草稿。**限 2 轮迭代**。

---

## Step 1 — 准备 judge 调用包

在工作目录或临时位置写下 judge 输入（YAML），打包：

```yaml
judge_input:
  user_profile: <B1 调性画像 — 完整 YAML>
  design_md_draft: <B4 DESIGN.md 草稿全文>
  provenance_report: <B4 三段式 Provenance YAML>
  rules_subset_summary:
    rule_ids: [...]              # B3 自洽子集的 rule_id 列表
    source_systems: [...]        # 这些规则来自的 system 列表
  rules_yaml_paths:                # judge 自己读规则原文核验
    - <path to>/grammar/rules/<system>.yaml
    - ...
  references_paths:
    - <path to>/references/anti-slop-blacklist.md
    - <path to>/references/kansei-theory.md
    - <path to>/references/brand-archetypes.md
    - <path to>/references/design-md-spec.md
```

**关键**：传给 judge 的是**产物 + 路径**，不是 B4 的内部推理过程。让 judge 自己读规则原文做真实性核验，避免被 B4 的辩护性 rationale 感染。

---

## Step 2 — 调用 rationale-judge

通过 Agent 工具发起调用。**约定**：

```
Agent({
  description: "P0 gate review for bespoke DESIGN.md draft",
  subagent_type: "rationale-judge",
  prompt: <judge_input as inline YAML>
         + "\n\nFollow the rationale-judge agent definition strictly. "
         + "Read the rules YAMLs and references at the provided paths. "
         + "Output ONLY the standard JSON verdict (see your agent definition). "
         + "Do not output Markdown wrappers around the JSON."
})
```

**为什么 subagent_type="rationale-judge" 能工作**：本 plugin 在 `plugins/bespoke-design-system/agents/rationale-judge.md` 注册了同名 agent。Claude Code 自动把 plugin 的 agents/ 目录加入 subagent 池，调用时上下文与主对话**完全隔离**。

**如果 subagent_type="rationale-judge" 不可用**（例如 plugin 未启用、Agent 工具无法识别），fallback：
- 用 `subagent_type: "general-purpose"`
- 把 `agents/rationale-judge.md` 的全部内容（除 frontmatter）作为 prompt 前缀
- 接 judge_input

但**必须在产物 provenance.yaml 标记** `gate_subagent_mode: native` 或 `gate_subagent_mode: fallback_general_purpose`，便于审计。

---

## Step 3 — 解析 verdict

rationale-judge 输出标准 JSON（schema 见 `agents/rationale-judge.md` 中的"输出格式"段）：

```json
{
  "verdict": "pass | needs_revision | reject",
  "per_decision_review": [...],
  "global_issues": [...],
  "kansei_completeness": {...},
  "reality_calibration": {...},
  "anti_slop_check": {...}
}
```

如果 judge 输出含 markdown 包裹（如 ```json ... ```），剥掉外层。如果输出不是合法 JSON，记录这是 judge 的问题（write a warning to provenance），按 `needs_revision` 处理（保守）。

---

## Step 4 — 分支

### verdict == pass

→ B4 草稿与 Provenance Report 直接进入 B6。把 judge 输出的非 blocker `warnings` 传到 B6，让 negotiation-summary 能列出"已知限制"。

### verdict == needs_revision（轮次 1）

→ 把 issues + suggestions 作为修正指令，**回到 B4** 重新生成。修正时严格只动被指出的决策，不重写整体。

进入第 2 轮 B5 评判，**禁止把第 1 轮 verdict 详情透露给 rationale-judge**（防止串供）。第 2 轮 judge 还是独立看草稿。

### verdict == needs_revision（轮次 2）

→ 仍失败说明输入（规则集 + 画像）本身有问题。**不要进第 3 轮**。停下，给用户：

```
P0 闸门 2 轮迭代均未通过。这通常意味着：
1. 候选规则集与画像的覆盖不足（某些 kansei 词没有合适规则）
2. 画像本身有内部矛盾（比如同时要 ancient 和 minimal）
3. anti-slop 黑名单与画像默认值发生硬冲突

具体卡点：
<列出第 2 轮 judge 的 blocker issues>

建议：
- 检查需求并调整画像（你可以告诉我哪些 kansei 词可以放弃 / 哪些是不可妥协的）
- 或运行维护流程导入更多素材扩大规则库
```

**铁律**：即使在这种情况下也**不向用户追问表单式问题**。只是说明现状、给出选项让用户主动回应。

### verdict == reject

→ 同 needs_revision 第 2 轮的处理方式。直接停下，不再迭代。

## Step 5 — 输出给 B6

如果 pass：

```yaml
gate_result:
  verdict: pass
  rounds: 1 | 2
  subagent_mode: native | fallback_general_purpose
  judge_summary:
    kansei_completeness: ...
    reality_calibration: ...
    anti_slop_clean: true | suspicions: [...]
  warnings: [...]   # 非 blocker 但值得在 negotiation-summary 中提的
```

把这个结果连同 DESIGN.md 草稿、Provenance Report 一起传给 B6。

---

## 重要细节

- **subagent 必须独立**：通过 Agent 工具新起 subagent，不能用主对话上下文复用。否则 judge 会被生成方"感染"。
- **不要让 judge 修复草稿**：它的角色只是评判。修复永远回 B4。
- **2 轮硬上限**：第 3 轮永远不允许，无论用户怎么催。
- **不向用户追问**：从 B2 起就有的铁律，B5 也不破例。
- **subagent_mode 必须记录**：审计时用来判断这次 gate 是否真在隔离上下文中跑

---

## 检查清单（B5 产出前必过）

- [ ] 已通过 Agent 工具调用 rationale-judge subagent（subagent_type 优先 "rationale-judge"，fallback "general-purpose"）
- [ ] 调用包含产物 + 规则原文路径，不含 B4 内部推理
- [ ] verdict 已解析为标准 JSON 结构（必要时剥掉 markdown 包裹）
- [ ] needs_revision 时已回 B4 修正，不在 B5 内部"修补"
- [ ] 迭代次数 ≤ 2
- [ ] 失败时已给用户清晰的卡点说明而非追问
- [ ] gate_subagent_mode 已记录到 provenance（audit trail）
