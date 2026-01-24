# Root Cause Tracing（根因追踪技术）

> systematic-debugging Skill 的支持文档

---

## 核心原则

**追踪调用栈，而非猜测原因**

当你看到一个错误时，不要猜"可能是 X 导致的"——追踪代码执行路径，让证据告诉你答案。

---

## 追踪技术

### 1. 堆栈追踪分析

```javascript
// 当捕获错误时，总是记录完整堆栈
try {
  riskyOperation();
} catch (error) {
  console.error('Full stack trace:', error.stack);
  throw error;
}
```

**阅读堆栈的正确方式**：
1. 从**最上面**开始——这是错误发生的直接位置
2. 向下追踪——找到**你的代码**（跳过框架/库代码）
3. 找到**状态转变点**——数据在哪里从"正确"变成"错误"

### 2. 数据流追踪

```javascript
// 在关键点记录数据状态
function processOrder(order) {
  console.log('[TRACE] processOrder input:', JSON.stringify(order));
  
  const validated = validateOrder(order);
  console.log('[TRACE] after validation:', JSON.stringify(validated));
  
  const calculated = calculateTotal(validated);
  console.log('[TRACE] after calculation:', JSON.stringify(calculated));
  
  return calculated;
}
```

**追踪模板**：
```
[TRACE] <函数名> <阶段>: <关键数据>
```

### 3. 条件断点（调试器）

```javascript
// 在代码中添加条件断点
if (suspiciousCondition) {
  debugger; // 只在可疑条件下暂停
}
```

### 4. 执行路径标记

```javascript
const executionPath = [];

function funcA() {
  executionPath.push('funcA:entry');
  // ...
  executionPath.push('funcA:exit');
}

function funcB() {
  executionPath.push('funcB:entry');
  // ...
  executionPath.push('funcB:exit');
}

// 错误发生时
console.log('Execution path:', executionPath.join(' -> '));
```

---

## 追踪检查清单

```markdown
□ 我有完整的错误堆栈
□ 我标记了数据在每个关键点的状态
□ 我知道数据在哪个点从"正确"变成"错误"
□ 我能复现问题并看到一致的追踪输出
□ 我没有猜测，而是用证据定位
```

---

## 常见陷阱

| 陷阱 | 正确做法 |
|------|----------|
| 只看错误消息，不看堆栈 | 阅读完整堆栈，追踪到你的代码 |
| 在框架代码中找原因 | 找到你的代码中传入的参数 |
| 猜测"可能是这里" | 添加追踪日志验证 |
| 修改代码同时追踪 | 先追踪确定，再修改 |

---

## 清理

**追踪完成后，删除所有调试代码**：

```bash
# 找到所有调试代码
grep -rn "\[TRACE\]\|console.log\|debugger" --include="*.ts" src/ | grep -v ".test.ts"

# 确保没有遗留
git diff --name-only | xargs grep -l "TRACE\|debugger"
```
