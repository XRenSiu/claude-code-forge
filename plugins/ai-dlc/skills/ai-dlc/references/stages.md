# 逐阶段清单：输入 → 输出 · 现状 · 缺口 · 完成判据

> 对齐 *Spec Loop v1.2 × done_when Pipeline · 对账* §3。"现状"指本插件（AI-DLC）能做到什么、
> 哪些交给邻居、哪些仍是空白——诚实登记，不装作已有。

## 上半段 · 建世界（本插件：/psl → /psl-derive → G1）

| 环节 | 输入 → 输出 | 本插件 | 缺口 |
|---|---|---|---|
| U1 产品级 PSL | 产品负责人判断 → `PSL-<产品>.md`（规律带 PSL-ID + context 声明） | `/psl`（`verify_psl.py`） | context 声明 lint 未实现；PSL-ID 由 `verify_derived.py` 反查 |
| U2 功能级 PSL | 产品级 PSL + 需求意图 → 切片引用 + 范围段 + Acceptance 雏形 | `/psl`（功能级）+ `/issue` 的范围四项 | 引用完整性 lint 未实现 |
| U3 推导产物 | 功能级 PSL → DOS 提案 / Workflow / 形态草案 / 分歧集 | `/psl-derive`（`verify_derived.py`；DOS 提案复用 dos-extract schema） | N 次隔离推导的行为层未跑 |
| G1 世界裁决 | 推导产物 + 分歧集 → `g1-record.md` + 签字版形态草案哈希 | `assets/g1_record.md` + `aidlc_state.py gate g1`（pass 要求 `world.derived_dir` 存在；reject 必须归因） | 外部证据钩子只是 checklist 项 |

**接缝**：issue 的输入 = PSL 轨：G1 签字版形态草案 + 范围段；TASK 轨：人直接写的需求 + 已有 DOS。
客观触发：`verify_issue.py --dos dos.yaml` 闭包失败 → 强制 PSL 轨。

## 下半段 · 收敛交付（本插件主干）

### L1 TASK · 澄清 · 台账 → `/issue`
- 输入：接缝产物。输出：issue（EARS 风格陈述 + AC v2 + 假设台账 + 依赖 DOS）。
- 完成判据：`verify_issue.py` 过；假设台账每条绑定 REQ/AC 与验证点；澄清最多 3 轮，余下转台账。
- 缺口：EARS 触发条件里的形容词必须可解析为 DOS 属性——只 flag，不机械判。

### L2 接口契约（条件触发）
- 触发判据机器化：issue AC 的 `observe` 边界（route / CLI / 组件）在代码或 DOS 里不存在 → 触发。
  `verify_issue.py` 只能 flag `observe_unresolved`；contract.yaml 的 schema 校验**未实现**（空白）。
- 与 done_when 一起在 G2 签，同进哈希锁（`lock_done_when.py sign done_when.yaml contract.yaml`）。

### L3 DONE_WHEN v2 → `/donewhen-extract`（AC 优先）或 `/acceptance-spec`（EARS spec.md），都在本插件
- v2 形状：以 AC 为单位；`kind: mechanical`（observe + given + expect）/ `kind: human`（statement +
  judge + evidence）；`existence` 只留观察边界；`thresholds` 保留（它们本身是判据）；`constraints`
  （forbidden_paths / mock_allowlist）；`budgets`。测试名不进契约（去 tests-manifest）。
- 完成判据：每条 AC 有 req 且 REQ 全覆盖；existence 无文件路径；`spec-gaming-detector` 与 ratchet 能消费。

### G2 签字 · 冻结 → `validate_done_when_v2.py`（`advance g2` 自动跑）+ `lock_done_when.py sign --stage g2`；L5 后 `--stage l5` 二次锁
- 输出 `.done_when.lock`（sha256 · 签字人 · 时间 · 文件清单）。
- 完成判据：篡改 AC 的 fixture 被拒（exit 1）；附合法变更提案的同一篡改放行（exit 2）并计入 task 回流。
- G2 的裁决在 `advance cards` **和** `advance implement` 都查：S 档跳过 cards 这个阶段，跳不掉签字（v1.4.0）。

### L4 PLAN · 任务卡 → `/plan-cards`（`assets/card_template.yaml` + `lint_cards.py`）
- 三项：REQ 全覆盖且无重复归属 · 卡间无文件写冲突（含共享文件归属）· 名词可被 DOS 切片解析。
- 上下文 > 40k 必拆（lint）。卡级验收 ≠ 需求级验收：`advance acceptance` 要求所有卡 done。

