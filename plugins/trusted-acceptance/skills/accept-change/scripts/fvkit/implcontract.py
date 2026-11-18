"""Implementation contract (step 05) and implementation verification (step 07).

A model that passes the checker says nothing about code that does not exist yet. Step 05 turns
the QUALIFIED model into engineering requirements a coding agent can execute; step 07 checks
that the code that was written actually honours them. Both follow vendored upstream
procedures (upstream.py):

  step 05  Quint quint-execute-spec Phase 1-2 (map every spec variable and action to code,
           name gaps and out-of-scope code, plan with verification gates); Specula
           instrumentation-spec-format (one entry per action: code location, trigger point,
           captured fields); Spec Kit plan / tasks (data model, contracts, tests before code);
           pstack create-formal-verification-skill (a check must be seen failing).
  step 07  Quint quint-execute-spec Phase 4 (verify after implementing, never loosen the spec);
           Specula harness-generation (real code only, every action covered by a trace) and
           bug-confirmation reproduction (trigger through public interfaces, positive and
           negative controls); Spec Kit analyze (coverage gaps, inconsistency, severity);
           pstack maintain-formal-verification-skill (break the code, see the check catch it).

What the model fixes is derived mechanically here, so the agent cannot reinterpret it:
  - state:     every model variable and contract observable needs a code counterpart;
  - atomicity: an action that reads and writes the same state (check-then-act) or writes
               several variables must take effect atomically in code; actions writing what
               another action reads contend and need a concurrency test;
  - liveness:  fair actions must not be dropped on failure;
  - tests:     every property, every mutant (a design the checker showed to be wrong) and every
               assumption needs an acceptance obligation.
The agent fills in what only the codebase can answer (where, which mechanism, what happens on
error / timeout / conflict / retry, which commands test it). `check_impl_contract` rejects a
contract whose derived part was edited or no longer matches the model.
"""
import ast
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

from .spec import _keys, load_document
from .upstream import citations
from .values import FvError, digest, require, sha_bytes

FAILURE_CLASSES = ("error", "timeout", "conflict", "retry")
TEST_KINDS = ("property", "concurrency", "regression", "mbt", "liveness", "proof")
COVERING_KINDS = {"invariant": ("property", "mbt", "proof"), "transition": ("property", "mbt", "proof"),
                  "reachable": ("property", "mbt"), "leads_to": ("liveness", "mbt", "proof"),
                  "eventually": ("liveness", "mbt", "proof"), "infinitely_often": ("liveness", "mbt", "proof")}
REVIEW_SEVERITY = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
REVIEW_CATEGORY = ("coverage_gap", "inconsistency", "underspecification", "unmodeled_behavior", "assumption", "other")
UNMODELED_DISPOSITION = ("out_of_scope", "model_it", "defect")
ASSUMPTION_STATUS = ("holds", "violated", "unverified")
OUTPUT_TAIL = 2000
DROP = re.compile(r"\b(drop|discard|ignore|give up|abandon)\b|丢弃|放弃|忽略|不再处理", re.I)   # heuristic, see check_impl_contract


def _nonempty(v):
    return isinstance(v, str) and bool(v.strip())


def _norm(text):
    return re.sub(r"\s+", " ", text).strip()


def _ruled(r):
    return isinstance(r, dict) and _nonempty(r.get("by")) and _nonempty(r.get("text")) and (
        r.get("signer_kind") == "human" or (r.get("signer_kind") == "delegated_agent" and _nonempty(r.get("authorization"))))


# ---- step 05: what the verified model fixes -------------------------------------------------
def _expr_names(e):
    if e is None:
        return set()
    out = set(e.names)
    for n in ast.walk(e.tree):   # pre.x / post.x are rewritten to _fv_field(pre, "x")
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_fv_field" and len(n.args) == 2
                and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str)):
            out.add(n.args[1].value)
    return out


def _state_reads(model, exprs):
    defs = dict(model.definitions)
    seen, todo, out = set(), [e for e in exprs if e is not None], set()
    while todo:
        names = _expr_names(todo.pop())
        out |= names & set(model.variables)
        for n in names & set(defs):
            if n not in seen:
                seen.add(n)
                todo.append(defs[n])
    return out


def _uses(model, expr, params):
    """Variable reads in one expression: {var: set of keys}; key None = the whole variable.

    `v[p]` with p an action parameter reads only p's slot; `update(v, p, x)` reads nothing of v
    (it replaces one slot). Anything else, including a variable reached through a definition,
    reads the whole variable."""
    out = {}
    if expr is None:
        return out
    keyed_nodes = set()
    for n in ast.walk(expr.tree):
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and isinstance(n.slice, ast.Name) and n.slice.id in params:
            keyed_nodes.add(id(n.value))
            out.setdefault(n.value.id, set()).add(n.slice.id)
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "update" and len(n.args) == 3
                and isinstance(n.args[0], ast.Name) and isinstance(n.args[1], ast.Name) and n.args[1].id in params):
            keyed_nodes.add(id(n.args[0]))
    for n in ast.walk(expr.tree):
        if isinstance(n, ast.Name) and n.id in model.variables and id(n) not in keyed_nodes:
            out.setdefault(n.id, set()).add(None)
    for v in _state_reads(model, [expr]) - set(_expr_names(expr)):
        out.setdefault(v, set()).add(None)   # through a definition: conservatively whole
    return {v: k for v, k in out.items() if v in model.variables}


