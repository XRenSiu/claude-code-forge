---
component: thought-genealogy
version: 0.1.0
purpose: Upstream influences (3-5) and downstream descendants (≥3) of the persona's thought, with substantive textual links rather than namedropping. Used by public-mirror schema to situate the persona in an intellectual lineage.
required_for_schemas: [public-mirror]
optional_for_schemas: []
depends_on: [identity, mental-models]
produces: []
llm_consumption: progressive
---

## Purpose

A public-mirror persona that can't say "I learned this move from X and taught it to Y" is a flattened persona. Thought genealogy gives the produced skill a *position in the network* — it can decline a question on the grounds that it belongs to an upstream influence, or it can locate a user's intuition inside a downstream descendant and route accordingly.

Crucially, genealogy is not a reading list. Each edge must carry a *substantive link*: a specific idea transferred, with corpus evidence on both ends of the edge when possible.

## Extraction Prompt

**Input**: Persona's own corpus (who they cite, whom they thank, who they argue with) plus targeted lookups for downstream citations (who cites the persona substantively, not in passing).

**Procedure** (LLM executes):

1. **Upstream pass**: scan the persona's corpus for attribution signals — "I got this from…", "X taught me…", "I disagree with Y because…", reading lists, dedications.
   - Accept 3-5 upstream influences.
   - For each, name the **specific idea transferred**, not the influencer's whole oeuvre.
   - Require ≥2 corpus citations from the persona demonstrating the borrowing.
2. **Downstream pass**: search for thinkers, movements, or works that cite the persona as formative.
   - Accept ≥3 downstream descendants.
   - For each, name the **specific idea received** and cite where the descendant acknowledges it.
   - Downstream citations come from the descendant's corpus, not the persona's.
3. Reject any edge where the link reduces to "was in the same field" or "wrote a blurb". This is namedropping, not genealogy.

**Output schema**:

```yaml
upstream:
  - influence: <name>
    idea_received: <specific move or framing>
    persona_citations:
      - source: <persona's work>
        passage: "<quote or locator>"
      - source: ...
    confidence: high | medium | low

downstream:
  - descendant: <name or movement>
    idea_transmitted: <specific move>
    descendant_citations:
      - source: <descendant's work>
        passage: "<quote or locator>"
    confidence: high | medium | low
```

**Anti-example**: `upstream: [{influence: "Hemingway", idea_received: "writing"}]` — whole oeuvre handwave, not a specific idea, no passage.

## Output Format

The generated `thought-genealogy.md` in the produced skill contains:

1. **Frontmatter** with `produced_for` fingerprint.
2. **`## Upstream`** — 3-5 entries as H3 blocks (influence name + idea + citations).
3. **`## Downstream`** — ≥3 entries in the same shape.
4. **`## Disavowed Lineage`** — optional: 1-3 figures the persona is commonly *assumed* to descend from but explicitly rejects, with the persona's own rebuttal cited.

Rendering prefers prose over tables here — the link is the content.

## Quality Criteria

1. **Edge substantiveness** — 100% of edges name a specific idea, not a whole body of work; persona-judge spot-checks 3 edges.
2. **Bidirectional evidence** — upstream edges carry ≥2 citations from the persona; downstream edges carry ≥1 citation from the descendant. Missing descendant-side citation auto-downgrades confidence to `low`.
3. **Count floors** — upstream ∈ [3, 5], downstream ≥ 3.
4. **No self-reference loops** — an edge cannot cite the persona citing themselves; the corpus boundary matters.
5. **Disavowal honesty** — if public sources commonly mislabel the lineage, the component is expected to include a `## Disavowed Lineage` section rather than silently omit.

## Failure Modes

- **Namedropping**: entries list famous figures with no specific idea transferred. Fails edge-substantiveness; REMOVE.
- **Reading-list pretense**: `upstream` populated from the persona's bookshelf / syllabus rather than demonstrable borrowings. Without `persona_citations`, the edge is speculative; REMOVE.
- **Downstream hallucination**: descendants named without descendant-side citations. The LLM often confabulates influence claims in this direction; require direct quotation.
- **Whole-oeuvre handwave**: `idea_received: "his whole way of thinking"` — not actionable. Rewrite to a specific move.
- **Contemporary confusion**: listing a peer the persona *debated* as an upstream influence. Peers go in `internal-tensions` or `mental-models` context, not here.
- **Lineage flattery**: picking famous descendants to inflate the persona. Filter by demanding substantive citation.

## Borrowed From

- `alchaincyf/nuwa-skill` — https://github.com/alchaincyf/nuwa-skill [UNVERIFIED-FROM-README]
  > Quoted from PRD §6: *"认知 OS 架构、三重验证、七轴 DNA、6 agent 并行、质量验证"* — nuwa explicitly models a thought lineage layer as part of the public-mirror skeleton. We inherit the layer and the upstream/downstream symmetry.
- Golden sample: `munger-skill` https://github.com/alchaincyf/munger-skill [UNVERIFIED-FROM-README] — used as the target-density exemplar for upstream (Franklin, Graham) + downstream (value-investing descendants) edges, each with specific idea transferred.

## Examples

```markdown
### Upstream: Benjamin Graham

Idea received: the reframing of securities analysis as a search for discrepancies between price and intrinsic value, specifically the "margin of safety" construction.

Persona citations:
  - 1988 letter: "I learned more from chapter 8 of *The Intelligent Investor* than from any business school course."
  - 2003 interview, 12:40: "Graham gave me the frame; I swapped out the filter."

Confidence: high
```
