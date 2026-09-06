# agent-map — claude-code-forge

> 给一个没有任何上下文的实现者的四个答案：怎么跑测试、怎么构建、哪个目录管什么、哪里不能碰。
> 由 `/dos-extract` 维护，`plugins/sdlc/skills/dos-extract/scripts/verify_agent_map.py --probe` 检
> （命令逐条实跑）。每条"已知陷阱"指向一次真实失败，没有来路的条目不进这张表。

## 跑起来

| 用途 | 命令 | 期望 | 大约耗时 |
|---|---|---|---|
| 全套测试 | `bash plugins/sdlc/eval/smoke.sh` | exit 0，末行 `0 failed` | 100s |
| 单个 skill 的脚本 | `python3 plugins/sdlc/skills/sdlc/scripts/sdlc_state.py graph check` | exit 0 | 1s |
| 结构闸自检 | `python3 plugins/sdlc/skills/qa-reviewer/scripts/verify_structure.py --done-when plugins/sdlc/skills/qa-reviewer/fixtures/structure-clean.yaml --repo plugins/sdlc/skills/qa-reviewer/fixtures/repo --out /dev/null` | exit 0 | 1s |
| 文风闸 | `python3 plugins/humanize/skills/humanize/scripts/humanlint.py README.md` | 见输出，exit 1 = 有 flag | 1s |
| lint | `无` | — | — |
| 类型检查 | `无` | — | — |
| 构建 | `无`（插件是数据，没有构建产物） | — | — |

## 目录职责

| 路径 | 负责什么 | 改它要注意 |
|---|---|---|
| `.claude-plugin/marketplace.json` | 市场注册表：每个插件的版本与描述 | 版本必须与 `plugins/<name>/.claude-plugin/plugin.json` 同步，两处都改 |
| `plugins/<name>/skills/<skill>/SKILL.md` | 一个 skill 的全部判据；frontmatter 的 `name` 决定斜杠命令名 | 改内容就要 bump 三处版本（skill / plugin / marketplace） |
| `plugins/<name>/skills/<skill>/scripts/` | 该 skill 的机械预门；检产物不检过程 | 新脚本必须同时在 `plugins/sdlc/eval/smoke.sh` 里加期望，否则没人知道它坏了 |
| `plugins/<name>/skills/<skill>/eval/gate.json` | 该 skill 的证据档：跑过什么、残留什么 | 只降不升：没有行为层对比就不许写 verified（dos.yaml R017） |
| `plugins/sdlc/dogfood/` | 用 sdlc 审自己留下的产物 | 只增不删，是账本不是草稿 |
| `plugins/sdlc/eval/smoke.sh` | 全仓脚本的冒烟期望，一个文件 | 加期望时同时加一条"变异证明"：故意改坏一处，确认它真的红 |

## 禁区

| 路径 | 为什么不能碰 | 要改怎么办 |
|---|---|---|
| `.sdlc/` | 运行时状态，脚本拥有；手改会让状态机与账本对不上 | 用 `sdlc_state.py` 的子命令 |
| `~/.claude/settings.json`、`~/.claude/plugins/` | 用户级本机配置，不入 git；一个 session 改了别的 session 不知道 | 由人执行；agent 只提示 |
| 别的 session 正在改的分支与工作树 | 这个仓库常有并行 session；`commit --amend` 会吞掉别人的 commit | 只提交自己的 hunk；要改共享分支先发消息 |
| `plugins/*/skills/*/eval/gate.json` 的档位字段 | 档位是证据的结论，不是意愿 | 先跑出证据再改档位 |

## 已知陷阱

| 症状 | 原因 | 怎么绕 | 来路 |
|---|---|---|---|
| `sdlc_state.py --root X init` 报 `invalid choice` | `--root` / `--slug` 挂在子解析器上，不是顶层；必须写在子命令**后面** | `sdlc_state.py init --root X --slug Y` | `file:plugins/sdlc/skills/sdlc/scripts/sdlc_state.py#L966` |
| 新插件装好了但 `/命令` 报 Unknown skill | marketplace 注册只完成一半：还要 `~/.claude/settings.json` 的 `enabledPlugins`，以及 `~/.claude/plugins/cache/` 里有对应版本目录 | 按 CLAUDE.md「新建插件的额外步骤」第 4–6 项做完，然后**重启 session**（skill 列表在启动时定型） | `file:CLAUDE.md` |
| 让 `/humanize` 改一份研究报告，回来变成 40 段密实散文 | 它默认按方案体裁改，判据里列表占比、标题密度都是扣分项 | 报告 / README 用 `--genre report --keep-structure`，骨架由 `structdiff.py` 守住 | `file:plugins/humanize/skills/humanize/eval/report.md` |
| 改完 skill 忘了 bump 版本，别人拉下来行为不一致 | 版本有三处（skill frontmatter / plugin.json / marketplace.json），漏一处就不同步 | 三处一起改，版本 bump 单独一个 commit | `file:CLAUDE.md` |