def _write_key(expr, var, params):
    t = expr.tree.body
    if (isinstance(t, ast.Call) and isinstance(t.func, ast.Name) and t.func.id == "update" and len(t.args) == 3
            and isinstance(t.args[0], ast.Name) and t.args[0].id == var and isinstance(t.args[1], ast.Name) and t.args[1].id in params):
        return t.args[1].id
    return None


def derive(model):
    """Everything the QUALIFIED model already decides about the implementation (deterministic)."""
    contract = model.contract
    require(contract is not None, "the model must be bound to its contract")
    variables = []
    for v in model.variables:
        variables.append({"name": v, "observed_by": sorted(o for o, e in model.observables.items() if v in _state_reads(model, [e]))})
    info = {}
    for a in model.actions:
        params = {p for p, _ in a.params}
        reads = {}
        for e in [a.guard] + list(a.updates.values()):
            for v, keys in _uses(model, e, params).items():
                reads.setdefault(v, set()).update(keys)
        writes = {v: _write_key(e, v, params) for v, e in a.updates.items()}
        info[a.name] = (reads, writes)
    fair = {f["action"]: f["kind"] for f in model.fairness}
    ops = []
    for a in model.actions:
        reads, writes = info[a.name]
        shared_rmw = sorted(v for v in writes if None in reads.get(v, set()))
        keyed_rmw = sorted(v for v, k in writes.items() if k is not None and k in reads.get(v, set()) and v not in shared_rmw)
        reasons = []
        if shared_rmw:
            reasons.append("reads and writes shared state %s in one step (check-then-act): the read and the write must not be separable"
                           % shared_rmw)
        if keyed_rmw:
            reasons.append("reads and writes %s for the same %s in one step: concurrent calls for the same key must not interleave"
                           % (keyed_rmw, sorted({writes[v] for v in keyed_rmw})))
        if len(writes) > 1:
            reasons.append("updates %s together: all of them or none must become visible" % sorted(writes))
        contended, same_key = set(), set()
        for b, (_, bw) in info.items():
            for v, keys in reads.items():
                if v not in bw:
                    continue
                if None in keys or bw[v] is None:
                    contended.add(b)
                else:
                    same_key.add(b)
        affects = sorted({o for v in writes for var in variables if var["name"] == v for o in var["observed_by"]})
        ops.append({"action": a.name, "params": [p for p, _ in a.params],
                    "guard": a.guard.source if a.guard is not None else None,
                    "reads": {v: sorted("*" if k is None else k for k in keys) for v, keys in sorted(reads.items())},
                    "writes": {v: ("*" if k is None else k) for v, k in sorted(writes.items())},
                    "read_modify_write": {"shared": shared_rmw, "per_key": keyed_rmw},
                    "atomic_required": bool(reasons), "reasons": reasons,
                    "contended_by": sorted(contended), "same_key_contended_by": sorted(same_key - contended),
                    "affects_observables": affects, "fairness": fair.get(a.name)})
    props = [{"id": p.id, "kind": p.kind, "covered_by_kinds": list(COVERING_KINDS[p.kind])} for p in contract.properties]
    mutants = [{"id": m["id"], "expect_killed_by": list(m.get("expect_killed_by") or [])} for m in model.mutants]
    return {"model": model.id, "model_digest": model.digest, "contract_digest": contract.digest,
            "variables": variables, "observables": sorted(contract.observables), "operations": ops,
            "obligations": {"properties": props, "mutants": mutants,
                            "assumptions": [a["id"] for a in contract.assumptions]}}


def coenabled(model):
    """{(a, b)}: actions a and b are both enabled in some reachable state (None if exploration was incomplete)."""
    from .checker import check
    result, g, _ = check(model, keep_graph=True)
    if not result["complete"]:
        return None
    pairs = set()
    for labels in g.enabled:
        names = {lbl[0] for lbl in labels}
        pairs |= {(a, b) for a in names for b in names}
    return pairs


def draft(model, qualification=None, upstream=None):
    """A contract skeleton: the derived part filled in, the codebase part left as TODO for the agent."""
    d = derive(model)
    proc = []
    if upstream is not None:
        from .upstream import REQUIRED
        proc = [upstream.cite(p, path) for p, path in REQUIRED["fv-impl-contract"]]
    q = None
    if qualification:
        q = {"receipt": str(qualification), "digest": sha_bytes(Path(qualification).read_bytes())}
    todo = "TODO"
    return {
        "schema_version": 1, "kind": "fv-impl-contract", "id": model.id,
        "model_digest": model.digest, "contract_digest": model.contract.digest, "root": ".",
        "qualification": q, "procedure": proc, "derived": d,
        "state": [{"variable": v["name"], "code": todo} for v in d["variables"]],
        "observables": [{"observable": o, "read": todo} for o in d["observables"]],
        "operations": [{
            "action": op["action"], "code": {"file": todo, "symbol": todo},
            "atomicity": {"mechanism": todo if op["atomic_required"] else "none", "scope": todo, "evidence": todo},
            "idempotency": {"required": False, "reason": todo},
            "failures": {k: {"behavior": todo, "model_effect": "no_change"} for k in FAILURE_CLASSES},
            "trace": {"event": op["action"], "trigger": todo, "fields": list(d["observables"])},
        } for op in d["operations"]],
        "acceptance": {"tests": [], "regressions": [{"mutant": m["id"], "detected_by": {"test": todo}} for m in d["obligations"]["mutants"]],
                       "assumptions": [{"assumption": a, "evidence": todo} for a in d["obligations"]["assumptions"]]},
        "out_of_scope": [],
    }


