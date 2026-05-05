# Bespoke-Design-System Skill 问题记录(汇总)

**日期**:2026-05-05
**Skill 版本**:1.9.0
**触发场景**:用户要求"用项目里的 bespoke skill 给 OPC 工作台生成 DESIGN.md"
**执行方式**:Skill 工具不可用 → 改为直接用 Python + Bash 跑源码,完整走完 B0-B6
**最终结果**:5 项 P0 闸门全部通过(2 轮迭代),产物落在
`~/Documents/Downloads/bespoke-design/opc-workbench/`(DESIGN.md / provenance.yaml /
negotiation-summary.md / tokens.json)

---

## 问题清单

| # | 严重度 | 类型 | 一句话描述 |
|---|-------|------|-----------|
| 1 | **blocker** | 部署 | plugin cache 没同步,session 中 skill 不可用 |
| 2 | medium | schema | `b3_resolve.py` 期望 `candidate_rules` 字段,但 B2 输出字段名 SKILL.md 未规范 |
| 3 | medium | docs/code 不一致 | `b3_resolve.py` docstring 把 `--output` 写成"目录",实际是文件路径 |
| 4 | medium | docs/code 不一致 | `coherence_check.py` docstring 标了 `--design-md`,但 argparse 没注册该参数 |
| 5 | medium | schema | `kansei_coverage_check.py` 期望 `justification.user_kansei_coverage` 是 dict,SKILL.md §六 3.3.7 未明确,写成 string 会 `AttributeError` 崩溃 |
| 6 | low | 流程模糊 | B3 自洽集允许 archetype-mismatch 规则进入,但 SKILL.md 铁律说"B4 不创造新规则",未规范"选择性使用 ≠ 创造" |

---

---

## 现象

`bespoke-design-system` skill 在当前 Claude Code session 中**未出现在可用 skills 列表**,
无法通过 `Skill(bespoke-design-system)` 调用。

但与现有 memory `feedback_plugin_enable_required.md` 描述的情况**不同**——
这次三处注册全部正确:

| 检查项 | 状态 | 路径 / 内容 |
|--------|------|-------------|
| marketplace.json 注册 | ✅ 完整 | `.claude-plugin/marketplace.json` 含 `bespoke-design-system` 条目,`source: "./plugins/bespoke-design-system"` |
| plugin.json 完整 | ✅ 完整 | `plugins/bespoke-design-system/.claude-plugin/plugin.json`,version 1.9.0 |
| SKILL.md 完整 | ✅ 完整 | frontmatter 含 `user-invocable: true`,name 一致 |
| enabledPlugins 启用 | ✅ 已启用 | `~/.claude/settings.json` 含 `"bespoke-design-system@claude-code-forge": true` |

但 session 启动后,可用 skills 列表里仍然**没有** `bespoke-design-system:*` 任何 skill。

---

## 根因定位

**Plugin cache 没同步**:

```bash
$ ls ~/.claude/plugins/cache/claude-code-forge/
forge-teams    pdforge
```

`~/.claude/plugins/cache/claude-code-forge/` 下**只有 `forge-teams` 和 `pdforge`**,
**没有 `bespoke-design-system` 目录**。对比已正常工作的两个 plugin,正确结构应该是:

```
~/.claude/plugins/cache/claude-code-forge/
├── forge-teams/1.9.0/...
├── pdforge/1.14.0/...
└── bespoke-design-system/1.9.0/...   ← 缺失
```

Claude Code session 启动时是从 `cache/` 读取 SKILL.md 索引,而**不是**从
源仓库 `plugins/<name>/` 直接读。所以即使源仓库一切正常、enabledPlugins 已启用,
cache 没同步 = skill 不可见。

---

## 与现有 memory 的差异

`feedback_plugin_enable_required.md` 记录的 bug:
> marketplace 注册完只完成一半,enabledPlugins 漏了

本次 bug:
> marketplace + enabledPlugins 都对,**但 plugin cache 没同步**

→ 现有 memory 里"修改 enabledPlugins 后重启 session"的修复路径**不充分**。
还需要保证 `cache/<marketplace>/<plugin>/<version>/` 目录存在。

---

## 修复路径(待用户验证)

**候选 1**:让 Claude Code 重新拉取 plugin 到 cache
```bash
# 推测命令(需用户在 Claude Code 中尝试):
/plugin install bespoke-design-system@claude-code-forge
# 或
/plugin update bespoke-design-system@claude-code-forge
```

