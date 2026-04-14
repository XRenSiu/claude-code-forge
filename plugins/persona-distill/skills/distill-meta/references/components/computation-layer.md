---
component: computation-layer
version: 0.1.0
purpose: Specifies a deterministic Python-backed calculation module whose outputs the persona routes through interpretation-layer — the component that keeps arithmetic, calendar conversions, and indicator math out of LLM hallucination range.
required_for_schemas: [executor]
optional_for_schemas: ["any, experimental only — see scope-limit note below"]
depends_on: []
produces: [interpretation-layer]
llm_consumption: progressive
---

> ### Scope-limit note (v1)
>
> **v1 ships `computation-layer` for the `executor` schema only.** Cross-schema attachment (e.g., `mentor + computation` as in PRD §2.4 Example C, or `public-domain + computation`) is marked `[EXPERIMENTAL]` and is **not** a stable interface. The YAML/manifest plumbing for non-executor attachment may change without a major version bump until at least v2. Schema writers must not rely on it for production persona skills in v1. This scope is set by risk-assessment DEP-06 / SPEC-03 / TEC-03.

## Purpose

`computation-layer` is the **spec-and-interface** half of the executor architecture borrowed from `bazi-skill`: a manifest-level declaration that the persona delegates a specific, deterministic calculation to a Python module rather than attempting it inside the LLM. The LLM-hallucination failure surface for arithmetic, calendar/lunar conversions, technical indicators, drug-interaction table lookups, and rule-table joins is large; this component is the explicit escape hatch.

The component itself is **not** the Python code. It is the YAML contract — `module_name`, `python_packages[]`, `input_schema`, `output_schema`, `function_entrypoint` — that `persona-judge` validates, that `distill-meta` records in `manifest.json`, and that the runtime uses to dispatch a tool call. The actual `.py` file lives under the produced persona skill's `tools/` directory; shipping it is the producer's responsibility, not this component's.

## Extraction Prompt

**Input**: the domain's canonical rule-table / typology source (e.g., the 24-solar-terms table for bazi, a ta-lib indicator list, a formulary interaction table) plus any user-provided computation hints.

**Output**: YAML block with `module_name`, `python_packages`, `input_schema`, `output_schema`, `function_entrypoint`, `determinism_notes`, `hallucination_risk`.

**Prompt** (executable on corpus):

```
You are extracting the computation-layer interface for a persona.

STEP 1 — Identify operations in the domain that LLMs hallucinate. Mark
  a candidate if ANY of:
    - Requires exact arithmetic on >5-digit numbers
    - Requires calendar / lunar / timezone conversion
    - Requires a rule-table join with >50 rows
    - Requires a numerical indicator (moving average, RSI, beta,
      present-value, dosage-adjustment, etc.)
    - Has a known wrong-answer rate >5% when done by LLM in your
      informal tests

STEP 2 — For each surviving candidate, specify:
  - module_name (snake_case)
  - python_packages (stdlib-preferred; if non-stdlib, MUST be declared
    at manifest level as computation_python_packages per
    component-contract §7)
  - input_schema (JSON Schema)
  - output_schema (JSON Schema)
  - function_entrypoint (e.g., "bazi_core.compute_chart")
  - determinism_notes (is the function pure? any I/O?)
  - hallucination_risk (what the LLM would get wrong if it tried this
    without the tool)

STEP 3 — Reject any candidate whose output is not mechanically checkable
  (e.g., "summarize the mood of this text" is NOT a computation-layer
  target — it belongs in expression-dna).

ANTI-EXAMPLES (reject):
  - "compute_vibe": non-deterministic, belongs in persona-5layer.
  - Python module importing `torch` / `pandas` without declaring it in
    manifest.computation_python_packages — breaks persona-judge.
  - Input schema that accepts arbitrary strings with no validation —
    re-opens the hallucination surface.
```

**Few-shot example** (bazi executor):

```yaml
module_name: "bazi_core"
python_packages: ["lunardate"]          # non-stdlib — MUST appear in manifest.computation_python_packages
input_schema:
  type: object
  required: ["birth_datetime_iso", "timezone", "gender"]
  properties:
    birth_datetime_iso: { type: string, format: date-time }
    timezone: { type: string }
    gender: { type: string, enum: [M, F] }
output_schema:
  type: object
  required: ["four_pillars", "day_master", "ten_gods"]
function_entrypoint: "bazi_core.compute_chart"
determinism_notes: "Pure function; no I/O; identical input → identical output."
hallucination_risk: "LLMs get lunar-to-solar conversion wrong ~30% of the time beyond 1950."
```

## Output Format

Generated `components/computation-layer.md` emits:

```markdown
# Computation Layer

> Delegated calculations. The LLM MUST NOT attempt these inline.

## Module: {module_name}
- **Python packages**: [...]  (declared in manifest.computation_python_packages)
- **Entrypoint**: `{function_entrypoint}`
- **Input schema**: (JSON Schema block)
- **Output schema**: (JSON Schema block)
- **Determinism**: pure | has-I/O (describe)
- **Hallucination risk without tool**: ...
- **Interpretation binding**: emits to `interpretation-layer` under key `{module_name}`
```

Required fields: all seven keys above. One module per block; a persona MAY declare multiple modules.

Allowed variability: JSON-Schema drafts 7 or 2020-12; entrypoint may be `module.function` or `module.Class.method`.

## Quality Criteria

1. **Every non-stdlib package is declared at manifest level** in `computation_python_packages` per component-contract §7.
2. **Input and output schemas are complete JSON Schema** — not prose descriptions — enabling `persona-judge` to run mechanical validation.
3. **Determinism is stated explicitly** — pure functions preferred; any I/O (filesystem, network, clock) must be enumerated.
4. **Hallucination risk is stated** — forces the extractor to justify why this operation deserves a tool vs. inline LLM.
5. **Entrypoint resolves** against the declared `module_name` (checked at produce-time).

## Failure Modes

- **Undeclared non-stdlib import**: Python module imports `numpy` / `pandas` / `ta-lib` / `lunardate` but the persona's manifest does not list it in `computation_python_packages`. This breaks `persona-judge` validation and is the top observed failure in the `bazi-skill` lineage.
- **Input schema too loose** (`{ type: object }` with no `required`): lets malformed calls through, re-opens the hallucination surface the component was supposed to close.
- **Non-deterministic function labeled pure**: silently re-introduces LLM-style unreliability.
- **Scope creep**: attaching `computation-layer` to a non-executor schema in v1 without the `[EXPERIMENTAL]` marker (see scope-limit note).
- **`.py` file missing at produce-time**: the spec declares an entrypoint but `tools/{module_name}.py` is absent — producer failed to emit.
- **Computation result never reaches `interpretation-layer`**: raw JSON leaks into final output, breaking voice.

## Borrowed From

- `jinchenma94/bazi-skill` — https://github.com/jinchenma94/bazi-skill — originator of the "Python calculation module + separate interpretation layer" split that this component codifies. `[UNVERIFIED-FROM-README]` README fragment per PRD §5 Tier 4: *"Python 计算层 + Agent 解读层分离 — 抄架构作为 executor schema + computation-layer 组件"*.
- `gaoxin492/bazi-skill` — https://github.com/gaoxin492/bazi-skill — parallel lineage; same computation/interpretation split pattern; cited together in PRD §5 Tier 4. `[UNVERIFIED-FROM-README]`.
- JSON Schema interface choice is re-derived from the general contract-testing pattern, not from a specific skill.
