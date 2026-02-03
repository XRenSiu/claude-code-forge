# 生成代码 Prompt

## 任务

根据 ComponentTree JSON 和项目上下文，生成使用项目组件库的代码。

## 输入

1. **ComponentTree JSON** - `local-code-connect transform` 的输出
2. **组件注册表** - 项目可用组件及其 props
3. **项目结构** - 现有代码和目录布局
4. **Figma 截图** - 视觉参考

## 决策流程

### 1. 还原整体布局结构（最重要）

**在写任何代码之前，先从 JSON 的根节点 className 推断布局方向和层级关系。**

```
根节点 className 解读规则：

flex（无 flex-col）     → 水平布局（子元素左右排列）
flex flex-col           → 垂直布局（子元素上下排列）
gap-[Npx]              → 子元素间距
p-[Npx]                → 容器内边距
rounded-[Npx]          → 圆角半径
relative               → 内部有绝对定位子元素
```

**子节点 className 解读规则：**

```
absolute + top/left/right/bottom  → 浮动覆盖层，不参与 flex 布局
flex-[1_0_0] / flex-1             → 填满剩余空间的主内容
shrink-0 + w-[Npx]               → 固定宽度的侧栏
h-full                            → 撑满父容器高度
```

#### 示例

```json
{
  "root": {
    "props": { "className": "flex gap-[8px] p-[8px] rounded-[26px] relative" },
    "children": [
      { "props": { "className": "flex-[1_0_0] h-full relative rounded-[18px]" } },
      { "props": { "className": "shrink-0 w-[268px] h-full" } },
      { "type": "component", "name": "XmNavigationBar", "className": "absolute left-[7px] top-0 w-[1440px]" }
    ]
  }
}
```

解读为：
```
根容器（水平 flex，8px 间距，8px 内边距，26px 圆角）
├── 主内容区（flex-1，18px 圆角，position: relative）
├── 右侧面板（固定 268px 宽）
└── 导航栏（绝对定位覆盖层，浮在最上方）
```

### 2. 处理包装 div 的 className（最易遗漏！）

**`type: "element"` 的 div 节点如果包装了 `type: "component"` 节点，其 className 包含关键定位信息。** 这是导致布局错位的最常见原因。

#### 识别方法

在 ComponentTree JSON 中，查找以下模式：

```json
{
  "type": "element",
  "tag": "div",
  "props": {
    "className": "-translate-x-1/2 absolute left-1/2 top-[16px]"  // ⚠️ 关键定位信息！
  },
  "children": [
    {
      "type": "component",
      "name": "XmToolbar",
      ...
    }
  ]
}
```

**这个 div 的 className 不是可选的装饰，而是决定子组件定位的关键。**

#### 常见的包装 div 定位类

| className 片段 | 含义 | 必须实现 |
|----------------|------|---------|
| `absolute left-1/2 -translate-x-1/2` | 水平居中的绝对定位 | `position: absolute; left: 50%; transform: translateX(-50%)` |
| `absolute top-[16px]` | 距顶部 16px | `top: 16px` |
| `absolute right-[8px] top-0` | 右上角定位 | `position: absolute; right: 8px; top: 0` |
| `relative` | 作为子元素的定位上下文 | `position: relative` |

#### 生成代码时

```vue
<!-- JSON 中 div 包装了 XmToolbar，div 的 className 有绝对定位 -->

✅ 正确：保留包装 div 并应用定位
<div class="center-tools">
  <XmToolbar>...</XmToolbar>
</div>

<style scoped>
.center-tools {
  position: absolute;
  left: 50%;
  top: 16px;  /* 从 top-[16px] 提取 */
  transform: translateX(-50%);  /* 从 -translate-x-1/2 提取 */
}
</style>

❌ 错误：忽略包装 div，直接输出组件
<XmToolbar>...</XmToolbar>  <!-- 丢失了定位信息！ -->
```

### 3. 处理 ComponentNode 的 className（必须执行）

**`type: "component"` 的节点可能有 `className` 字段。** 这是 Figma 中该组件外层容器的布局类名，包含定位、尺寸、间距等信息。**你必须从 className 中提取布局属性并应用到组件上。**

#### 提取规则

逐个扫描每个 component 节点的 `className`，提取以下关键布局属性：

```
className 中的属性         →  CSS 转换
─────────────────────────────────────────────
w-[72px]                   →  width: 72px; flex-shrink: 0
w-[228px]                  →  width: 228px; flex-shrink: 0
h-[24px]                   →  height: 24px
flex-[1_0_0]               →  flex: 1 0 0; min-width: 0
shrink-0                   →  flex-shrink: 0
absolute + left/top/...    →  position: absolute; ...
```

