# 三档验收 ↔ 检查项 ↔ 执行者 ↔ 效力（Spec Loop L7 / 裁决 C9）

| 档位 | 检查项 | 执行者 | 效力 | severity |
|---|---|---|---|---|
| **A 机械档** | existence（观察边界）· 测试通过 · PBT · 变异 kill rate · 覆盖阈值 · lint / 类型 · 依赖方向 · DOS 词表闭包（结构化字段）· 改动白名单 · REQ-ID 覆盖 · AC / contract 哈希锁 · 红-绿证据 · 隐藏变体集 · **新增依赖**（注册表存在性 / 许可证 / 漏洞）· secrets 扫描 · 契约硬命中（改测试、删断言、mock 越界）· 正确性 / 安全缺陷（有复现） | 脚本（verify_*.py / CI）· qa-reviewer · spec-gaming-detector · pr-review（缺陷类） | **一票否决** = P0，有则一起修 | P0 / P1 |
| **B 结构档** | 圈复杂度 · 重复率 · 公共 API 变更 · diff 体量 · 依赖方向告警 · spec-gaming 软命中 · spec-drift（REQ / AC ↔ 代码） | pr-review · spec-drift-detector | **超阈值告警**，有界可进（G3 决定带告警合入还是回卡） | P1 / P2 |
| **C 判断档** | human AC 路由到指定裁决人 · 架构意图 · 可读性 · 命名 · meta-judge 汇总各 skill 输出并决定是否触发 G3 | pr-review（C 档条目）· pm-reviewer（只路由）· meta-judge | **请求人工** | P3 / G3 |

## 规则

- 一条发现只归一档；档位由**内容**决定（能不能机械判 → A；能量化但需权衡 → B；只能人判 → C）。
- A 档发现 ⇒ review event = `REQUEST_CHANGES`；仅 B/C ⇒ `COMMENT`。
- `meets_done_when` 由脚本比对 evaluation_result 与阈值得出——评估 agent 不宣布它（本插件未实现该比对脚本，登记为空白）。
- 六个 skill 各自输出，编排层做映射；不要每个 skill 自己决定档位——pr-review 的 `tier` 字段是**建议**，
  meta-judge / 人可改判。

## B 档默认阈值（`--rules` 可覆盖）

| 项 | 阈值 |
|---|---|
| 函数长度 | > 50 行 |
| 嵌套深度 | > 4 |
| 文件长度 | > 500 行 |
| 重复块 | > 20 行 × 2 处 |
| 公共 API 变更 | 导出签名变更且无 CHANGELOG / 迁移说明 |
| diff 体量 | > 500 行（L）告警；≥ 1000（XL）在 /pr 已拒 |