**候选 2**:手动同步(临时绕过)
```bash
mkdir -p ~/.claude/plugins/cache/claude-code-forge/bespoke-design-system/1.9.0
cp -r /Users/xrensiu/development/owner/claude-code-forge/plugins/bespoke-design-system/* \
      ~/.claude/plugins/cache/claude-code-forge/bespoke-design-system/1.9.0/
# 然后重启 session
```

**候选 3**:删除整个 cache 重建
```bash
rm -rf ~/.claude/plugins/cache/claude-code-forge
# 重启 Claude Code,应触发自动 sync
# 但风险:其他 plugin 也会被重拉,有风险
```

均未实测;**建议候选 1 优先**。

---

## 对项目的影响 / 应记录到 CLAUDE.md 或 memory

1. **CLAUDE.md 当前的"同步清单"不完整**:
   - 现有写的:SKILL.md → plugin.json → marketplace.json → enabledPlugins(共 4 处)
   - 实际还要保证:plugin cache 真的有这个版本目录
   - 第 5 项是 Claude Code 内部行为,文档应说明"如果做了前 4 步还报 Unknown skill,
     检查 `~/.claude/plugins/cache/<marketplace>/<plugin>/`"

2. **memory `feedback_plugin_enable_required.md` 应扩充**:
   - 排查顺序加一条:cache 目录是否存在该 plugin
   - "重启 session 即可"的说法不严谨

---

## 临时方案:不依赖 skill 调用,手动跑流程

skill 源代码完整且齐全(本仓库 `plugins/bespoke-design-system/skills/bespoke-design-system/` 下):

- `grammar/rules/` 含 43 个 yaml(airbnb/apple/arc/...)+ `_generated.yaml` —— **B2 检索可用**
- `grammar/graph/rules_graph.json` —— **B3 冲突解决可用**
- `grammar/meta/defaults.yaml` —— **B1b auto 模式默认值可用**
- `checks/coherence_check.py / archetype_check.py / kansei_coverage_check.py / neighbor_check.py` —— **B5 闸门可用**
- `agents/rationale-judge.md` —— **可通过 Agent(subagent_type=...) 调用,但需要插件层注册**

可以手动按 SKILL.md 的 B0–B6 流程,直接读取这些文件、用 Bash 跑 checks 脚本,
模拟 skill 行为产出 DESIGN.md + provenance.yaml + negotiation-summary.md。
**但这是降级方案**——失去:
- skill 提供的状态消息规范("Now retrieving candidate rules from grammar...")
- 调用 rationale-judge 时的隔离上下文(需手动用 Agent 工具显式隔离)
- Skill 框架对 anti-pattern 的兜底校验

---

## 建议下一步

1. **先修复 plugin cache 问题**(优先候选 1,失败再候选 2),重启 session
2. 修复后用真正的 `Skill(bespoke-design-system)` 跑流程
3. 把本 issue 的发现整合进 `CLAUDE.md` 与 `feedback_plugin_enable_required.md`
4. 验证 forge-teams 和 pdforge 能进 cache 但 bespoke 不能进 cache 的根因
   (可能是 plugin 添加时机 / `/plugin install` 是否被显式跑过 / marketplace 索引刷新机制)

---

## 问题 #2-#6 详情(执行 B0-B6 时新发现)

### #2 — `b3_resolve.py` 期望字段名 `candidate_rules`

**位置**:`tools/b3_resolve.py` line 91
```python
candidates = b2['candidate_rules']
```

但 SKILL.md §三 B2 节 + `prompts/b2-rule-retrieval.md` 没规定 B2 输出 JSON 应该用什么字段名。
执行时如果 B2 用了 `candidates` 或 `rules` 等其他字段名,b3_resolve 会 `KeyError`。

**修复建议**:在 `prompts/b2-rule-retrieval.md` 显式声明输出 schema
`{candidate_rules: [{rule_id, section, final_score, ...}], count, profile}`,
或让 b3_resolve 兼容多字段名。

### #3 — `b3_resolve.py` `--output` 参数语义混乱

**位置**:`tools/b3_resolve.py`
- docstring(line 5-11):
  ```
  Reads:
    - <output_dir>/_b2-candidates.json (B2 output)
  Writes:
    - <output_dir>/_b3-self-consistent.json
  ```
- 实际(line 322):`with open(output_path, 'w')` — 把 `args.output` 当**文件路径**用

**症状**:传目录会 `IsADirectoryError`,传文件路径才能跑通。docstring 应改成"`--output <file_path>`"
或代码改成接收目录然后内部组合文件名。

