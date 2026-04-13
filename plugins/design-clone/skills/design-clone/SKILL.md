---
name: design-clone
description: >-
  从任意网站精确提取三维设计画像（Design DNA JSON）并可选地生成像素级克隆。
  使用 Browser MCP + getComputedStyle() 程序化提取设计系统 token（颜色、字体、
  间距、圆角、阴影、动效），AI 认知判断设计风格（情绪、流派、构图），代码扫描
  + AI 判断视觉特效（Canvas、WebGL、粒子、Shader、滚动效果）。
  触发词："design clone"、"提取设计"、"设计 DNA"、"克隆网站"、"提取设计数据"、
  "分析这个网站的设计"、"复刻这个网站"、"design dna"、"clone this site"。
  使用 --dna-only 仅输出 DNA JSON（跳过 Phase 4-6），使用 --full 或不加参数则完整克隆。
argument-hint: "[--dna-only | --full] <url1> [<url2> ...]"
version: 1.0.0
user-invocable: true
---

# Design Clone — Design DNA 提取 × 像素级克隆

你被调用来处理 **$ARGUMENTS**：可能是提取一份结构化的三维设计画像（Design DNA JSON），可能是完整克隆一个网站的源码，也可能两者都要。

这份 skill 提供两项核心能力：
- **精确提取**：用 Browser MCP 注入 JS，通过 `getComputedStyle()` 读取像素级精确 CSS 值，零猜测
- **结构化表达**：用三维 schema（150+ 字段）把提取到的原始值归类成可复用的设计画像

> 📖 参考：[`references/schema.md`](references/schema.md) — 三维 schema 完整字段定义；[`references/generation-guide.md`](references/generation-guide.md) — DNA JSON → 代码的映射规则。

**开始时告诉用户：** "I'm using the design-clone skill to extract a Design DNA profile [and clone the site]."

---

## 模式识别（必须首先做）

解析 `$ARGUMENTS`，识别两类信息：

1. **模式标志**
   - 出现 `--dna-only` → 仅提取设计数据，执行 Phase 0–3 即完成
   - 出现 `--full` 或没有标志 → 完整克隆，执行 Phase 0–6
2. **URL 列表**：剩余参数都是 URL。规范化、验证可访问。

**多 URL 处理：**
- `--dna-only` 多 URL：询问用户是并行处理输出多份 DNA，还是合并为一份 DNA（识别主导模式并标注差异）
- `--full` 多 URL：每个站点独立处理，产物隔离到 `docs/research/<hostname>/`

把识别结果作为首条状态输出给用户：
```
Mode: --dna-only
Targets: [url1, url2]
Merge strategy: combine into one DNA (dominant pattern + variants)
```

---

## 两种模式的执行路径

```
/design-clone --dna-only <url>          /design-clone --full <url>（或省略标志）

Phase 0: Pre-Flight (精简版)            Phase 0: Pre-Flight (完整版)
   ↓                                       ↓
Phase 1: Reconnaissance                  Phase 1: Reconnaissance
   ↓                                       ↓
Phase 2: Foundation (仅提取,不写入)       Phase 2: Foundation Build
   ↓                                       ↓
Phase 3: DNA Extraction                  Phase 3: DNA Extraction
   ↓                                       ↓
✅ 输出 design-dna.json 完成              Phase 4: Component Spec & Dispatch
                                            ↓
                                         Phase 5: Page Assembly
                                            ↓
                                         Phase 6: Visual QA
                                            ↓
                                         ✅ 输出 DNA JSON + 克隆源码
```

**核心原则：** `--dna-only` 模式跑同样的 JS 提取脚本获取精确数据，但数据流向 DNA JSON，而非写入 Next.js 项目。Phase 1 两种模式完全一样——DNA 的第一维和第三维都依赖 Phase 1 的精确数据和交互行为记录。

---

## Guiding Principles

这些原则是"成功克隆"与"差不多就行"的分水岭。每一个决策前先过一遍。

### 1. Completeness Beats Speed
每个 builder / DNA 字段都必须拿到**它所需的全部信息**：截图、精确 CSS、本地资源路径、真实文本、组件结构、多状态 diff。如果要 builder 猜一个颜色或间距，提取阶段就已经失败了。多花一分钟多提一个属性，也不要交付残缺简报。

### 2. Small Tasks, Perfect Results
给一个 agent "build the entire features section" 会糊弄细节；给它一张单一组件的带精确 CSS 值的 spec，它每次都能做对。
**复杂度预算规则：** 任何 builder prompt 超过 ~150 行 spec 内容 → 拆。这是机械规则，不要因为"它们是相关的"而放弃拆分。

### 3. Real Content, Real Assets
提取真实文本、图片、视频、SVG。这是克隆不是 mockup。用 `element.textContent` 读真文本；用脚本枚举并下载每一个 `<img>` / `<video>` / `<svg>`。
**关注分层资源**：一个看似单图的 section 往往是多层叠加（背景水彩 + 前景 UI mockup + overlay icon）。每个容器都要遍历全部 DOM，枚举所有 `<img>` 和 `backgroundImage`，包括绝对定位的 overlay。

### 4. Foundation First（仅 `--full`）
全局 CSS token、TypeScript 类型、全局资源必须先到位，后面才能并行。这一步不可省、不可并行。

### 5. Extract Appearance AND Behavior
一个网站不是一张截图，是一个活物。只提静态 CSS 会让克隆在截图里对、在使用时死。
每个元素同时提取：
- **外观**：`getComputedStyle()` 的精确值
- **行为**：什么变、什么触发、怎么过渡（duration / easing / CSS transition 或 JS-driven 或 `animation-timeline`）