def _root(path, doc):
    base = Path(path).resolve().parent
    return (base / (doc.get("root") or ".")).resolve()


def check_impl_contract(path, model, upstream=None):
    """Step 05 gate: the contract is complete against the verified model and was not reinterpreted."""
    from .receipt import load as load_receipt, validate
    doc = load_document(path)
    require(isinstance(doc, dict) and doc.get("kind") == "fv-impl-contract" and doc.get("schema_version") == 1,
            "%s is not an fv-impl-contract (schema_version 1)" % path)
    _keys(doc, ["schema_version", "kind", "id", "model_digest", "contract_digest", "qualification", "procedure", "derived",
                "state", "observables", "operations", "acceptance"], ["root", "out_of_scope", "notes"], "implementation contract")
    issues = []
    if doc["model_digest"] != model.digest or doc["contract_digest"] != model.contract.digest:
        issues.append("written for another model or contract version: regenerate with `fv impl-contract draft` and carry the answers over")
    d = derive(model)
    if doc["derived"] != d:
        issues.append("the derived section differs from what the verified model fixes (edited by hand, or the model changed)")
    issues += citations(doc["procedure"], "fv-impl-contract", upstream)
    q = doc["qualification"]
    if not (isinstance(q, dict) and q.get("receipt")):
        issues.append("no QUALIFIED receipt: the implementation contract comes after the model check passes")
    else:
        rp = Path(q["receipt"]) if Path(q["receipt"]).is_absolute() else Path(path).resolve().parent / q["receipt"]
        try:
            if q.get("digest") and sha_bytes(rp.read_bytes()) != q["digest"]:
                issues.append("the qualification receipt changed after it was cited")
            validate(load_receipt(rp), model=model, contract=model.contract, expect_verdicts=["QUALIFIED"], min_level="E2")
        except (FvError, OSError) as error:
            issues.append("qualification receipt rejected: %s" % error)

    def todo(v):
        return not _nonempty(v) or v.strip().upper().startswith("TODO")
    state = {s.get("variable"): s for s in doc["state"] or [] if isinstance(s, dict)}
    for v in model.variables:
        if v not in state or todo(state[v].get("code")):
            issues.append("state: model variable %s has no code counterpart (Quint execute-spec Phase 1 question 1)" % v)
    for extra in sorted(set(state) - set(model.variables)):
        issues.append("state: %s is not a model variable" % extra)
    obs = {o.get("observable"): o for o in doc["observables"] or [] if isinstance(o, dict)}
    for o in sorted(model.contract.observables):
        if o not in obs or todo(obs[o].get("read")):
            issues.append("observable %s: say how acceptance reads it from the real system (Specula trace event schema)" % o)
    derived_ops = {op["action"]: op for op in d["operations"]}
    ops = {}
    for i, op in enumerate(doc["operations"] or []):
        _keys(op, ["action", "code", "atomicity", "idempotency", "failures", "trace"], ["notes", "plan"], "operations[%d]" % i)
        ops[op["action"]] = op
    for a in sorted(set(derived_ops) - set(ops)):
        issues.append("operation %s has no entry (Specula: one entry per spec action)" % a)
    for a in sorted(set(ops) - set(derived_ops)):
        issues.append("operation %s is not a model action" % a)
    actions = set(derived_ops)
    together = coenabled(model)
    events = {}
    for name, op in sorted(ops.items()):
        if name not in derived_ops:
            continue
        der, where = derived_ops[name], "operation %s" % name
        code = op["code"] or {}
        if todo(code.get("file")) or todo(code.get("symbol")):
            issues.append("%s: code.file and code.symbol name where it is implemented (Quint execute-spec Phase 1 question 2)" % where)
        at = op["atomicity"] or {}
        if der["atomic_required"]:
            if todo(at.get("mechanism")) or at.get("mechanism") == "none":
                issues.append("%s must be atomic (%s): name the mechanism (transaction, lock, CAS, single statement)"
                              % (where, "; ".join(der["reasons"])))
            if todo(at.get("evidence")):
                issues.append("%s: atomicity.evidence is the verbatim code that provides it (checked in step 07)" % where)
            if todo(at.get("scope")):
                issues.append("%s: atomicity.scope says what the atomic region covers" % where)
        idem = op["idempotency"] or {}
        if not isinstance(idem.get("required"), bool):
            issues.append("%s: idempotency.required is true or false, decided explicitly" % where)
        elif idem["required"] and (todo(idem.get("key")) or todo(idem.get("evidence"))):
            issues.append("%s: idempotent operations name the key and the verbatim code that enforces it" % where)
        elif not idem["required"] and todo(idem.get("reason")):
            issues.append("%s: say why repeating it is harmless or impossible" % where)
        fails = op["failures"] or {}
        for k in FAILURE_CLASSES:
            f = fails.get(k)
            if not (isinstance(f, dict) and not todo(f.get("behavior"))):
                issues.append("%s: failures.%s needs the behaviour on %s" % (where, k, k))
                continue
            eff = f.get("model_effect")
            if eff == "no_change":
                continue
            if eff == "repeat":
                if not idem.get("required"):
                    issues.append("%s: a retry that repeats the operation requires idempotency" % where)
            elif isinstance(eff, str) and eff.startswith("action:") and eff[7:] in actions:
                if together is not None and (name, eff[7:]) not in together:
                    issues.append("%s: failures.%s.model_effect %s — in no reachable state are %s and %s possible together, so this "
                                  "failure would leave the system in a state the model does not allow" % (where, k, eff, name, eff[7:]))
                continue
            elif eff != "repeat":
                issues.append("%s: failures.%s.model_effect must be no_change, repeat or action:<model action> — "
                              "a failure may only leave the system in a state the model allows" % (where, k))
        if der["fairness"] and any(DROP.search((fails.get(k) or {}).get("behavior", "")) for k in FAILURE_CLASSES):
            issues.append("%s is fair in the model (%s): a failure must not silently drop it" % (where, der["fairness"]))
        tr = op["trace"] or {}
        if tr.get("event") != name:
            issues.append("%s: trace.event must be the action name (Specula: one trace event type per spec action)" % where)
        if todo(tr.get("trigger")):
            issues.append("%s: trace.trigger says when the state is captured (before / after which statement)" % where)
        bad = [f for f in tr.get("fields") or [] if f not in model.contract.observables]
        if bad or not tr.get("fields"):
            issues.append("%s: trace.fields must be contract observables %s" % (where, bad or ""))
        unseen = [o for o in der["affects_observables"] if o not in (tr.get("fields") or [])]
        if unseen:
            issues.append("%s: trace.fields omit %s, which this action changes — the trace could not show it going wrong "
                          "(Specula: capture the fields the action modifies)" % (where, unseen))
        events[name] = tr.get("event")
    acc = doc["acceptance"] or {}
    _keys(acc, ["tests", "regressions", "assumptions"], [], "acceptance")
    tests, negative = {}, 0
    for i, t in enumerate(acc["tests"] or []):
        _keys(t, ["id", "kind", "covers"], ["argv", "must_fail_with", "timeout_seconds", "receipt", "notes"], "acceptance.tests[%d]" % i)
        if t["id"] in tests:
            issues.append("test id %s is duplicated" % t["id"])
        tests[t["id"]] = t
        if t["kind"] not in TEST_KINDS:
            issues.append("test %s: kind must be one of %s" % (t["id"], TEST_KINDS))
        if t["kind"] == "proof":
            if not t.get("receipt"):
                issues.append("test %s: a proof obligation cites an external receipt (E4)" % t["id"])
        elif not (isinstance(t.get("argv"), list) and t["argv"] and all(isinstance(x, str) for x in t["argv"])):
            issues.append("test %s: argv is a non-empty list of strings (no shell)" % t["id"])
        if t.get("must_fail_with") is not None:
            if not (isinstance(t["must_fail_with"], list) and t["must_fail_with"] and all(isinstance(x, str) for x in t["must_fail_with"])):
                issues.append("test %s: must_fail_with is an argv list" % t["id"])
            elif not (isinstance(t.get("argv"), list) and len(t["must_fail_with"]) > len(t["argv"])
                      and t["must_fail_with"][:len(t["argv"])] == t["argv"]):
                issues.append("test %s: must_fail_with must be the test's own argv plus the arguments that select the broken "
                              "variant — an unrelated failing command shows nothing about this test" % t["id"])
            else:
                negative += 1
        known = set(derived_ops) | {p.id for p in model.contract.properties} | {a["id"] for a in model.contract.assumptions}
        for c in t["covers"] or []:
            if c not in known:
                issues.append("test %s covers unknown %s" % (t["id"], c))
    for p in d["obligations"]["properties"]:
        if not any(p["id"] in (t["covers"] or []) and t["kind"] in p["covered_by_kinds"] for t in tests.values()):
            issues.append("property %s (%s) has no acceptance test of kind %s (Spec Kit analyze: zero coverage)"
                          % (p["id"], p["kind"], "/".join(p["covered_by_kinds"])))
    for op in d["operations"]:
        if op["atomic_required"] and op["contended_by"] and not any(
                op["action"] in (t["covers"] or []) and t["kind"] == "concurrency" for t in tests.values()):
            issues.append("operation %s contends with %s: it needs a concurrency test" % (op["action"], op["contended_by"]))
    if negative == 0:
        issues.append("no test declares must_fail_with: a check never seen failing proves nothing (pstack: able to fail)")
    regs = {}
    for i, r in enumerate(acc["regressions"] or []):
        _keys(r, ["mutant", "detected_by"], ["notes"], "acceptance.regressions[%d]" % i)
        regs[r["mutant"]] = r
        by = r["detected_by"] or {}
        if by.get("vector"):
            continue
        t = tests.get(by.get("test"))
        if t is None:
            issues.append("regression %s: detected_by names a vector or an existing test" % r["mutant"])
            continue
        killers = next((m["expect_killed_by"] for m in d["obligations"]["mutants"] if m["id"] == r["mutant"]), [])
        if killers and not set(killers) & set(t["covers"] or []):
            issues.append("regression %s: test %s covers none of the properties that kill it %s" % (r["mutant"], t["id"], killers))
    for m in d["obligations"]["mutants"]:
        if m["id"] not in regs:
            issues.append("mutant %s (a design the checker proved wrong) has no regression obligation in code" % m["id"])
    assum = {a.get("assumption"): a for a in acc["assumptions"] or [] if isinstance(a, dict)}
    for a in d["obligations"]["assumptions"]:
        ev = (assum.get(a) or {}).get("evidence")
        if todo(ev) or not (ev == "review" or (ev.startswith("test:") and ev[5:] in tests)):
            issues.append("assumption %s: evidence is `test:<id>` or `review` (checked in step 07)" % a)
    for i, o in enumerate(doc.get("out_of_scope") or []):
        if not (isinstance(o, dict) and _nonempty(o.get("behavior")) and _nonempty(o.get("reason"))):
            issues.append("out_of_scope[%d] needs behavior and reason (Quint execute-spec Phase 1 question 4)" % i)
    return {"verdict": "READY" if not issues else "NOT_READY", "issues": issues, "derived": d,
            "digest": sha_bytes(Path(path).read_bytes())}


