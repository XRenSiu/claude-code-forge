# Pipeline Flow — v1.0.0 全流程

本文档画清 done-when-pipeline 在 v1.0+ 架构下端到端怎么跑通：两层拓扑（6 个独立 review skill + 1 个编排 skill），以及上游 contract producer (`/acceptance-spec` → `/test-suite-generator`) 怎么喂给下游编排层。

> v1.0 是 BREAKING 重构。如果你来自 v0.3.x，对照看 README 的"Migrating from v0.x"小节。

辅助文档：
- `README.md` — 快速上手 + 设计哲学
- `INTEGRATION.md` — 跨厂商 evaluator (Codex/Gemini)、forge-teams impl 团队等可选集成细节
- `skills/<skill>/SKILL.md` — 单个 skill 的完整规格
- `skills/acceptance-fleet/references/skill-dispatch-matrix.md` — 编排层怎么把 v0.x 角色映射到 v1.0+ skill 调用

---

## 全景图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — STANDALONE SKILLS (each user-invocable, contract-agnostic)        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Contract producers:                                                         │
│    /acceptance-spec ─────► specs/<feature>/  (NL → EARS + done_when.yaml +   │
│                                              spec-robustness.md)             │
│    /test-suite-generator ► tests/<feature>/  (5-layer test pyramid)          │
│                                                                              │
│  Review skills (any subset usable independently):                            │
│    /code-reviewer         diff → findings (focus-driven, Detective Loop)     │
│    /qa-reviewer           run tests + classify failures → release readiness  │
│    /pm-reviewer           Agent-as-Judge per-REQ compliance                  │
│    /spec-drift-detector   spec vs code factual divergence (3 types)          │
│    /spec-gaming-detector  6 RHD patterns + diff mode → risk score + gaps     │
│    /meta-judge            synthesize findings → PASS / BLOCK / NEEDS_HUMAN   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2 — ORCHESTRATOR                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    /acceptance-fleet ─────► ratchet-log/iteration-NNN/                       │
│      Dispatches the 6 review skills in parallel,                             │
│      hands findings to /meta-judge,                                          │
│      decodes verdict into four-state ratchet:                                │
│      DONE / FIX / SPEC_DRIFT / GAMING_RISK / NEEDS_HUMAN                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**关键属性：** Layer 1 的 review skills 不知道 `done_when.yaml` 存在。它们各自接受任意格式的 spec / 任意路径的 code，输出独立的 finding-schema。这让任何一个 review skill 都可以独立用于 done_when pipeline 之外的场景（PR 审查、老项目体检、KPI gaming 审计、合规验收）。`/acceptance-fleet` 只是它们的一个消费者。

---

## 全流程（Step 1-6）

### Step 1-3 · `/acceptance-spec` — 写契约

```
/acceptance-spec  "用户能取消订阅,但保留到付费期结束"
         │
         │   S0 Bootstrap   读 brief, 定 feature-slug
         │   S1 Draft       NL → EARS, 模糊处打 [?] tag
         │   S2 Clarify     3 类问题、2-3 轮、≤5 轮硬上限
         │   S2.5 反作弊    "如果我要 game 这个 done_when 我会怎么 game?"
         │                  → 扫 6 类 RHD pattern, close/document/accept 每一项
         │   S3 Solidify    写 5 份文件
         ▼
    specs/<feature>/
      ├── proposal.md           Why / What / Non-goals
      ├── spec.md               EARS REQ-001..NNN, 每条带 source: 行
      ├── tasks.md              拆解任务
      ├── done_when.yaml        v1.0+ schema: existence + behavior + rules
      └── spec-robustness.md    反作弊伴生文件
                                · closed_vectors   (S2.5 已结构性堵掉)
                                · surfaced_vectors (堵不掉, /spec-gaming-detector 监控)
                                · accepted_risks   (识别但故意不防)
                                · verifier_hints   (域特定提醒)
```

**v1.0 schema 变化：** `done_when.yaml` 三层架构是 `existence + behavior + rules`，**不再有 `fitness:` 层**。原来的 fitness 内容 90% 重新归类到程序性验证（grep/ tsc/ 真跑 quickstart），剩下 10% "真的没法机器评估" 由 `/pm-reviewer` 输出的 `requires_human_verification` verdict 承接。详见 HTML v2 §3.5。

