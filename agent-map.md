# agent-map — claude-code-forge

> 给一个没有任何上下文的实现者的四个答案：怎么跑测试、怎么构建、哪个目录管什么、哪里不能碰。
> 由 `/dos-extract` 维护，`plugins/ai-dlc/skills/dos-extract/scripts/verify_agent_map.py --probe` 检
> （命令逐条实跑）。每条"已知陷阱"指向一次真实失败，没有来路的条目不进这张表。
>
> **作用域是整个 claude-code-forge，不是某一个插件**——「目录职责」里的 `plugins/<name>/` 对 12 个
> 插件都成立，「禁区」有一半在 `~/.claude/` 与别人的工作树上，「陷阱」里两条来自 CLAUDE.md、一条
> 来自 `/humanize`。「跑起来」几乎全是 `plugins/ai-dlc/` 的路径，是因为它的 `smoke.sh` 就是**全仓**
> 的冒烟入口（见下表），不是因为这份地图属于那个插件。
>
> 与 `dos.yaml` 的区别正在这里：本体一个 bounded context 一份（所以在 `plugins/ai-dlc/dos.yaml`），
> 地图是「这个**仓库**怎么干活」一份。真要加一份 package 级的地图，注意 `repo_assets.py` 的候选序
> 是**更具体的赢**：`plugins/<pkg>/agent-map.md` 会盖住这一份，而地图的内容是可加的——它会报一条
> `遮蔽` 告警提醒你把两边合起来，别让仓库级的禁区悄悄消失。

## 跑起来

| 用途 | 命令 | 期望 | 大约耗时 |
|---|---|---|---|
| 全套测试 | `bash plugins/ai-dlc/eval/smoke.sh` | exit 0，末行 `0 failed` | ~5min |
| 全套测试（快，跳过嵌套变异自检） | `SMOKE_NESTED=1 bash plugins/ai-dlc/eval/smoke.sh` | exit 0，末行 `0 failed` | ~90s |
| 单个 skill 的脚本 | `python3 plugins/ai-dlc/skills/ai-dlc/scripts/aidlc_state.py graph check` | exit 0 | 1s |
| 结构闸自检 | `python3 plugins/ai-dlc/skills/qa-reviewer/scripts/verify_structure.py --done-when plugins/ai-dlc/skills/qa-reviewer/fixtures/structure-clean.yaml --repo plugins/ai-dlc/skills/qa-reviewer/fixtures/repo --out /dev/null` | exit 0 | 1s |
| 文风闸 | `python3 plugins/humanize/skills/humanize/scripts/humanlint.py README.md` | 见输出，exit 1 = 有 flag | 1s |
| lint | `无` | — | — |
| 类型检查 | `无` | — | — |
| 构建 | `无`（插件是数据，没有构建产物） | — | — |

## 目录职责

| 路径 | 负责什么 | 改它要注意 |
|---|---|---|
| `.claude-plugin/marketplace.json` | 市场注册表：每个插件的版本与描述 | 版本必须与 `plugins/<name>/.claude-plugin/plugin.json` 同步，两处都改 |
| `plugins/<name>/skills/<skill>/SKILL.md` | 一个 skill 的全部判据；frontmatter 的 `name` 决定斜杠命令名 | 改内容就要 bump 三处版本（skill / plugin / marketplace） |
| `plugins/<name>/skills/<skill>/scripts/` | 该 skill 的机械预门；检产物不检过程 | 新脚本必须同时在 `plugins/ai-dlc/eval/smoke.sh` 里加期望，否则没人知道它坏了 |
| `plugins/<name>/skills/<skill>/eval/gate.json` | 该 skill 的证据档：跑过什么、残留什么 | 只降不升：没有行为层对比就不许写 verified（dos.yaml R017） |
| `plugins/ai-dlc/dogfood/` | 用 AI-DLC 审自己留下的产物 | 只增不删，是账本不是草稿 |
| `plugins/ai-dlc/eval/smoke.sh` | 全仓脚本的冒烟期望，一个文件 | 加期望时同时加一条"变异证明"：故意改坏一处，确认它真的红 |

## 禁区

| 路径 | 为什么不能碰 | 要改怎么办 |
|---|---|---|
| `.aidlc/` | 运行时状态，脚本拥有；手改会让状态机与账本对不上 | 用 `aidlc_state.py` 的子命令 |
| `~/.claude/settings.json`、`~/.claude/plugins/` | 用户级本机配置，不入 git；一个 session 改了别的 session 不知道 | 由人执行；agent 只提示 |
| 别的 session 正在改的分支与工作树 | 这个仓库常有并行 session；`commit --amend` 会吞掉别人的 commit | 只提交自己的 hunk；要改共享分支先发消息 |
| `plugins/*/skills/*/eval/gate.json` 的档位字段 | 档位是证据的结论，不是意愿 | 先跑出证据再改档位 |

## 已知陷阱

| 症状 | 原因 | 怎么绕 | 来路 |
|---|---|---|---|
| `aidlc_state.py --root X init` 报 `invalid choice` | `--root` / `--slug` 挂在子解析器上，不是顶层；必须写在子命令**后面** | `aidlc_state.py init --root X --slug Y` | `file:plugins/ai-dlc/skills/ai-dlc/scripts/aidlc_state.py#L966` |
| 新插件装好了但 `/命令` 报 Unknown skill | marketplace 注册只完成一半：还要 `~/.claude/settings.json` 的 `enabledPlugins`，以及 `~/.claude/plugins/cache/` 里有对应版本目录 | 按 CLAUDE.md「新建插件的额外步骤」第 4–6 项做完，然后**重启 session**（skill 列表在启动时定型） | `file:CLAUDE.md` |
| 让 `/humanize` 改一份研究报告，回来变成 40 段密实散文 | 它默认按方案体裁改，判据里列表占比、标题密度都是扣分项 | 报告 / README 用 `--genre report --keep-structure`，骨架由 `structdiff.py` 守住 | `file:plugins/humanize/skills/humanize/eval/report.md` |
| 改完 skill 忘了 bump 版本，别人拉下来行为不一致 | 版本有三处（skill frontmatter / plugin.json / marketplace.json），漏一处就不同步 | 三处一起改，版本 bump 单独一个 commit | `file:CLAUDE.md` |
