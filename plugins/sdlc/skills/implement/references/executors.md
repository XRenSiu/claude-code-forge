# 执行器与隔离检查表

| 执行器 | 何时 | 接法 | 隔离检查 |
|---|---|---|---|
| self | 单卡、上下文小 | 当前会话只读 `assets/card_context.md` 形状的输入 | 会话里已有评审输出？→ 先归档/清理，或改用 agent |
| agent | 默认 | `Agent(subagent_type=general-purpose, prompt=card_context + agents/card-implementer.md)` | prompt 不含评审判据 / 隐藏集 / 其他卡 |
| ratchet | 需迭代到达标（性能 / 差分测试） | `/ratchet` 以卡的 AC 为 P0，`budget = card.budget.retries`，`frozen_files = forbidden_files + lock` | worker 看不到 evaluate.sh；evaluate 引用已校准标准 |
| forge-teams | 多卡并行 | `/parallel-implementation`（邻居），卡的 allowed_files = 文件所有权 | 各实现者互不读对方卡；quality-sentinel 的发现只给 lead |

## 隔离检查表（任一不满足不启动）

- [ ] 输入只含卡 + 状态摘要 + AC 子集 + 红基线
- [ ] 评审 skill 的提示词 / findings 不在输入里
- [ ] 隐藏变体集不在实现者可读路径
- [ ] tests/**、契约、锁在 forbidden_files
- [ ] 执行器不能改 `verify_commit.py` / `sdlc_state.py`
