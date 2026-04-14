# Recommendation Output Template

**Owner**: `persona-router`
**Referenced from**: `SKILL.md` §"Step 4 — Emit 1-3 Recommendations"
**Scoring source**: `references/matching.md`
**Field source**: `contracts/manifest.schema.json`

Router renders its final answer by filling in the template below. Placeholders are in
`{ALL_CAPS}`. All field references (e.g. `identity.name`) are from
`contracts/manifest.schema.json`.

---

## Template

```markdown
## 建议调用 / Recommended Personas

{FOR EACH RECOMMENDATION}
### {RANK}. {PERSONA_NAME} ({SCHEMA_TYPE})
- **Why**: {MATCH_REASON} (matched on: {MATCHED_DIMENSIONS})
- **Score**: {SCORE}/1.0 (schema:{SCHEMA_SCORE}, domain:{DOMAIN_SCORE}, components:{COMP_SCORE}, density:{DENSITY}, primary:{PRIMARY})
- **Strong for**: {DOMAINS_LIST}
- **Invoke**: {INVOCATION_HINT}
{END FOR}

{IF EMPTY}
No suitable persona found. Suggestions:
- Run `/distill-meta` to create one
- Review discovered skills: {DISCOVERED_LIST}
{END IF}
```

---

## Placeholder Reference

| Placeholder | Source | Notes |
|-------------|--------|-------|
| `{RANK}` | router | `1`..`top_k` |
| `{PERSONA_NAME}` | `identity.display_name` ?? `identity.name` | Prefer display name. |
| `{SCHEMA_TYPE}` | `schema_type` | One of 9 enum values. |
| `{MATCH_REASON}` | router | One sentence, <= 25 words. |
| `{MATCHED_DIMENSIONS}` | router | Comma-separated subset of `{schema, domain, components, density, primary}`; only those contributing materially. |
| `{SCORE}` | `references/matching.md` §1 | Rounded to 2 decimals. |
| `{SCHEMA_SCORE}` ... `{PRIMARY}` | `references/matching.md` §2-§6 | Rounded to 2 decimals. |
| `{DOMAINS_LIST}` | `identity.domains` | Comma-separated, max 5 items. |
| `{INVOCATION_HINT}` | router | E.g. backtick-quoted trigger from `triggers[0]`. |
| `{DISCOVERED_LIST}` | scanner | Only rendered in empty state; comma-separated `identity.name` values. |

### Conditional blocks

- **`{FOR EACH RECOMMENDATION}` ... `{END FOR}`**: iterate recommendations (up to `top_k`,
  default 3). If zero recommendations survive the threshold (`references/matching.md` §7),
  skip this block entirely.
- **`{IF EMPTY}` ... `{END IF}`**: render iff the recommendations list is empty.

### Warning suffix (optional)

When a rendered persona has `unvalidated: true` (contract §`unvalidated`), append a line
immediately after its block:

```
> ⚠ Unvalidated: this skill shipped before dog-food validation. Cross-check answers.
```

---

## Rendered Example

````markdown
## 建议调用 / Recommended Personas

### 1. Mentor Li Si (mentor)
- **Why**: 直接匹配战略取舍类问题，激活了 decision-heuristics 与 mental-models (matched on: schema, components, domain)
- **Score**: 0.65/1.0 (schema:0.90, domain:0.33, components:0.67, density:0.72, primary:0.80)
- **Strong for**: career, engineering-leadership, org-design
- **Invoke**: `ask mentor-lisi`

### 2. Steve Jobs Mirror (public-mirror)
- **Why**: 产品判断 + 取舍框架在此问题类别上权重最高 (matched on: schema, components)
- **Score**: 0.58/1.0 (schema:1.00, domain:0.20, components:0.67, density:0.60, primary:0.50)
- **Strong for**: product, taste, trade-off
- **Invoke**: `ask steve-jobs-mirror`

> ⚠ Unvalidated: this skill shipped before dog-food validation. Cross-check answers.

### 3. Colleague Zhang San (collaborator)
- **Why**: 近期做过类似 API 设计决策，work-capability 覆盖 (matched on: domain, components)
- **Score**: 0.47/1.0 (schema:0.60, domain:0.50, components:0.33, density:0.55, primary:0.70)
- **Strong for**: backend, api-design, team-ops
- **Invoke**: `ask colleague-zhangsan`

---

你挑一个或多个触发即可。需要直接进入辩论？→ `persona-debate`
````

### Empty-state rendered example

````markdown
## 建议调用 / Recommended Personas

No suitable persona found. Suggestions:
- Run `/distill-meta` to create one
- Review discovered skills: friend-alice, topic-paxos-notes, executor-shell-helper
````

---

## Progressive Disclosure

- Scan mechanism: `references/manifest-scanner.md`.
- Scoring formula: `references/matching.md`.
- Input contract: `contracts/manifest.schema.json`.
