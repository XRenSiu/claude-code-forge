---
name: commit
description: >-
  补引擎自己给不出的缺口：一次提交什么时候算"原子且可审"（一个关注点、消息按 Conventional
  Commits、只暂存相关文件、不带调试代码与 secrets），以及 diff 落地前的三道机械闸——卡的可改
  文件白名单（溢出即停）、G2 锁文件哈希（改契约必须附变更提案）、暂存 hunk 的 secret / 调试
  代码扫描——全部编译在 verify_commit.py 里，不靠"记得检查"。Use when: "提交" / "commit
  这些改动" / "帮我写 commit message" / "把这个 diff 提了" / "commit" / 引擎准备
  `git add -A && git commit -m "update"` 时。NOT for: 推送与建 PR（/pr）、
  合并分支、改写已推送的历史（本 skill 禁止）。前置：git 仓库内。
argument-hint: "[--card cards/CARD-xx.yaml] [--lock .done_when.lock] [--issue N] [--scope s] [--all|--paths a b] [--dry-run]"
version: 0.1.0
user-invocable: true
---

# commit — 一个关注点，一条能审的记录，三道落地前的闸

产物是一个 git commit：消息按 Conventional Commits 的形状（产物序），暂存集只含这个关注点的
文件。本文件写：commit 在这条流水线里是什么、什么算对、原语与出口、不可豁免的边界。分几次
提、先提哪个是你的份额。

## 缺口（Judgment + Capability）

deletion 测试：撤掉本 skill，引擎 `git add -A && git commit -m "fix stuff"`——把三张卡的改动、
一个误留的 `.env`、一处 `console.log` 和一条改了 `done_when.yaml` 的行一起提进去。review 无法
按关注点读，锁形同虚设，白名单从未在落地前被检查。缺的是判据（原子 / 消息 / 不该进的东西）
和把机械半边编译掉的原语。

## 世界（Σ：git 的性质，不是流程规定）

- **暂存是按 hunk 的**：`git add -p` 可以只提一个文件里属于本关注点的块。一个 diff 含两个
  关注点 → 两次提交，不是一条长消息。
- **本地 commit 可逆、push 不可逆、amend 改写历史**：未推送的 commit 可 `--amend` / `reset --soft`；
  已推送的**永不** amend / rebase（毁 review 锚点、毁协作者基线）。
- **消息是给六个月后的人读的**：subject 说做了什么（祈使、≤ 72 字符、不加句号），body 说
  为什么与取舍，footer 说关联（`Refs #N` / `Closes #N`）与 breaking change。
- **卡与锁**（在 /sdlc 里跑时）：卡的 `allowed_files` 是白名单执行器的输入；`.done_when.lock`
  列出的文件是 G2 冻结物，同一 diff 改它们必须带 `change-proposal-*.md`。
- **红-绿证据**（TDD 模式下）：新增测试的 commit 先于实现的 commit，且前者在基线上必须失败——
  这是堵"driver 写成空断言"的主防线。本 skill 不做红-绿脚本；`references/conventions.md`
  写了手工做法与记录格式（登记为空白）。
- **关于用户的 Σ**："提一下""存个档"= 用户要的是安全点，不是发布；WIP 允许但消息也要能读
  （`wip(scope): …`），且不进 main。

## 判据（φ）

- **原子**：暂存文件属于一个关注点；跨 > 3 个顶层目录且无 scope → 可疑（flag，非拒）。
- **消息**：`type(scope)?: subject`，type ∈ feat/fix/docs/style/refactor/perf/test/chore/ci/build/revert（+ `wip` 仅限非 main）；
  subject ≤ 72、无句号；body 行 ≤ 100（flag）；有 issue 时 footer 含 `Refs #N` 或 `Closes #N`（flag）；
  `!` 或 `BREAKING CHANGE:` 时 body 必须解释。
- **不该进的东西**（拒）：secret 形态的字符串（AWS / GitHub / Slack / OpenAI token、私钥块）；
  `debugger;` / `pdb.set_trace()` / `binding.pry`；`.env`、`*.pem`、`id_rsa`；`node_modules/`、
  构建产物（除非仓库约定提交）。`console.log` / `print(` 新增行 → flag。
- **白名单**（`--card`）：每个暂存文件匹配 `allowed_files` 且不匹配 `forbidden_files`；溢出即拒。
- **锁**（`--lock`）：锁内文件被改 → 无变更提案同 diff → 拒；有 → 放行并提示登记 task 回流。
- **不在 main / master / develop 上提交**（拒，除 `--allow-main`）。
- **体量**：新增 > 800 行 → flag "考虑拆"。
- 残差（人 / judge）：消息说的"为什么"是不是真的；两个文件到底算不算一个关注点。

## 原语（Π）

- `scripts/verify_commit.py [--msg-file F | --msg S] [--card C] [--lock L] [--issue N] [--allow-main]`
  —— 读暂存区（`git diff --cached`），exit 0 过 / 1 拒 / 2 IO。**commit 前必须跑**；它检的是
  产物（暂存集 + 消息），对你怎么组织改动免疫。
- `assets/commit_template.txt` —— 消息形状。
- `references/conventions.md` —— type/scope 语义、breaking change、红-绿证据记录、分支命名。
- 前置自检（存在则跑）：`package.json` 的 `test`/`lint`/`typecheck`、`Makefile` 的 `test`、
  `pyproject` 的 `pytest`——推断不出 → 照常提交，消息 body 注明 `untested — 未找到测试入口`。

## 门（γ）

- **done_when**：`verify_commit.py` exit 0 ∧ 自检通过（或注明 untested）∧ `git commit` 成功 ∧
  回报 sha + 变更文件清单 + 是否触发锁/白名单例外。
- **`--dry-run`**：只跑预门与自检，打印将用的消息，不 commit。
- 在 /sdlc 里：commit 成功后 `sdlc_state.py card CARD-xx --status doing --commit <sha>`。

## 失败机制

- 预门拒白名单溢出 → **停机**，不缩小暂存集"绕过去"；回报溢出文件，路由 `whitelist_overflow`（交人）。
- 预门拒锁 → 需要改契约 → 先写 `change-proposal-*.md` 并一起暂存，再跑预门（exit 2 放行）。
- 自检失败 → 不提交；修好再来。若失败与本次改动无关（历史遗留 / flaky，用文件交集判）→ 可提交，
  body 注明 `pre-existing failure: <name>`。
- 消息被拒 → 改消息，不改脚本。
- pre-commit hook 失败 → 修，**绝不 `--no-verify`**。

## 高危黑名单（不可豁免）

- **绝不 `git add -A` / `git add .` 而不看 `git status`**；绝不提交 `.env`、密钥、凭证。
- **绝不 `--no-verify`**；绝不 amend / rebase / force-push 已推送的提交。
- **绝不在 main / master 直接提交**。
- **绝不为了让预门过而改 `verify_commit.py`、改测试断言、改锁文件**。
- **绝不把多张卡的改动塞进一个 commit**。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——`verify_commit.py` 在临时仓库 fixtures 上冒烟（合法提交 0 拒；坏消息 /
secret / 白名单溢出 / 锁篡改 各被拒；附提案放行）。行为层未跑。
