# 逐阶段清单：输入 → 输出 · 现状 · 缺口 · 完成判据

> 对齐 *Spec Loop v1.2 × done_when Pipeline · 对账* §3。"现状"指本插件（sdlc）能做到什么、
> 哪些交给邻居、哪些仍是空白——诚实登记，不装作已有。

## 上半段 · 建世界（邻居 looper；本插件只留接缝）

| 环节 | 输入 → 输出 | 本插件 | 缺口 |
|---|---|---|---|
| U1 产品级 PSL | 产品负责人判断 → `psl/product.md`（规律带 PSL-ID + context 声明） | 不做；`/psl` 邻居 | 规律 ID / context 声明 lint 未实现 |
| U2 功能级 PSL | 产品级 PSL + 需求意图 → 切片引用 + 范围段 + Acceptance 雏形 | `/issue` 的范围四项即范围段；切片引用留空合法（TASK 轨） | 引用完整性 lint 未实现 |
| U3 推导产物 | 功能级 PSL → DOS 提案 / Workflow / 形态草案 / 分歧集 | 空白（暂名 psl-derive，不在本插件） | 全部 |
| G1 世界裁决 | 推导产物 + 分歧集 → `g1-record.md` + 签字版形态草案哈希 | `assets/g1_record.md` + `sdlc_state.py gate g1`（reject 必须归因） | 外部证据钩子只是 checklist 项 |

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

### L3 DONE_WHEN v2 → 邻居 `/acceptance-spec`，无则从 issue AC 内联
- v2 形状：以 AC 为单位；`kind: mechanical`（observe + given + expect）/ `kind: human`（statement +
  judge + evidence）；`existence` 只留观察边界；`thresholds` 保留（它们本身是判据）；`constraints`
  （forbidden_paths / mock_allowlist）；`budgets`。测试名不进契约（去 tests-manifest）。
- 完成判据：每条 AC 有 req 且 REQ 全覆盖；existence 无文件路径；`spec-gaming-detector` 与 ratchet 能消费。

### G2 签字 · 冻结 → `lock_done_when.py`
- 输出 `.done_when.lock`（sha256 · 签字人 · 时间 · 文件清单）。
- 完成判据：篡改 AC 的 fixture 被拒（exit 1）；附合法变更提案的同一篡改放行（exit 2）并计入 task 回流。

### L4 PLAN · 任务卡 → `assets/card_template.yaml` + `lint_cards.py`
- 三项：REQ 全覆盖且无重复归属 · 卡间无文件写冲突（含共享文件归属）· 名词可被 DOS 切片解析。
- 上下文 > 40k 必拆（lint）。卡级验收 ≠ 需求级验收：`advance acceptance` 要求所有卡 done。

### L5 测试实现 → 邻居 `/test-suite-generator`（PLAN 之后按卡分批；写完进禁改清单）
- 红-绿证据：新 AC 的测试先在基线提交上跑必须失败。**本插件未实现红-绿脚本**——`/commit` 的
  references 里写了手工做法；空白登记。

### L6 实现 → 隔离子 agent + `/commit`
- 白名单执行器 = `verify_commit.py --card CARD-xx`（溢出即拒）。
- 卡重试计数与失败指纹 = `sdlc_state.py fail --card`（同指纹立即升级）。

### L7 验收执行 A/B/C → 邻居 `/acceptance-fleet`；无则 `/pr-review` + 跑测试
- A 机械档一票否决；B 结构档告警有界可进；C 判断档只请求人。
- `meets_done_when` 应由脚本比对 evaluation_result 与 thresholds 得出——**本插件未实现该比对脚本**（空白）；
  `/pr-review` 的 findings 带 `tier: A|B|C`，是映射的一半。

### G3 例外复核 → `assets/g3_record.md` + `sdlc_state.py gate g3`
- 默认触发（产品需求）；无 human AC 且 B 无告警 → `set gates.g3.required=false` 留痕后可跳。

### L8 合入 · 交付 · 逃逸缺陷 → `sdlc_state.py archive` + `/issue --escape`
- 归档目录结构固定；`metrics.py` 读它。逃逸缺陷登记模板 `assets/escape_defect.md`。

## 横切

- **X1 DOS 生命周期**：邻居 `/dos-extract`（现状本体一源）。本插件只做闭包检查（issue 依赖 DOS
  字段、卡的 dos_slice）；应然本体对账、candidate 命名空间、ontology-drift 均**空白**。
- **X2 回流路由 · 终止预算**：`assets/routing.yaml` + `sdlc_state.py fail`。归因器是启发式：
  白名单溢出 → 例外；哈希不匹配 → 任务层；反例引用 DOS 不变量 → 本体层；与 PSL 规律冲突 → 世界层；
  同卡同指纹 → 方案层。人只确认或改判。
- **X3 度量**：`metrics.py` 从归档导出 lead time、PR 返工轮次、回流分布、G1 拦截率、human AC 占比、
  逃逸缺陷、豁免数。先记基线。
