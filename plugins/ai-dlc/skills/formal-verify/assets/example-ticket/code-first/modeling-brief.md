# Modeling Brief：ticket-ordering（入口 B 示例）

> 按 Specula `code_analysis/references/modeling-brief-format.md` 写成，是入口 B 交给 model-builder 的材料。
> 分析对象是 `../impl/tickets.py` 的两条购买路径。本例的仓库没有 git 历史与 issue，
> 所以 Bug Archaeology 只记录“没有可挖的历史”，证据全部来自代码阅读。

## 1. System Overview

- 系统：票务下单服务 `TicketService`，Python 3 + sqlite3（WAL），核心逻辑约 80 行。
- 类别：**Category B (Concurrent / Lock-Free / Runtime)**。多个线程各自持有数据库连接，共享一张库存表，正确性取决于事务边界内语句的交错。
- 实现的协议：带库存上限的并发购买。参考设计是“提交时一条条件 UPDATE 预占库存”。
- 偏离参考设计之处：保留了一条 `check-then-act` 路径，依据读取时看到的值扣减（`impl/tickets.py:64-72`）。
- 并发模型：每个用户一个线程、一个连接（`impl/tickets.py:20-23`），没有应用层锁，只靠 SQLite 的写锁。

## 2. Scenarios

### Scenario 1: 依据过期读数的扣减（check-then-act）

**Mechanism**: 购买判定用的是 read 阶段记下的 `seen`，不是提交时的库存；判定与扣减之间没有事务。

**Evidence**:
- Historical: 无（示例仓库没有 git 历史与 issue）。
- Code analysis: `impl/tickets.py:42-45` 把 read 时的库存写进 `requests.seen`；`impl/tickets.py:65-67` 只检查 `seen > 0` 就无条件扣减，没有 `BEGIN`。

**Affected code paths**: `TicketService.read`, `TicketService._purchase_check_then_act`。

**Suggested modeling approach**:
- Variables: 每个用户的 `seen` 快照、`phase` 程序计数器。
- Actions: read 与 buy 分成两个动作；buy 的守卫用 `seen[u] > 0`。
- Granularity: read 与 buy 之间是交错点，必须拆开（Specula 粒度审计：load → conditional → store）。

**Priority**: High
**Rationale**: 直接导致超卖，对外可见；状态空间小，模型检查能穷尽。

### Scenario 2: 事务内的条件预占（atomic 基线）

**Mechanism**: `BEGIN IMMEDIATE` 持写锁覆盖条件 UPDATE、订单写入与状态更新，判定与扣减在同一语句里。

**Evidence**:
- Historical: 无。
- Code analysis: `impl/tickets.py:50-58` 的事务；`impl/tickets.py:52-53` 的 `remaining > 0` 条件与 `rowcount` 判定。

**Affected code paths**: `TicketService.purchase`（atomic 变体）。

**Suggested modeling approach**:
- Variables: 与 Scenario 1 相同。
- Actions: buy / reject 各对应同一事务的一种结果。
- Granularity: 整个事务是一个动作（单锁覆盖整个动作）。

**Priority**: Medium
**Rationale**: 基线行为与合同的守恒、活性性质都落在这条路径上，即使这里没有怀疑的缺陷也要建模。

## 3. Modeling Recommendations

### 3.1 Model (with rationale)

- **What**: 两条购买路径与 read。**Why**: 合同 R1/R2 的性质都由它们决定（Scenario 1、2）。**How**: 用 `phase` 作程序计数器，read 与 buy 拆开。
- **What**: 售罄答复。**Why**: R3 的活性。**How**: reject 动作，与 buy 同一事务的另一结果。

### 3.2 Do Not Model (with rationale)

- **What**: WAL 模式与连接超时（`impl/tickets.py:21-22`）。**Why**: 只影响性能与锁等待，不改变可观测结果。
- **What**: 崩溃后的恢复。**Why**: 需求明确不在范围内；相关的崩溃窗口记在 6.2（D-3），由代码审阅确认。

## 4. Proposed Extensions

| Extension | Variables | Purpose | Scope / Contract / Scenario |
|-----------|-----------|---------|------------|
| 读数快照 | seen | 表达“依据旧值判定” | Scenario 1 |
| 程序计数器 | phase | 拆开 read 与 buy 的交错点 | Scenario 1, R1 |

## 5. Proposed Invariants

| Invariant | Type | Description | Targets |
|-----------|------|-------------|---------|
| NoOversell | Safety | 成功订单数不超过 STOCK | Scenario 1, MC-1 |
| StockNonNegative | Safety | 剩余库存不为负 | Scenario 1, MC-1 |
| Conservation | Safety | 成功订单与剩余库存守恒 | Scenario 2 |
| EveryRequestAnswered | Liveness | 已提交的请求最终成功或售罄。依赖的动作：`purchase` 总会走到 COMMIT 或 ROLLBACK（`impl/tickets.py:50-61`）；要求服务持续运行（A-FAIR） | Scenario 2 |

## 6. Findings Pending Verification

### 6.1 Model-Checkable

| ID | Description | Expected invariant violation | Scenario |
|----|-------------|----------------------------|------------|
| MC-1 | 两个用户都读到 remaining=1 后，check-then-act 路径能否让两人都成功？ | NoOversell, StockNonNegative | Scenario 1 |

### 6.2 Defect Ledger

| ID | Location | Trigger | Wrong behavior | Evidence | Category | Verification | Scenario | Known |
|----|----------|---------|----------------|----------|----------|--------------|----------|-------|
| D-1 | `impl/tickets.py:66-67` | 两个用户在任一方购买前都读到 remaining=1 | 两人都扣减：remaining=-1，两笔成功订单 | `tickets.py:65-67` 只看 `seen`，没有事务 | concurrency | MC | Scenario 1 | none |
| D-2 | `impl/tickets.py:40` | 同一用户第二次提交请求 | `requests.user` 是主键，INSERT 抛出 IntegrityError，用户得不到答复 | `tickets.py:14` 主键定义；`tickets.py:40` 没有 OR IGNORE 或捕获 | low-level | CR | — | none |
| D-3 | `impl/tickets.py:67-69` | 进程在扣减与写订单之间停止 | 库存已扣、订单未写，守恒被破坏 | check-then-act 路径的三条语句不在事务里 | low-level | CR | — | none |

## 7. Reference Pointers

- 源码：`impl/tickets.py:39-72`（请求、读取、两条购买路径）。
- 需求：`../requirements.md`；合同：`../contract.yaml`。
- 已有并发测试：`impl/test_concurrency.py`。
- 本 brief 分析的是实现契约（`../impl-contract.yaml`）落地之前的代码，行号对应当时的版本。之后的变化：D-2 已按契约里 `request` 的幂等要求修复（`INSERT OR IGNORE`）；`purchase` 增加了幂等的重复购买检查，其后的行号下移 4 行。