#### 应用方式

**方式 A — 直接在组件上加 class/style：**
```vue
<!-- className 含 w-[72px] -->
<XmSelectIcon style="width: 72px; flex-shrink: 0" />

<!-- className 含 flex-[1_0_0] -->
<XmTitle class="flex-1-0-0" style="flex: 1 0 0; min-width: 0">Shape</XmTitle>
```

**方式 B — 定义语义化的 CSS 工具类复用：**
```css
/* 从 JSON className 提取的布局约束 */
.fp-w72  { width: 72px; flex-shrink: 0; }
.fp-w228 { width: 228px; flex-shrink: 0; }
.fp-flex-1 { flex: 1 0 0; min-width: 0; }
```
```vue
<XmTitle class="fp-flex-1">Shape</XmTitle>
<XmSelectIcon class="fp-w72" />
```

**方式 C — 用 wrapper div（仅当组件不接受 class 时）：**
```vue
<div style="position: absolute; left: 7px; top: 0">
  <XmNavigationBar />
</div>
```

#### 常见 className 模式速查

| className 片段 | 含义 | 应用 |
|----------------|------|------|
| `w-[72px]` | 固定 72px 宽（选择器、颜色选择器） | `width: 72px; flex-shrink: 0` |
| `w-[228px]` | 固定 228px 宽（分段控件） | `width: 228px` |
| `w-full` / `shrink-0 w-full` | 撑满父容器宽度 | `width: 100%` |
| `flex-[1_0_0]` | 填充剩余空间 | `flex: 1 0 0; min-width: 0` |
| `h-[24px]` | 固定 24px 高 | `height: 24px` |
| `absolute left-[7px] top-0` | 绝对定位 | `position: absolute; left: 7px; top: 0` |

```
❌ 错误：忽略 className，不设置宽度约束
<XmTitle>Shape</XmTitle>        <!-- 没有 flex-1，可能不撑满 -->
<XmSelectIcon />                <!-- 没有 w-72，宽度不可控 -->

✅ 正确：从 className 提取并应用布局约束
<XmTitle class="fp-flex-1">Shape</XmTitle>
<XmSelectIcon class="fp-w72" />
```

### 4. 确定输出文件

问自己：
- 这是新页面还是现有页面的一部分？
- 应该创建新文件还是修改现有文件？
- 文件应该放在哪个目录？

**参考项目现有结构做出决策。**

### 5. 确定组件拆分

问自己：
- JSON 中有多少个顶级组件？
- 是否需要拆分为多个文件？
- 哪些部分可以复用？

**原则**：如果组件超过 100 行，考虑拆分。

### 6. 处理未匹配的节点

JSON 中 `type: "element"` 的节点没有对应的项目组件。选择：
- 使用最接近的项目组件
- 保留原始 HTML 结构
- 向用户询问如何处理

**注意**：`className: "undefined"` 是一个已知的 parser bug 产物，应忽略该值，不要将字符串 `"undefined"` 作为 class 输出。

### 7. 从 `_source.dataName` 推断正确的文本内容

MCP 生成的代码常包含**占位符文本**（如所有标题都写 "Shape"，所有标签页都写 "normal"）。这些不是真实内容，需要根据 JSON 中的 `_source.dataName` 来推断正确文本。

**规则：当组件的 text/children 内容看起来是占位符时，优先使用上层 `_source.dataName` 的语义。**

```
JSON 结构：
{
  "_source": { "dataName": "Style/Text" },     ← 父容器 dataName
  "children": [{
    "type": "component",
    "name": "XmTitle",
    "_source": { "dataName": "Title/Primary" },
    "props": { "children": "Shape" }            ← 占位符文本！
  }]
}

推断逻辑：
父容器 dataName = "Style/Text"  → 最后一段 "Text" = 实际标题
父容器 dataName = "Style/Shape" → 最后一段 "Shape" = 实际标题
父容器 dataName = "Style/Border" → 最后一段 "Border" = 实际标题
父容器 dataName = "Style/Branch" → 最后一段 "Branch" = 实际标题
```

**标签页文本推断**：Tab 组件如果文本全是 "normal"，需要从截图和上下文推断实际标签文字。观察 Tab 组件所在面板的用途，比如 Format Panel 的标签页通常是 "Style" / "Pitch" / "Map" 等。

