# Token Schema (v1.5.0 — single source of truth)

> 这份文档是 `grammar/tokens/<system>.json` 与 `<output_dir>/draft-tokens.json` 的**唯一权威 schema**。
> SKILL.md §六 §3.3.1、`prompts/*.md`、`tools/extract_tokens.py`、`checks/*.py` 都引用本文档而不复述。

---

## 顶层结构

```json
{
  "_meta": {
    "system_name": "linear-app",
    "source": "open-design-71",
    "extracted_at": "2026-05-04T00:00:00Z",
    "extraction_method": "programmatic_a1 | b4_synthesized",
    "tool_version": "1.0.0",
    "schema_version": "1.0.0"
  },

  "color":         { ... },
  "typography":    { ... },
  "spacing":       { ... },
  "radius":        { ... },
  "components":    { ... },   // optional — populated by B4
  "depth_elevation": { ... }, // optional
  "motion":        { ... },
  "responsive":    { ... },
  "icon":          { ... },   // optional
  "design":        { ... },   // optional — high-level flags

  "sections_present":     ["color", "typography", ...],
  "sections_unhandled":   [],
  "sections_meta_for_llm": ["visual_theme", "agent_guide"],
  "llm_followup_hints":   ["..."]
}
```

---

## color

```json
{
  "bg": {
    "canvas":   "#0A0B0F",
    "panel":    "#12141B",
    "elevated": "#1A1D27",
    "overlay":  "#232735"
  },
  "text": {
    "primary":   "#E5E6EE",
    "secondary": "#A8ABBE",
    "tertiary":  "#6F7388",
    "disabled":  "#4A4D5C",
    "max_lightness": 0.92,
    "is_pure_white": false
  },
  "brand": {
    "primary":          "#5764D5",
    "primary_hsl":      [234, 0.60, 0.59],
    "hover":            "#6772E1",
    "active":           "#4A56C5",
    "on_text":          "#FFFFFF",
    "chromatic_count":  1,
    "saturation_max":   0.60,
    "saturation_min":   0.55,
    "lightness_at_brand": 0.59,
    "hue":              234,
    "identity_hexes":   ["#5764D5"]
  },
  "state": {
    "running":         "#56C896",
    "awaiting_review": "#E8B45A",
    "success":         "#6FCF97",
    "failed":          "#E15B5B",
    "idle":            "#7B7F92"
  },
  "border": {
    "subtle":      "rgba(255,255,255,0.06)",
    "default":     "rgba(255,255,255,0.10)",
    "strong":      "rgba(255,255,255,0.14)",
    "alpha_range": [0.05, 0.14]
  },
  "contrast": {
    "body_on_bg":      14.5,
    "secondary_on_bg": 7.8,
    "tertiary_on_bg":  4.6,
    "brand_on_canvas": 5.1,
    "brand_on_text":   4.6
  },
  "dark_surface": {
    "lightness_min":     0.04,
    "lightness_steps":   [0.04, 0.08, 0.13, 0.17],
    "stepping_strategy": "luminance"
  },
  "gradient_count":         0,
  "is_pure_monochromatic":  false,
  "all_hex_colors":         ["#0A0B0F", "..."]
}
```

### color.brand 的关键字段（v1.5.0 + Issue 9 修复后）

| 字段 | 用途 | 谁读 |
|---|---|---|
| `chromatic_count` | brand 识别色数量（**不**包括 state/text/text-tinted） | archetype_check Sage rule |
| `identity_hexes` | brand 角色色 hex 列表（用于 saturation_max 精确计算） | archetype_check fallback |
| `saturation_max` | brand 最大饱和度 | archetype_check Sage/Magician rule |

**v1.5.0 起 archetype_check 优先读 `chromatic_count` / `identity_hexes`，缺失才回落 all_hex_colors fallback**。token 作者应**显式声明** brand 角色字段。

---

## typography

```json
{
  "display": {
    "family":       "Geist",
    "fallback":     ["Geist Variable", "Inter Display", "system-ui"],
    "weight_range": [400, 590]
  },
  "body": { "family": "Geist", "fallback": [...], "weight_range": [400, 510] },
  "mono": { "family": "Geist Mono", "fallback": [...] },
  "cjk":  { "family": "HarmonyOS Sans SC", "fallback": [...], "strategy": "latin_first_cjk_fallback" },
  "scale": {
    "base":             14,
    "values":           [12, 13, 14, 16, 18, 20, 24, 30, 36, 48, 64],
    "ratio_consistent": true,
    "ratio":            1.2,
    "ratio_max":        1.4
  },
  "weight": {
    "regular":     400,
    "emphasis":    510,
    "strong":      590,
    "max":         590,
    "no_700_bold": true
  },
  "letter_spacing": {
    "display_64px": "-0.022em",
    "body_14px":    "-0.005em",
    "small_12px":   "0",
    "strategy":     "tighter_at_display_relaxes_at_body"
  },
  "line_height": {
    "display":       1.05,
    "heading":       1.2,
    "body":          1.5,
    "compact_label": 1.3
  },
  "opentype_features": ["cv01", "ss03", "tnum"]
}
```

---

## spacing

```json
{
  "base":  4,
  "scale": [4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 120],
  "panel_padding":         [16, 24],
  "section_min_vertical":  64,
  "no_explicit_section_dividers": true
}
```

⚠️ **必须用 `base` 不是 `base_unit_px`**——v1.4.0 的 archetype_check 因为字段名错把 Sage 的 spacing.base ≥ 4 规则搞坏了一段时间。v1.5.0 修复后 schema 与代码对齐。

---

## radius

```json
{
  "none": 0,
  "sm":   4,
  "md":   6,
  "lg":   8,
  "max":  8,
  "role_radius_pairs": {
    "button": 6,
    "card":   8,
    "input":  6
  }
}
```

`max` 字段是上限断言（用于 archetype_check radius>16 触发 Sage warning）。

---

## components / depth_elevation / motion / responsive / icon / design

可选 sections，通常由 B4 阶段填写到 draft-tokens（用于 B5 check）。具体字段参考 `examples/<system>/draft-tokens.json`。

---

## 必填 vs 可选

**必填**：`color.bg.*` / `color.text.primary` / `color.brand.primary` / `typography.body.family` / `spacing.base` / `radius.max`。

**强烈建议**（B5 check 准确性依赖）：`color.brand.chromatic_count` / `color.brand.identity_hexes` / `color.contrast.body_on_bg` / `typography.weight.max` / `motion.has_bounce_easing` / `design.flat_only`。

**可选**：其它所有字段。
