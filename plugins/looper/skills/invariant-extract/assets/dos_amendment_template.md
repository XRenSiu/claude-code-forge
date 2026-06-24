# 有界 dos.yaml 修订提案 —— 给 □ 不变量一个落脚字段

> **状态:已采纳(方案 A)于 dos 0.1.14(2026-06-24)。** `Territory.invariants` 字段已入宪。
> 本文件保留作历史记录与体例参考;后续若再需扩展 invariants 相关 schema,沿用此格式。
>
> 落卡阶段产物之一。**先提案,不先斩后奏**(CLAUDE.md)。本提案只解决"□ 不变量在现行 schema
> 无处安放"这一个有界问题,不夹带其他改动。

## 背景(为什么需要这次修订)

现行 `dos.yaml` 的 `Territory` **没有 `invariants` 字段**。唯一能装"从失败蒸馏出的规则"的现成
通道是 `MemoryAsset(failure_memory) --REFINES--> Contract(template)`,但它收紧的是**模板的
`done_when` = ◊ 任务级**。把责任级 □ 不变量塞进 done_when,等于重演 invariant-extract 全力反对的
**□/◊ 两层混淆**。因此 □ 不变量需要一个**责任级**的落脚处。

## 两个候选方案(择一,附推荐)

### 方案 A(推荐):给 `Territory` 加 `invariants` 字段

```yaml
# objects.Territory.properties 新增:
invariants:
  type: array
  required: false
  description: >-
    责任级常驻不变量(□):名下每个 Run 都必须守、不随任务变。每项
    {id, statement(EARS), strength: hard|overridable, authority_level?,
     channel: deductive|abductive|both, provenance:{execution_point?|obstacle_ref?}}。
    硬不变量是责任级,默认非 R00x;可经立法提案上升为系统宪法。
    与 done_when(◊ 任务级)严格分层:invariants 跨 Run 常驻,done_when 一次性。
    由 invariant-extract 起草、经立法签字落地(R002:闸门资产只有人能签)。
```

- **优点**:□ 直接挂在它所属的责任单元上,海拔正确(责任级),与 `kpi` 并列自然。
- **守的约束**:不新增领域对象(只加 Territory 值字段);硬不变量入驻仍须人签(R002);
  写入口经事件 + 守卫表(R009),不直写投影;新增字段需"守卫表 / 投影 / UI 三件套同 PR"。

### 方案 B:给 `MemoryAsset.asset_type` 加 `invariant` 枚举

```yaml
# objects.MemoryAsset.properties.asset_type 描述扩展:
asset_type: failure_memory | eval_case | rubric_version | invariant
# 并新增关系:MemoryAsset(invariant) --GOVERNS--> Territory(常驻约束),或复用 ACCRUES
```

- **优点**:复用 MemoryAsset 的复利 / 溯源 / 签字机制(`signed_by`),与 failure_memory→eval_case
  的蒸馏链同构,棘轮天然。
- **代价**:□ 不变量与领地的归属要靠 territory_id + 新关系表达,比方案 A 间接。

## 推荐

**方案 A**,理由:□ 是责任单元的固有属性,挂在 `Territory` 上海拔最正、查询最直接;MemoryAsset
更适合承载"蒸馏资产 / 回归用例"。可在方案 A 落地后,仍用 MemoryAsset 登记每条不变量的 golden
回归用例(棘轮),两者不冲突。

## 三件套清单(若采纳,需同 PR)

- [ ] dos.yaml schema 改动(本提案)
- [ ] 守卫表:新增 `invariant.proposed` / `invariant.signed` 事件 + 守卫(只有人能签,R002)
- [ ] 投影函数:Territory 的 invariants 投影(禁止直写,R009)
- [ ] UI:领地不变量栏的呈现 + 立法签字入口
- [ ] decisions.md:记录本次命名与取舍(体例与 dos-extract 标准一致)

> 本提案由 invariant-extract 自动起草;采纳与否、最终条款由立法者(人)定。
