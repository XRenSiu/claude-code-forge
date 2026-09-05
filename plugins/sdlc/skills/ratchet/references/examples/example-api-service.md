# REST API Todo Service — Ratchet 实验协议

> Schema 验证 + property-based testing + 独立评估脚本示例

## Goal

用 Node.js + Express 实现一个 Todo CRUD API,
符合给定的 OpenAPI spec,通过全部 property-based 测试。

## Criteria

### P0 (Must)

1. schemathesis 对 openapi.yaml 跑 `--checks all` 零 failure
2. 所有 CRUD 端点返回正确 status code + response schema
3. 认证套件:无 token/过期 token/他人 token 各返回正确错误码
4. 并发写入:10 并发 POST 不丢数据不重复 ID

### P1 (Should)

1. 幂等性:同一 PUT 请求发两次结果一致
2. p99 延迟 < 50ms（wrk 100 并发 10 秒）
3. 错误响应包含 `error.code` 和 `error.message`

### Invariants

- `npm test` 全部通过
- 无 N+1 查询（检测方式:日志中单请求 SQL 数 ≤ 3）
- 不引入新 npm 依赖（package.json frozen）

## done_when

```yaml
success: "P0 #1-#4 全部通过 AND invariant 全保持"
convergence: "连续 10 轮无改善"
budget: "总轮次 >= 50"
```

## Milestones

```
M1 Skeleton:  GET /todos 返回 200 + 空数组
M2 CRUD:      POST/GET/PUT/DELETE 基本流程通
M3 Schema:    schemathesis --checks all 通过率 ≥ 80%
M4 Auth:      认证套件全过
M5 Complete:  schemathesis 100% + 并发测试过
```

## Scope

### CAN
- 修改 src/ 下所有文件
- 修改 database schema（migration 文件）
- 添加新的 middleware

### CANNOT
- 不得修改 evaluate.sh
- 不得修改 openapi.yaml
- 不得修改 test_data/auth_payloads.json
- 不得修改 package.json（不加新依赖）
- 不得修改 results.tsv 已有记录

### Anti-Cheat
- 不许修改 OpenAPI spec 来让实现"符合"规范
- 不许在路由中硬编码测试 payload 的期望响应
- 不许 mock 数据库来通过并发测试
- 不许 try/catch 吞异常返回 200

## 评估方式: 模式 A

**evaluate.sh**:

```bash
#!/bin/bash
set -euo pipefail

pass=0; fail=0; milestone="M1"

# 启动服务（后台）
npm start &
SERVER_PID=$!
sleep 3
trap "kill $SERVER_PID 2>/dev/null" EXIT

# ── Invariant: npm test ──
npm test --silent && ((pass++)) || ((fail++))

# ── M1: GET /todos ──
status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/todos)
[[ "$status" == "200" ]] && milestone="M2" || true

# ── M2-M3: Schemathesis ──
schema_result=$(schemathesis run openapi.yaml \
  --base-url http://localhost:3000 \
  --checks all \
  --hypothesis-max-examples 200 \
  --report 2>&1)
schema_failures=$(echo "$schema_result" | grep -c "FAILED" || echo "0")
schema_total=$(echo "$schema_result" | grep -c "PASSED\|FAILED" || echo "1")
schema_rate=$(echo "scale=4; ($schema_total - $schema_failures) / $schema_total" | bc)

[[ $(echo "$schema_rate >= 0.80" | bc) -eq 1 ]] && milestone="M3"
[[ $(echo "$schema_rate >= 1.00" | bc) -eq 1 ]] && { ((pass++)); milestone="M4"; } || ((fail++))

# ── M4: Auth ──
auth_pass=0; auth_total=3
# 无 token
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/todos -X POST \
  -H "Content-Type: application/json" -d '{"title":"test"}' | grep -q "401" && ((auth_pass++))
# 过期 token
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/todos \
  -H "Authorization: Bearer expired_token_xxx" | grep -q "401" && ((auth_pass++))
# 他人 token
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/todos/1 -X DELETE \
  -H "Authorization: Bearer other_user_token" | grep -q "403" && ((auth_pass++))

[[ $auth_pass -eq $auth_total ]] && { ((pass++)); milestone="M5"; } || ((fail++))

# ── M5: 并发 ──
# 10 并发 POST,检查最终数量
for i in $(seq 1 10); do
  curl -s -X POST http://localhost:3000/todos \
    -H "Authorization: Bearer valid_token" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"concurrent-$i\"}" &
done
wait
count=$(curl -s http://localhost:3000/todos -H "Authorization: Bearer valid_token" | jq length)
[[ "$count" -ge 10 ]] && ((pass++)) || ((fail++))

# ── 汇总 ──
total=$((pass + fail))
score=$(echo "scale=4; $pass / $total" | bc)
echo "SCORE=$score PASS=$pass FAIL=$fail MILESTONE=$milestone"
```
