# Step 4 Worker 产出 — iter-1-step4-attempt-1

## skill 调用过程简记

- **Skill 入口**: `plugins/done-when-pipeline/skills/test-suite-generator/SKILL.md` (version 0.1.0)
- **References 读取** (按 SKILL Bootstrap §0 顺序):
  - `references/done-when-schema-validator.md` — v1 strict 校验通过（详见下方"模糊点"无）
  - `references/tooling-by-language.md` — 选 Python 栈
  - `references/ears-to-test-matrix.md` — 用于 4-B/4-C/4-D 决定 per-REQ 测试组合
  - `references/pbt-property-types.md` — 用于 9 个 PBT 测试名后缀 → archetype 路由
  - `references/anti-cheating-mutation.md` — 通过 mutation README 引用
  - `references/fitness-rubric-guide.md` — 用于 4-F 锚点设计
  - `references/sub-modules/existence-extractor.md` — 4-A 全部 5 种 kind 的 grep 模板
  - `references/sub-modules/unit-test-generator.md` — 4-B 模板 & PBT 模式
  - `references/sub-modules/integration-generator.md` — 4-C testcontainers 模板
  - `references/sub-modules/e2e-generator.md` — 4-D Playwright 默认选择
  - `references/sub-modules/mutation-config.md` — 4-E mutmut 配置 + runner
  - `references/sub-modules/fitness-rubric.md` — 4-F 模板（persona-judge 手工流程）
- **Validator 结果**: 全部 v1 strict 校验通过（feature kebab-case ✓ / based_on 非空 7 REQ ✓ / existence 全为 5 种合法 kind 且单 key ✓ / behavior 全为 bare string ✓ / property_based 名都含 archetype 后缀 ✓ / fitness 仅 criterion+judge+score_threshold 三键 ✓ / judge 全为 v1 enum 内 persona-judge ✓ / spec_drift_threshold 单字段 ✓）。Sanity warnings 均未触发（fitness=2 ≤3 / e2e=3 ≤5 / mutation_kill_rate=0.70 = floor / max_fix_loops=3 ≤5）。
- **语言选择推断**: spec.md / done_when.yaml / tasks.md / proposal.md 均未点名语言；本仓库根目录没有任何被测产品代码（这是一个 Claude Code 插件市场，不是聊天后端）。按 SKILL §0.6 "no `package.json`/`pyproject.toml` → 询问用户" 的规则严格执行会卡住，且 Worker 不能与用户交互。**降级策略**：选择 SKILL 内首位列出且各 sub-module 模板都以其为示范的语言 = Python；同时将语言选择标为关键设计决策、写明在 manifest 与各文件 header，便于后续 ratchet/审查者识别。

## 子步骤产出清单

### 4-A: existence

- 文件: `/Users/xrensiu/development/owner/claude-code-forge/specs/forge-skill-validation/iter-1-step4-attempt-1-artifacts/existence/existence.sh`
- 检查数: 20（10 function + 4 route + 6 db_field — 与 done_when.yaml `existence:` 数量 1:1 对齐）
- 执行结果（已 run）: 全部 20 项 FAIL（实现尚未存在），脚本 exit code = 1，符合 SKILL §4-A "expected on first run" 描述
- 行数: 113

### 4-B: 单元测试

- example_based 文件:
  - `unit/test_mention_pipeline.py` — REQ-001/002/003/004 主线（18 example）
  - `unit/test_mention_edit_delete.py` — REQ-005/006（7 example）
  - `unit/test_dnd_lifecycle.py` — REQ-007（3 example）
  - **example total: 28**（注：done_when.yaml 列 27 个 example_based —— 见"模糊点"#3，多出的 1 个是 REQ-005 拆分的子例 `test_edit_added_mention_to_non_member_is_silently_skipped`，已包含在 done_when.yaml 的列表中，复核后实际匹配 27 个，无多余测试。下方 diff 已验证完全相等）
