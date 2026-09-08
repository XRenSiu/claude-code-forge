# 触发绑定：环的"等待"交给原生原语，"谓词"仍是 pr-poll.sh

`pr-poll.sh watch` 的 bash sleep 不是唯一的等待方式。Claude Code 有四个原生原语；本环的终止谓词
（`done` / `round` / `strike`）与去重（水位线）不变，只是由谁把你叫醒可以换。总表在 `../../ai-dlc/assets/triggers.yaml`。

| 场景 | 绑定 | 备注 |
|---|---|---|
| 交互式，想省 token | `bash pr-poll.sh watch <PR> 45 480`（Bash timeout ≥ 600000ms） | 原路径；等待期间零 token |
| 交互式，不想长阻塞 | `/loop 5m bash <skill_dir>/scripts/pr-poll.sh snapshot <PR>` | 每拍 exit 20 直接等下一拍；exit 0 按 SKILL.md 裁决 |
| 无人值守 | `/goal` 条件见下 | 独立小模型每轮判 Met / Not yet / Impossible |
| headless / 跨 session | `/schedule` 一条 routine 每 30 分钟 `claude -p "/review-loop <PR>"` | 水位线与计数器在 `.aidlc/pr-watch` 延续 |

## /goal 条件怎么写

评估者**只读 transcript，不跑命令、不读文件**——条件里引用的每个退出码都必须被你回显到对话：

```
/goal bash <skill_dir>/scripts/pr-poll.sh done <PR> 已回显 exit 0 或 exit 10；
或存在 REJECT 悬而未决且我已汇报"合法不收敛"（exit 20）；or stop after 10 turns
```

- `or stop after N turns`：N = MAX_ROUNDS（loops.yaml#review_loop.stop.budget.rounds）。
- 评估者判 **Impossible** 的情形：所有剩余线程都是 REJECT / ESCALATE / strike 冻结——这就是 SKILL.md 说的"合法不收敛"，
  循环该停，不该为了凑 exit 0 去 resolve 未达成一致的线程。
- 后台命令未结束时 /goal 延迟评估（30 分钟起 check-in）；`watch` 是前台阻塞，不触发这条。

## 早停判据（SKILL.md 判据段的补充）

连续两次 watch **有活动但零新线程、且所有线程已是终态**（resolved / REJECT 已回帖 / ESCALATE / 冻结）→ 直接调 `done`，
不等 `MAX_EMPTY_WATCHES`。证据日志 `no_new_threads_streak` 记它。理由：agentpatterns convergence-detection——"没有新发现"
是比"没有活动"更早的收敛信号；多等只烧预算。

## 不变的事

- 本 skill `disable-model-invocation: true`——任何绑定都以人显式启动为前提。
- approve / merge / close 是人类动作；任何触发绑定都不能代做。
- `MAX_WAIT` 必须小于 Bash 工具超时——只对 `watch` 路径有意义。
