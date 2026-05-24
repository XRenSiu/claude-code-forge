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

```
Round <N> of clarification — <X> questions:

[ambiguity] REQ-001: ...
  (a) ...
  (b) ...
  (c) ...

[missing edge] REQ-002: ...
  (a) ...
  (b) ...

[undefined term] REQ-003: by "premium" do you mean
  (a) ...
  (b) ...
  (c) ...
```

Nothing else in the message. No preamble, no apology, no "thanks for clarifying earlier". The user is here to answer questions; respect their time.

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