### Step 4 · `/test-suite-generator` — 派生测试

```
/test-suite-generator  specs/<feature>/
         │
         │   4-A existence    ripgrep/tree-sitter 存在性检查
         │   4-B unit         example + PBT (Hypothesis/fast-check)
         │   4-C integration  testcontainers, 不许 mock
         │   4-D e2e          Playwright/Cypress
         │   4-E mutation     mutmut/Stryker (反 reward-hacking)
         │   ─────────────────────────────────────────────────
         │   每个 batch 一次跑完不混 — 不一次性出全部
         ▼
    tests/<feature>/
      ├── existence.sh         (fail-fast, set -e)
      ├── unit/                example + property-based
      ├── integration/         + testcontainers
      ├── e2e/                 + Playwright config
      └── mutation.config      kill-rate ≥ 阈值
```

**v1.0 变化：** 4-F (fitness rubric) 已经删除。原来生成的 `fitness.rubric` 文件不再产出。如果你拿到一个 v0.x 时代的 `done_when.yaml` 里还有 `fitness:` 块，schema validator 会拒绝它，让你重新跑 `/acceptance-spec` v1.0+ 生成新的契约。

### Implementation phase（用户自选 agent，**新 session**）

实现阶段不属于这个 plugin。用户用任意 agent（Claude Code subagent、Cursor、Aider、人工）实现，**必须在新 session 跑** —— 实现 agent 不能看到下游 review skill 的 prompt（否则就是 gaming substrate，整个反作弊架构作废）。

### Step 5-6 · `/acceptance-fleet` — 编排 review + ratchet

```
/acceptance-fleet  specs/<feature>/
         │
         │   S0  Bootstrap         读 specs/<feature>/, 检测隔离层级
         │                         strong (Codex/Gemini 可用) / medium (Claude 混合 size)
         │                         weak / 拒绝运行 (无法保证 fresh session)
         │
         │   S1  Dispatch fleet    并行调起 7 个 sub-skill 调用:
         │                         /code-reviewer --focus=security --adversarial  ★ 跨厂商优先
         │                         /code-reviewer --focus=logic
         │                         /code-reviewer --focus=perf
         │                         /qa-reviewer       (跑测试 + maintenance/genuine 分类)
         │                         /pm-reviewer       (Agent-as-Judge: LOCATE/READ/RETRIEVE)
         │                         /spec-drift-detector  (iteration ≥ 2)
         │                         /spec-gaming-detector ★ 跨厂商优先, 比对 history
         │
         │   S2  Synthesize        /meta-judge ← 7 份 review 输出 + done_when.yaml.rules
         │                         (HARD WALL: meta-judge 不重新看代码,只综合)
         │
         │   S3  Ratchet decision  解码 meta-judge verdict + gaming/drift 信号 →
         │                         DONE | FIX | SPEC_DRIFT | GAMING_RISK | NEEDS_HUMAN
         │
         │   S4  State output      写对应 report
         │   S5  Persist           完整 trace 落盘
         ▼
    ratchet-log/iteration-NNN/
      ├── timestamp.txt
      ├── isolation.json
      ├── input-manifest.json
      ├── impl-snapshot.tar.gz       (next iteration 的 --history 输入)
      ├── impl-diff.patch
      ├── fleet-outputs/
      │   ├── code-reviewer-security.yaml
      │   ├── code-reviewer-logic.yaml
      │   ├── code-reviewer-perf.yaml
      │   ├── qa-reviewer.yaml
      │   ├── pm-reviewer.yaml
      │   ├── spec-drift-detector.yaml
      │   └── spec-gaming-detector.yaml
      ├── meta-judge-output.yaml
      ├── final-state.json
      └── <state-specific report>.md
          ├ fix-prompt.md            (FIX state)
          ├ spec-drift-report.md     (SPEC_DRIFT)
          ├ gaming-risk-report.md    (GAMING_RISK)
          └ needs-human.md           (NEEDS_HUMAN)
```

**编排层不拥有 review 逻辑。** 它只是 dispatch + state machine + persistence。任何 review 判断都发生在 6 个独立 skill 内部，meta-judge 综合。

---

## 四态 ratchet 状态机

