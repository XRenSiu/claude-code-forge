# 生成代码 Prompt

## 任务

根据 ComponentTree JSON 和项目上下文，生成使用项目组件库的代码。

## 输入

1. **ComponentTree JSON** - `local-code-connect transform` 的输出
2. **组件注册表** - 项目可用组件及其 props
3. **项目结构** - 现有代码和目录布局
4. **Figma 截图** - 视觉参考

## 决策流程

### 1. 确定输出文件

问自己：
- 这是新页面还是现有页面的一部分？
- 应该创建新文件还是修改现有文件？
- 文件应该放在哪个目录？

**参考项目现有结构做出决策。**

### 2. 确定组件拆分

问自己：
- JSON 中有多少个顶级组件？
- 是否需要拆分为多个文件？
- 哪些部分可以复用？

**原则**：如果组件超过 100 行，考虑拆分。

### 3. 处理未匹配的节点

JSON 中 `_matched: false` 的节点没有对应的项目组件。选择：
- 使用最接近的项目组件
- 保留原始 HTML 结构
- 向用户询问如何处理

## 生成规则

### 组件使用

```
✅ 正确：使用 JSON 中 importPath 指定的组件
import { Button } from '@xrs/vue'

❌ 错误：使用 Figma 生成的组件名
import { BtnPrimary } from './components'
```

### Props 映射

```
✅ 正确：使用注册表中定义的 props
<Button variant="primary" size="md">

❌ 错误：使用 Figma 的 data-* 属性作为 props
<Button data-variant="primary">
```

### 样式处理

优先级（从高到低）：
1. 项目设计系统 token
2. 组件内置样式
3. Tailwind 类（如果项目使用）
4. 内联样式（最后手段）

```
✅ 优先使用 token
<div className="text-primary-500 p-4">

⚠️ 必要时使用内联
<div style={{ width: '347px' }}>
```

### 框架适配

根据项目框架生成对应代码：

**Vue 3 (Composition API)**
```vue
<script setup lang="ts">
import { Button } from '@xrs/vue'
</script>

<template>
  <Button variant="primary">Click me</Button>
</template>
```

**React**
```tsx
import { Button } from '@xrs/react'

export function MyComponent() {
  return <Button variant="primary">Click me</Button>
}
```

## 输出格式

### 单文件输出

```
// 文件路径: src/views/NewPage.vue

<script setup lang="ts">
// imports
</script>

<template>
  // 组件树
</template>

<style scoped>
// 必要的样式
</style>
```

### 多文件输出

```
// 文件 1: src/components/FeatureCard.vue
...

// 文件 2: src/views/Dashboard.vue
import FeatureCard from '@/components/FeatureCard.vue'
...
```

## 验证清单

生成代码后检查：

- [ ] 所有 import 路径正确
- [ ] 所有组件 props 符合注册表定义
- [ ] 布局与截图匹配
- [ ] 没有硬编码的 Figma node-id
- [ ] 代码符合项目 lint 规则

## 示例

### 输入 JSON

```json
{
  "root": {
    "type": "component",
    "name": "Button",
    "importPath": "@xrs/vue",
    "props": { "variant": "primary" },
    "children": [{ "type": "text", "content": "Submit" }]
  },
  "imports": [{ "name": "Button", "path": "@xrs/vue" }]
}
```

### 输入注册表（部分）

```json
{
  "components": {
    "Button": {
      "importPath": "@xrs/vue",
      "props": {
        "variant": ["primary", "secondary", "ghost"],
        "size": ["sm", "md", "lg"],
        "disabled": "boolean"
      }
    }
  }
}
```

### 输出代码

```vue
<script setup lang="ts">
import { Button } from '@xrs/vue'
</script>

<template>
  <Button variant="primary">Submit</Button>
</template>
```
