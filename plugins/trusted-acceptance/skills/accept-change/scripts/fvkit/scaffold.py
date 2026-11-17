"""`fv init` and `fv vendor`: project assets for the two entrances, and a self-contained copy.

Layout written by init (names are a convention, not a requirement):
  <dir>/requirements.md    A1/B1: what is promised, questions, what is NOT promised
  <dir>/contract.yaml      A2/B1: authoritative rules (observables, assumptions, properties)
  <dir>/model.yaml         A3/B3: executable state machine + refinement mapping + mutants
  <dir>/model-scope.md     scope, bounds, exclusions (what this model does not cover)
  <dir>/source-map.yaml    B2/C5: model action <-> code, anchors, protected paths
  <dir>/decisions.md       triage and rule-change decisions (append-only)
  <dir>/counterexamples/   recorded counterexamples and their replays
"""
import json
import shutil
from pathlib import Path

from .values import require

REQUIREMENTS = """# {name}: requirements

> Entrance {entrance_label}. Rules come from the requirement, never from what the code happens to do.

## Promises (each must become a property in contract.yaml)

| id | given | when | must / must not | source |
|----|-------|------|-----------------|--------|
| R1 | | | | |

## Environment assumptions (become `assumptions` — never hide them in the model)

- e.g. "the conditional UPDATE is atomic in the database"

## Open questions (block G0 / G2 until answered)

- What exactly counts as success? timeout? retry? cancellation? duplicate request?

## Out of scope (stated, not silently dropped)

-
{code_first}"""

CODE_FIRST = """
## Code-first: facts vs. requirements (B1/B2)

| behaviour the code has today | is it required? (yes / no / unknown) | evidence |
|------------------------------|--------------------------------------|----------|
| | | |

Existing behaviour is a fact, not a rule. A rule that only exists because "the code does it"
would legalise the bug you are looking for.
"""

CONTRACT = """# fv-contract: the authoritative rules. Changing a property needs an approval
# (G2 lock in AI-DLC, or `fv approve`); `fv diff-contract` flags any weakening.
schema_version: 1
kind: fv-contract
id: {name}
version: 1
title: "{name}"
parameters: [LIMIT, CLIENTS]          # constants every model must define
observables:                           # the vocabulary the rules are written in
  granted: {{type: int, domain: "range(0, 4)", description: "how many grants exist"}}
  status: {{type: map, description: "per-client status: idle / waiting / granted / refused"}}
assumptions:
  - {{id: A1, text: "replace: e.g. the database update is atomic"}}
properties:
  - {{id: WithinLimit, kind: invariant, expr: "granted <= LIMIT", source: R1, text: "never grant more than LIMIT"}}
  - {{id: GrantedNeverDecreases, kind: transition, expr: "post.granted >= pre.granted"}}
  - {{id: LimitReachable, kind: reachable, expr: "granted == LIMIT"}}
  - id: EveryRequestAnswered
    kind: leads_to
    forall: {{c: CLIENTS}}
    from: "status[c] == 'waiting'"
    to: "status[c] in ('granted', 'refused')"
"""

MODEL = """# fv-model: a small, exact state machine. Actions are the atomic steps the REAL code takes
# (one transaction = one action). Observables map model state onto the contract vocabulary.
schema_version: 1
kind: fv-model
id: {name}-design
contract: contract.yaml
constants: {{LIMIT: 1, CLIENTS: ["c1", "c2"]}}
variables:
  granted: {{init: "0"}}
  status: {{init: "{{c: 'idle' for c in CLIENTS}}"}}
actions:
  request:
    params: {{c: CLIENTS}}
    guard: "status[c] == 'idle'"
    update: {{status: "update(status, c, 'waiting')"}}
  grant:                                 # atomic check-and-grant
    params: {{c: CLIENTS}}
    guard: "status[c] == 'waiting' and granted < LIMIT"
    update: {{granted: "granted + 1", status: "update(status, c, 'granted')"}}
  refuse:
    params: {{c: CLIENTS}}
    guard: "status[c] == 'waiting' and granted >= LIMIT"
    update: {{status: "update(status, c, 'refused')"}}
fairness:
  - {{action: grant, kind: weak, per_params: true}}
  - {{action: refuse, kind: weak, per_params: true}}
terminal: "all(status[c] != 'waiting' for c in CLIENTS)"
observables:
  granted: "granted"
  status: "status"
symmetry: [CLIENTS]
mutants:                                 # G1: prove the rules catch the defects they exist for
  - id: check-then-act
    description: "grant checks a stale value instead of checking at commit"
    edits:
      - {{op: set_guard, action: grant, expr: "status[c] == 'waiting'"}}
    expect_killed_by: [WithinLimit]
"""