要留意（非穷举）：滚动后 navbar 变形、视口进入动画、`scroll-snap`、视差、hover 动画、dropdown/modal/accordion 出入场、滚动进度条、自动轮播、主题切换、**scroll-driven tab/accordion 切换**（IntersectionObserver，不是 click）、**smooth scroll 库**（Lenis / Locomotive — 查 `.lenis` / `.locomotive-scroll` 类）。

### 6. Identify the Interaction Model BEFORE Building
克隆里最贵的错：把 scroll-driven UI 做成 click-based（或反之）。**先滚不要先点。**
1. 先慢慢滚动，观察是否自行变化 → 是 → scroll-driven → 记录机制（IntersectionObserver / `scroll-snap` / `position: sticky` / `animation-timeline` / JS scroll listeners）
2. 如果滚动没变化 → 再测 click / hover
3. 在 spec 里**显式写明**："INTERACTION MODEL: scroll-driven with IntersectionObserver"

sticky sidebar + 滚动切换 panels ≠ tabbed click 切换。搞错要整段重写。

### 7. Extract Every State, Not Just the Default
tab 组件每个 tab 一组卡片；header 在 scroll 0 和 100 样式不同；hover 态可能完全变样。**提取全部状态**，不只是页面加载时那一态。

- **tabbed/stateful content**：通过 Browser MCP 点击每个 tab，各自提取内容和样式，记录 state 归属；记录过渡动画
- **scroll-dependent**：在 scroll=0 提一次，滚过阈值后再提一次，diff → 记录 trigger 阈值（px 或 IntersectionObserver ratio）、变化的属性、过渡 CSS

### 8. Spec Files Are the Source of Truth（`--full`）
每个组件在 `docs/research/components/` 有一份 spec 文件，**先写 spec 再派 builder**。spec inline 进 builder prompt，文件同时作为可审计 artifact。没有 spec 就派 builder = 让 builder 用残缺指令猜。

### 9. Build Must Always Compile（`--full`）
每个 builder 结束前跑 `npx tsc --noEmit`；每次 worktree merge 后跑 `npm run build`。坏构建任何时刻都不可接受。

### 10. DNA JSON ↔ Clone Code Consistency（`--full`）
`globals.css` 的 CSS 变量必须**完全对应** DNA JSON 的 `design_system`；组件 spec 引用 **DNA token 名**而非硬编码值；Phase 6 做一致性验证。

---

## Phase 0: Pre-Flight 预检

**两种模式共有：**

1. **验证 Browser MCP 可用** — 检测 Chrome MCP / Playwright MCP / Browserbase MCP / Puppeteer MCP（优先 Chrome MCP）。没有任何一个 → 询问用户安装哪个并停止；这个 skill **不能**没有浏览器自动化。
2. **解析参数** — `--dna-only` 或 `--full`（默认），分离 URL 列表。规范化每个 URL，验证可访问。
3. **创建 DNA 输出目录** — `docs/dna/`、`docs/design-references/`

**仅 `--full` 模式：**

4. 验证 Next.js 项目可构建：`npm run build`。若失败 → 告知用户先修好脚手架。
5. 创建完整输出目录：`docs/research/`、`docs/research/components/`、`scripts/`

**仅 `--dna-only` 模式：**

4. 仅创建 `docs/research/`（用于 BEHAVIORS.md / PAGE_TOPOLOGY.md）和 `docs/design-references/`（截图）
5. 多 URL 时询问：并行多份 DNA，还是合并成一份？

**多站点 `--full`：** 准备 per-site 文件夹 `docs/research/<hostname>/`、`docs/design-references/<hostname>/`。

---

## Phase 1: Reconnaissance 侦察（两种模式都完整执行）

> DNA 的 Dimension 1（精确 token）和 Dimension 3（视觉特效）都依赖这里采集到的数据，任何模式都**不能跳过**。

### 1.1 截图
- 用 Browser MCP 导航到 URL
- 全页截图 **1440px**（desktop）+ **390px**（mobile）
- 保存到 `docs/design-references/`，用描述性文件名

### 1.2 全局提取

对每个 URL 运行以下 JS（通过 Browser MCP 执行），结果保存：

```javascript
// Global extraction script — run once per page
JSON.stringify({
  images: [...document.querySelectorAll('img')].map(img => ({
    src: img.src || img.currentSrc,
    alt: img.alt,
    width: img.naturalWidth,
    height: img.naturalHeight,
    parentClasses: img.parentElement?.className,
    siblings: img.parentElement ? [...img.parentElement.querySelectorAll('img')].length : 0,
    position: getComputedStyle(img).position,
    zIndex: getComputedStyle(img).zIndex
  })),
  videos: [...document.querySelectorAll('video')].map(v => ({
    src: v.src || v.querySelector('source')?.src,
    poster: v.poster,
    autoplay: v.autoplay,
    loop: v.loop,
    muted: v.muted
  })),
  backgroundImages: [...document.querySelectorAll('*')].filter(el => {
    const bg = getComputedStyle(el).backgroundImage;
    return bg && bg !== 'none';
  }).map(el => ({
    url: getComputedStyle(el).backgroundImage,
    element: el.tagName + '.' + (el.className?.toString().split(' ')[0] || '')
  })),
  svgCount: document.querySelectorAll('svg').length,
  fonts: [...new Set([...document.querySelectorAll('*')].slice(0, 300).map(el => getComputedStyle(el).fontFamily))],
  favicons: [...document.querySelectorAll('link[rel*="icon"]')].map(l => ({ href: l.href, sizes: l.sizes?.toString() })),
  ogMeta: [...document.querySelectorAll('meta[property^="og:"]')].map(m => ({ property: m.getAttribute('property'), content: m.content })),
  rootVars: (() => {
    const s = getComputedStyle(document.documentElement);
    const out = {};
    for (let i = 0; i < s.length; i++) {
      const n = s[i];
      if (n.startsWith('--')) out[n] = s.getPropertyValue(n).trim();
    }
    return out;
  })()
});
```