```
            ┌─────────────────────────────────┐
            │  iteration N 完成 review + judge │
            └─────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┬──────────────┐
              ▼             ▼             ▼              ▼
         ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌────────────┐
         │  DONE   │   │   FIX   │   │SPEC_DRIFT│   │GAMING_RISK │
         └─────────┘   └─────────┘   └──────────┘   └────────────┘
              │             │             │              │
              │             ▼             │              │
              │       fix-prompt.md       │              │
              │             │             │              │
              │             ▼             │              │
              │    用户喂给新 impl session │              │
              │             │             │              │
              │             ▼             ▼              ▼
              │       iteration N+1   /acceptance-spec   /acceptance-spec
              │       (continue)      (narrow REQ)       (harden contract)
              ▼
         loop exits
```

**触发规则（strict 顺序，first match wins）：**

| State | 触发 |
|---|---|
| `NEEDS_HUMAN` | `/meta-judge` 返回 NEEDS_HUMAN（冲突无法仲裁 / `requires_human_verification` 未解决 / 跨厂商对 P0/P1 有分歧但证据相当） |
| `GAMING_RISK` | `gaming_risk_score ≥ 7` OR 连续 2+ 轮单调上涨 ≥2/轮 OR 同一个 `surfaced_vector` 连续 2 轮触发 |
| `SPEC_DRIFT` | `/spec-drift-detector` 报告同一 REQ 的 behavior_mismatch 在 ≥ `SPEC_DRIFT_TRIGGER` (默认 3) 轮反复出现 OR `/pm-reviewer` 同一 REQ 反复 `not_compliant` 但 impl 在变 |
| `FIX` | `/meta-judge` 返回 BLOCK_MERGE 且没有上面三种触发 |
| `DONE` | `/meta-judge` 返回 PASS AND `gaming_risk_score < 3` AND 没有上面任何递归模式 |

**GAMING_RISK 和 SPEC_DRIFT 都不能通过打补丁解决** —— 它们意味着契约本身有问题，必须回到 `/acceptance-spec` 收紧。`/acceptance-fleet` 看到这两种状态会拒绝生成 fix-prompt，强制用户回上游。

---

## 跨厂商隔离层级（防 sycophancy）

`/acceptance-fleet` S0 自动检测可用 evaluator，挑最高可达层级运行：

| Level | 触发条件 | 评审分布 |
|---|---|---|
| **strong** | `which codex` 或 `which gemini` 成功 | Codex/Gemini 跑 `/code-reviewer --adversarial` + `/spec-gaming-detector`; Claude Opus/Sonnet/Haiku 跑其他 |
| **medium** | Claude 多 size 可选, 无跨厂商 | 全 Claude, 但 evaluator 用与 impl 不同的 size (Haiku/Sonnet/Opus 混) |
| **weak** | 只有单 Claude size | 全 Claude 同 size, 加 caveat 警告 |
| **refuse** | 无法保证 fresh session | 拒绝运行 |

**为什么 strong > medium > weak：** Milvus benchmark 实证 Claude + Gemini 抓到 91% bug, 单 vendor 5 个 agent 也抓不全。跨厂商打破 RLHF 共同盲点。详见 `skills/acceptance-fleet/references/evaluation-isolation-levels.md`。

---

## 独立用例（不走 done_when pipeline）

v1.0 把 6 个 review skill 拆出来后，它们各自有独立用途。下面是一些典型的非 pipeline 场景：

| 场景 | 用法 |
|---|---|
| PR 安全审查 | `/code-reviewer HEAD~3..HEAD --focus=security --adversarial` |
| 跨厂商对抗审查 | `/code-reviewer ... --adversarial`（让 Codex/Gemini 跑） |
| CI 集成 | `/qa-reviewer tests/ --thresholds=ci-policy.yaml --baseline=last-build.yaml` |
| PRD 验收 | `/pm-reviewer prd.md src/` |
| Jira ticket 验收 | `/pm-reviewer jira-export.md src/` |
| 老项目文档体检 | `/spec-drift-detector docs/ src/` |
| API 演进追踪 | `/spec-drift-detector openapi.yaml src/api/ --history-depth=200` |
| AI-coding 防作弊审计 | `/spec-gaming-detector spec.md src/ --history=HEAD~5` |
| KPI gaming 审计 | `/spec-gaming-detector kpi-doc.md analytics/` |
| 多 reviewer 综合 | `/meta-judge ./review-outputs/ --rules=team-policy.yaml` |

