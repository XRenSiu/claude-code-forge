---
name: pr-review
description: >-
  补引擎自己给不出的缺口：审 PR 时什么算一条"能落地的发现"（P0/P1 必带复现场景、自我反驳一遍
  再发、上限 5 条不凑数、空结果也要给走过的路径）、发现按 A 机械 / B 结构 / C 判断三档归位
  （只有 A 档一票否决，B 有界可进，C 请求人工）、以及 Detective Loop（自己决定下一步读什么，
  不按清单走）。效果：PR# / ref 范围 / diff 文件 → findings.yaml → 可选发成 GitHub review
  （行内评论；永不 approve）。Use when: "审一下这个 PR" / "review PR #12" / "看看这个 diff 有
  没有 bug" / "code review" / "帮我找问题" / 引擎准备只回"看起来不错"时。NOT for: 需求合规
  （/pm-reviewer）、真跑测试（/qa-reviewer）、契约作弊检测（/spec-gaming-detector）、
  你是 PR 作者要处理评论（/review-loop）。借鉴 done-when-pipeline `/code-reviewer` v1.0.0。
argument-hint: "<PR# | git ref range | .diff 文件 | 目录> [--focus security|logic|perf|style|all] [--rules PATH] [--post] [--event COMMENT|REQUEST_CHANGES] [--max-findings 5] [--adversarial]"
version: 0.1.0
user-invocable: true
---

# pr-review — diff 进，能落地的发现出

产物是 `findings.yaml`（形状：`assets/findings_template.yaml`），可选地发成一个 GitHub review。本文件
写：发现的判据、三档映射、原语与出口、发之前的门。先读哪个 hunk、要不要多跳几层是你的份额。

## 缺口（Judgment + Capability + Control）

deletion 测试：撤掉本 skill，引擎读完 diff 回"整体结构清晰，有几个小建议"——没有一条带复现场景，
没有一条能直接改，reviewer 的时间被 nit 淹没，真正的 P0 被"看起来不错"盖住。缺的是判据（什么算
发现、什么不算）、档位（谁一票否决、谁只告警）、原语（把发现发到正确的行）与门（永不 approve）。

## 世界（Σ）

- **你看到的是 diff，不是整个仓库**：diff 引用了你看不到的定义 → `LOCATE` + `READ` 去看，不因
  "看不到"标发现；预算内看不到 → `needs_codebase_check: true`，交人。
- **三档**（Spec Loop L7 的裁决 C9）：**A 机械档**——测试 / lint / 类型 / secrets / 白名单 / 锁 /
  新增依赖（注册表存在性、许可证、漏洞）/ 契约硬命中（改测试、删断言、mock 越界）——一票否决 =
  P0，有则一起修；**B 结构档**——圈复杂度 / 重复 / 公共 API 变更 / diff 体量 / 依赖方向——超阈值告警
  = P1/P2，有界可进；**C 判断档**——架构意图、可读性、命名、human AC——只请求人工 = P3 或路由 G3。
  一条发现只归一档，档位由内容决定不由语气决定。
- **发现的成本不对称**：P0/P1 漏报 = 事故，误报 = reviewer 花 5 分钟；P2/P3 误报 = 噪声淹没信号。
  所以 P0/P1 偏召回（中等置信也报），P2/P3 偏精确（不确定就不报，不报成 `confidence: low`）。
- **同模型审同模型有系统盲区**：对抗式审查（"假设这段代码造成了线上事故，找为什么"）用另一家
  模型（Codex / Gemini CLI 在则用）或至少不同尺寸；做不到就在输出顶部标 `single-vendor caveat`。
- **GitHub review 的性质**：行内评论只能挂在 diff 里出现的行（新文件坐标）；不在 diff 里的位置降级
  为 PR 级评论并引用 `path:line`；`REQUEST_CHANGES` 会阻塞合并（有 A 档发现时才用）；
  **APPROVE 是人类动作**。
- **关于用户的 Σ**："看看有没有问题"= 要发现，不要夸奖；"帮我 review 一下再合"= 要一个能否合的
  结论 + 阻塞项清单，不是散文。

## 判据（φ）

- **一条发现 = 位置 + 机制 + 复现 + 证据 + 改法**：`file:line_range`、`root_cause`（一句机械描述）、
  P0/P1 必有 `reproduction_scenario`（具体输入 / 时序 / 状态），`evidence`（读了哪、grep 了什么、
  git log 看到什么），`suggested_change`（P0/P1 必有，一行可执行）。缺任一项的 P0/P1 降级或删。
- **自我反驳后才发**：把发现写成假设，"如果它不是 bug，代码会长什么样？实际代码是不是那样？"能
  构造出合理的非 bug 解释 → 删。
- **上限 5 条**（`--max-findings`）：超过按严重度再按证据强度取前 5；剩下的留给下一轮。发现少于
  5 不凑；发现为 0 → `findings: []` + `rationale`（走了哪些路径、为什么没问题）。
