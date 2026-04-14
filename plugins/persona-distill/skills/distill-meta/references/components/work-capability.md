---
component: work-capability
version: 0.1.0
purpose: PART A of the colleague/mentor architecture — the target's work-domain capability encoded as domains, methodologies, decision heuristics, and anti-patterns, separate from personality.
required_for_schemas: [collaborator, mentor]
optional_for_schemas: []
depends_on: [identity]
produces: []
llm_consumption: eager
---

## Purpose

`colleague-skill`'s core architectural insight is that a workplace persona is two orthogonal things: *how they work* (Work) and *how they show up* (Persona). Mixing them produces skills that either have no real craft (pure vibes) or no real voice (pure process). `work-capability` is the Work half — a structured map of what the target actually knows how to do, the procedures they follow, the rules-of-thumb they apply inside their craft, and the mistakes they consistently refuse to make.

For the `collaborator` schema this pairs with `persona-5layer`; for `mentor` it pairs additionally with `mental-models` and `decision-heuristics` (work-specific heuristics live here; general life heuristics live in the dedicated component).

## Extraction Prompt

**Input**: Workplace corpus — Feishu/Slack/DingTalk threads, PR reviews, email threads, meeting notes, design docs, one-on-one transcripts. Redacted.

**Procedure** (LLM executes):

1. **Domain pass** — cluster the corpus by subject matter. Accept 3-7 domains; reject a candidate domain with fewer than 15 corpus hits.
2. For each domain, extract:
   - **Methodologies**: named procedures or prompts the target visibly follows (checklist they repeat, templates they reuse, questions they always ask first).
   - **Decision heuristics (work-specific)**: IF-conditions the target applies inside this domain (e.g., "IF a PR touches auth AND no test was added, THEN block"). Keep to 3-7 per domain.
   - **Anti-patterns**: failure modes the target has explicitly named or repeatedly pushed back against.
3. For each extracted item, carry ≥1 corpus citation.
4. Refuse to emit a domain where *mechanism* is missing — a bare skills list ("good at debugging") is not a domain entry.

**Output schema**:

```yaml
domains:
  - name: <domain>
    scope: <one-paragraph definition>
    methodologies:
      - name: <procedure name>
        steps: [<step>, <step>, ...]
        citation: <corpus id>
    heuristics:
      - if: <condition>
        then: <action>
        citation: <corpus id>
    anti_patterns:
      - description: <the failure mode>
        rebuttal: <what target says/does instead>
        citation: <corpus id>
```

**Anti-example**: `domains: [{name: "backend", methodologies: ["writes good code"]}]` — no mechanism, no citations, will be rejected.

## Output Format

The generated `work.md` inside the produced skill contains:

1. **Frontmatter** with `produced_for` fingerprint.
2. **`## Domains`** — one H3 per domain, containing scope paragraph + methodology list + heuristic list + anti-pattern list, in that order.
3. **`## Cross-Domain Moves`** — 1-3 moves the target reuses across domains (e.g., "always asks 'what's the simplest version that could fail?' regardless of domain").
4. **`## Out-of-Scope`** — 2-5 domains the corpus suggests the target defers on or declines; fed into `honest-boundaries`.

## Quality Criteria

1. **Mechanism over label** — every methodology has ≥2 steps; no one-word entries.
2. **Citation coverage** — ≥80% of heuristics and methodologies carry a corpus citation.
3. **Domain separability** — no two domains overlap >50% in their heuristic set; overlap indicates over-splitting.
4. **Anti-pattern presence** — every domain has ≥1 anti-pattern; a capability map without refusals is suspect.
5. **Runtime executability** — a downstream agent can read a heuristic's IF/THEN and act on it without additional context.

## Failure Modes

- **Skills-list syndrome**: domains collapse to bullet lists of tools/languages ("Python, SQL, debugging") with no methodology or heuristic. The result reads like a résumé, not a capability model. REMOVE.
- **Methodology inflation**: methodologies named after generic SE concepts ("code review") without the target's specific steps. DILUTE — re-extract from citations.
- **Ghost domains**: a domain is emitted because the corpus *mentions* it, but the target never actually operates in it. Catch via citation count < 15; demote to `## Out-of-Scope`.
- **Persona leakage**: personality observations ("is patient with juniors") smuggled into work domains. Belongs in `persona-5layer`, not here; strip at review.
- **Heuristic inflation**: emitting 20+ heuristics to look thorough, most of which are tautological. Keep 3-7 per domain; move overflow to DILUTE review.

## Borrowed From

- `titanwings/colleague-skill` — https://github.com/titanwings/colleague-skill [UNVERIFIED-FROM-README]
  > Quoted from PRD §6: *"双层架构（Work+Persona）、5 层人格、采集脚本套件、merger/correction"* — we adopt the Work/Persona bifurcation wholesale, materializing the Work half as this component. We drop the colleague-only framing so `mentor` can reuse the same capability map.

## Examples

```markdown
### Domain: API Design Reviews

Scope: any PR that changes a public HTTP or gRPC contract for the payments service.

Methodology — "Consumer First" Review:
  1. Open the contract diff before the implementation diff.
  2. List every consumer (grep service mesh).
  3. Ask: which consumer breaks silently?

Heuristics:
  - IF a field is removed AND consumers > 1 THEN require a deprecation window, not a rename.
  - IF a new enum value is added THEN require clients to declare forward-compat behavior in the PR description.

Anti-patterns:
  - "Version in the URL": target consistently pushes back, cites a 2022 incident where v2 and v1 diverged silently.
```
