# Coding Style Rules

**来源**: PDForge
**类型**: 约束规范

---

## General Principles

1. **可读性优先** - 代码是写给人看的
2. **一致性** - 整个项目保持统一风格
3. **简单性** - 简单的代码比聪明的代码好
4. **明确性** - 显式优于隐式

## Naming Conventions

### Variables & Functions

| 类型 | 风格 | 示例 |
|------|------|------|
| 变量 | camelCase | `userName`, `totalCount` |
| 函数 | camelCase | `getUserById`, `calculateTotal` |
| 常量 | SCREAMING_SNAKE_CASE | `MAX_RETRY`, `API_BASE_URL` |
| 布尔变量 | is/has/can 前缀 | `isActive`, `hasPermission`, `canEdit` |

### Classes & Types

| 类型 | 风格 | 示例 |
|------|------|------|
| 类 | PascalCase | `UserService`, `AuthController` |
| 接口 | PascalCase (无 I 前缀) | `User`, `ApiResponse` |
| 类型 | PascalCase | `CreateUserInput`, `UserRole` |
| 枚举 | PascalCase | `UserStatus`, `OrderState` |
| 枚举值 | SCREAMING_SNAKE_CASE | `PENDING`, `COMPLETED` |

### Files & Directories

| 类型 | 风格 | 示例 |
|------|------|------|
| 文件 | kebab-case | `user-service.ts`, `auth-controller.ts` |
| 目录 | kebab-case | `user-management/`, `error-handling/` |
| 组件文件 | PascalCase | `UserProfile.tsx`, `LoginForm.tsx` |
| 测试文件 | 源文件名 + .test/.spec | `user-service.test.ts` |

## TypeScript Rules

### Type Safety

```typescript
// ✅ Good: 明确的类型
function getUser(id: string): Promise<User> {
  return userRepository.findById(id);
}

// ❌ Bad: 使用 any
function getUser(id: any): any {
  return userRepository.findById(id);
}
```

### Prefer Interfaces for Objects

```typescript
// ✅ Good: 对象用 interface
interface User {
  id: string;
  email: string;
  name: string;
}

// ✅ Good: 联合类型用 type
type UserRole = 'admin' | 'user' | 'guest';

// ✅ Good: 函数类型用 type
type CreateUserFn = (data: CreateUserInput) => Promise<User>;
```

### Null Handling

```typescript
// ✅ Good: 使用可选链和空值合并
const userName = user?.name ?? 'Anonymous';

// ❌ Bad: 隐式假设非空
const userName = user.name; // 可能崩溃

// ✅ Good: 类型守卫
if (user) {
  console.log(user.name);
}
```

### Avoid Type Assertions

```typescript
// ✅ Good: 类型守卫
function isUser(obj: unknown): obj is User {
  return typeof obj === 'object' && obj !== null && 'email' in obj;
}

// ❌ Bad: 强制断言
const user = data as User; // 危险
```

## Code Structure

### Function Length

- **推荐**: < 30 行
- **最大**: 50 行
- 超过则考虑拆分

### Nesting Depth

- **推荐**: < 3 层
- **最大**: 4 层
- 使用早返回减少嵌套

```typescript
// ✅ Good: 早返回
function processUser(user: User | null) {
  if (!user) return;
  if (!user.isActive) return;
  
  // 主逻辑
  doSomething(user);
}

// ❌ Bad: 深层嵌套
function processUser(user: User | null) {
  if (user) {
    if (user.isActive) {
      // 主逻辑
      doSomething(user);
    }
  }
}
```

### Function Parameters

- **推荐**: < 3 个参数
- **最大**: 4 个参数
- 超过则使用对象参数

```typescript
// ✅ Good: 对象参数
interface CreateUserOptions {
  email: string;
  name: string;
  role?: UserRole;
  department?: string;
}

function createUser(options: CreateUserOptions): Promise<User> {
  // ...
}

// ❌ Bad: 过多参数
function createUser(
  email: string, 
  name: string, 
  role: UserRole, 
  department: string
): Promise<User> {
  // ...
}
```

## Error Handling

### Always Handle Errors

