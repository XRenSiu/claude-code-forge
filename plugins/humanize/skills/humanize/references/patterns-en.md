# English AI-flavor pattern catalog

Principle (same as the Chinese catalog): a single hit is not AI flavor; density, detachment from specifics, and
rhetoric running idle are. humanlint reports densities, not hits. Each row says when *not* to change it.

Register gate: the default register here is professional technical prose (design docs, RFCs, ADRs, postmortems,
engineering email). Do not inject contractions quotas, jokes, typos, or "personality" to fake humanity; in this
register those are a new tell (arXiv 2605.19516: detectors and readers key on the RLHF register, not on polish).

## A. Discourse and structure (fix these first; see `discourse.md` for mechanisms)

| # | Pattern | Example | Fix | Leave alone when |
|---|---|---|---|---|
| A1 | Intro previews, conclusion restates, every section ends with a mini-summary | "In this section we will…" / "Overall, …" | Delete previews and restatements; end on the last new point (next step, open question) | Abstract of a paper |
| A2 | Firstly / Secondly / Finally skeleton | Three paragraphs each opened by an ordinal | Delete ordinals; link by content (end of sentence n → start of n+1) | Genuine ordered procedure |
| A3 | Balanced overview, no recommendation | "Each approach has trade-offs…" | Recommend one; kill each alternative with one specific reason | A survey explicitly asked for |
| A4 | Uniform sentence and paragraph length | Every sentence 18–25 words, every paragraph 3–4 sentences | Vary deliberately; allow a 6-word sentence and a 45-word one | Never |
| A5 | List replaces argument | Four "**Label**: phrase" bullets whose items are actually premise → consequence | Expand to prose with the relation words (so, but, because, at the cost of) | Truly parallel, order-free items (goals, non-goals, change list) |
| A6 | Empty signposting | Sentence-initial Furthermore / Moreover / Additionally / It's worth noting | Delete; if the sentences no longer connect, the gap is in content | Never needed |
| A7 | Generic opening | "In today's fast-paced digital landscape…" / "As our platform continues to grow…" | Open with the incident, date, and number that triggered the doc | Never |
| A8 | Participle tail (superficial analysis) | "…, enhancing overall efficiency and reliability." | Promote to its own sentence with evidence, or delete | Never as a habit |
| A9 | Narrating the document / collaborative residue | "This document aims to explore…", "Let's dive in", "If you plan to add this…" | Say the thing; headings carry structure | Never |
| A10 | Generic placeholder examples | "the user submits a request" | Named scenario with concrete invented detail ("Mei, 40k SKUs, bulk-uploads at 09:00 CST") | Source has none → mark `[unverified]` rather than invent |

## B. Sentence level

| # | Pattern | Example → fix | Note |
|---|---|---|---|
| B1 | Nominalization | "The implementation of caching enables the reduction of latency" → "Caching cuts latency (P99 1.4 s → 120 ms)" | LLMs 1.5–2× human rate (Reinhart, PNAS 2025) |
| B2 | Copula avoidance | serves as / functions as / marks / stands as / refers to → is / has | Wikipedia: >10% drop in is/are in AI text |
| B3 | Negative parallelism | "not just X but Y", "It's not about X, it's about Y", "not because X but because Y" | Delete the negative half; say Y |
| B4 | Rule of three | "fast, reliable, and secure" | Keep only what is true; two items when two suffice |
| B5 | Uniform hedging or uniform boosting | every claim "may / could potentially" or every claim "crucial / significant" | Assert what you know; hedge with a stated reason; recommend one thing |
| B6 | Em dash as glue | "— a strategic investment in our platform's future" | Split into two sentences; ≤2 per 1,000 words |
| B7 | Elegant variation (synonym cycling) | cache → caching layer → caching mechanism → this component | Repeat the key term; humans repeat (dispersion 16 vs 5) |
| B8 | Mannered prose (2026 density-era tell) | "a dial worth turning" for "a parameter worth varying"; "instrumentation is the unlock" | When a literal phrase exists, use it (Anthropic Fable 5.1 guide) |
| B9 | Invented jargon presented as standard | "load-bearing assumption", "reflexive hedging" | Use only terms the field already uses |
| B10 | Compressed clauses / density mistaken for concision | 58% longer sentences, 46% more clauses (paddo.dev on Opus 5) | One claim per sentence; break at the comma |
| B11 | Vague attribution | "experts say", "observers have noted", "research shows" | Name the source or drop the claim |
| B12 | Adjective instead of fact | "robust", "significant improvement", "comprehensive" | Number, example, or mechanism; if none, say "not measured" |

