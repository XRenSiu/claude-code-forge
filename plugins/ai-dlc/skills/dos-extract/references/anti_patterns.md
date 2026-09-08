# Anti-Patterns — Ontology Pollution Catalog

These are recurring patterns that pollute extracted ontologies. Use this file as
a **checklist while classifying and converging objects**: for each candidate
object, run through the patterns below and flag any matches.

When extracting a DOS, distinguish between:
- **Anti-patterns this skill should AVOID producing** — listed below.
- **Anti-patterns the codebase EXHIBITED** — these go into the DOS's own
  `anti_patterns` section, with the codebase-specific evidence attached.

---

## Pattern 1: UI-Element-as-Object

**Symptoms**: The candidate object name contains a UI primitive: `Card`, `Modal`,
`Drawer`, `Toast`, `Sheet` (when it means "bottom sheet UI"), `Panel`, `Tab`,
`Section`, `Row`, `Cell`, `Bubble`, `Pill`, `Chip`, `Badge`.

**Why bad**: UI re-skins frequently. Hard-coding the visual form into the
ontology means every redesign requires renaming the contract.

**How to spot**: The term appears almost exclusively in `components/` or
`ui/` directories. The class extends a UI framework base class.

**Correction**: Look at what the UI element **represents**. A `TopicCard` is the
UI of a `Topic`. A `MessageBubble` is the UI of a `Message`. The DOS uses the
underlying object name.

**Special note on `Sheet`**: This is a tricky one — in Xmind, `Sheet` is a
legitimate business object (a canvas of thoughts). In an iOS app, `Sheet` would
be UI (a bottom-sheet modal). Use Judgment 1 step 1: can a user describe it
without referring to a screen? In Xmind: yes (a Sheet is a coherent thought
space). In iOS: no (a Sheet is "the thing that slides up from the bottom").

---

## Pattern 2: Implementation-Suffix-as-Object

**Symptoms**: Object name ends in `Repository`, `Service`, `Manager`, `Handler`,
`Controller`, `Provider`, `Factory`, `Builder`, `Helper`, `Utility`, `DAO`,
`DTO`, `Resolver`, `Mapper`, `Serializer`, `Adapter`, `Wrapper`, `Proxy`.

**Why bad**: These are **architecture roles**, not business concepts. The
business object is what the role *operates on*.

**Correction**: Strip the suffix and check what remains.
- `TopicRepository` → operates on `Topic` → `Topic` is the object.
- `UserService` → operates on `User` → `User` (or its context-appropriate name).
- `MessageBuilder` → builds `Message` → `Message` is the object.

If stripping leaves nothing meaningful (e.g. `EventHandler` → `Event` is too
generic), the object likely doesn't have a corresponding business concept and
the suffixed term is purely infrastructure. Exclude entirely.

---

## Pattern 3: Synonym Sprawl

**Symptoms**: Multiple terms that probably mean the same thing:
- `Post` / `Tweet` / `Message` / `Status` / `Update`
- `User` / `Account` / `Member` / `Person`
- `Tag` / `Label` / `Category` / `Topic` (when "Topic" means classification)
- `Comment` / `Reply` / `Note` / `Annotation`
- `Item` / `Entry` / `Record` / `Element`
- `Group` / `Team` / `Org` / `Workspace`

**Why bad**: Each unmerged synonym multiplies rules, relationships, and agent
guidelines. A system claiming both `Post` and `Tweet` as core objects has 2x
the maintenance with no expressive benefit.

**Correction**: Apply Judgment 2 (Same Object vs. Two Objects). Most of the
time the merge is correct. When it's not, the distinction usually reduces to a
**type field** within one object (`Post.kind = 'short' | 'long'`).

**Trap**: `Comment` and `Reply` look like synonyms but often aren't. A `Comment`
on a Post is one thing; a `Reply` to another `Comment` (forming a tree) might
be the same object with a `parent_id` field, OR might genuinely be different
if Replies have different lifecycle (e.g. cannot be top-level). Apply
Judgment 2 carefully here.

---

## Pattern 4: Action-as-Object (when it shouldn't be)

**Symptoms**: Object name is verb-based: `LoginAttempt`, `SearchQuery`,
`SaveAction`, `ClickEvent`, `EditOperation`.

**Why bad**: Most of these are **rules**, **behaviors**, or **values passed
through behaviors**, not first-class business objects. Promoting them creates
phantom objects with no clear lifecycle.

**Correction**: Move the concept to:
- `behaviors` section if it describes a side-effect chain.
- `rules` section if it describes a constraint.
- A field/parameter of an existing object if it's just a value that flows
  through.

**Exception**: In **event-sourced** systems where the event log IS the source of
truth, `LoginEvent` etc. genuinely are business objects (because the event log
is queryable, replayable, and definitional). Inspect the codebase: if there's
an event store with replay logic, treat events as objects. Otherwise, demote.

