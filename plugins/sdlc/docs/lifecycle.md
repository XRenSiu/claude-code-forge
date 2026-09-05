# 生命周期全景：阶段 × 承载 × 邻居 × 缺口

> 对齐 *Spec Loop v1.2 × done_when Pipeline · 对账、冲突裁决与逐步实现清单*（2026-09-04）。
> 本插件覆盖**上半段（/psl → /psl-derive → G1）、下半段 L1–L8 + G2/G3、横切 X1（/dos-extract、/invariant-extract）/ X2 / X3**；
> done-when-pipeline 的九个验收线 skill 与 ratchet 也已收编；仅 forge-teams / pdforge（实现侧执行器）留作可选邻居。

```
上半段 · 建世界（sdlc：psl / psl-derive）          接缝              下半段 · 收敛交付（全部在 sdlc）
─────────────────────────         ────              ─────────────────────────────────────────────
U1 产品级 PSL   (/psl)                                L1 TASK          /issue ──────────────┐
U2 功能级 PSL   (/psl)         issue 输入 :=          L2 接口契约      （空白，条件触发）    │
U3 推导产物     (/psl-derive)       G1 形态草案        L3 DONE_WHEN v2  /donewhen-extract | /acceptance-spec（均在本插件）
G1 世界裁决     人 · gate g1     + 范围段             G2 签字冻结      lock_done_when.py · 人
                                 TASK 轨直接进 L1     L4 PLAN 任务卡   /plan-cards（lint_cards.py）
                                 闭包失败 → 强制 U 段  L5 测试实现      /test-suite-generator + /spec-compile → /calibrate
                                                      L6 实现          /implement（隔离实现者）/ /ratchet + /commit（白名单执行器）
                                                      L7 验收 A/B/C    /acceptance-fleet → 六审查 skill → /meta-judge
                                                      G3 例外复核      人 · gate g3
                                                      L8 合入·交付     /pr → /review-loop → merge → /release → archive
                                                      逃逸缺陷         /issue --escape
横切  X1 DOS 生命周期 (/dos-extract + /invariant-extract；对账/候选态/drift 空白)
      X2 回流路由 + 终止预算 (routing.yaml + sdlc_state.py fail)
      X3 度量 (/retro · metrics.py)
```

## 制品映射（v1.2 制品 → 本插件 / 邻居 → 状态）

| v1.2 制品 / 环节 | 承载 | 状态 | 说明 |
|---|---|---|---|
| 产品级 / 功能级 PSL | `/psl`（本插件，引自 looper） | 已有 | 引用完整性 lint 未实现 |
| 推导产物 | `/psl-derive` + `verify_derived.py` | 已有 | DOS 提案复用 dos-extract schema；N 次隔离推导行为层未跑 |
| G1 世界裁决 | `sdlc` `assets/g1_record.md` + `gate g1`（pass 要求 derived_dir） | 已有 | reject 必须归因；外部证据只是 checklist 项 |
| TASK（EARS + REQ-ID） | `/issue`（雏形）→ `/acceptance-spec`（spec.md，本插件） | 已有 | issue 的 AC 已是 v2 形状；acceptance-spec 的 done_when 仍是 v1 形状（C1/C2 待其升级） |
| 澄清 + 假设台账 | `/issue` Assumptions 段 | 已有 | 3 轮上限是判据，未编译 |
| 接口契约 | — | **空白** | `verify_issue.py` 只 flag observe 边界不存在 |
| DONE_WHEN v2 | `/donewhen-extract`（AC 优先）或 `/acceptance-spec` + `convert_v1_to_v2.py` | 已有 | 唯一契约 schema = v2（`references/done-when-v2-schema.yaml`）；`validate_done_when_v2.py` |
| G2 签字冻结 | `validate_done_when_v2.py` + `lock_done_when.py --stage g2|l5` + `gate g2` | 已有 | 契约 v2 校验编译进 advance g2；篡改被拒 / 附提案放行 已冒烟 |
| PLAN 任务卡 | `/plan-cards`（`card_template.yaml` + `lint_cards.py`） | 已有 | 三项 lint + 上下文上限 |
| 测试实现 | `/test-suite-generator` + `/spec-compile` + `/calibrate`（本插件） | 已有 | 红-绿证据脚本 **空白** |
| 实现 | `/implement`（card-implementer / self / `/ratchet` / forge-teams）+ `/commit` | 已有 | 白名单执行器 = verify_commit.py；实现者信息隔离 |
| 验收 A/B/C | `/acceptance-fleet` + 六审查 skill + `/meta-judge`（本插件）；单 PR 用 `/pr-review` | 已有 | `meets_done_when` 比对脚本 **空白**；三档映射写在各 Wiring 段 |
| G3 例外复核 | `assets/g3_record.md` + `gate g3` | 已有 | 默认触发；required=false 需留痕 |
| 合入 · 交付 · 逃逸缺陷 | `/pr` `/review-loop` `/release` `archive` `/issue --escape` | 已有 | 验证绿才交付；归档结构固定 |
| DOS 本体 + 闭包 | `/dos-extract` + `/invariant-extract`（本插件，引自 looper）+ `verify_issue.py --dos` / `lint_cards.py --dos` | 部分 | 应然↔现状对账 / candidate / ontology-drift **空白** |
| 回流路由 | `routing.yaml` + `sdlc_state.py fail`；`/acceptance-fleet` 四态、`/ratchet` kill/restart 映射到它 | 已有 | 归因器是启发式，人确认 |
| 终止预算 | 分层计数 + 指纹终止 | 已有 | 按轨道分预算 |
| 度量 | `/retro`（`metrics.py`） | 已有 | 先记基线；提案落层 |

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
Phase 2 路由与预算（routing.yaml、指纹终止、G3 触发）→ Phase 3 DOS 横切（/dos-extract、/invariant-extract）→
Phase 4 上半段（/psl、/psl-derive、G1）→ Phase 5 对账与度量（metrics.py 先记基线）。
