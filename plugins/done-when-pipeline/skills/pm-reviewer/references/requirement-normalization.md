# requirement-normalization.md — per-format parsers

`pm-reviewer` accepts requirements in any of six formats. Phase P1 of the skill converts each into a uniform internal representation: a flat list of `{req_id, original_text, bulleted, criticality, category}` records. Below are the parsing rules per source format.

The single output goal: **one testable claim per `req_id`**. Multi-claim source bullets get split.

---

## Format 1: EARS spec.md (preferred)

Detection: file ends `.md` AND contains `WHEN ... THE SYSTEM SHALL` or `UBIQUITOUS:` patterns.

Parser:
- Each `### REQ-NNN` heading begins a new requirement.
- The `req_id` is the heading literal (e.g. `REQ-001`).
- `original_text` is the body of the section, verbatim until the next heading.
- `bulleted` is the SHALL clause restated as a single line: "The system <verb> <object> when <condition>." If the EARS clause is already a single sentence, copy verbatim with light editing for prose flow.
- `criticality` is `critical` if `**Criticality: critical**` appears in the body, else `normal`.
- `category` is `functional` unless the body says `**Category: non_functional**` (or similar).

Example EARS bullet:
```markdown
### REQ-001

WHEN a user submits a cancellation request for an active subscription
THE SYSTEM SHALL transition the subscription state to `cancelled_active`
AND record the cancellation timestamp in UTC ISO-8601 format.

**Criticality: critical**
**Source: user clarified at S2 round 1 Q3 that cancellation honors UTC boundary**
```

Normalizes to:
```yaml
- req_id: REQ-001
  original_text: |
    WHEN a user submits a cancellation request for an active subscription
    THE SYSTEM SHALL transition the subscription state to `cancelled_active`
    AND record the cancellation timestamp in UTC ISO-8601 format.
  bulleted: "Transition subscription state to cancelled_active and record UTC ISO-8601 timestamp on cancellation request."
  criticality: critical
  category: functional
```

Note the split: the example bullet has *two* SHALL operations (`transition` + `record`). Whether to split depends on whether they can fail independently. In this case they always co-occur, so keep as one REQ with both behaviors named. If they could fail independently (different code paths), split into `REQ-001a` and `REQ-001b`.

---

## Format 2: Jira / Linear ticket (exported)

Detection: the file contains `Ticket: <ID>` or `Issue: <ID>` headers, or the URL pattern matches `*.atlassian.net` / `linear.app`.

**Network access is NOT allowed**; the skill does not call the ticketing API. The user must export the ticket to a local markdown file first.

Parser:
- `req_id` is the ticket key (e.g. `BILLING-1234`).
- `original_text` is the ticket's "Description" + "Acceptance Criteria" sections.
- `bulleted` is generated from the Acceptance Criteria items (if present) — one per ticket only if the ticket has a single AC bullet; multiple ACs split into `BILLING-1234.1`, `BILLING-1234.2`, ... .
- `criticality` mapping: Jira "Highest" → critical; "High" → critical; "Medium" → normal; "Low" → normal. Linear: "Urgent" → critical; "High" → critical; others → normal.
- `category` is inferred from labels: a "performance" label → non_functional; "bug" label → leave as functional (bug fixes ARE functional REQs).

Common pitfall: tickets often have prose Descriptions ("As a user I want to..." Stories) without explicit Acceptance Criteria. In that case, the parser falls back to LLM extraction: read the Description, restate as 1-3 bulleted acceptance claims. This is a lossy step — record `bulleted_source: "llm_extracted_from_prose"` so the downstream consumer knows the bullet came from inference, not from the ticket author.

---

## Format 3: PRD markdown (freeform)

Detection: file ends `.md` AND no EARS patterns AND has section headings like "Requirements", "Features", "User Stories", "Acceptance Criteria".

Parser:
- Walk the file's heading structure.
- For each section that contains requirements (heuristic: includes verbs like "user can / should / must" or "system should / must"), extract bullets.
- Each bullet becomes a candidate REQ.
- `req_id` is auto-generated `PRD-001`, `PRD-002`, ... in document order.
- `original_text` is the bullet verbatim with parent section heading as context.
- `bulleted` is the bullet restated as a single testable claim. Multi-clause bullets ("user can cancel AND see refund preview") → split into multiple REQ-IDs.
- `criticality`: no native PRD field; default to `normal` unless `--severity-marks` overrides. PRDs sometimes use bold or "MUST" / "SHOULD" / "MAY" semantics (RFC 2119) — `MUST` → critical, others → normal.
- `category`: heuristic by section name ("Performance" → non_functional, etc.).

Example PRD section:
```markdown
## Cancellation

Users should be able to cancel their subscription. The cancellation must be
immediate. After cancelling, the user should see a confirmation modal with
the date of access expiration.
```

