# Pilot Run — Contract Issues Found

> 用 linear-app + vercel 两套真实素材跑通 A1-A4 + B0-B6 端到端后暴露的 skill 自身契约问题。

---

## #1 [BLOCKER] DESIGN.md 9-section 标准定义错误

**问题**：`references/design-md-spec.md` 写的"标准 9-section"是 `Color / Typography / Spacing / Layout / Components / Motion / Voice / Brand / Anti-patterns`。

但 OD（`nexu-io/open-design`，spec 提到的核心起步源）的 137 套 DESIGN.md（spec 说 71 套是过时数字）实际格式是：

1. Visual Theme & Atmosphere
2. Color Palette & Roles
3. Typography Rules
4. Component Stylings
5. Layout Principles
6. Depth & Elevation
7. Do's and Don'ts
8. Responsive Behavior
9. Agent Prompt Guide

两者**完全不同**——既不能简单一一映射（OD 没有专门 Motion / Voice / Brand section；我们的标准没有 Visual Theme / Depth & Elevation / Responsive / Agent Guide），也违反 spec §1.4 "输出可被任何 DESIGN.md 兼容工具消费"。

awesome-design-md（spec 提到的另一起步源）我没有验证，但据此推断它也接近 OD 方言。

**影响范围**：
- `references/design-md-spec.md`（描述错的标准）
- `prompts/b4-generation-with-rationale.md`（按错的 9-section 生成）
- `prompts/b6-output-formatting.md`（按错的 9-section 输出）
- SKILL.md §六 schema 速查（仅一处提到，但全文多处假设这套 9-section）

**修复方向**：
- 选项 A（推荐）：把 design-md-spec.md 改为 OD 实际方言。所有 prompt 改为按 OD 9-section 输出。
- 选项 B：自定义一套"理想 9-section"，但产物需要双输出（同时输出方言适配版）。比 A 复杂得多，违反 single-skill self-contained 原则。

**当前 pilot 走的是选项 A 的精神**——`output-design.md` 用了 OD 9-section 格式，因此能与 OD/Stitch 等工具兼容。但 prompt 文件还没改，下次按 prompt 跑会再出错。

---

## #2 [BLOCKER] B5 P0 闸门 subagent 调用机制存在歧义

**问题**：spec § 3.6 + SKILL.md §三 B5 + `prompts/b5-p0-gate.md` 都强调"必须调用独立 subagent"，但实际操作时：

1. Claude Code 的 Agent 工具确实能 spawn 新 subagent，**但**有两种调用路径：
   - 直接传 subagent_type=general-purpose + 把 rationale-judge.md 全文作为 prompt
   - 用某个具体的 reviewer agent（如 `pdforge:code-reviewer`）但语义不对

2. 没有"专为 bespoke-design-system 创建的 rationale-judge agent 注册到 plugin.json 的 agents/"机制——本 skill 只在 skills/.../subagents/rationale-judge.md 放了一份指令文档，但 Claude Code 的 Agent 工具**找不到**它（agents 必须在 plugin/.claude-plugin/plugin.json 或 plugin/agents/ 才会被自动发现）。

3. 在 pilot 中我**直接跳过了 B5**（provenance.yaml 标了 `gate_skipped_for_pilot: true`）。这意味着：
   - Inheritance 真实性 / Adaptation 合理性 / Justification 协同性 / Confidence 校准 这 4 个维度的对抗性评判**没有发生**
   - 所有决策由生成方自审，违反 spec § 2.2 + § 3.10 的"分离生成方和评判方"铁律

**修复方向**：
- 把 rationale-judge 真正放到 `plugins/bespoke-design-system/agents/rationale-judge.md`（plugin 级别的 agent 目录），让 Claude Code 自动发现
- 或在 prompts/b5-p0-gate.md 里改成显式调用 Agent 工具时使用 `subagent_type=general-purpose` + 把 subagents/rationale-judge.md 全文 inline 作为 prompt
- 当前 SKILL.md 提到调用 subagent 但没具体到"用 Agent 工具 / 哪种 subagent_type / 如何隔离上下文"——指令太模糊导致实操时没人知道怎么做

---

## #3 [HIGH] Section 命名没有枚举约束

