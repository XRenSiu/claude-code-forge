# Rust JSON Parser — Ratchet 实验协议

> 差分测试 + fuzz + milestone 递进示例

## Goal

用 Rust 实现一个完整的 JSON parser 库,支持 RFC 8259 全部语法,
性能不低于 serde_json 的 70%。

## Criteria

### P0 (Must)

1. JSONTestSuite 的 y_*.json（合法输入）100% 解析成功
2. JSONTestSuite 的 n_*.json（非法输入）100% 返回错误不 panic
3. 与 serde_json 差分对拍：10,000 个随机生成的合法 JSON,
   `our_parse(s) == serde_json::from_str(s)` 全部一致
4. cargo-fuzz 跑 30 分钟零 crash

### P1 (Should)

1. i_*.json（实现自定义）行为合理且有文档说明
2. 错误信息包含行号和列号
3. 公共 API 100% 有 doc comment

### P2 (Could)

1. 吞吐 ≥ serde_json × 0.7（criterion benchmark）

### Invariants

- `cargo test` 全部通过（包括已有测试）
- `cargo clippy -- -D warnings` 零警告
- 不引入 unsafe 代码
- 不引入除 dev-dependencies 外的新依赖

## done_when

```yaml
success: "P0 #1-#4 全部通过 AND 所有 invariant 保持"
convergence: "连续 15 轮 best_score 无改善"
budget: "总轮次 >= 80"
```

## Milestones

```
M1 Tokenizer: 能 tokenize null/true/false/数字/字符串,50 个 tokenizer 单测过
M2 Parser:    JSONTestSuite y_*.json 通过率 ≥ 80%
M3 Error:     n_*.json 100% 返回错误不 panic
M4 Diff:      与 serde_json 差分对拍 10,000 个随机 JSON 全部一致
M5 Fuzz:      cargo-fuzz 30 分钟零 crash
M6 Polish:    P1 criteria + clippy clean
```

## Scope

### CAN
- 创建和修改 src/ 下所有 Rust 文件
- 添加 dev-dependencies（测试/benchmark 用）
- 创建 tests/ 目录下的集成测试
- 创建 fuzz/ 目录

### CANNOT
- 不得修改 evaluate.sh
- 不得修改 test_data/（JSONTestSuite 文件）
- 不得修改 results.tsv 已有记录
- 不得引入 unsafe 代码
- 不得引入非 dev 的新依赖

### Anti-Cheat
- 不许硬编码 JSONTestSuite 的期望输出
- 不许跳过或注释掉任何测试文件
- 不许修改 JSONTestSuite 的测试数据
- 不许 `process::exit(0)` 伪造退出码
- 不许对 serde_json 做 monkey-patch

## 评估方式: 模式 A（独立脚本）

**evaluate.sh**:

```bash
#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

pass=0; fail=0; milestone="M1"

# ── Invariants ──
cargo test --quiet 2>/dev/null && ((pass++)) || ((fail++))
cargo clippy -- -D warnings 2>/dev/null && ((pass++)) || ((fail++))
# unsafe 检查
if grep -rn "unsafe" src/ --include="*.rs" | grep -v "// SAFETY:" | head -1; then
  ((fail++))
else
  ((pass++))
fi

# ── M1: Tokenizer ──
cargo test tokenizer --quiet 2>/dev/null && milestone="M2" || true

# ── M2: JSONTestSuite y_* ──
y_total=0; y_pass=0
for f in test_data/y_*.json; do
  ((y_total++))
  cargo run --quiet -- "$f" 2>/dev/null && ((y_pass++)) || true
done
y_rate=$(echo "scale=4; $y_pass / $y_total" | bc)
[[ $(echo "$y_rate >= 0.80" | bc) -eq 1 ]] && milestone="M3"
[[ $(echo "$y_rate >= 1.00" | bc) -eq 1 ]] && ((pass++)) || ((fail++))

# ── M3: JSONTestSuite n_* ──
n_total=0; n_reject=0
for f in test_data/n_*.json; do
  ((n_total++))
  cargo run --quiet -- "$f" 2>/dev/null && true || ((n_reject++))
done
n_rate=$(echo "scale=4; $n_reject / $n_total" | bc)
[[ $(echo "$n_rate >= 1.00" | bc) -eq 1 ]] && { ((pass++)); milestone="M4"; } || ((fail++))

# ── M4: 差分对拍 ──
cargo test differential -- --ignored --quiet 2>/dev/null && { ((pass++)); milestone="M5"; } || ((fail++))

# ── M5: Fuzz ──
if command -v cargo-fuzz &>/dev/null; then
  timeout 1800 cargo fuzz run parse -- -max_total_time=1800 2>/dev/null && { ((pass++)); milestone="M6"; } || ((fail++))
else
  echo "WARN: cargo-fuzz not installed, skipping"
fi

# ── 汇总 ──
total=$((pass + fail))
score=$(echo "scale=4; $pass / $total" | bc)
echo "SCORE=$score PASS=$pass FAIL=$fail MILESTONE=$milestone"
```

## Setup

1. 创建实验目录:
   ```bash
   mkdir -p /home/claude/ratchet-json-parser && cd /home/claude/ratchet-json-parser
   cargo init --lib
   ```
2. 下载 JSONTestSuite 到 test_data/（frozen）
3. 将 evaluate.sh 写入实验目录（frozen）
4. 初始化 results.tsv
5. 运行基线评估

## subagent_prompt

```
你是一个 Rust 工程师。你的唯一目标是：

用 Rust 实现一个完整的 JSON parser 库,支持 RFC 8259 全部语法。

你可以修改: src/ 下所有 Rust 文件,tests/ 目录,fuzz/ 目录,Cargo.toml(仅 dev-dependencies)
你不能修改: evaluate.sh, test_data/, results.tsv

防作弊: 不许硬编码测试期望输出、不许跳过测试、不许 process::exit(0)、不许修改测试数据

当前进度:
- 当前 Milestone: {milestone}
- 最佳评分: {best_score}
- 上一轮反馈: {failure_summary}
- 实验历史: {last_10_rows}

Milestones:
M1 Tokenizer → M2 Parser → M3 Error → M4 Diff → M5 Fuzz → M6 Polish
当前: {milestone}

工作方式:
1. 读取 src/ 和 tests/ 理解当前实现
2. 基于反馈制定本轮改进计划,每次只改一个方面
3. 改完 commit: git add -A && git commit -m "r{N}: {改了什么}"
4. 你不需要自己评估——有独立评估者判断
```
