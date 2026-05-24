# Sub-step 4-F: Fitness rubric generator

**Goal:** turn each `fitness:` entry in `done_when.yaml` into a runnable artifact: a script (for `judge: programmatic`), a rubric markdown file (for `judge: llm-rubric`), or a checklist (for `judge: manual`).

**Background:** see `../fitness-rubric-guide.md` — bad rubrics actively hurt judge accuracy; follow the structured anchors approach. Also note the honest scope: there is no packaged "fitness judge" skill in this marketplace; `llm-rubric` is consumed manually by a fresh Claude session.

---

## Per-judge-kind recipe

### `judge: programmatic`

Emit a script that returns 0 (pass) or nonzero (fail). No LLM involved.

Example for "README quickstart runs zero-modification":

```bash
#!/usr/bin/env bash
# tests/<feature>/fitness/readme_quickstart_runs.sh
# Source criterion: "README quickstart runs zero-modification"
# Source REQ: <REQ-IDs>
set -euo pipefail

SANDBOX=$(mktemp -d)
trap "rm -rf $SANDBOX" EXIT
cd "$SANDBOX"

# Extract fenced code blocks tagged `bash` from README and run them in order
awk '/^```bash$/,/^```$/{ if (!/^```/) print }' "$OLDPWD/README.md" > quickstart.sh
chmod +x quickstart.sh
./quickstart.sh
echo "✓ README quickstart runs without modification"
```

For "API responses match the documented OpenAPI schema":

```bash
#!/usr/bin/env bash
set -euo pipefail
# Use Schemathesis or Dredd
schemathesis run --base-url=http://localhost:3000 openapi.yaml
```

Programmatic fitness checks are strongly preferred whenever possible — they are deterministic, fast, and cheap. Push every criterion you can into this category.

### `judge: llm-rubric`

Emit a markdown rubric file. Path: `tests/<feature>/fitness/<criterion>.rubric.md`.

**How it gets consumed (today):** manually. The user opens a fresh Claude session, pastes the rubric, points at the artifacts, asks for a score. No automation. The rubric file itself must call out this workflow at the top so a human dropping in cold knows what to do.

Use this template (mirrors `../fitness-rubric-guide.md` and is fully self-contained — no external persona library required):

```markdown
# Fitness criterion: <criterion text verbatim from done_when.yaml>

**Source REQ(s):** <REQ-IDs>
**Judge:** llm-rubric (manual workflow — see "How to run" below)
**Threshold:** <verbatim from `score_threshold:`>

> WARNING TO THE JUDGING AGENT:
> Research (JudgeBench) shows naively-written rubrics drop judge accuracy from
> 55.6% to 42.9% — worse than no rubric. Use the structured sub-dimensions
> below verbatim. Do not collapse into "overall impression". Cite passages
> for every score.

## How to run this rubric (no packaged automation today)

1. Open a fresh Claude session (separate from the implementer).
2. Paste this rubric file.
3. Provide paths or contents of the inputs listed below.
4. Ask Claude to score per the sub-dimensions, citing evidence.
5. Compare the aggregated score to the threshold. Record pass/fail in your dev log.

(A `fitness-judge` skill that automates this is potential future work in this plugin.)

## Inputs

The judge examines:
- <path/to/artifact-1>      # e.g. README.md
- <path/to/artifact-2>      # e.g. docs/api-reference.md
- <path/to/artifact-3>      # e.g. tests/<feature>/integration/  (to see how a user would call this)

## Audience archetype

<3-5 lines describing exactly who the judge should simulate. Self-contained.
Do NOT reference a persona-distill persona — those are for a different ecosystem.>

## Rubric

### Sub-dimension 1: <name> (weight 0.X)

Score 1-10 with these anchors:
- **10** — <concrete description of what perfect looks like, with example>
- **7** — <concrete>
- **4** — <concrete>
- **1** — <concrete>

The judge must cite at least one passage from the inputs supporting the score.

### Sub-dimension 2: <name> (weight 0.X)
<...>

### Sub-dimension 3: <name> (weight 0.X)
<...>

(3–7 sub-dimensions; weights sum to 1.0)

## Aggregation

Final score = sum(sub-dimension_score × weight)

## Pass/fail

Pass if:
  - final score >= <threshold>
  - AND no sub-dimension scored below 5