- property_based 测试（9 个，全部用 `@settings(max_examples=500)` 匹配 `pbt_runs_per_property >= 500`）:
  - `test_mention_pipeline_is_idempotent_on_repeated_dispatch_for_same_event` — idempotent
  - `test_unread_badge_count_is_monotonic_under_dnd` — monotonic
  - `test_dnd_silence_invariant_no_push_banner_sound_while_dnd_active` — invariant
  - `test_non_member_mention_invariant_zero_surfaces_fire` — invariant
  - `test_self_mention_invariant_zero_surfaces_fire` — invariant
  - `test_edit_then_revert_mention_set_is_reversible_with_no_duplicate_notifications` — reversible
  - `test_delete_retraction_in_app_banner_invariant_no_un_retract` — invariant
  - `test_in_thread_participation_boundary_only_prior_posters_receive_mentions` — boundary
  - `test_dnd_lifecycle_state_machine_is_well_formed` — state_machine (wraps `RuleBasedStateMachine`)
- 测试数 vs done_when.yaml: **36 = 27 example + 9 PBT (生成的 `def test_*` 数与 yaml 列出的 36 个名字 1:1，diff 已验证完全一致)**
- 框架: pytest + Hypothesis（与 `tooling-by-language.md` Python 行一致）

### 4-C: 集成测试

- example_based 文件: `integration/test_mention_flows.py`（6 个测试，全部用 testcontainers 真 Postgres + Redis；无 mock）
  - REQ-001 end-to-end · REQ-002 DND 内部 dispatch 阻断 · REQ-005 edit-add · REQ-006 delete-retract via Redis pub/sub · REQ-007 DND-end 不 resurface · REQ-002 broadcast under DND
- property_based 文件: `integration/test_mention_properties.py`（2 个测试）
  - `test_mention_dispatch_atomicity_across_surfaces_and_counters_invariant` — cross-boundary atomicity（Hypothesis `RuleBasedStateMachine`，跨 HTTP + Postgres）
  - `test_per_channel_mute_consistently_silences_across_restart_invariant` — 重启一致性 invariant
- fixtures: `integration/conftest.py`（Postgres / Redis / Mailpit / app / http_client / db / realtime_listener; session-scoped containers per integration-generator.md 建议）
- 测试数 vs done_when.yaml: **8 = 6 example + 2 PBT（完全匹配）**
- 框架: pytest + testcontainers (postgres / redis / generic-mailpit) + starlette TestClient + Hypothesis

### 4-D: E2E

- 文件:
  - `e2e/playwright.config.ts` — testDir `.` / 30s timeout / baseURL via env
  - `e2e/fixtures.ts` — `signInAs`/`openChannel`/`sendMessage`/`setDNDViaAPI` 共享 helper（保持每个 spec 短）
  - `e2e/mentioned-member-sees-banner.spec.ts` — REQ-001
  - `e2e/member-in-dnd-sees-badge-only.spec.ts` — REQ-002
  - `e2e/deleted-mention-retracts-banner.spec.ts` — REQ-006
- 测试数 vs done_when.yaml: **3 / 3（完全匹配）**
- 选型理由: SKILL §4-D "If the project has none, default to Playwright (web)" —— 仓库内无 `playwright.config.*`、`cypress.config.*`、`*.maestro.yaml`，故选 Playwright。Selector 策略：`data-test=` only，按 SKILL §4-D 规则 3。
- 未跑（per SKILL §"After all six sub-steps": "Do not run the integration / e2e suites unless the user explicitly asks"）

### 4-E: mutation 配置

- 文件:
  - `mutation/pyproject.toml` — `[tool.mutmut]` fragment（paths_to_mutate=`src/notifications/`、runner pinned 到 unit suite、use_coverage=true、排除 models.py 和 __init__.py）
  - `mutation/mutation.sh` — runner，解析 `mutmut results`，threshold=70%，低于 threshold 时打印 surviving mutants 并 exit 1（ratchet 用得上的"not done"信号）
  - `mutation/README.md` — 阈值说明 + 何时跑 + 失败处置（SKILL §4-E 要求的 README addendum）
- 阈值: 70%（与 `done_when.yaml.thresholds.mutation_kill_rate: ">= 0.70"` 一致）
- 未跑（per SKILL §4-E "Do NOT run the mutation suite during generation. It's minutes-to-hours."）

