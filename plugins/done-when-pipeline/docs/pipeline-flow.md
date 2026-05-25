# Pipeline Flow — v0.3.0 全流程

本文档画清 done-when-pipeline 三个 skill (`/acceptance-spec` → `/test-suite-generator` → `/acceptance-fleet`) 串起来的端到端流程，包括每个阶段的输入/输出、子步骤、关键约束、以及两个最容易踩坑的 boundary。

辅助文档：
- `README.md` — 快速上手 + 设计哲学
- `INTEGRATION.md` — 跟 `/ratchet` 等外部 skill 的 hand-off 细节
- `skills/<skill>/SKILL.md` — 单个 skill 的完整规格
- `skills/acceptance-fleet/references/` — fleet 内部协议（角色 prompt / finding schema / 隔离层级 / 反作弊 pattern / 留痕格式 / fix-prompt 模板 / meta-judge 协议）

---

## 全景图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1-3                                                                    │
│  /acceptance-spec  "用户能取消订阅,但保留到付费期结束"                          │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │   S0 Bootstrap   读 brief,定 feature-slug
         │   S1 Draft       NL → EARS,每个模糊处打 [?] tag
         │   S2 Clarify     3 类问题、2-3 轮、≤5 轮硬上限
         │   S2.5 反作弊    "如果我要 game 这个 done_when 我会怎么 game?"
         │                  → 扫 6 类 RHD pattern,close/document/accept 每一项
         │   S3 Solidify    写 5 份文件
         ▼
    specs/<feature>/
      ├── proposal.md           Why / What / Non-goals
      ├── spec.md               EARS REQ-001..NNN,每条带 source: 行
      ├── tasks.md              拆解任务
      ├── done_when.yaml        v1 strict 契约(Appendix C 不可加字段)
      └── spec-robustness.md    ★v0.3.0 新★ 反作弊伴生文件
                                · closed_vectors   (S2.5 已结构性堵掉)
                                · surfaced_vectors (堵不掉,acceptance-fleet 监控)
                                · accepted_risks   (识别但故意不防)
                                · verifier_hints   (域特定提醒)

┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 4                                                                      │
│  /test-suite-generator  specs/<feature>/                                     │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │   4-A existence    ripgrep/tree-sitter 检查
         │   4-B unit         example + PBT (Hypothesis/fast-check)
         │   4-C integration  testcontainers,不许 mock
         │   4-D e2e          Playwright/Cypress
         │   4-E mutation     mutmut/Stryker (反 reward-hacking)
         │   4-F fitness      rubric 文件(留给 fresh Claude session 手判)
         │   每个 batch 一次跑完不混 — 不一次性出全部
         ▼
    tests/<feature>/
      ├── existence.sh
      ├── unit/
      ├── integration/
      ├── e2e/
      ├── mutation.sh
      └── fitness/

