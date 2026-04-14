---
component: expression-dna
version: 0.1.0
purpose: Seven-axis quantification of the subject's expression style; the key innovation borrowed from nuwa-skill and the single most discriminative component for voice-test identification.
required_for_schemas: [self, collaborator, mentor, loved-one, friend, public-mirror, public-domain]
optional_for_schemas: [topic, executor]
depends_on: [identity]
produces: []
llm_consumption: eager
---

## Purpose

`expression-dna` is **the** signature component of a persona skill. It is what makes a Steve Jobs persona sound like Steve Jobs and not a generic "visionary CEO" — not by word-matching, but by quantifying seven orthogonal axes of expression style and citing verbatim corpus evidence on each.

The seven axes are chosen to be **mostly orthogonal** (minimal redundancy) and **observable on ≥200 lines of primary corpus**. Each axis is scored 1-5 with a textual scale descriptor and at least one representative quote from corpus. A skill that scores 4 on "assertiveness" but 2 on "formality" is measurably different from one that scores 2/4 — and both are different from a generic "warm and professional" persona.

For the `topic` schema, a **neutral variant** is emitted: axes are documented but scores are explicitly set to 3 (mid-scale) with a note "neutral voice; topic schema does not mimic a single speaker".

## The Seven Axes

| # | Axis | Scale 1 ←→ Scale 5 | What it measures |
|---|------|--------------------|------------------|
| 1 | **formality** | casual ↔ formal | register; use of contractions, slang, honorifics |
| 2 | **abstraction** | concrete ↔ abstract | ratio of concrete nouns/examples to abstract principles |
| 3 | **assertiveness** | hedging ↔ certain | density of hedges ("maybe", "perhaps") vs. flat declaratives |
| 4 | **sentence-length** | short ↔ compound | mean clause count per sentence; use of subordinate structure |
| 5 | **vocabulary-domain** | general ↔ specialized-jargon | frequency of domain-specific terminology without defining |
| 6 | **emotionality** | reserved ↔ expressive | use of exclamation, emotional adjectives, first-person affect |
| 7 | **persuasion-style** | data ↔ story ↔ appeal-to-authority | three-pole: which mode dominates in persuasive passages (scored 1=data, 3=story, 5=appeal) |

## Extraction Prompt

**Input**: primary corpus, minimum **200 lines** of the subject's own utterances (excluding replies written about them). If <200 lines available, emit a `data_insufficient: true` flag in output and cap confidence.

**Output**: markdown table of 7 axes, each with score 1-5, scale descriptor, and one verbatim quote.

**Prompt** (executable):

```
You are quantifying the subject's expression style on seven axes.

STEP 1 — Line census:
  Count primary-source lines (subject-authored utterances). If < 200,
  emit `data_insufficient: true`. Proceed anyway but mark confidence=LOW.

STEP 2 — For each of the 7 axes:

  2a. Score 1-5 based on the scale descriptor below. Use the MEDIAN of the
      corpus, not extremes.
  2b. Cite ONE representative line (verbatim, ≤ 50 words, redacted).
      The line must be INDEPENDENTLY defensible — a reader scoring the
      line alone would assign the same score ±1.
  2c. Add a 1-sentence "evidence note" explaining why this line is
      representative.

STEP 3 — Cross-check:
  If 6 of 7 axes scored 3 (mid-scale), the DNA is generic — FAIL with
  "DILUTE-grade: subject has no distinctive voice in corpus, or
  extraction was lazy. Rerun with tighter sampling or reject."

STEP 4 — Compute DNA-fingerprint:
  Concatenate scores: e.g., "2-4-5-3-2-1-3" → this is the persona's
  voice-print, used by persona-judge voice-test for 100-word blind
  identification.

AXIS SCALE DESCRIPTORS (abbreviated — expand inline during extraction):
  formality:         1=slang/emoji; 3=conversational-pro; 5=formal-written
  abstraction:       1=all-examples; 3=balanced; 5=all-principles
  assertiveness:     1=heavy-hedge; 3=mixed; 5=flat-declarative
  sentence-length:   1=≤7 words; 3=12-18; 5=compound/subordinate
  vocabulary-domain: 1=general-English; 3=mild-jargon; 5=heavy-undefined-jargon
  emotionality:      1=clinical; 3=measured-affect; 5=exclamatory
  persuasion-style:  1=data-first; 3=story-first; 5=authority-first

ANTI-EXAMPLES (reject output):
  - Generic DNA: "warm and professional" → reject (not an axis score).
  - Single-quote per axis missing → reject.
  - All axes scored 3 → DILUTE-grade failure.
  - Quote is a paraphrase not verbatim → reject.
```

