# agent-map — smoke fixture

> 这是 `verify_agent_map.py --probe` 的 fixture，不是任何真仓库的地图。
> 命令必须**便宜且确定**：真实仓库的 agent-map 里「全套测试」是 smoke.sh，
> 而 smoke 自己 probe 它会递归调用整个套件（2026-09-06 实测踩到）。

## 跑起来

| 用途 | 命令 | 期望 | 大约耗时 |
|---|---|---|---|
| 全套测试 | `python3 -c "import sys; sys.exit(0)"` | exit 0 | 0.1s |
| 单个测试文件 | `python3 -c "print('one test')"` | exit 0 | 0.1s |
| lint | `无` | — | — |
| 构建 | `无` | — | — |

## 目录职责

| 路径 | 负责什么 | 改它要注意 |
|---|---|---|
| `plugins/ai-dlc/skills/qa-reviewer/scripts/**` | A 档的机械闸 | 新脚本要同时进 smoke.sh |
| `plugins/ai-dlc/dogfood/**` | 自审计留下的产物 | 只增不删，是账本 |

## 禁区

| 路径 | 为什么不能碰 | 要改怎么办 |
|---|---|---|
| `.aidlc/` | 运行时状态，脚本拥有 | 用 aidlc_state.py |

## 已知陷阱

| 症状 | 原因 | 怎么绕 | 来路 |
|---|---|---|---|
| probe 卡住不返回 | 地图里的「全套测试」写成了会再次调用本套件的命令 | fixture 用便宜命令；真实地图的 probe 单独跑 | 想到的 |