┌─────────────────────────────────────────────────────────────────────────────┐
│  实现阶段(任意 agent / 任意人)                                                │
│  ★必须用 fresh session★ — 不能让实现 agent 看见下一步的评估 prompt          │
│  (看到了 = 作弊温床,acceptance-fleet 会拒绝同 session 跑)                    │
└─────────────────────────────────────────────────────────────────────────────┘
         │  写代码进 src/
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 5-6 (推荐路径)                                                          │
│  /acceptance-fleet  specs/<feature>/                                         │
└─────────────────────────────────────────────────────────────────────────────┘

         ┌─ S0 Bootstrap ──────────────────────────────────────────────┐
         │ • 验证 5 份输入齐备                                          │
         │ • 检测可用 evaluator:                                        │
         │     codex CLI?  → 强隔离(跨厂商)                            │
         │     仅 Claude?  → 中等隔离(Haiku+Sonnet+Opus 混尺寸)        │
         │     单模型?     → 弱隔离 + 警告                             │
         │     无法分会话? → 拒绝运行                                   │
         │ • 写 ratchet-log/iteration-NNN/isolation.json               │
         └─────────────────────────────────────────────────────────────┘
                                       │
         ┌─ S1 Fleet 并行 spawn 8 角色 (互不通气) ────────────────────┐
         │                                                              │
         │  程序性层 (Haiku — 跑数字,不做 LLM 判断)                     │
         │    ├─ test-runner         跑 4-A..4-E 测试                  │
         │    └─ existence-checker   核 existence: 条目                │
         │                                                              │
         │  语义层 (Opus + 工具)                                        │
         │    ├─ requirement-tracer  Agent-as-Judge:每条 REQ          │
         │    │                      LOCATE/READ/RETRIEVE 找证据       │
         │    │                      4 态:fully/partially/not/         │
         │    │                      requires_human_verification       │
         │    └─ design-reviewer     检查实现是否符合 spec 意图         │
         │                                                              │
         │  对抗层 (跨厂商优先)                                          │
         │    ├─ adversarial-reviewer  ★Codex/Gemini★ — "假设这代码  │
         │    │                        引发了线上事故,找原因.找不到   │
         │    │                        = 你失败"                       │
         │    └─ edge-case-hunter    边界/竞态/异常路径系统扫描       │
         │                                                              │
         │  行为层 (Opus + Playwright)                                  │
         │    └─ e2e-explorer        在真浏览器里像用户一样走流程     │
         │                                                              │
         │  反作弊层 (Opus + git_diff)                                  │
         │    └─ spec-gaming-detector 读 spec-robustness.md 监控点 +   │
         │                          扫 6 类 RHD pattern (absolute +    │
         │                          diff 模式),算 gaming_risk_score   │
         │                                                              │
         │  每个角色写一份 fleet-outputs/<role>.yaml,统一 schema       │
         └─────────────────────────────────────────────────────────────┘
                                       │
         ┌─ S2 Rebuttal Pass (4-Eyes Principle) ──────────────────────┐
         │ 每条 finding 路由给另一个角色尝试反驳                         │
         │ 反驳成功 → 移入 rebutted_findings(不删,留审计)              │
         │ 反驳失败 → 进 S3                                            │
         │ 只跑一轮 — 多轮就退化成辩论                                 │
         └─────────────────────────────────────────────────────────────┘
                                       │
         ┌─ S3 Meta-Judge (只合成,绝不重审代码) ──────────────────────┐
         │ 1. Dedupe        同 file:line + 同 root_cause 合并          │
         │ 2. Weight        多源 + 跨厂商 → confidence +;              │
         │                  单源 + 单厂商 → confidence -               │
         │ 3. Arbitrate     冲突看证据强度,不看票数;无法决 → NEEDS_HUMAN│
         │ 4. Classify      对照 done_when.thresholds 出 state         │
         │                                                              │
         │ ★硬墙★ 不读 src/,不形成自己的代码判断 — 一旦越界就退化成   │
         │       又一个有 bias 的 reviewer                              │
         └─────────────────────────────────────────────────────────────┘
                                       │
         ┌─ S4 Ratchet 四态 + 一个逃逸阀 ─────────────────────────────┐
         │                                                              │
         │  ① DONE          所有阈值过 + gaming_risk < 3                │
         │                  → 归档,任务完成                            │
         │                                                              │
         │  ② FIX           部分过,findings 明确                       │
         │                  → 生成 fix-prompt.md(不带评估角色名/分数/  │
         │                    pattern 名 — 信息隔离)                   │
         │                  → 用户喂回 fresh impl session → 再跑 N+1   │
         │                                                              │
         │  ③ SPEC_DRIFT    PBT 反驳与 REQ 字面一致地连续命中 N 轮     │
         │                  → ★不修代码★ → 回 /acceptance-spec        │
         │                                                              │
         │  ④ GAMING_RISK   gaming_risk_score ≥ 7,或趋势单调上升       │
         │                  → ★不修代码★ → 回 /acceptance-spec        │
         │                                                              │
         │  ⑤ NEEDS_HUMAN   meta-judge 拒绝独断(冲突无法仲裁/UI 题)    │
         │                  → 暂停问用户,得答案后重回 S3              │
         └─────────────────────────────────────────────────────────────┘
                                       │
         ┌─ S5 Persist (永远跑) ──────────────────────────────────────┐
         │ ratchet-log/iteration-NNN/                                  │
         │   ├── timestamp.txt                                          │
         │   ├── isolation.json                                         │
         │   ├── input-manifest.json   (5 份输入 sha256)                │
         │   ├── impl-snapshot.txt     (本轮代码快照)                   │
         │   ├── impl-diff.patch       (vs 上一轮)                      │
         │   ├── fleet-outputs/*.yaml  (8 个角色)                       │
         │   ├── rebuttals/*.yaml                                       │
         │   ├── meta-judge-output.yaml                                 │
         │   ├── final-state.json                                       │
         │   └── <state>.md            (fix-prompt / spec-drift /       │
         │                              gaming-risk / needs-human)      │
         │ + ratchet-log/summary.json (整 feature 历史)                 │
         │ + ratchet-log/findings-history.jsonl                         │
         └─────────────────────────────────────────────────────────────┘

         典型收敛:2-4 轮(四态机制让 spec-drift / gaming 不在 FIX 死循环)
         每轮成本:~$0.75 ;整 feature ~$2-3
```

---

## 两个关键 boundary，必须记住

### 1. 实现 → acceptance-fleet 之间必须换 session

不是软建议。`/acceptance-fleet` 在 S0 检测如果是同 session 会直接 refuse 运行。

原因：fix-prompt 故意**不告诉**实现 agent
- 哪个评估角色发现的（"adversarial-reviewer 找到..." 不出现）
- gaming_risk_score 多少（"我们盯着 coverage_gaming pattern" 不出现）
- 在防哪类 RHD pattern（"再这么改我会标 P0" 不出现）

只给 `file:line + 简短描述 + 建议改法 + REQ-ID`。

一旦 session 共享，这些被隐藏的信息从对话历史里全部泄露，实现 agent 就能从"修代码"切到"绕过评估"——整套反作弊瞬间废掉。

这也是为什么 `evaluation-isolation-levels.md` 把 Level 0（同 session）单独标为 **FORBIDDEN**，最低接受是 Level 2 Medium（混尺寸 Claude）。

### 2. SPEC_DRIFT / GAMING_RISK 决不修代码

这两态 `/acceptance-fleet` 直接调头把控制权送回 `/acceptance-spec`。

- **SPEC_DRIFT**：PBT 反例与 REQ 字面文本一致地连续命中 N 轮（默认 N=3，来自 `spec_drift_threshold.max_fix_loops_before_escalation`）。代码改了好几轮，反例还是踩同样的字。结论：spec 本身有歧义/漏洞，再修代码就是糊墙。
- **GAMING_RISK**：`gaming_risk_score ≥ 7`，或者趋势单调上升（2 → 3 → 5 → 7...）。代码在"满足契约的字面"和"达成需求的精神"之间越走越偏。结论：契约本身有可被 game 的洞，要回 `/acceptance-spec` S2.5 重新扫一遍 RHD pattern、加 surfaced_vectors / 改 REQ 措辞。

这两态对应的报告（`spec-drift-report.md` / `gaming-risk-report.md`）都包含"应该回头问的具体 REQ + 具体 done_when.yaml 字段建议"，方便用户重启 /acceptance-spec 时直接当 narrow brief 用。

---

## 单 skill 最小用法（独立使用）

三个 skill 都可以单独用，不必走完整 pipeline。

### 只用 /acceptance-spec
当你只想把一段模糊需求结构化成 EARS + 可验收契约，但不打算自动跑测试：
```
/acceptance-spec "用户能取消订阅..."
```
拿到 5 份文件后人工写测试 / 直接喂 PR 描述 / 交给其他工具消费都行。

### 只用 /test-suite-generator
当你已经有 `specs/<feature>/` 目录（来自任何渠道，不一定是 acceptance-spec 生成的）想派生测试金字塔：
```
/test-suite-generator specs/<feature>/
```
对 `done_when.yaml` 的 schema 要求是 v1 strict（Appendix C），其他字段可以缺。

### 只用 /acceptance-fleet
当你拿到别人写好的实现 + spec + done_when.yaml，只想跑一轮多 agent 验收看看：
```
/acceptance-fleet specs/<feature>/
```
注意：`spec-robustness.md` 缺失不会 refuse，但 spec-gaming-detector 会进入"最大怀疑模式"，并在输出里标 "spec-robustness.md absent — verifier ran in max-suspicion mode"。建议先补一轮 `/acceptance-spec` 把 S2.5 跑出来。

---

## Legacy 路径（不推荐但保留）

如果环境里没装 Codex/Gemini、feature 又简单、不想付多 agent 的成本，可以跳过 `/acceptance-fleet` 直接用 `/ratchet`：

```
/acceptance-spec ...
/test-suite-generator specs/<feature>/
/ratchet  <用 INTEGRATION.md 的 Goal/Criteria/Scope 配方翻译 done_when.yaml>
```

代价：
- ❌ 没有 spec-gaming-detector，反作弊只剩 mutation testing 一层
- ❌ 没有四态 ratchet，spec_drift_threshold 只能被翻译成 `convergence` 让 ratchet 停下来，"是 spec 错还是 code 错"由你手动判
- ❌ 没有跨厂商对抗，Claude 写代码 Claude 自己审，sycophancy 没被打断
- ❌ 没有 ratchet-log/ 审计 trail

适合：
- 单文件 bug fix 这种 1-2 步就收敛的小活儿
- 个人项目环境，没装 Codex CLI / Gemini CLI 也不想配
- 学习阶段，想先把 pipeline 概念跑通再上多 agent

具体 hand-off 配方见 `INTEGRATION.md` "Handoff: test-suite-generator → ratchet (legacy, manual)"。

---

## 成本与收敛速度参考

| 路径 | 单轮成本 | 典型收敛轮数 | 整 feature 成本 |
|------|---------|-------------|----------------|
| `/acceptance-fleet`（推荐） | ~$0.75 | 2-4 | ~$2-3 |
| `/ratchet`（legacy） | ~$0.10/轮 subagent | 5-12 | ~$1-2 |

acceptance-fleet 单轮贵但收敛快——四态机制让 SPEC_DRIFT / GAMING_RISK 不在 FIX 里死循环，跨厂商对抗每轮 catch 的 bug 也多。在中等规模 feature 上总成本通常更低，且每条 finding 都有完整 evidence chain。

ratchet legacy 路径单轮便宜但容易循环——典型死循环是"修 → 评分 → 同一个反例又来 → 又修 → ..."，因为没有 SPEC_DRIFT 信号自动逃出。

合规/审计场景（ISO 26262 / SOC 2 等）必须走 acceptance-fleet，因为 ratchet-log/ 提供的可追溯性是 ratchet 不具备的。

---

## 故障排查速查

| 症状 | 多半在哪 |
|------|---------|
| `/acceptance-spec` 5 轮还没把 [?] 清光 | spec 太大，按 SKILL.md 提示拆 feature |
| `/test-suite-generator` 跑某 batch 报 schema 不符 | done_when.yaml 偷加了 sub-field（v1 strict 禁止）；检查 acceptance-spec iron rule 11 |
| `/acceptance-fleet` S0 refuse "cannot guarantee isolation" | 实现和评估同 session 了；开一个 fresh Claude session 跑 fleet |
| 同一个 finding 几轮都修不掉 | meta-judge 会在 iteration 3 自动转 SPEC_DRIFT；该回 /acceptance-spec |
| `gaming_risk_score` 缓慢上升 | impl agent 在压力下学着 game；不要等到 7，趋势单调上升 2 轮就该回头看 spec-robustness.md |
| `spec-robustness.md absent` 警告 | 你跳过了 /acceptance-spec S2.5；可以接受运行，但 fleet 进 max-suspicion，会噪一些 |
| 跨厂商不可用，弱隔离警告 | 装 Codex CLI 或 Gemini CLI；都没有就接受 Level 2 medium |
