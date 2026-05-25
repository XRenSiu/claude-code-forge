# Forge Skill Validation Protocol

本文件是 /goal 验证流程的完整协议，goal condition 只引用本文件。

## Reference Brief (Worker 输入)
"用户能取消订阅，但已支付当月仍可访问"

## 文件命名约定
- iter-{N}-step{M}-attempt-{K}-output.md     ← Worker 产出
- iter-{N}-step{M}-attempt-{K}-issues.md     ← Auditor 产出
- iter-{N}-step{M}-attempt-{K}-patches.md    ← Fixer 产出
- iter-log.md                                ← 主控总日志
- issues-summary.md                          ← 累计 ACCEPTED 的 P1/P2

N = 完整轮次，M = Step 编号 (本次只跑 1 和 2)，K = attempt 计数。
所有文件都放在 specs/forge-skill-validation/。

## Step 范围 (acceptance-fleet 本轮不验证)

Step 1: 验证 /acceptance-spec
  输入: Reference Brief
  期望产出: specs/<feature>/{proposal.md, spec.md, tasks.md,
           done_when.yaml, spec-robustness.md}

Step 2: 验证 /test-suite-generator
  输入: Step 1 产出的 specs/<feature>/ 目录
  期望产出: tests/<feature>/{existence.sh, unit/, integration/,
           e2e/, mutation.sh, fitness/}

## 每个 Step 的执行流程

### [1] 派 Worker subagent (Opus)
完整 prompt：

> 你的任务是在当前项目里执行 /acceptance-spec (Step 1) 或
> /test-suite-generator (Step 2) 这个 skill，处理输入：
> [Step 1: Reference Brief 字符串 / Step 2: Step 1 产出的目录]
>
> 严格按 skill 内部定义的流程跑。不要补全 skill 没做好的部分，
> 不要"帮忙"生成 skill 漏掉的内容，不要替 skill 决策。
> skill 输出什么就保留什么。
>
> 把 skill 的完整产出保留在原本输出位置。另外写运行日志到
> iter-{N}-step{M}-attempt-{K}-output.md，内容包括：
> - 调用的 skill 命令
> - skill 的完整对话日志（含每一轮 clarify）
> - 产出文件路径列表
> - 每个产出文件的完整内容（cat 出来贴进 log）
>
> 严禁阅读 FLOW.md，你不需要知道"应该长什么样"。

### [2] 派 Auditor subagent (Opus)
完整 prompt：

> 你是独立审查员。读两份文件：
> 1. FLOW.md (权威 spec)
> 2. iter-{N}-step{M}-attempt-{K}-output.md (worker 产出归档)
>
> 对照 FLOW.md 中关于本 Step 对应 skill 的所有要求逐项检查。
> 任何偏差按 P0/P1/P2 分级记录到
> iter-{N}-step{M}-attempt-{K}-issues.md。
>
> P0 阻断 (skill 违反 FLOW.md 明确写出的硬性约束)：
>
> Step 1 / acceptance-spec:
> - 未产出 5 份文件之一 (proposal/spec/tasks/done_when/
>   spec-robustness)
> - spec.md 中的 REQ 缺失 source: 字段
> - clarify 循环超过 5 轮硬上限
> - clarify 中问了非"歧义/缺失边界/未定义术语"三类之外的问题
>   (如技术栈、性能指标等实现细节)
> - done_when.yaml 添加了 Appendix C 不允许的字段 (v1 strict)
> - spec-robustness.md 缺四节中的任一节
>   (closed_vectors/surfaced_vectors/accepted_risks/verifier_hints)
> - 没跑 S2.5 反作弊扫描
>
> Step 2 / test-suite-generator:
> - 缺 6 batch 中的任一个
>   (existence/unit/integration/e2e/mutation/fitness)
> - unit batch 缺 PBT 部分 (Hypothesis 或 fast-check 都没用)
> - integration batch 使用 mock 而非 testcontainers
> - 一次性出全部 batch 而不是分批
>
> P1 质量 (动作做了但做得不到位)：
> - EARS 句式合法但选择不合理
> - PBT 属性过于浅层
> - existence 检查只覆盖部分名词指代
> - clarify 问题质量低
>
> P2 风格 (主观偏好不一致)：
> - 文件命名风格、注释详细程度、排版等
>
> 严禁：试图修复、给 worker 善意解释、自己脑补 FLOW.md 没说的
> "应该的样子"、跨 Step 提建议。你只负责按字面挑刺。

### [3] 主控读 issues 文件，判断分支

分支 A (阻塞: 存在 P0，或 P1 > 3)：
  → 派 Fixer subagent (Opus)，prompt 见下
  → Fixer 完成后检查 patches.md：
     - 含 NEEDS_DESIGN_REVIEW → 停机
     - 否则继续
  → attempt K += 1，回到 [1] 重跑当前 Step
  → 绝对不准进入下一 Step

分支 B (通过: 无 P0 且 P1 ≤ 3)：
  → 不派 Fixer
  → P1/P2 追加到 issues-summary.md 标记 ACCEPTED
  → iter-log.md 追加 "Step {M} CLEARED (attempt {K},
    P0=0, P1=x accepted, P2=y accepted)"
  → 进入 Step M+1

分支 C (attempt {K=5} 仍阻塞)：
  → iter-log.md 追加 "Step {M} STUCK after 5 attempts"
  → 停止整个 /goal，等人介入

### Fixer subagent prompt (Opus)

> 读 issues 文件中所有 P0/P1/P2 条目，全部一起修。
> 只能改 skills/acceptance-spec/** 和
> skills/test-suite-generator/** 内部文件。
>
> 重要约束 — 你只能加约束不能删约束：
> - 可以新增指令、检查项、产出要求
> - 可以加严现有约束 (建议 → 必须)
> - 不能删除现有指令、检查项、产出要求
> - 不能放宽现有约束 (必须 → 建议)
> - 不能删除 FLOW.md 提到的任何机制
> 如果某条 issue 根因是"skill 的某个约束本身有问题"，
> 不要删该约束。把判断写进 patches.md 并标记
> NEEDS_DESIGN_REVIEW，等人介入。
>
> 不能修改 FLOW.md、issues.md、worker 的产出归档。
>
> 修完写 patches.md，逐条说明：
> - 这条 issue 是什么
> - 改了哪个文件的哪几行
> - 改的是加约束还是其他形式
> - 是否触发 NEEDS_DESIGN_REVIEW
> 文件路径: iter-{N}-step{M}-attempt-{K}-patches.md

## 强制约束 (违反任一直接终止)

- 主控自己不许执行 skill 命令，必须派 Worker
- 主控自己不许审查 worker 产出，必须派 Auditor
- 主控自己不许改 skill 源码，必须派 Fixer
- 每个 subagent 派发后，主控必须 cat 其产出文件让 evaluator
  看到完整证据 (不许只 cat 末尾或 head)
- 单 Step attempt 上限 5
- 当前 Step 阻塞时绝对不准进入下一 Step
- Fixer patches.md 含 NEEDS_DESIGN_REVIEW 必须停机
- 不能修改 /goal condition、FLOW.md、不能软化 issues 分级
- 所有 subagent 必须使用 Opus
- 本次只覆盖 Step 1-2，不要尝试验证 /acceptance-fleet