The second clause prevents a strong dimension from masking a weak one.

## Re-run policy

If first pass produces a score within ±0.5 of threshold, run a second time on
the revised artifact and require the score to not decrease before declaring pass.
```

**Pre-fill the audience-archetype block for common cases:**

#### "integration engineer" archetype defaults

```
**Audience archetype: integration engineer**
- 5+ years writing API clients in some language.
- Reads docs once-through, then runs an example.
- Will silently move on if confused.
- Cares about: completeness of error-response examples, idempotency clarity, auth flow precision, exact field types and edge cases.
```

Default sub-dimensions:
1. **completeness** (0.30) — every concept used in the docs is also defined; no dangling references.
2. **runnable_examples** (0.30) — every example block runs as-is in a fresh sandbox.
3. **mental_model_clarity** (0.20) — the docs build the user's mental model in the right order (concepts before APIs that use them).
4. **error_path_coverage** (0.10) — common errors are documented with what they mean and how to recover.
5. **searchability** (0.10) — terminology is consistent; a Ctrl-F on key concepts lands in the right place.

#### "non-technical end user" archetype defaults

```
**Audience archetype: non-technical end user**
- Does not know JSON, status codes, or terminology like "endpoint" or "header".
- Expects task-oriented sections answering "how do I X".
- Cares about: clarity of consequences (will I lose my data?), reassurance on common worries, plain English.
```

Default sub-dimensions:
1. **plain_language** (0.40) — no unexplained jargon; abbreviations spelled out on first use.
2. **task_orientation** (0.30) — sections answer "how do I X" not "what is X".
3. **example_first** (0.20) — a concrete example precedes the formal definition.
4. **emotional_tone** (0.10) — does not blame the user for confusion; failure paths are kind.

#### "oncall SRE" archetype defaults

```
**Audience archetype: oncall SRE**
- Wakes up at 3am to a page; needs to triage in <5 minutes.
- Has the runbook open and the dashboard up.
- Cares about: log/metric clarity, fail-loud rather than silent-degrade, blast-radius docs, runbook completeness.
```

Default sub-dimensions:
1. **observability** (0.30) — every failure mode emits a log/metric with enough info to debug.
2. **fail_loud** (0.25) — silent fallbacks are documented as such; the system does not silently degrade.
3. **runbook_completeness** (0.25) — every alert that can fire has a corresponding runbook section.
4. **blast_radius_documentation** (0.20) — for each component, what depends on it is stated.

### `judge: manual`

Only acceptable for criteria genuinely tacit (visual taste, brand fit, "feels right"). Emit:

```markdown
# Manual checklist: <criterion>

**Source REQ(s):** <REQ-IDs>
**Runner:** human review required
**When to run:** before declaring this REQ done

## Checklist

- [ ] <concrete item — yes/no, no scale>
- [ ] <concrete item>
- [ ] <concrete item>

All items must be checked for pass. If any item is "no", document the gap
and either fix it or formally accept the deviation (with sign-off from the
named approver below).

**Approver:** <role — typically tech lead, design lead, or product owner>
```

Manual checklists must be **concrete yes/no items**, not "rate the design 1-10".

---

## Where the generated files live

```
tests/<feature>/fitness/
  ├── README.md                                  # what's here, how each kind is consumed
  ├── <criterion-1-slug>.<sh|rubric.md|manual-checklist.md>
  ├── <criterion-2-slug>.<...>
  └── ...
```

The `README.md` in the fitness directory must explain:
- programmatic files: run them like any shell/python script.
- rubric files: manual workflow (fresh Claude session) — there is no packaged auto-runner.
- manual files: human runs the checklist; no automation possible.

---

## When to push back

- `fitness:` has > 3 entries → "consider moving some to `behavior:` as programmatic checks; LLM-judge is the layer of last resort".
- A criterion in `fitness:` looks like it should be programmatic (e.g. "all endpoints return JSON" → JSON Schema validator) → suggest moving it to `behavior:`.
- The criterion is genuinely unmeasurable as worded ("the system feels fast") → reject and ask the user to re-state with a measurable surrogate (p95 latency ≤ 200ms).
- The criterion specifies `judge: persona-judge` → reject; that skill is for evaluating distilled persona skills, not arbitrary artifacts. Suggest `judge: llm-rubric` instead.
