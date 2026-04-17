# [项目名] — Ratchet 实验协议

<!--
生成指南（生成后删除此注释块）：
- 所有 [方括号] 内容必须替换为具体值
- 评估方式必须独立于 subagent：要么是独立脚本,要么是独立评估 subagent
- frozen_files 中的所有文件必须在 CANNOT 段列出
- done_when 三个条件必须都有具体数值
- subagent_prompt 段是给执行 subagent 的,不包含评估细节
-->

## Goal

[一句话描述最终目标]

## Criteria

### P0 (Must — 全部通过才算成功)

1. [具体的可机器验证条件]
2. [具体的可机器验证条件]
3. [具体的可机器验证条件]

### P1 (Should — 尽量满足)

1. [条件]
2. [条件]

### P2 (Could — 时间够就做)

1. [条件]

### Invariants (永远不能破坏)

- [不变量,如"所有现有测试必须继续通过"]
- [不变量,如"不得引入新依赖"]
- [不变量,如"内存使用不超过 512MB"]

## done_when

```yaml
success: "所有 P0 criteria 通过 AND 所有 invariant 保持"
convergence: "连续 [N] 轮 best_score 无改善"
budget: "总轮次 >= [M] 或总时间 >= [T 小时]"
```

## Milestones

```
M1: [描述] — P0 criteria 子集: [#1, #2]
M2: [描述] — P0 criteria 子集: [#3] + P1 [#1]
M3: [描述] — 全部 P0 + P1
```

前一个 milestone 未过不允许跳到下一个。

## Scope

### CAN (subagent 可以做的)

- [具体操作,如"修改 src/ 下的所有文件"]
- [具体操作,如"添加新文件"]
- [具体操作,如"安装必要的依赖"]

### CANNOT (subagent 不能做的)

- 不得修改评估脚本 `evaluate.sh`
- 不得修改评估标准 `evaluate_criteria.md`
- 不得修改测试数据 `test_data/`
- 不得修改 `results.tsv` 已有记录
- 不得删除或跳过已有测试
- [其他项目特定禁令]

### Anti-Cheat (写入 subagent prompt 的 inoculation)

不许用以下任何手段通过评估：
- 修改测试文件或评估脚本
- 硬编码测试输入的期望输出
- try/except 吞掉异常
- sys.exit(0) 伪造退出码
- monkey-patch 计时器或评估函数
- 注释或 skip 测试用例
- 从 git log 或调用栈中偷取答案

## 评估方式

<!--
选择一种,删除另一种。

模式 A: 独立评估脚本(硬指标,首选)
模式 B: 独立评估 subagent(二值分解,当无硬指标时)
-->

### 模式 A: 独立评估脚本

**evaluate.sh** (master 在独立上下文中执行,subagent 不可见):

```bash
#!/bin/bash
set -euo pipefail

# ── P0 Criteria ──
[评估命令 1]
[评估命令 2]
[评估命令 3]

# ── Invariants ──
[不变量检查命令]

# ── 汇总 ──
echo "SCORE=$score PASS=$pass FAIL=$fail MILESTONE=$milestone"
```

### 模式 B: 独立评估 subagent

**evaluate_criteria.md** (frozen,subagent 不可修改):

```markdown
对产物逐条判断：
1. [是/否问题 — 过"陌生人测试"]
2. [是/否问题]
3. [是/否问题]
...
```

**评估 subagent prompt**:

```
你是独立评估者。你不知道执行者是谁、做了什么决策。
你只看最终产物,严格按标准判断。

读取:
1. [靶标文件路径]
2. evaluate_criteria.md
3. test_data/ 下的测试场景

逐条输出 PASS/FAIL + 一句话理由。
最后输出: SCORE=X.XX PASS=N FAIL=M MILESTONE=Mx
```

## Setup

1. 进入实验目录:
   ```bash
   mkdir -p [实验目录] && cd [实验目录]
   git init && git add -A && git commit -m "init: ratchet baseline"
   ```
2. 初始化实验记录:
   ```bash
   echo -e "round\tscore\tpass\tfail\tmilestone\tstale_count\tbest\ttimestamp" > results.tsv
   ```
3. 运行基线评估,记录 round=0

## subagent_prompt

<!--
这段是给执行 subagent 的 prompt。
注意: 不包含评估脚本的具体内容、criteria 的判断逻辑、done_when 的阈值。
-->

```
你是一个软件工程师,你的唯一目标是:

[Goal 描述]

你可以修改:
[CAN 列表]

你不能修改:
[CANNOT 列表]

防作弊条款:
[Anti-Cheat 列表]

当前进度:
- 当前 Milestone: [Mx]
- 最佳评分: [best_score]
- 上一轮反馈: [master 提供的简要反馈]
- 实验历史(最近 10 轮):
[results.tsv 最近 10 行]

Milestones:
[Milestone 列表,标注当前位置]

工作方式:
1. 先读取文件系统中已有的代码/产物,理解当前状态
2. 基于上一轮反馈和历史,制定本轮改进计划
3. 每次只改一个方面
4. 改完后 commit: git add -A && git commit -m "r[N]: [改了什么]"
5. 持续工作直到你认为当前 milestone 的所有条件都满足

你不需要自己评估是否通过——会有独立的评估者来判断。
专注于把事情做好就行。
```

## Master 执行逻辑

```
round = 0
best_score = 0
stale_count = 0

LOOP:
  启动 subagent(prompt = subagent_prompt,填入当前进度)
  等待 subagent 返回

  round += 1
  执行评估 → score, pass, fail, milestone
  追加 results.tsv

  if done_when.success 满足:
    git tag "final-success"
    输出成功报告 → 停止

  if score > best_score:
    best_score = score
    stale_count = 0
    git tag "best-r{round}"
  else:
    stale_count += 1

  if stale_count >= [convergence_limit]:
    git checkout "best-r{上次 best 的 round}"
    输出收敛报告 → 停止

  if round >= [budget_limit]:
    git checkout "best-r{上次 best 的 round}"
    输出预算报告 → 停止

  准备 failure_summary:
    "本轮评分 {score},未通过的 criteria: {fail_list},
     当前 milestone: {milestone},建议方向: {suggestion}"

  → 回到 LOOP(用 failure_summary 更新 subagent_prompt)
```
