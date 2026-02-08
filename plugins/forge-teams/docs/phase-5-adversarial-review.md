# 阶段 5：对抗审查 + 红队攻击 (Adversarial Review + Red Team)

> 并行审查 + 红队主动攻击 + 交叉验证，全方位检验代码质量和安全性

---

## 📋 阶段概述

| 维度 | 说明 |
|------|------|
| **目标** | 通过并行审查 + 红队攻击 + 交叉验证，全方位检验代码质量和安全性 |
| **输入** | 已实现的代码（来自阶段4） |
| **输出** | 审查报告（含红队攻击结果） |
| **上游阶段** | 并行实现（阶段4） |
| **下游阶段** | 对抗调试（阶段6）或 交叉验收（阶段7） |

---

## 🧩 组件清单

| 类型 | 名称 | 模型 | 说明 |
|------|------|------|------|
| **Agent** | `red-team-attacker` | opus | 红队攻击者，主动利用漏洞 |
| **Agent** | `review-synthesizer` | opus | 审查综合员，统一判定 |
| **Agent** | `spec-reviewer` (general-purpose) | sonnet | 规格合规审查 |
| **Agent** | `code-reviewer` (general-purpose) | sonnet | 代码质量审查 |
| **Agent** | `security-reviewer` (general-purpose) | sonnet | 安全模式审查 |
| **Skill** | `adversarial-review` | - | Phase 5 编排逻辑 |
| **Rule** | `adversarial-protocol.md` | - | 对抗审查协议 |

```
┌───────────────────────────────────────────────────────────────┐
│                    阶段 5 三阶段流水线                          │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Phase A: 并行审查 (Parallel Review)                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │
│  │spec-       │ │code-       │ │security-   │ │red-team- │  │
│  │reviewer    │ │reviewer    │ │reviewer    │ │attacker  │  │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └────┬─────┘  │
│        │              │              │              │         │
│        ▼              ▼              ▼              ▼         │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              各自产出独立报告                          │    │
│  └──────────────────────┬───────────────────────────────┘    │
│                         │                                     │
│  Phase B: 交叉验证 (Cross-Examination)                        │
│                         ▼                                     │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  审查者之间共享发现、互相验证                          │    │
│  │  red-team exploits → security-reviewer 验证           │    │
│  │  spec gaps → code-reviewer 评估影响                    │    │
│  └──────────────────────┬───────────────────────────────┘    │
│                         │                                     │
│  Phase C: 综合判定 (Synthesis)                                │
│                         ▼                                     │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              review-synthesizer                       │    │
│  │  去重 → 交叉验证评分 → 优先级排序 → 统一判定          │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 💡 为什么这样设计

### pdforge 审查的局限

pdforge uses sequential, passive review:

```
┌─────────────────────────────────────────────────────────────┐
│              pdforge 审查模型局限分析                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  pdforge 流程:                                              │
│  design-reviewer → spec-reviewer → code-reviewer            │
│                                    → security-reviewer      │
│                                                             │
│  局限 1: 顺序瓶颈                                           │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                   │
│  │ spec │→ │ code │→ │ sec  │→ │ done │  Wall time: 4T    │
│  └──────┘  └──────┘  └──────┘  └──────┘                   │
│  每个 reviewer 等待前一个完成                                │
│                                                             │
│  局限 2: 被动发现                                           │
│  Reviewers 检查模式 (pattern matching)                      │
│  不会主动构造攻击输入来验证漏洞                              │
│  报告: "这里可能有风险" vs "这里确实可以被攻击"              │
│                                                             │
│  局限 3: 无交叉验证                                         │
│  Reviewer A 的发现从不被 Reviewer B 验证                    │
│  误报无法被过滤，真正的问题也没有二次确认                    │
│                                                             │
│  局限 4: 无攻击者视角                                       │
│  Security reviewer 从防御者角度检查                         │
│  不具备攻击者思维（如何利用漏洞链？）                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 为什么引入 Red Team

Red Team (red-team-attacker) is **fundamentally different** from Security Reviewer:

| 维度 | Security Reviewer | Red Team Attacker |
|------|------------------|-------------------|
| **方法** | 检查模式（pattern matching） | 尝试攻击（active exploitation） |
| **输出** | "这里可能有 SQL 注入风险" | "我用这个输入成功注入了 SQL" |
| **思维** | 防御者视角 | 攻击者视角 |
| **深度** | 浅扫描（单点检查） | 深度利用链（多步骤攻击路径） |
| **可信度** | 可能是误报 | 已验证的漏洞 |
| **模型** | sonnet（模式匹配足够） | opus（利用链需要深度推理） |