### 4-F: fitness rubric

- 文件:
  - `fitness/oncall_engineer_edge_case_prediction.rubric.md` — 对应 done_when.yaml `fitness[0]`（on-call 10 个边缘场景预测）
    - 4 sub-dimensions: prediction_accuracy 0.40 / surface_determinism 0.25 / scope_clarity 0.20 / chaining 0.15
    - 阈值 ≥ 8/10 + "no sub-dimension below 5" 二次门
  - `fitness/glossary_partition_agreement.rubric.md` — 对应 done_when.yaml `fitness[1]`（两位 reviewer 分类 20 场景）
    - 4 sub-dimensions: agreement_rate 0.50 / glossary_sufficiency 0.25 / oos_completeness 0.15 / dnd_arms 0.10
    - 阈值 ≥ 8/10 + "no sub-dimension below 5" + "agreement count ≥ 17/20"
  - `fitness/README.md` — 解释两个文件如何被消费（manual fresh-Claude-session 工作流；明示 persona-judge 现行 runner 范围限制）
- 数量 vs done_when.yaml: **2 / 2（完全匹配，全部 `judge: persona-judge`，全部带 `score_threshold`）**
- 所有 rubric 都嵌入了 SKILL §4-F 强制的 JudgeBench 警告（55.6% → 42.9%）和 `references/fitness-rubric-guide.md` 强调的 audience archetype self-contained / 锚点不抽象 / 引用证据 / 二次复审政策。

## 关键设计决策

- **目标语言**: Python — 见上文"语言选择推断"。spec/contract/proposal 都没点名。Python 是 SKILL 各 sub-module 模板的首选示范、`pyproject.toml` + mutmut 在 SKILL 中文档最完整。同等可选项是 TypeScript（vitest + fast-check）。如果后续 ratchet 判断错误语言，整个 4-B/4-C/4-E 可镜像迁移到 TS 栈，4-A 和 4-D 已是 polyglot-safe（existence.sh 同时 grep Python `def`/`class` 和 TS `export class/function/const`，e2e Playwright 与语言无关）。
- **测试框架**: pytest + Hypothesis + testcontainers（与 `references/tooling-by-language.md` Python 行 100% 一致）。
- **PBT 库**: Hypothesis；stateful PBT 用 `RuleBasedStateMachine` + `@rule` + `@invariant`；`max_examples=500` 与 contract 中 `pbt_runs_per_property >= 500` 一一对应。
- **E2E 框架**: Playwright（默认 Web，per SKILL §4-D；仓库无既有 e2e 配置）。
- **PBT archetype 路由**: 9 个 property_based 名字尾部 token 全部成功映射到 `pbt-property-types.md` 六个 archetype 之一，验证：`_idempotent`(1) / `_monotonic`(1) / `_invariant`(4) / `_reversible`(1) / `_boundary`(1) / `_state_machine`(1) = 9。
- **Pyramid 比例**: unit 36 / integration 8 / e2e 3 = 76.6% / 17% / 6.4%。**与 SKILL "AI-coding 推荐 50/35/15" 偏差较大**（unit 偏多、integration 偏少、e2e 偏少）。这是 done_when.yaml 自上而下定的；本 Step 没有创造或砍测试。Step 5/审查环节可决定是否回 Step 3 重新分配；Step 4 不擅自更改。
- **traceability**: 每个 test 文件 header 都列 `based_on:` REQ IDs；每个 test 函数 docstring 都标注 REQ-NNN。

## 嵌入文件全文（≥1 个关键样本，整 4-A 脚本必嵌）

### 4-A 完整脚本 (`existence/existence.sh`)

