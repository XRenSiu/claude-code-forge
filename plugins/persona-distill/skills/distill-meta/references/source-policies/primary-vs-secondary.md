---
policy_version: 0.1.0
default_language: zh
applies_to: distill-collector (tagging), persona-judge (Primary Source Ratio dimension)
---

# Primary vs Secondary vs Tertiary — 来源层级定义

> Three-tier provenance taxonomy used across persona-distill. Every document ingested
> under `{persona-skill}/knowledge/**` MUST carry a `tier:` frontmatter field; the tier
> determines its weight in `manifest.json → sources.primary_ratio`.

## Definitions

### Primary (一手)

The **person's own words, verbatim**. The author-of-record is the persona themselves, and
the text has not been editorially re-paraphrased.

Examples:
- Their own writing (blog post, book chapter, tweet, email, chat message).
- A recorded interview where the quoted text is a verbatim transcript of their speech.
- A conference talk transcript from their own recording, or a letter/memo they authored.

Weight: **1.0×** (subject to whitelist/blacklist multiplier on the hosting source).

### Secondary (二手)

A **third-party description or paraphrase** of their views, written by someone with direct
access to the person or primary material (journalist, colleague, biographer), who exercises
editorial judgment but cites primary sources.

Examples:
- A 财新 / The New Yorker profile quoting interviews partially.
- A biographer's chapter paraphrasing the subject's statements with citations.
- A colleague's essay recounting direct conversations with the persona.

Weight: **0.5×** (treated as grey by default unless whitelisted).

### Tertiary (三手)

**Summary-of-summary.** The author has no direct access; the text is aggregated from
secondary sources, often without citation discipline.

Examples:
- Wikipedia main-space articles (summarizes secondary sources).
- Aggregator blogs ("10 lessons from …").
- 百度百科, Medium listicles, quote-compilation sites.

Weight: **0×** for `primary_source_ratio` computation. Tertiary material MAY still be
ingested for orientation but does not count toward the ratio.

## The Rule (consumed by persona-judge)

> `primary_source_ratio` in `manifest.json` MUST **exceed 0.5** for persona-judge's
> **Primary Source Ratio** dimension to score **≥ 5/10**.

Formula (computed by distill-collector):

```
primary_ratio = Σ(chars_primary × 1.0) / Σ(chars_all_non_tertiary)
```

- Tertiary characters are excluded from both numerator and denominator.
- Whitelist/blacklist multipliers apply on top of the base tier weight. Full spec:
  `distill-collector/references/ratio-computation.md` (v2).

## How corpus-scout Tags Each Document

During Phase 1 (ingestion), the `corpus-scout` agent MUST, for each document:

1. **Identify author-of-record.** Is it the persona? → candidate primary.
2. **Check for paraphrase markers.** Phrases like "他说 / X argued that / according to" in
   the document body → downgrade to secondary.
3. **Check citation chain.** If the document cites another document which is itself
   secondary → mark as tertiary.
4. **Apply source policy.** Cross-reference `whitelist.md` and `blacklist.md`; apply
   multiplier.
5. **Write frontmatter.** Emit:

   ```yaml
   ---
   tier: primary | secondary | tertiary
   tier_reason: <one-line justification>
   source_url: <original URL if any>
   source_policy: whitelist | grey | blacklist
   author_of_record: <name or "unknown">
   captured_at: <ISO 8601>
   ---
   ```

6. **Flag ambiguity.** If tier is ambiguous, tag `tier: secondary` AND add
   `tier_ambiguous: true`; human reviewer resolves in Phase 2 gate.

## Anti-patterns

- Treating any interview as primary without checking whether quoted text is verbatim.
- Counting tertiary material toward the denominator (it's excluded from both sides).
- Promoting to primary solely because a whitelisted outlet published it — outlet
  credibility affects the multiplier, not the tier itself.