**关键区别**: A security reviewer might say "SQL injection risk at line 42" but a red team attacker actually constructs the malicious input and proves exploitation is possible. This distinction between **"potential vulnerability"** and **"proven exploit"** is crucial for prioritization.

**7 攻击向量**:

| # | 攻击向量 | 利用方法 | 影响 |
|---|---------|---------|------|
| 1 | **SQL Injection** | 构造恶意 SQL 输入 | 数据泄露、数据篡改 |
| 2 | **XSS** | 注入恶意脚本 | Session 劫持、数据窃取 |
| 3 | **Auth Bypass** | 绕过认证/授权逻辑 | 未授权访问 |
| 4 | **IDOR** | 操纵对象引用 | 越权访问其他用户数据 |
| 5 | **Command Injection** | 构造恶意命令输入 | 服务器控制 |
| 6 | **Data Exfiltration** | 通过合法 API 泄露数据 | 敏感信息泄露 |
| 7 | **Race Conditions** | 构造并发请求 | 数据不一致、双重支付 |

**每个攻击向量的 5 步利用流程**:

```
┌─────────────────────────────────────────────────────────────┐
│              Red Team 5 步利用流程 (per vector)               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: RECON (侦察)                                       │
│     扫描代码，识别攻击面 (entry points)                      │
│                                                             │
│  Step 2: ANALYZE (分析)                                     │
│     追踪数据流: input → processing → output                 │
│     识别验证缺失和信任边界                                   │
│                                                             │
│  Step 3: CRAFT (构造)                                       │
│     构造恶意输入 / 攻击载荷 (Proof of Concept)               │
│                                                             │
│  Step 4: EXPLOIT (利用)                                     │
│     模拟执行攻击路径，验证是否可被利用                        │
│                                                             │
│  Step 5: REPORT (报告)                                      │
│     结构化报告: 入口点、追踪链、PoC、影响、修复建议           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 为什么并行 + 交叉验证

**Phase A (Parallel Review)**: All 4 reviewers + red team work simultaneously:

| 对比 | pdforge 顺序 | forge-teams 并行 |
|------|-------------|-----------------|
| 时间 | 4T (顺序执行) | 1T (并行执行) |
| 瓶颈 | 每个等前一个 | 无瓶颈 |
| Token | ~T (顺序分摊) | ~T (同量并行) |

**Phase B (Cross-Examination)**: Reviewers share findings and challenge each other:

```
┌─────────────────────────────────────────────────────────────┐
│              Phase B 交叉验证矩阵                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Red Team exploits                                          │
│    → security-reviewer: 验证攻击是否真实可行                 │
│    → code-reviewer: 评估代码修复影响范围                     │
│                                                             │
│  Spec-reviewer gaps                                         │
│    → code-reviewer: 评估缺失功能的影响                      │
│    → security-reviewer: 检查缺失功能是否引入安全风险         │
│                                                             │
│  Code-reviewer issues                                       │
│    → spec-reviewer: 确认是否为规格要求                       │
│    → red-team: 检查代码问题是否可被利用                      │
│                                                             │
│  Security-reviewer findings                                 │
│    → red-team: 尝试实际利用验证                              │
│    → code-reviewer: 评估修复难度                             │
│                                                             │
│  交叉验证结果:                                               │
│    2+ reviewers 确认 → HIGH confidence                       │
│    1 reviewer only   → MEDIUM confidence                     │
│    Red team proven   → CONFIRMED (最高可信度)                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Phase C (Synthesis)**: Review synthesizer de-duplicates, prioritizes, and produces unified verdict.

---

### 为什么 Review Synthesizer 是独立角色

Without synthesizer:
- Lead must manually read 4-5 separate reports
- De-duplicate same issues reported by multiple reviewers
- Prioritize across different severity scales
- **Error-prone and time-consuming**

With synthesizer:

| Synthesizer 职责 | 说明 |
|-----------------|------|
| **去重** | 同一问题被多个 reviewer 报告 -> 合并为一条 |
| **交叉验证评分** | 2+ reviewers 确认 = higher confidence |
| **统一严重度** | 跨 reviewer 统一 severity ranking |
| **优先级排序** | Tier 1 (Critical) -> Tier 4 (Low) |
| **统一判定** | APPROVE / APPROVE WITH CHANGES / REQUEST CHANGES |