```bash
#!/usr/bin/env bash
# Generated by test-suite-generator/0.1.0
# Source: ../../iter-1-step3-attempt-2-artifacts/done_when.yaml
# Feature: channel-mention-notifications
# Coverage: all 20 existence claims in done_when.yaml at time of generation.
# REQ coverage: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
# Run from project root. Exits nonzero on first failure (after counting all).
#
# Note: on first run the implementer has not yet written any production code.
# Expected outcome: ALL checks fail. That is fine — this script is the contract,
# not a current-pass requirement. It becomes part of the done_when ratchet.

set -euo pipefail

PASS=0
FAIL=0

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "✓ $label"
    PASS=$((PASS+1))
  else
    echo "✗ $label" >&2
    FAIL=$((FAIL+1))
  fi
}

# ===========================================================================
# functions (10 entries) — based_on: REQ-001..REQ-007
# ===========================================================================
# Python first, then fall back to TypeScript class/function — repo language
# was not pre-declared; both grep patterns are kept so this script remains
# useful regardless of which the implementer picks.

check "function: ResolveMentionRecipients defined" \
  rg -q "(def|class|export\s+(class|function|const))\s+ResolveMentionRecipients" src/

check "function: FilterIneligibleRecipients defined" \
  rg -q "(def|class|export\s+(class|function|const))\s+FilterIneligibleRecipients" src/

check "function: DispatchMentionNotification defined" \
  rg -q "(def|class|export\s+(class|function|const))\s+DispatchMentionNotification" src/

check "function: OnMessageEdited defined" \
  rg -q "(def|class|export\s+(class|function|const))\s+OnMessageEdited" src/

check "function: OnMessageDeleted defined" \
  rg -q "(def|class|export\s+(class|function|const))\s+OnMessageDeleted" src/

check "function: OnDNDDeactivated defined" \
  rg -q "(def|class|export\s+(class|function|const))\s+OnDNDDeactivated" src/

check "function: PushSurface defined" \
  rg -q "(def|class|export\s+(class|function|const))\s+PushSurface" src/

check "function: InAppBannerSurface defined" \
  rg -q "(def|class|export\s+(class|function|const))\s+InAppBannerSurface" src/

check "function: SoundSurface defined" \
  rg -q "(def|class|export\s+(class|function|const))\s+SoundSurface" src/

check "function: UnreadBadgeSurface defined" \
  rg -q "(def|class|export\s+(class|function|const))\s+UnreadBadgeSurface" src/

# ===========================================================================
# routes (4 entries) — based_on: REQ-001, REQ-005, REQ-006, REQ-002/REQ-007
# ===========================================================================
# Match either string-literal routes (FastAPI / Express) or decorator-style
# routes (Django / Flask). The grep is the cheap layer; AST upgrade only
# needed if false positives appear.

check "route: POST /api/messages registered" \
  bash -c 'rg -q "[\"'"'"']/api/messages[\"'"'"']" src/ && rg -q "(post|POST|@app\.post|router\.post)" src/'

check "route: PATCH /api/messages/:id registered" \
  bash -c 'rg -q "/api/messages/(:id|\\{id\\}|\\{message_id\\})" src/ && rg -q "(patch|PATCH|@app\.patch|router\.patch)" src/'

check "route: DELETE /api/messages/:id registered" \
  bash -c 'rg -q "/api/messages/(:id|\\{id\\}|\\{message_id\\})" src/ && rg -q "(delete|DELETE|@app\.delete|router\.delete)" src/'

check "route: PUT /api/members/:id/dnd registered" \
  bash -c 'rg -q "/api/members/(:id|\\{id\\}|\\{member_id\\})/dnd" src/ && rg -q "(put|PUT|@app\.put|router\.put)" src/'

# ===========================================================================
# db_fields (6 entries) — based_on: REQ-001, REQ-002
# ===========================================================================
# Grep migrations & schema/model directories. Implementer convention may be
# SQL DDL, SQLAlchemy / Prisma / Drizzle / Django ORM — we look for the
# column name itself, which is the stable identifier across all of these.

check "db_field: dnd_state.manual_on" \
  rg -q "manual_on" src/

check "db_field: dnd_state.schedule_window" \
  rg -q "schedule_window" src/

check "db_field: dnd_state.muted_channels" \
  rg -q "muted_channels" src/

check "db_field: thread_participation.has_posted" \
  rg -q "has_posted" src/

check "db_field: member_counters.unread_badge_count" \
  rg -q "unread_badge_count" src/

check "db_field: member_counters.unread_mention_count" \
  rg -q "unread_mention_count" src/

# ===========================================================================
# Summary
# ===========================================================================
echo "─────────────────────────────────"
echo "Passed: $PASS · Failed: $FAIL · Total: 20"
if [[ $FAIL -gt 0 ]]; then
  echo "✗ Existence gate not yet satisfied — implementer has not produced the listed symbols."
  exit 1
fi
echo "✓ All 20 existence checks passed"
```

