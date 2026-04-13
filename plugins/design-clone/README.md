# Design Clone

> 从任意网站精确提取**三维设计画像（Design DNA）**，并可选生成**像素级克隆源码**。

核心能力：

- Browser MCP + `getComputedStyle()` 程序化提取精确 CSS 值，并行 builder 构建
- 三维 schema（design_system / design_style / visual_effects）结构化描述设计身份

## 安装

```bash
/plugin marketplace add XRenSiu/claude-code-forge
/plugin install design-clone@claude-code-forge
```

## 使用

### 仅提取设计数据（`--dna-only`）

输出一份 `design-dna.json`，不生成克隆代码。

```bash
/design-clone --dna-only https://example.com
/design-clone --dna-only https://site-a.com https://site-b.com   # 多站合并
```

### 完整克隆（`--full`，默认）

输出 DNA JSON + 基于 Next.js 的像素级克隆源码。

```bash
/design-clone https://example.com
/design-clone --full https://example.com
```

## 运行前置

- 已连接 Browser MCP（Chrome MCP / Playwright MCP / Browserbase / Puppeteer 均可，优先 Chrome MCP）
- `--full` 模式需要 Next.js + shadcn/ui + Tailwind v4 脚手架就位（`npm run build` 能跑通）

## 产出

| 路径 | 模式 | 内容 |
|------|------|------|
| `docs/dna/design-dna.json` | 两种 | 三维设计画像（150+ 字段） |
| `docs/research/BEHAVIORS.md` | 两种 | 交互行为清单 |
| `docs/research/PAGE_TOPOLOGY.md` | 两种 | 页面拓扑图 |
| `docs/design-references/` | 两种 | 全页 + 分段截图（1440px / 390px） |
| `docs/research/components/*.spec.md` | `--full` | 组件 spec 文件 |
| `src/`, `public/` | `--full` | Next.js 克隆源码 |

## 核心设计

**提取精度分层：**
- **Dimension 1 (design_system)**：100% 程序提取，零猜测
- **Dimension 2 (design_style)**：AI 基于第一维精确数据 + 截图做定性判断
- **Dimension 3 (visual_effects)**：代码扫描（Canvas/WebGL/Three.js/GSAP/Lottie）+ AI 视觉判断

**DNA ↔ 克隆一致性：** `globals.css` 变量映射到 DNA `design_system` token，组件 spec 引用 token 名而非硬编码值，Phase 6 做一致性验证。

## 文件结构

```
plugins/design-clone/
├── .claude-plugin/plugin.json
├── skills/design-clone/
│   ├── SKILL.md                  ← 主入口
│   └── references/
│       ├── schema.md             ← DNA 三维 schema
│       └── generation-guide.md   ← DNA → 代码 生成指南
├── LICENSE
└── README.md
```

## License

MIT