这一步采到：所有 `<img>` / `<video>` 的 URL 和尺寸、所有 `backgroundImage`、SVG 数量、所有 `fontFamily`、favicon / OG 元数据、原站点 `:root` 上定义的 CSS 变量。

### 1.3 强制交互扫描（Mandatory Interaction Sweep）

**目的**：挖出静态截图里看不见的所有行为。

**Scroll sweep** — 用 Browser MCP 从顶部缓慢滚动到底部，每个 section 停下观察：
- header 是否变？记录触发 scrollY。
- 元素是否 fade-in / slide-in 入场？记录哪些和动画类型。
- sidebar / tab indicator 是否随滚动自动切换？记录机制。
- 是否有 scroll-snap 容器？
- 是否非原生 smooth scroll（Lenis 等）？

**Click sweep** — 点击所有看起来可交互的元素（buttons / tabs / pills / links / cards）。对 tabs/pills：**每一个都点开**，记录每个 state 下出现的内容。

**Hover sweep** — 悬停所有可能有 hover 态的元素（buttons / cards / links / images / nav items），记录变化（color / scale / shadow / underline / opacity）及过渡。

**Responsive sweep** — 在 Browser MCP 里切 3 个宽度（1440 / 768 / 390），每个宽度记录哪些 section 布局变了、在什么断点变。

**产出：** `docs/research/BEHAVIORS.md` — 这是你的"行为圣经"，写每个 component spec 时都要引用。

### 1.4 Page Topology

映射页面所有 section，从顶到底。每个 section 起一个工作名，记录：
- 视觉顺序
- 哪些是 fixed/sticky overlay，哪些是 flow 内容
- 整体布局（scroll container / 列结构 / z-index 层）
- section 间依赖（如 floating nav overlay 所有内容）
- **每个 section 的 interaction model**（static / click-driven / scroll-driven / time-driven）

**产出：** `docs/research/PAGE_TOPOLOGY.md` — 组装蓝图。

---

## Phase 2: Foundation Build / 基础数据提取

### `--full` 模式：完整基础设施构建（顺序执行，不派 agent）

这一步碰很多文件，自己做。

1. **更新字体** → `src/app/layout.tsx`，用 `next/font/google` 或 `next/font/local` 配置目标站点实际字体
2. **更新全局 CSS** → `src/app/globals.css`：
   - `:root` / `.dark` 里写入目标站色板
   - 映射到 shadcn token（background / foreground / primary / muted 等）
   - 不匹配 shadcn 的颜色加 custom property
   - 加入全局 keyframes / 工具类 / **smooth scroll CSS**（若检测到 Lenis 等）
3. **创建 TypeScript 类型** → `src/types/`，为观察到的内容结构写 interface
4. **提取 SVG 图标** → 把页面所有 inline `<svg>` 去重，命名为 React 组件写入 `src/components/icons.tsx`（按视觉功能命名：`SearchIcon` / `ArrowRightIcon` / `LogoIcon`）
5. **下载全局资源** → 写 `scripts/download-assets.mjs`，把所有 images / videos / favicons / OG 图片下载到 `public/`。保留有意义的目录结构。并行下载（4 个一批），做 error handling。
6. **更新 metadata** → `layout.tsx` 的 favicon / OG meta / webmanifest
7. **验证构建**：`npm run build` 必须通过

### `--dna-only` 模式：仅提取数据，不写入项目

同样跑 Phase 1.2 的枚举脚本和 Phase 2 的字体/颜色/SVG/资源提取，**但不生成任何项目文件**：

1. 字体信息 → 中间数据（不配 layout.tsx）
2. 颜色值 → 中间数据（不写 globals.css）
3. SVG 形态信息 → 中间数据（不生成 React 组件）
4. 资源 URL + 元数据 → **只记录清单**，不下载到 public/
5. 跳过 TypeScript 类型创建
6. 跳过构建验证

**所有中间数据都在 Phase 3 流向 DNA JSON。**

---

## Phase 3: Design DNA Extraction ⭐ 核心阶段

用程序精确提取的原始 CSS 值填充三维 schema。三个维度分别用不同方式获得：

### 3.1 Dimension 1: `design_system`（程序 100% 精确提取）

利用 Phase 1 / Phase 2 中通过 `getComputedStyle()` 采到的精确值，按 schema 自动归类。

**通用采样脚本**（通过 Browser MCP 注入）：