SCOPE = """# {name}: model scope

- Constants checked: LIMIT=1, CLIENTS={{c1, c2}} (small-scope hypothesis; say why it is enough)
- Exhaustive or bounded: (fill from the receipt: states, exhaustive_depth)
- Not modelled (and therefore not claimed): payments, refunds, crash recovery, ...
- Atomicity claims that must hold in the code (cross-check with source-map.yaml):
"""

SOURCE_MAP = """# fv-source-map: every model action is tied to code by a VERBATIM anchor. After a review run
#   fv source-map sync --map source-map.yaml --model model.yaml --by <name> --reason <why>
# which writes source-map.lock.json (file digests, model digest, reviewed commit).
schema_version: 1
kind: fv-source-map
model: model.yaml
actions:
  grant:
    atomicity: "replace: e.g. single UPDATE ... WHERE granted < limit RETURNING"
    locations:
      - {{path: "src/replace_me.py", symbol: "grant", anchor: "replace with verbatim code text"}}
  request:
    locations:
      - {{path: "src/replace_me.py", symbol: "request", anchor: "replace with verbatim code text"}}
  refuse:
    locations:
      - {{path: "src/replace_me.py", symbol: "refuse", anchor: "replace with verbatim code text"}}
environment_actions: {{}}
protected_paths: ["src/replace_me.py"]
"""

DECISIONS = """# {name}: decisions (append-only)

| at | counterexample / change | class (requirement_gap / model_infidelity / design_defect / implementation_defect / checker_defect) | decision | by |
|----|-------------------------|-----|----------|----|
"""


def init(directory, name, entrance):
    require(entrance in ("spec-first", "code-first"), "entrance must be spec-first|code-first")
    d = Path(directory)
    require(not d.exists() or not any(d.iterdir()), "target directory exists and is not empty: %s" % d)
    (d / "counterexamples").mkdir(parents=True, exist_ok=True)
    label = "A (spec first: requirements -> rules -> model -> check -> code)" if entrance == "spec-first" else \
        "B (code first: rules from requirements, behaviour map from code -> model -> counterexample -> replay)"
    files = {
        "requirements.md": REQUIREMENTS.format(name=name, entrance_label=label, code_first=CODE_FIRST if entrance == "code-first" else ""),
        "contract.yaml": CONTRACT.format(name=name),
        "model.yaml": MODEL.format(name=name),
        "model-scope.md": SCOPE.format(name=name),
        "source-map.yaml": SOURCE_MAP.format(name=name),
        "decisions.md": DECISIONS.format(name=name),
    }
    for fname, text in files.items():
        (d / fname).write_text(text, encoding="utf-8")
    (d / "counterexamples" / ".keep").write_text("", encoding="utf-8")
    return sorted(str(d / f) for f in files)


def vendor(target):
    here = Path(__file__).resolve().parent
    t = Path(target)
    require(not t.exists() or not any(t.iterdir()), "vendor target must be new or empty: %s" % t)
    (t / "fvkit").mkdir(parents=True, exist_ok=True)
    for p in sorted(here.glob("*.py")):
        shutil.copy2(p, t / "fvkit" / p.name)
    shutil.copy2(here.parent / "fv.py", t / "fv.py")
    from .receipt import engine_identity
    (t / "VENDORED.json").write_text(json.dumps({"engine": engine_identity(), "source": str(here)}, indent=2) + "\n")
    return str(t)
