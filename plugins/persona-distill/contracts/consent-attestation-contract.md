---
name: consent-attestation-contract
description: Authoritative format for consent-attestation.md — the file that a persona skill MUST carry at its root when identity.subject_type = real-person. Closes integration.md §6.2 S2.
version: 1.0.0
---

# Consent Attestation Contract

> Distilling a real living person without their consent is a policy red line
> (`hard-rules` component). This contract adds structural **friction** to that
> red line: skills with `identity.subject_type = "real-person"` MUST ship a
> `consent-attestation.md` at the skill root, and Phase 0 of `distill-meta`
> blocks until one is present. This does NOT constitute enforcement — a
> motivated attacker can still declare `fictional` — but it removes the
> "accidental non-consent" failure mode and creates an audit trail.

## 1. When attestation is REQUIRED

| `identity.subject_type` | Attestation required? | Rationale |
|---|---|---|
| `real-person` | **YES** | The whole point. |
| `composite` | YES (per contributing person) | Composite = multiple reals; attest for each. |
| `fictional` | NO | Literary / fictional figures with no living subject. |
| `rule-system` | NO | 八字 / 奇门 / 塔罗 — not a person. |
| `topic` | NO | Domain, not a person. |

If `subject_type` ∈ {`real-person`, `composite`}, the Phase 0 agent checks
for `consent-attestation.md` at the persona-skill root BEFORE any corpus is
collected. Missing or malformed file → HALT with friendly error.

## 2. File location

```
{persona-skill-root}/consent-attestation.md
```

Sits at root alongside `conflicts.md`, `validation-report.md`. Not inside
`components/` (runtime-consulted) or `knowledge/` (corpus). The migrator
never rewrites this file; it's user-owned.

## 3. Required structure

```markdown
---
attestation_version: 1.0.0
subject_type: real-person | composite
subjects:
  - name: <full name as given>
    consent_obtained: true
    consent_method: <written | verbal-recorded | implicit-public-figure | self>
    consent_date: <YYYY-MM-DD>
    consent_evidence: <file path inside knowledge/ OR external URL OR "see §5">
    corpus_scope: <one-sentence description of what the subject agreed to>
    revocation_contact: <email or other reachable channel>
relationship_to_distiller: <self | family | colleague | friend | public>
attestation_date: <YYYY-MM-DD>
attester_handle: <user handle or @self>
---

# Consent Attestation for {persona-slug}

## Scope

<free-form paragraph, ≤ 500 chars: what the subject agreed to have distilled>

## What is EXCLUDED by this attestation

<≥ 1 explicit exclusion; "nothing excluded" is rejected by the Phase 0 gate>

## Revocation policy

The subject may revoke consent at any time by contacting {revocation_contact}.
On revocation, the skill maintainer will: (a) stop all further generation
runs; (b) either regenerate with reduced corpus or delete the skill entirely;
(c) record the revocation in this file under `## Revocation log` (append-only).

## Revocation log

<!-- Append-only. Format per entry:
- date: YYYY-MM-DD
- scope: <what was revoked>
- action_taken: <regenerate | delete | partial-removal>
-->
```

## 4. Phase 0 gate behavior

When `distill-meta` Phase 0 detects `subject_type ∈ {real-person, composite}`:

1. Check `{persona-skill-root}/consent-attestation.md` exists.
2. Parse frontmatter. All required fields present?
3. For each `subjects[]` entry: `consent_obtained: true` AND `consent_method`
   is one of the allowed enum AND `consent_date` parses as ISO date.
4. `## What is EXCLUDED` section body is non-empty.
5. If ANY check fails → HALT with error pointing to this contract.

On pass, Phase 0 emits:
- `manifest.consent_attestation.present: true`
- `manifest.consent_attestation.method: <consent_method of primary subject>`
- `manifest.consent_attestation.date: <consent_date>`
- `manifest.consent_attestation.hash: <SHA-256 of consent-attestation.md>`

These fields are readable by downstream skills (router / judge / debate) —
skills without consent attestation should not be auto-selected for broad
distribution contexts.

## 5. `consent_method` enum

| Value | Means |
|---|---|
| `written` | Signed document exists; path in `consent_evidence` or stored separately. |
| `verbal-recorded` | Audio/video recording of consent; path in `consent_evidence`. |
| `implicit-public-figure` | Public figure in their public capacity (essays, talks, tweets). Valid ONLY for strictly-public corpus — `corpus_access_declared: public-only` in manifest (see S7). Private chats with a public figure DO NOT qualify. |
| `self` | Distiller is distilling themselves (`schema_type: self`). Auto-valid. |

Any other value → Phase 0 rejects.

## 6. What this contract does NOT do

- **Does not verify signatures.** A PDF can be forged; we take the attester's
  word. Lying in this file is a legal / ethical issue, not a technical one.
- **Does not prevent a bad actor from declaring `fictional`** to bypass. The
  cross-check against corpus proper-nouns (S7's `corpus_access_declared`
  + Phase 1.5 warning) adds a second layer, but neither is enforcement.
- **Does not handle consent for deceased subjects.** For public figures whose
  estates control rights, declare `implicit-public-figure` if all corpus is
  public; otherwise the distiller is on their own — this is out of scope.

## 7. Versioning

- `attestation_version` in the file's frontmatter bumps when THIS contract
  changes. Breaking changes bump major; field additions bump minor.
- `distill-meta` Phase 0 reads the attestation version; refuses attestations
  with a major version it does not support.

## 8. Example (self schema, auto-valid)

```markdown
---
attestation_version: 1.0.0
subject_type: real-person
subjects:
  - name: Xiao Ming
    consent_obtained: true
    consent_method: self
    consent_date: 2026-04-15
    consent_evidence: self
    corpus_scope: "My own journals, iMessage history with myself, and emails I authored."
    revocation_contact: xm@example.com
relationship_to_distiller: self
attestation_date: 2026-04-15
attester_handle: "@xm"
---

# Consent Attestation for xm-self-skill

## Scope

I am distilling myself from my own writings. I consent to all usage.

## What is EXCLUDED by this attestation

- Conversations where counterparties had reasonable expectation of privacy
  (these were removed from corpus pre-generation, see `knowledge/` audit).
- Medical records; financial account details.

## Revocation policy

I can delete this skill at any time from my own machine.

## Revocation log

<!-- none yet -->
```

## 9. Change log

- 1.0.0 — Initial contract. Phase 0 gate. Four `consent_method` enum values.
