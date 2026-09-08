---
name: pr
description: >-
  补引擎自己给不出的缺口：PR 描述必须呈现的产物序（范围声明 → Closes #N → 变更 → 验证证据 →
  AC→证据映射 → 风险与回滚 → 审阅焦点），它是 review 阶段判"越界"的基准、是 A 档验收的输入；
  PR 体量分级与"XL 必拆"的判据；push 前的预检（不在 base 上、与 base 同步、自检绿、提交都合规）——
  全部编译在 verify_pr.py 里。效果：`gh pr create --fill` 变成一个能被机器检、能被 reviewer
  按图索骥的 PR。Use when: "发 PR" / "开个 pull request" / "把分支提上去 review" / "create a
  PR" / "open a pull request" / 引擎准备 `gh pr create --fill` 时。NOT for: 单次 commit
  （/commit）、跟进 PR 评论（/review-loop）、审别人的 PR（/pr-review）、直接合并（人类动作）。
  前置：gh 已认证、在目标仓库内、分支已有至少一个 commit。
argument-hint: "[--base main] [--issue N] [--draft] [--done-when done_when.yaml] [--cards cards/] [--pre-review [--rounds 2]] [--yes] [--dry-run]"
version: 0.3.1
user-invocable: true
---

# pr — 一份能被机器检、能被人按图索骥的 PR

产物是一个 GitHub PR：body 按 `assets/pr_template.md` 的段落序呈现（产物序，出口可检）。本文件
写：PR 在流水线里是什么、什么算写对、原语与出口、建之前的门。先 rebase 还是先写 body、要不要拆
是你的份额——除非下面说了它是不可逆的。

## 缺口（Judgment + Capability + Control）

deletion 测试：撤掉本 skill，引擎 `git push && gh pr create --fill`：标题是最后一条 commit，body
是 commit 列表。reviewer 不知道范围在哪、AC 有没有被覆盖、怎么验证；/review-loop 判"越界"没有
基准；1200 行的 diff 一次扔过去。缺的是 body 的产物序判据、体量判据、以及把这些编译掉的预门。

## 世界（Σ）

- **PR body 的范围声明是下游的基准**：/review-loop 判"越界类"评论对照它；/pr-review 判 B 档
  "公共 API 变更"对照它。写得越具体，后面判定越省力。
- **AC → 证据映射是 A 档验收的输入**：每条 mechanical AC 对应一个可复现的证据（测试名 + 命令 +
  结果、或 evaluation_result 路径）；human AC 标 `judge: <角色>` 等 G3。
- **证据会随分支增长而失效**：`git diff --stat <首个卡提交>^..HEAD -- <目录>` 这类**开放端点**的
  原始命令，写下时为真，此后任何**非卡的提交**落在首个卡提交之后就让它变假——同一条命令，同样的
  断言，第二天再跑结果不同（dogfood 2026-09-06，I-79：两条修复提交把"空"变成 5 files / 11 insertions）。
  "某类提交没碰某些目录"的承重证据是**卡范围的回放仪器**（按卡的 commit 列表逐个 replay，如
  `dogfood/ring-audit/replay_card_commits.sh` 的 `card_commits_touching_audited_dirs`），它只看卡的提交，
  分支后续怎么长都不改变结论。原始 diff 只能当补充，且必须钉死两端 + 标记录时刻。
- **体量**（按 diff 行数）：XS < 50 · S < 200 · M < 500 · L < 1000 · XL ≥ 1000。L 建议拆，
  **XL 必拆**（按卡 / 按目录 / 先重构后功能）——long-context 下 review 质量崩，这是经验事实不是偏好。
- **push 不可逆、PR 公开**：push 之前该确认的都在预检里；PR 建了之后改 body 可以，但已通知的
  reviewer 已经读过第一版。
- **Draft 的语义**：还想再改 / B 档有告警 / 等 CI 结果 → draft；`--draft` 或预门 flags 非空时默认 draft。
- **base 分支**：`git config branch.<b>.merge` → `gh repo view --json defaultBranchRef` → 问用户。
- **关于用户的 Σ**："提上去" = push + 建 PR；"先别通知人" = draft；"顺手合了" ≠ 本 skill 合——
  merge 是人类动作。

## 判据（φ）

- **预检**（拒）：当前分支 ≠ base；`git status` 干净；与 `origin/<base>` 无落后（有则 merge——
  **不 rebase 已推送分支**）；范围内每条**非 merge** commit 消息合规（Conventional Commits）；自检绿
  （入口推断同 /commit）或 body 注明 `untested`。merge 提交的主题由 git 生成，而"落后就 merge"正是
  本预检自己的要求——把它按 Conventional Commits 判拒等于照做就过不了（I-74）；按 parent 数放行，
  非 merge 提交照判不误。
