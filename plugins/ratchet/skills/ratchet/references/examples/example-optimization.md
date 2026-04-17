# Prompt 质量优化 — Ratchet 实验协议

> 模式 B(独立评估 subagent) + 二值分解 + 反向约束示例
> 适用于无硬指标的主观质量优化场景

## Goal

优化客服系统的 system prompt,使其在 20 个真实用户场景中
通过率达到 90% 以上。

## Criteria

### P0 (Must)

1. 全部 20 个场景的综合 pass_rate ≥ 0.90
2. 每条评估标准的单项通过率 ≥ 0.70（不能靠某几条拉高均值）

### P1 (Should)

1. pass_rate ≥ 0.95
2. prompt 长度不超过 1500 字符

### Invariants

- prompt 长度不超过基线的 1.5 倍
- prompt 不得包含任何测试场景的具体内容（防过拟合）

## done_when

```yaml
success: "pass_rate >= 0.90 AND 每条标准单项 ≥ 0.70 AND invariant 全保持"
convergence: "连续 8 轮 best_score 无改善"
budget: "总轮次 >= 40"
```

## Milestones

```
M1 Baseline:   能输出 pass_rate 数字,记录基线
M2 Core:       pass_rate ≥ 0.60
M3 Solid:      pass_rate ≥ 0.80 AND 每条标准 ≥ 0.50
M4 Target:     pass_rate ≥ 0.90 AND 每条标准 ≥ 0.70
```

## Scope

### CAN
- 重写 prompts/customer_support.md 的任何部分
- 调整 prompt 结构(示例、角色设定、约束等)
- 尝试不同的 prompt 工程技术

### CANNOT
- 不得修改 evaluate_criteria.md
- 不得修改 test_data/scenarios.jsonl
- 不得修改 results.tsv 已有记录
- 不得在 prompt 中引用测试场景的具体内容

### Anti-Cheat
- 不许在 prompt 中硬编码场景 ID 或用户原文
- 不许把评估标准原文复制进 prompt(可以体现精神但不能逐字照搬)
- 不许删除或注释评估标准

## 评估方式: 模式 B（独立评估 subagent）

**evaluate_criteria.md** (frozen):

```markdown
对每个用户场景,判断 prompt 是否足够指导 AI 产出满足以下标准的回复：

1. 是否能直接回答用户的具体问题(非泛泛建议)?
2. 是否包含至少一个可操作的下一步?
3. 是否有机制避免编造(不确定时说明会确认)?
4. 语气是否友好且专业(无居高临下或过度道歉)?
5. 是否针对用户的具体情况而非套模板?
6. 回复长度是否合理(不过短敷衍也不过长啰嗦)?
```

**评估 subagent prompt**:

```
你是一个独立的 prompt 质量评估者。
你不知道这个 prompt 是谁写的、经过了几轮修改、修改了什么。
你只看 prompt 本身和测试场景,严格按标准判断。

执行以下步骤：

1. 读取 prompts/customer_support.md 全文
2. 读取 evaluate_criteria.md 全文
3. 对 test_data/scenarios.jsonl 中的每个场景:
   a. 读取 user_query
   b. 想象一个 AI 使用这个 prompt 处理这个查询
   c. 逐条过 6 个标准,输出 PASS 或 FAIL + 一句话理由
   d. 计算该场景通过率

4. 汇总:
   - 总 pass_rate = 总 PASS / (场景数 × 标准数)
   - 每条标准的单项通过率
   - prompt_length = 文件字符数

输出格式:
--- 场景: [ID] ---
标准 1: PASS — [理由]
标准 2: FAIL — [理由]
...

=== 汇总 ===
SCORE=[pass_rate] PASS=[n] FAIL=[m] MILESTONE=[Mx]
per_criterion: [c1=0.85, c2=0.70, c3=0.90, c4=0.95, c5=0.75, c6=0.80]
prompt_length: [chars]
min_criterion: [最低的那条标准的通过率]
```

**Master 的评估流程**:

1. 启动评估 subagent(上述 prompt)
2. 解析返回的 SCORE 和 per_criterion
3. 检查 invariant:
   - prompt_length ≤ baseline × 1.5?
   - prompt 内容不含 scenarios.jsonl 中的原文?(grep 检查)
4. 综合判断: SCORE ≥ 0.90 AND min_criterion ≥ 0.70 AND invariant 全过 → done

## Setup

1. 创建实验目录并初始化
2. 将 prompts/customer_support.md 复制到实验目录
3. 将 evaluate_criteria.md 和 test_data/ 写入实验目录(frozen)
4. 初始化 results.tsv
5. 运行基线评估(启动评估 subagent)

## subagent_prompt

```
你是一个 prompt 工程师。你的唯一目标是：

优化 prompts/customer_support.md 这个客服系统 prompt,
使其在真实用户场景中表现更好。

你可以修改: prompts/customer_support.md
你不能修改: evaluate_criteria.md, test_data/, results.tsv

防作弊: 不许在 prompt 中硬编码测试场景内容、不许照搬评估标准原文

当前进度:
- 当前 Milestone: {milestone}
- 最佳评分: {best_score}
- 上一轮反馈: {failure_summary}
- 实验历史: {last_10_rows}

工作方式:
1. 读取当前 prompt 和上一轮反馈
2. 针对反馈中提到的弱项,制定本轮改进假设
3. 每次只改一个方面
4. 改完 commit
5. 你不需要自己评估——有独立评估者判断
```