```javascript
// DNA Dimension-1 collector — gather full style distribution
(function() {
  const selector = '*';
  const sample = [...document.querySelectorAll(selector)].slice(0, 2000);
  const out = {
    colors: {},         // { hex: { count, asText, asBg, asBorder } }
    fontSizes: {},      // { px: count }
    fontWeights: {},
    fontFamilies: {},
    lineHeights: {},
    letterSpacings: {},
    paddings: {},
    margins: {},
    gaps: {},
    radii: {},
    shadows: {},
    transitions: {},
    displays: {},
    maxWidths: {},
    headingFonts: new Set(),
    bodyFonts: new Set(),
    headingSizes: [],   // [{tag, size, weight, family, lh}]
    rootVars: {}
  };

  const bump = (bag, key) => { if (!key) return; bag[key] = (bag[key] || 0) + 1; };
  const bumpColor = (hex, kind) => {
    if (!hex || hex === 'rgba(0, 0, 0, 0)' || hex === 'transparent') return;
    out.colors[hex] = out.colors[hex] || { count: 0, asText: 0, asBg: 0, asBorder: 0 };
    out.colors[hex].count++;
    out.colors[hex][kind]++;
  };

  sample.forEach(el => {
    const s = getComputedStyle(el);
    bumpColor(s.color, 'asText');
    bumpColor(s.backgroundColor, 'asBg');
    bumpColor(s.borderColor, 'asBorder');
    bump(out.fontSizes, s.fontSize);
    bump(out.fontWeights, s.fontWeight);
    bump(out.fontFamilies, s.fontFamily);
    bump(out.lineHeights, s.lineHeight);
    bump(out.letterSpacings, s.letterSpacing);
    bump(out.paddings, s.padding);
    bump(out.margins, s.margin);
    bump(out.gaps, s.gap);
    bump(out.radii, s.borderRadius);
    if (s.boxShadow !== 'none') bump(out.shadows, s.boxShadow);
    if (s.transition !== 'all 0s ease 0s' && s.transition) bump(out.transitions, s.transition);
    bump(out.displays, s.display);
    if (s.maxWidth !== 'none') bump(out.maxWidths, s.maxWidth);

    const tag = el.tagName.toLowerCase();
    if (/^h[1-6]$/.test(tag)) {
      out.headingFonts.add(s.fontFamily);
      out.headingSizes.push({ tag, size: s.fontSize, weight: s.fontWeight, family: s.fontFamily, lh: s.lineHeight, tracking: s.letterSpacing });
    }
    if (tag === 'p' || tag === 'span' || tag === 'li') out.bodyFonts.add(s.fontFamily);
  });

  const rs = getComputedStyle(document.documentElement);
  for (let i = 0; i < rs.length; i++) {
    const n = rs[i];
    if (n.startsWith('--')) out.rootVars[n] = rs.getPropertyValue(n).trim();
  }

  out.headingFonts = [...out.headingFonts];
  out.bodyFonts = [...out.bodyFonts];
  return JSON.stringify(out);
})();
```

把返回值作为原始分布数据，按以下规则归类到 schema：

#### Color 归类

- 把所有出现的颜色按 `count` 降序排
- **面积占比最大的 `asBg` 颜色** → `surface.background`
- 排在前几的 `asBg` 颜色（覆盖卡片/elevated 容器）→ `surface.card`、`surface.elevated`
- **按钮/CTA** 元素（通过选择器 `button, [class*="cta"], [class*="btn"]`）的 `backgroundColor` → `accent.hex` + `accent.role`（"CTA primary"）
- 主导 `asText` 颜色 → 推导 `neutral.scale`（从最深文本 → 最浅背景的灰阶）
- 所有颜色去重后做色相分析 → `palette_type`（"monochromatic" / "complementary" / "analogous" / "triadic" / "split-complementary"）
- 文字最深/背景最浅的对比组合 → `contrast_strategy`（"high contrast" / "subtle layers" / "dark-on-light dominant"）
- `semantic.success/warning/error/info` 从语义选择器识别（`.success` / `.error` / `[role="alert"]`）或留为 `null` 并在 `composite_notes` 注明未观察到

#### Typography 归类

- 把 `fontSizes` 按 px 数值降序去重
- 最大值 → `type_scale.display`；依次向下：`heading_1` / `heading_2` / `heading_3` / `body` / `body_small` / `caption` / `overline`
- 每个尺寸对应的 `weight` / `line_height` / `tracking` 从 `headingSizes` 数组里拿同 `fontSize` 的记录聚合
- `font_families.heading` = `headingFonts`（去重后最高频的）
- `font_families.body` = `bodyFonts` 里最高频的
- `font_families.mono` 从包含 "mono" / "code" / "courier" 的 fontFamily 里找，没有则 `null`
- `font_style_notes`：AI 描述字体感受（"geometric sans with humanist touches"）

#### Spacing 归类

- 从 `paddings` / `margins` / `gaps` 里提取所有独立间距值（px），去重 → 间距集合
- 集合最小公约数 → `base_unit`（通常 4 / 8）
- 按 base_unit 倍数排列 → `scale`（如 `[4, 8, 16, 24, 32, 48, 64]`）
- 根据元素间距密度 → `content_density`（密集 "compact" / 中等 "comfortable" / 稀疏 "spacious"）
- 根据 section 间垂直间距变化 → `section_rhythm`

#### Shape / Elevation / Motion

- `radii` 去重升序 → 最小 → `border_radius.small`；中位 → `medium`；最大（非 9999） → `large`；≥9999 或 50% → `pill`
- `borderColor` / border-style 出现频率 → `border_usage`（"none" / "subtle 1px" / "bold borders" / "only on inputs"）
- `shadows` 集合 → 按模糊半径分类 → `elevation.levels.low/medium/high`；描述整体风格 → `shadow_style`
- `transitions` 解析 duration → 最小/中位/最大 → `motion.duration_scale.micro/normal/macro`；解析 easing → `motion.easing`（"ease-in-out" / "cubic-bezier(...)"）

#### Layout

- `displays` 里 `grid` 比例高 → `grid_system: "css-grid"`；`flex` 为主 → `"flexbox"`
- `maxWidths` 里最高频的容器宽度 → `max_content_width`
- 响应式扫描记录的断点（1440 → 768 → 390 之间切换布局的像素点） → `breakpoints`
- 根据 `textAlign` / `justify-content` 分布 → `alignment_tendency`（"strict grid" / "centered" / "asymmetric" / "mixed"）

#### Iconography

