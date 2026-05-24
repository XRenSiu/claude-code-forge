# Feature: <feature-slug>

> Authoritative EARS specification. Every REQ has a stable ID (never renumber).
> Every clause traces back to a clarify answer via `source:`.
> Keep REQ bodies tight (≤ ~25 words per SHALL clause). Long term definitions
> go in `## Glossary` below, not inline in the REQ body.

## REQ-001 (<EARS type: Ubiquitous | Event-driven | State-driven | Unwanted | Optional>)
<full EARS sentence — no [?] markers, no fuzz>
source: <where the resolution came from — typically "S2 round N QM" or "original brief">

## REQ-002 (<EARS type>)
<full EARS sentence>

### Constraint:
<additional always-applies condition narrowing the SHALL clause — optional>

### Extension:
<additional case this REQ also covers — optional>

source: <...>

## REQ-NNN (<EARS type>)
<...>
source: <...>

## Glossary
<only include if any clarify round produced a precisely-defined domain term>

- **<term>** — <precise definition>. (source: S2 round N QM)
- **<term>** — <precise definition>. (source: S2 round N QM)

---

Sub-clause grammar (REQ blocks):

- `### Constraint:` — narrows the SHALL action (always-applies precondition).
- `### Extension:` — broadens the REQ to cover an additional case symmetric to the primary one.
- No other `### …:` labels are sanctioned. Anything that needs more structure than
  Constraint/Extension should be a separate REQ with its own ID.