`BehaviorSignal` in the Xmind Agent example is on this boundary — it's an
event-shaped object, but it's a first-class business concept because HoneyComb's
entire value proposition is built on querying it. So it stays as an object.

---

## Pattern 5: God Object via Premature Unification

**Symptoms**: A single object with 30+ fields, conditional logic everywhere
based on a `type` discriminator, and rules that read "if type === 'X' then
must have Y else must have Z".

**Why bad**: Indicates Judgment 2 was applied too aggressively, merging things
that should be separate.

**Correction**: When a `type` field's branches each demand exclusive fields and
exclusive rules, that's a signal that the merge was wrong. Split back into
two (or more) objects.

**Distinguishing from healthy unification**: A healthy unified object has:
- Most fields shared across types.
- The `type` field affecting only a few rules.
- Same lifecycle, permission, and purpose across types.

---

## Pattern 6: Cross-Context Smoosh

**Symptoms**: One object (often `User` or `Organization`) carries fields from
multiple unrelated concerns: auth credentials, billing, preferences, behavioral
data, all in one place.

**Why bad**: Different parts of the system care about different facets, and
forcing one definition makes every consumer read fields they don't need and
risk breaking when unrelated fields change.

**Correction**: Apply Judgment 4. Split into Bounded Contexts. The DOS being
extracted should own only one slim version of the concept and reference others
in `bounded_contexts.upstream_contexts` / `downstream_contexts`.

---

## Pattern 7: Framework-Concept-as-Object

**Symptoms**: Object name comes from the framework, not the domain:
`ReactComponent`, `RouteParam`, `Middleware`, `StoreSlice`, `Reducer`,
`Hook`, `Context` (when it means React Context), `Selector`.

**Why bad**: Conflates application architecture with business architecture.
A framework swap would force a DOS rewrite.

**Correction**: Exclude entirely. These are infrastructure.

**Trap**: `Context` is overloaded — it can mean React Context (framework, exclude)
or Bounded Context (DOS concept, keep). Look at the import to disambiguate.

---

## Pattern 8: Tense/Aspect-as-Object

**Symptoms**: Multiple objects representing the same thing in different
states: `DraftPost` / `PublishedPost` / `ArchivedPost`. Or:
`PendingOrder` / `CompletedOrder` / `CancelledOrder`.

**Why bad**: State is a property of an object, not a separate object.

**Correction**: One object (`Post`, `Order`) with a `status` enum field.
The differences in behavior across states belong in `rules` (e.g.
"a Post with status='archived' cannot be edited").

**Exception**: When the states have **truly different lifecycles, owners, or
permissions**, splitting can be correct. E.g., `Quote` and `Order` in some B2B
systems are genuinely different objects, even though one becomes the other —
because Quote can be edited by sales, Order cannot, and the transition is a
formal event.

Apply Judgment 2 to distinguish.

---

## Pattern 9: Container-Without-Contents

**Symptoms**: An object exists only to hold other objects, with no behavior,
no rules, no identity beyond grouping. Examples: `TopicList`, `MessageCollection`,
`UserSet`.

**Why bad**: These are usually **derived views** (compositions), not first-class
objects.

**Correction**: Move to `composition` section. Document what they're derived
from. Example:

```yaml
composition:
  Feed:
    description: "User's home timeline"
    derived_from:
      - "Tweets authored by Persons that the current user FOLLOWS"
      - "Sorted by created_at descending"
    is_persistent: false
```

**Exception**: If the container has its own identity, lifecycle, and rules
(e.g. `Playlist` in a music app — it has an ID, an owner, edit history, sharing
rules), it IS a first-class object. The test is whether you can talk about
`Playlist` independently of its tracks; you can. Whereas `TopicList` only
exists relative to the topics inside.

---

## Pattern 10: AI-Hallucinated Concept

**Symptoms** (specific to AI extraction): The proposed object doesn't appear
in the codebase at all, but the AI suggested it because "this kind of system
usually has X".

**Why bad**: The DOS is supposed to describe **this** system, not a generic
template. Hallucinated objects waste reviewer time and erode trust.

**Correction**: Every object in the DOS must trace to either:
- Concrete code evidence (class name, table name, type definition).
- Concrete documentation evidence (README mention, design doc).
- An explicit user-confirmed addition during a checkpoint.

If none of these apply, exclude.

---

## How to use this catalog

When classifying candidate objects:
- For each candidate **business** object, run patterns 1, 2, 7 to see if it's
  actually UI/impl/framework noise misclassified.

When converging the surviving objects:
- Run patterns 3, 4, 5, 6, 8, 9 on the surviving business objects to find
  merges, splits, and demotions.

When drafting `dos.yaml`:
- Run pattern 10 as a final check on every object before writing it into
  the DOS.

When recording the audit trail:
- For each anti-pattern that triggered while classifying or converging, record it
  in `decisions.md` AND in the DOS's own `anti_patterns` section if there's
  evidence the codebase actually exhibited it.
