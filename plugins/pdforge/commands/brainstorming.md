---
description: 启动需求澄清对话。需求模糊、新功能设计、复杂问题探索时使用。
argument-hint: <idea-description>
---

## Mission

通过苏格拉底式问答澄清需求，产出结构化的设计文档。

## Usage

```bash
# 简短想法
/brainstorm "给 app 加个用户认证"

# 详细描述
/brainstorm "我们需要一个支持 OAuth2 和 JWT 的认证系统，企业客户要求 SOC2 合规"

# 从文件读取
/brainstorm @docs/ideas/payment-v2.txt
```

## Behavior

1. 激活 `brainstorming` skill
2. 执行 6 阶段流程：
   - 阶段 1：侦察（静默分析代码库）
   - 阶段 2：发散探索（2-3 个方案）
   - 阶段 3：提问（每次一个问题）
   - 阶段 4：收敛呈现（分块 200-300 字）
   - 阶段 5：文档（保存 design-doc）
   - 阶段 6：交接（指引下一步）
3. 保存设计文档到 `docs/designs/YYYY-MM-DD-<topic>.md`

## Output

- 设计文档：`docs/designs/YYYY-MM-DD-<topic>.md`
- 包含：问题定义、需求澄清记录、推荐方案、否决方案、风险、范围边界、成功指标

## Next Steps

澄清完成后：

```bash
# 生成 PRD
/prd docs/designs/<file>.md

# 或全流程自动化
/pdforge --from-design docs/designs/<file>.md
```

## When to Use

| 场景 | 使用 /brainstorm? |
|------|------------------|
| 需求模糊，需要探索 | ✅ 是 |
| 新功能设计 | ✅ 是 |
| 多种可能方案需要权衡 | ✅ 是 |
| 需求已经很清晰 | ❌ 直接用 /prd |
| 有现成的需求文档 | ❌ 直接用 /prd |

## Anti-Patterns

🚫 不要在 brainstorming 完成后直接写代码
🚫 不要跳过 PRD 生成阶段
🚫 不要一次问多个问题
🚫 不要一次性输出完整设计