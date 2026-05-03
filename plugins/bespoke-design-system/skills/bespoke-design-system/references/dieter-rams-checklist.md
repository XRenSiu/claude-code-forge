# Dieter Rams 十条 — 反向 Anti-pattern 清单

> Rams 在 1970s 提出"good design"的 10 项原则。本文档把它们倒置作为 anti-pattern 清单，由 archetype_check 和 anti-slop-blacklist 引用。

## Rams 十条 → 设计反例（违反时是 anti-pattern）

| # | Rams 原则 | 设计违反时的特征（anti-pattern） |
|---|---|---|
| 1 | Innovative — 创新与技术发展并行 | 产品做出一年前就有的同质化方案，没有 typeface / chromatic / interaction 的新探索 |
| 2 | Useful — 强调实用性 | 装饰性 chrome 占据大量视觉权重，功能 surface 反被弱化 |
| 3 | Aesthetic — 美感来自精确 | 圆角随意（4 / 6 / 8 / 12 同 page 混用）、间距不在 grid 上、颜色饱和度无理由 |
| 4 | Understandable — 不需要说明 | 重要 action 用 ghost button + small icon-only 表达，需要标签解释 |
| 5 | Unobtrusive — 不喧宾夺主 | brand chromatic 被装饰使用（多 section 重复），不留给关键 action |
| 6 | Honest — 不假装 | text-button 看起来像 link、disabled state 看起来像 enabled、错误提示看起来像 success |
| 7 | Long-lasting — 经得起时间 | 跟随短期 trend（neumorphism / glassmorphism 全套），3 年后看会过时 |
| 8 | Thorough — 关注细节 | hover state 缺失、focus ring 不一致、touch target < 36px、空状态无 |
| 9 | Environmentally friendly — 可持续 | 大量装饰图片不优化加载、动画 60fps 全程跑 GPU、暗色模式仅作为切换无优化 |
| 10 | As little design as possible — 少即是多 | 每个 section 都有装饰元素、多种字体、多种 spacing scale、多种 radius |

## 在本 skill 中的角色

### archetype_check

对所有 archetype 都自动添加这些"通用 anti-pattern"作为隐含 never list：

- ⚠️ Rams #5：brand chromatic 装饰使用（duplicate-brand 信号）
- ⚠️ Rams #6：text 看起来像 link、ghost 看起来像 disabled（label semantic mismatch）
- ⚠️ Rams #7：neumorphism / aggressive glassmorphism 全套（trend 跟随）
- ⚠️ Rams #10：多 family / 多 radius scale / 多 spacing scale 同时使用

### anti-slop-blacklist

`anti-slop-blacklist.md` 中的"AI slop"组合（紫渐变 + Inter + 圆角卡片）正是 Rams #1 + #7 + #10 的违反——同质化 + 跟随 trend + 过度元素。

## 关于 Rams 与"品味"

Rams 十条**不能保证有品味**——很多遵循它们的设计仍然平庸。但它们能保证**没有明显错误**。这与本 skill 的定位一致：5 项 check 不保证上限，只保证下限。

## 参考

- Vitsoe, "Dieter Rams: ten principles for good design": https://www.vitsoe.com/us/about/good-design
- Sophie Lovell, *Dieter Rams: As Little Design as Possible* (Phaidon, 2011)
