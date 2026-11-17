"""Detect weakened rules: the anti-pattern `sold <= 1` -> `sold <= 2` -> green -> "done".

Each changed property is compared semantically on a finite universe of observable values:
- `domain`: every observable a property reads declares a finite domain in the contract,
  so the comparison is exhaustive over that typed universe (decision is exact);
- `sampled`: otherwise the universe is the observable valuations reached by the model and
  by its auto mutants (guards/updates relaxed). That can miss a difference: a `not_weakened`
  answer from sampling is labelled as such, never as a proof.
Removing a property, adding an assumption or shrinking a forall domain is a weakening.
A weakening is legitimate only with an explicit approval of the new contract digest.
"""
import itertools

from .expr import _items, truth
from .values import ckey

MAX_UNIVERSE = 200000


def _raw(contract, pid):
    for p in contract.doc["properties"]:
        if p["id"] == pid:
            return p
    return None


def _universe(contract_pair, names, consts, sample):
    old, new = contract_pair
    doms = []
    for n in sorted(names):
        spec = new.observables.get(n) or old.observables.get(n)
        if spec is None or spec["domain"] is None:
            doms = None
            break
        doms.append((n, list(_items(spec["domain"](dict(consts))))))
    if doms is not None:
        size = 1
        for _, d in doms:
            size *= max(len(d), 1)
        if size <= MAX_UNIVERSE:
            return "domain", [dict(zip([n for n, _ in doms], combo)) for combo in itertools.product(*[d for _, d in doms])]
    if sample is None:
        return None, []
    return "sampled", sample


def _truth_set(expr, consts, binding, points):
    out = []
    for pt in points:
        env = dict(consts)
        env.update(pt)
        env.update(binding)
        try:
            out.append(truth(expr(env), expr.source))
        except Exception:  # an expression undefined on a point cannot be compared there
            out.append(None)
    return out


def _compare(old_vals, new_vals):
    weaker = any(n is True and o is False for o, n in zip(old_vals, new_vals))
    stronger = any(o is True and n is False for o, n in zip(old_vals, new_vals))
    return "incomparable" if weaker and stronger else "weakened" if weaker else "strengthened" if stronger else "equivalent"


def _bindings(prop, consts):
    bs = [()]
    for name, dom in prop.forall:
        nxt = []
        for b in bs:
            env = dict(consts)
            env.update(b)
            for v in _items(dom(env)):
                nxt.append(b + ((name, v),))
        bs = nxt
    return bs


def sample_universe(model, max_states=20000):
    """Observable valuations of the model and its auto mutants (a relaxed, sampled universe)."""
    from .checker import check
    from .mutate import apply_edits, auto_mutants
    from .spec import model_from_doc
    points = {}
    models = [model]
    for m in auto_mutants(model.doc):
        try:
            models.append(model_from_doc(apply_edits(model.doc, m["edits"]), model.contract))
        except Exception:
            continue
    for m in models:
        try:
            _, g, _ = check(m, max_states=max_states, symmetry=False, keep_graph=True)
        except Exception:
            continue
        for obs in g.obs:
            points[ckey(tuple(sorted(obs.items())))] = dict(obs)
    return list(points.values())


def diff(old, new, consts, sample=None):
    findings = []
    old_ids = {p.id: p for p in old.properties}
    new_ids = {p.id: p for p in new.properties}
    for pid in sorted(set(old_ids) - set(new_ids)):
        findings.append({"property": pid, "change": "removed", "effect": "weakened"})
    for pid in sorted(set(new_ids) - set(old_ids)):
        findings.append({"property": pid, "change": "added", "effect": "strengthened"})
    for pid in sorted(set(old_ids) & set(new_ids)):
        a, b = old_ids[pid], new_ids[pid]
        if _raw(old, pid) == _raw(new, pid):
            continue
        rec = {"property": pid, "change": "modified"}
        if a.kind != b.kind:
            rec.update(effect="incomparable", reason="kind changed %s -> %s" % (a.kind, b.kind))
            findings.append(rec)
            continue
        ba, bb = _bindings(a, consts), _bindings(b, consts)
        ka, kb = {ckey(x) for x in ba}, {ckey(x) for x in bb}
        if ka != kb:
            effect = "weakened" if kb < ka else "strengthened" if ka < kb else "incomparable"
            rec.update(effect=effect, reason="forall instances changed (%d -> %d)" % (len(ka), len(kb)))
            findings.append(rec)
            continue
        if a.kind == "transition":
            rec.update(effect="unknown", reason="transition properties are compared by review, not by enumeration")
            findings.append(rec)
            continue
        names = set()
        for e in a.exprs() + b.exprs():
            names |= e.names & (set(old.observables) | set(new.observables))
        method, points = _universe((old, new), names, consts, sample)
        if not method:
            rec.update(effect="unknown", reason="no finite domains declared and no model to sample from")
            findings.append(rec)
            continue
        effects = []
        for binding in ba:
            if a.kind == "leads_to":
                p_eff = _compare(_truth_set(a.from_, consts, binding, points), _truth_set(b.from_, consts, binding, points))
                q_eff = _compare(_truth_set(a.to, consts, binding, points), _truth_set(b.to, consts, binding, points))
                # P ~> Q is weaker when P shrinks or Q grows.
                flip = {"weakened": "strengthened", "strengthened": "weakened"}
                p_eff = flip.get(p_eff, p_eff)
                parts = {p_eff, q_eff} - {"equivalent"}
                effects.append("equivalent" if not parts else parts.pop() if len(parts) == 1 else "incomparable")
            else:
                effects.append(_compare(_truth_set(a.expr, consts, binding, points), _truth_set(b.expr, consts, binding, points)))
        found = set(effects) - {"equivalent"}
        effect = "equivalent" if not found else found.pop() if len(found) == 1 else "incomparable"
        rec.update(effect=effect, method=method, universe=len(points))
        findings.append(rec)
    old_a = {x["id"]: x for x in old.assumptions}
    new_a = {x["id"]: x for x in new.assumptions}
    for aid in sorted(set(new_a) - set(old_a)):
        findings.append({"assumption": aid, "change": "added", "effect": "weakened", "reason": "a new assumption narrows what is guaranteed"})
    for aid in sorted(set(old_a) - set(new_a)):
        findings.append({"assumption": aid, "change": "removed", "effect": "strengthened"})
    for aid in sorted(set(old_a) & set(new_a)):
        if old_a[aid] != new_a[aid]:
            findings.append({"assumption": aid, "change": "modified", "effect": "unknown", "reason": "assumption text changed; review"})
    for name in sorted(set(old.observables) | set(new.observables)):
        if old.doc["observables"].get(name) != new.doc["observables"].get(name):
            findings.append({"observable": name, "change": "modified", "effect": "unknown", "reason": "observable vocabulary changed; review"})
    if old.parameters != new.parameters:
        findings.append({"parameters": new.parameters, "change": "modified", "effect": "unknown"})
    effects = {f["effect"] for f in findings}
    if effects & {"weakened", "incomparable"}:
        verdict = "WEAKENED"
    elif "unknown" in effects:
        verdict = "UNKNOWN"
    else:
        verdict = "NOT_WEAKENED"
    sampled = any(f.get("method") == "sampled" for f in findings)
    return {"verdict": verdict, "findings": findings, "old": old.identity(), "new": new.identity(),
            "sampled": sampled, "version_increased": new.version > old.version}
