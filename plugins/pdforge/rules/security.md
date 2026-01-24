# Security Rules

安全约束红线规则。所有代码生成和审查必须遵守这些规则。

**优先级**：这些规则是**不可协商的红线**，违反任何一条都是阻塞性问题。

---

## 🔴 绝对禁止（Zero Tolerance）

这些行为在任何情况下都不允许：

### 1. 硬编码凭证

```typescript
// ❌ 绝对禁止
const API_KEY = "sk-1234567890abcdef";
const password = "admin123";
const connectionString = "mongodb://user:pass@host/db";

// ✅ 正确做法
const API_KEY = process.env.API_KEY;
const connectionString = process.env.DATABASE_URL;
```

**检测方法**：
```bash
grep -rn "password\s*=\s*['\"]" --include="*.ts" | grep -v "test\|spec\|example"
grep -rn "api_key\|apiKey\|secret\|token" --include="*.ts" | grep "=\s*['\"]"
```

### 2. SQL 注入

```typescript
// ❌ 绝对禁止
const query = `SELECT * FROM users WHERE id = ${userId}`;
db.query(`DELETE FROM orders WHERE id = '${orderId}'`);

// ✅ 正确做法
const query = "SELECT * FROM users WHERE id = ?";
db.query(query, [userId]);
// 或使用 ORM
await User.findByPk(userId);
```

**检测方法**：
```bash
grep -rn "query\s*(\s*['\`]" --include="*.ts" | grep "\${"
grep -rn "execute\s*(\s*['\`]" --include="*.ts" | grep "\${"
```

### 3. 命令注入

```typescript
// ❌ 绝对禁止
exec(`ls ${userInput}`);
spawn('sh', ['-c', `echo ${userInput}`]);

// ✅ 正确做法
// 使用参数数组，不用 shell
execFile('ls', [validatedPath]);
// 或使用白名单验证
if (ALLOWED_COMMANDS.includes(command)) {
  execFile(command, args);
}
```

**检测方法**：
```bash
grep -rn "exec\|spawn\|execSync" --include="*.ts" | grep "\${"
```

### 4. eval() 和 Function()

```typescript
// ❌ 绝对禁止
eval(userInput);
new Function(userCode)();

// ✅ 如果必须动态执行（极罕见），使用沙箱
import { VM } from 'vm2';
const vm = new VM({ sandbox: {} });
vm.run(untrustedCode);
```

**检测方法**：
```bash
grep -rn "eval\s*(" --include="*.ts"
grep -rn "new\s*Function\s*(" --include="*.ts"
```

### 5. 敏感数据暴露到日志

```typescript
// ❌ 绝对禁止
console.log("User logged in:", { username, password });
logger.info(`Payment processed: ${creditCardNumber}`);

// ✅ 正确做法
console.log("User logged in:", { username, password: "[REDACTED]" });
logger.info("Payment processed", { last4: creditCard.slice(-4) });
```

**检测方法**：
```bash
grep -rn "console.log\|logger\." --include="*.ts" | grep -i "password\|token\|secret\|credit"
```

---

## 🟠 必须遵守（Mandatory Requirements）

### 1. 输入验证

所有外部输入**必须**验证：

```typescript
// ✅ 必须验证
import { z } from 'zod';

const UserSchema = z.object({
  email: z.string().email(),
  age: z.number().min(0).max(150),
  role: z.enum(['user', 'admin'])
});

function createUser(input: unknown) {
  const validated = UserSchema.parse(input); // 抛出错误如果无效
  // 使用 validated...
}
```

**检测方法**：
```bash
# 查找是否有验证库
grep -rn "zod\|yup\|joi\|validator" --include="*.ts" | head -5

# 查找直接使用 req.body 的地方
grep -rn "req.body\." --include="*.ts" | grep -v "validate\|parse\|schema"
```

### 2. 密码存储

密码**必须**使用强哈希：

```typescript
// ✅ 必须使用
import bcrypt from 'bcrypt';

const SALT_ROUNDS = 12;

async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}
```

**可接受的哈希算法**：
- ✅ bcrypt (推荐)
- ✅ argon2
- ✅ scrypt
- ❌ SHA-256 (太快，易被暴力破解)
- ❌ MD5 (已破解)

**检测方法**：
```bash
# 应该找到 bcrypt/argon2
grep -rn "bcrypt\|argon2\|scrypt" --include="*.ts"

# 不应该用于密码的算法
grep -rn "md5\|sha1\|sha256" --include="*.ts" | grep -i "password"
```

### 3. HTTPS / TLS

生产环境**必须**使用 HTTPS：

```typescript
// ✅ 必须配置
// 在入口文件
if (process.env.NODE_ENV === 'production') {
  app.use((req, res, next) => {
    if (!req.secure) {
      return res.redirect(`https://${req.headers.host}${req.url}`);
    }
    next();
  });
}

