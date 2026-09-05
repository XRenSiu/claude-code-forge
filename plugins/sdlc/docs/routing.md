# X2 回流路由与归因启发式

默认行为是灾难性的：任何失败都塞回实现层再试一次。路由表存在的意义就是不让世界层的错误在实现层
被重试二十次。

## 表在哪、谁读

`skills/sdlc/assets/routing.yaml`（数据）→ `skills/sdlc/scripts/sdlc_state.py fail --signal <signal>`
（读表、记账、判升级）。引擎不在 prompt 里复述表；它报信号，脚本给决定。

## 归因启发式（候选层由这些规则给，人确认或改判）

| 失败信号 | 候选层 | 为什么 |
|---|---|---|
| diff 溢出白名单 | 例外（停机交人） | 不是任何一层的正常回流 |
| 锁哈希不匹配 | task | 契约被动了：要么判据写错，要么有人绕锁 |
| PBT / 测试反例引用 DOS 不变量 | ontology | 本体错了，改代码没用 |
| 反例与 PSL 规律冲突 | world | 世界错了或推错了 → G1 归因 |
| 同卡同指纹再现 | plan | 无进展 = 卡切错 / 方案错，不是再试 |
| 连续 3 次以与 REQ 一致的反例失败 | task | REQ / AC 该收窄（N=3 规则） |
| 隐藏变体集失败 | task | AC 不完备（含新需求的隐藏集是规格缺陷） |
| review 线程往返到上限 | task（交人） | 争议不在实现层解决 |
| 合后逃逸缺陷 | 人归因 | 唯一的外部校准源 |

## 分层计数与预算

| 层 | PSL 轨 | TASK 轨 | 耗尽后 |
|---|---|---|---|
| card | 3 | 3 | → plan |
| plan | 2 | 2 | → task |
| task | 2 | 1 | → ontology / G3 |
| ontology | 1 | 1 | → world |
| world | 无上限 | 无上限 | 本来就该停下来交人 |

**指纹终止**：同层同指纹连续 2 次 = 无进展 → 立即升级，不等预算烧完。指纹 = 失败输出的稳定
摘要（`--fingerprint`），或 `--evidence` 文本的 sha1 前 12 位。

## 失败报告（G3 的输入；模板 `assets/failure_report.md`）

当前状态 · 候选归因层 + 依据规则 + 证据 · 已排除的可能 · 建议回退目标 · 请人确认 / 改判。
人不看原始日志。

## 完成判据（fixture）

- 人为注入"两条 AC 互相矛盾"→ 被路由到 task 层而非实现层重试；
- 同指纹连续失败在第 2 次即升级；
- 全绿 fixture 不触发 G3（`gates.g3.required=false` 留痕后）。
前两条由 `sdlc_state.py fail` 冒烟覆盖（见 `skills/sdlc/eval/report.md`）；第三条是 /sdlc 的行为层，未跑。