```
✅ 正确：根据 dataName 推断标题
<!-- _source.dataName = "Style/Text" 的父容器 -->
<XmTitle>Text</XmTitle>

❌ 错误：直接输出占位符
<XmTitle>Shape</XmTitle>  <!-- 所有标题都变成 Shape！ -->
```

### 8. 处理 Figma 资产 URL（图标和图片）

JSON 的 `assets` 字段包含 Figma 资产 URL 映射。`type: "element"` 的 `img` 标签的 `src` 属性会是已解析的 Figma 资产 URL。

**这些 URL 是 Figma MCP 的临时资产链接，格式为 `https://www.figma.com/api/mcp/asset/...`。这些 URL 会过期，不能直接在生产代码中使用！**

#### 处理方式（按优先级）

1. **组件库图标**：如果组件库有对应图标组件，优先使用
   ```vue
   <XmIcon name="arrow-down" />
   ```

2. **下载到本地**：将 MCP URL 的图片下载到项目 assets 目录
   ```bash
   # 下载图标到本地
   curl -o src/assets/icons/home.svg "https://www.figma.com/api/mcp/asset/xxx"
   ```
   ```vue
   <img src="@/assets/icons/home.svg" alt="Home" />
   ```

3. **装饰性元素**：用 CSS 实现（分隔线、阴影等）
   ```css
   .divider { border-bottom: 1px solid rgba(0, 0, 0, 0.08); }
   ```

4. **内容型图片**：下载后放入 public 或 assets 目录

#### 下载脚本示例

```bash
# 批量下载 MCP 资产
mkdir -p src/assets/icons

# 从 JSON assets 字段提取 URL 并下载
curl -o src/assets/icons/home.svg "https://www.figma.com/api/mcp/asset/c326780f-..."
curl -o src/assets/icons/share.svg "https://www.figma.com/api/mcp/asset/4ab5bf98-..."
# ... 其他图标
```

```
✅ 正确：下载到本地使用
<img src="@/assets/icons/home.svg" alt="Home" />

✅ 正确：使用组件库图标
<XmIcon name="arrow-down" />

❌ 错误：直接使用 MCP URL（会过期！）
<img src="https://www.figma.com/api/mcp/asset/..." />

❌ 错误：删除所有 img 或留空 src
<img src="" />
```

## 生成规则

### 布局还原（最高优先级）

**绝对定位元素**：JSON 中 className 含 `absolute` 的节点是覆盖层（overlay），不参与父容器的 flex 布局。生成代码时必须用 `position: absolute` 实现，不能放入文档流。

**父子包含关系**：如果一个 `absolute` 元素在 JSON 中是某个 `relative` 容器的子节点，它应该在代码中也是该容器的子元素。

**颜色提取**：从 JSON 的 className 中提取实际颜色值。
```
className 中的 bg-[#7eaa77]  → color="#7eaa77"
className 中的 bg-[#fb6843]  → background: #fb6843
```
不要猜测或使用默认颜色，始终从 className 或 CSS 变量中提取准确值。

**Flex 方向**：根节点的 `flex` 不含 `flex-col` 则为水平布局。不要自作主张改成垂直布局。

### 严格遵循 JSON 数据（关键）

**不要发明 JSON 中不存在的 props。** 只使用 JSON 中明确提供的属性值。

```
✅ 正确：JSON 中有 props.type = "primary"，使用 type="primary"
❌ 错误：JSON 中没有 suffix prop，自己加上 suffix="PX"
❌ 错误：JSON 中没有 label prop，自己编造 label="Border Width"
```

**不要用不同组件替代。** 如果 JSON 中节点是 `XmSelectIcon`，不要替换成 `XmSelectText`。组件匹配已由 CLI 完成，AI 不应更改。

**不要简化或省略节点。** JSON 中每个 `type: "element"` 和 `type: "component"` 节点都应有对应输出。如果某个区域有 8 行图标控件，代码中也必须有 8 行，不能减少到 5 行。

**不要合并不同层级的节点。** JSON 的树形结构代表了真实的 DOM 嵌套关系。不要为了「简洁」而扁平化嵌套。

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

### 分隔线 (Divider) 处理

JSON 中 `_source.dataName` 为 `"Divider"` 的节点通常包含一个 img 标签渲染分隔线图像。**不要用 img 渲染分隔线**，用 CSS 或组件库的分隔线组件实现。