- 来自 Phase 2 提取的 SVG 集合
- 平均 `stroke-width` → `stroke_weight`
- 尺寸分布 → `size_scale`
- 判断风格 → `style`（"line" / "solid" / "duotone" / "hand-drawn"）

#### Components

- 按钮元素（`button` / `[role="button"]` / `.btn` 等）聚合样式 → `button_style`（"ghost buttons with thick borders" 这类描述）
- 输入框 → `input_style`
- 卡片容器（有 `border-radius` + `box-shadow` + 背景差异的重复容器） → `card_style`
- 顶部/侧边导航 → `navigation_pattern`

### 3.2 Dimension 2: `design_style`（AI 认知判断 + 第一维精确数据）

拿着**已归类好的 Dimension 1 数据** + 全页截图 + Phase 1.3 的 BEHAVIORS 记录，让 AI 综合判断：

- `aesthetic.mood`：3–5 个情绪词（["calm", "professional", "warm"]）
- `aesthetic.genre`："corporate SaaS" / "indie creative" / "luxury editorial" / "neo-brutalist" 等
- `aesthetic.personality_traits`：拟人化描述
- `aesthetic.adjectives` / `era_influence` / `visual_metaphor`：根据截图和 token 推断
- `visual_language.whitespace_usage`：结合 `spacing.content_density` 和截图留白比例
- `visual_language.complexity`：结合元素密度和 ornament 程度
- `composition.balance_type`：根据布局对称性（中心对齐 / 左右交错 / 放射）
- `composition.hierarchy_method`：根据字号差、颜色权重、空间隔离方式选一
- `interaction_feel.hover_behavior` / `transition_personality`：**直接来自 Phase 1.3 的 hover sweep 和 motion 记录**
- `interaction_feel.microinteraction_density`：按扫描到的可交互元素数 vs. 有动效的元素数估计
- `brand_voice_in_ui.tone` / `cta_style`：来自真实文案（CTA 按钮文本、表单 label、error 文案）

**关键**：Dimension 2 的判断**基于 Dimension 1 的精确数据**，不是纯看图猜，可信度显著高于纯视觉判断。

### 3.3 Dimension 3: `visual_effects`（代码扫描 + AI 判断混合）

**程序扫描脚本**（Browser MCP 执行）：

```javascript
// visual_effects tech-stack scanner
(function() {
  const all = [...document.querySelectorAll('*')];
  const cs = el => getComputedStyle(el);

  return JSON.stringify({
    canvas: document.querySelectorAll('canvas').length,
    canvasWebGL: [...document.querySelectorAll('canvas')].some(c => {
      try { return !!(c.getContext('webgl2') || c.getContext('webgl')); } catch { return false; }
    }),
    threeJs: !!window.THREE || !!document.querySelector('script[src*="three"]'),
    pixiJs: !!window.PIXI || !!document.querySelector('script[src*="pixi"]'),
    gsap: !!window.gsap || !!document.querySelector('script[src*="gsap"]'),
    lottie: !!window.lottie || !!document.querySelector('script[src*="lottie"]') || document.querySelectorAll('[class*="lottie"]').length,
    anime: !!window.anime || !!document.querySelector('script[src*="anime"]'),
    lenis: !!document.querySelector('.lenis, [data-lenis], [class*="lenis"]') || !!window.Lenis,
    locomotiveScroll: !!document.querySelector('.locomotive-scroll, [data-scroll-container]'),

    svgAnimateCount: document.querySelectorAll('svg animate, svg animateTransform, svg animateMotion').length,
    svgSmilActive: [...document.querySelectorAll('svg animate')].some(a => a.beginElement),

    hasCustomCursor: cs(document.body).cursor !== 'auto' && cs(document.body).cursor !== 'default',
    customCursorElements: all.filter(el => cs(el).cursor === 'none').length,

    backdropFilterCount: all.filter(el => {
      const bf = cs(el).backdropFilter || cs(el).webkitBackdropFilter;
      return bf && bf !== 'none';
    }).length,

    mixBlendModes: [...new Set(all.map(el => cs(el).mixBlendMode).filter(v => v && v !== 'normal'))],
    filters: [...new Set(all.map(el => cs(el).filter).filter(v => v && v !== 'none'))].slice(0, 10),
    clipPaths: [...new Set(all.map(el => cs(el).clipPath).filter(v => v && v !== 'none'))].slice(0, 10),

    scrollSnapContainers: all.filter(el => cs(el).scrollSnapType !== 'none').length,
    stickyElements: all.filter(el => cs(el).position === 'sticky').length,

    animationTimelineUsed: all.some(el => cs(el).animationTimeline && cs(el).animationTimeline !== 'auto'),

    iframeVideoBg: !!document.querySelector('video[autoplay][muted][loop]'),
    videoBgCount: document.querySelectorAll('video[autoplay]').length
  });
})();
```

**AI 判断部分**（结合扫描结果 + 截图 + BEHAVIORS.md）：

