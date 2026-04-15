---
policy_version: 0.2.0
default_language: zh
applies_to: distill-collector (tagging), persona-judge (Primary Source Ratio dimension), distill-meta Phase 1.5 (schema_type ↔ access-level cross-check)
changelog:
  - 0.2.0 — Added `access_level` dimension (public | private | semi-public) orthogonal to tier. Feeds manifest.corpus_access_declared; Phase 1.5 cross-checks against schema_type (closes integration.md §6.2 S7).
  - 0.1.0 — Initial primary/secondary/tertiary taxonomy.
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

## Access Level (v0.2.0, orthogonal to tier)

Each document also carries an `access_level` — did the persona (or public) share it with
an **unrestricted** audience, or only with a specific private audience?

| Level | Means | Examples |
|-------|-------|----------|
| `public` | Published for anyone, no gatekeeping | Books, public talks, tweets, public blog posts, printed interviews, press releases |
| `semi-public` | Shared with a defined non-intimate audience | Company-wide memos, industry Slack group, conference keynotes behind paywall |
| `private` | Shared with individuals under reasonable expectation of privacy | 1-on-1 chats, direct DMs, private emails, off-the-record interviews, personal journals |

Access level is **orthogonal to tier**. A tweet is `tier: primary, access_level: public`;
a private DM is `tier: primary, access_level: private`.

### Why this matters (Phase 1.5 gate)

`manifest.corpus_access_declared` summarises the whole corpus as
`public-only | mixed | private-only`, derived from the access-level histogram:

- 100% `public` → `public-only`
- any `private` > 0 → `mixed` (or `private-only` if 100%)

Phase 1.5 Research Review **warns** if:

- `schema_type = public-mirror` AND `corpus_access_declared ≠ public-only` — a public-mirror
  persona with private corpus leaks private content under a label that implies public.
  User must either (a) reclassify to `collaborator` / `mentor`, or (b) remove private
  sources from the corpus.
- `consent_method = implicit-public-figure` (from `consent-attestation.md`) AND
  `corpus_access_declared ≠ public-only` — the "public-figure" consent only covers public
  material; private sources require `written` or `verbal-recorded` consent.

### How corpus-scout tags access_level

1. **File origin metadata**: chat-platform exports → `private` by default; public-web
   scrapes → `public`; enterprise SaaS (Slack / Feishu) → `semi-public` unless the
   specific channel is `#public-*`.
2. **Speaker audience**: if the document's `audience:` metadata (from Phase 1 ingestion)
   is `general_public` → `public`; `specific_individuals` → `private`; `professional_peers`
   / `internal_org` → `semi-public`.
3. **Absence of signal**: default to `private` (conservative). User can override in
   Phase 1.5.

## How corpus-scout Tags Each Document

During Phase 1 (ingestion), the `corpus-scout` agent MUST, for each document:

1. **Identify author-of-record.** Is it the persona? → candidate primary.
2. **Check for paraphrase markers.** Phrases like "他说 / X argued that / according to" in
   the document body → downgrade to secondary.
3. **Check citation chain.** If the document cites another document which is itself
   secondary → mark as tertiary.
4. **Apply source policy.** Cross-reference `whitelist.md` and `blacklist.md`; apply
   multiplier.
5. **Determine access_level** per §Access Level above.
6. **Write frontmatter.** Emit:

   ```yaml
   ---
   tier: primary | secondary | tertiary
   tier_reason: <one-line justification>
   access_level: public | semi-public | private
   access_reason: <one-line justification>
   source_url: <original URL if any>
   source_policy: whitelist | grey | blacklist
   author_of_record: <name or "unknown">
   audience: general_public | professional_peers | specific_individuals | internal_org
   captured_at: <ISO 8601>
   ---
   ```

7. **Flag ambiguity.** If tier or access_level is ambiguous, tag conservatively
   (`tier: secondary`, `access_level: private`) AND add `tier_ambiguous: true` or
   `access_ambiguous: true`; human reviewer resolves in Phase 1.5 gate.

## Anti-patterns

- Treating any interview as primary without checking whether quoted text is verbatim.
- Counting tertiary material toward the denominator (it's excluded from both sides).
- Promoting to primary solely because a whitelisted outlet published it — outlet
  credibility affects the multiplier, not the tier itself.
- **Access-level laundering** (v0.2.0): tagging private DMs as `public` because the
  sender posted screenshots later. The access level is judged at **creation time**, not
  at leak time. If someone's private chat was screenshot-leaked, the original message is
  still `access_level: private` and requires corresponding consent.
- **Mixed-corpus public-mirror skills**: distilling a public figure using a mix of their
  public essays AND leaked private emails, then declaring the skill `public-mirror`.
  Phase 1.5 warns; reviewer should either strip private material or reclassify the
  schema to `collaborator` / `mentor` / `friend`.
