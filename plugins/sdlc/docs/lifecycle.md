# 生命周期全景：阶段 × 承载 × 邻居 × 缺口

> 对齐 *Spec Loop v1.2 × done_when Pipeline · 对账、冲突裁决与逐步实现清单*（2026-09-04）。
> 本插件是**下半段的交付主干 + 横切的 X2/X3**；上半段与契约/测试生成由邻居承担，缺席不阻塞。

```
上半段 · 建世界（looper）          接缝              下半段 · 收敛交付（sdlc 主干 + done-when-pipeline）
─────────────────────────         ────              ─────────────────────────────────────────────
U1 产品级 PSL   (/psl)                                L1 TASK          /issue ──────────────┐
U2 功能级 PSL   (/psl)         issue 输入 :=          L2 接口契约      （空白，条件触发）    │
U3 推导产物     (空白: psl-derive)  G1 形态草案        L3 DONE_WHEN v2  /acceptance-spec | issue 内联
G1 世界裁决     人 · gate g1     + 范围段             G2 签字冻结      lock_done_when.py · 人
                                 TASK 轨直接进 L1     L4 PLAN 任务卡   cards + lint_cards.py
                                 闭包失败 → 强制 U 段  L5 测试实现      /test-suite-generator（红-绿：空白）
                                                      L6 实现          隔离子 agent + /commit（白名单执行器）
                                                      L7 验收 A/B/C    /acceptance-fleet | /pr-review + 测试
                                                      G3 例外复核      人 · gate g3
                                                      L8 合入·交付     /pr → /review-loop → merge → archive
                                                      逃逸缺陷         /issue --escape
横切  X1 DOS 生命周期 (/dos-extract 一源；对账/候选态/drift 空白)
      X2 回流路由 + 终止预算 (routing.yaml + sdlc_state.py fail)
      X3 度量 (metrics.py)
```

## 制品映射（v1.2 制品 → 本插件 / 邻居 → 状态）

| v1.2 制品 / 环节 | 承载 | 状态 | 说明 |
|---|---|---|---|
| 产品级 / 功能级 PSL | looper `/psl` | 邻居 | 引用完整性 lint 未实现 |
| 推导产物 | — | **空白** | 暂名 psl-derive；DOS 提案应复用 dos-extract schema |
| G1 世界裁决 | `sdlc` `assets/g1_record.md` + `gate g1` | 已有 | reject 必须归因；外部证据只是 checklist 项 |
| TASK（EARS + REQ-ID） | `/issue`（雏形）→ `/acceptance-spec`（spec.md） | 已有 | issue 的 AC 已是 v2 形状 |
| 澄清 + 假设台账 | `/issue` Assumptions 段 | 已有 | 3 轮上限是判据，未编译 |
| 接口契约 | — | **空白** | `verify_issue.py` 只 flag observe 边界不存在 |
| DONE_WHEN v2 | `/acceptance-spec`（v1 schema 冲突待其升级）或 issue 内联 | 部分 | 本插件按 v2 形状消费 |
| G2 签字冻结 | `lock_done_when.py` + `gate g2` | 已有 | 篡改被拒 / 附提案放行 已冒烟 |
| PLAN 任务卡 | `card_template.yaml` + `lint_cards.py` | 已有 | 三项 lint + 上下文上限 |
| 测试实现 | `/test-suite-generator` | 邻居 | 红-绿证据脚本 **空白** |
| 实现 | forge-teams / pdforge / 你 + `/commit` | 已有 | 白名单执行器 = verify_commit.py |
| 验收 A/B/C | `/acceptance-fleet` 六 skill；无则 `/pr-review` | 部分 | `meets_done_when` 比对脚本 **空白** |
| G3 例外复核 | `assets/g3_record.md` + `gate g3` | 已有 | 默认触发；required=false 需留痕 |
| 合入 · 交付 · 逃逸缺陷 | `/pr` `/review-loop` `archive` `/issue --escape` | 已有 | 归档结构固定 |
| DOS 本体 + 闭包 | `/dos-extract` + `verify_issue.py --dos` / `lint_cards.py --dos` | 部分 | 对账 / candidate / ontology-drift **空白** |
| 回流路由 | `routing.yaml` + `sdlc_state.py fail` | 已有 | 归因器是启发式，人确认 |
| 终止预算 | 分层计数 + 指纹终止 | 已有 | 按轨道分预算 |
| 度量 | `metrics.py` | 已有 | 先记基线 |

## 十个裁决在本插件里的落点

| 裁决 | 落点 |
|---|---|
| C1 done_when 以 AC 为单位 | issue AC v2 形状；pr 的 AC→证据映射；测试名不进契约 |
| C2 existence 只留观察边界 | `verify_issue.py` 拒文件路径；文件级存在性在卡的 allowed_files |
| C3 fitness / persona-judge 移除 | human AC = `kind: human` + judge + evidence；pm-reviewer 只路由 |
| C4 澄清 3 轮 + 台账 | issue Assumptions 段；G3 逐条处置 |
| C5 drift 两义 | spec-drift（任务层）vs ontology-drift（本体层，空白） |
| C6 测试非实现者写、写完锁 | 卡 forbidden_files 默认含 tests/**；锁进 A 档 |
| C7 防作弊清单 | A 档：白名单 / 锁 / secrets / 新增依赖 / 红-绿（部分） |
| C8 N=3 并入路由表 | routing.yaml R05 |
| C9 三档 ↔ 六 skill | pr-review `tier` + `references/tiers.md` |
| C10 文档漂移 | 本插件以 md 为源；无 html |

## 起手顺序（与参考文档 §4 一致）

Phase 1 下半段判据化（本插件已提供零件：issue AC v2、G2 锁、白名单、卡 lint、A 档清单）→
Phase 2 路由与预算（routing.yaml、指纹终止、G3 触发）→ Phase 3 DOS 横切（邻居）→
Phase 4 上半段（邻居）→ Phase 5 对账与度量（metrics.py 先记基线）。