- `overview.primary_technology`：从扫描结果选（"CSS only" / "Canvas 2D" / "WebGL/Three.js" / "GSAP" / "Lottie" / "SVG SMIL"）
- `overview.effect_intensity`：按总效果数 + 动画强度分档（"none" / "subtle-accent" / "moderate" / "heavy-immersive"）
- `overview.performance_tier`："lightweight" / "medium" / "heavy"
- `overview.fallback_strategy`：若检测到 `prefers-reduced-motion` 处理逻辑则记录
- `background_effects.type`：看背景——gradient + keyframes → `gradient-animation`；canvas 噪点 → `noise-field`；video → `video-bg`
- `particle_systems.*`：若 canvas 存在 + 持续 rAF → AI 看截图描述粒子行为
- `3d_elements.*`：若 `threeJs` 或 `pixiJs` 为真 → AI 判断类型（`hero-model` / `product-viewer` / `scene-bg` / `text-extrusion` / `abstract-geometry`）
- `shader_effects.*`：若有 WebGL shader 代码 → 记录 `type` 和 `noise_type`
- `scroll_effects.*`：结合 `scrollSnapContainers` / `stickyElements` / `animationTimelineUsed` / BEHAVIORS 里的滚动行为
- `text_effects.*`：看 SVG `<animate>` 的 path 或 CSS keyframes 在 text 上的使用
- `cursor_effects.*`：`hasCustomCursor` 为真 → 描述类型（`custom-cursor` / `magnetic-buttons` / `spotlight` / `trail`）
- `image_effects.*`：从 hover sweep 记录 + `filter` / `clipPath` 分布
- `glassmorphism_neumorphism.*`：`backdropFilterCount > 0` → `"glass"`；双向 inset shadow → `"neumorphic-*"`
- `canvas_drawings.*`：canvas 存在但不是 WebGL / 不是粒子 → 描述绘制行为
- `svg_animations.*`：`svgAnimateCount > 0` → 分析每个 `<animate>` 的 attr 判断类型

**任何 `enabled` flag**：当该分类没有任何观察到的行为时，设 `false`。

**特别说明的 `composite_notes`**：用于记录多层叠加效果、实现歧义、性能权衡、或只能通过截图看到而无法代码判断的效果。

### 3.4 输出 DNA JSON

将三维合并为 `docs/dna/design-dna.json`。**每个字段都必须有值，不允许空字符串**——未观察到的枚举字段用文档规定的字面值（如 `"none"`、`enabled: false`），未采样到的度量值使用 `null` 并在 `composite_notes` 注明。

顶层结构：

```jsonc
{
  "meta": {
    "name": "<site-name>",
    "description": "<short description>",
    "source_references": ["<url1>", "<url2>"],
    "created_at": "<ISO 8601>"
  },
  "design_system": { /* Dimension 1 — 按 schema.md 所有字段填充 */ },
  "design_style":  { /* Dimension 2 */ },
  "visual_effects":{ /* Dimension 3 */ }
}
```

> 📖 所有字段严格按 [`references/schema.md`](references/schema.md)。任何字段缺失视为提取失败，回到 Phase 1/2/3 继续采。

### 3.5 `--dna-only` 完成报告

`--dna-only` 模式在此处结束。输出：

```
✅ Design DNA extracted

📄 docs/dna/design-dna.json
   ├─ design_system:  XX/XX fields populated (NN% from programmatic extraction)
   ├─ design_style:   XX/XX fields populated (AI synthesis on Dim-1 data)
   └─ visual_effects: XX/XX fields populated (code scan + AI judgment)

📊 Extraction summary
   - Colors sampled: N unique, top 8: #... #... ...
   - Fonts: <heading> + <body>
   - Spacing base unit: Npx, scale: [...]
   - Effect intensity: <tier>, primary tech: <stack>
   - Unresolved fields (composite_notes): N

📦 Asset inventory (not downloaded)
   - Images: N URLs
   - Videos: N URLs
   - Fonts: N families

→ Next steps?
  1. Adjust any values in design-dna.json before use
  2. Generate a new design from this DNA → invoke design-dna or /impeccable
  3. Full clone this site → re-run with --full
```

---

## Phase 4: Component Specification & Dispatch（仅 `--full`）

> `--dna-only` 模式在 Phase 3 后即结束，不执行 Phase 4–6。

对 PAGE_TOPOLOGY 里的每个 section，循环做四步：**Extract → Write Spec → Dispatch → Merge**。

### Step 1: Extract（逐组件精确提取）

对每个 section：

1. **Section 截图**：用 Browser MCP 滚到该 section，截 viewport，存 `docs/design-references/`
2. **CSS 提取**（对 section 根选择器运行以下脚本）：

```javascript
// Per-component extractor — replace SELECTOR
(function(selector) {
  const el = document.querySelector(selector);
  if (!el) return JSON.stringify({ error: 'Element not found: ' + selector });
  const props = [
    'fontSize','fontWeight','fontFamily','lineHeight','letterSpacing','color',
    'textTransform','textDecoration','backgroundColor','background',
    'padding','paddingTop','paddingRight','paddingBottom','paddingLeft',
    'margin','marginTop','marginRight','marginBottom','marginLeft',
    'width','height','maxWidth','minWidth','maxHeight','minHeight',
    'display','flexDirection','justifyContent','alignItems','gap',
    'gridTemplateColumns','gridTemplateRows',
    'borderRadius','border','borderTop','borderBottom','borderLeft','borderRight',
    'boxShadow','overflow','overflowX','overflowY',
    'position','top','right','bottom','left','zIndex',
    'opacity','transform','transition','cursor',
    'objectFit','objectPosition','mixBlendMode','filter','backdropFilter',
    'whiteSpace','textOverflow','WebkitLineClamp'
  ];
  const extract = e => {
    const cs = getComputedStyle(e);
    const styles = {};
    props.forEach(p => {
      const v = cs[p];
      if (v && v !== 'none' && v !== 'normal' && v !== 'auto' && v !== '0px' && v !== 'rgba(0, 0, 0, 0)') styles[p] = v;
    });
    return styles;
  };
  const walk = (e, depth) => {
    if (depth > 4) return null;
    const kids = [...e.children];
    return {
      tag: e.tagName.toLowerCase(),
      classes: e.className?.toString().split(' ').slice(0, 5).join(' '),
      text: e.childNodes.length === 1 && e.childNodes[0].nodeType === 3 ? e.textContent.trim().slice(0, 200) : null,
      styles: extract(e),
      images: e.tagName === 'IMG' ? { src: e.src, alt: e.alt, naturalWidth: e.naturalWidth, naturalHeight: e.naturalHeight } : null,
      childCount: kids.length,
      children: kids.slice(0, 20).map(c => walk(c, depth + 1)).filter(Boolean)
    };
  };
  return JSON.stringify(walk(el, 0), null, 2);
})('SELECTOR');
```