# ---- step 07: does the code honour the contract? --------------------------------------------
def _run(argv, cwd, timeout, env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    started = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, env=env)
        return {"argv": argv, "exit": p.returncode, "timed_out": False, "millis": int((time.monotonic() - started) * 1000),
                "output_tail": (p.stdout + p.stderr)[-OUTPUT_TAIL:]}
    except subprocess.TimeoutExpired:
        return {"argv": argv, "exit": None, "timed_out": True, "millis": int((time.monotonic() - started) * 1000), "output_tail": ""}
    except OSError as error:
        return {"argv": argv, "exit": None, "timed_out": False, "millis": 0, "output_tail": "cannot start: %s" % error}


def _python_symbol(path, symbol):
    """Source of `Class.method` / `function` with comments and its docstring blanked; None if not found."""
    import io
    import tokenize
    src = path.read_text(encoding="utf-8", errors="replace")
    try:
        node = ast.parse(src)
    except SyntaxError:
        return None
    for part in str(symbol).split("."):
        node = next((c for c in ast.iter_child_nodes(node)
                     if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and c.name == part), None)
        if node is None:
            return None
    lines = src.splitlines(keepends=True)
    first, last = node.lineno - 1, node.end_lineno
    seg = [list(x) for x in lines[first:last]]
    body = getattr(node, "body", [])
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        for n in range(body[0].lineno - 1, body[0].end_lineno):
            seg[n - first] = list("\n")
    try:
        for tok in tokenize.generate_tokens(io.StringIO("".join(lines[first:last])).readline):
            if tok.type == tokenize.COMMENT:
                row, (c0, c1) = tok.start[0] - 1, (tok.start[1], tok.end[1])
                seg[row][c0:c1] = [" "] * (c1 - c0)
    except (tokenize.TokenError, IndentationError):
        pass
    return "".join("".join(x) for x in seg)


