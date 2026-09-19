---
name: dos-extract
description: |
  Use when a codebase has NO shared ontology — when the team (and AI agents) lack a
  single agreed vocabulary of what the system's core objects, relationships, and
  constitutional rules ARE, and you want to reverse-engineer one from the existing
  code (and docs). Produces a Design Ontology Spec (DOS): a `dos.yaml` (13-section
  ontology in TWO layers — the core model of ≤7 objects + rules, and the complete
  `vocabulary`: every other term the team says, with kind, owner, synonyms and rejected
  names) + `decisions.md` (audit trail of every non-trivial naming/classification
  judgment). The gap is not scanning — the engine can grep nouns — it is the *semantic
  judgment* the engine skips: which noun is a real business object vs a UI artifact vs
  an implementation detail vs a rule; which are synonyms of one thing; which rules are
  constitution vs transient policy; where the bounded-context seams are — and the
  *placement* discipline the engine also skips: a term that is not a core object still
  has exactly one home in the DOS, never the bin. Triggers:
  "DOS", "提取本体" / "本体提取", "ontology extraction", "domain model", "ubiquitous
  language", "design ontology spec", "给这个项目立个宪法", "extract the domain model so
  AI agents can use it", "retrofit a contract over a vibe-coded prototype". The symmetric
  counterpart of invariant-extract (which abductively recovers a single Territory's □
  invariants from failures); this one deductively recovers the system's ontology +
  constitution from a static repo. Do NOT use for: a single Territory's resident
  invariants (that is invariant-extract), or task-level acceptance criteria (acceptance-spec).
argument-hint: "[repo path] [--auto]"
version: 0.11.2
user-invocable: true
---

# dos-extract

Reverse-engineer a **Design Ontology Spec** from a repository. The product is two files:
`dos.yaml` (the 13-section ontology: a **core model** of ≤7 objects + rules, and the
**complete vocabulary** of everything else the team says) + `decisions.md` (why `Topic`,
not `TopicNode`).
This skill describes what a DOS is, the judgments that separate a real ontology from a
scan dump, the primitive that does the mechanical scanning, the human seam, and the exit
that certifies the result. **It prescribes no step order — the engine sequences the work;
what follows are the gaps and the gates.**

## The gap (why a scan is not an ontology)

