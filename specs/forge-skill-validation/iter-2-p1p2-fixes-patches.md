# iter-2 P1/P2 Fixes — Patches Report

修复对象：iter-2 Step 1 (acceptance-spec) + Step 2 (test-suite-generator) 共 4 P1 + 7 P2。
约束：只能加约束不能删约束 / 不能修改 FLOW.md / 不能修改 issues 归档。
触发 NEEDS_DESIGN_REVIEW：**否**。

---

## 版本同步状态（最终值）

| 文件 | 修复前 | 修复后 |
|------|-------|-------|
| `plugins/done-when-pipeline/.claude-plugin/plugin.json` `version` | 0.3.0 | **0.3.1** |
| `plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md` frontmatter | 0.3.0 | **0.3.1** |
| `plugins/done-when-pipeline/skills/test-suite-generator/SKILL.md` frontmatter | **0.2.0**（漏 bump，是 Step 2 P2-1 直接根因） | **0.3.1** |
| `.claude-plugin/marketplace.json` done-when-pipeline 条目 `version` | 0.3.0 | **0.3.1** |

按 CLAUDE.md 三处同步规则全部对齐到 0.3.1。本次属 typo/template/加约束类，SemVer 取 patch (+0.0.1)。

---

## Step 1 / acceptance-spec — 5 条 issues

### step1-P1-1: REQ-003 把两个独立可派生行为塞进一条 Event-driven SHALL
- **性质**: source-only
- **根因**: SKILL.md 既有铁律没禁止 AND-compound SHALL，worker 判断空间过大
- **修改**:
  - `plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md` 新增 **iron rule 11 "One SHALL clause = one independently-derivable action"**（template 加约束 / 加严现有铁律集，原 11/12 顺移到 13）
  - 同时在 `references/ears-syntax.md` 的 "Common drafting mistakes" 加 "AND-compound SHALL" 行作为铁律 11 的引用锚点
- **artifact 处置**: 不改 `specs/subscription-cancellation/spec.md`，REQ-003 是已 ACCEPTED 的 worker 判断；新规则保未来产出不重蹈

### step1-P1-2: existence 漏列 tasks.md 中已命名的 REQ-005 组件
- **性质**: source-only
- **根因**: SKILL.md 没有"tasks.md 中命名工件必须升 existence"的完备性规则
- **修改**:
  - `plugins/done-when-pipeline/skills/acceptance-spec/SKILL.md` 新增 **iron rule 12 "Existence completeness vs tasks.md"**（template 加约束 / 强制 S3 solidify 前回扫 tasks.md 命名 noun）
- **artifact 处置**: 不改 `done_when.yaml`；新规则保未来产出在 S3 前自动补齐

### step1-P2-1: `done_when.yaml.created_at` 用零点占位与文件 mtime 不一致
- **性质**: 不修
- **根因判定**: SKILL.md / done-when-schema.yaml 没说必须秒级精度。零点占位是常见 ISO-8601 约定。这是 worker 的产物风格选择
- **修改**: 无
- **artifact 处置**: 不动

### step1-P2-2: spec-robustness.md 每条目同时给 `pattern:` 和 `rhd_pattern:` 两个 key
- **性质**: source-only（template）
- **根因**: `references/spec-robustness-template.md` 自身在 closed_vectors / surfaced_vectors 示例里两个 key 都演示，没说明语义边界
- **修改**:
  - `plugins/done-when-pipeline/skills/acceptance-spec/references/spec-robustness-template.md` 把示例中 `pattern: assertion_weakening` 改为 `rhd_pattern: test_modification`（用六类 canonical RHD enum）；保留 `pattern:` 仅作 free-form sub-classification（如 `pattern: branch_coverage_gap`）
  - 在 template 末尾加注释："Use `rhd_pattern:` whenever the entry maps to one of the six RHD patterns; use `pattern:` only for free-form local sub-classification"
  - `acceptance-spec/SKILL.md` 的 S2.5 示例段对齐到新 template
- **artifact 处置**: 不重写 `specs/subscription-cancellation/spec-robustness.md`；保留 worker 已 ACCEPTED 的产物

### step1-P2-3: clarify 答题段把 PM 决策理由内联到 worker 归档日志
- **性质**: 不修
- **根因判定**: 这是 worker 写 output log 的风格，跟 skill 源码无关
- **修改**: 无

---

## Step 2 / test-suite-generator — 6 条 issues

### step2-P1-1: `unit/premium_access.test.ts` 末尾再次 import `CancelSubscriptionUseCase`
- **性质**: both (source + artifact)
- **根因**: `references/sub-modules/unit-test-generator.md` 检查表没有"所有 import 必须顶部"硬规则
- **修改**:
  - `plugins/done-when-pipeline/skills/test-suite-generator/references/sub-modules/unit-test-generator.md` 新增 **"Imports stay at the top (hard rule)"** 章节 + checklist 新增 "All `import` statements live at the top of the file" 检查项
  - 章节内含正例 TS code block 演示一次性 import 全部 PBT 体引用的符号
- **artifact 修补**: `tests/subscription-cancellation/unit/premium_access.test.ts` 把末尾游离的 `import { CancelSubscriptionUseCase }` 合并到顶部 import block（验证：`grep "^import" premium_access.test.ts` 现仅返回顶部 3 个 import 语句）

### step2-P1-2: existence.sh `function:` rg pattern 漏 `export {}` 和 `export default`
- **性质**: both (source + artifact)
- **根因**: `references/sub-modules/existence-extractor.md` function-kind 模板 rg pattern 只写 `export\s+(class|function|const)\s+<Name>`
- **修改**:
  - `plugins/done-when-pipeline/skills/test-suite-generator/SKILL.md` §4-A function 行改为加宽 pattern：`rg -qU "export\s+(default\s+)?(class|function|const|let|var)\s+<Name>\b|export\s*\{[^}]*\b<Name>\b" src/`
  - `references/sub-modules/existence-extractor.md` 同步更新模板，加注释解释为何要覆盖 default / named re-export