def _code_evidence(doc, root):
    """Each operation's evidence must sit in its own symbol. Python is parsed (comments and docstrings do not count);
    other languages fall back to the whole file, and the record says so (`scope: file`)."""
    out = []
    for op in doc["operations"]:
        rec = {"action": op["action"], "file": (op["code"] or {}).get("file"), "symbol": (op["code"] or {}).get("symbol"), "missing": []}
        f = (root / (rec["file"] or "")).resolve()
        if not (rec["file"] and (f == root or root in f.parents) and f.is_file()):
            rec["missing"].append("file %s" % rec["file"])
            out.append(rec)
            continue
        rec["file_digest"] = sha_bytes(f.read_bytes())
        if f.suffix == ".py":
            scoped = _python_symbol(f, rec["symbol"])
            rec["scope"] = "symbol"
            if scoped is None:
                rec["missing"].append("symbol %s" % rec["symbol"])
                out.append(rec)
                continue
            text = _norm(scoped)
        else:
            text = _norm(f.read_text(encoding="utf-8", errors="replace"))
            rec["scope"] = "file"
            last = str(rec["symbol"] or "").split(".")[-1]
            if not last or last not in text:
                rec["missing"].append("symbol %s" % rec["symbol"])
        at = op["atomicity"] or {}
        if at.get("mechanism") not in (None, "none") and _nonempty(at.get("evidence")) and _norm(at["evidence"]) not in text:
            rec["missing"].append("atomicity evidence %r in %s" % (at["evidence"][:80], rec["symbol"]))
        idem = op["idempotency"] or {}
        if idem.get("required") and _nonempty(idem.get("evidence")) and _norm(idem["evidence"]) not in text:
            rec["missing"].append("idempotency evidence %r in %s" % (idem["evidence"][:80], rec["symbol"]))
        out.append(rec)
    return out