```
JSON 中的 Divider 节点：
{
  "type": "element",
  "tag": "div",
  "_source": { "dataName": "Divider" },
  "children": [{ "tag": "img", "props": { "src": "..." } }]
}

✅ 正确：
<div class="divider" />   <!-- 用 CSS border-bottom 或 hr 实现 -->

❌ 错误：
<img src="https://www.figma.com/api/mcp/asset/..." />  <!-- 不要用图片做分隔线 -->
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

### 尺寸和圆角

从 JSON 的 className 中提取**精确**的尺寸值，不要使用近似值。

```
className 中的 w-[72px]        → width: 72px（不要写成 width: 70px）
className 中的 h-[24px]        → height: 24px
className 中的 rounded-[8px]   → border-radius: 8px（不要改成 rounded-full）
className 中的 rounded-[99px]  → border-radius: 99px（这是药丸形状，可用 rounded-full）
className 中的 rounded-[18px]  → border-radius: 18px（不要改成 16px 或 20px）
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

- [ ] **布局方向**：根节点 flex 方向是否与 JSON className 一致？
- [ ] **包装 div 定位**：包含组件的 `type: element` div 的 className 是否已提取并应用（特别是 `absolute`、`left-1/2`、`top-[Npx]`、`-translate-x-1/2`）？
- [ ] **绝对定位**：JSON 中 `absolute` 的节点是否在代码中也是绝对定位？
- [ ] **父子关系**：SheetBar 等组件是否在正确的容器内？
- [ ] **容器样式**：padding、gap、border-radius 是否与 JSON 根节点一致？
- [ ] **组件 className**：每个 `type: "component"` 节点的 className 中的 `w-[Npx]`、`flex-[1_0_0]`、`absolute` 等是否已转换为 CSS 并应用？
- [ ] **颜色值**：从 JSON className 提取的颜色是否准确？
- [ ] **节点完整性**：JSON 中的每个节点是否都有对应输出？没有遗漏？
- [ ] **标题文本**：section 标题是否从 `_source.dataName` 推断而非使用占位符？
- [ ] **组件一致性**：JSON 中 `type: "component"` 的 name 是否原封不动地使用？没有被替换成其他组件？
- [ ] **Props 真实性**：所有 props 是否来自 JSON？没有发明 JSON 中不存在的 prop？
- [ ] **资产 URL**：img 标签的 src 是否保留了 JSON 中的 URL？
- [ ] 所有 import 路径正确
- [ ] 所有组件 props 符合注册表定义
- [ ] 没有硬编码的 Figma node-id
- [ ] 代码符合项目 lint 规则

## 常见错误

| 错误 | 后果 | 正确做法 |
|------|------|---------|
| **忽略包装 div 的 className** | 子组件丢失定位（如居中、偏移），布局严重错位 | 扫描 `type: element` 的 div，提取其 className 中的 `absolute`、`left-1/2`、`top-[16px]`、`-translate-x-1/2` 等 |
| 根节点 `flex` 写成 `flex-direction: column` | 整体布局方向错误 | 从 className 判断：无 `flex-col` = 水平 |
| 把 `absolute` 元素放入文档流 | 元素占据空间，挤压其他内容 | 用 `position: absolute` 实现 |
| 把子组件从其容器中移出 | 绝对定位元素失去定位上下文 | 保持 JSON 中的父子关系 |
| 忽略 ComponentNode 的 className | 组件宽度/定位/flex 全错 | 提取 `w-[Npx]`→width、`flex-[1_0_0]`→flex:1、`absolute`→position |
| 颜色用默认值而非 JSON 中的值 | 视觉不匹配 | 从 `bg-[#xxx]` 提取颜色 |
| `className: "undefined"` 当作真实类名 | 输出无效的 CSS class | 忽略，这是 parser bug |
| 容器缺少 padding/gap/rounded | 视觉细节不匹配 | 从根节点 className 提取所有样式 |
| 所有标题都显示 "Shape" | 各 section 标题错误 | 从父容器 `_source.dataName` 推断实际标题 |
| 标签页文字都是 "normal" | Tab 文字无意义 | 结合截图和上下文推断真实标签文字 |
| 用 XmSelectText 替代 XmSelectIcon | 组件类型不对 | 严格使用 JSON 中指定的组件名 |
| 自己发明 `suffix="PX"` 等 props | 运行时 prop 无效 | 只使用 JSON 中存在的 props |
| 省略 JSON 中的部分节点 | 界面缺失控件 | 每个 JSON 节点都必须有对应输出 |
| 用 img 标签渲染分隔线 | 分隔线依赖外部图片 | 用 CSS 或组件库实现分隔线 |
| 圆角值使用近似值 | 视觉不精确 | 从 className 提取精确的 `rounded-[Npx]` 值 |

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
