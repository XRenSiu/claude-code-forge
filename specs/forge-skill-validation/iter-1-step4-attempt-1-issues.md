# Step 4 Attempt 1 — Audit Issues

**Auditor**: independent subagent
**Scope**: 仅 done-when-pipeline.md 第六章 (6.1–6.8) + 附录 B
**Worker manifest**: `iter-1-step4-attempt-1-output.md`
**Artifacts dir**: `iter-1-step4-attempt-1-artifacts/`
**Contract**: `iter-1-step3-attempt-2-artifacts/done_when.yaml`

铁律：只挑刺，不修复。每个 P0 必引设计文档原文。

---

## 总体结论

**子步骤齐全度**：6/6 全有（existence / unit / integration / e2e / mutation / fitness）。

**测试名逐一对账**（重点）：
- Unit：done_when.yaml 列 36 个 → 文件中 `def test_` 找到 36 个 → **1:1 字面对应，0 漏，0 多。**
- Integration：done_when.yaml 列 8 个 → 文件中找到 8 个 → **1:1 字面对应。**
- E2E：done_when.yaml 列 3 个 snake_case 名 → 文件中 `test('<sentence>', ...)` 全部是 **空格-连字符-破折号自然语言句**，没有 `test_` 前缀，没有下划线分词 → **字面不对账**（详见 P0-1）。

**PBT 真实性**：9 unit + 2 integration = 11 PBT。**无一为 `assert True` 空壳**；全部有实质属性断言。但有几条策略写法弱（详见 P1）。

**Existence 覆盖**：done_when.yaml 列 20 条 → existence.sh 含 20 条 `check` → **1:1 完全覆盖**。

**Mutation 阈值**：脚本 `THRESHOLD=70` ↔ contract `>= 0.70` → 对齐。

**Fitness rubric 维度**：两份 rubric 都有 4 个加权子维度 + 1/4/7/10 锚点 + 证据引用要求 + 二次复审政策 + JudgeBench 警告。**显著不是通用 prompt**。

---

## P0 — 违反硬性约束

### P0-1 · E2E 测试名违背 done_when.yaml 契约（字面不对账）

**设计文档引用**（6.5）：
> "3 个测试名要对齐 done_when.yaml"

**审查 checklist** 明确说：
> "每个 test 名必须出自 done_when.yaml（不能私自重命名、不能新增、不能漏掉）"

**事实**：
done_when.yaml `behavior.e2e_tests` 列：
```yaml
- test_mentioned_member_sees_in_app_banner_in_active_channel
- test_member_in_dnd_sees_only_badge_increment_no_banner_no_sound
- test_deleted_mention_message_retracts_visible_banner
```

但 e2e 三个 .spec.ts 文件中的 Playwright `test()` 字符串分别是：
```ts
// mentioned-member-sees-banner.spec.ts:9
test('mentioned member sees in-app banner in active channel', ...)

// member-in-dnd-sees-badge-only.spec.ts:9
test('member in DND sees only badge increment — no banner, no sound', ...)

// deleted-mention-retracts-banner.spec.ts:9
test('deleted mention message retracts visible banner', ...)
```

**违反点**：
1. 不是契约里的 `test_xxx_xxx` snake_case 标识符 — 没有 `test_` 前缀，没有下划线。
2. 第二条还把 `_no_banner_no_sound` 改写成 `— no banner, no sound`（含连字符、破折号、逗号），第三条把 `mention_message` 顺序保留但去掉下划线。**这是 paraphrase，不是 verbatim**。
3. 后续 ratchet / Step 5 evaluator 若按字符串 grep 契约名找测试会全部找不到。Worker 在每个 spec 头注释里写了 `// Maps to done_when.yaml e2e: <name>`，但那只是 manifest 级别的人类提示，没有任何机器可消费的 binding。

**为什么是 P0**：审查 checklist 把"测试名是否原样来自 done_when.yaml（逐一对账）"列为 P0 项；任意命名重写一律 P0。Playwright 不强制 test 标题必须是空格句 — `test('test_mentioned_member_sees_in_app_banner_in_active_channel', …)` 是完全合法且会被 Playwright runner 正确发现的写法。Worker 选择重新表达是主动决策，没有依据。

**影响**：契约 ↔ 实现物之间的 traceability 在 E2E 层断裂。

---

### P0-2 · Existence 脚本的执行语义与设计文档冲突

**设计文档引用**（6.2）：
> "失败立即停止后续测试（`set -e`）"

