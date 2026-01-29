# 修复 MCP Code Prompt

## 任务

将 Figma MCP 返回的代码修复为合法的 JSX。

## 输入

MCP 返回的原始代码（可能有语法错误）。

## 修复规则

### 必须保留

1. **所有 `data-node-id` 属性** - 这是组件匹配的关键
2. **所有 `data-name` 属性** - 这是 Figma 图层名称
3. **所有 `className` 属性** - 这是样式信息
4. **所有内联 style** - 这是布局信息
5. **组件结构和嵌套关系** - 这是组件树

### 常见语法问题及修复

| 问题 | 示例 | 修复 |
|------|------|------|
| 未闭合标签 | `<div>` | `<div></div>` 或 `<div />` |
| 多余的闭合标签 | `</div></div>` | 删除多余的 |
| 非法属性名 | `class=` | `className=` |
| 非法字符 | `<div &nbsp;>` | `<div>` |
| 字符串未闭合 | `className="foo` | `className="foo"` |
| 表达式未闭合 | `style={{color: 'red'` | `style={{color: 'red'}}` |
| 注释格式错误 | `<!-- comment -->` | `{/* comment */}` |
| 多根元素 | `<div/><div/>` | 包裹在 `<>...</>` 中 |

### 不允许做的修改

- ❌ 不要改变组件结构
- ❌ 不要删除任何 `data-*` 属性
- ❌ 不要优化或简化代码
- ❌ 不要添加新的属性或元素
- ❌ 不要转换为其他框架（保持 JSX）

## 输出格式

输出一个完整的、可被 Babel 解析的 JSX 文件：

```jsx
// 保留顶部的变量声明（如图片 URL）
const img1 = "https://...";

// 主组件
function Component() {
  return (
    // 修复后的 JSX
  );
}

export default Component;
```

## 验证方法

修复后的代码应该能通过：
```bash
npx babel --presets @babel/preset-react /tmp/figma-fixed.jsx
```

如果报错，继续修复直到通过。

## 示例

### 输入（有问题的 MCP 代码）

```jsx
const img = "https://figma.com/api/mcp/asset/...";

function Component() {
  return (
    <div data-node-id="86:6167" className="flex flex-col
      <div data-node-id="I411:20434" data-name="Btn/Primary">
        <p>Click me</p>
      </div>
    </div>
  );
}
```

### 输出（修复后）

```jsx
const img = "https://figma.com/api/mcp/asset/...";

function Component() {
  return (
    <div data-node-id="86:6167" className="flex flex-col">
      <div data-node-id="I411:20434" data-name="Btn/Primary">
        <p>Click me</p>
      </div>
    </div>
  );
}

export default Component;
```

修复内容：`className="flex flex-col` → `className="flex flex-col"`（闭合引号）
