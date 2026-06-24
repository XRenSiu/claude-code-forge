---
name: dos-extract
description: |
  Use when a codebase has NO shared ontology — when the team (and AI agents) lack a
  single agreed vocabulary of what the system's core objects, relationships, and
  constitutional rules ARE, and you want to reverse-engineer one from the existing
  code (and docs). Produces a Design Ontology Spec (DOS): a `dos.yaml` (12-section
  ontology) + `decisions.md` (audit trail of every non-trivial naming/classification
  judgment). The gap is not scanning — the engine can grep nouns — it is the *semantic
  judgment* the engine skips: which noun is a real business object vs a UI artifact vs
  an implementation detail vs a rule; which are synonyms of one thing; which rules are
  constitution vs transient policy; where the bounded-context seams are. Triggers:
  "DOS", "提取本体" / "本体提取", "ontology extraction", "domain model", "ubiquitous
  language", "design ontology spec", "给这个项目立个宪法", "extract the domain model so
  AI agents can use it", "retrofit a contract over a vibe-coded prototype". The symmetric
  counterpart of invariant-extract (which abductively recovers a single Territory's □
  invariants from failures); this one deductively recovers the system's ontology +
  constitution from a static repo. Do NOT use for: a single Territory's resident
  invariants (that is invariant-extract), or task-level acceptance criteria (acceptance-spec).
argument-hint: "[repo path] [--auto]"
version: 0.2.0
user-invocable: true
---

# dos-extract

Reverse-engineer a **Design Ontology Spec** from a repository. The product is two files:
`dos.yaml` (the 12-section ontology) + `decisions.md` (why `Topic`, not `TopicNode`).
This skill describes what a DOS is, the judgments that separate a real ontology from a
scan dump, the primitive that does the mechanical scanning, the human seam, and the exit
that certifies the result. **It prescribes no step order — the engine sequences the work;
what follows are the gaps and the gates.**

## The gap (why a scan is not an ontology)

A composite of three atoms: **Knowledge** (what a DOS is — the 12-section format, the
code-vs-docs signal priority), **Capability** (the mechanical noun/verb scan — a primitive
the engine otherwise mis-improvises), **Judgment** (the four classification calls below).

The load-bearing reason this is not free:

> **Code contains the *current implementation choices*, not the *ontology that should
> exist*.** A naive "scan code → emit objects" pass freezes mistakes into the contract: a
> `CommentCard` React component becomes a `CommentCard` object — wrong twice (it is UI, and
> `Card` is presentation, not domain).

Deletion test: remove this skill and ask the engine to "extract a DOS from this repo." It
greps nouns and emits a polluted ontology — UI elements and `*Repository`/`*Service` names
promoted to objects, no ≤7 discipline, code vocabulary winning over the team's language.
The gap is the *semantic judgment*, plus the knowledge of what a clean DOS looks like.

## The world

- **A DOS** is a YAML contract in a fixed 12-section shape (`assets/dos_template.yaml`):
  meta, scope, objects, relationships, rules, composition, behaviors, bounded_contexts,
  agent_guidelines, anti_patterns, open_questions, evolution_log. It is the shared language
  between humans and AI agents — code converges to it, not it to code.
- **Two signal sources, divergence is signal.** *Code* shows what was built; *docs* show
  what the team talks about. When they agree, confidence is high. When they diverge (docs
  say `Topic`, code says `Node`), that divergence is itself evidence — and for ontology
  questions **docs generally outrank code** (code drifts under deadline; docs reflect intent).
  Full priority rules: `references/methodology.md` (code-vs-docs signal priority).
- **Output is two files.** `dos.yaml` (the ontology) + `decisions.md` (the audit trail —
  every non-trivial judgment traceable to one of the four by name).

## What counts as correct (the judgments — declared, not sequenced)

The whole skill is the application of **four judgments** (full procedures + worked examples
in `references/judgments.md`). They are the criteria, holding whenever a term is evaluated:

1. **Object vs UI vs Impl vs Rule.** A business object is describable without referring to a
   screen and does not end in an infra suffix (`Repository`/`Service`/`Manager`/`DTO`/…). 90%
   of ontology pollution is misclassifying this.
2. **Same object vs two objects.** Same lifecycle + same permission model + same skeleton →
   merge (the merge error is the common one in extraction).
3. **Constitution vs policy.** "If I removed this rule, is the system still recognizably
   itself?" No → constitution (goes in `rules`). Yes → policy (does NOT enter the DOS).
4. **Single vs multi context.** Small attribute overlap across consuming areas → split into
   bounded contexts, owned by one and referenced by others.

Plus the standing quality criteria (the exit, below, makes these runnable): **≤7 core
objects** (or documented justification), relationships reference only declared objects,
every `agent_guidelines.must_not` traces to an anti-pattern or rule, naming follows the
docs-win priority, and `open_questions` is non-empty (a DOS with none is dishonest).