**事实**：脚本第 13 行有 `set -euo pipefail`，但所有断言都被包在 `check()` 函数内、以 `if "$@" ...; then PASS=...; else FAIL=...; fi` 调用 —— `if` 语境会**禁用** `errexit`，所以失败的 `check` 不会触发 `set -e` 早退；脚本反而是"全部数完再 exit"。Worker 已经验证过这点（manifest 写"已 run, exit code = 1, 全部 20 项 FAIL"）。

文件 header 第 7 行还自相矛盾地写着：
```
# Run from project root. Exits nonzero on first failure (after counting all).
```
"first failure" 和 "after counting all" 在同一句里互斥。

**为什么是 P0**：设计文档 6.2 节明确把 "失败立即停止后续测试（`set -e`）" 列为 4-A 的硬性约束。当前实现是"全部数完再 exit" — 工程上更友好（一次跑出所有缺失项更利于 ratchet 诊断），但是**违背了设计文档原文**。Worker 没有在 manifest 模糊点里指出这个选择是有意背离设计文档，反而在 header 注释里"假装"自己是 fail-fast。

**修复方向**（仅供参考，不在 Auditor 职责内）：要么按设计文档改成 fail-fast，要么把这个偏离明确标注并升级 SKILL spec 允许"count-all-then-exit"模式。

---

## P1 — 质量瑕疵

### P1-1 · Mutation runner 的 path 是悬空路径

**位置**：`mutation/pyproject.toml:20`
```toml
runner = "pytest -x tests/channel-mention-notifications/unit/"
tests_dir = "tests/channel-mention-notifications/unit/"
```

但 Step 4 实际把 unit 测试产出到 `iter-1-step4-attempt-1-artifacts/unit/`。没有 `tests/channel-mention-notifications/unit/` 目录存在或被规划。Worker 没在 manifest 中说明 "implementer 需要把这些文件移到此目录"。ratchet 直接跑 `mutation.sh` 会失败 "mutmut produced no mutants — config likely wrong"。

**为什么不是 P0**：mutation 配置存在且阈值正确，"产出可用 mutation kill rate 配置"的硬性约束（6.6）勉强达成。只是路径需要 ratchet/Step 5 阶段手工纠正。

---

### P1-2 · 两个 PBT 用 `return` 而不是 `assume()` 过滤无效输入

**位置**：
- `unit/test_mention_pipeline.py:452-453` (`test_non_member_mention_invariant_zero_surfaces_fire`):
  ```python
  if outsider_id in channel.member_ids:
      return  # generator produced an in-channel id; skip — vacuously true
  ```
- `unit/test_mention_edit_delete.py:200-201` (`test_edit_then_revert_mention_set_is_reversible_with_no_duplicate_notifications`):
  ```python
  if not initial_mentions:
      return  # nothing to edit; vacuously true
  ```

**问题**：Hypothesis 把无 `assume()` 包装的 `return` 当成通过；这会让大比例（依赖随机生成器输出）example "vacuously pass" 而**不真正执行**属性断言。SKILL 在 `pbt-property-types.md` 等子模块没有显式禁用此模式，但 Hypothesis 官方建议用 `hypothesis.assume(...)` —— assume 会被记入 Hypothesis 的 events 统计，并允许 shrinker 优化生成空间。

**为什么不是 P0**：测试**本体不是空壳**，断言是真的；只是有效样本数有概率衰减。pbt_runs_per_property=500 给了足够余量。

---

### P1-3 · 集成 PBT 的 fixture 共享 + Hypothesis 重复运行有状态泄漏风险

**位置**：`integration/test_mention_properties.py:110-156`

`test_per_channel_mute_consistently_silences_across_restart_invariant` 同时使用 `@settings(max_examples=500)` `@given(...)` 装饰器**和** pytest 函数级 fixture（`http_client, db, postgres_url, redis_url`）。Hypothesis 与 function-scoped pytest fixture 配合是已知反模式：fixture 只在 `@given` 函数本身被调用时实例化一次，而非每个 example 一次 —— 500 次 example 共享同一个 Postgres 会话和 TestClient，**状态 (DB 行、Redis sub) 在 example 之间累积**。

测试前两行 `DELETE FROM member_counters WHERE member_id = 'mp'` 试图自救，但 `mention_dispatch` 表也累积了上次 example 的 row，`ORDER BY created_at DESC LIMIT 1` 不一定指向本次发的 mention（除非 created_at 精度足够分辨毫秒）。

