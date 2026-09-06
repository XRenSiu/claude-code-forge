# Convergence (Judgments 2 & 4) — sdlc plugin

Surviving business candidates after J1: Run, Contract (+AC), Card, Gate, Event (+Failure/Reflow/Ledger/Trace), Node
(+skill/agent/human/stage), Loop (+Ring?), plus the GitHub / world / evaluation neighbours.

## Merges (Judgment 2)

### Run ← { run, slug, feature, 一次交付, lifecycle instance, `.sdlc/<slug>/` }
- Lifecycle: identical (init → intake … archive; one state.json).
- Permission: identical (script-owned state; human-signed gates).
- Sentence test: "a Run PASSES a Gate" ✓ · "a Feature passes a gate" ✗ (feature = the requirement) · "a Slug …" ✗ (identifier).
- Chosen: **Run** (weak docs frequency; strongest explicit definition is the 术语映射 "Run = 一次 issue → PR 的交付"). Confidence medium.

### Contract ← { 契约, done_when.yaml, 判据契约, acceptance contract, contract.yaml(接口契约, blank) } ; AC absorbed as items
- AC vs Contract: AC has no lifecycle apart from its Contract (frozen together, superseded via change proposal) → items.
- REQ vs AC: different lifecycle (REQ stable, never renumbered, authored upstream) → REQ stays a referenced id, not merged.
- Rejected names: DoneWhen (file-name leak), Spec (spec.md is the EARS form, docs keep them distinct), AcceptanceCriteria (the items).

### WorkUnit ← { 卡, 任务卡, Card, CARD-xx, prompt 载荷 }
- Docs and code both say 卡/Card. `verify_dos.py` rejects any object name ending in `Card` (UI-suffix heuristic, no whitelist, exit 1).
- Chosen: **WorkUnit** (= docs definition "自包含的任务单元"); `Card` recorded as canonical synonym. Rejected: Task (collides with TASK 轨/L1 TASK), Assignment (not the team's word, awkward "assignment-level acceptance").
- This is a verifier-forced rename, logged loudly (decisions.md, Q001).

### Gate ← { 门, 三道门, G1/G2/G3, gate record, human seam }
- Kept distinct from Node(kind=human): declaration vs per-Run verdict record (different lifecycle).
- Kept distinct from 闸/预门 (mechanical pre-gates are edge guards / prereqs, not Gates) — docs also call two script checks "自动门"; resolved by definition: Gate = human-signed.
- human.merge / human.harness-review are human Nodes without a Gate record → not Gates (docs: "merge 是人类动作"). Flagged Q004.

### Event ← { 账本记录, 迹事件, fail, reflow, gate event, card event, waiver, failure_report, escape }
- Lifecycle: identical (append-only, immutable). Permission: identical (script-appended).
- Skeleton: {id, at, stage, kind, signal?, layer?, fingerprint?, note, decision, by, refs} — shared; `kind` discriminates (Pattern 8 healthy unification; few exclusive fields).
- Ledger (ledger.md) and Trace (trace.jsonl) are two projections of the stream → composition (Pattern 9).
- Event-sourced exception to Pattern 4 applies: trace.py why/impact and metrics.py query the log as source of truth.
- Rejected: LedgerEntry/TraceEvent (projection leak), Record (empty), Failure (one kind only).

### Node ← { 节点, skill node, agent node, human node, stage node, participant }
- skill/agent/script/asset are framework constructs (Pattern 7); the domain-level thing is the boundary identity graph.yaml declares.
- Sentence: "an evaluator Node HANDS_OFF only fix_prompt to an implementer Node" ✓.
- Divergence noted: 5 agents in `agents/` but 4 `kind: agent` nodes in graph.yaml (pr-reviewer missing).

### Loop ← { 环契约, loops.yaml entry, 六个环 } — NOT merged with Ring
- Ring (九环 R0–R8) vs Loop: different skeleton (phase grouping vs cycle contract with generator/verifier/stop). Chinese 环 covers both → two concepts.
- Ring → composition derived from Node.role (graph.yaml roles ≈ rings: world=R0 … learning=R8, orchestrator=脊柱).
- Trigger → Loop.trigger (value).

## Demotions

- Lock → Contract.lock (value object; stage g2|l5, signed_by, signed_at, files).
- Waiver, Assumption → Run values. Fingerprint, Signal, Layer, Track, Stage → enums/values.
- RoutingRule → rules (constitution) + policy (contents); Event.refs decided_by `routing.Rxx`.
- FailureReport, ChangeProposal, Archive, Ledger, Trace, Graph, Ring, EvidenceLog → composition.

## Bounded contexts (Judgment 4)

Attribute overlap test on the multi-area nouns:

| Noun | Areas that care | Overlap | Verdict |
|---|---|---|---|
| skill | execution graph (reads/writes/authority) · plugin packaging (version, user-invocable) · skill evaluation (gate.json tier/fix_list) · rings | id only | split: lifecycle owns **Node**; packaging + evaluation are upstream contexts |
| issue / PR / thread | GitHub (body, comments, resolved) · lifecycle (number/url/size_class/merge.sha) · review_loop (verdicts, strikes, watermark) | id/url | GitHub upstream; lifecycle keeps slim refs |
| finding / verdict | evaluation (severity, tier, confidence, vendor, four-state) · lifecycle (file:line, tier→veto, signal) | thin | evaluation is a downstream/return context; verdicts translate to Event signals |
| PSL / DOS / invariant | world (six layers, R00x, provenance) · lifecycle (paths in Run.world, closure) | paths + ids | world upstream (R0/R1) |

Current context = **software delivery lifecycle** (7 objects). Others recorded in `bounded_contexts` with translation notes.
