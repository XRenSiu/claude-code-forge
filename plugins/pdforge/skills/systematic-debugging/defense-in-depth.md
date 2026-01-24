# Defense in Depth（多层验证策略）

> systematic-debugging Skill 的支持文档

---

## 核心原则

**不要假设上游已经验证，每层都要自我保护**

当一个 bug 穿透到达你的代码时，问题往往是因为某一层假设"前面已经检查过了"。

---

## 多层验证架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户输入                                │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 输入验证 (API Gateway / Controller)               │
│           - 格式校验                                         │
│           - 类型检查                                         │
│           - 必填字段                                         │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 业务验证 (Service)                                │
│           - 业务规则                                         │
│           - 权限检查                                         │
│           - 状态一致性                                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: 数据层验证 (Repository / ORM)                     │
│           - 约束检查                                         │
│           - 引用完整性                                       │
│           - 唯一性验证                                       │
├─────────────────────────────────────────────────────────────┤
│                      数据存储                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 验证策略

### 1. 不要相信任何输入

```typescript
// ❌ 错误：假设输入已验证
function processUser(user: User) {
  return user.email.toLowerCase(); // 如果 email 是 undefined？
}

// ✅ 正确：自我保护
function processUser(user: User) {
  if (!user?.email) {
    throw new ValidationError('User email is required');
  }
  return user.email.toLowerCase();
}
```

### 2. 快速失败（Fail Fast）

```typescript
// 在函数开始处验证所有前置条件
function transferMoney(from: Account, to: Account, amount: number) {
  // 前置条件检查 - 全部通过才继续
  if (!from) throw new Error('Source account required');
  if (!to) throw new Error('Destination account required');
  if (amount <= 0) throw new Error('Amount must be positive');
  if (from.id === to.id) throw new Error('Cannot transfer to same account');
  if (from.balance < amount) throw new Error('Insufficient balance');
  
  // 所有验证通过，执行业务逻辑
  // ...
}
```

### 3. 边界条件检查

```typescript
// 检查所有边界条件
function getItem(array: any[], index: number) {
  if (!Array.isArray(array)) {
    throw new TypeError('Expected array');
  }
  if (index < 0 || index >= array.length) {
    throw new RangeError(`Index ${index} out of bounds [0, ${array.length})`);
  }
  return array[index];
}
```

### 4. 类型守卫

```typescript
// 使用类型守卫确保类型安全
function isUser(obj: unknown): obj is User {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'email' in obj
  );
}

function processResponse(data: unknown) {
  if (!isUser(data)) {
    throw new Error('Invalid user data');
  }
  // 现在 TypeScript 知道 data 是 User 类型
  return data.email;
}
```

---

## 验证清单

```markdown
□ 函数开头检查所有参数
□ 空值/undefined 有明确处理
□ 数组访问前检查边界
□ 对象属性访问前检查存在性
□ 数值计算前检查有效性（NaN, Infinity）
□ 字符串操作前检查非空
□ 外部调用结果有错误处理
```

---

## 调试时的验证追踪

当追踪 bug 时，检查每一层的验证：

```bash
# 找到所有验证代码
grep -rn "throw\|assert\|validate\|check" --include="*.ts" src/

# 找到可能缺少验证的模式
grep -rn "\.length\|\.map\|\.filter" --include="*.ts" src/ | \
  grep -v "if\|?\.\|&&"  # 找出没有保护的数组操作
```

---

## 常见漏洞模式

| 漏洞 | 防御 |
|------|------|
| `undefined.property` | 可选链 `?.` 或前置检查 |
| `array[index]` 越界 | 边界检查 |
| 空数组 `.map()` | 空数组是安全的，但注意 `.reduce()` 需要初始值 |
| `parseInt()` 返回 NaN | `isNaN()` 检查 |
| `JSON.parse()` 失败 | try-catch 包装 |
| 异步结果未等待 | 确保 `await` |