`MentionDispatchAtomicityMachine` 同样把 fixture 通过 class attribute 注入 (`machine_cls.http = http_client`)，是绕过 fixture 生命周期的取巧做法；500 个 example 全在同一个 DB 实例上跑，`@initialize()` 内的 `seed_member` 用 `ON CONFLICT DO NOTHING`，所以 counters_before 会随 example 累积而漂移，`assert badge_delta == 1` 在后续 example 上会失败。

**为什么不是 P0**：测试结构存在、PBT 不是空壳、testcontainers 真容器接入正确（满足 6.4 的核心要求"可用 testcontainers 启动真实依赖"）。只是 example 之间隔离不干净 —— Step 5 跑起来才会暴露。

---

### P1-4 · REQ-004 (self-mention) 没有 integration 测试覆盖

**事实**：done_when.yaml 把 REQ-004 列在 `based_on` 第 4 位。spec.md 我没有直接读（不在审查范围）；但根据自然语言，REQ-004 "self-mention emits no notification" 在 done_when.yaml 中：
- unit example_based: ✓ (`test_self_mention_emits_no_notification`)
- unit property_based: ✓ (`test_self_mention_invariant_zero_surfaces_fire`)
- integration: ✗
- e2e: ✗

**关联设计文档 6.8**：
> "Ubiquitous (SHALL Y) → 单元 ✓ 集成 ✓ E2E ✗ ; Unwanted (IF condition) → 单元 ✓ 集成 ✗ E2E ✗"

REQ-004 若属于 Unwanted（"IF self-mention, THEN no notification"），缺集成符合矩阵。若属于 Ubiquitous，则缺集成是违反 6.8 矩阵。**Auditor 没读 spec.md，无法定句式**，所以保守报 P1 而非 P0。Worker 在 manifest 也没有显式提及 REQ-004 句式归类。

---

### P1-5 · `_b3-self-consistent.json`-级 manifest 自打脸：声称 28 example 但又说 27

**位置**：`iter-1-step4-attempt-1-output.md:36-37`：
> "example total: 28（注：done_when.yaml 列 27 个 example_based —— 见'模糊点'#3，多出的 1 个是 REQ-005 拆分的子例 `test_edit_added_mention_to_non_member_is_silently_skipped`，已包含在 done_when.yaml 的列表中，复核后实际匹配 27 个，无多余测试。"

**事实**（我刚 grep）：unit example_based count = 27（done_when.yaml 列了 27 个，文件里 def test_ 数也是 27）。Worker manifest 自己把 28 改口成 27，但句子内部仍写 "example total: 28"。这是 manifest 一处自相矛盾的措辞错误（实际数据正确）。属于报告质量瑕疵，不影响测试本身。

---

### P1-6 · `pytest` 与 `pytest.mark.integration` 不一致使用

**事实**：
- `integration/test_mention_properties.py:91` 有 `@pytest.mark.integration`。
- `integration/test_mention_flows.py` 完全没有 `@pytest.mark.integration`。
- `mutation/pyproject.toml:13` 注册了 `"integration: requires testcontainers (Docker)"` marker。

意图是用 marker 让 mutation runner 自动排除 integration suite，但只有 1/8 个 integration 测试被 mark。SKILL（manifest 模糊点 #5 也认领了这点）没有强制规定 marker 应用范围。Mutation pyproject 通过 `runner = "pytest -x tests/channel-mention-notifications/unit/"` 显式 pin 路径，绕过 marker —— 所以 marker 现在是死代码，意图与实现冲突。

---

## P2 — 风格

### P2-1 · existence.sh 头注释自相矛盾

`existence/existence.sh:7`：`# Run from project root. Exits nonzero on first failure (after counting all).`

"first failure" 和 "after counting all" 在同一行里互斥。挑一个写。

---

### P2-2 · Worker manifest 称 4-A 已 run，但脚本通过 `set -e` 加 `if` 的组合实际上不是 fail-fast

Manifest 第 28 行声称 "全部 20 项 FAIL（实现尚未存在），脚本 exit code = 1，符合 SKILL §4-A 'expected on first run' 描述"。fail tally + 末尾 exit 1 是正确的，但不是设计文档 6.2 节描述的 `set -e` "失败立即停止"语义。**这一项已在 P0-2 中以"语义违背"报；这里仅记 manifest 的措辞过于轻巧没有揭示偏离**。

---

### P2-3 · 集成 PBT 用 `RuleBasedStateMachine` 但 done_when.yaml 名是 `_invariant` 后缀，archetype 路由不一致