### #4 — `coherence_check.py` `--design-md` 参数缺失

**位置**:`checks/coherence_check.py` line 1-3
```python
"""
  python3 coherence_check.py <path/to/tokens.json> [--design-md <path>]
"""
```

但实际 argparse 只注册了 `tokens_path` positional 参数。

**症状**:按 docstring 示例传 `--design-md path` 直接 `unrecognized arguments`。

**修复建议**:要么实现 `--design-md`(用于检查 DESIGN.md 中的描述与 tokens 一致性),
要么从 docstring 删除该参数。

### #5 — provenance schema 不一致(类型未规范)

**位置**:`checks/kansei_coverage_check.py` line 46
```python
cov = just.get('user_kansei_coverage', {}) or {}
for k in (cov.get('addressed_in_this_decision') or []):
```

但 `SKILL.md §六 3.3.7 Provenance Report Schema` 只写:
> `justification.{internal_consistency[], user_kansei_coverage, conflict_check}`

**没规定** `user_kansei_coverage` 是 dict 还是 string。生成方按字面理解写成 string
(如 "precise + confident") 会让 check 在 `cov.get(...)` 处 `AttributeError`。

**修复建议**:`SKILL.md §六 3.3.7` 显式声明:
```yaml
user_kansei_coverage:
  addressed_in_this_decision: [<kansei_word>, ...]   # required, list of strings
  addressed_elsewhere: [<kansei_word>, ...]          # optional
  uncovered: [<kansei_word>, ...]                    # optional
```

### #6 — B3 自洽集 vs B4 选择性使用的边界模糊

**症状**:B3 算法把 `cohere-components-22px-signature-radius-002` 留在自洽集
(它跟 Linear 6px button 没在 conflicts_with 关系里),但实际 B4 应该拒绝采用——
因为 Cohere brand_archetypes 是 [Sage, Ruler],我们是 [Sage, Creator],secondary 不匹配。

按 SKILL.md 铁律 "B4 是翻译不是创造,不引入 B3 子集之外的新规则",
**严格读**会以为 B4 必须用 B3 子集里所有规则。但实际产生品味需要 B4 选择性使用,
对不匹配的规则做出"拒绝采用"的判断(同时记录到 provenance 的 conflict_check 里)。

**修复建议**:在 `prompts/b4-generation-with-rationale.md` 加一节"B3 子集是上限,
B4 可对任一规则做 'rejected' 判断,但拒绝必须有 archetype/kansei 层面的论证证据
(对 archetype-do-dont-table 或 kansei-theory 的具体引用),否则视为越权"。

本次执行的 §4.1 button 决策里,我已经按这个理解记录了
`rejected_alternative_cohere_22px`,但 SKILL.md 没明文授权。

---

## 实测产物质量

虽然 skill 工具有上述 6 个问题,在生成方(我)逐一绕过后,B0-B6 完整跑完:

- **B0**:规则库健康度 276 rules / 42 systems / 1226 edges / 0 broken refs
- **B1b**:auto 模式推断 8 个字段,inferred 全部标注
- **B2**:202 候选(archetype filter Sage+Creator + product_type 兜底)
- **B3**:76 自洽规则 / 9 sections / 0 degraded sections
- **B4**:9-section DESIGN.md(Dialect A)+ 完整 provenance.yaml + negotiation-summary.md
- **B5**:5 项 P0 闸门 round 2 全部通过
  - coherence: score 0.765(threshold 0.55)
  - archetype: 0 blocker on Sage primary
  - kansei: coverage 100%(threshold 80%),0 reverse violations
  - neighbor: distance 0.178(threshold 0.3),最近邻 = linear-app
  - rationale-judge:round 1 抓到 1 真实 blocker(luminance step +0.02 vs +0.04)+
                    5 specific warnings + 1 global,round 2 全部解决
- **B6**:产物路径 `~/Documents/Downloads/bespoke-design/opc-workbench/`,
         自演化数据(adaptation-stats updates)写入 provenance

**rationale-judge 抓到的真实问题特别值得记录**:
我在初稿里把 Linear elevation 规则原文 `level_increments_via: bg_alpha_white +0.02 per step`
误述为 preserve `+0.04`。这是真实的事实错误,被 round 1 评判方一击命中。
说明 P0 闸门第 5 项(rationale-judge)的对抗式审查机制是有效的,**不是装饰**——
即使是认真生成的草稿也会有需要外部独立审查才能发现的事实漂移。
这条价值实测之后,plugin cache 修复优先级建议 ↑。
