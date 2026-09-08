# Criteria 设计方法论

## 核心原则

写不出机器可验的 criteria,就不该启动循环。
Criteria 是规约,不是测试。它定义了"什么算完成"的完整契约。

## 从模糊需求到硬判据：5 步法

### 第 1 步：逼问真目标

问三件事：
- 最终要解决什么问题？
- 什么结果算"真的好"？
- **什么结果"看着好但其实不行"？**（最关键）

第三问用 OKR 的 Litmus test 验证：
"如果所有 criteria 都满分,但主目标仍没达成,可能吗？"
答案是"可能" → criteria 有洞,补。

### 第 2 步：三段式拆解

每条 criterion 拆进四元组：

| 段位 | 含义 | 例子 |
|------|------|------|
| Given | 输入约束 | 输入是 UTF-8,长度 ≤ 1MB |
| When | 触发动作 | 调用 parse(s) |
| Then | 输出性质 | 返回合法 AST,或抛 ParseError 带行列号 |
| Invariant | 不变量 | 不写文件、不超内存、不联网 |

**Invariant 最容易漏。** agent 的作弊空间就在 invariant 的缝隙里。

Safety(坏事不发生) + Liveness(好事终将发生),两个都要写。

### 第 3 步：∀ 量化 — 用性质代替用例

定义"对任意合法输入都必须成立的性质",比列举用例强一个数量级。

5 大性质模式,拿到任何任务对着套一遍：

1. **Round-trip(往返)**
   `decode(encode(x)) == x`
   Parser: `parse(print(ast)) == ast`
   Codec: `decompress(compress(x)) == x`

2. **Invariant(守恒)**
   `len(sort(xs)) == len(xs)`
   `multiset(sort(xs)) == multiset(xs)`
   排序后元素个数不变、总和不变

3. **Idempotence(幂等)**
   `f(f(x)) == f(x)`
   normalize、strip、DELETE 请求、ETL 重跑

4. **Metamorphic(变换关系)**
   输入做已知变换,输出做已知变换
   `sort(reverse(xs)) == sort(xs)`

5. **Model-based oracle(参照对拍)**
   和一个慢但正确的参考实现对拍
   **有参考实现时,差分测试永远是第一选择**

工具：Hypothesis(Python)、QuickCheck(Haskell)、
fast-check(JS)、Schemathesis(API)

### 第 4 步：软指标硬化

把软要求拆成硬子条件的 **AND 组合**（不是加权和）。

| 软要求 | 硬化为 |
|--------|--------|
| 代码质量好 | ESLint 零警告 AND mypy --strict 通过 AND 圈复杂度 ≤ 10 AND 重复率 < 3% |
| 性能好 | Lighthouse ≥ 90 AND LCP < 2.5s AND bundle < 170KB |
| 文档完整 | 每个 public API 有 docstring AND doctest 全过 AND 零死链 |
| 安全 | Semgrep OWASP 过 AND pip-audit 无 high AND gitleaks 零命中 |
| 测试有效 | 覆盖 ≥ 90% AND mutation score ≥ 75% AND 每个测试 ≥ 1 个非平凡 assert |

**为什么 AND 不是加权？** 加权会被 agent 用拉高一个指标掩盖另一个的方式绕过。

实在没法硬化的（创意、美学）：
- LLM-as-judge + 固定 rubric + 多采样取中位数（"半硬判据"）
- 配合行为型硬指标兜底

### 第 5 步：防作弊自检

写完 criteria 后,花 5 分钟扮演想偷懒的 agent：

| 作弊方式 | 防御 |
|----------|------|
| 硬编码 `if input == test1: return expected1` | 用随机生成大量输入,不固定 |
| `try: ... except: pass` 吞异常 | 加异常路径测试 |
| 改测试文件 | frozen_files + git diff 检查 |
| `sys.exit(0)` | runner assert `len(tests) >= N` |
| monkey-patch 计时器 | 用外部 `hyperfine` |
| 只过 public test | hidden test 在独立容器 |
| 删 fixture | fixture 目录 chmod 555 |

想到的每种偷懒方式,都补一条防御。

## 反向指标（Goodhart 护栏）

为主指标配至少一个反向指标：
- 主指标升 + 反向指标降 = 报警
- 例：通过率 ↑ + 回复长度 ≤ 基线 1.5 倍
- 例：性能 ↑ + 测试通过率 = 100%
- 例：覆盖率 ↑ + mutation score ≥ 75%

每个指标过四种失效模式：
回归性（优化噪声？）、极端性（推到极端还有效？）、
因果性（因果还是相关？）、对抗性（agent 怎么钻空子？）

## 各任务类型的 Criteria 要点

| 任务类型 | 核心硬判据 | 首选评估方式 | 关键防作弊 |
|----------|-----------|-------------|-----------|
| 编译器/解释器 | 差分 vs 官方实现 + fuzz 30min 零 crash | differential testing | 随机生成程序,不用固定用例 |
| Web API | OpenAPI spec + schemathesis + 认证/并发套件 | property-based | 反向测试(invalid token 等) |
| 数据 ETL | schema 匹配 + 行数相等 + 列级 checksum + 幂等 | Great Expectations | 同时断言其他 batch 不受影响 |
| 库/SDK | mypy strict + 90% 覆盖 + 75% mutation + semver | mutation testing | API surface AST 比对 |
| 文档 | Sphinx -W + doctest + linkcheck + Vale | 多工具交叉 | 每页最小字数 + 必须含示例 |
| Bug 修复 | regression test 在旧 commit 失败/新 commit 通过 | git bisect 验证 | 禁改已有测试 + 最小修改原则 |
| 测试套件 | 90% 覆盖 + 80% mutation + 断言密度 ≥ 1.5 | mutation testing | 禁空测试 + 禁平凡断言 |
| 性能优化 | 输出 byte-identical + 多 size benchmark + hyperfine | 外部 wall-clock | 禁特殊 fast-path + 精度不降 |
| 安全审计 | Semgrep + CodeQL + DAST + payload 套件 | SAST + DAST 交叉 | 禁 nosec 注释 + 全仓扫描 |

## Criteria 质量检查清单

写完后对着过一遍：

**目标澄清**
- [ ] 写了"看着好但其实不行"的反例
- [ ] Litmus test 通过(criteria 全过 → 目标必然达成)

**结构**
- [ ] 每条有 Given / When / Then / Invariant
- [ ] Safety + Liveness 都覆盖
- [ ] Criteria 只约束输出性质,不约束解题方法

**量化**
- [ ] 对着 5 大 property 模式套过
- [ ] 有参考实现就用差分测试
- [ ] 随机输入 seed 固定

**硬化**
- [ ] 软要求拆成硬子条件 AND 组合
- [ ] 有反向指标

**防作弊**
- [ ] frozen_files 列表完整
- [ ] 写了 inoculation prompt
- [ ] 做了 5 分钟作弊扮演

**终止**
- [ ] done_when 三个条件有具体数值
- [ ] 分了 P0/P1/P2 层级
- [ ] 拆了 Milestone
