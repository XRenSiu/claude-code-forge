---
persona_skill: {PERSONA_SKILL}
persona_skill_version: {PERSONA_SKILL_VERSION}
persona_judge_version: {PERSONA_JUDGE_VERSION}
evaluated_at: {EVALUATED_AT}
overall_score_raw: {OVERALL_SCORE_RAW}
overall_score_normalized: {OVERALL_SCORE_NORMALIZED}
pass_threshold_raw: {PASS_THRESHOLD_RAW}
verdict: {VERDICT}
density_score: {DENSITY_SCORE}
critical_failures: {CRITICAL_FAILURES}
dimensions:
  known_test: {KNOWN_TEST_SCORE}
  edge_test: {EDGE_TEST_SCORE}
  voice_test: {VOICE_TEST_SCORE}
  knowledge_delta: {KNOWLEDGE_DELTA_SCORE}
  mindset_transfer: {MINDSET_TRANSFER_SCORE}
  anti_pattern_specificity: {ANTI_PATTERN_SPECIFICITY_SCORE}
  specification_quality: {SPECIFICATION_QUALITY_SCORE}
  structure: {STRUCTURE_SCORE}
  density: {DENSITY_DIMENSION_SCORE}
  internal_tensions: {INTERNAL_TENSIONS_SCORE}
  honest_boundaries: {HONEST_BOUNDARIES_SCORE}
  primary_source_ratio: {PRIMARY_SOURCE_RATIO_SCORE}
---

<!--
  Validation Report Template / 验证报告模板
  ------------------------------------------------------------------
  此模板严格遵循 plugins/persona-distill/contracts/validation-report.schema.md。
  placeholder 使用 {UPPER_SNAKE_CASE} 语法；渲染前所有 {...} 必须被替换。
  7 个 H2 段必须保留且顺序不得变动，distill-meta 可能按段扫描。
  Frontmatter 字段名与顺序锁死 (契约硬约束)——绝不允许增删字段。
  -->

## Summary

{SUMMARY_PARAGRAPH}

<!-- 1-3 句：判决 + 首要隐忧。示例：
     "PASS at {OVERALL_SCORE_NORMALIZED}/100. Strongest on voice and known-test reproduction;
      weakest on density (still some 正确废话 in decision-heuristics §3)."
     末尾必须注明本次评估使用的阈值集合：
     pass_threshold_raw={PASS_THRESHOLD_RAW}, density_floor={DENSITY_FLOOR},
     required_tensions={REQUIRED_TENSIONS}, required_boundaries={REQUIRED_BOUNDARIES},
     primary_source_min={PRIMARY_SOURCE_MIN}, critical_failure_count={CRITICAL_FAILURE_COUNT}
-->

Thresholds in effect: `pass_threshold_raw={PASS_THRESHOLD_RAW}`, `density_floor={DENSITY_FLOOR}`, `required_tensions={REQUIRED_TENSIONS}`, `required_boundaries={REQUIRED_BOUNDARIES}`, `primary_source_min={PRIMARY_SOURCE_MIN}`, `critical_failure_count={CRITICAL_FAILURE_COUNT}`.

## Dimension Scores