## Primitives (the mechanical share — `scripts/`, `assets/`)

- **`scripts/inventory.py`** — the deductive scan: emits frequency tables of business nouns
  (class/type/table names, API path segments) and verbs, with example locations. Named-table
  output so classification has clean material. It exists; the engine runs it — the body does
  not narrate a call sequence.
- **`assets/dos_template.yaml`** — the named 12-section output structure (so a value cannot
  land in the wrong section). **`assets/decisions_template.md`** — the audit-trail shape.
- **`assets/docs_extraction_prompt.md`** — the procedure + output format for the docs scan.

## The exit — mechanical pre-gate, then the real guarantee

`scripts/verify_dos.py <dos.yaml>` is the **mechanical pre-gate** — and it checks the
*product*, not mere well-formedness (it rejects UI/impl-suffixed object names, undeclared
relationship refs, >7 objects). Run it before presenting. It **rejects** on:

- >7 objects → **reject** (a justification for exceeding is a human waiver recorded in
  `decisions.md`; the script does not auto-detect it — it errs strict, the judge relaxes);
- every object in `relationships` is declared in `objects`; every relationship has both
  cardinality sides;
- no object name carries a UI/impl suffix (`*Card`, `*Repository`, `*Service`, …);
- the load-bearing sections (`objects` / `relationships` / `rules`) present — omission rejects;
  the softer six are reported as `info`, not rejected;
- `open_questions` non-empty.

The semantic half — is this *really* a business object? did Judgment 2 merge correctly? does
each `agent_guidelines.must_not` trace to an anti-pattern or rule? — is a judge call against
the four judgments; `verify_dos.py` *flags* these (`needs_semantic_review`), it does not decide
them. The **certified guarantee** is that judge call + the human seam + (production)
`delta_exist` on held-out repos (`static_only` today); the script lowers defect frequency.

## The human seam (Control — role separation, non-skippable)

The human owns the two highest-stakes judgment calls; the machine drafts only after sign-off.
This is the judgment ↔ capability boundary:

- **Classify** (Judgment 1) and **Converge** (Judgments 2 + 4) are where errors propagate
  everywhere downstream. In **interactive mode (default)**, surface the classification buckets
  + the full `unclear` list + the most surprising calls, and the ≤7 converged list + every
  non-trivial merge, and **wait for confirmation** before drafting.
- In **`--auto` mode**, the machine makes the calls itself but logs every one to `decisions.md`
  (the trade-off seen, the choice made) so the human audits after. Auto trades the live seam
  for a complete audit trail — never for silence.

Mode is chosen at the start (request contains `--auto` → auto; else interactive). Intermediate
artifacts live in a `.dos-extract/` workspace; finals copy to the project root.

## High-risk — never do (non-waivable)

- **Never promote a UI element or an infra-suffixed name to a business object** (`TopicCard`,
  `UserRepository` are not objects).
- **Never let code vocabulary win over docs for naming** unless docs are demonstrably stale —
  and then flag it loudly in `decisions.md` + `open_questions`.
- **Never exceed 7 core objects without a documented justification** (it usually means
  Judgment 2 or 4 was skipped).
- **Never bake policy as constitution** (Judgment 3) — a pricing/limit/A-B rule in `rules`
  makes the DOS a moving target and destroys its authority.
- **Never invent `anti_patterns` the codebase didn't exhibit** — that section records real
  history, not generic warnings (those are `agent_guidelines`).
- **Never present a DOS with `open_questions: []`** — it is either trivial or dishonest.

## References

- `references/judgments.md` — the four judgments, full decision procedures + worked examples.
  **Read in full; the whole pipeline is their application.**
- `references/methodology.md` — code-vs-docs signal priority, the quality/evaluation criteria,
  versioning, bounded-context detection. (Describes the methodology's typical chaining as
  *guidance*; the engine sequences — the stage names there are descriptive, not a mandated march.)
- `references/anti_patterns.md` — known ontology-pollution patterns; a checklist for classify/converge.

## Edge cases

- **Monorepo** → one bounded context per package; build a top-level context map at the end.
- **Greenfield (little code)** → switch input to README + design docs; label it "DOS v0.0,
  before-code edition."
- **Mock/stub-heavy** → filter test fixtures from the inventory (ghost objects like `MockUser`).
- **Disagreement after the fact** → re-run the relevant judgment; workspace artifacts persist.

## Exit gate for this skill itself

Verify with skillwise `evaluate-skill`. A read is not the verdict (an unguided judge is ~46%
on "which skill is better"). Scaffold tier: static structural read + one smoke run on a small
repo. Production tier: with/without `delta_exist` on held-out repos — until such a set exists
this honestly sits at `static_only`.