每个 skill 都有自己的 SKILL.md 描述完整接口。`/acceptance-fleet` 只是它们的诸多消费者之一。

---

## Boundary 1: Step 4 → Step 5-6 隔离

```
        Step 4                        Step 5-6
   /test-suite-generator          /acceptance-fleet (orchestrator)
        │                                │
        │ writes tests/<feature>/         │ dispatches 6 review skills
        ▼                                 │
   user/impl agent runs in              ★ MUST NOT see review prompts ★
   FRESH SESSION                          │
        │                                ▼
        │ implements src/             reviewer sessions are
        ▼                              SEPARATE from impl session
   src/ matches contract                   │
        │                                  ▼
        └──────────────────────────► acceptance-fleet S1 dispatches
```

**铁律：** impl agent 不能看到 review skill 的 prompt。这是 v1.0 / v0.x 都坚持的核心反作弊保证。`/acceptance-fleet` S0 检测隔离层级时如果发现达不到 medium，会拒绝运行。

---

## Boundary 2: SPEC_DRIFT vs GAMING_RISK — 都是 "回到 spec"，区别在哪？

| | SPEC_DRIFT | GAMING_RISK |
|---|---|---|
| **触发信号** | 反复的 PBT 反例 / 同一 REQ 反复 not_compliant；impl 在变但同样的事在反复出错 | gaming_risk_score 高 / 监控 vector 反复触发 / 趋势单调上涨 |
| **根因** | spec 写得不准/不完整，impl 在合理范围内但 spec 没法明确判定对错 | spec 写得有漏洞，impl 形式合规但精神违规 |
| **回去做什么** | `/acceptance-spec` 重新跑 clarify loop，把模糊 REQ 拆细 | `/acceptance-spec` S2.5 强化，关闭 `surfaced_vectors` 里漏掉的 gaming 路径 |
| **风险信号** | "代码做了 5 次但还是过不了同一个 PBT，每次问 ChatGPT 它都说看起来对" | "impl 在改但 mutation_kill_rate 在掉" / "测试里出现新的 mock" / "代码加了 30 行 dead code" |
| **修 spec 后** | 跑 `/test-suite-generator` 派生新测试，从 iteration 1 重新跑 | 同上 |

两种 state 都不允许打补丁修代码。这是 v1.0 ratchet 最重要的设计 —— 大多数循环失败的根因是上游契约不好，而不是下游 impl 不会写。打补丁只会把问题往后推。

---

## 性能与成本

每轮一次 `/acceptance-fleet` 跑完（带 prompt caching）：

| Sub-skill | 模型 | 估算 | 估算 cost |
|---|---|---|---|
| code-reviewer × 3 focuses | Opus + Sonnet + Haiku | 50K in / 9K out | $0.20 |
| qa-reviewer | Sonnet + 工具调用 | 50K in / 10K out | $0.20 |
| pm-reviewer | Opus + 工具调用 | 30K in / 5K out | $0.12 |
| spec-drift-detector | Opus | 25K in / 4K out | $0.10 |
| spec-gaming-detector | Opus (跨厂商时为 Codex/Gemini) | 25K in / 4K out | $0.10 |
| meta-judge | Opus（never weaker） | 25K in / 4K out | $0.10 |
| Orchestrator | Sonnet | 5K in / 1K out | $0.02 |
| **总计 / 轮** | | | **~$0.84** |

典型 feature 收敛 2-4 轮：**~$2-4 / feature**。

跨厂商 evaluator 单次调用稍贵但收敛更快（一轮抓到更多 bug），净 cost 通常低于纯 Claude。

---

## 历史

- **v1.0.0** — BREAKING 架构重构per HTML v2 设计。6 个 review skill 抽出独立, `/acceptance-fleet` 纯编排化, `done_when.yaml` schema 简化为 `existence + behavior + rules`(retired fitness layer), test-suite-generator 4-F 删除。
- v0.3.x — three-role validation pass; landed `/acceptance-fleet` v0.1 as monolithic 7-role fleet。
- v0.2.0 — three-role validation pass; surfaced 17 P0 issues。
- v0.1.0 — initial release, Steps 1-4 only。