LOCATION = re.compile(r"^([^\s:]+):([0-9]+)(?:-([0-9]+))?$")


def _location_issue(root, loc):
    m = LOCATION.match(str(loc or ""))
    if not m:
        return "location %r is not file:line[-line]" % loc
    f = (root / m.group(1)).resolve()
    if not ((f == root or root in f.parents) and f.is_file()):
        return "location %s names no file under the contract root" % loc
    a, b = int(m.group(2)), int(m.group(3) or m.group(2))
    n = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
    if not 1 <= a <= b <= n:
        return "location %s is outside %s (%d lines)" % (loc, m.group(1), n)
    return None


def check_impl_review(path, contract_path, doc, root, upstream=None):
    """Spec Kit analyze + Quint execute-spec gap questions, written by a fresh reviewer after coding."""
    rev = load_document(path)
    require(isinstance(rev, dict) and rev.get("kind") == "fv-impl-review" and rev.get("schema_version") == 1,
            "%s is not an fv-impl-review" % path)
    _keys(rev, ["schema_version", "kind", "impl_contract_digest", "source", "procedure", "reviewer", "coverage",
                "unmodeled_behaviors", "assumptions", "findings", "review_complete"], ["notes"], "implementation review")
    issues = []
    if rev["impl_contract_digest"] != sha_bytes(Path(contract_path).read_bytes()):
        issues.append("review was written against another version of the implementation contract")
    issues += citations(rev["procedure"], "fv-impl-review", upstream)
    for rel, dg in sorted(((rev["source"] or {}).get("files") or {}).items()):
        f = root / rel
        if not f.is_file() or sha_bytes(f.read_bytes()) != dg:
            issues.append("reviewed code changed since the review: %s" % rel)
    files = {(op["code"] or {}).get("file") for op in doc["operations"]}
    missing_files = sorted(f for f in files if f and f not in ((rev["source"] or {}).get("files") or {}))
    if missing_files:
        issues.append("the review did not pin the code it read: %s" % missing_files)
    if (rev["reviewer"] or {}).get("context") != "fresh":
        issues.append("the reviewer must work in a fresh context (reviewer.context: fresh)")
    cov = {c.get("operation"): c for c in rev["coverage"] or [] if isinstance(c, dict)}
    for op in doc["operations"]:
        c = cov.get(op["action"])
        if c is None:
            issues.append("coverage: operation %s was not reviewed (Spec Kit analyze coverage summary)" % op["action"])
        elif c.get("implemented") is not True or not _nonempty(c.get("location")):
            issues.append("coverage: operation %s is not implemented as contracted (%s)" % (op["action"], c.get("notes") or "no location"))
        elif _location_issue(root, c["location"]):
            issues.append("coverage: operation %s: %s" % (op["action"], _location_issue(root, c["location"])))
    for i, u in enumerate(rev["unmodeled_behaviors"] or []):
        _keys(u, ["behavior", "location", "disposition", "reason"], [], "unmodeled_behaviors[%d]" % i)
        if _location_issue(root, u["location"]):
            issues.append("unmodeled behaviour %r: %s" % (u["behavior"][:60], _location_issue(root, u["location"])))
        if u["disposition"] not in UNMODELED_DISPOSITION or not _nonempty(u["reason"]):
            issues.append("unmodeled behaviour %r: disposition out_of_scope|model_it|defect with a reason" % u["behavior"][:60])
        elif u["disposition"] == "model_it":
            issues.append("unmodeled behaviour %r must be modelled before acceptance (route fv_model_infidelity)" % u["behavior"][:60])
        elif u["disposition"] == "defect":
            issues.append("unmodeled behaviour %r is a defect in the code (route fv_implementation_defect)" % u["behavior"][:60])
    ass = {a.get("assumption"): a for a in rev["assumptions"] or [] if isinstance(a, dict)}
    for a in (doc["derived"]["obligations"]["assumptions"]):
        r = ass.get(a)
        if r is None or r.get("status") not in ASSUMPTION_STATUS or not _nonempty(r.get("evidence")):
            issues.append("assumption %s: status holds|violated|unverified with evidence" % a)
        elif r["status"] == "violated":
            issues.append("assumption %s does not hold in the implementation: every property built on it is void" % a)
        elif r["status"] == "unverified" and not _ruled(r.get("ruling")):
            issues.append("assumption %s is unverified: a human accepts the risk (ruling) or it is checked" % a)
    ids = set()
    for i, f in enumerate(rev["findings"] or []):
        _keys(f, ["id", "category", "severity", "location", "summary", "recommendation"], ["resolution"], "findings[%d]" % i)
        if f["id"] in ids:
            issues.append("duplicate finding id %s" % f["id"])
        ids.add(f["id"])
        if f["severity"] not in REVIEW_SEVERITY or f["category"] not in REVIEW_CATEGORY:
            issues.append("finding %s: severity CRITICAL|HIGH|MEDIUM|LOW and a known category" % f["id"])
        elif f["severity"] in ("CRITICAL", "HIGH") and not _ruled(f.get("resolution")):
            issues.append("finding %s (%s) is open: fix the code or have a human rule on it" % (f["id"], f["severity"]))
    done = rev["review_complete"] or {}
    if done.get("status") != "complete" or done.get("findings_count") != len(rev["findings"] or []):
        issues.append("review is incomplete or truncated (completion marker missing, or finding count does not match)")
    return {"verdict": "REVIEWED" if not issues else "NOT_REVIEWED", "issues": issues, "digest": sha_bytes(Path(path).read_bytes())}