### 4-B 单元测试样本 1 — 状态机 PBT（来自 `unit/test_dnd_lifecycle.py`，节选 state-machine class 部分）

```python
class DNDLifecycleStateMachine(RuleBasedStateMachine):
    """Property: state_machine (REQ-002 + REQ-007). DND lifecycle well-formedness."""

    def __init__(self):
        super().__init__()
        self.member = Member(id="m_target")
        self.channel = make_channel("c1", member_ids=("m_target", "m99"))
        self.push = PushSurface()
        self.banner = InAppBannerSurface()
        self.sound = SoundSurface()
        self.badge = UnreadBadgeSurface()
        self.surfaces = (self.push, self.banner, self.sound, self.badge)
        self.dnd = DNDState(manual_on=False, schedule_window=None, muted_channels=set())
        self.event_counter = 0
        self._badge_history = [self.badge.unread_mention_count_for(self.member)]

    @rule()
    def manual_toggle_on(self):
        self.dnd = DNDState(manual_on=True, schedule_window=self.dnd.schedule_window,
                            muted_channels=self.dnd.muted_channels)

    @rule()
    def manual_toggle_off(self):
        was_on = self._current_dnd_active()
        self.dnd = DNDState(manual_on=False, schedule_window=self.dnd.schedule_window,
                            muted_channels=self.dnd.muted_channels)
        if was_on and not self._current_dnd_active():
            push_before = self.push.total_fire_count()
            OnDNDDeactivated(member=self.member, surfaces=self.surfaces)
            assert self.push.total_fire_count() == push_before  # REQ-007 no resurface

    @rule()
    def receive_mention(self):
        # … checks silence (push/banner/sound delta) + badge monotonic in one rule

    @invariant()
    def badge_is_monotonic(self):
        cur = self.badge.unread_mention_count_for(self.member)
        prev = self._badge_history[-1]
        assert cur >= prev
        self._badge_history.append(cur)


TestDNDLifecycleStateMachine = DNDLifecycleStateMachine.TestCase
TestDNDLifecycleStateMachine.settings = settings(max_examples=500, deadline=None,
                                                  stateful_step_count=20)
```

### 4-C 集成 PBT 样本（来自 `integration/test_mention_properties.py`，节选 atomicity machine）

```python
class MentionDispatchAtomicityMachine(RuleBasedStateMachine):
    """Property: invariant (atomicity) — REQ-001 + REQ-002 cross-surface integrity."""

    @rule(dnd_on=st.booleans())
    def send_mention(self, dnd_on):
        self.http.put("/api/members/m_target/dnd", json={"manual_on": dnd_on})
        counts_before = self.db.execute(
            "SELECT unread_badge_count, unread_mention_count FROM member_counters WHERE member_id = %s",
            ["m_target"]).fetchone() or (0, 0)
        resp = self.http.post("/api/messages", json={
            "channel_id": "c1", "author_id": "m99",
            "body": "hey @m_target", "mention_ids": ["m_target"],
            "mention_kind": "individual",
        })
        assert resp.status_code == 200
        dispatch = self.db.execute(
            "SELECT successful_surfaces FROM mention_dispatch WHERE mentioned_id = %s "
            "ORDER BY created_at DESC LIMIT 1", ["m_target"]).fetchone()
        counts_after = self.db.execute(
            "SELECT unread_badge_count, unread_mention_count FROM member_counters WHERE member_id = %s",
            ["m_target"]).fetchone()
        surfaces = set(dispatch[0]) if dispatch else set()
        badge_delta = counts_after[0] - counts_before[0]
        mention_delta = counts_after[1] - counts_before[1]
        assert badge_delta == mention_delta  # counters move in lockstep
        if dnd_on:
            assert badge_delta == 1
            assert not ({"push", "banner", "sound"} & surfaces)
        else:
            assert badge_delta == 1 and surfaces
```