**问题**：rule schema 的 `section` 字段我自己写就出现了不一致：
- `linear-app.yaml` 用 `section: elevation`
- `vercel.yaml` 把 elevation 规则归到 `section: components`

`prompts/b3-conflict-resolution.md` 假设 9 section 是确定的固定集合并要求每个 section 都覆盖，但 schema 没枚举哪些是有效 section name，导致 grouping 不一致 → B3 的"section 覆盖检查"误报。

**修复方向**：
- 在 `references/design-md-spec.md`（修复后的版本）中显式列出有效 section name 枚举
- A3 步骤的 prompt 加一句"section 必须从下列枚举中选"

---

## #4 [HIGH] B3 候选/自洽集规模假设了大规模规则库

**问题**：`prompts/b2-rule-retrieval.md` 写"候选集 100-200 条"，`prompts/b3-conflict-resolution.md` 写"自洽子集 40-80"。

实测：2 套素材 × 10 条规则 = 20 条总规则。候选集只有 20 条，自洽子集 14 条。完全不到 spec 假设的量级。

如果 prompt 里的"硬性"检查清单（"自洽子集规模在 [40, 80] 区间"）严格执行，**整个 pipeline 会在 B3 失败**——而失败的原因不是 pipeline 错，是规模假设不成立。

**修复方向**：
- 把规模上下限改为相对值：候选集 ≥ min(N_total_rules, 100) 且 ≥ section_count × 5；自洽子集 ≥ 9（每 section 至少 1 条）
- 或加一档"小规则库（< 50 条）模式"，免除规模检查
- 或在 SKILL.md §三 B0 加"规则库 < N 条时，警告用户产物质量受限"

---

## #5 [MEDIUM] auto 模式默认推断字段太宽，把"reverse_constraint 普适项"和"category-specific"混在一起

**问题**：`prompts/b1b-auto-inference.md` 让 reverse_constraint 默认包含 ai_slop + generic_corporate（这部分对）+ category 默认的 avoid_kansei（这部分混乱）。

实测时，brief 含"不要又一个企业 SaaS"被简单加到 reverse_constraint，但其实它应该是**unique_constraint**（产品级约束）而不是 kansei reverse 约束。这导致 B2 在过滤规则时可能误判。

**修复方向**：
- 区分"kansei 反向"（词汇级，与规则 preconditions.kansei 比对）和"产品级否定约束"（unique_constraints，进入 anti-pattern section）
- B1b 推断时显式分流

---

## #6 [MEDIUM] adaptation_id 命名规则没有跑通验证

**问题**：`prompts/b6-output-formatting.md` 定义了 `adaptation_id = <source_rule_id>:<dimension>_<direction>_for_<top_kansei_match>`，但实测时不清楚：

- "direction" 是 `decrease`/`increase` 还是 `from_X_to_Y`？
- "top_kansei_match" 怎么选？我有 5 条 positive kansei，选哪个？
- 同一规则改两个 dimension 算 1 条还是 2 条 adaptation？

pilot 跳过了 adaptation-stats 更新（也没有第二次生成可以累计），但如果跑第二次相同 brief，命名不稳定 → occurrence 计数会错乱 → 自演化机制基础不可靠。

**修复方向**：
- 在 b6 prompt 里给 adaptation_id 一个确定性算法（伪代码）
- 加一个 sanity test：对同一 (rule_id, dimension, direction, top_kansei) 元组，命名必须 deterministic

---

## #7 [MEDIUM] 规则的 `section` 字段命名空间混乱（OD vs spec）

**问题**：与 #3 相关但更深。`grammar/rules/*.yaml` 的 section 字段我用了 `color/typography/components/elevation/layout/voice/anti_patterns`——这是**我自创的混合方言**，既不完全对应 OD 9-section，也不完全对应 spec 写的 9-section。

具体冲突：
- OD 有 "Visual Theme & Atmosphere"，但我没把任何规则归到那里——因为该 section 是综合性描述，难以拆为独立规则
- OD 有 "Responsive Behavior"，我也没规则覆盖（规则库太小）
- OD 有 "Agent Prompt Guide"，这本身就是产物的"使用说明"section，不应该有规则覆盖它（规则在生成时自动产生 section 内容）