def _dirty(root, files):
    """Pinned files whose working-tree bytes are not the committed ones (modified, staged or untracked)."""
    if not files:
        return []
    changed = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all", "--"] + files,
                             capture_output=True, text=True)
    if changed.returncode != 0:
        return []
    top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    out = set()
    for line in changed.stdout.splitlines():
        path = line[3:].split(" -> ")[-1].strip('"')
        full = (Path(top) / path).resolve() if top else None
        for f in files:
            if full is not None and full == (root / f).resolve():
                out.add(f)
    return sorted(out)


def decide(res):
    """Reasons follow from the recorded parts alone, so a receipt can be re-decided."""
    reasons = ["contract: " + i for i in res["contract"]["issues"]]
    for c in res["code"]:
        for m in c["missing"]:
            reasons.append("operation %s: %s not found in code" % (c["action"], m))
    if not res["tests"]:
        reasons.append("the acceptance tests were not run")
    elif not any(t["role"] == "negative" for t in res["tests"]):
        reasons.append("no negative control ran: no test was seen failing on a broken variant")
    for t in res["tests"]:
        if t["role"] == "positive" and t["exit"] != 0:
            reasons.append("test %s failed (%s)" % (t["id"], "timeout" if t["timed_out"] else "exit %s" % t["exit"]))
        if t["role"] == "negative" and t["exit"] == 0:
            reasons.append("test %s still passes on its broken variant: it cannot see the defect it guards against" % t["id"])
        elif t["role"] == "negative" and not isinstance(t["exit"], int):
            reasons.append("test %s's negative control never ran to a verdict (%s): a crash or hang shows nothing"
                           % (t["id"], "timeout" if t["timed_out"] else "could not start"))
    tr = res["traces"]
    produced = (res.get("trace_origin") or {}).get("tests")
    if tr is None or not tr["traces"]:
        reasons.append("no implementation traces: real operations were never checked against the model's transitions")
    elif produced is not None and not produced:
        reasons.append("no trace was produced by the contract's own tests: supplied traces are checked but cannot stand in "
                       "for running the real code (Specula: never hand-write trace data)")
    elif tr["verdict"] != "CONFORMS":
        for t in tr["traces"]:
            if t["verdict"] != "CONFORMS":
                reasons.append("trace %s is %s at line %s: %s" % (Path(t["trace"]["path"]).name, t["verdict"], t.get("failed_at_line"), t.get("reason")))
            for v in t["property_violations"]:
                reasons.append("trace %s violates %s at %s" % (Path(t["trace"]["path"]).name, v["property"], v["at"]))
    for a in res["coverage"]["unexercised"]:
        reasons.append("operation %s never happened in a conforming trace (Specula: every event type covered)" % a)
    for r in res["replays"]:
        if not r["conforming_trace"]:
            reasons.append("counterexample replay %s (mutant %s) has no conforming trace: not shown fixed in real code" % (r["vector"], r["mutant"]))
    for f in (res.get("source") or {}).get("dirty") or []:
        reasons.append("%s was verified with uncommitted changes: the receipt's commit does not describe the bytes that were tested" % f)
    if res["source_map"] is not None and res["source_map"]["status"] != "FRESH":
        reasons.append("source map is %s" % res["source_map"]["status"])
    if res["review"] is None:
        reasons.append("no implementation review (Spec Kit analyze + Quint execute-spec gap questions by a fresh reviewer)")
    else:
        reasons += ["review: " + i for i in res["review"]["issues"]]
    return reasons


