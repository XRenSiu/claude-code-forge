# API 设计模式约束规则

> 此规则在系统设计和 API 开发阶段强制执行
---

## 适用范围

此规则适用于：
- 系统架构设计
- API 端点设计
- 数据模型设计
- 服务间通信设计

---

## 1. RESTful API 设计原则

### 1.1 资源命名

**必须遵循**：
```
✅ 使用名词，不使用动词
   /users           (不是 /getUsers)
   /orders          (不是 /createOrder)
   /products/{id}   (不是 /getProductById)

✅ 使用复数形式
   /users           (不是 /user)
   /products        (不是 /product)

✅ 使用连字符分隔
   /user-profiles   (不是 /user_profiles 或 /userProfiles)

✅ 使用小写
   /api/v1/users    (不是 /api/v1/Users)
```

**禁止**：
```
❌ 动词作为路径
   /getUsers, /createUser, /deleteUser

❌ 混合命名风格
   /user_profiles, /userProfiles

❌ 层级过深 (最多 3 层)
   /users/{id}/orders/{orderId}/items/{itemId}/details  ← 太深
```

### 1.2 HTTP 方法使用

| 方法 | 用途 | 幂等 | 安全 |
|------|------|------|------|
| GET | 读取资源 | ✅ | ✅ |
| POST | 创建资源 | ❌ | ❌ |
| PUT | 完整替换资源 | ✅ | ❌ |
| PATCH | 部分更新资源 | ❌ | ❌ |
| DELETE | 删除资源 | ✅ | ❌ |

**必须遵循**：
```
✅ GET 不应有副作用
✅ PUT 必须是幂等的（多次调用结果相同）
✅ DELETE 对不存在的资源返回 204，不是 404
```

### 1.3 HTTP 状态码

**必须使用正确的状态码**：

| 场景 | 状态码 | 说明 |
|------|--------|------|
| 成功获取 | 200 OK | GET 成功 |
| 成功创建 | 201 Created | POST 成功，返回 Location header |
| 成功无内容 | 204 No Content | DELETE 成功 |
| 客户端错误 | 400 Bad Request | 请求格式错误 |
| 未认证 | 401 Unauthorized | 需要认证 |
| 无权限 | 403 Forbidden | 认证了但无权限 |
| 未找到 | 404 Not Found | 资源不存在 |
| 方法不允许 | 405 Method Not Allowed | HTTP 方法不支持 |
| 冲突 | 409 Conflict | 资源状态冲突 |
| 验证失败 | 422 Unprocessable Entity | 业务验证失败 |
| 服务器错误 | 500 Internal Server Error | 服务器异常 |

**禁止**：
```
❌ 所有错误都返回 200 + error 字段
❌ 500 用于业务逻辑错误
❌ 404 用于已认证但无权限的情况（应该用 403）
```

---

## 2. API 版本控制

### 2.1 版本策略

**推荐**：URL 路径版本控制
```
✅ /api/v1/users
✅ /api/v2/users
```

**可接受**：Header 版本控制
```
Accept: application/vnd.myapp.v1+json
```

**禁止**：
```
❌ 无版本控制
❌ 查询参数版本控制 (/users?version=1)
```

### 2.2 版本迁移

```
1. 新版本与旧版本并行运行至少 6 个月
2. 旧版本废弃前至少提前 3 个月通知
3. 重大变更必须增加主版本号
```

---

## 3. 请求/响应格式

### 3.1 请求体

**必须遵循**：
```json
// ✅ 使用 camelCase
{
  "firstName": "John",
  "lastName": "Doe",
  "emailAddress": "john@example.com"
}

// ❌ 禁止 snake_case（除非项目已有约定）
{
  "first_name": "John"
}
```

### 3.2 响应体

**成功响应**：
```json
// 单个资源
{
  "id": "123",
  "name": "Product",
  "createdAt": "2024-01-15T10:30:00Z"
}

// 集合资源
{
  "data": [...],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalPages": 10,
    "totalItems": 195
  }
}
```