```typescript
// ✅ Good: 处理错误
try {
  await userService.createUser(data);
} catch (error) {
  if (error instanceof ValidationError) {
    return res.status(400).json({ error: error.message });
  }
  logger.error('Failed to create user', { error, data });
  return res.status(500).json({ error: 'Internal server error' });
}

// ❌ Bad: 忽略错误
try {
  await userService.createUser(data);
} catch (error) {
  // 空的 catch 块
}
```

### Custom Error Classes

```typescript
// ✅ Good: 自定义错误类
class ValidationError extends Error {
  constructor(
    message: string,
    public readonly field: string
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

class NotFoundError extends Error {
  constructor(resource: string, id: string) {
    super(`${resource} with id ${id} not found`);
    this.name = 'NotFoundError';
  }
}
```

### Async Error Handling

```typescript
// ✅ Good: Promise 错误处理
async function getUser(id: string): Promise<User> {
  const user = await userRepository.findById(id);
  if (!user) {
    throw new NotFoundError('User', id);
  }
  return user;
}

// 调用处
try {
  const user = await getUser('123');
} catch (error) {
  if (error instanceof NotFoundError) {
    // 处理未找到
  }
  throw error; // 重新抛出其他错误
}
```

## Comments & Documentation

### When to Comment

```typescript
// ✅ Good: 解释"为什么"
// 使用延迟删除是因为外部系统需要 24 小时同步周期
await scheduleDelete(user.id, { delay: '24h' });

// ❌ Bad: 解释"是什么"（代码已经说明）
// 获取用户
const user = await getUser(id);
```

### JSDoc for Public APIs

```typescript
/**
 * 创建新用户
 * 
 * @param data - 用户创建数据
 * @returns 创建的用户对象
 * @throws {ValidationError} 当 email 格式无效时
 * @throws {ConflictError} 当 email 已存在时
 * 
 * @example
 * const user = await createUser({
 *   email: 'user@example.com',
 *   name: 'John Doe'
 * });
 */
async function createUser(data: CreateUserInput): Promise<User> {
  // ...
}
```

## Import Organization

### Order

```typescript
// 1. 第三方库
import { Router } from 'express';
import { z } from 'zod';

// 2. 内部模块 (绝对路径)
import { UserService } from '@/services/user';
import { logger } from '@/utils/logger';

// 3. 相对路径导入
import { validateEmail } from './validators';
import { UserDTO } from './types';
```

### Naming

```typescript
// ✅ Good: 清晰的导入
import { UserService } from './services/user';
import type { User, CreateUserInput } from './types';

// ❌ Bad: 默认导出配合模糊名称
import userStuff from './services/user';
```

## Formatting

### Prettier Configuration

```json
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "bracketSpacing": true,
  "arrowParens": "always"
}
```

### ESLint Configuration

```javascript
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'prettier',
  ],
  rules: {
    'no-console': 'warn',
    'no-unused-vars': 'off',
    '@typescript-eslint/no-unused-vars': 'error',
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-explicit-any': 'error',
    'prefer-const': 'error',
  },
};
```

## Code Smells to Avoid

### 🚩 God Objects

```typescript
// ❌ Bad: 类做太多事
class UserManager {
  createUser() {}
  updateUser() {}
  deleteUser() {}
  sendEmail() {}       // 不相关
  generateReport() {}   // 不相关
  processPayment() {}   // 不相关
}

// ✅ Good: 单一职责
class UserService {
  createUser() {}
  updateUser() {}
  deleteUser() {}
}

class EmailService {
  sendEmail() {}
}
```

### 🚩 Magic Numbers

```typescript
// ❌ Bad
if (user.age > 18) { }
if (retryCount > 3) { }

// ✅ Good
const LEGAL_AGE = 18;
const MAX_RETRIES = 3;

if (user.age > LEGAL_AGE) { }
if (retryCount > MAX_RETRIES) { }
```

### 🚩 Boolean Parameters

```typescript
// ❌ Bad: 调用时不清楚含义
processOrder(order, true, false);

// ✅ Good: 使用对象
processOrder(order, { urgent: true, notifyCustomer: false });
```

## Verification Commands

```bash
# 检查类型
npx tsc --noEmit

# 运行 linter
npx eslint .

# 格式化检查
npx prettier --check .

# 自动修复
npx eslint . --fix
npx prettier --write .
```