`test_mention_dispatch_atomicity_across_surfaces_and_counters_invariant` 命名 archetype 后缀是 `_invariant`，但实现是 `RuleBasedStateMachine`（stateful machine）。manifest 把它路由到 "invariant"。SKILL `pbt-property-types.md` 严格区分 `invariant` 和 `state_machine` 两个 archetype，stateful machine 通常应命名为 `_state_machine` 后缀。

不是 P0/P1 因为 archetype 后缀是 SKILL 内部 routing convention，名字字面属于 done_when.yaml 契约（已确认 1:1 对应），改不动；只是命名与实现风格不完全自洽。

---

### P2-4 · Fitness rubric 第二份的 sub-dimension 1 anchor 表里有跳跃

`fitness/glossary_partition_agreement.rubric.md` sub-dimension 1 锚点：10/8/6/4/1 —— 跳过了 7 和其他奇数档，与第一份 rubric 的 1/4/7/10 风格不统一。两份风格不一致，reviewer 用第一份训练过的直觉迁移到第二份可能误读。

---

## 设计文档 6.8 句式映射表合规性（Auditor 不读 spec.md，仅做软核对）

| REQ | yaml 覆盖 | 推测句式（未验证） | 6.8 矩阵预期 | 偏差 |
|---|---|---|---|---|
| REQ-001 | unit ✓ / int ✓ / e2e ✓ | Event-driven | unit ✓ int ✓ e2e ✓ | 无 |
| REQ-002 | unit ✓ / int ✓ / e2e ✓ | State-driven | unit ✓ int ✓ e2e ✗ | E2E 多了（设计 6.8 说 State-driven 不应有 E2E）— P2 |
| REQ-003 | unit ✓ / int ✗ / e2e ✗ | Unwanted | unit ✓ int ✗ e2e ✗ | 无 |
| REQ-004 | unit ✓ / int ✗ / e2e ✗ | Unwanted? Ubiquitous? | 两种解读各异 | 见 P1-4 |
| REQ-005 | unit ✓ / int ✓ / e2e ✗ | Event-driven | unit ✓ int ✓ e2e ✓ | E2E 缺（Event-driven 应有） — P2 |
| REQ-006 | unit ✓ / int ✓ / e2e ✓ | Event-driven | unit ✓ int ✓ e2e ✓ | 无 |
| REQ-007 | unit ✓ / int ✓ / e2e ✗ | Event-driven | unit ✓ int ✓ e2e ✓ | E2E 缺（Event-driven 应有） — P2 |

E2E 缺失/多余总体属于 P2 风格观察，因为：
1. 设计 6.5 也说 E2E "数量少而精，只覆盖关键用户旅程" —— 隐含允许选择性覆盖。
2. 句式归类未经 spec.md 核验。
3. Step 4 不创造测试名 —— E2E 名是 done_when.yaml 自上而下定的，Worker 不应擅自添加。

但 REQ-002 在 yaml 里**有** E2E 名 (`test_member_in_dnd_sees_only_badge_increment_no_banner_no_sound`) 而 6.8 矩阵说 State-driven 不应有 E2E —— 这是 **done_when.yaml 与 6.8 的冲突**，Step 4 不能修；Step 3 攻坚才是地方。仅作记录。

---

## 总结

| 等级 | 数量 | 主要议题 |
|---|---|---|
| **P0** | 2 | E2E 测试名 paraphrase / existence.sh 不 fail-fast |
| **P1** | 6 | mutation path 悬空 / PBT 用 return 替代 assume / 集成 PBT fixture 复用泄漏 / REQ-004 集成覆盖缺 / manifest 28 vs 27 / marker 死代码 |
| **P2** | 4 | header 自相矛盾 / fail-fast 措辞 / archetype 后缀风格 / rubric anchor 阶梯不一致 |

**6 个子步骤齐全度**：通过。
**测试名逐一对账**：unit 1:1 / integration 1:1 / **e2e 字面不一致（P0-1）**。
**existence 覆盖度**：20/20 完全覆盖。
**PBT 真实性**：无空壳；存在弱样本写法（P1-2）和有状态泄漏风险（P1-3）。
**mutation 阈值**：对齐（70 / 0.70）。
**fitness rubric 质量**：精心设计，非通用 prompt，满足 6.7 警告。

P0-1 必须修；P0-2 取决于是否修订 SKILL 允许 count-all 模式。其它 P1 在 Step 5 / ratchet 阶段会自然暴露并被修复。