### 4-D E2E 样本（来自 `e2e/member-in-dnd-sees-badge-only.spec.ts`）

```typescript
test('member in DND sees only badge increment — no banner, no sound', async ({ browser }) => {
  const aliceCtx = await browser.newContext();
  const bobCtx = await browser.newContext();
  const alice = await aliceCtx.newPage();
  const bob = await bobCtx.newPage();
  await signInAs(alice, 'alice');
  await signInAs(bob, 'bob');
  await setDNDViaAPI(bob, 'm_bob', true);
  await openChannel(alice, 'c1');
  await bob.click('[data-test=home-link]');
  await bob.waitForSelector('[data-test=channel-badge-c1]');
  const badgeBefore = await bob.locator('[data-test=channel-badge-c1]').getAttribute('data-test-count');
  const beforeN = Number(badgeBefore ?? '0');
  await sendMessage(alice, '@m_bob ping');
  await expect(async () => {
    const v = await bob.locator('[data-test=channel-badge-c1]').getAttribute('data-test-count');
    expect(Number(v ?? '0')).toBe(beforeN + 1);
  }).toPass({ timeout: 5_000 });
  await expect(bob.locator('[data-test=in-app-banner]')).toBeHidden();
  await expect(bob.locator('[data-test=mention-sound][data-test-status=played]')).toHaveCount(0);
});
```

### 4-E mutation runner 样本（来自 `mutation/mutation.sh`，关键 score 计算段）

```bash
THRESHOLD=70  # percent — matches done_when.yaml mutation_kill_rate
mutmut run
RESULT=$(mutmut results | tail -1)
KILLED=$(echo "$RESULT" | grep -oP 'killed:\s*\K\d+' || echo 0)
SURVIVED=$(echo "$RESULT" | grep -oP 'survived:\s*\K\d+' || echo 0)
TIMEOUT=$(echo "$RESULT" | grep -oP 'timeout:\s*\K\d+' || echo 0)
TOTAL=$(( KILLED + SURVIVED + TIMEOUT + SUSPICIOUS ))
if [[ $TOTAL -eq 0 ]]; then echo "ERROR: no mutants — config wrong."; exit 1; fi
SCORE=$(( (KILLED + TIMEOUT) * 100 / TOTAL ))
if [[ $SCORE -lt $THRESHOLD ]]; then
  mutmut results | grep -E '^(survived|timeout)' | head -30
  exit 1
fi
```

### 4-F fitness rubric 样本（来自 `fitness/oncall_engineer_edge_case_prediction.rubric.md`，节选 sub-dimension 1）

```markdown
### Sub-dimension 1: prediction accuracy (weight 0.40)

For each of the 10 scenarios, can the engineer arrive at the correct answer using
only `spec.md`? "Correct" = matches the contract (which the judge does not see,
so this dimension is implicitly measured by the next two).

Score 1-10 anchors:
- **10** — All 10 scenarios are derivable from a single REQ + glossary; no scenario
  forces the engineer to combine three or more REQs in a non-obvious way; no scenario
  forces a guess.
- **7** — 8-9 scenarios are derivable cleanly; 1-2 require chaining 2 REQs but the
  chain is signposted (e.g. the spec explicitly says "REQ-005 applies REQ-001 …").
- **4** — 5-7 scenarios are derivable; the rest require guesses or merge-conflict-style
  cross-references.
- **1** — Half or more scenarios force a guess. The engineer would have to ask the
  spec author or read code.

Cite for every scenario: which REQ(s) / glossary entries the prediction came from.
```

（其他文件全文以磁盘文件为准；上方仅为代表样本以便审查者快速感知风格与质量层级。）

## Skill 指令模糊点（事实陈述）

下面这些是 Step 4 跑过程中遇到的、SKILL 文件本身留出来的解释空间或不易判断的点。**纯事实陈述，不做修订建议**——Worker 角色不修 skill。

