# Clarify protocol

The clarify loop is **the only step in this whole pipeline where a human is in the inner loop**. Everything before it is preparation; everything after it is automation. So this loop has to be efficient. Asking 20 questions, asking the wrong kind of questions, or asking them in 8 rounds will burn the user's patience and make them stop using the skill.

These rules exist to keep the loop tight.

---

## Rule 1: Only three question types are legal

| Tag | What it means | Example |
|---|---|---|
| `[ambiguity]` | The same wording supports more than one reasonable reading. | "Current billing period end" = local midnight, UTC midnight, or 30 days from cancellation? |
| `[missing edge]` | An exception / extreme / empty / concurrent / retry / failure case is undefined. | What happens if the user cancels mid-checkout? What if they cancel twice? |
| `[undefined term]` | A domain noun has no precise definition. | What does "premium" cover exactly? Which features? |

If a question does not fit one of these three tags, **do not ask it.** Common temptations to resist:

- "Which framework should we use?" → Implementation choice, belongs to design/planning, not requirements.
- "Should we cache the result?" → Same — implementation.
- "Do you want this in v1 or v2?" → Scoping/PM decision, not requirements clarification.
- "Should we add analytics tracking?" → Out of scope unless the user mentioned it.
- "Do you want it to be fast?" → Of course they do. If there's a SLO question, ask "what response time is acceptable?" — that's `[ambiguity]` on "responsive".

If you tagged a question and it feels like a stretch ("hmm, is this really an ambiguity?"), it probably isn't — drop it.

---

## Rule 2: 3-5 per round, 2-3 rounds typical, **hard cap 5 rounds**

| Round | Typical content |
|---|---|
| 1 | The deepest unknowns from S1 — the things that change the whole shape of the spec. |
| 2 | Second-order ambiguities exposed by round 1 answers + remaining edge cases. |
| 3 | Loose ends (timezones, units, precise terms in glossary). Often unnecessary. |
| 4 | Means the requirement is bigger than expected. Acceptable but unusual. |
| 5 | **Stop.** If you still have open `[?]`, the brief is too big. Split it. |

Under no circumstance ask more than 5 questions in one round — even if the user said "ask away". Users underestimate how tired they will get answering them, and the answers degrade in quality after the third or fourth.

### What if the round has fewer than 3 questions left?

The upper bound (5) is hard. The lower bound (3) is a target. When you reach a round and the remaining open `[?]` list is < 3, apply this decision in order:

1. **If any *previous* round's second-order question could legitimately be deferred to this round** — pull it forward so this round has 3+ questions. (Example: a thread-scope follow-up exposed by a round-1 answer that you put in round 2 could instead live in round 3 if it pairs naturally with this round's other items. Rule 5 — group related topics — gets a small tax; it's worth it.) Plan this *at round 2*, not retroactively in round 3.
2. **Otherwise, stop normally per Rule 6** with as few as 1-2 final questions, finish the round, and proceed to S3. Do **not** invent a third question to pad — under Rule 1, any question you cannot honestly tag is a bad question, and Rule 6's "Bail-out stop" is strictly for `[?]` *remaining* at round 5, not for under-3-per-round.

Document the choice in your reasoning, not in the user-visible output. Never tell the user "I would have asked 3 but only have 2 left, so picking option (1) vs option (2)" — that is the kind of skill-internal log that does not belong in the deliverable.

---

## Rule 3: Closed > open

A closed question with 2-4 explicit options converges far faster than an open question:

**Bad (open):**
> Q: How should we handle the case where the user cancels mid-checkout?

User now has to invent the whole answer. Likely response: a paragraph that itself contains 3 new ambiguities.

**Good (closed):**
> [missing edge] REQ-001: when the user clicks "cancel subscription" *during* an in-flight upgrade checkout, the system should
>   (a) refuse the cancellation until the checkout completes or aborts,
>   (b) cancel both atomically (rollback the checkout, set status to cancelled_active),
>   (c) cancel the subscription but let the checkout continue and bill normally.

User picks (a), (b), or (c), or writes "(d) something else: ...". You converge in one round, not three.

