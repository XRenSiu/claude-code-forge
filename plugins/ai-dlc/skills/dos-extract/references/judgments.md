# The 4 Core Judgments

Every meaningful decision during DOS extraction reduces to one of four judgments.
Memorize the *form* of each — the surface examples vary by project, but the
shape of the reasoning does not.

When `decisions.md` is generated, every non-trivial entry should be
traceable to one of these four judgments by name (e.g. "Judgment 2: Topic absorbs
Node because lifecycle is identical").

---

## Judgment 1: Object vs. UI vs. Implementation vs. Rule

**Question**: "What category of thing is this term?"

**Why it matters**: 90% of ontology pollution comes from misclassifying these.
A UI element promoted to an object freezes presentation choices into the contract.
An implementation suffix (`Repository`, `Manager`) promoted to an object
contaminates the ontology with framework conventions.

### Decision procedure

For a given term `X`, ask in order:

1. **Is `X` something a user could point at and describe **without** referring to
   a screen or interaction?**
   - Yes → likely a business object. Continue.
   - No, only describable via "the thing that pops up when..." or "the box in
     the corner..." → **UI element**. Excluded.

2. **Does `X` end in a known infrastructure suffix?**
   Common suffixes: `Repository`, `DAO`, `DTO`, `Service`, `Manager`, `Handler`,
   `Controller`, `Provider`, `Factory`, `Builder`, `Helper`, `Util`, `Adapter`,
   `Resolver`, `Mapper`, `Serializer`, `Schema` (when used as suffix not
   standalone), `Config`, `Context` (when used as React/framework context).
   - Yes → **implementation detail**. Excluded.
   - No → continue.

3. **Is `X` a verb-noun describing an action, not a thing?**
   Examples: `LoginAttempt`, `SearchQuery`, `ClickEvent`. These can be objects
   in event-sourced systems, but in most products they are **rules / behaviors /
   intents**, not objects.
   - Yes → likely belongs in `rules` or `behaviors`, not `objects`.
   - No → continue.

4. **Could you remove `X` from the system and still describe the product?**
   - Yes → it's not core. Mark as candidate for **derived/composition** or
     for absorption into another object.
   - No → it's a **business object**.

### Worked examples

| Term | Steps | Verdict |
|------|-------|---------|
| `Topic` | 1: yes (a thought node). 4: no (product collapses without it). | **business** |
| `TopicCard` | 1: no — only describable as "the rendered Topic on screen". | **UI** |
| `TopicRepository` | 2: yes, suffix `Repository`. | **impl** |
| `Modal` | 1: no — purely visual. | **UI** |
| `Conversation` | 1: yes (a dialogue, even off-screen). 4: no. | **business** |
| `LoginEvent` | 3: yes — it's an action, not a thing. | **behavior** (not object) |
| `SearchService` | 2: yes, suffix `Service`. | **impl** |
| `Sheet` | 1: yes (a canvas of thoughts). 4: no. | **business** |

### Common traps

- **`Comment` / `Reply` / `Note` / `Annotation`** — all might pass step 1, but
  Judgment 2 may reveal they are the same object.
- **`User` / `Person` / `Account` / `Member`** — all pass step 1, but Judgment 4
  may reveal they belong to different Bounded Contexts.
- **`Page`** — ambiguous. In a documents app it's business; in a web app it's UI.
  Mark as `unclear` and ask the user.

---

## Judgment 2: Same Object vs. Two Objects

**Question**: "Are these two terms two views of one thing, or two different things?"

**Why it matters**: Splitting one object into two doubles the rules, the relations,
the agent guidelines, the test surface. Merging two distinct objects into one
creates conditional logic everywhere ("if type === 'X' then..."). Both errors
are expensive; the merge error is more common in extraction.

### Decision procedure (apply in order — first decisive answer wins)

1. **Lifecycle test.** Are the create / edit / delete / archive rules the same?
   - "ChatMessage" and "SystemMessage" — both immutable, both append-only,
     both belong to a Conversation → **same lifecycle** → likely one object.
   - "Topic" and "Message" — Topic is editable forever, Message is immutable
     once sent → **different lifecycle** → two objects.

2. **Permission/ownership test.** Who can read/write/share each one? Is the
   model identical?
   - "Post" and "Reply" — both have a single author, public visibility, same
     edit window → likely one object (`Post` with optional `parent_id`).
   - "Document" and "Comment" — Document owner has full control; Comment
     author has limited rights tied to Document → different model → two objects.

3. **Skeleton test.** If you strip every type-specific field, does the remaining
   skeleton describe one thing or two?
   - `Email`: { from, to, subject, body, sent_at }
     `Tweet`: { author, content, posted_at }
     Strip "subject" and "to/from" specifics: `{ author, content, timestamp }` —
     same skeleton → these *could* be one object (`Post` with `kind` field), but
     usually shouldn't be merged because Judgment 1 already separated their
     **purpose**. Use this test only when the prior tests are inconclusive.

4. **Sentence test.** Read the candidate relationships out loud:
   - "A Person CREATES a Topic" — natural.
   - "A Person CREATES a TopicNode" — clunky; "Node" is implementation.
   - "A Sheet CONTAINS Items" — vague; "Items" of what?
   - "A Sheet CONTAINS Topics" — clear.
   The version that flows naturally and uses the team's actual vocabulary wins.

### Worked examples

**Case A**: Codebase has `Post`, `Tweet`, `Message` classes.
- Lifecycle: all three are immutable-after-publish. ✓ same
- Permission: all single-author, public. ✓ same
- Skeleton: `{ author, content, timestamp }`. ✓ same
- **Verdict**: merge into single `Post` object. (This is the Jorgenson reference
  case from the methodology doc.)

**Case B**: Codebase has `Topic`, `Note`.
- Lifecycle: Topic is mutable and may be deleted; Note is append-only. ✗ different
- **Verdict**: stop at lifecycle test. Two objects.

**Case C**: Codebase has `Topic`, `Node`.
- Lifecycle: identical (both editable canvas elements). ✓ same
- Permission: identical. ✓ same
- Sentence test: "A Sheet CONTAINS Topics" reads naturally; "A Sheet CONTAINS
  Nodes" sounds like a graph database. Team uses "Topic" in design discussions.
- **Verdict**: merge. Canonical name is `Topic`. `Node` is rejected because it
  leaks the graph-implementation choice into the contract.

### How to record this in `decisions.md`

```markdown
### Topic ← {Topic, Node, Item}

- Lifecycle: identical (mutable canvas elements with same archive semantics)
- Permission: identical
- Sentence test: "Sheet CONTAINS Topics" reads naturally; "Sheet CONTAINS Nodes"
  reads as graph-DB terminology; "Sheet CONTAINS Items" reads vague
- Chosen name: **Topic**
- Rejected names: Node (leaks graph implementation), Item (semantically empty)
```

---

## Judgment 3: Constitution vs. Policy

**Question**: "Is this rule fundamental to what the system **is**, or is it the
current business strategy?"

**Why it matters**: Policies change with pricing, market, A/B test outcomes.
If you bake them into the DOS, the DOS becomes a moving target and loses
authority. Constitution rules change rarely and signal architectural intent.

### Decision procedure

For a candidate rule, ask: **"If I removed this rule, would the system still be
recognizably itself?"**

- **No** (system collapses or becomes a different product) → **constitution** →
  goes into `rules` section.
- **Yes** (system runs fine, just with different policy) → **policy** → does NOT
  go into DOS. Document elsewhere (PRD, business rules engine, feature flags).

### Worked examples

| Candidate rule | Test | Verdict |
|----------------|------|---------|
| "A Sheet must have exactly one root_topic." | Without it, Sheet degenerates into a Topic bag. System is no longer a mind-mapping tool. | **constitution** ✓ |
| "Free tier users can have at most 3 Sheets." | Remove it: paying model changes, system unchanged. | **policy** ✗ |
| "BehaviorSignal is append-only and immutable." | Remove it: HoneyComb's audit/replay properties collapse; insights become unreliable. | **constitution** ✓ |
| "Topics older than 90 days are archived automatically." | Remove it: storage costs change, UX changes, but the system is still itself. | **policy** ✗ |
| "Every Message has exactly one author." | Without it: provenance breaks, history corrupts. | **constitution** ✓ |
| "Premium users get GPT-4; free users get GPT-3.5." | Pure pricing. | **policy** ✗ |

### Edge case: rate limits

Rate limits are usually policy. But if a rate limit exists for **correctness**
(e.g. "a user cannot send two Messages within the same millisecond, because
ordering would be ambiguous"), that's constitution.

---

## Judgment 4: Single Context vs. Multi-Context

**Question**: "Does this concept have the same *important attributes* across all
parts of the product, or do different parts care about different facets?"

**Why it matters**: Forcing one definition across multiple contexts produces a
god-object. Splitting into Bounded Contexts with explicit translation produces
healthy boundaries.

### Decision procedure

For a candidate object that appears in multiple parts of the system:

1. List the attributes that **each consuming area** cares about.
2. Compute the overlap.
   - **Overlap is most attributes** → single context, one object.
   - **Overlap is small or empty** → multiple Bounded Contexts; the object should
     be **owned by one** and **referenced by others** through translation.

### Worked example: `User`

In a typical SaaS product:

| Context | Attributes that matter |
|---------|------------------------|
| Identity / Auth | `email`, `password_hash`, `2fa_enabled`, `last_login_at` |
| Billing | `subscription_tier`, `payment_method`, `seat_count`, `dunning_state` |
| Product (Xmind Agent's Thinking Workspace) | `thinking_history`, `behavior_signals`, `style_preferences` |
| Notifications | `email_pref`, `push_token`, `quiet_hours` |

Overlap: `id` and maybe `display_name`. That's it.

**Verdict**: 4 contexts. `User` should be **owned by Identity**, and each other
context should have its own slim representation:
- Billing has `Subscriber` (linked to User by `id`)
- Product has `Actor` / `Person` (this DOS's choice)
- Notifications has `NotificationRecipient`

The DOS being extracted should:
- Define its own slim version (in this case, `Actor` with subtype `Person`)
- Reference Identity Context as upstream in `bounded_contexts.upstream_contexts`
- Document the translation in `translation_notes`

### Worked example: `Topic` (no split needed)

In Xmind Agent:
- Canvas rendering: cares about `id`, `content`, `position`, `style`
- Agent code: cares about `id`, `content`, `author`
- Persistence: cares about all fields

Overlap: substantial. **Verdict**: single object, single context.

### When to NOT split

- The system is small (< 10K LOC, < 5 engineers). Premature splitting is
  more expensive than premature merging at this scale.
- The "different attributes" are actually just **optional fields** of one object,
  not different perspectives.
- You can't name the contexts cleanly — if "Context A" and "Context B" sound
  arbitrary, the split isn't real.

---

## How the judgments depend on each other

There is a natural partial order — not a fixed workflow, but a real data
dependency between the judgments:

- **Judgment 1 runs first**, because it filters out the UI and implementation
  noise. Everything downstream only makes sense once you're looking at genuine
  business-object candidates.
- **Judgment 2 (merge synonyms) and Judgment 4 (split contexts)** operate on the
  surviving candidates. They can run in either order, but both need Judgment 1's
  output: you merge synonyms among real objects and split contexts among real
  objects.
- **Judgment 3 (filter policy from constitution)** applies when you fill the
  `rules` — it doesn't need the object set fully settled, but the rules you keep
  must reference declared objects, so in practice it lands after the object roster
  is mostly stable.

In short: filter UI/impl (J1), then converge — merge synonyms (J2) and split
contexts (J4) — then keep only constitutional rules (J3). That's a dependency
chain, not a checklist of steps to march through.

If you find yourself reaching for a fifth judgment, stop — usually it's a special
case of one of these four, and forcing it into a new judgment dilutes the framework.