3. **多状态 A→B Diff**：对任何有多状态的元素（scroll-triggered / hover / active tab）：
   - **State A**：当前状态下跑上面的脚本
   - 通过 Browser MCP 触发状态切换（scroll / click / hover）
   - **State B**：同一元素再跑一次
   - 显式写 diff："property X changes from A to B, triggered by TRIGGER, transition: T"

4. **真实内容**：`element.textContent` / alt / aria-label / placeholder。对 tabbed/stateful 内容，**点击每个 tab** 并分别提取

5. **识别资源**：section 用到的哪些 `public/` 图片/视频、哪些 `icons.tsx` 组件、是否有 **分层图像**（多个 `<img>` / background-image 叠加）

6. **复杂度评估**：section 含多少个 distinct 子组件？（每个有独立样式/结构/行为的元素算一个）

### Step 2: Write the Component Spec File

**路径**：`docs/research/components/<component-name>.spec.md`

**模板**：

```markdown
# <ComponentName> Specification

## Overview
- **Target file:** `src/components/<ComponentName>.tsx`
- **Screenshot:** `docs/design-references/<screenshot-name>.png`
- **Interaction model:** <static | click-driven | scroll-driven | time-driven>
- **DNA tokens referenced:** `--color-primary`, `--radius-md`, `--shadow-low`, `--duration-normal`
  <!-- Builder MUST use these CSS variables, not hardcoded hex/px values. -->

## DOM Structure
<element hierarchy — what contains what>

## Computed Styles (from getComputedStyle — exact values)

### Container
- display: ...
- padding: ... (= var(--space-6) per DNA)
- maxWidth: ...

### <Child 1>
- fontSize: ... (= DNA typography.heading_2.size)
- color: ... (= var(--color-foreground))

### <Child N>
...

## States & Behaviors

### <Behavior name, e.g. "Scroll-triggered floating mode">
- **Trigger:** <exact mechanism — scroll position 50px, IntersectionObserver rootMargin "-30% 0px", click on .tab-btn, hover>
- **State A (before):** maxWidth: 100vw, boxShadow: none, borderRadius: 0
- **State B (after):** maxWidth: 1200px, boxShadow: var(--shadow-med), borderRadius: var(--radius-lg)
- **Transition:** transition: all var(--duration-normal) var(--ease)
- **Implementation approach:** <CSS transition + scroll listener | IntersectionObserver | animation-timeline>

### Hover states
- **<Element>:** <property>: <before> → <after>, transition: ...

## Per-State Content (if applicable)

### State: "Featured"
- Title: "..."
- Cards: [{ title, description, image, link }, ...]

### State: "Productivity"
- Cards: [...]

## Assets
- Background: `public/images/<file>.webp`
- Overlay: `public/images/<file>.png`
- Icons: <ArrowIcon>, <SearchIcon> from icons.tsx

## Text Content (verbatim)
<all text copied from live site>

## Responsive Behavior
- **Desktop (1440px):** <layout>
- **Tablet (768px):** <what changes>
- **Mobile (390px):** <what changes>
- **Breakpoint:** switches at ~<N>px
```

**DNA token 规则**：
- spec 里出现的每个 CSS 值要么引用 DNA token（`var(--color-primary)`），要么标注"hardcoded — not in DNA"（极少数情况）
- builder 的最终代码**禁止硬编码** DNA 已定义的 token

### Step 3: Dispatch Builders

基于复杂度派遣 builder agent 到 git worktree：

- **简单 section**（1–2 子组件）：一个 builder 做整个 section
- **复杂 section**（3+ distinct 子组件）：拆。一个 builder 做一个子组件，再加一个 builder 做 wrapper（wrapper 依赖子组件，最后派）

每个 builder 收到：
- **完整 spec 文件内容 inline**（不要说 "go read the spec file"）
- section 截图路径
- 共享组件引用（`icons.tsx` / `cn()` / shadcn primitives）
- 目标文件路径（`src/components/<Name>.tsx`）
- **DNA token 使用要求**：必须用 `var(--...)` 而非硬编码
- 完成前必须 `npx tsc --noEmit` 通过
- 响应式断点和变化说明

**不要等**。派完一个 section 的 builder 立刻去提取下一个 section。builder 在 worktree 并行干活。

### Step 4: Merge

builder 完成后：
- merge worktree 到 main
- 解决冲突（你有完整上下文，能做明智判断）
- 每次 merge 后跑 `npm run build`
- 若 merge 引入 type error 立刻修

**循环 Extract → Spec → Dispatch → Merge 直到所有 section 建完。**

---

## Phase 5: Page Assembly（仅 `--full`）

所有 section 建完、merge 完后，在 `src/app/page.tsx` 里组装：

- import 所有 section 组件
- 实现 page-level 布局（scroll container / 列 / sticky / z-index）
- 连真实内容到组件 props
- 实现 page-level 行为：scroll snap / scroll-driven 动画 / 主题过渡 / IntersectionObserver / smooth scroll（Lenis 等）
- **`globals.css` 的 CSS 变量必须已经由 DNA JSON 的 `design_system` 生成**（Phase 2 完成时已写入，此处验证一致）
- 验证：`npm run build` 干净通过

