---
name: figma-to-code
description: >
  将 Figma 设计稿转换为使用项目组件库的代码。
  Use when: (1) 用户提供 Figma URL 要求实现设计, (2) 需要将设计稿转为项目代码, (3) 用户说"实现这个设计"/"把这个加到页面"。
  Examples: "帮我实现这个设计稿 https://figma.com/...", "把这个组件加到 Dashboard", "figma to code"
when_to_use: |
  - 用户提供 Figma URL 并要求生成代码
  - 用户要求将设计稿转换为项目组件
  - 用户说"实现设计"、"figma to code"、"设计转代码"
version: 1.0.0
---

# Figma to Code

## 核心原则

**使用项目组件库生成代码，而非 Figma MCP 的原始输出。** MCP 返回的代码有语法问题且不使用项目组件，必须经过修复和转换。

## 前提条件

1. **Figma MCP 已连接**
2. **项目已配置 local-code-connect**：
   - `package.json` 中有 `localCodeConnect.registry` 配置
   - 组件库已导出注册表文件
3. **local-code-connect CLI 可用**（作为组件库依赖安装）

## 流程

**必须按顺序执行，不允许跳过任何步骤。**

### Step 1: 读取项目上下文

在调用任何 Figma MCP 之前：

1. **读取 `package.json`**，获取 `localCodeConnect.registry` 路径
2. **读取组件注册表**，了解可用组件及其 props
3. **分析项目结构**，了解现有代码布局和约定

```json
// package.json 配置示例
{
  "localCodeConnect": {
    "registry": "./node_modules/@xrs/vue/dist/.figma-registry.json"
  }
}
```

**如果找不到配置**：停止并告知用户需要先配置 `localCodeConnect.registry`。

### Step 2: 获取设计稿信息

从 Figma URL 提取 fileKey 和 nodeId：
- URL 格式：`https://figma.com/design/:fileKey/:fileName?node-id=1-2`
- fileKey: `/design/` 后的部分
- nodeId: `node-id` 参数值

调用 Figma MCP：
```
get_design_context(fileKey=":fileKey", nodeId="1-2")
get_screenshot(fileKey=":fileKey", nodeId="1-2")
```

**截图是视觉验证的基准**，保留到最后。

### Step 3: 修复 MCP Code

MCP 返回的代码可能有语法问题。按照 `prompts/fix-mcp-code.md` 修复：

**修复规则**：
- 只修复语法问题，不改变语义
- 保留所有 `data-node-id`、`data-name` 属性
- 保留所有 `className`、样式信息
- 输出合法的 JSX 文件

将修复后的代码保存为临时文件：`/tmp/figma-fixed.jsx`

### Step 4: 转换为 JSON

使用 local-code-connect CLI 转换：

```bash
npx local-code-connect transform /tmp/figma-fixed.jsx \
  --registry <registry路径> \
  -o /tmp/figma-result.json
```

**输出是 ComponentTree JSON**，包含：
- 匹配到的项目组件
- 组件 props
- 导入信息
- 组件树结构

### Step 5: 生成代码

根据以下信息生成最终代码：
1. **ComponentTree JSON**（Step 4 输出）
2. **组件注册表**（组件详细 props 和用法）
3. **项目结构**（现有代码和目录布局）

**决策由你做出**：
- 创建新文件还是修改现有文件
- 文件放在哪个目录
- 是否拆分为多个组件
- 如何与现有代码集成

按照 `prompts/generate-code.md` 指南生成代码。

### Step 6: 验证

对比截图验证：
- [ ] 布局匹配（间距、对齐、尺寸）
- [ ] 排版匹配（字体、大小、粗细）
- [ ] 颜色匹配
- [ ] 使用了正确的项目组件

## 反模式

| 坏行为 | 为什么失败 | 正确做法 |
|--------|-----------|---------|
| 跳过 Step 1 直接调 MCP | 不知道项目有什么组件 | 必须先读组件注册表 |
| 直接使用 MCP 返回的代码 | 语法错误 + 不用项目组件 | 经过 Step 3-5 转换 |
| 不保存临时文件 | CLI 需要文件路径 | 保存为 /tmp/figma-*.jsx |
| 手动写组件映射 | 不准确、不一致 | 使用 CLI transform |
| 忽略组件注册表 | 生成的代码不符合项目规范 | 始终参考注册表 |

## 你可能想跳过部分步骤

| 借口 | 反驳 |
|------|------|
| "MCP 代码看起来没问题" | 语法问题可能很隐蔽，CLI 会报错 |
| "这个组件很简单" | 简单组件更容易不一致 |
| "用户很急" | 返工比多花 2 分钟更慢 |
| "我知道项目用什么组件" | 注册表是唯一真相来源 |
| "CLI 太麻烦" | CLI 保证组件映射准确 |

**必须完整执行 Step 1-6。没有例外。**

## 资源

- `prompts/fix-mcp-code.md` - 修复 MCP 代码的详细指南
- `prompts/generate-code.md` - 生成最终代码的详细指南
- `examples/` - 各阶段输出示例

## 常见问题

### 找不到 localCodeConnect 配置

项目未配置。告知用户需要：
1. 组件库导出注册表
2. 在 `package.json` 添加 `localCodeConnect.registry` 配置

### CLI transform 失败

通常是 JSX 语法问题。检查：
1. 修复后的代码是否能被 Babel 解析
2. 是否有未闭合的标签
3. 是否有非法字符

### 组件未匹配

注册表中没有对应组件。选择：
1. 使用最接近的项目组件
2. 保留原始 HTML 结构
3. 告知用户需要在组件库添加该组件

### 设计稿太大

`get_design_context` 返回截断。使用：
1. `get_metadata` 获取节点结构
2. 分别获取子节点的 design context
3. 分多次处理