---
name: decision-tree
version: 0.1.0
phase: 0.5
consumed_by: distill-meta (Phase 0.5 agent)
produces: schema-decision.json
---

# Schema Decision Tree / Schema 决策树

> **Used by**: Phase 0.5 Schema Decision agent.
> **Authority**: PRD §3.3.
> **Output**: a JSON object (see [Output Schema](#output-schema)) written to the new persona skill's `.schema-decision.json` scratch file.

This tree answers one question: **given what the user told us in Phase 0, which of the 9 schemas should we use, and which components should we activate?**

The agent MUST walk this tree top-down. Each branch has an explicit default. Never ask follow-up questions — see [Fallback Rule](#fallback-rule-兜底规则).

## Visible Tree / 可视决策树

```
root: 对象是人还是规则体系 / Person or rule-system?
│
├── [rule-system] 规则体系 (八字 / 奇门 / 塔罗 / 纳音 / 术数 / 法条引擎)
│   └── schema = executor
│       required = [hard-rules, identity, computation-layer, interpretation-layer, expression-dna]
│       optional = [correction-layer]
│
└── [person] 是人
    │
    ├── corpus-access: 你有多少关于 TA 的私有语料？
    │
    ├── [public-only] 没有，只有公开资料
    │   │
    │   ├── intent = "给我视角 / 思维框架"       → schema = public-mirror
    │   │   required = [hard-rules, identity, mental-models, decision-heuristics,
    │   │               expression-dna, internal-tensions, thought-genealogy,
    │   │               honest-boundaries, correction-layer]
    │   │
    │   ├── intent = "借助一个方法论解决问题"     → schema = public-domain
    │   │   required = [hard-rules, identity, domain-framework, expression-dna,
    │   │               honest-boundaries, correction-layer]
    │   │   optional = [mental-models, computation-layer]
    │   │
    │   └── object = "一整个领域，而不是某一个人" → schema = topic
    │       required = [hard-rules, identity, domain-framework (consensus + divergences),
    │                   expression-dna (neutral voice), honest-boundaries, correction-layer]
    │
    └── [private-corpus] 有（聊天记录 / 邮件 / 访谈 / 亲身接触）
        │
        ├── subject = 你自己                     → schema = self
        │   required = [hard-rules, identity, self-memory, persona-5layer,
        │               expression-dna, honest-boundaries, correction-layer]
        │   optional = [computation-layer]
        │
        ├── relation = 工作关系 (work)
        │   ├── peer / subordinate / collaborator → schema = collaborator
        │   │   required = [hard-rules, identity, work-capability, persona-5layer,
        │   │               expression-dna, honest-boundaries, correction-layer]
        │   │   optional = [computation-layer]
        │   │
        │   └── boss / mentor / senior           → schema = mentor
        │       required = [hard-rules, identity, work-capability, persona-5layer,
        │                   decision-heuristics, mental-models, expression-dna,
        │                   honest-boundaries, correction-layer]
        │       optional = [computation-layer, internal-tensions]
        │
        └── relation = 亲密关系 (intimate)
            ├── family / partner / ex           → schema = loved-one
            │   required = [hard-rules, identity, shared-memories, persona-6layer,
            │               emotional-patterns, expression-dna, honest-boundaries,
            │               correction-layer]
            │
            └── friend (casual, non-romantic)   → schema = friend
                required = [hard-rules, identity, shared-memories (lightweight),
                            persona-5layer, expression-dna, honest-boundaries,
                            correction-layer]
```

## Fallback Rule / 兜底规则

> **Source**: PRD §3.3 "don't interrogate" (borrowed from nuwa-skill).

If the user just says "distill 张三" / "蒸馏 X" without providing any information:

| Missing Signal | Default |
|----------------|---------|
| corpus-access unknown | assume `public-only` UNLESS the user explicitly says "我同事" / "我朋友" / "my colleague" |
| object type unknown | assume `person` |
| relation unknown (when `private-corpus` is implied) | **default = collaborator + all 18 components**, then let Phase 1.5 corpus review narrow down |
| intent unknown (when `public-only`) | **default = public-mirror** (most general public-facing schema) |

The Phase 0.5 agent MUST NOT ask the user clarifying questions. Pick the default, create the skill directory, and let Phase 1.5 Research Review surface any mismatch for the user to correct.

## Tie-breakers / 歧义处理

| Ambiguity | Rule |
|-----------|------|
| 用户既有公开语料又说"我朋友" | `private-corpus` wins → `friend` or `loved-one` |
| 用户说"我老板"但只有公司官网链接 | Treat as `public-only` + `public-mirror` until private corpus arrives |
| 用户说"蒸馏巴菲特投资" | `public-only` + intent=方法论 → `public-domain` (not `public-mirror`) |
| 用户说"蒸馏价值投资" | object is a 领域 → `topic` |
| 用户说"蒸馏八字" | rule-system → `executor` |
| 用户说"蒸馏我老板的选股方法" | `mentor + computation-layer(optional)` |

## Output Schema / Phase 0.5 Agent 产出

The decision agent MUST emit a JSON object conforming to the following shape, written to `<new-skill>/.schema-decision.json`:

```json
{
  "schema": "self | collaborator | mentor | loved-one | friend | public-mirror | public-domain | topic | executor",
  "components": ["hard-rules", "identity", "..."],
  "confidence": 0.0,
  "fallback_to": "collaborator | null",
  "reasoning": "one-paragraph trace of the walk through the tree",
  "user_signals": {
    "object_type": "person | rule-system | topic",
    "corpus_access": "private | public-only | unknown",
    "relation": "self | peer | mentor | intimate | friend | unknown",
    "intent": "perspective | methodology | domain-overview | execution | unknown"
  }
}
```

### Field contracts

- `schema` — MUST be one of the 9 enum values (matches `manifest.schema.json` `schema_type`).
- `components` — MUST be the union of `required` and any declared-optional components the agent chose to activate. All items MUST be from the 18-slug reservation table in [component-contract.md](../../../contracts/component-contract.md).
- `confidence` — float in `[0.0, 1.0]`. `< 0.5` triggers a Phase 1.5 "please correct me" banner. `>= 0.9` when the user gave all three of {object-type, corpus-access, relation/intent}.
- `fallback_to` — set to the fallback schema that would have been picked if `confidence < 0.5`; else `null`. This tells Phase 1.5 what alternative to offer.
- `reasoning` — readable for the user in Phase 1.5 checkpoint.
- `user_signals` — verbatim classification of the user's Phase 0 inputs; `unknown` is allowed.

### Confidence heuristic

```
start at 1.0
- 0.2 if object_type is "unknown"
- 0.2 if corpus_access is "unknown"
- 0.2 if relation/intent is "unknown"
- 0.1 if user corpus contradicts declared relation
floor at 0.1
```

## Examples

```json
// "蒸馏乔布斯"  → public-mirror, confidence 0.6
// "蒸馏张三" (zero info) → collaborator, confidence 0.1, fallback_to public-mirror
// "蒸馏八字"  → executor, confidence 0.95
{
  "schema": "public-mirror", "confidence": 0.6, "fallback_to": null,
  "components": ["hard-rules","identity","mental-models","decision-heuristics",
                 "expression-dna","internal-tensions","thought-genealogy",
                 "honest-boundaries","correction-layer"],
  "user_signals": {"object_type":"person","corpus_access":"public-only",
                   "relation":"unknown","intent":"perspective"}
}
```

## Downstream contract

- Phase 1 consumes `components` to drive `corpus-scout` tasks (one per component).
- Phase 3 consumes `schema` + `components` to assemble the persona skill.
- Phase 4 consumes `schema` via `manifest.schema_type` to route rubric dimensions inside `persona-judge`.
- If the user rejects the decision at Phase 1.5, the agent re-runs this tree with the corrected signals.