A composite of three atoms: **Knowledge** (what a DOS is — the 13-section, two-layer format, the
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

The **second gap** (found on this plugin's own DOS, 2026-09-18) is the mirror image: a skill
that only knows the ≤7 discipline produces a *clean sliver*. The 2026-09-05 dogfood run
classified 45 real terms and shipped 7 objects; the other ~38 — `AC`, `指纹`, `层`, `三档`,
`隐藏集`, `Finding`, `Verdict`, `PSL`, `Territory`… — survived only as prose in `decisions.md`
and a workspace table, where no closure check, no card linter and no drift sensor could see
them. The docs even carried an explicit glossary (`ARCHITECTURE.md §16 术语`, 13 terms) that
the DOS did not lift as a glossary. From outside that reads as "it extracts a small part and
aligns nothing" — and it is right. **≤7 caps the core model, not the language.** No ontology
methodology caps concepts: Ontology 101 enumerates every term first (step 3), METHONTOLOGY
and NeOn open with a glossary, Evans's *Highlighted Core* flags the core inside the full
model instead of deleting the rest, and every AI-facing semantic layer (Palantir, dbt,
Snowflake, DataHub) treats coverage as the accuracy lever. They layer; they do not truncate.
The origin of the ≤7 figure (Jorgenson's "no more than 5 objects") was a consolidation
exercise for a greenfield prototype — never a completeness criterion for an existing repo.
Full grounding: `references/methodology.md` §"Industry grounding".

## The world

- **A DOS** is a YAML contract in a fixed 13-section shape (`assets/dos_template.yaml`):
  meta, scope, objects, **vocabulary**, relationships, rules, composition, behaviors,
  bounded_contexts, agent_guidelines, anti_patterns, open_questions, evolution_log. It is
  the shared language between humans and AI agents — code converges to it, not it to code.
- **Two layers, one file.** `objects` (≤7) + `relationships` + `rules` + `composition` are
  the **core model** — Evans's distillation, what fits on a napkin. `vocabulary` is the
  **ubiquitous language**: every other term the team says, each with `kind` (value · enum ·
  event · command · policy · artifact · role · process · external · concept), `of` (the
  owning object / term — SKOS broader, ISO partitive), a one-sentence `definition`,
  `synonyms` (SKOS altLabel), `rejected_names` (SKOS hiddenLabel / ISO deprecated term — it
  closes so the reader learns the right word, and consumers flag it), `context` (homonyms are
  disambiguated per bounded context), `see_also`, `status` (deprecate, never delete). Judgment 1
  decides a term's *kind*, never its *inclusion*: the placement table in `references/judgments.md`
  maps every bucket to its home. A term with no home is the extraction's loss, and the exit
  measures it (`verify_dos.py --terms`).
- **Two signal sources, divergence is signal.** *Code* shows what was built; *docs* show
  what the team talks about. When they agree, confidence is high. When they diverge (docs
  say `Topic`, code says `Node`), that divergence is itself evidence — and for ontology
  questions **docs generally outrank code** (code drifts under deadline; docs reflect intent).
  Full priority rules: `references/methodology.md` (code-vs-docs signal priority).
- **Output is two files.** `dos.yaml` (the ontology) + `decisions.md` (the audit trail —
  every non-trivial judgment traceable to one of the four by name).
- **They belong in the project directory, committed to git.** The ontology is the team's
  shared vocabulary — one bounded context, one copy, everyone's. Write them at the root of the
  context (`dos.yaml` / `decisions.md`; `docs/` and `ontology/` are also discovered), **never
  under `.aidlc/`** — that is per-run runtime state, so an ontology parked there is found by
  neither the next feature nor the next person. **In a monorepo the context is the package**,
  not the repository: `plugins/<pkg>/dos.yaml`, discovered with
  `repo_assets.py --scope plugins/<pkg>` (which falls back to the root, so one repo-level
  `agent-map.md` and a per-package `dos.yaml` coexist). A root-level DOS covering one package
  of twelve claims a scope it does not have. **The scope is where the context's artefacts live, not
  necessarily a code directory**: a feature-sliced context that spans `app/main` / `app/renderer` /
  `app/common` has no single code directory, so it uses `--scope docs/ontology/<context>`. A scope
  directory that does not exist is reported, because falling back to the root ontology looks exactly
  like "this context has an ontology". `aidlc_state.py repo` reports where they landed and
  whether `git ls-files` can see them; untracked is not "has an ontology", it is
  "you have an ontology". Same for `agent-map.md` and the `invariants/` cards.

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
objects** (or documented justification), **complete vocabulary** (every term the docs and
code inventories counted resolves through some layer — objects, composition, vocabulary,
synonyms, rejected names, rule ids; the unplaced are named), relationships reference only
declared objects, every `agent_guidelines.must_not` traces to an anti-pattern or rule,
naming follows the docs-win priority, and `open_questions` is non-empty (a DOS with none
is dishonest).

**Placement is not a fifth judgment** — it is what happens to Judgment 1's output. The rule
is one line: *every classified term lands in exactly one section, and `decisions.md` is not a
section.* `business` → `objects` (if it survives Judgment 2/4 as one of the ≤7) else
`vocabulary` kind concept; `value` / attribute → `vocabulary` kind value with `of`; enum member
/ discriminator → kind enum with `of`; derived container → `composition`; event / command /
policy → the matching kind (or `behaviors` when it is a cause→effect chain, `rules` when it is
constitution); actor → kind role; another context's noun → kind external with `context`; a
UI / impl / framework name → a `rejected_names` entry on the object it renders or operates on
(so `TopicCard` resolves to `Topic` and is flagged), or nothing at all when it is pure
framework noise (`Middleware`); a rejected canonical → `rejected_names`; a foreign vocabulary
(the 术语映射 tables) → `synonyms` on the object it maps to.

## Primitives (the mechanical share — `scripts/`, `assets/`)

- **`scripts/inventory.py`** — the deductive scan: emits frequency tables of business nouns
  (class/type/table names, API path segments) and verbs, with example locations. Named-table
  output so classification has clean material. It exists; the engine runs it — the body does
  not narrate a call sequence.
  **Two channels.** Class/type declarations in TS/JS/Py/Go/Rust/Java/Kotlin, *and* (on by
  default) YAML/JSON: `$defs` keys, JSON-Schema `properties` children, `enum` members, and
  discriminator (`kind`/`type`) values, plus plain mapping keys down to `--key-depth`. Each
  noun carries its source tag, and the report puts *declarations* above *plain keys* — a repo
  whose objects live in schemas, not classes, otherwise scores **zero nouns** and the operator
  falls back to hand-counting. `--exclude` takes path-segment **names, matched at any depth**,
  not globs.
- **`scripts/count_terms.py`** — the docs channel's counting primitive: a terms file (canonical
  label = variants, literal or `/regex/`) × named corpus globs → a reproducible count table with
  `file:line` evidence. `01b_docs_terms.md`'s frequencies are a measurement, not a recollection.
- **`scripts/reconcile_dos.py`** — the X1 as-is ↔ to-be comparison as a *product*: emits
  `dos-reconciled.yaml`, the as-is DOS with each mapped to-be name folded into `synonyms:`, so
  one closure source accepts both vocabularies. It never invents a mapping — unmapped to-be
  objects and same-id/different-statement rule conflicts come back as human judgments.
- **`scripts/dos_closure.py`** — import-only: the single definition of "what a DOS term resolves
  to": an `objects` / `composition` / `vocabulary` key, a declared `synonyms` entry on any of
  them, a declared `rejected_names` entry (resolves, `via_rejected()` true, consumers flag or
  reject), or a `rules[].id` / `aliases` entry. A label two concepts both claim (`环` on `Loop`
  and on `Ring`) is a **homonym**: it resolves to nothing, `why_unresolved()` says
  `ambiguous: 环 → Loop | Ring`, and the consumer asks for the qualified word. `describe(term)`
  returns canonical / layer / kind / via / of for a consumer that wants to say *why* a word
  closed. `verify_issue.py --dos`, `lint_cards.py --dos` and `verify_vocabulary.py` all import
  it, so closure means one thing on every side of the seam. `Closure.vocabulary()` is the same
  file's answer to the *other* question — which words ARE the contract — so the drift sensor
  never grows a second, subtly different reader of the three layers.
- **`scripts/verify_vocabulary.py`** — the **cross-artifact terminology sensor (B-tier)**. Closure
  used to run in exactly one place: an issue's `依赖 DOS:` field, plus a card's structured
  `dos_slice`. Everything downstream — a contract's `statement`, a card's `notes`, `spec.md`, an
  issue body, a PR body — could introduce a domain noun `dos.yaml` cannot resolve and nothing
  noticed. That is the semantic drift AI-DLC pays for at runtime, one corrected word at a time,
  because it has no ontology to check against. This one does, so the check is mechanical:

      verify_vocabulary.py --dos dos.yaml done_when.yaml 'cards/CARD-*.yaml' spec.md pr-body.md \
                          [--out .aidlc/<slug>/vocabulary-facts.yaml]

  Output: each unresolved domain term with `file:line` and its **closest resolvable neighbour**
  (`transaction` ≈ `BankingTransaction` — the high-value finding), plus the inverse signal
  (ontology entries no artifact uses; weaker evidence, printed, never counted).
  Exit `0` clean · `1` above threshold · `2` usage/IO · `3` **unevaluated** — no `dos.yaml`, or
  no usable term table. A repo with no ontology has not PASSED a terminology check, it simply
  was not checked; `--require-ontology` turns 3 into 1 for the gate posture.
  **The design problem is false positives**, and the conservatism is explicit and configurable:
  a stopword list, code/path/fenced-block filtering, prose-field-only reading of YAML, an
  artifact's own `<!-- out-of-domain: … -->` / `out_of_domain:` declaration, `--waive` and a
  `## Vocabulary waivers` section in `decisions.md` (the same bullet convention `verify_dos.py`
  reads), and a corroboration rule: a term is a finding only when it near-misses the ontology,
  or occurs `--min-occurrences` times (that second class does not gate unless `--count-unknown`).
  `--out` has **no default**: a B-tier sensor gets run ad hoc from wherever you happen to be, and a
  facts file nobody asked for is a file that gets committed by accident. Ask for it, or use `--json`.
  The precision/recall trade-offs, and which of them were bought with a real dogfood run, are
  in the script's docstring.
- **`assets/dos_template.yaml`** — the named 13-section output structure (so a value cannot
  land in the wrong section). **`assets/decisions_template.md`** — the audit-trail shape,
  including the `## Naming waivers` section `verify_dos.py --decisions` reads.
- **`assets/docs_extraction_prompt.md`** — the procedure + output format for the docs scan.

## The exit — mechanical pre-gate, then the real guarantee

`scripts/verify_dos.py <dos.yaml> [--decisions decisions.md] [--terms terms.txt]` is the
**mechanical pre-gate** — and it checks the *product*, not mere well-formedness (it rejects
UI/impl-suffixed object names, undeclared relationship refs, >7 objects, a missing language
layer, a term the inventory counted that the DOS cannot place). Run it before presenting. It
**rejects** on:

- >7 objects → **reject**, cleared only by a `## Naming waivers` bullet named `object_count`
  in `decisions.md` (reported under `waived` and flagged, never silent). Until v0.9.0 the reject
  text named that waiver and no code read it, so the only way past was to ignore a permanently
  red pre-gate — a gate you can only pass by ignoring it is not a gate. The eighth object is
  usually a long-tail term that belongs in `vocabulary`, not another aggregate;
- **`vocabulary` missing or empty** → reject. A core model without its language is half a DOS.
  The one legitimate exception is a to-be proposal derived from a PSL before any code exists
  (`/psl-derive` runs the check with `--core-only`; a `core_only` waiver bullet does the same for
  a hand-run), reported as `mode: core_only`, never silent;
- a vocabulary entry with a `kind` outside the closed set, an empty `definition`, an `of` that
  resolves to nothing (value / enum must name their owner), an `external` with no `context`, a
  `status` outside active | deprecated | proposed, a word that is both a synonym and a rejected
  name, or a synonym that is somebody else's canonical key (one word, one home). A **homonym**
  — the same synonym on two concepts — is *flagged*, not rejected: it is true about the docs,
  the closure refuses the bare word, and the judge confirms the split is real;
- **coverage** (`--terms terms.txt`, the `count_terms.py` file the docs channel already
  produces): every counted label must resolve through some layer. The unplaced come back by
  name, and the report carries `coverage: {terms, resolved, unplaced}`. Without `--terms` the
  report says `unmeasured` — a coverage nobody measured is not a coverage;
- every object in `relationships` is declared in `objects` (a declared synonym resolves, with
  a flag to prefer the canonical name); every relationship has both cardinality sides;
- no object name is **compounded** on a UI/impl primitive (`TopicCard`, `UserRepository`) —
  non-waivable;
- an object name that **IS** a whole primitive (`Card`, `Modal`, `Service`) rejects too, but is
  **waivable**: `--decisions decisions.md` reads a `## Naming waivers` bullet, or `--waive Card`
  for an ad-hoc call. The heuristic exists for `TopicCard`; a whole word can be a real domain
  object, and *renaming the domain to satisfy the heuristic breaks downstream closure* — every
  consumer resolves the operator's actual vocabulary against this file;
- a `properties.<p>.derived_from` that is present but empty;
- the load-bearing sections (`objects` / `relationships` / `rules`) present — omission rejects;
  the softer six are reported as `info`, not rejected;
- `open_questions` non-empty.

It also emits **warnings** that never touch the exit code: `dos.yaml` past `--max-lines` (800)
or past a ~100-lines-per-object budget, and object descriptions that are empty, still a template
placeholder, or longer than a sentence. `references/methodology.md` §6 has stated the 300-500-line
target for 6 objects all along; nothing measured it, so a 719-line draft passed clean.

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
  non-trivial merge **+ the placement of everything that did not make the ≤7** (which
  vocabulary kind, which owner, which rejected names), and **wait for confirmation** before
  drafting. The human is confirming two things: the napkin, and that nothing fell off it.
- In **`--auto` mode**, the machine makes the calls itself but logs every one to `decisions.md`
  (the trade-off seen, the choice made) so the human audits after. Auto trades the live seam
  for a complete audit trail — never for silence.

Mode is chosen at the start (request contains `--auto` → auto; else interactive). Intermediate
artifacts live in a `.dos-extract/` workspace; finals copy to the project root.

## High-risk — never do (non-waivable)

- **Never promote a UI element or an infra-suffixed name to a business object** (`TopicCard`,
  `UserRepository` are not objects). A *whole* primitive is the one waivable case — `Card` alone
  can be a real domain word — and the waiver is recorded in `decisions.md`, never assumed.
- **Never rename a domain object to get past the suffix heuristic.** The rename looks free and is
  not: every downstream closure check resolves the team's real vocabulary against this file, so
  the rename either breaks closure or forces a `synonyms:` entry anyway. Waive, or record the
  synonym — the DOS is the team's language, not the verifier's.
- **Never let code vocabulary win over docs for naming** unless docs are demonstrably stale —
  and then flag it loudly in `decisions.md` + `open_questions`.
- **Never exceed 7 core objects without a documented justification** (it usually means
  Judgment 2 or 4 was skipped — or a long-tail term is being forced into `objects` because the
  extractor forgot `vocabulary` exists).
- **Never let a classified term vanish.** "Absorbed", "demoted", "value of X", "belongs to the
  evaluation context" are placements, not exits: each lands as a `vocabulary` entry (kind
  value / enum / external …), a `composition`, a `rejected_names` or a `synonyms` entry.
  `decisions.md` records *why*; it is not *where*. A term that lives only in `decisions.md`
  resolves nowhere, and downstream that is indistinguishable from a term nobody extracted.
- **Never read ≤7 as the size of the ontology.** It caps the core model. The language is as
  large as the team's, and its size is measured (`--terms`), not chosen.
- **Never delete a term the team stopped using — deprecate it** (`status: deprecated`, or move
  the old word to `rejected_names`): the artefacts that still say it must keep resolving.
- **Never bake policy as constitution** (Judgment 3) — a pricing/limit/A-B rule in `rules`
  makes the DOS a moving target and destroys its authority.
- **Never invent `anti_patterns` the codebase didn't exhibit** — that section records real
  history, not generic warnings (those are `agent_guidelines`).
- **Never present a DOS with `open_questions: []`** — it is either trivial or dishonest.

## References

- `references/judgments.md` — the four judgments, full decision procedures + worked examples.
  **Read in full; the whole pipeline is their application.**
- `references/methodology.md` — code-vs-docs signal priority, the quality/evaluation criteria
  (Simplicity now caps the *core*; Completeness is measured as term coverage), versioning,
  bounded-context detection, and **§Industry grounding**: what DDD, ontology engineering, SKOS /
  ISO 1087 / OBO and the AI-era semantic layers actually say about "core vs complete" — the
  sources behind the two-layer shape. (Describes the methodology's typical chaining as
  *guidance*; the engine sequences — the stage names there are descriptive, not a mandated march.)
- `references/anti_patterns.md` — known ontology-pollution patterns; a checklist for classify/converge.

## Edge cases

- **Monorepo** → one bounded context per package; build a top-level context map at the end.
- **Greenfield (little code)** → switch input to README + design docs; label it "DOS v0.0,
  before-code edition."
- **Mock/stub-heavy** → filter test fixtures from the inventory (ghost objects like `MockUser`).
- **Disagreement after the fact** → re-run the relevant judgment; workspace artifacts persist.

## 与 ai-dlc 的关系（这份拷贝怎么维护）

dos-extract 的开发地是 `plugins/ai-dlc/skills/dos-extract`（它 2026-09-05 从本插件 v0.2.0 引入，之后在那里
长出了两层 DOS、闭包模块、词表传感器与覆盖率闸）。本插件保留一份拷贝，让只装 looper 的用户也能
`/dos-extract`。**`scripts/` · `assets/` · `references/` 与 ai-dlc 那份逐字节相同**，由 ai-dlc 的
`eval/smoke.sh` 一条期望盯着（两边一分叉就红）；本文件是 ai-dlc SKILL.md 去掉 AI-DLC 专属接线
（agent-map、`/issue --dos` / `lint_cards --dos` 闭包接线）后的正文。要改 skill，改 ai-dlc 那份再同步过来，
不要在这里单改。

## Exit gate for this skill itself

Verify with skillwise `evaluate-skill`. A read is not the verdict (an unguided judge is ~46%
on "which skill is better"). Scaffold tier: static structural read + one smoke run on a small
repo. Production tier: with/without `delta_exist` on held-out repos — until such a set exists
this honestly sits at `static_only`.