Open questions are acceptable when you genuinely cannot enumerate the options (the user's mental model determines the shape, e.g. "what does 'premium' include?"). For those, ask open — but expect the answer itself to produce a `[?]` for round 2.

---

## Rule 4: Apply answers immediately and look for second-order gaps

After each round of answers, before sending the next round:

1. Update the in-progress spec — convert each answered `[?]` into a normal clause + add a `source:` line citing the round/question number.
2. Re-read each updated REQ. Does the resolution **expose a new ambiguity**? Very often it does. Example:
   - User says: "Cancellation honors UTC boundary."
   - You now realize: the spec didn't say what happens to users in timezones east of UTC where "end of paid period" could feel like they're losing hours of access. Is that surfaced in UI? `[missing edge]` for round 2.
3. Add new `[?]` markers to the open list.
4. Re-check: any `[?]` from the original draft that *did not* get answered because you didn't ask it this round? Pull it into the next batch.

---

## Rule 5: Group related questions in one round, not interleaved across rounds

If round 1 has three questions all about REQ-001 (timezone, atomicity, what "premium" covers), great — the user stays in one mental context. Do not artificially spread them across rounds to "save questions for later" — that costs the user more total time as they have to swap context back in each round.

Conversely, do not mix REQ-001-timezone with REQ-004-retry-policy in the same round if you can avoid it — those are different mental contexts and the user has to context-switch.

---

## Rule 6: Stop conditions and how to bail out gracefully

**Normal stop:** all `[?]` resolved → proceed to S3.

**Bail-out stop:** round 5 elapsed and `[?]` remain. Tell the user, with specifics:

> "Five rounds in, and `<N>` questions remain open. This usually means the requirement is wider than originally framed. Looking at the open list, I'd suggest splitting:
>
> - **Feature A:** REQ-001, REQ-002 (cancellation flow proper)
> - **Feature B:** REQ-004, REQ-005 (trial-vs-paid handling — separate problem space)
>
> Two options:
> (i) I write a partial done_when contract covering only the resolved REQs and you re-invoke me for the split feature.
> (ii) You give me a narrower brief and we restart.
>
> Which?"

Do not silently keep asking. The cost of three more rounds is high, and the chance that the gap actually resolves rather than spawning more `[?]` is low — the spec is genuinely too big.

---

## Rule 7: One question per `[?]` marker — do not bundle

This is bad:

> [ambiguity] REQ-001: what timezone is used for end_date, what happens to trial users, and how does retry interact with cancellation?

The user will answer one of the three and forget the others. Split into three questions, each tagged.

---

## Format for a clarify-round message

Each numbered question is `[<tag>] [REQ-anchor]: "<noun-being-clarified>" <reading-options>?` — the double-quoted noun is what binds the question to a specific clause; options follow on indented lines. Both the S1 `## Open questions` list and S2 round messages use this same shape, so the user reads one consistent format throughout.

```
Round <N> of clarification — <X> questions:

[ambiguity] REQ-001: "current billing period end" means
  (a) user's local timezone midnight on end_date
  (b) UTC 23:59:59 on end_date
  (c) exactly 30 days from cancellation timestamp

[missing edge] REQ-002: what happens if the user cancels mid-checkout?
  (a) refuse cancel until checkout resolves
  (b) atomically cancel both
  (c) cancel sub, let checkout continue

[undefined term] REQ-003: by "premium" do you mean
  (a) all paid features
  (b) top tier only
  (c) named feature set X / Y / Z
```

Nothing else in the message. No preamble, no apology, no "thanks for clarifying earlier", no notes about "this round only has 2 questions because…". The user is here to answer questions; respect their time.

---

## Calibration: examples of well-tagged vs badly-tagged questions

| Question | Tag | Verdict |
|---|---|---|
| "What does 'end of paid period' mean — UTC midnight or local midnight?" | `[ambiguity]` | Good. Same wording, two readings. |
| "What if the user is in the middle of a checkout when they cancel?" | `[missing edge]` | Good. Edge case the brief did not cover. |
| "By 'premium' do you mean all paid features or just the top tier?" | `[undefined term]` | Good. Domain noun, needs precision. |
| "Should we use Stripe or Braintree?" | (none) | Bad — implementation choice, drop. |
| "Do you want a confirmation modal?" | `[missing edge]` only if "confirmation" is genuinely unspecified | Borderline. If brief says "the user confirms cancellation", it's `[ambiguity]` (modal vs page vs dialog). If brief never mentioned confirmation, do not invent it — drop. |
| "Should this be performant?" | (none) | Bad — degenerate. Either re-frame as `[ambiguity]` on a specific SLO claim, or drop. |
| "Where should we store the cancellation record?" | (none) | Bad — implementation. Drop. |