def verify_implementation(contract_path, model, traces=None, review=None, source_map=None, run=True, upstream=None,
                          out_dir=None, timeout=600):
    """Step 07: constraints present in code, real steps allowed by the model, counterexamples fixed, tests seen failing."""
    from .trace import check_files, load_trace
    doc = load_document(contract_path)
    contract_res = check_impl_contract(contract_path, model, upstream)
    root = _root(contract_path, doc)
    res = {"contract": {"verdict": contract_res["verdict"], "issues": contract_res["issues"], "digest": contract_res["digest"]},
           "code": [], "tests": [], "traces": None, "coverage": {"exercised": [], "unexercised": []}, "replays": [],
           "source_map": None, "review": None, "source": {"head": None, "files": {}}}
    try:
        res["code"] = _code_evidence(doc, root)
    except (KeyError, TypeError) as error:
        res["code"] = [{"action": "?", "missing": ["unreadable operations: %s" % error]}]
    for c in res["code"]:
        if c.get("file_digest"):
            res["source"]["files"][c["file"]] = c["file_digest"]
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True)
    res["source"]["head"] = head.stdout.strip() if head.returncode == 0 else None
    supplied = [str(p) for p in traces or []]
    produced = []
    work = Path(out_dir or tempfile.mkdtemp(prefix="fv-impl-")).resolve()   # tests run with cwd = the contract root
    acc = doc.get("acceptance") or {}
    for t in acc.get("tests") or []:   # the tests are part of what was verified: pin the scripts they run
        for a in (t.get("argv") or []) + (t.get("must_fail_with") or []):
            f = (root / a).resolve() if "{" not in a else None
            if f is not None and (root in f.parents) and f.is_file():
                res["source"]["files"][str(f.relative_to(root))] = sha_bytes(f.read_bytes())
    if run:
        for t in acc.get("tests") or []:
            if t.get("kind") == "proof" or not t.get("argv"):
                continue
            tdir = work / ("traces-" + re.sub(r"[^A-Za-z0-9_.-]+", "_", t["id"]))
            uses_traces = any("{traces}" in a for a in t["argv"])
            if uses_traces:
                tdir.mkdir(parents=True, exist_ok=False)
            argv = [a.replace("{traces}", str(tdir)) for a in t["argv"]]
            r = _run(argv, root, t.get("timeout_seconds") or timeout)
            res["tests"].append(dict(r, id=t["id"], kind=t["kind"], role="positive", argv=t["argv"]))
            if uses_traces and r["exit"] == 0:
                produced += sorted(str(p) for p in tdir.glob("*.jsonl"))
            if t.get("must_fail_with"):
                ndir = work / ("negative-" + re.sub(r"[^A-Za-z0-9_.-]+", "_", t["id"]))
                if any("{traces}" in a for a in t["must_fail_with"]):
                    ndir.mkdir(parents=True, exist_ok=False)
                nargv = [a.replace("{traces}", str(ndir)) for a in t["must_fail_with"]]
                n = _run(nargv, root, t.get("timeout_seconds") or timeout)
                res["tests"].append(dict(n, id=t["id"], kind=t["kind"], role="negative", argv=t["must_fail_with"]))
    res["trace_origin"] = {"tests": produced, "supplied": supplied}
    if produced or supplied:
        tr = check_files(model, produced + supplied)
        res["traces"] = tr
        seen = set()
        for t in tr["traces"]:
            if t["verdict"] != "CONFORMS" or t["trace"]["path"] not in produced:
                continue   # coverage and replays count only real runs of the contract's own tests
            _, events = load_trace(t["trace"]["path"])
            seen |= {e["action"] for e in events if e.get("action") and not e.get("rejected")}
        res["coverage"] = {"exercised": sorted(seen), "unexercised": sorted({a.name for a in model.actions} - seen)}
        for r in acc.get("regressions") or []:
            vec = (r.get("detected_by") or {}).get("vector")
            if vec:
                ok = any((t["trace"].get("header") or {}).get("vector") == vec and t["verdict"] == "CONFORMS"
                         and t["trace"]["path"] in produced for t in tr["traces"])
                res["replays"].append({"mutant": r["mutant"], "vector": vec, "conforming_trace": ok})
    else:
        for r in acc.get("regressions") or []:
            vec = (r.get("detected_by") or {}).get("vector")
            if vec:
                res["replays"].append({"mutant": r["mutant"], "vector": vec, "conforming_trace": False})
    if source_map:
        from .sourcemap import verify as verify_map
        sm = verify_map(source_map, model)
        res["source_map"] = {k: sm[k] for k in ("status", "issues", "stale", "drifted_files", "map_digest")}
    if review:
        res["review"] = check_impl_review(review, contract_path, doc, root, upstream)
    res["source"]["dirty"] = _dirty(root, sorted(res["source"]["files"])) if res["source"]["head"] else []
    reasons = decide(res)
    res["reasons"] = reasons
    return {"verdict": "IMPLEMENTS" if not reasons else "NOT_IMPLEMENTED", "result": res,
            "impl_contract": {"path": str(contract_path), "digest": contract_res["digest"]}}


def dump(doc, path):
    p = Path(path)
    require(not p.exists(), "refusing to overwrite %s" % p)
    if p.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            raise FvError("PyYAML is needed to write YAML; use a .json path") from None
        class NoAlias(yaml.SafeDumper):   # a contract is read by people and agents: no &anchors / *aliases
            def ignore_aliases(self, data):
                return True
        text = yaml.dump(doc, Dumper=NoAlias, allow_unicode=True, sort_keys=False, width=120)
    else:
        text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return str(p)


__all__ = ["derive", "draft", "check_impl_contract", "check_impl_review", "verify_implementation", "decide", "dump", "digest"]
