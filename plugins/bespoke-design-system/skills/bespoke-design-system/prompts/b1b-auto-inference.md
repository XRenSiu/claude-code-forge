# B1b — 全自动推断（auto 模式）

> 当 SKILL.md 主流程进入 B1b 时读取本文件作为执行指引。

## 你的任务

不向用户问任何问题，从用户已给的需求 + 项目上下文推断出完整的调性画像。所有缺失字段走 `grammar/meta/defaults.yaml` 推断，并在画像的 `inferred_fields` 中标注。

---

## Step 1 — 抓取所有可用上下文

按下列顺序读取，**不要遗漏**：

1. 用户当前消息中的产品需求描述
2. 用户最近 3 条消息（往往含暗示性偏好，如"我不喜欢 Linear 那种冷感"）
3. 当前工作目录有 `CLAUDE.md` / `README.md` / `package.json` 时读取（项目类型、技术栈、目标用户线索）
4. 当前工作目录有 logo / 现有设计资产路径（图片、`globals.css`、`tailwind.config.*`）→ 记录但不强行解析（Phase B 不做颜色提取，避免越权）
5. 用户历史会话中如果出现过偏好声明（"我做 X 的时候喜欢极简")，作为软证据

把所有上下文聚合成一个临时 `context_bundle` 备用。

## Step 2 — 推断 product_category

从需求关键词命中 `grammar/meta/defaults.yaml` 的 `category_defaults` 字典：

- 命中明确分类（"developer_tool" / "spiritual_saas" / "ecommerce" / "content_platform" 等）→ 直接用
- 命中多个 → 选最具体的（developer_tool 比 b2b_saas 更具体）
- 全没命中 → 查 `defaults.yaml` 的 `_uncategorized` 兜底配置；记录到 `inferred_fields`

## Step 3 — 用 category defaults 填充骨架

从 `defaults.yaml` 读取该 category 的：

- `likely_archetypes` → 画像 `brand_archetypes.primary` / `secondary`
- `likely_kansei` → 画像 `kansei_words.positive`
- `avoid_kansei` → 画像 `kansei_words.reverse_constraint`
- `sd_defaults` → 画像 `semantic_differentials`

**这一步只填 default 值**。下一步会被上下文覆盖。

## Step 4 — 上下文覆盖

按可信度从高到低应用上下文，覆盖 default 值：

1. **明确否定 / 反向声明**（最高优先级）：用户说"不要像 X"、"避免 Y" → 加到 `kansei_words.reverse_constraint`
2. **正向锚点**：用户说"想要类似 Linear 的精度感" → 把 Linear 的 archetype（Sage+Creator）和 kansei（structured/precise/modern）合入画像
3. **行业暗示**：项目中存在 React + TypeScript + Tailwind → 受众多半技术化，把 SD `serious_to_playful` 偏负
4. **品牌资产暗示**：已有 logo 是手写体 → SD `modern_to_classical` 偏正

每次覆盖**记录到 `inferred_fields`**，格式：

```yaml
inferred_fields:
  - field: brand_archetypes.primary
    value: Sage
    source: category_default + user_keyword "developer"
    confidence: high | medium | low
```

## Step 5 — 反向约束兜底

任何 category 都自动补几条通用 `reverse_constraint`：

- `ai_slop`（紫渐变 + Inter + 圆角卡片那套）—— **永远在 reverse_constraint**
- `generic_corporate`（无个性的企业站感）

加到 `kansei_words.reverse_constraint` 末尾。

## Step 6 — 合成画像

输出完整画像（schema 见 SKILL.md §六 3.3.5），`mode` 字段填 `auto`，`inferred_fields` 含所有推断条目。

**直接进入 B2**，不向用户确认。

---

## defaults.yaml 期望结构（如果文件不存在或不完整时的兜底）

```yaml
category_defaults:
  spiritual_saas:
    likely_archetypes: [Sage, Magician]
    likely_kansei: [mystical, trustworthy, calm, structured]
    avoid_kansei: [aggressive, playful, casual]
    sd_defaults:
      warm_to_cold: -0.1
      ornate_to_minimal: 0.2
      serious_to_playful: -0.6
      modern_to_classical: 0.0

  developer_tool:
    likely_archetypes: [Sage, Creator]
    likely_kansei: [structured, precise, modern, calm]
    avoid_kansei: [decorative, playful]
    sd_defaults:
      warm_to_cold: 0.2
      ornate_to_minimal: 0.6
      serious_to_playful: -0.3
      modern_to_classical: -0.4

  _uncategorized:
    likely_archetypes: [Sage, Everyman]
    likely_kansei: [trustworthy, clear, calm]
    avoid_kansei: [aggressive]
    sd_defaults:
      warm_to_cold: 0.0
      ornate_to_minimal: 0.0
      serious_to_playful: -0.2
      modern_to_classical: -0.2
```

如果 `defaults.yaml` 缺失，**直接停下**告诉用户："`grammar/meta/defaults.yaml` 缺失，无法在 auto 模式下安全推断默认值。请运行维护流程初始化默认值，或切换到 interactive 模式。"

---

## 检查清单（B1b 产出前必过）

- [ ] `mode: auto`
- [ ] `inferred_fields` 不为空（auto 模式必然有推断字段）
- [ ] `kansei_words.reverse_constraint` 至少含 `ai_slop` 和 `generic_corporate`
- [ ] 每个 inferred_fields 项有 `source` 和 `confidence`
- [ ] 画像 9 大字段全部填充（无 null）
- [ ] 上下文证据全部用上（用户消息、CLAUDE.md、项目文件已扫描）