**Few-shot** (Steve Jobs-style):

```markdown
| # | Axis | Score | Scale | Quote | Evidence |
|---|------|-------|-------|-------|----------|
| 1 | formality | 2 | casual-professional; contractions, occasional profanity | "This thing is a bag of hurt." | Signature informal-direct register. |
| 3 | assertiveness | 5 | flat declarative, near-zero hedging | "It just works." | Three-word absolute claim, no qualifier. |
| 7 | persuasion-style | 3→5 | dominantly story, sometimes authority | "I was fired, and it was the best thing that ever happened to me." | Personal-narrative persuasion mode. |
```

## Output Format

Generated `components/expression-dna.md` emits:

```markdown
# Expression DNA

**Fingerprint**: `{s1}-{s2}-{s3}-{s4}-{s5}-{s6}-{s7}`
**Corpus**: {N} primary lines | Confidence: HIGH | MEDIUM | LOW

## Axes

### 1. Formality — {score}/5

- **Scale**: {scale descriptor}
- **Quote**: "{verbatim, ≤50 words}"
- **Evidence**: {1-sentence note}

### 2. Abstraction — {score}/5
... (one section per axis, 7 total) ...

## Voice Test Baseline

To pass the 100-word voice test, a generated reply must score within
±1 on all 7 axes when re-measured against this baseline.
```

## Quality Criteria

1. **All 7 axes present with scores 1-5** — skipping an axis is a blocking failure.
2. **One verbatim quote per axis** — never a paraphrase; redaction of PII is allowed.
3. **Score variance ≥ 1.2 across axes** — uniform scores indicate lazy extraction.
4. **Primary-source line count ≥ 200** OR `confidence: LOW` flag set.
5. **Neutral variant for `topic` schema**: scores pinned to 3/5, explicit note present, no quotes required.

## Failure Modes

- **Generic DNA** ("warm and professional", "thoughtful and precise") — DILUTE-grade failure; blocks Phase 4. The extraction produced no quantification.
- **Paraphrased quotes** — if the reviewer cannot find the quote in the corpus by string search, reject.
- **All-3 scores** — subject has no distinctive voice in corpus, OR extractor gave up. Rerun with tighter source filtering (primary only) or reject the skill.
- **Axis collapse** — two axes scoring identically on every corpus subset suggest they are not orthogonal here; note as a known limitation, do not hide.
- **Contamination** — quotes taken from interviewer questions, not subject answers. Quote attribution must be verified per line.

## Borrowed From

- `alchaincyf/nuwa-skill` — https://github.com/alchaincyf/nuwa-skill — **origin of the seven-axis DNA concept**, documented in `references/extraction-framework.md`. `[UNVERIFIED-FROM-README]` README fragment: *"七轴表达 DNA 是 nuwa 的核心创新：正式度、抽象度、笃定度、句长、术语密度、情绪度、说服模式，每轴量化并引用原句"*.
- Sample implementations reviewed in Tier-3 public-mirror skills (e.g., `alchaincyf/steve-jobs-skill`, `alchaincyf/trump-skill`). `[UNVERIFIED-FROM-README]` — not cloned, only README-inspected.

## Examples

For a `topic` schema shipping this as neutral variant:

```markdown
# Expression DNA (Neutral Variant)

**Fingerprint**: `3-3-3-3-3-3-3` (neutral)
**Note**: This is a `topic` schema; it does not mimic a single speaker.
All axes held at mid-scale; replies use register-appropriate neutral
expository prose.
```