---

## Phase 6: Visual QA Diff（仅 `--full`）

组装完成**不能**就宣布完工。做三层 QA：

### 6.1 并排视觉对比

- 同时打开原站和克隆站（或同视口截图）
- 从上到下 section 对 section 比对
  - **1440px (desktop)**：逐段检查
  - **390px (mobile)**：逐段检查
- 每个差异：
  - 查 spec 文件：值提对了吗？
  - spec 错了 → Browser MCP 重提 → 更新 spec → 修组件
  - spec 对但 builder 做错了 → 修组件对齐 spec

### 6.2 交互验证

- 从头滚到尾：smooth scroll 手感对吗？header 过渡正确吗？
- 点每个 button / tab / card
- hover 所有可交互元素
- 测所有动画

### 6.3 DNA 一致性验证（新增）

- 克隆代码里所有颜色是否**全部来自** DNA `design_system.color` 色板？
- 字体是否匹配 `font_families.heading` / `.body`？
- 间距是否遵循 `spacing.scale`？
- 视觉特效实现是否匹配 `visual_effects` 规格（type / technology / params）？
- 若有偏差：优先改代码对齐 DNA；若 DNA 本身提取错 → 回 Phase 3 修 DNA JSON，然后再对齐代码

---

## Pre-Dispatch Checklist（仅 `--full`，派 builder 前必过）

- [ ] spec 文件已写到 `docs/research/components/<name>.spec.md`，全部 section 填满
- [ ] spec 里每个 CSS 值都来自 `getComputedStyle()`，不是估的
- [ ] spec 里每个 token 已映射到 DNA JSON 的对应字段
- [ ] interaction model 明确写出（static / click / scroll / time）
- [ ] 多状态组件每个 state 的内容和样式都采到
- [ ] scroll-driven 组件的 trigger 阈值、before/after、transition 都采到
- [ ] hover 态 before/after + transition timing 都采到
- [ ] section 所有图片（含 overlay 和 layered）都枚举到
- [ ] 响应式行为至少 desktop + mobile 记录
- [ ] 文本内容逐字从站点复制，没改写
- [ ] builder prompt 的 spec 部分 < 150 行；超了就拆

---

## Anti-Patterns（别做这些）

- ❌ **别把 scroll-driven UI 做成 click-based**（#1 最贵错误）。先滚再点来判定 interaction model
- ❌ **别只提默认状态**。tabs 要点遍；header 要在 0 和 100 各提一次
- ❌ **别漏 overlay/layered 图**。每个容器遍历全部 `<img>` 和 `backgroundImage`
- ❌ **别把视频/动画做成 HTML mockup**。先查是否 `<video>` / Lottie / canvas
- ❌ **别近似 Tailwind class**。"看起来像 `text-lg`" 错。精确值 18px / line-height 24px 才是真的
- ❌ **别搞一次性 monolithic commit**。整套 pipeline 的意义就是 incremental + verified
- ❌ **别让 builder 读外部文档**。spec inline 进 prompt，builder 不需要读任何外部 md
- ❌ **别跳过资源提取**。没有真图真视频真字体，不管 CSS 多对都看着像假货
- ❌ **别给 builder 一大块 scope**。spec 在变长就是该拆的信号
- ❌ **别把不相关 section 绑到一个 agent**（CTA + footer 是两个组件，不要塞给一个 agent）
- ❌ **别跳响应式提取**。只测 desktop 会在 tablet/mobile 碎
- ❌ **别忘 smooth scroll 库**。Lenis / Locomotive 会让你原生 scroll 的克隆一眼就被抓包
- ❌ **别不写 spec 就派 builder**。spec 强制详尽提取 + 审计 artifact
- ❌ **别硬编码 DNA 已定义的 token**。用 `var(--color-primary)` 而不是 `#0A84FF`
- ❌ **别让 DNA JSON 留空字符串**。未观察到的字段使用 `null` 或 `"none"` 或 `enabled: false`
- ❌ **别跳过 Phase 6.3 的 DNA 一致性检查**。clone 代码和 DNA 漂移会让两者都逐渐失真

---

## 完成报告模板

### `--dna-only` 完成

见 3.5。

### `--full` 完成

```
✅ Design Clone complete

📄 Deliverables
   ├─ docs/dna/design-dna.json          (Design DNA profile)
   ├─ docs/research/BEHAVIORS.md        (interaction sweep)
   ├─ docs/research/PAGE_TOPOLOGY.md    (assembly blueprint)
   ├─ docs/research/components/*.spec.md (N specs)
   ├─ docs/design-references/           (N screenshots)
   └─ src/ + public/                     (Next.js clone)

📊 Build metrics
   - Sections built: N
   - Components created: N
   - Spec files written: N   ← must equal components
   - Assets downloaded: N images, N videos, N SVG, N fonts
   - npm run build: ✅ / ❌

🎨 DNA consistency
   - Colors traced to DNA palette:        N/N
   - Font families match DNA:             ✅ / ❌
   - Spacing follows DNA scale:           ✅ / ❌
   - Visual effects match DNA spec:       ✅ / ❌

🔍 Visual QA (1440px + 390px)
   - Sections verified: N/N
   - Interactive behaviors verified: N/N
   - Remaining discrepancies: N (see <list>)

⚠️  Known gaps / limitations
   - <any unresolved items>
```

---

## 参考

- [`references/schema.md`](references/schema.md) — Design DNA 三维 schema 完整字段定义
- [`references/generation-guide.md`](references/generation-guide.md) — DNA JSON → 代码的映射规则