### L5 测试实现 → `/test-suite-generator`（按卡分批的五层金字塔）+ `/spec-compile`（可判性阶梯）+ `/calibrate`（标准的标准）
- 三者都在本插件；产物合并进 `tests-manifest.yaml`；写完进禁改清单（卡 forbidden_files 默认含 tests/**）。
- 未过 `/calibrate` 的标准 `calibration_pending`，不能当 PR 的验证证据：`advance acceptance` 按 `sizing.yaml.calibration.by_tier` 读它——L 档缺报告拒，M 档缺报告记 `calibration_unevaluated` 账本行，任何档有报告就必须过 `verify_calibration.py`（v1.4.0）。
- l5 锁（契约 + 测试）是 `advance implement` 的前置；红基线经 `capture_red_baseline.py --verify` 后记 `contract.red_baseline`；实现后 `verify_red_green.py` 的报告记 `acceptance.red_green`，`advance pr` 读它。
- 红-绿证据：新 AC 的测试先在基线提交上跑必须失败（`capture_red_baseline.py`），实现后基线里每条红测试都要出现且通过、
  一条都不能失踪（`verify_red_green.py`，v1.4.0）；删测试是最便宜的变绿，所以失踪算不绿。

### L6 实现 → `/implement`（隔离实现者 `card-implementer` / self / `/ratchet` / forge-teams）+ `/commit`
- 白名单执行器 = `verify_commit.py --card CARD-xx`（溢出即拒）。
- 卡重试计数与失败指纹 = `aidlc_state.py fail --card`（同指纹立即升级）。

### L7 验收执行 A/B/C → `/acceptance-fleet` 派发六审查 skill → `/meta-judge`（本插件）；单 PR 手工审查用 `/pr-review`
- A 机械档一票否决；B 结构档告警有界可进；C 判断档只请求人。
- `meets_done_when` 由 `acceptance-fleet/scripts/meets_done_when.py` 比对 `behavior.thresholds` 与 qa 测量得出，经 `aidlc_state.py acceptance --meets` 记录，不可 set（v1.4.0）；`advance pr` 读 final-state.json（DONE ∧ 无 unevaluated review）；
  `/pr-review` 的 findings 带 `tier: A|B|C`，是映射的一半。

### G3 例外复核 → `assets/g3_record.md` + `aidlc_state.py gate g3`
- 默认触发（产品需求）；无 human AC 且 B 无告警 → `set gates.g3.required=false` 留痕后可跳；契约里有 `kind: human` 的 AC 时这条 set 被拒。
- 进 G3 / 合入前评审出口要有 `pr-poll.sh done` 写的 `pr-watch/pr-<N>.done.json`（exit 0 / 10）；`review.done` 本身不是凭证。

### L8 合入 · 交付 · 逃逸缺陷 → `/release`（tag · changelog · notes · 部署验证 · 回滚）+ `aidlc_state.py archive` + `/issue --escape`
- `advance release / archive` 要求 `merge.sha` 解析得到且已在 `branch.base` 里；`advance archive` 要求 `release.done`（notes 有 post-deploy 行、tag 指着 merge.sha）或 `skipped_reason`；归档目录结构固定；`/retro` 的 `metrics.py` 读它。逃逸缺陷登记：`/issue --escape` 建 issue 后 `aidlc_state.py escape --issue <N> …`（模板 `assets/escape_defect.md`）。

## 横切

- **X1 DOS 生命周期**：`/dos-extract`（现状本体）+ `/invariant-extract`（□ 不变量）+ `/psl-derive` 的 dos-proposal（应然本体）
  都在本插件；闭包检查（issue 依赖 DOS 字段、卡的 dos_slice）已有。应然 ↔ 现状的对账 skill、candidate 命名空间、
  ontology-drift 仍**空白**（对账目前由人在 G1 记录里做）。
- **X2 回流路由 · 终止预算**：`assets/routing.yaml` + `aidlc_state.py fail`；`/acceptance-fleet` 的四态棘轮与 `/ratchet` 的 kill/restart 都映射到它（见各自 Wiring 段）。归因器是启发式：
  白名单溢出 → 例外；哈希不匹配 → 任务层；反例引用 DOS 不变量 → 本体层；与 PSL 规律冲突 → 世界层；
  同卡同指纹 → 方案层。人只确认或改判。
- **X3 度量**：`/retro`（`metrics.py`）从归档导出 lead time、PR 返工轮次、回流分布、G1 拦截率、human AC 占比、
  逃逸缺陷、豁免数；先记基线，提案落到层。
