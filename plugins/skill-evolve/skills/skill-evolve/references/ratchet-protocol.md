# 棘轮协议（Ratchet Protocol）

> 棘轮的核心承诺：**分数只能涨，不能跌**。不是靠克制，是靠 git 强制执行。

---

## 前置条件

启动一轮迭代前必须满足：

1. `git status` 返回 working tree clean（或仅有 `.skill-evolve/` 工作目录的变更）
2. 当前在 git 仓库内（`git rev-parse --is-inside-work-tree` == true）
3. `experiments.tsv` 已存在（首次运行时由 baseline 阶段创建）
4. 上一轮的基线 commit hash 已知

如果有未提交的与目标 skill 无关的变更，**先暂停**询问用户：是否 stash？是否中止？

---

## 一轮的 git 操作流（必须严格按序）

```bash
# T0：锁定基线快照
git add <SKILL.md path> <skill-evolve workspace>
git commit -m "experiment: round-N baseline before mutation" --allow-empty

# T1：执行 mutation（用 Edit 工具，不 commit）
# ... Edit operations ...

# T2：复评（spawn 独立 subagent，等返回 JSON）
# ... evaluation ...

# T3：根据复评结果决策
# 见下方决策表
```

---

## 决策表（Strict）

| Δ total | 任一维度下降？ | 决策 | git 操作 |
|---------|---------------|------|----------|
| > 0 | 否 | **KEEP** | `git add . && git commit -m "evolve: <change> (+N pts: <old>→<new>) [dim: <dim>]"` |
| > 0 | 是（且非用户已确认的牺牲） | **REVERT** | `git checkout -- <SKILL.md path>` 然后日志记录"局部回退" |
| == 0 | 否 + 至少一弱维提升 | **KEEP**（横向重平衡） | 同 KEEP，commit message 注明 `(rebalance)` |
| == 0 | 是 | **REVERT** | 同上 |
| < 0 | 任意 | **REVERT** | 同上 |
| 评分崩溃 / subagent 失败 | — | **SKIP** | `git checkout -- <SKILL.md path>`，experiments.tsv 标记 SKIP |

**永远不要 `git revert HEAD`**（那会创建反向 commit），用 `git checkout -- <file>` 直接丢弃工作区改动。基线 commit 仍在 history 里供后续诊断。

---

## experiments.tsv 行格式（必填）

每轮一行，tab 分隔：

```
round  timestamp  total_old  total_new  delta  dim_old_lowest  dim_new_lowest  hypothesis  decision  commit_hash
```

字段说明：
- `round`：从 1 开始递增
- `timestamp`：ISO 8601
- `total_old` / `total_new`：本轮改动前后总分
- `delta`：新-旧
- `dim_old_lowest`：本轮改动前最弱维度名
- `dim_new_lowest`：复评后最弱维度名（用于看是否真的修好了）
- `hypothesis`：「如果 X 改成 Y，则 dim 应 +N」一句话
- `decision`：KEEP / REVERT / SKIP
- `commit_hash`：KEEP 时是 evolve commit hash，REVERT/SKIP 时是 baseline experiment commit hash

---

## 收敛与终止

```python
# 伪代码：终止条件检查（每轮 T3 之后执行）
def should_stop(history, target=90, max_rounds=15, plateau=3):
    last = history[-1]
    if last.total >= target:
        return True, "TARGET_REACHED"
    if len(history) >= max_rounds:
        return True, "MAX_ROUNDS"
    if len(history) >= plateau:
        recent_keeps = [h for h in history[-plateau:] if h.decision == "KEEP"]
        if not recent_keeps:
            return True, "CONVERGED"  # 连续 plateau 轮无 KEEP
    return False, None
```

终止后立即生成 `final-report.md`，**不要**再做任何 mutation。

---

## 防退化的隐性约束

棘轮表面是「保留涨分」，深层是「保护已有价值」。三条隐性约束：

1. **不删除已有的好东西**：mutate 时如果删了一段已经被打高分的内容（如 KEEP 历史中明确表扬过的段落），即使总分小涨也要 REVERT
2. **不破坏 frontmatter**：`name` / `version` / `description` 字段被改动需用户确认；`when_to_use` / `Triggers` 改动正常
3. **不引入未声明的依赖**：mutate 不能要求 SKILL.md 依赖外部 MCP / 文件 / agent，除非该依赖已在 plugin.json 或现有 skill 中存在

任何隐性约束被触发都视为 REVERT，且记录到 experiments.tsv 的 `decision` 列为 `REVERT(constraint)`。

---

## 故障恢复

如果 skill-evolve 自身中断（用户 Ctrl-C / 进程崩溃 / token 耗尽）：

1. 重启时先读 `experiments.tsv` 最后一行
2. `git log --oneline | head -20` 检查最近 commit 是否与 tsv 最后一行匹配
3. 不匹配 → 用户工作区可能脏，**停下**问用户：保留还是丢弃
4. 匹配 → 直接进入下一轮 Phase 1

**永远不要在恢复时假设状态**。问比猜便宜。