---

### 关键设计决策

| 决策 | 选项 A | 选项 B | 选择 | 原因 |
|------|--------|--------|------|------|
| 审查模式 | 顺序 | 并行 | **并行** | Agent Teams 支持，大幅加速 |
| 红队 | 无 | 有 | **有** | 主动攻击发现被动审查遗漏的漏洞 |
| 交叉验证 | 无 | 有 | **有** | 减少误报，提高发现可信度 |
| Red Team model | sonnet | opus | **opus** | 攻击利用链需要深度推理 |
| Synthesizer | 无 (Lead 做) | 有 | **有** | 专职综合比 Lead 手动合并更可靠 |
| 修复循环 | 无 | 有 (max 3) | **有** | REQUEST CHANGES -> fix -> re-review |
| 前置检查 | 可选 | 必须 | **必须** | build/test/lint 通过才审查 |

---

## 🔧 组件详解

### 1. red-team-attacker Agent

**角色定义**:

```yaml
name: red-team-attacker
model: opus
tools: Read, Grep, Glob, Bash
```

**职责**:
- 7 攻击向量，每个含 5 步利用流程
- 产出结构化攻击报告
- 发现 CRITICAL 漏洞时立即通知 Lead

**攻击报告格式**:

```markdown
## Red Team Attack Report

### Attack Vector: SQL Injection

**Severity**: CRITICAL
**CVSS Estimate**: 9.1
**CWE Reference**: CWE-89

**Entry Point**: `src/api/users.ts:42` — `getUserById(req.params.id)`

**Trace Chain**:
```
req.params.id (user input)
  → getUserById(id)           [no validation]
    → db.query(`SELECT * FROM users WHERE id = ${id}`)  [string interpolation]
      → SQL executed with injected payload
```

**Proof of Concept**:
```bash
# Malicious input
id = "1; DROP TABLE users; --"

# Resulting SQL
SELECT * FROM users WHERE id = 1; DROP TABLE users; --
```

**CIA Impact**:
- Confidentiality: HIGH (can read all user data)
- Integrity: HIGH (can modify/delete data)
- Availability: HIGH (can drop tables)

**Recommended Fix**:
```typescript
// Before (vulnerable)
db.query(`SELECT * FROM users WHERE id = ${id}`)

// After (parameterized)
db.query('SELECT * FROM users WHERE id = $1', [id])
```
```

**CRITICAL 漏洞立即通知协议**:

| 条件 | 动作 |
|------|------|
| CVSS >= 9.0 | 立即通知 Lead，暂停其他审查 |
| 可远程利用 | 立即通知 Lead |
| 数据泄露风险 | 立即通知 Lead |
| 其他 | 正常报告，等待 Phase C 综合 |

---

### 2. review-synthesizer Agent

**角色定义**:

```yaml
name: review-synthesizer
model: opus
tools: Read, Grep, Glob, Bash
```

**职责**:
- 收集所有审查报告 + 红队攻击结果
- 执行去重、交叉验证、优先级排序
- 产出统一判定

**去重规则**:

| 场景 | 规则 | 示例 |
|------|------|------|
| 同一文件同一行 | 合并，取最高严重度 | spec + code 都报 line 42 |
| 同一类型不同位置 | 分别保留 | SQL injection at line 42 and line 87 |
| Red team 确认 | 提升为 CONFIRMED | security says "risk", red team proves it |
| Red team 未确认 | 保持原始评级 | security says "risk", red team can't exploit |

**交叉验证置信度矩阵**:

```
┌─────────────────────────────────────────────────────────────┐
│              交叉验证置信度评分                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONFIRMED (最高)                                           │
│    Red team 实际利用成功                                     │
│    → 必须修复，无可商量                                      │
│                                                             │
│  HIGH CONFIDENCE                                            │
│    2+ reviewers 独立发现同一问题                             │
│    → 强烈建议修复                                           │
│                                                             │
│  MEDIUM CONFIDENCE                                          │
│    1 reviewer 发现，未被其他 reviewer 验证或否定             │
│    → 建议修复                                               │
│                                                             │
│  LOW CONFIDENCE                                             │
│    1 reviewer 发现，其他 reviewer 认为误报                   │
│    → 可选修复                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**优先级排序**:

| Tier | 条件 | 处理 |
|------|------|------|
| **Tier 1 (Critical)** | CONFIRMED exploit OR CVSS >= 9.0 | 必须修复，阻塞发布 |
| **Tier 2 (High)** | HIGH confidence + security/correctness | 强烈建议修复 |
| **Tier 3 (Medium)** | MEDIUM confidence + quality/maintainability | 建议修复 |
| **Tier 4 (Low)** | LOW confidence OR style/suggestion | 可选修复 |

**判定条件**:

| 判定 | 条件 |
|------|------|
| **APPROVE** | 无 Tier 1-2 问题 |
| **APPROVE WITH CHANGES** | 有 Tier 2-3 问题，无 Tier 1 |
| **REQUEST CHANGES** | 有 Tier 1 问题，或 Tier 2 问题 >= 3 个 |

---

### 3. Reviewer Agents (x3, general-purpose)

**spec-reviewer**:

```yaml
name: spec-reviewer
type: general-purpose
model: sonnet
tools: Read, Grep, Glob
```

检查清单:
- PRD 需求 100% 覆盖
- 验收标准全部满足
- API 契约匹配规格
- 无未指定的行为

**code-reviewer**:

```yaml
name: code-reviewer
type: general-purpose
model: sonnet
tools: Read, Grep, Glob, Bash
```

审查维度:

| 维度 | 检查 | 优先级 |
|------|------|--------|
| 正确性 | 逻辑是否正确 | CRITICAL |
| 清晰性 | 凌晨 3 点能读懂吗 | HIGH |
| 错误处理 | 异常路径覆盖 | HIGH |
| 类型安全 | TypeScript 严格模式 | MEDIUM |
| 可维护性 | 6 个月后能改吗 | MEDIUM |

**security-reviewer**:

```yaml
name: security-reviewer
type: general-purpose
model: sonnet
tools: Read, Grep, Glob, Bash
```

基于 OWASP Top 10 检查:
- 注入攻击、认证失效、敏感数据暴露
- XSS、访问控制、安全配置
- 不安全反序列化、已知漏洞组件

---

### 4. adversarial-review Skill

**编排流程**:

| 步骤 | 名称 | 说明 |
|------|------|------|
| Step 0 | **Pre-check** | 运行 build + test + lint，必须全部通过 |
| Step 1 | **Phase A: Parallel Review** | 5 agents 并行审查 |
| Step 2 | **Phase B: Cross-Examination** | 审查者间共享发现、互相验证 |
| Step 3 | **Phase C: Synthesis** | review-synthesizer 统一判定 |
| Step 4 | **Fix Cycle** | REQUEST CHANGES -> 修复 -> 范围限定重审 (max 3) |
| Step 5 | **Final Verdict** | 最终判定 + 报告输出 |

**修复循环 (Fix Cycle) 详解**:

```
┌─────────────────────────────────────────────────────────────┐
│              修复循环 (最多 3 轮)                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Round 1:                                                   │
│    Verdict: REQUEST CHANGES (5 issues)                      │
│    → Fix all 5 issues                                       │
│    → Scoped re-review (only changed files + related)        │
│                                                             │
│  Round 2:                                                   │
│    Verdict: APPROVE WITH CHANGES (2 remaining)              │
│    → Fix 2 issues                                           │
│    → Scoped re-review                                       │
│                                                             │
│  Round 3:                                                   │
│    Verdict: APPROVE                                         │
│    → Done, proceed to P6/P7                                 │
│                                                             │
│  如果 3 轮后仍 REQUEST CHANGES:                              │
│    → 断路器触发，需要人工干预                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Scoped Re-review（范围限定重审）**:

| 重审范围 | 说明 |
|---------|------|
| 修改的文件 | 直接修改的文件必须重审 |
| 相关文件 | import/依赖修改文件的代码 |
| 不重审 | 未受影响的文件 |

这比全量重审节省大量 token，同时确保修复不引入新问题。

---

## 🚀 使用流程

### 标准用法

```bash
# 完整审查（含红队）
/forge-teams --phase 5

# 不使用红队（省 token）
/forge-teams --phase 5 --no-red-team

# 自定义修复循环轮数
/forge-teams --phase 5 --max-fix-rounds 2
```

### Token 预算估算