- **artifact 修补**: `tests/subscription-cancellation/existence.sh` 第 30 行 rg pattern 替换为加宽版本（验证：grep 显示新 pattern 含 `default\s+`、`let|var`、和 `export\s*\{[^}]*\b...`）

### step2-P2-1: 14 个产出文件自报 `test-suite-generator/0.2.0`
- **性质**: both (root cause 是源码 frontmatter，artifact 也要顺手刷)
- **根因（最致命）**: `plugins/done-when-pipeline/skills/test-suite-generator/SKILL.md` frontmatter `version: 0.2.0` 在 v0.3.0 plugin 升级时未 bump。其它 sub-modules 用了硬编码 `0.1.0` / `0.2.0` 而不是占位符
- **修改**:
  - SKILL.md frontmatter version `0.2.0 → 0.3.1`（同时对齐到本次 patch）
  - SKILL.md 新增 **iron rule 12 "Self-report version comes from this SKILL.md frontmatter"** + §4-B "Version-string substitution rule" 说明（template 加约束）
  - 5 个 sub-modules (`unit-test-generator.md`, `existence-extractor.md`, `mutation-config.md`, `fitness-rubric.md`, `e2e-generator.md`) 模板里 `Generated by test-suite-generator/0.1.0` / `/0.2.0` 全部替换为 `<skill-version>` 占位符并加注释 "substitute from SKILL.md frontmatter `version:`"
  - `plugin.json` + `marketplace.json` 同步到 0.3.1（见版本表格）
- **artifact 修补**: `tests/subscription-cancellation/` 下所有 14 个产出文件的 "Generated by …/0.2.0" 字符串替换为 "…/0.3.1"（验证：grep 显示全 14 个文件均报 0.3.1）

### step2-P2-2: `stryker.conf.json` mutate 数组同一来源列两遍
- **性质**: both
- **根因**: `references/sub-modules/mutation-config.md` 示例同时列具体路径和 glob
- **修改**:
  - `references/sub-modules/mutation-config.md` 示例只留 glob `src/<module>/**/*.ts`，加注释 "Do not list both a specific path and a glob that already covers it — the glob alone is sufficient"
- **artifact 修补**: `tests/subscription-cancellation/stryker.conf.json` mutate 数组去掉具体路径 `"src/billing/cancel_subscription_use_case.ts"`，只留 `"src/billing/**/*.ts"` 加 4 条排除

### step2-P2-3: 两份 rubric "How to run" 段落几乎逐字重复
- **性质**: both
- **根因**: `references/sub-modules/fitness-rubric.md` 示例让每份 rubric 自带完整 "How to run"
- **修改**:
  - `references/sub-modules/fitness-rubric.md` 改为"在 fitness/README.md 写一次完整 How to run，每份 rubric.md 只 link 到 README.md"
  - 加 "DRY: never duplicate the workflow text across multiple .rubric.md files" 注释
- **artifact 修补**:
  - `tests/subscription-cancellation/fitness/README.md` 扩写为含完整 5 步 "How to run" 说明
  - 两份 `.rubric.md` 各自 "How to run" 段替换为单行 "See `fitness/README.md` § How to run"
  - 验证：`grep -c "Open a fresh Claude session"` README.md=1, 两份 rubric=0

### step2-P2-4: README.md "Counts" 段 16 unit vs NOTE 14 unit 自相矛盾
- **性质**: both
- **根因**: SKILL.md "After all six sub-steps" 段没规定 counts 必须 verbatim 数 `done_when.yaml`
- **修改**:
  - `plugins/done-when-pipeline/skills/test-suite-generator/SKILL.md` "After all six sub-steps" 新增 **"Counts must be verbatim from `done_when.yaml`" hard rule**：每个数值 = `len(YAML 对应字段)`，禁止 "本来 10 例子 + 4 PBT + 凑出几个 helper = 16" 这种推理式计数
- **artifact 修补**: `tests/subscription-cancellation/README.md` Counts 段改为 `**7 existence checks · 14 unit tests (10 example / 4 PBT) · 5 integration tests (3 example / 2 PBT) · 2 e2e tests · 2 fitness criteria**`（verbatim 对应 done_when.yaml）

---

## 总结

| 类别 | 数量 |
|------|------|
| 处理 issues 总数 | 11 (4 P1 + 7 P2) |
| Source 加约束 | 9 (iron rules / hard rules / template 收紧) |
| Artifact 修补 | 8 (Step 2 全部 + Step 1 P2-2 spec-robustness) |
| 不修 (worker 风格 / 已 ACCEPTED 产物) | 3 (step1 P2-1 created_at 占位 / step1 P2-3 log 风格 / step1 P1-1+P1-2 artifact 不动) |
| 版本 bump | 4 处全部对齐 0.3.1 |
| NEEDS_DESIGN_REVIEW | **否** |

修复模式总体属"加约束 + template 加严 + 版本同步"，未删除任何现有指令或机制；未改 FLOW.md (`docs/pipeline-flow.md`)；未改 worker 产出归档 (`specs/forge-skill-validation/iter-2-*-output.md` + `iter-2-*-issues.md`)；未改 issues-summary.md / iter-log.md 中已记录的 ACCEPTED 结论。

下一轮验证（如果再开 iter-3）应能在 attempt 1 用更严的 skill 产出更干净的 5 份 / 6 batch 文件。