Normalizes to:
```yaml
- req_id: PRD-001
  original_text: "Users should be able to cancel their subscription."
  bulleted: "User can cancel an active subscription."
  criticality: normal
  category: functional
- req_id: PRD-002
  original_text: "The cancellation must be immediate."
  bulleted: "Cancellation takes effect immediately (no delay)."
  criticality: critical   # MUST keyword
  category: functional
- req_id: PRD-003
  original_text: "After cancelling, the user should see a confirmation modal with the date of access expiration."
  bulleted: "After cancellation, a confirmation modal displays the access expiration date."
  criticality: normal
  category: functional
```

---

## Format 4: GitHub issue (exported)

Detection: file is a GitHub-style issue export OR the URL matches `github.com/*/issues/*`.

Like Jira/Linear: no network access; user exports first.

Parser:
- `req_id` is the issue number prefixed: `ISSUE-42`.
- `original_text` is the issue body.
- `bulleted` is extracted from "Acceptance Criteria" section if present, else LLM-extracted from prose.
- `criticality` from labels: `bug` → critical (bugs by definition block); `enhancement` → normal; `discussion` → skip (not a REQ).
- Comments are ignored unless explicitly tagged "acceptance update" or similar.

---

## Format 5: PR description

Detection: `--requirements-source` resolves to a git ref AND the ref has a commit message body OR `--pr-description=<path>` is explicit.

Parser:
- `req_id` is auto-generated `PR-DESC-001`, ... in description order.
- `original_text` is each bullet of the PR description's "Summary" or "What this PR does" section.
- Most other fields are heuristic; PR descriptions are typically informal.

This format is the least reliable — PR descriptions often paraphrase intent rather than enumerate testable claims. Use as a last resort; encourage the user to point at a proper PRD or EARS spec instead.

---

## Format 6: User-supplied requirements YAML

Detection: file ends `.yaml` AND has a top-level key `requirements:` with list value.

Parser:
- Direct mapping. The user has already done the normalization.

Schema:
```yaml
requirements:
  - req_id: BILLING-1234
    original_text: "..."
    bulleted: "..."
    criticality: critical | normal
    category: functional | non_functional
```

This is the escape hatch for cases where the source format isn't recognized. The user normalizes manually, hands the YAML to pm-reviewer.

---

## Cross-format rules

1. **Always preserve the original ID if the source has one.** Mintingauto-IDs (PRD-001, ISSUE-42) only when the source doesn't.
2. **Always preserve `original_text` verbatim.** The `bulleted:` form is for the judgment phase; `original_text:` is for audit ("this is what the requirement actually said").
3. **Splitting > merging.** When in doubt, split a multi-claim requirement into multiple REQ-IDs. A `partially_compliant` verdict on a single REQ that contained two claims (one satisfied, one not) loses information — better to have `fully_compliant` on one and `not_compliant` on the other.
4. **Mark `bulleted_source: "llm_extracted_from_prose"`** whenever the bullet came from LLM inference rather than direct source quoting. Lets downstream consumers (`/meta-judge`, `/acceptance-fleet`, human reviewers) discount confidence on those REQs.
5. **Refuse unparseable input.** If the source has zero recognizable requirements, refuse with the recognized-format list. Do not invent requirements from thin air to make the source "parseable".

---

## Worked example: PRD → normalized output

Input (`requirements.md`):
```markdown
# Subscription cancellation v2

## Goals
Let users cancel subscriptions cleanly.

## Requirements

The system must allow users to cancel their subscription from the account page.
The cancellation should be immediate — billing stops with the next cycle.

Users with active trials must be able to cancel and retain their remaining trial days.

Performance: cancellation endpoint must respond within 200ms p99.
```

Output (normalized):
```yaml
- req_id: PRD-001
  original_text: "The system must allow users to cancel their subscription from the account page."
  bulleted: "User can cancel a subscription from the account page UI."
  criticality: critical   # MUST keyword
  category: functional
  bulleted_source: "direct_quote"

- req_id: PRD-002
  original_text: "The cancellation should be immediate — billing stops with the next cycle."
  bulleted: "Cancellation takes effect immediately; no further billing cycles after cancellation."
  criticality: normal
  category: functional
  bulleted_source: "direct_quote"

- req_id: PRD-003
  original_text: "Users with active trials must be able to cancel and retain their remaining trial days."
  bulleted: "Cancellation during trial preserves remaining trial-period access (does not expire access immediately)."
  criticality: critical   # MUST
  category: functional
  bulleted_source: "direct_quote"

- req_id: PRD-004
  original_text: "Performance: cancellation endpoint must respond within 200ms p99."
  bulleted: "Cancellation endpoint responds in <200ms p99 under realistic load."
  criticality: normal
  category: non_functional
  bulleted_source: "direct_quote"
```

REQ-004 is non_functional — pm-reviewer will likely route it to `requires_human_verification` because performance under load is not judgeable from static code reading alone (delegate to `/qa-reviewer` perf layer if integration tests measure it; otherwise human must run load test).