// 或使用 helmet
import helmet from 'helmet';
app.use(helmet());
```

### 4. 权限检查

每个敏感端点**必须**有权限检查：

```typescript
// ✅ 必须实现
function requireAuth(req, res, next) {
  if (!req.user) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
}

function requireRole(role: string) {
  return (req, res, next) => {
    if (req.user?.role !== role) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    next();
  };
}

// 使用
router.delete('/users/:id', requireAuth, requireRole('admin'), deleteUser);
```

**检测方法**：
```bash
# 查找没有中间件的路由
grep -rn "router\.\(get\|post\|put\|delete\)" --include="*.ts" | grep -v "auth\|guard\|require"
```

### 5. CSRF 防护

状态变更操作**必须**有 CSRF 防护：

```typescript
// ✅ 必须配置
import csrf from 'csurf';

const csrfProtection = csrf({ cookie: true });

// 对所有 POST/PUT/DELETE 启用
app.use(csrfProtection);

// 在表单中包含 token
app.get('/form', (req, res) => {
  res.render('form', { csrfToken: req.csrfToken() });
});
```

**检测方法**：
```bash
grep -rn "csrf\|xsrf" --include="*.ts"
```

---

## 🟡 强烈建议（Strongly Recommended）

### 1. 安全 Headers

使用 `helmet` 设置安全 headers：

```typescript
import helmet from 'helmet';

app.use(helmet());
// 或手动配置
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"], // 尽量避免
    }
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true
  }
}));
```

### 2. 速率限制

API 端点应有速率限制：

```typescript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 分钟
  max: 100, // 每窗口最多 100 请求
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', limiter);

// 登录等敏感端点用更严格的限制
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5, // 15 分钟内最多 5 次尝试
});
app.post('/login', loginLimiter, loginHandler);
```

### 3. 错误处理不泄露信息

```typescript
// ❌ 不好
app.use((err, req, res, next) => {
  res.status(500).json({ 
    error: err.message,
    stack: err.stack  // 泄露实现细节！
  });
});

// ✅ 正确做法
app.use((err, req, res, next) => {
  // 记录完整错误到服务端日志
  logger.error(err);
  
  // 只返回通用信息给客户端
  res.status(500).json({ 
    error: 'Internal server error',
    requestId: req.id  // 用于追踪
  });
});
```

### 4. 会话安全

```typescript
import session from 'express-session';

app.use(session({
  secret: process.env.SESSION_SECRET, // 不能硬编码
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: true,     // 仅 HTTPS
    httpOnly: true,   // 防止 XSS 窃取
    sameSite: 'strict', // 防止 CSRF
    maxAge: 3600000   // 1 小时过期
  }
}));
```

### 5. 依赖安全

定期检查依赖漏洞：

```bash
# npm
npm audit
npm audit fix

# 或使用 snyk
npx snyk test
```

---

## 检查清单

在代码审查时，确认以下安全检查项：

### 认证相关
- [ ] 密码使用 bcrypt/argon2 哈希
- [ ] 没有硬编码凭证
- [ ] JWT secret 来自环境变量
- [ ] 会话有合理的超时时间
- [ ] 登录有速率限制

### 授权相关
- [ ] 每个端点都有权限检查
- [ ] 资源访问验证所有权
- [ ] 管理员功能有额外保护

### 输入处理
- [ ] 所有输入都经过验证
- [ ] SQL 查询使用参数化
- [ ] 没有 eval() 或 Function()
- [ ] 文件上传有类型和大小限制

### 输出处理
- [ ] HTML 输出正确转义（防 XSS）
- [ ] API 响应不泄露敏感信息
- [ ] 错误消息不泄露实现细节

### 传输安全
- [ ] 生产环境强制 HTTPS
- [ ] 设置了安全 headers
- [ ] Cookie 设置了 secure/httpOnly/sameSite

### 日志与监控
- [ ] 日志不包含敏感数据
- [ ] 关键操作有审计日志
- [ ] 异常情况有告警

---

## 合规要求参考

### OWASP Top 10 (2021)
- A01 Broken Access Control
- A02 Cryptographic Failures  
- A03 Injection
- A04 Insecure Design
- A05 Security Misconfiguration
- A06 Vulnerable Components
- A07 Identification Failures
- A08 Data Integrity Failures
- A09 Logging Failures
- A10 SSRF

### GDPR（如适用）
- 数据最小化
- 存储时加密
- 访问日志
- 删除权实现

### PCI-DSS（如处理支付）
- 不存储完整卡号
- 使用 tokenization
- 网络隔离
- 定期审计

---

## 违规处理

| 严重度 | 示例 | 处理 |
|--------|------|------|
| 🔴 Critical | SQL 注入、硬编码凭证 | 立即修复，阻塞合并 |
| 🟠 High | 缺少权限检查、弱哈希 | 必须修复后合并 |
| 🟡 Medium | 缺少速率限制、日志不足 | 创建 Issue 跟踪 |
| 🟢 Low | 可以更好的实践 | 建议改进 |

**记住**：安全不是特性，是基线要求。