**错误响应**：
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "requestId": "req_abc123"
}
```

### 3.3 日期时间格式

**必须使用 ISO 8601 格式**：
```
✅ "2024-01-15T10:30:00Z"      (UTC)
✅ "2024-01-15T10:30:00+08:00" (带时区)

❌ "2024/01/15 10:30:00"
❌ "1705312200"                 (Unix 时间戳作为字符串)
❌ "Jan 15, 2024"
```

---

## 4. 分页设计

### 4.1 标准分页参数

```
GET /users?page=1&pageSize=20
GET /users?offset=0&limit=20
```

**必须包含**：
- 总数信息
- 当前页/偏移量
- 每页大小
- 是否有更多页

### 4.2 游标分页（大数据集推荐）

```
GET /users?cursor=eyJpZCI6MTIzfQ&limit=20

Response:
{
  "data": [...],
  "pagination": {
    "nextCursor": "eyJpZCI6MTQzfQ",
    "hasMore": true
  }
}
```

### 4.3 分页限制

```
✅ 设置最大 pageSize (如 100)
✅ 设置默认 pageSize (如 20)
❌ 允许无限制的 pageSize
```

---

## 5. 过滤、排序、搜索

### 5.1 过滤

```
// 简单过滤
GET /users?status=active

// 多值过滤
GET /users?status=active,pending

// 范围过滤
GET /users?createdAt[gte]=2024-01-01&createdAt[lte]=2024-12-31

// 或使用更简洁的格式
GET /orders?minAmount=100&maxAmount=500
```

### 5.2 排序

```
// 单字段排序
GET /users?sort=createdAt
GET /users?sort=-createdAt  // 降序

// 多字段排序
GET /users?sort=-createdAt,name
```

### 5.3 搜索

```
// 全文搜索
GET /users?q=john

// 字段搜索
GET /users?search[name]=john&search[email]=example
```

---

## 6. 安全模式

### 6.1 认证

**必须**：
```
✅ 使用 HTTPS
✅ 使用标准认证头
   Authorization: Bearer <token>
✅ Token 有过期时间
✅ 支持 Token 刷新机制
```

**禁止**：
```
❌ URL 中传递认证信息
   /users?token=abc123
❌ 无过期的 Token
❌ 在响应体中返回敏感信息
```

### 6.2 授权

```
✅ 基于角色的访问控制 (RBAC)
✅ 最小权限原则
✅ 资源级别的权限检查
```

### 6.3 输入验证

**必须验证**：
- 数据类型
- 长度限制
- 格式（邮箱、URL 等）
- 范围（数字上下限）
- 必填字段

**必须防护**：
- SQL 注入
- XSS
- CSRF (状态变更操作)
- 路径遍历

---

## 7. 错误处理模式

### 7.1 错误码规范

```
// 使用有意义的错误码
{
  "error": {
    "code": "USER_NOT_FOUND",        // 应用级错误码
    "message": "User not found",
    "httpStatus": 404
  }
}

// 错误码命名规范
RESOURCE_NOT_FOUND    // 资源不存在
VALIDATION_ERROR      // 验证失败
UNAUTHORIZED          // 未认证
FORBIDDEN            // 无权限
RATE_LIMIT_EXCEEDED  // 超出限制
INTERNAL_ERROR       // 内部错误
```

### 7.2 错误信息

**必须**：
```
✅ 提供人类可读的错误信息
✅ 不暴露内部实现细节
✅ 提供足够信息帮助客户端修复问题
✅ 包含请求 ID 便于排查
```

**禁止**：
```
❌ 暴露堆栈跟踪
❌ 暴露数据库错误详情
❌ 使用技术术语作为用户消息
```

---

## 8. 幂等性设计

### 8.1 幂等键

对于非幂等操作（POST），使用幂等键：

```
POST /payments
Idempotency-Key: unique-request-id-123