- **一次一个 focus**：`--focus=security` 只报安全类；其他焦点另开一次（`all` 只在 Opus 级模型上用）。
- **禁语**：`看起来不错` / `整体结构清晰` / `可以考虑` / `作为小建议`——要么有证据的发现，要么没有。
- **B 档阈值**（可被 `--rules` 覆盖）：函数 > 50 行、嵌套 > 4、文件 > 500 行、重复块 > 20 行 ×2、
  公共 API 签名变更无 CHANGELOG / 迁移说明、diff > 500 行。
- **新增依赖进 A 档**：`package.json` / `requirements.txt` / `go.mod` 新增包 → 注册表存在（防编造包名）
  + 许可证 + 已知漏洞（`npm audit` / `pip-audit` 有则跑）；查不到 → P0 `needs_codebase_check`。
- 残差（人）：架构意图对不对、这个抽象值不值——写成 C 档 P3，或直接建议 G3。

## 原语（Π）

- `scripts/post_review.py findings.yaml --pr N [--event COMMENT|REQUEST_CHANGES] [--dry-run] [--summary-only]`
  —— 把 findings 发成一个 GitHub review：行内评论落在 diff 可评论行上（脚本对照 `gh pr diff` 校验，
  不可评论的降级为汇总里的 `path:line`）；**拒绝 APPROVE**（不是选项）；`--dry-run` 只打印 payload。
- `assets/findings_template.yaml` —— 输出形状（含 `tier`、`severity`、`reproduction_scenario`、`evidence`）。
- `references/focus-areas.md` —— 各 focus 的问题清单（security / logic / perf / style）。
- `references/tiers.md` —— 三档 ↔ 检查项 ↔ 执行者 ↔ 效力的映射表与 B 档阈值。
- 输入解析：`#N` / 纯数字 → `gh pr diff N`；`A..B` → `git diff A..B`；`.diff/.patch` 文件；目录 →
  `git diff HEAD`。空 diff → 拒："no diff to review"。> 500 hunks → 拒："按目录 / commit 拆开审"。
- 只读工具：read / grep / git log / git blame（不用 blame 找人，只找"什么时候拿掉的检查"）。
  预算 ~20 次工具调用；超预算的 hunk 放弃，不硬凑发现。

## 门（γ）

- **发之前给人看**：`--post` 时先展示 findings + 将用的 event，确认再发（`--yes` / autopilot 免）。
  无 `--post` 只写 `findings.yaml` 到 `.sdlc/review/<pr>-<focus>.yaml`（或用户指定路径）。
- **event 由档位决定**：任一 A 档发现 → `REQUEST_CHANGES`；只有 B/C → `COMMENT`。不因"感觉"升级。
- **done_when**：findings.yaml 形状合法 ∧（发了 review 或明确未发）∧ 回报：档位统计、P0/P1 清单、
  能否合的结论（`mergeable: yes | no (A-tier) | with-warnings (B-tier)`）。
- **信息隔离**：作为 /sdlc 验收的一部分时，本 skill 的输出只给人和 meta-judge，**不直接给实现
  子 agent**（实现者拿到的是 fix-prompt 形态：file:line + 改法，不含评审者身份与置信度）。

## 失败机制

- PR 不存在 / 无权限 → 停，报错原文。
- diff 里调用了看不到的函数 → 读它；读不到 → `needs_codebase_check`，不猜。
- `post_review.py` 报某行不可评论 → 自动降级到汇总，不改行号硬贴。
- 用户要求 approve → 拒绝并说明：approve 是人类动作；可给"我认为可合"的结论。
- `--adversarial` 但无跨供应商评估器 → 照跑，顶部标 caveat，不静默降级。

## 高危黑名单（不可豁免）

- **绝不 approve / merge**。
- **绝不发无复现场景的 P0/P1**；绝不凑数到 5 条；绝不用禁语。
- **绝不把 findings 直接喂给实现子 agent**（信息隔离）；绝不在评论里泄露隐藏集内容。
- **绝不把 B 档告警写成阻塞**（除非 `--rules` 明确提升）；绝不把 A 档发现写成"建议"。
- **绝不修改被审代码**（只读角色）。

## 接线

- 上游：/pr（body 的 Scope 与 Reviewer focus 是读 diff 的起点）。
- 邻居：done-when-pipeline 的 `/code-reviewer`（同源；有则优先用它做 security/logic 焦点）、
  `/qa-reviewer`、`/spec-gaming-detector`、`/meta-judge`（汇总多份 findings）。
- 下游：/review-loop（PR 作者侧处理这些评论）；/sdlc 的 acceptance 阶段（无 acceptance-fleet 时的替代）。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`post_review.py --dry-run` 在 fixture findings + fixture diff 上冒烟
（可评论行 / 不可评论行降级 / APPROVE 被拒）。行为层未跑。
