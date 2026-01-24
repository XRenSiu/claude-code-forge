# /review Command

手动触发代码审查。

## 语法

```
/review [options] <path>
```

## 参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `path` | string | 是 | 要审查的代码路径（支持 glob） |
| `--type` | enum | 否 | 审查类型：`spec` / `code` / `security` / `all` (默认: `code`) |
| `--spec` | string | 否 | PRD 或规格文档路径 |
| `--plan` | string | 否 | 计划文档路径 |
| `--focus` | string | 否 | 重点关注领域（逗号分隔） |
| `--sha` | string | 否 | Git 提交范围 (`base..head`) |

## 使用示例

### 基本代码审查
```
/review src/auth/
```
对 `src/auth/` 目录进行代码质量审查。

### 规格合规审查
```
/review --type spec --spec docs/prd/auth.md src/auth/
```
检查实现是否满足 PRD 中的所有需求。

### 安全审查
```
/review --type security --focus authentication,session src/auth/
```
针对认证和会话管理进行安全审查。

### 完整审查（三阶段）
```
/review --type all --spec docs/prd/auth.md --plan docs/plans/auth.md src/auth/
```
依次进行规格、代码、安全审查。

### 针对特定提交
```
/review --sha abc123..def456 src/
```
只审查两个提交之间的变更。

### 指定关注领域
```
/review --focus error-handling,performance src/services/
```
重点关注错误处理和性能方面。

## 执行逻辑

```
/review 命令执行流程

1. 解析参数
   └── 确定审查类型、路径、关联文档

2. 预检查
   ├── 验证路径存在
   ├── 检查关联文档存在
   └── 运行基本 lint/compile 检查

3. 按类型调用审查员
   ├── spec → dispatch spec-reviewer
   ├── code → dispatch code-reviewer
   ├── security → dispatch security-reviewer
   └── all → 依次调用三个审查员

4. 汇总报告
   └── 合并所有审查结果，生成统一报告
```

## 输出格式

```markdown
## 审查结果

**审查类型**: [spec/code/security/all]
**审查路径**: [path]
**执行时间**: [timestamp]

---

### 规格审查 (如执行)
[spec-reviewer 的输出]

---

### 代码审查 (如执行)
[code-reviewer 的输出]

---

### 安全审查 (如执行)
[security-reviewer 的输出]

---

## 总结

| 审查类型 | 结果 | 关键发现 |
|----------|------|----------|
| 规格 | 🟢/🟡/🔴 | X 个问题 |
| 代码 | 🟢/🟡/🔴 | Y 个问题 |
| 安全 | 🟢/🟡/🔴 | Z 个问题 |

**总体评估**: 🟢 可以合并 / 🟡 需要小改动 / 🔴 需要大修改
```

## 与其他命令的关系

| 命令 | 关系 |
|------|------|
| `/accept` | `/review --type all` + 自动修复循环 |
| `/fix` | 根据 `/review` 的反馈进行修复 |
| `/tdd` | 开发时使用，`/review` 是开发后使用 |

## 注意事项

1. **先完成自检**：运行 `/review` 前确保代码可编译、测试通过
2. **提供上下文**：使用 `--spec` 和 `--plan` 提供更好的审查质量
3. **分阶段审查**：大型变更建议按模块分别审查
4. **记录反馈**：审查结果应记录以便后续追踪