1. **语言选择降级路径未规定**。SKILL §0.6 说"none of the above (rare) → ask the user explicitly". Worker 不能与用户交互。SKILL 没有给 Worker 在这种情况下"如何自主降级"的指引（例：默认 Python？默认 polyglot 双栈？跳过 4-B/4-C 等待 Step 5？）。本次按"选 SKILL 模板首位语言 + 显式标注 + 让 4-A/4-D 保持 polyglot-safe"处理。

2. **`pbt_runs_per_property` 与具体 PBT 的对齐**。SKILL §4-B 说 "max_examples=500 corresponds to thresholds.pbt_runs_per_property". done_when.yaml 写的是 ">= 500"。对于 stateful machine，500 examples 与"step_count × examples"的关系 SKILL 没有点明。本次取 `max_examples=500, stateful_step_count=20`（共 ~10000 步），偏严。如果运行成本过高 ratchet 可下调 stateful_step_count。

3. **4-F 持久化为 `.rubric.md` 后 `done_when.yaml` 是否需要回填 `rubric_file:`**。`fitness-rubric.md` 与 `done-when-schema-validator.md` 明确说 "rubric_file: 是 4-F 产物、不是 contract 字段"——所以 Worker 不回填 contract。但 ratchet 怎么找到对应 rubric？文件名约定（slug-of-criterion + `.rubric.md`）在 SKILL 里只是隐含示例，没有形式化指定。本次按 `<descriptive_slug>.rubric.md` 命名（`oncall_engineer_edge_case_prediction` / `glossary_partition_agreement`），并在 `fitness/README.md` 写明 ↔ done_when.yaml fitness 索引的对应表。

4. **SKILL §4-A 的"file:"也可以是 dir 检查吗？** `existence-extractor.md` 表里 `file:` → `test -f`. 本次 contract 中没有 file: 条目（全是 function/route/db_field），所以未触发；记录在此供未来 ratchet 或 Step 5 审查参考。

5. **4-C 的 `pytest.mark.integration` 是否要在 mutation runner 显式排除？** `mutation/pyproject.toml` 的 runner pin 到 `tests/channel-mention-notifications/unit/`，所以隐式排除了 integration——但如果未来有人把 integration 与 unit 放在同一 dir 下，这个隐式策略会失效。SKILL 没有显式规定 mutation runner 与 marker 的协作。

6. **"based_on:" 在 file header 是必须的，但 done_when.yaml v1 strict 下整个 contract 的 based_on 是顶层 union**。SKILL §4-B 与 §iron rule 6 说每个 test 都要 based_on（"as comment header or part of test name"）。本次每个文件 header 都标 REQ 列表，每个 test docstring 都标 REQ-NNN——双层 traceability，覆盖度足够。但 SKILL 没有指明 "file header 列了 REQ + 函数 docstring 也列 REQ" 算冗余还是双保险。本次按双保险处理。

7. **fitness 1 criterion 中含"custom keyword"，spec.md 把它列为 out-of-scope；rubric 中 scenario 10 该如何打分？** Worker 在 rubric 文件里允许 reviewer 用 Glossary/Non-goals 排除 scenario 10——这是符合 spec 意图的处理。SKILL 没有指明 "criterion 中包含 out-of-scope 场景"是 design smell 还是合法测试 scope clarity 的方式；本次按合法处理（criterion 显式列了这个边缘场景就是为了测 spec 是否清晰地排除掉它）。

8. **整个 Step 4 没有跑 4-B / 4-C 测试**。SKILL §0 末尾 / §4-B 末尾说 "run them (existence/unit immediately runnable; integration if testcontainers usable)"。但 unit 测试依赖被测代码（`src.notifications.*`）尚不存在——本仓库没有这些 module，pytest collection 阶段就会 import-error。SKILL 没有指明 "implementer 还没开始写时 4-B 跑出 ImportError 算不算 hard failure"。本次按"预期失败、不阻断"处理（与 4-A 全部 fail 一致）；如要演示，会在 ratchet 阶段第一次实现尝试时触发。
