# Testing Rules

**来源**: PDForge
**类型**: 约束规范

---

## Coverage Requirements

### 1→100 产品（生产级）

```yaml
coverage:
  statements: 80%    # 硬性要求
  branches: 75%      # 分支覆盖
  functions: 80%     # 函数覆盖
  lines: 80%         # 行覆盖
```

### 0→1 产品（MVP）

```yaml
coverage:
  statements: 50%    # 核心路径
  branches: 40%      # 主要分支
  functions: 50%     # 关键函数
  lines: 50%         # 主要代码
```

## Test Organization

### Directory Structure

```
src/
├── services/
│   └── user.ts
└── __tests__/           # 或 tests/
    └── services/
        └── user.test.ts
```

Or co-located:

```
src/
└── services/
    ├── user.ts
    └── user.test.ts     # 与源文件同目录
```

### Naming Convention

| 源文件 | 测试文件 |
|--------|----------|
| `user.ts` | `user.test.ts` 或 `user.spec.ts` |
| `UserService.ts` | `UserService.test.ts` |
| `auth.controller.ts` | `auth.controller.test.ts` |

## Test Structure

### AAA Pattern (Arrange-Act-Assert)

```typescript
describe('UserService', () => {
  describe('register', () => {
    it('should create user with hashed password', async () => {
      // Arrange
      const userData = {
        email: 'test@example.com',
        password: 'password123'
      };
      
      // Act
      const result = await userService.register(userData);
      
      // Assert
      expect(result.email).toBe('test@example.com');
      expect(result.password).not.toBe('password123');
    });
  });
});
```

### Test Naming

```typescript
// ✅ Good: 描述行为
it('should reject registration with invalid email format')
it('should return 401 when token is expired')
it('should hash password before storing')

// ❌ Bad: 测试实现
it('should call bcrypt.hash')
it('should set user.password')
it('test register')
```

## What to Test

### Must Test

| 类型 | 说明 | 覆盖率要求 |
|------|------|-----------|
| 业务逻辑 | 核心功能 | 90%+ |
| API 端点 | 请求/响应 | 80%+ |
| 数据验证 | 输入校验 | 100% |
| 错误处理 | 异常情况 | 80%+ |
| 边界条件 | 极端情况 | 80%+ |

### Should Test

| 类型 | 说明 | 覆盖率要求 |
|------|------|-----------|
| 工具函数 | Utils/Helpers | 70%+ |
| 数据转换 | Mappers/Transformers | 70%+ |
| 中间件 | Middleware | 70%+ |

### May Skip

| 类型 | 说明 | 原因 |
|------|------|------|
| 配置文件 | Config | 简单，风险低 |
| 类型定义 | Types/Interfaces | 编译时检查 |
| 常量 | Constants | 不包含逻辑 |

## Test Types

### Unit Tests

```typescript
// 隔离测试，mock 依赖
describe('UserService', () => {
  let userService: UserService;
  let mockUserRepo: jest.Mocked<UserRepository>;
  
  beforeEach(() => {
    mockUserRepo = {
      create: jest.fn(),
      findByEmail: jest.fn(),
    };
    userService = new UserService(mockUserRepo);
  });
  
  it('should create user', async () => {
    mockUserRepo.create.mockResolvedValue({ id: '1', email: 'test@test.com' });
    
    const result = await userService.register({ email: 'test@test.com', password: '123' });
    
    expect(result.id).toBe('1');
    expect(mockUserRepo.create).toHaveBeenCalledTimes(1);
  });
});
```

### Integration Tests

```typescript
// 测试多个组件协作
describe('Auth API', () => {
  let app: Express;
  
  beforeAll(async () => {
    app = await createTestApp();
  });
  
  it('should register and login user', async () => {
    // Register
    const registerRes = await request(app)
      .post('/api/auth/register')
      .send({ email: 'test@test.com', password: '123456' });
    expect(registerRes.status).toBe(201);
    
    // Login
    const loginRes = await request(app)
      .post('/api/auth/login')
      .send({ email: 'test@test.com', password: '123456' });
    expect(loginRes.status).toBe(200);
    expect(loginRes.body.token).toBeDefined();
  });
});
```

### E2E Tests

```typescript
// 端到端测试（完整流程）
describe('User Registration Flow', () => {
  it('should complete registration flow', async () => {
    // 1. Visit registration page
    await page.goto('/register');
    
    // 2. Fill form
    await page.fill('[name="email"]', 'test@test.com');
    await page.fill('[name="password"]', '123456');
    
    // 3. Submit
    await page.click('[type="submit"]');
    
    // 4. Verify redirect
    await expect(page).toHaveURL('/dashboard');
  });
});
```

## Test Quality Rules

### ✅ Do

- 测试行为，不是实现
- 每个测试一个断言主题
- 使用有意义的测试数据
- 清理测试状态
- 使用 describe 分组

### ❌ Don't

- 测试私有方法
- 依赖测试执行顺序
- 使用硬编码延迟 (sleep)
- 共享可变状态
- 忽略异步错误

## Coverage Enforcement

### Jest Configuration

```javascript
// jest.config.js
module.exports = {
  collectCoverage: true,
  coverageThreshold: {
    global: {
      statements: 80,
      branches: 75,
      functions: 80,
      lines: 80,
    },
  },
  coverageReporters: ['text', 'lcov', 'html'],
};
```

### CI/CD Gate

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: npm test -- --coverage --coverageReporters=text-summary
  
- name: Check Coverage
  run: |
    COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.statements.pct')
    if (( $(echo "$COVERAGE < 80" | bc -l) )); then
      echo "Coverage $COVERAGE% is below 80%"
      exit 1
    fi
```

## Common Patterns

### Testing Async Code

```typescript
// ✅ Good: await + expect
it('should fetch user', async () => {
  const user = await userService.getById('1');
  expect(user.name).toBe('John');
});

// ✅ Good: expect + rejects
it('should throw on invalid id', async () => {
  await expect(userService.getById('invalid'))
    .rejects.toThrow('User not found');
});
```

### Testing Errors

```typescript
// ✅ Good: 测试错误类型和消息
it('should throw ValidationError for invalid email', async () => {
  await expect(userService.register({ email: 'invalid' }))
    .rejects.toThrow(ValidationError);
  
  await expect(userService.register({ email: 'invalid' }))
    .rejects.toThrow('Invalid email format');
});
```

### Testing with Time

```typescript
// ✅ Good: 使用 fake timers
it('should expire after 1 hour', () => {
  jest.useFakeTimers();
  
  const token = createToken();
  expect(token.isValid()).toBe(true);
  
  jest.advanceTimersByTime(60 * 60 * 1000 + 1);
  expect(token.isValid()).toBe(false);
  
  jest.useRealTimers();
});
```

## Verification Commands

```bash
# 运行所有测试
npm test

# 运行特定测试
npm test -- --grep "UserService"

# 运行并显示覆盖率
npm test -- --coverage

# 监视模式
npm test -- --watch

# 只运行失败的测试
npm test -- --onlyFailures
```