| Dimension | Score | Max | Notes |
| --- | --- | --- | --- |
| Known Test | {KNOWN_TEST_SCORE} | 10 | {KNOWN_TEST_NOTES} |
| Edge Test | {EDGE_TEST_SCORE} | 10 | {EDGE_TEST_NOTES} |
| Voice Test | {VOICE_TEST_SCORE} | 10 | {VOICE_TEST_NOTES} |
| Knowledge Delta | {KNOWLEDGE_DELTA_SCORE} | 10 | {KNOWLEDGE_DELTA_NOTES} |
| Mindset Transfer | {MINDSET_TRANSFER_SCORE} | 10 | {MINDSET_TRANSFER_NOTES} |
| Anti-Pattern Specificity | {ANTI_PATTERN_SPECIFICITY_SCORE} | 10 | {ANTI_PATTERN_SPECIFICITY_NOTES} |
| Specification Quality | {SPECIFICATION_QUALITY_SCORE} | 5 | {SPECIFICATION_QUALITY_NOTES} |
| Structure | {STRUCTURE_SCORE} | 5 | {STRUCTURE_NOTES} |
| Density | {DENSITY_DIMENSION_SCORE} | 10 | {DENSITY_NOTES} |
| Internal Tensions | {INTERNAL_TENSIONS_SCORE} | 10 | {INTERNAL_TENSIONS_NOTES} |
| Honest Boundaries | {HONEST_BOUNDARIES_SCORE} | 10 | {HONEST_BOUNDARIES_NOTES} |
| Primary Source Ratio | {PRIMARY_SOURCE_RATIO_SCORE} | 10 | {PRIMARY_SOURCE_RATIO_NOTES} |

<!-- 12 行顺序必须与 frontmatter `dimensions:` 对象键顺序完全一致。契约硬约束。 -->

## Strengths

{STRENGTHS_LIST}

<!-- ≥1 条 bullet；示例：
     - Voice test: 9/10 blind identification with 3 cited language features
     - Internal tensions: 3 well-documented pairs with specific contexts
     - Primary source ratio: 72% (exceeds 50% threshold)
-->

## Weaknesses

{WEAKNESSES_LIST}

<!-- ≥0 条 bullet；反作弊发现也在此记录。示例：
     - Decision-heuristic #3 too generic ("focus on users") — reads as 正确废话
     - voice-without-mindset: Voice=9 but Mindset Transfer=4 (see rubric §Anti-Gaming)
     - empty-component: components/edge-case-library.md has 0 bullets
-->

## Recommended Actions

{RECOMMENDED_ACTIONS_LIST}

<!-- ≥0 项编号列表，每项**必须**含目标文件路径 + 具体改动。示例：
     1. Rewrite components/decision-heuristics.md heuristic #3 with specific 1984-Macintosh case
     2. Add primary-source citations for heuristic #5 in knowledge/articles/
     3. density-floor-breach: remove DILUTE paragraphs in SKILL.md §Overview (lines 34-52)
     verdict=FAIL 时此段不得为空；distill-meta 会把它作为回 Phase 2 的 fix-brief。
-->

## Test Evidence

{TEST_EVIDENCE}

<!-- 可选但强烈推荐；Known/Edge/Voice 三测的逐字证据。
     格式见 references/three-tests.md §Evidence Template。示例骨架：

     ### Known Test
     - Q1 (src: {url1}) / GT: {...} / Persona: {...} / Judge: semantic-match
     - Q2 ... Q3 ... / Hits: N/3 → score X
     ### Edge Test
     - Q (confirmed out-of-corpus): {...}
     - Persona: {...} / Class: uncertain-in-voice / Markers hit: [...]
     ### Voice Test
     - A/B/C (one persona, two baseline decoys)
     - Pick: {letter} conf={high|med|low} / features: [...]
     - Correct: {letter}
-->

<!--
  Rendering Checklist / 渲染前自检
  1. 所有 {PLACEHOLDER} 已被替换 (grep '{[A-Z_]\+}' 应无输出)。
  2. Frontmatter 12 个 dimension 分数与 Dimension Scores 表 12 行完全一致。
  3. overall_score_raw == sum(12 dimensions)；overall_score_normalized == round(raw * 100 / 110)。
  4. verdict ∈ {PASS, CONDITIONAL_PASS, FAIL}；FAIL 时 Recommended Actions 非空。
  5. density_score < density_floor → verdict 必须是 FAIL。
  6. ≥ critical_failure_count 个维度为 0 → verdict 必须是 FAIL。
  7. evaluated_at 为 ISO 8601 UTC (e.g. 2026-04-14T10:00:00Z)。
  8. 同时写入 {persona-root}/validation-report.md 与 versions/validation-report-{ISO}.md。
-->
