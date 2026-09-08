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
version: 0.6.1
user-invocable: true
# imported into AI-DLC 2026-09-05 from looper v0.2.0; body kept, AI-DLC wiring added (see 接线 / 术语映射)
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
  to" (canonical key, or a declared `objects.<X>.synonyms` / `rules[].aliases` entry).
  `verify_issue.py --dos`, `lint_cards.py --dos` and `verify_vocabulary.py` all import it, so
  closure means one thing on every side of the seam. `Closure.vocabulary()` is the same file's
  answer to the *other* question — which words ARE the contract — so the drift sensor never
  grows a second, subtly different reader of `objects:` / `rules:`.
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
- **`assets/dos_template.yaml`** — the named 12-section output structure (so a value cannot
  land in the wrong section). **`assets/decisions_template.md`** — the audit-trail shape,
  including the `## Naming waivers` section `verify_dos.py --decisions` reads.
- **`assets/docs_extraction_prompt.md`** — the procedure + output format for the docs scan.

## The exit — mechanical pre-gate, then the real guarantee

`scripts/verify_dos.py <dos.yaml> [--decisions decisions.md]` is the **mechanical pre-gate** —
and it checks the *product*, not mere well-formedness (it rejects UI/impl-suffixed object names,
undeclared relationship refs, >7 objects). Run it before presenting. It **rejects** on:

- >7 objects → **reject** (a justification for exceeding is a human waiver recorded in
  `decisions.md`; the script does not auto-detect it — it errs strict, the judge relaxes);
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
  non-trivial merge, and **wait for confirmation** before drafting.
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

## agent-map：仓库怎么干活（v0.3.0）

DOS 说的是「系统里有什么、叫什么、什么不可违反」。它不说「测试怎么跑、构建怎么起、哪个目录管什么」——
而那恰恰是一个无上下文的实现者上手时必问、卡里又从来没有的四件事。AI-DLC 有意不做 rules/ 与 hooks
（怕注入每个会话），结果这部分知识回到了每个人自己的 CLAUDE.md，正是「不同人给的上下文不一样」这个
差异的来源。

产物 `agent-map.md`（形状 `assets/agent_map_template.md`），四节：**跑起来** / **目录职责** /
**禁区** / **已知陷阱**。三条纪律由 `scripts/verify_agent_map.py --probe` 编译：

- **命令必须真能跑**：`--probe` 逐条执行并比对期望退出码。跑不通的命令比没有命令更糟——
  实现者会照着它试三次再去猜。没有 `--probe` 的一次检查，输出里写明 `probed=false`：那时候
  这份地图里的命令是**声明**，不是事实。
- **陷阱必须有来路**（`ledger:` / `issue:#N` / `commit:sha` / `file:`）。没有来路的陷阱是想出来的，
  不是这个仓库里的——与 `invariant-extract` 的 provenance 纪律同源。
- **占位符不算填写**；没有的项写 `无`（那是一条信息：实现者不必去找）。

不是把 README 塞给 agent：2607.27250 那 288 次运行说，把仓库知识堆进上下文**不提高正确率**。
所以地图只装这四样，且由 `../plan-cards/scripts/slice_agent_map.py` 按卡切片后才进 `card_context.md`。

## 接线（在 AI-DLC 里的位置）

- **X1 DOS 生命周期的现状本体一源**：产出的 `dos.yaml` 是 `/issue --dos`（依赖 DOS 词表闭包）、
  `lint_cards.py --dos`（卡的 dos_slice 闭包）与 `verify_vocabulary.py`（**全部下游制品的散文**）
  的解析源；闭包失败 = 客观触发 PSL 轨。
  三个消费者分工不重叠：前两个查**声明**（作者主动列出来的名词），第三个查**散文**——
  契约的 statement、卡的 notes、spec、issue / PR body。本体在生命周期里因此有两个时刻：
  **写下来**（本 skill 的产出，`verify_dos.py` 把关）与**被遵守**（`verify_vocabulary.py` 持续
  测量）。只有第一个而没有第二个，本体会安静地过期——这正是 AI-DLC 2.0 没有本体、
  只能靠事后学习循环一次记一个词所付的代价；有本体却不拿它当传感器，等于自愿退化到那个位置。
  两个消费者都 import `scripts/dos_closure.py`，所以**闭包认 `objects.<X>.synonyms` 与 `rules[].aliases`**：
  收编来的词表（qanat 的 `Territory` / `Run` / `MemoryAsset`）要么写进 synonyms 成为闭包源，
  要么在术语映射表里写明"不参与闭包"——只活在映射表里而下游按 key 闭包，是本次实测咬人的地方。
- **应然本体**（`/psl-derive` 的 `dos-proposal.yaml`，同一 schema `assets/dos_template.yaml`）与本 skill 的现状本体
  逐条对账。对账的**产物是文件不是散文**：`scripts/reconcile_dos.py --as-is dos.yaml --to-be
  derived/dos-proposal.yaml --map "<to_be>=<as_is>,…" --output dos-reconciled.yaml`。
  一致 → `identical`；名异实同 → 折进 `synonyms`（下游一份闭包源同时认两套词）；
  应然有而现状无 → `unmapped_to_be`，进 `open_questions` 等人裁决，脚本不替你造映射；
  同 id 不同语义的规则 → `rule_conflicts`，同样是人的活。对账表本身仍在 G1 记录里，
  但 `dos-reconciled.yaml` 让 lint / verify 不必再被手工指到某份提案文件上。
- **YAML / Markdown 为主的仓库**（插件、基础设施、schema-first 服务）：`inventory.py` 的结构化通道
  出 `$defs` / schema property / enum / 判别值，docs 通道用 `count_terms.py` 出可复现计数；
  代码通道抽出 0 个名词是**关于这个仓库的事实**，照实写进 `decisions.md`（模板已留位置），
  不要装作有一张剪枝表。
- **agent 无写权**：`dos.yaml` 进 G2 锁与卡的 `forbidden_files`；改本体走变更提案（本体层回流）。
- 路径记入 `aidlc_state.py set world.dos=…`（由编排者记，不是本 skill 的执行者）。

## Exit gate for this skill itself

Verify with skillwise `evaluate-skill`. A read is not the verdict (an unguided judge is ~46%
on "which skill is better"). Scaffold tier: static structural read + one smoke run on a small
repo. Production tier: with/without `delta_exist` on held-out repos — until such a set exists
this honestly sits at `static_only`.