// 相同 Idempotency-Key 的重复请求返回相同结果
```

### 8.2 乐观锁

使用版本号或 ETag 防止并发冲突：

```
GET /users/123
Response:
  ETag: "version-5"
  {
    "id": "123",
    "name": "John",
    "version": 5
  }

PUT /users/123
If-Match: "version-5"
{
  "name": "John Updated"
}

// 如果版本不匹配，返回 409 Conflict
```

---

## 9. 性能模式

### 9.1 响应压缩

```
✅ 支持 gzip/br 压缩
✅ 客户端声明: Accept-Encoding: gzip, br
```

### 9.2 缓存

```
// 静态资源
Cache-Control: public, max-age=31536000

// 动态资源
Cache-Control: private, max-age=0, no-cache

// 条件请求
If-None-Match: "etag-value"
If-Modified-Since: Wed, 15 Jan 2024 10:30:00 GMT
```

### 9.3 批量操作

```
// 批量获取
POST /users/batch
{
  "ids": ["1", "2", "3"]
}

// 批量创建
POST /users/bulk
{
  "users": [
    {"name": "User 1"},
    {"name": "User 2"}
  ]
}

// 批量操作响应
{
  "results": [
    {"id": "1", "status": "success"},
    {"id": "2", "status": "error", "error": {...}}
  ],
  "summary": {
    "total": 2,
    "succeeded": 1,
    "failed": 1
  }
}
```

---

## 10. 数据模型模式

### 10.1 实体设计

**必须包含**：
```typescript
interface BaseEntity {
  id: string;           // 唯一标识符
  createdAt: DateTime;  // 创建时间
  updatedAt: DateTime;  // 更新时间
}

// 可选但推荐
interface AuditableEntity extends BaseEntity {
  createdBy: string;    // 创建者
  updatedBy: string;    // 更新者
  version: number;      // 乐观锁版本
}
```

### 10.2 关联设计

```typescript
// 嵌入（1:1 或 1:少量）
interface User {
  id: string;
  profile: {           // 嵌入式
    bio: string;
    avatar: string;
  };
}

// 引用（1:多 或 多:多）
interface Order {
  id: string;
  userId: string;      // 外键引用
  // 不要: user: User  // 避免嵌入完整对象
}
```

### 10.3 枚举设计

```typescript
// ✅ 使用字符串枚举
enum OrderStatus {
  PENDING = 'PENDING',
  PROCESSING = 'PROCESSING',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED'
}

// ❌ 不要使用数字枚举
enum OrderStatus {
  PENDING = 0,    // 不直观，易出错
  PROCESSING = 1
}
```

---

## 检测命令

```bash
# 检查 API 路径命名
grep -rn "app\.\(get\|post\|put\|patch\|delete\)" --include="*.ts" | \
  grep -v "\/api\/v[0-9]"

# 检查是否使用了动词作为路径
grep -rn "\/get\|\/create\|\/update\|\/delete" --include="*.ts"

# 检查状态码使用
grep -rn "res\.status\|ctx\.status" --include="*.ts" | head -20

# 检查是否有硬编码的错误消息
grep -rn "throw new Error\|res\.json.*error" --include="*.ts" | head -20
```

---

## 违规处理

| 严重程度 | 违规类型 | 处理 |
|----------|----------|------|
| 🔴 Critical | 安全漏洞（SQL 注入、XSS） | 阻止合并 |
| 🔴 Critical | 认证信息泄露 | 阻止合并 |
| 🟡 Important | 不符合 RESTful 规范 | 必须修复 |
| 🟡 Important | 缺少输入验证 | 必须修复 |
| 🟢 Advisory | 命名风格不一致 | 建议修复 |
| 🟢 Advisory | 缺少分页 | 建议修复 |

---

## 参考资源

- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines)
- [Google API Design Guide](https://cloud.google.com/apis/design)
- [JSON:API Specification](https://jsonapi.org/)
- [OpenAPI Specification](https://swagger.io/specification/)