## C. Lexical (same source as humanlint `STOCK_EN`; edit both together)

**Meta-discourse**: it's important to note, it's worth noting, it is essential to, notably, in conclusion, in summary,
to summarize, to sum up, at the end of the day, all in all, this article will, this document aims, let's explore, let's dive,
deep dive, unpack, key takeaways, actionable insights

**Importance inflation**: crucial, pivotal, vital, invaluable, underscore(s), highlight the importance, plays a crucial/vital/key/pivotal role,
profound, groundbreaking, transformative, revolutionize, game-changer, cutting-edge, state-of-the-art

**Background generator**: in today's, in the ever-evolving, rapidly evolving, fast-paced, in the realm of, in the world of,
in an era, with the rise of, as technology, landscape, paradigm, realm, tapestry, testament to

**Empty intensifiers / prestige verbs**: leverage, harness, empower, elevate, foster, streamline, enhance, utilize, facilitate,
unlock, embark, delve, navigate, showcase, boast, meticulous, intricate, multifaceted, holistic, comprehensive, nuanced,
robust, seamless, synergy, vibrant, innovative, myriad, plethora, a wide range of, a variety of, a range of

**Connectives (sentence-initial)**: moreover, furthermore, additionally, consequently, thus, hence, overall, ultimately

**Structure phrases**: not only… but also, whether you're, when it comes to, one of the key, a key aspect, various aspects,
ensuring that, aims to, is designed to, serves as, lays the foundation, in terms of, the ability to

Vocabulary drifts by model era (Wikipedia documents GPT-4 delve/tapestry → GPT-4o align/foster/showcase → GPT-5 emphasizing/
highlighting; Claude: em dashes, "not X, it's Y"). A blacklist is a floor, not the method; the structural rows above
do not drift.

## D. Positive targets (signs of human writing; almost no existing tool encodes these)

- Simple is/has: "there is a", "it has a", "the API is synchronous".
- Plain verbs: use, wrote, died, buy, help, about (not utilize, authored, passed away, purchase, assist, approximately).
- Willingness to be definitive: "this is the slowest endpoint", "it was the first outage of that kind".
- Temporal and proper-noun specificity: "on 27 Aug", "SendGrid", "`orders-api`", not "recently", "a third-party provider".
- A person present: "I recommend", "I didn't choose", "what worries me most", "I checked with product".
- Sentence fragments and And/But openers are fine. Semicolons and parentheses are fine.
- Repeat the key term instead of rotating synonyms.
- At least one rough edge per document: an admitted unknown, an unmeasured estimate labelled as such, a non-mainstream observation.
  This is judgment, not colloquialism.
- Short sentences exist: at least one ≤6 words per 150 words.

## E. Before / after (full samples: `fixtures/ai-en.md` → `fixtures/human-en.md`)

**Opening**
> ✗ In today's fast-paced digital landscape, delivering timely and reliable notifications is crucial for maintaining user engagement. As our platform continues to grow, the current notification service faces increasing challenges…
>
> ✓ Twice in the last month (Aug 12, Aug 27) SendGrid returned 503s for about 20 minutes, and both times checkout latency went from 300ms to 4s because `POST /orders` calls the notification service synchronously.

**Alternatives**
> ✗ We propose leveraging an event-driven architecture to decouple the notification service from its producers. This approach not only addresses the current challenges but also lays a robust foundation for future growth.
>
> ✓ We did add a 500ms timeout in July. It stopped the latency bleed but we still drop the email when SendGrid is down. Kafka would also work, but we already run SQS for the export jobs and nobody on the team has operated Kafka. I'll take the boring option.

**Risk**
> ✗ While the migration presents significant opportunities, it also introduces certain risks. Eventual consistency may lead to delays… To mitigate these risks, we will implement comprehensive testing…
>
> ✓ Ordering. Standard SQS doesn't preserve order, so a "shipped" email could in theory arrive before "confirmed" if both are queued within seconds. I think this is fine because the templates stand alone, but if product disagrees we'd need a FIFO queue, which caps at 300 msg/s per group. Our peak is 40/s.

**Ending**
> ✗ In conclusion, migrating to an event-driven architecture represents a pivotal step… This is not just a technical upgrade—it's a strategic investment in our platform's future.
>
> ✓ Flag on for internal accounts Monday, 5% of traffic Tuesday, 100% by Thursday if the DLQ stays empty. Rollback is the flag; the old code path stays for two weeks.