| 配置 | 审查 agents | Token 倍数 (vs pdforge) | 适用场景 |
|------|-----------|----------------------|---------|
| `--no-red-team` | 3 reviewers + synthesizer | ~1.2x | Token 敏感场景 |
| 默认 | 3 reviewers + red team + synthesizer | ~1.5x | 标准场景 |
| `--deep-red-team` | 同上 + 额外攻击向量 | ~2.0x | 高安全要求 |

---

## ⚙️ vs pdforge 对比

| 维度 | pdforge (3-stage review) | forge-teams (P5) | 增量价值 |
|------|-------------------------|------------------|---------|
| 执行模式 | 顺序 4 阶段 | 并行 5 角色 | 更快 (1T vs 4T) |
| 安全检测 | 被动 pattern 检查 | 红队主动攻击 | 发现更多真实漏洞 |
| 验证方式 | 无交叉验证 | Phase B 交叉验证 | 减少误报，提高可信度 |
| 报告输出 | 各自独立报告 | 统一综合判定 | 更清晰的决策 |
| 修复循环 | `/accept --fix --loop` | Scoped re-review (max 3) | 更精确的重审范围 |
| Token 开销 | 中 | 高 (~1.5x) | 质量显著提升 |

### 何时用 pdforge 审查就够了

| 条件 | 推荐 | 原因 |
|------|------|------|
| 内部工具 | pdforge | 安全要求低 |
| 简单 CRUD | pdforge | 攻击面小 |
| Token 预算紧 | pdforge | P5 开销 ~1.5x |
| 面向用户的产品 | forge-teams P5 | 需要红队验证 |
| 处理支付/PII | forge-teams P5 | 安全是硬需求 |
| 合规要求 (SOC2, etc.) | forge-teams P5 | 需要攻击验证记录 |

---

## ⚠️ 注意事项

### 硬约束

1. **Red Team 需要 opus**: 攻击利用链需要深度推理能力，sonnet 无法有效构造多步骤攻击路径
2. **前置检查必须通过**: build/test/lint 必须全部通过才能开始审查，否则审查结果不可靠
3. **修复循环最多 3 轮**: REQUEST CHANGES 触发 fix -> 范围限定重审 -> 最多 3 轮，超过触发断路器
4. **Red Team 不修改代码**: 只报告攻击路径和 PoC，不实施修复，保持攻击者角色纯粹

### 反模式清单

| 反模式 | 问题 | 正确做法 |
|--------|------|---------|
| 跳过前置检查 | 审查构建失败的代码 | build + test + lint 必须先通过 |
| Red Team 用 sonnet | 攻击利用链质量低 | 使用 opus 进行深度推理 |
| 跳过交叉验证 (Phase B) | 误报率高 | 必须执行交叉验证 |
| Lead 手动综合报告 | 效率低、易遗漏 | 使用 review-synthesizer |
| 全量重审修复 | Token 浪费 | 使用 scoped re-review |
| 忽略 CONFIRMED 漏洞 | 已验证的安全问题 | CONFIRMED = 必须修复 |
| 修复循环超过 3 轮 | 进入死循环 | 3 轮后触发断路器，人工干预 |
| Red Team 修改代码 | 角色混淆 | Red Team 只攻击不修复 |

### 前置检查清单

在启动阶段 5 之前，确保:

- [ ] `npm run build` 或等效命令通过
- [ ] `npm test` 全部通过
- [ ] `npm run lint` 无 error
- [ ] 阶段 4 所有任务标记为 DONE
- [ ] Quality Sentinel 无未解决的 CRITICAL/HIGH 问题

---

## 🔗 下一阶段

根据审查结果:

```
┌─────────────────────────────────────────────────────────────┐
│              审查结果 → 下一步                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  APPROVE                                                    │
│    → 跳过阶段 6，直接进入 阶段 7：交叉验收                   │
│    /forge-teams --phase 7                                   │
│                                                             │
│  APPROVE WITH CHANGES                                       │
│    → 修复 Tier 2-3 问题 → 范围限定重审                       │
│    → 通过后进入 阶段 7                                       │
│                                                             │
│  REQUEST CHANGES                                            │
│    → 进入 阶段 6：对抗调试                                   │
│    /forge-teams --phase 6                                   │
│                                                             │
│  REQUEST CHANGES (3 轮后仍未通过)                            │
│    → 断路器触发，需要人工干预                                │
│    → 审查架构决策是否需要回退到阶段 2                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