**修复方向**：
- Rule schema 的 `section` 字段应该用 OD section 的 short slug：`visual_theme | color | typography | components | layout | depth_elevation | dos_donts | responsive | agent_guide`
- 但其中 `visual_theme` / `dos_donts` / `agent_guide` 是 derivative section（由其它 section 生成），不需要独立规则
- 真正承担规则的是 5 个：color / typography / components / layout / depth_elevation
- 这意味着 9-section 中**只有 5 个是规则承载 section**，其它 4 个是元 section（generated from rules and brief）

这个区分必须明确写到 `references/design-md-spec.md` 修复版中。

---

## #8 [LOW] 规则库 fingerprint hashing 与 source-registry 不联动

**问题**：source-registry 里我手动填了 fingerprint hash，但没有自动校验机制。`scripts/add-new-design-system.md` 提到 fingerprint，但没说怎么算、什么时候比对。

如果上游素材库（OD）更新了某套 DESIGN.md，本地 hash 不变 → 用旧规则但用户以为是新的。

**修复方向**：
- `scripts/import-from-collection.md` 增加"重新拉取时比对 hash + 检测漂移"步骤
- `scripts/extract-grammar.md` 在 A1 完成后自动写新 hash 到 registry

---

## #9 [LOW] 工作目录写产物路径默认值缺乏校验

**问题**：spec 说"默认 `./bespoke-design/<slug>/`"，但 pilot 时我**直接写到了** `examples/code-review-saas/` 而非 `./bespoke-design/code-review-saas/`。

这是因为 pilot 是 skill 自身的测试用例，应归入 `examples/`。但 SKILL.md §三 B6 没有区分"用户调用产生的产物"和"skill 自带 example case"——两者落地路径应不同。

**修复方向**：
- B6 prompt 里加：如果当前是 pilot/example 模式，写入 `examples/<slug>/`；否则写入 `./bespoke-design/<slug>/`
- 或在 SKILL.md 添加 `--example` 参数显式标记

---

## #10 [INFO] OD section 数量对了，名字过时了

**问题**：spec § 1.1 说 OD 是"71 套"，实测 `gh api repos/nexu-io/open-design/contents/design-systems` 返回 **137 个目录**。可能 spec 写的时候 OD 还是 71，现在已经增长到 137。

不算 bug——本 skill 不依赖具体数量，只是 README / spec 的描述需要更新。

---

## 端到端 pilot 跑得通的部分

虽然有 9 个 issue，但端到端确实跑通了：

- ✅ 拉取真实素材（2 套）
- ✅ A1 token 提取（结构化精确）
- ✅ A2 三段式 rationale 抽取（trade_off / intent / avoid）
- ✅ A3 参数化规则 + Kansei 标签（共 20 条）
- ✅ A4 关系图构建（4 类边、对称性 OK、无悬挂引用）
- ✅ B0 模式分流
- ✅ B1b auto 推断（合成完整画像）
- ✅ B2 三层检索 + final_score 排序
- ✅ B3 图算法冲突消解（保 Linear 暗底子图、drop Vercel 白底冲突项）
- ✅ B4 三段式 inheritance + adaptation + justification（9 个决策）
- ⚠️ B5 P0 闸门跳过（issue #2）
- ✅ B6 三份产物 + adaptation 提示

**核心机制（双向 rationale 对称、规则反推-正向生成、风格岛聚集）在小规模上验证可行。** 但要生产可用，先修 #1 + #2 这两个 BLOCKER。

---

## 行动建议

修复优先级：

1. **修 #1**（重写 design-md-spec.md + 改 b4/b6 prompt 与 OD 方言对齐）
2. **修 #2**（把 rationale-judge 提到 plugin/agents/，并验证 Agent 工具能调起来）
3. **修 #3 + #7**（合并：明确 rule.section 枚举 + section 是否承载规则的二分）
4. **修 #4**（B3 规模相对化）
5. **修 #5 + #6**（auto 推断分流 + adaptation_id 算法确定化）
6. **修 #8 + #9**（路径与 fingerprint 工程细节）
7. 更新 README / spec 的"71 套"为"137 套（持续增长）"或"~150 套"
