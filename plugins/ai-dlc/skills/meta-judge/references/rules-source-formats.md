# rules-source-formats.md — pluggable rules ingestion

The `--rules` argument tells meta-judge what conditions to check the findings against. Five formats are supported. Schema is permissive — unknown fields are warned, not rejected.

## Internal rule representation

Regardless of source format, meta-judge parses every rule into:

```python
class Rule:
    condition: str                  # the rule text, e.g. "any P0 finding blocks merge"
    severity: str                   # blocking | conditional | informational | needs-human
    applies_to: str                 # any-reviewer | code-reviewer | qa-reviewer | ...
    parsed_predicate: dict          # parsed condition (e.g. {field: severity, op: >=, value: P0})
```

The `parsed_predicate` is what M4 (classify) actually evaluates against. If parsing fails, `parsed_predicate` is `null` and the rule is treated as `cannot_evaluate` → contributes to NEEDS_HUMAN.

---

## Format 1: `done_when.yaml` (post v1.0)

Detection: file is named `done_when.yaml` OR has top-level keys `feature:` + `behavior:`.

Read the top-level `rules:` block. Each entry is either:
- A bare string: `"any P0 finding blocks merge"` — parsed via regex against canonical patterns (see "Recognized conditions" below).
- A mapping: `{rule: "...", severity: blocking, applies_to: any-reviewer}` — direct map to internal Rule.

Example:
```yaml
rules:
  - "any P0 finding blocks merge"
  - "mutation_kill_rate >= 0.7"
  - rule: "all critical REQs must be fully_compliant or have explicit human OK"
    severity: blocking
    applies_to: pm-reviewer
```

If the `done_when.yaml` has a `behavior.thresholds:` block, those thresholds are AUTOMATICALLY added as rules (e.g. `mutation_kill_rate: ">= 0.7"` becomes a rule). The user does not need to duplicate them in `rules:`. This is the v1.0+ schema's main convenience over manual rule transcription.

---

## Format 2: CLAUDE.md

Detection: file is named `CLAUDE.md` OR contains the marker text `# Claude Code` or `# Project rules`.

Walk the file. Bullets that look like rules (start with imperative verb: "block", "require", "fail", "warn", "always", "never") get extracted. Bullets under headings like "Code review rules" / "Merge gates" / "Quality gates" are prioritized.

Example:
```markdown
## Merge gates

- Block merge on any P0 security finding.
- Require unit_coverage >= 0.85 for new modules.
- Warn if files in `src/legacy/` are modified without an `@migration-allowed` annotation.
```

Parsed as:
```yaml
- {condition: "Block merge on any P0 security finding", severity: blocking, applies_to: code-reviewer}
- {condition: "Require unit_coverage >= 0.85 for new modules", severity: blocking, applies_to: qa-reviewer}
- {condition: "Warn if files in src/legacy/ are modified without...", severity: informational, applies_to: code-reviewer}
```

CLAUDE.md often has rules scattered with other context (project description, examples). The parser is heuristic — false positives go into `caveats.heuristic_extracted_rules:` so the user can verify.

---

## Format 3: REVIEW.md

Same parser as CLAUDE.md, but the heuristic threshold for "this looks like a rule" is lower because the whole file is presumed to be rules. Use REVIEW.md when a project has dedicated review policy that's too verbose for CLAUDE.md.

---

## Format 4: Custom YAML

Detection: file ends `.yaml` or `.yml` AND has top-level `rules:` key.

```yaml
rules:
  - rule: "..."
    severity: blocking
    applies_to: any-reviewer
  - rule: "..."
    severity: conditional
    applies_to: qa-reviewer
    notes: "this rule is lenient during the migration period"
```

Custom YAML is the most explicit format and is the recommended choice when meta-judge is used outside `/acceptance-fleet`.

---

## Format 5: Plain text bullet list

Detection: file ends `.txt` OR `.md` with no recognized structure AND has bullets.

Each line starting with `-` or `*` is treated as a candidate rule. Parsed via the same heuristic as CLAUDE.md but with lower confidence — typically most rules become `severity: informational` unless they contain imperative blocking keywords ("block", "fail", "must not").

---

## Recognized conditions (regex patterns for bare-string rules)

When a rule is a bare string (formats 1, 2, 3, 5), it's parsed against these regex patterns to extract `parsed_predicate`:

| Pattern | Example | Predicate |
|---|---|---|
| `any (P[0-3]) finding\s+(blocks merge\|warns)` | "any P0 finding blocks merge" | `{field: severity, op: ==, value: P0, action: block}` |
| `(\w+) (>=\|<=\|>\|<) ([\d.]+)` | "mutation_kill_rate >= 0.7" | `{field: mutation_kill_rate, op: >=, value: 0.7}` |
| `qa-reviewer decision\s+(?:must be\|cannot be)\s+(\w+)` | "qa-reviewer decision must be GO or CONDITIONAL" | `{field: qa_decision, op: in, value: [GO, CONDITIONAL]}` |
| `all critical REQs must\s+(.+)` | "all critical REQs must be fully_compliant" | `{field: pm_critical_verdict, op: ==, value: fully_compliant}` |
| `gaming_risk_score\s+(>=\|<=\|>\|<)\s+(\d+)` | "gaming_risk_score < 7" | `{field: gaming_risk_score, op: <, value: 7}` |
| `(?:require\|need) (\w+)` | "require explicit human OK on UI REQs" | `{field: requires_human_ok, op: ==, value: true}` (low-confidence parse) |

Rules that don't match any pattern get `parsed_predicate: null` and `cannot_evaluate: pattern_unrecognized`. They're surfaced in the rules-evaluation output as NEEDS_HUMAN domain.

---

## Combining multiple rules sources

`--rules` can be a single path OR a comma-separated list of paths. Each is parsed independently, then merged. Conflicts (same condition with different severities) are resolved by taking the *stricter* severity (`blocking` > `conditional` > `informational` > `needs-human` for this ordering of "how much it blocks merging").

---

## Default rules (fallback)

When `--rules` yields zero parseable rules, meta-judge uses the default rule list:

```yaml
rules:
  - "any P0 finding blocks merge"
  - "any P1 from pm-reviewer with verdict: not_compliant blocks merge"
  - "qa-reviewer decision: NO-GO blocks merge"
  - "spec-gaming-detector.gaming_risk_score >= 7 blocks merge"
  - "pm-reviewer requires_human_verification on critical REQ → NEEDS_HUMAN"
```

These are deliberately conservative. Better to over-block than under-block in default mode.
