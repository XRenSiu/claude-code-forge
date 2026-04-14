<!--
  template: reference-file-template
  owner: distill-meta Phase 5 (render step 3 in references/output-spec.md §4 — "copy-with-inline components/**")
  produces: {persona-skill}/components/{COMPONENT_SLUG}.md for each slug in manifest.components_used
  conforms_to:
    - contracts/component-contract.md §4 (generated-file discipline)
    - references/output-spec.md §2.3 (copy-with-inlining rule)

  PLACEHOLDER GUIDE — distill-meta fills each {ALL_CAPS_SNAKE} token when copying a component
  definition from distill-meta/references/components/<slug>.md into the persona skill.

  | Placeholder         | Source                                                        | Notes |
  | ------------------- | ------------------------------------------------------------- | ----- |
  | {COMPONENT_SLUG}    | matches filename stem; one of the 18 reserved slugs           | required |
  | {COMPONENT_VERSION} | SemVer of the component definition at render time             | required; tracked in manifest.components_versions for consumer validation |
  | {PURPOSE}           | one-line string copied verbatim from the definition's frontmatter | required |
  | {PRODUCED_FOR}      | host persona's manifest.fingerprint (64-hex SHA-256)          | required; lets auditors verify this file was generated for THIS knowledge snapshot |
  | {OUTPUT_CONTENT}    | the concrete filled-in body produced by the Extraction Prompt | required; renders under "## Output Format" as finished content, NOT the format spec |
  | {EXAMPLES}          | 0-3 worked examples (optional; pass empty string if none)     | optional |

  DROPPED SECTIONS (per component-contract.md §4):
  - ## Extraction Prompt     (generation-time only, not runtime)
  - ## Failure Modes         (generation-time only)
  - ## Borrowed From         (citation belongs in distill-meta/references/, not here)
  - ## Quality Criteria      (judged externally by persona-judge; not needed at runtime)

  KEPT SECTIONS:
  - frontmatter (with produced_for injected)
  - ## Purpose
  - ## Output Format (as concrete content, not schema)
  - ## Examples (if present)
  - ## Interaction Notes (if present in the source)

  SELF-CONTAINED RULE: this file MUST NOT link back to distill-meta or to sibling persona
  skills. Borrow-copy, don't link. Any `../` path is a render bug.
-->

---
component: {COMPONENT_SLUG}
version: {COMPONENT_VERSION}
purpose: {PURPOSE}
produced_for: {PRODUCED_FOR}
---

# Component: {COMPONENT_SLUG}

## Purpose

{PURPOSE}

This component travels inside the persona skill as a self-contained copy. The
definition that produced it lives in `distill-meta/references/components/{COMPONENT_SLUG}.md`
(not readable from here — this file is the runtime view).

## Output Format

The content below is the concrete, populated output of this component for the host
persona. It is NOT a format schema — it is the finished artefact consumed at runtime.

{OUTPUT_CONTENT}

## Examples

{EXAMPLES}

<!--
  RENDER NOTE: if {EXAMPLES} is empty, distill-meta should either (a) leave the heading
  with the literal text "_No examples captured for this persona._" or (b) omit the
  Examples section entirely. Choose (a) for consistency across generated skills.
-->
