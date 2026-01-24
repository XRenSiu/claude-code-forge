# Condition-Based Waiting（条件等待策略）

> systematic-debugging Skill 的支持文档

---

## 核心原则

**用条件轮询替代任意超时**

`setTimeout(1000)` 是测试中最常见的 bug 来源。1 秒在你的机器上够用，在 CI 慢速机器上不够，在快速机器上又浪费时间。

---

## 反模式 vs 正确模式

### ❌ 反模式：任意超时

```javascript
// 这会导致测试不稳定
test('should show success message', async () => {
  await submitForm();
  await new Promise(resolve => setTimeout(resolve, 1000)); // 为什么是 1000？
  expect(screen.getByText('Success')).toBeInTheDocument();
});
```

**问题**：
- 1000ms 是猜测，不是根据实际情况
- CI 机器慢时会失败
- 开发机器快时浪费时间
- 无法处理条件提前满足

### ✅ 正确模式：条件等待

```javascript
// 等待直到条件满足
test('should show success message', async () => {
  await submitForm();
  await waitFor(() => {
    expect(screen.getByText('Success')).toBeInTheDocument();
  });
});
```

---

## 条件等待实现

### 通用等待函数

```typescript
/**
 * 等待条件满足
 * @param condition 条件函数，返回 true 表示满足
 * @param options 配置选项
 */
async function waitForCondition(
  condition: () => boolean | Promise<boolean>,
  options: {
    timeout?: number;      // 最大等待时间（安全网）
    interval?: number;     // 轮询间隔
    message?: string;      // 超时错误消息
  } = {}
): Promise<void> {
  const {
    timeout = 5000,
    interval = 50,
    message = 'Condition not met within timeout'
  } = options;

  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    if (await condition()) {
      return;
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  
  throw new Error(`${message} (waited ${timeout}ms)`);
}
```

### 使用示例

```typescript
// 等待元素出现
await waitForCondition(
  () => document.querySelector('.success-message') !== null,
  { message: 'Success message did not appear' }
);

// 等待状态变化
await waitForCondition(
  () => store.getState().loading === false,
  { message: 'Loading did not complete' }
);

// 等待 API 响应
await waitForCondition(
  async () => {
    const response = await fetch('/api/status');
    const data = await response.json();
    return data.ready === true;
  },
  { timeout: 10000, message: 'API did not become ready' }
);
```

---

## 测试框架的内置等待

### Jest + Testing Library

```javascript
import { waitFor, waitForElementToBeRemoved } from '@testing-library/react';

// 等待元素出现
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});

// 等待元素消失
await waitForElementToBeRemoved(() => screen.queryByText('Loading...'));

// 带自定义超时
await waitFor(
  () => expect(screen.getByText('Data')).toBeInTheDocument(),
  { timeout: 3000 }
);
```

### Playwright

```javascript
// 自动等待元素可见
await page.click('.submit-button');

// 显式等待
await page.waitForSelector('.success-message');

// 等待条件
await page.waitForFunction(() => {
  return document.querySelector('.loading') === null;
});
```

### Cypress

```javascript
// 自动重试直到断言通过
cy.get('.success-message').should('be.visible');

// 等待请求完成
cy.intercept('POST', '/api/submit').as('submitRequest');
cy.get('.submit').click();
cy.wait('@submitRequest');
```

---

## 超时设置策略

```
┌─────────────────────────────────────────────────────────────┐
│                    超时层级                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  轮询间隔（interval）：10-100ms                              │
│  └── 太短会浪费 CPU，太长会增加总等待时间                     │
│                                                             │
│  单次操作超时（timeout）：1-10s                              │
│  └── 根据操作类型设置：UI 操作 1-3s，API 调用 5-10s          │
│                                                             │
│  测试超时（test timeout）：30s-2min                         │
│  └── 整个测试的安全网，远大于预期执行时间                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**经验法则**：
- `interval = 50ms`（默认）
- `timeout = 预期时间 × 10`（安全余量）
- `test timeout = 最长操作 × 3`

---

## 调试间歇性失败

当测试有时过有时失败时：

### 1. 增加日志

```typescript
async function waitForCondition(condition, options) {
  const startTime = Date.now();
  let attempts = 0;
  
  while (Date.now() - startTime < timeout) {
    attempts++;
    const result = await condition();
    console.log(`[WAIT] Attempt ${attempts}, result: ${result}, elapsed: ${Date.now() - startTime}ms`);
    
    if (result) {
      console.log(`[WAIT] Condition met after ${attempts} attempts`);
      return;
    }
    await sleep(interval);
  }
  
  console.log(`[WAIT] Timed out after ${attempts} attempts`);
  throw new Error(message);
}
```

### 2. 分析日志

```bash
# 找到等待时间最长的测试
grep "\[WAIT\] Condition met" test.log | sort -t: -k2 -n -r | head
```

### 3. 调整策略

- 如果接近超时：增加 timeout
- 如果总是第 1 次就成功：减少 interval
- 如果 attempts 很多：检查条件是否正确

---

## Checklist

```markdown
□ 没有使用 setTimeout 等待状态变化
□ 所有异步断言用 waitFor 包装
□ 超时时间有合理的安全余量
□ 轮询间隔不会过度消耗资源
□ 超时错误消息清晰说明等待什么
□ CI 上的测试运行时间稳定
```