- **插件版本同步**（拒）：范围 diff 触及 `plugins/<p>/skills/**` 而 `plugins/<p>/.claude-plugin/plugin.json`
  的 version 未变（或 `marketplace.json` 与它不一致）→ 拒（`--no-version-sync` 显式豁免）。
  PR 范围看得见整个交付，版本 bump 就该在里面；插件缓存按版本号取目录，不 bump 的修复等于没发。
- **body 段落**（拒）：Summary / Scope（do / dont）/ Linked issue（`Closes #N` 或 `Refs #N`）/
  Changes / Verification（至少一条命令或测试证据）/ Acceptance mapping（有 `--done-when` 时每条
  mechanical AC 都出现）/ Risk & rollback / Reviewer focus。
- **Verification 里的证据形态**：命令要么**两端钉死**（`<sha>^..<记录时的 sha>`，并注明记录时刻），
  要么用**卡范围的回放仪器**——以 `..HEAD` 收尾的原始 diff 不能承载"某些提交没碰某些目录"这种
  否定断言（见 Σ / I-79）。断言在 PR 正文里必须**此刻仍为真**，不是记录当时为真。
- **体量**：XL → 拒（除 `--allow-xl` 并在 body 写明为什么不能拆）；L → flag。
- **锁**（`--lock` 或 `.done_when.lock` 存在）：范围 diff 触及锁文件且无变更提案 → 拒。
- **标题**：`type(scope): subject` 同 commit 规则（≤ 72）。
- **预审**（`--pre-review`）：建 PR 前用**新上下文**的 `agents/pr-reviewer.md`（跨供应商优先；同源则标 single-vendor caveat）审
  base..head 的 diff，最多 `--rounds`（默认 2）轮"修复 → 再审"——业界数据：自审 2–3 轮后收益见顶，且约减少 1/3 的 review 往返。
  两轮后仍存活的发现**写进 body 的 `## Known issues`**（每条带 file:line），不再迭代，留给人看；A 档 / P0 不许作为 known issue
  出现——修掉它。`verify_pr.py --pre-review` 检该段存在、每条有锚点、无 A 档。预审不替代 reviewer：它减少的是 nit，不是判断。
- 残差：Summary 是否诚实；Reviewer focus 是否指向真正的风险点。

## 原语（Π）

- `scripts/verify_pr.py --body BODY.md [--base main] [--head HEAD] [--title T] [--done-when F]
  [--lock L] [--allow-xl] [--skip-preflight] [--pre-review] [--no-version-sync]` —— exit 0 过 / 1 拒 /
  2 IO；输出 size_class。**建 PR 前必须跑**。
- `assets/pr_template.md` —— body 形状（含 `## Known issues`，`--pre-review` 时必填）。
- `../../agents/pr-reviewer.md` —— 预审用的只读审查 agent（新上下文；输出 findings.yaml，由你做修复与 Known issues）。
- `references/size-and-split.md` —— 拆分策略、draft 判据、base 推断。
- `gh pr create --title … --body-file … --base … [--draft]`；`gh pr edit` 更新 body。

## 门（γ）

- **给人看先于建**：预门过后展示标题 + body + size_class，确认再 push + create；`--yes` / autopilot 免确认。
  `--dry-run` 不 push 不建。
- **XL 停机**：不建，回报拆分建议（按卡 / 目录），让用户决定。
- **done_when**：预门 exit 0 ∧ 确认 ∧ PR 已建 ∧ 回报 PR# / URL / size_class / draft 与否（`--pre-review` 时另报预审轮数与存活发现数）；
  在 /ai-dlc 里 `aidlc_state.py set pr.number=N pr.url=… pr.size_class=… [pr.pre_review_rounds=k]`。

## 失败机制

- 落后 base → `git merge origin/<base>`（不 rebase）；git 生成的 merge 主题**不需要**改写成
  Conventional Commits，预检按 parent 数放行它。merge 冲突 → 停，回报冲突文件，交人（不自动解决语义冲突）。
- push 被拒（non-fast-forward）→ `git pull --no-rebase` 后重推；再拒 → 交人。
- gh 建 PR 403（fork / 无权限）→ 落盘 body 到 `.aidlc/<slug>/pr-body.md`，给出手动链接。
- 预门拒 body 段落 → 补段落，不删段落标题。
- 已有同分支 PR → `gh pr edit` 更新 body，不建第二个。

## 高危黑名单（不可豁免）

- **绝不 force-push**；绝不 rebase 已推送分支。
- **绝不合并 / approve** 自己的 PR——人类动作。
- **绝不无确认建 PR**（除 --yes / autopilot）；绝不建 XL PR 而不说明。
- **绝不在 body 里放 secrets / 内部凭证 / 隐藏集内容**（隐藏集对实现 agent 不可见，PR 是公开的）。
- **绝不用 `--fill`** 代替 body。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`verify_pr.py` 在 fixtures 上冒烟（合法 body 0 拒；缺段落 / 无 Closes /
XL / 缺 AC 映射 / 未同步的插件版本 各被拒；merge 提交主题放行而普通坏主题仍拒；体量分级正确）。行为层未跑。
