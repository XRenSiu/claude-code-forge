# 在 vana-builder 里用 AI-DLC 的操作方案

> 目标仓库：`~/development/repository/vana-builder`（xmindltd/vana）
> 插件版本：按 v1.7.0 写（V-01～V-09 已修）。使用中发现的问题追加到同目录 `issues-2026-09-14.md`。

vana 不是空仓库，它有自己的 harness（17 个 skill、3 个 hook、中文 PR 模板、`v*` 发版分支）。
这份方案是把 AI-DLC 叠上去，不是从零搭。

## 第 0 步：部署

```bash
# 1. /plugin 里更新 ai-dlc 到 1.7.0（本机现在装的是 1.6.0）
jq '.plugins["ai-dlc@claude-code-forge"][0].version' ~/.claude/plugins/installed_plugins.json   # 应为 "1.7.0"

# 2. 运行时目录只在本机忽略，不动团队 .gitignore
cd ~/development/repository/vana-builder
printf '.aidlc/\nspecs/\n' >> .git/info/exclude

# 3. 在 vana-builder 里新开会话，然后跑一次 doctor
AIDLC=~/development/claude-code/claude-code-forge/plugins/ai-dlc/skills
python3 $AIDLC/ai-dlc/scripts/aidlc_state.py doctor
```

doctor 预期会报：
- 同名 skill（warn）：`commit`、`pr`、`review-pr`，以及你用户级的 `dos-extract`。
- 近名 skill（info）：`pr-review-loop`、`release-build`。

所以在 vana 里调插件的子 skill 一律写全名：`/ai-dlc:commit`、`/ai-dlc:pr`、`/ai-dlc:review-loop`。
如果 doctor 还报「plugin version 漂移」，说明安装没更新或会话没重开。

## 第 1 步：选试点，先 dry-run

选题标准：
- 已有 issue、没人在做（别选标了 `S: doing` 的）；
- bug 或小改进，预计改 5 个文件以内，走 TASK 轨；
- 行为能用 vitest 验证，别选只能靠 E2E 验的原生 API 相关问题。

```
/ai-dlc "#<N>" --track task --dry-run
```

## 第 2 步：契约与 G2

- **issue**：复用已有 issue 号（`set issue.number=N`）。AI-DLC 格式的 issue 正文放在本地 `.aidlc/<slug>/issue-body.md`，
  用 `verify_issue.py` 校验，不在团队的 issue 列表里新建或改写。
- **定档**：`size --from-issue .aidlc/<slug>/issue-body.md --early --commit`，再用 `plan` 看要跑哪些阶段。
- **分支**：按 vana 规范命名 `<你>/fix/<desc>`，base 按 `.claude/skills/_shared/base-detection.md` 反查（可能是 `v*`）。
  `set branch.name=… branch.base=…`。
- **契约**：用 `/ai-dlc:donewhen-extract` 生成，`constraints` 里写：
  ```yaml
  test_globs: ["**/*.spec.ts", "**/*.spec.js", "test/**", "e2e/**"]
  forbidden_paths: [tests/**, done_when.yaml, dos.yaml, contract.yaml, .done_when.lock,
                    "**/*.spec.ts", "**/*.spec.js", "test/**", "e2e/**"]
  ```
  这组 glob 已对 vana 实测，覆盖 325/325 个测试文件。少写的话 `advance g2` 会拒，或 flag 出没盖住的文件。
- **G2**：先跑 `notes --for-gate g2` 逐字看完，再由你本人签 `lock_done_when.py sign --stage g2 --by <你>` 和 `gate g2`。

## 第 3 步：卡片、测试、实现

- **拆卡**：`/ai-dlc:plan-cards`（S 档可能被网格跳过）。
- **写测试**：`/ai-dlc:test-suite-generator`，写法按 vana 的 `.claude/rules/testing.md`（可以让 `vana-test-writer` 执笔，
  账本记 executor）。
  - 写完用 `lock_done_when.py sign --stage l5 done_when.yaml <spec 文件…>` 签锁；
  - 再用 `capture_red_baseline.py` 抓一份「实现前是红的」证据。
- **实现**：`/ai-dlc:implement`（card-implementer），提交用 `/ai-dlc:commit`，commit message 写英文。
- **观察点**：vana 的 `guard.mjs` / `format.mjs`（会改写文件）/ husky pre-commit，与 `verify_commit.py` 叠加时会不会打架。

## 第 4 步：验收

- `/ai-dlc:acceptance-fleet`，记下耗时和 token。
- 和 vana 自带的 `review-pr multi` 各跑一次，对比结果。

## 第 5 步：PR → review → G3 → 合入

- **PR 正文**：按 vana 模板写（`# 中文摘要 #N`、`## 🎯 概览`、`## ✅ 测试`…），AC id 写在对应条目后的 `<!-- AC-001 -->` 注释里。
  发之前用插件的闸检一次：
  ```bash
  python3 $AIDLC/pr/scripts/verify_pr.py --body body.md --base <切出来的分支> \
    --sections $AIDLC/pr/eval/fixtures/sections_zh.yaml --done-when <done_when.yaml> --title "fix(x): …"
  ```
  `sections_zh.yaml` 就是照 vana 模板写的映射，试点期直接用；跑通后再决定要不要放进团队仓库。
  scope、risk_rollback、reviewer_focus 三个槽是带理由豁免的，会作为 flag 呈现。
- **远端**：vana 的 `origin` 是 GitLab 镜像，本地 master 跟踪的是 `github`。feature 分支 push 到 `github` 并建立跟踪，
  同步检查才会比对对的远端，否则会记为跳过。
- **review**：用 `/ai-dlc:review-loop <PR#>`。`advance g3` 认的是它写在 `.aidlc/pr-watch/` 下的裁决文件，
  vana 自带的 `pr-review-loop` 写在 `.claude/pr-watch/`，不被认。
- **G3 与合入**：G3 你签，合入你点。

## 第 6 步：收尾

- **发版**：vana 走人工触发的 `release-build`，版本号 `26.04.01341` 不打 tag，所以
  `set release.skipped_reason="vana 发版走 release-build，版本与 tag 不由本流程产出"`。
  想留一份发布说明当证据的话，写 `releases/v<版本>.md`，用 `verify_release.py --version <版本> --scheme external` 检。
- **归档**：`archive --to specs/<slug>/`（已在本机 exclude），然后 `/ai-dlc:retro specs/`（一个样本只记基线）。
- **记问题**：把跑动中发现的问题追加到 `issues-2026-09-14.md` 的「跑动中发现的」。

## 第二轮（第一轮跑通之后）

- **X1 本体**：对试点模块做 `/ai-dlc:dos-extract`，`--scope docs/ontology/<模块>`（scope 不必是代码目录）。
- **agent-map**：不重抄 CLAUDE.md，禁区与陷阱用 `file:CLAUDE.md#"原文里的一句"` 引用，`verify_agent_map.py` 会核对原文还在。
- **L 档试点**：挑一个 `docs/features/` 里带人工验收项的需求，走 L 档，把 G3 和 acceptance 的人工 AC 路径走通。

## 需要你拍板的事

1. `dos.yaml` / `agent-map.md` / PR 映射文件要不要进团队仓库：建议试点期不提交。
2. 不在团队的 issue 列表里建 AI-DLC 格式的 issue，复用现有 issue。
3. G2 / G3 由你签，插件规则不允许模型代签。

## 已知未修

- `verify_commit.py` 的调试代码检测 `dd\(` 没加词边界，`seen.add(real)` 会被误报成调试输出。
  只产生 flag，不拦提交。
