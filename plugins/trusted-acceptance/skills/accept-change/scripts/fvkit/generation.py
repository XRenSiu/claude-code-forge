"""AI generation of rules and models, made checkable.

An agent writes the requirement inventory, the rules (fv-contract) and the model (fv-model) by
executing vendored open-source procedures (upstream.py lists them; methods.py checks their
outputs). Nothing here trusts that writing. Each step leaves an artifact a script can check:

1. Inventory (fv-requirements). Every requirement quotes its source verbatim; quotes are
   checked against the files, so an invented requirement has nothing to quote. Every
   normative sentence in the sources must land somewhere: a requirement, an assumption or an
   explicit out-of-scope entry. Silent omission is how rules get lost.
2. Intake (Spec Kit clarify + Quint from-requirements): ambiguity scan, human-answered
   questions, system-model checklist, extraction table with impact, granularity decisions.
3. Rules. At least two candidate contracts are written by isolated generators from the same
   inventory. `trace_rules` checks that each one covers every requirement (property or
   disposition) and cites only real requirement ids. `rules_divergence` compares the
   candidates per requirement on a finite universe and turns every difference into an
   agenda item with a witness. High-impact property requirements must be formalized.
4. Review (Formal Verification Skills review contract): a fresh reviewer's immutable review,
   the author's separate triage, human rulings for deferrals.
5. Models. At least two candidate models (Quint quint-modeling / TLA+ from-source / Specula
   spec generation) are compared by what an observer could see: reachable observable
   valuations, observable transitions and property verdicts. Each carries the Quint Step 7
   handoff; a fresh model review runs the Quint review checks and the Specula granularity
   audit. Code-first modules also need the Specula modeling brief with its coverage audit and
   a calibration: traces of the CURRENT code conform to the as-is model before any
   counterexample from it is believed.
6. Adoption. The adopted contract/model must itself be one of the compared candidates, and
   every divergence item needs a ruling (human, or delegated with the human's words).
"""
import itertools
import json
import re
from pathlib import Path

from .expr import _items, truth
from .spec import _keys, _text, load_document
from .values import FvError, ckey, digest, require, sha_bytes, show

MIN_CANDIDATES = 2
MAX_UNIVERSE = 200000
MAX_ITEMS = 200
NORMATIVE = re.compile(r"必须|不得|不能|不会|不允许|禁止|应当|应该|只能|最终|永远|恰好|\bmust\b|\bshall\b|\bnever\b|\balways\b", re.I)


def _norm(text):
    return re.sub(r"\s+", " ", text).strip()


# ---- 1. requirement inventory --------------------------------------------------------------
class Requirements:
    def __init__(self, path):
        self.path = Path(path).resolve()
        doc = load_document(self.path)
        _keys(doc, ["schema_version", "kind", "id", "sources", "requirements"],
              ["assumptions", "out_of_scope", "open_questions", "notes"], "requirements")
        require(doc["schema_version"] == 1 and doc["kind"] == "fv-requirements", "unsupported requirements (schema_version 1, kind fv-requirements)")
        self.doc = doc
        self.sources = {}
        for i, s in enumerate(doc["sources"]):
            _keys(s, ["id", "path"], ["kind"], "sources[%d]" % i)
            p = (self.path.parent / s["path"]).resolve()
            require(p.is_file(), "requirement source %s does not exist: %s" % (s["id"], s["path"]))
            require(s["id"] not in self.sources, "duplicate source id %s" % s["id"])
            self.sources[s["id"]] = {"path": p, "kind": s.get("kind", "text"), "rel": s["path"]}
        self.items = {}
        for section in ("requirements", "assumptions"):
            for i, r in enumerate(doc.get(section) or []):
                _keys(r, ["id", "text", "source"], ["notes"], "%s[%d]" % (section, i))
                require(r["id"] not in self.items, "duplicate requirement/assumption id %s" % r["id"])
                _text(r["text"], "%s[%d].text" % (section, i))
                self.items[r["id"]] = dict(r, section=section)
        self.requirement_ids = [r["id"] for r in doc["requirements"]]
        require(self.requirement_ids, "requirements must not be empty")
        self.out_of_scope = list(doc.get("out_of_scope") or [])
        for i, o in enumerate(self.out_of_scope):
            _keys(o, ["text", "reason"], ["source"], "out_of_scope[%d]" % i)
        self.open_questions = list(doc.get("open_questions") or [])
        for i, q in enumerate(self.open_questions):
            _keys(q, ["id", "text"], ["owner"], "open_questions[%d]" % i)

    def digest(self):
        return digest({"inventory": self.doc, "sources": {k: sha_bytes(v["path"].read_bytes()) for k, v in sorted(self.sources.items())}})

    def _quote_ok(self, src, where):
        if not isinstance(src, dict):
            return ["%s: source must be {doc, quote} or {doc, ac}" % where]
        doc_id = src.get("doc")
        if doc_id not in self.sources:
            return ["%s: unknown source %r" % (where, doc_id)]
        meta = self.sources[doc_id]
        if "ac" in src:
            try:
                import yaml
                dw = yaml.safe_load(meta["path"].read_text(encoding="utf-8")) or {}
            except ImportError:
                return ["%s: PyYAML is needed to resolve done_when AC ids" % where]
            acs = {a.get("id") for a in (dw.get("acceptance") or []) if isinstance(a, dict)}
            return [] if src["ac"] in acs else ["%s: AC %s not found in %s" % (where, src["ac"], meta["rel"])]
        quote = src.get("quote")
        if not (isinstance(quote, str) and len(_norm(quote)) >= 6):
            return ["%s: quote must be verbatim source text of at least 6 characters" % where]
        if _norm(quote) not in _norm(meta["path"].read_text(encoding="utf-8")):
            return ["%s: quote is not verbatim in %s: %r" % (where, meta["rel"], quote[:80])]
        return []

    def normative_fragments(self):
        out = []
        for doc_id, meta in self.sources.items():
            if meta["kind"] == "done_when":
                continue
            lines = meta["path"].read_text(encoding="utf-8").splitlines()
            for n, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or set(stripped) <= set("|-: "):
                    continue
                following = lines[n].strip() if n < len(lines) else ""
                if stripped.startswith("|") and following.startswith("|") and set(following) <= set("|-: "):
                    continue  # a table header names columns; it promises nothing
                for frag in re.split(r"[。；;！!？?]|\s\|\s|\|", stripped):
                    if NORMATIVE.search(frag) and len(_norm(frag)) >= 4:
                        out.append({"doc": doc_id, "line": n, "text": _norm(frag)})
        return out

    def check(self):
        issues = []
        for rid, r in self.items.items():
            issues += self._quote_ok(r["source"], "%s %s" % (r["section"][:-1], rid))
        quotes = [_norm(r["source"]["quote"]) for r in self.items.values() if isinstance(r["source"], dict) and r["source"].get("quote")]
        for i, o in enumerate(self.out_of_scope):
            if o.get("source"):
                issues += self._quote_ok(o["source"], "out_of_scope[%d]" % i)
                if isinstance(o["source"], dict) and o["source"].get("quote"):
                    quotes.append(_norm(o["source"]["quote"]))
        uncovered = []
        for frag in self.normative_fragments():
            if not any(q in frag["text"] or frag["text"] in q for q in quotes):
                uncovered.append(frag)
        for f in uncovered:
            issues.append("normative sentence not inventoried (make it a requirement, an assumption or out_of_scope with a quote): %s:%d %r"
                          % (self.sources[f["doc"]]["rel"], f["line"], f["text"][:100]))
        for doc_id, meta in self.sources.items():
            if meta["kind"] == "done_when":
                try:
                    import yaml
                    dw = yaml.safe_load(meta["path"].read_text(encoding="utf-8")) or {}
                except ImportError:
                    issues.append("PyYAML is needed to read %s" % meta["rel"])
                    continue
                cited = {r["source"].get("ac") for r in self.items.values() if isinstance(r["source"], dict) and r["source"].get("doc") == doc_id}
                cited |= {o["source"].get("ac") for o in self.out_of_scope if isinstance(o.get("source"), dict)}
                for ac in (dw.get("acceptance") or []):
                    if isinstance(ac, dict) and ac.get("id") not in cited:
                        issues.append("done_when %s is neither a requirement nor out_of_scope" % ac.get("id"))
        return {"verdict": "COMPLETE" if not issues else "GAPS", "issues": issues, "requirements": self.requirement_ids,
                "assumptions": [k for k, v in self.items.items() if v["section"] == "assumptions"],
                "open_questions": [q["id"] for q in self.open_questions], "digest": self.digest()}


def requirements_for(contract, explicit=None):
    if explicit:
        return Requirements(explicit)
    require(contract.requirements_ref and contract.path, "contract %s has no `requirements:` link; rules must trace to an inventory" % contract.id)
    return Requirements(Path(contract.path).resolve().parent / contract.requirements_ref)


# ---- 2. rules: traceability ----------------------------------------------------------------
def trace_rules(contract, reqs):
    issues = []
    inv = reqs.check()
    issues += inv["issues"]
    if reqs.open_questions:
        issues.append("open questions must be answered before the rules are signed: %s" % [q["id"] for q in reqs.open_questions])
    known = set(reqs.items)
    covered = {}
    for p in contract.properties:
        if not p.sources:
            issues.append("property %s cites no requirement" % p.id)
        if not (isinstance(p.text, str) and p.text.strip()):
            issues.append("property %s has no natural-language `text` (a reviewer cannot check what it is meant to say)" % p.id)
        for s in p.sources:
            if s not in known:
                issues.append("property %s cites unknown requirement %s" % (p.id, s))
            covered.setdefault(s, []).append(p.id)
    disp = {}
    for d in contract.dispositions:
        if d["requirement"] not in reqs.requirement_ids:
            issues.append("disposition for unknown requirement %s" % d["requirement"])
        disp[d["requirement"]] = d
    for rid in reqs.requirement_ids:
        if rid not in covered and rid not in disp:
            issues.append("requirement %s is neither formalized nor dispositioned" % rid)
        if rid in covered and rid in disp:
            issues.append("requirement %s is both formalized and dispositioned" % rid)
    for a in contract.assumptions:
        src = a.get("source")
        if not src or (src not in known and src not in ("environment", "design")):
            issues.append("assumption %s cites no inventoried requirement/assumption (or environment/design)" % a["id"])
    return {"verdict": "TRACEABLE" if not issues else "GAPS", "issues": issues, "coverage": covered,
            "dispositions": {k: v["status"] for k, v in disp.items()}, "inventory": inv,
            "contract": contract.identity(), "requirements_digest": reqs.digest()}


# ---- 2b. rules: divergence between independent candidates -----------------------------------
def _instances(prop, consts):
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


def _universe(candidates, names, consts):
    doms = []
    for n in sorted(names):
        spec = next((c.observables[n] for _, c in candidates if n in c.observables and c.observables[n]["domain"] is not None), None)
        if spec is None:
            return None
        doms.append((n, list(_items(spec["domain"](dict(consts))))))
    size = 1
    for _, d in doms:
        size *= max(len(d), 1)
    if size > MAX_UNIVERSE:
        return None
    names = [n for n, _ in doms]
    return [dict(zip(names, combo)) for combo in itertools.product(*[d for _, d in doms])]


def _predicate(props, consts, point, field="expr"):
    for p in props:
        expr = getattr(p, field)
        for b in _instances(p, consts):
            env = dict(consts)
            env.update(point)
            env.update(b)
            try:
                if not truth(expr(env), expr.source):
                    return False
            except FvError:
                return None
    return True


def rules_divergence(reqs, candidates, consts):
    """candidates: [(label, Contract)] written independently from the same inventory."""
    require(len(candidates) >= MIN_CANDIDATES, "divergence needs at least %d independently generated candidates" % MIN_CANDIDATES)
    labels = [l for l, _ in candidates]
    require(len(set(labels)) == len(labels), "candidate labels must be unique")
    items = []

    def add(item_type, **kw):
        if len(items) < MAX_ITEMS:
            items.append(dict({"id": "D%d" % (len(items) + 1), "type": item_type}, **kw))

    vocab = {l: {k: v["type"] for k, v in c.observables.items()} for l, c in candidates}
    if len({json.dumps(v, sort_keys=True) for v in vocab.values()}) > 1:
        add("vocabulary", detail="observable vocabularies differ", by_candidate=vocab)
    for rid in reqs.requirement_ids:
        props = {l: [p for p in c.properties if rid in p.sources] for l, c in candidates}
        disp = {l: next((d["status"] for d in c.dispositions if d["requirement"] == rid), None) for l, c in candidates}
        covering = [l for l in labels if props[l]]
        if covering and len(covering) != len(labels):
            add("coverage", requirement=rid, formalized_by=covering,
                not_formalized_by={l: disp[l] or "missing" for l in labels if l not in covering})
            continue
        if not covering:
            if len({disp[l] for l in labels}) > 1:
                add("disposition", requirement=rid, by_candidate=disp)
            continue
        kinds = {l: sorted({p.kind for p in props[l]}) for l in labels}   # two invariants vs one conjunction is not a kind change
        if len({tuple(k) for k in kinds.values()}) > 1:
            add("kind", requirement=rid, by_candidate=kinds)
            continue
        for kind in sorted({p.kind for p in props[labels[0]]}):
            group = {l: [p for p in props[l] if p.kind == kind] for l in labels}
            if kind == "transition":
                texts = {l: sorted(_norm(p.expr.source) for p in group[l]) for l in labels}
                if len({tuple(t) for t in texts.values()}) > 1:
                    add("unverified_equivalence", requirement=rid, kind=kind, by_candidate=texts,
                        detail="transition properties are compared by text; a human must rule on meaning")
                continue
            fields = ["from_", "to"] if kind == "leads_to" else ["expr"]
            names = set()
            for l in labels:
                for p in group[l]:
                    for f in fields:
                        names |= getattr(p, f).names
            names &= set().union(*[set(c.observables) for _, c in candidates])
            try:
                universe = _universe(candidates, names, consts)
                for l in labels:
                    for p in group[l]:
                        _instances(p, consts)
            except FvError:
                universe = None   # parameters unknown (pass --constants or --model): fall back to text
            if universe is None:
                texts = {l: sorted(_norm(" ~> ".join(getattr(p, f).source for f in fields)) for p in group[l]) for l in labels}
                if len({tuple(t) for t in texts.values()}) > 1:
                    add("unverified_equivalence", requirement=rid, kind=kind, by_candidate=texts,
                        detail="no finite domain for %s; compared by text only" % sorted(names))
                continue
            for f in fields:
                for point in universe:
                    verdicts = {l: _predicate(group[l], consts, point, f) for l in labels}
                    if len({v for v in verdicts.values()}) > 1:
                        add("semantic", requirement=rid, kind=kind, part=f.rstrip("_"),
                            witness={k: show(v) for k, v in point.items()}, by_candidate=verdicts,
                            detail="candidates disagree on this observable valuation")
                        break
    assumption_sets = {l: sorted(_norm(a["text"]) for a in c.assumptions) for l, c in candidates}
    if len({tuple(v) for v in assumption_sets.values()}) > 1:
        add("assumptions", by_candidate=assumption_sets, detail="stated assumptions differ; each one narrows the guarantee")
    return {"schema_version": 1, "kind": "fv-rules-divergence", "verdict": "AGREED" if not items else "DIVERGENT",
            "requirements_digest": reqs.digest(), "constants": {k: show(v) for k, v in sorted(consts.items())},
            "candidates": [{"label": l, "contract_id": c.id, "digest": c.digest, "path": c.path} for l, c in candidates],
            "items": items, "rulings": []}


# ---- 3. model divergence -------------------------------------------------------------------
def model_divergence(candidates, max_states=200000):
    """candidates: [(label, Model)] bound to the same contract, written independently."""
    from .checker import Tracer, check
    require(len(candidates) >= MIN_CANDIDATES, "divergence needs at least %d independently generated models" % MIN_CANDIDATES)
    contract_digests = {m.contract.digest for _, m in candidates}
    require(len(contract_digests) == 1, "candidate models must be bound to the same contract")
    views, items = {}, []

    def add(item_type, **kw):
        if len(items) < MAX_ITEMS:
            items.append(dict({"id": "M%d" % (len(items) + 1), "type": item_type}, **kw))

    for label, m in candidates:
        result, g, sem = check(m, max_states=max_states, symmetry=False, keep_graph=True)
        if not result["complete"]:
            add("incomplete", candidate=label, detail="exploration truncated (%s); projections are partial" % result["truncation"])
        obs = {}
        for sid, o in enumerate(g.obs):
            obs.setdefault(ckey(tuple(sorted(o.items()))), sid)
        trans = {}
        for sid, edges in enumerate(g.edges):
            a = ckey(tuple(sorted(g.obs[sid].items())))
            for lbl, t in edges:
                b = ckey(tuple(sorted(g.obs[t].items())))
                if a != b:
                    trans.setdefault((a, b), (sid, lbl))
        views[label] = {"obs": obs, "trans": trans, "graph": g, "sem": sem,
                        "verdicts": {p["id"]: p["status"] for p in result["properties"] if p["origin"] == "contract"},
                        "result": result}
    labels = [l for l, _ in candidates]
    all_ids = sorted(set().union(*[set(v["verdicts"]) for v in views.values()]))
    for pid in all_ids:
        verdicts = {l: views[l]["verdicts"].get(pid) for l in labels}
        if len(set(verdicts.values())) > 1:
            add("verdict", property=pid, by_candidate=verdicts, detail="the candidate models disagree on whether the rule holds")
    for kind in ("obs", "trans"):
        union = set().union(*[set(views[l][kind]) for l in labels])
        diff = sorted((k for k in union if any(k not in views[l][kind] for l in labels)), key=repr)
        for key in diff[:20]:
            present = [l for l in labels if key in views[l][kind]]
            v = views[present[0]]
            tracer = Tracer(v["sem"], v["graph"])
            witness = tracer.path(v[kind][key]) if kind == "obs" else tracer.path(v[kind][key][0], extra=v[kind][key][1])
            add("reachable" if kind == "obs" else "transition", in_candidates=present,
                missing_in=[l for l in labels if l not in present],
                observed=witness[-1]["observed"], witness=[(s["action"] or {}).get("name") for s in witness[1:]],
                detail="an observer could see this %s in some candidates only" % ("state" if kind == "obs" else "step"))
        if len(diff) > 20:
            add("more", kind=kind, count=len(diff) - 20)
    return {"schema_version": 1, "kind": "fv-model-divergence", "verdict": "AGREED" if not items else "DIVERGENT",
            "contract_digest": contract_digests.pop(),
            "candidates": [{"label": l, "model_id": m.id, "digest": m.digest, "path": m.path,
                            "states": views[l]["result"]["stats"]["states"], "verdict": views[l]["result"]["verdict"]} for l, m in candidates],
            "items": items, "rulings": []}


# ---- rulings, review, adoption -------------------------------------------------------------
def load_report(path, kind):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    require(isinstance(doc, dict) and doc.get("kind") == kind and doc.get("schema_version") == 1, "%s is not an %s report" % (path, kind))
    return doc


def resolve(path, item, ruling, by, signer_kind, authorization=None):
    from .receipt import now
    p = Path(path)
    doc = json.loads(p.read_text(encoding="utf-8"))
    require(doc.get("kind") in ("fv-rules-divergence", "fv-model-divergence"), "not a divergence report")
    require(item in {i["id"] for i in doc["items"]}, "unknown item %s" % item)
    require(ruling and ruling.strip() and by and by.strip(), "a ruling needs text and --by")
    require(signer_kind in ("human", "delegated_agent"), "signer kind must be human|delegated_agent")
    require(signer_kind == "human" or (authorization and authorization.strip()), "a delegated ruling must quote the human authorization")
    doc["rulings"].append({"item": item, "ruling": ruling, "by": by, "signer_kind": signer_kind,
                           "authorization": authorization, "at": now()})
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def unresolved(report):
    ruled = {r["item"] for r in report["rulings"]
             if r.get("signer_kind") == "human" or (r.get("signer_kind") == "delegated_agent" and r.get("authorization"))}
    return [i["id"] for i in report["items"] if i["id"] not in ruled]


def candidate_path(report_path, candidate):
    p = Path(candidate.get("path") or "")
    return p if p.is_absolute() else Path(report_path).resolve().parent / p


def _candidates_current(report_path, report, load):
    """Every compared candidate is kept, unchanged, next to the report."""
    issues = []
    for c in report["candidates"]:
        p = candidate_path(report_path, c)
        if not c.get("path") or not p.is_file():
            issues.append("candidate %s is gone (%s); candidates are part of the record" % (c["label"], c.get("path")))
        elif load(p).digest != c["digest"]:
            issues.append("candidate %s changed after the divergence was computed" % c["label"])
    return issues


def rules_evidence(contract, reqs, divergence_path, review_path, intake_path=None, triage_path=None, upstream=None):
    from .methods import check_intake, check_review
    from .spec import load_contract
    reasons = []
    if upstream is not None:
        up = upstream.verify()
        reasons += ["upstream: " + i for i in up["issues"]]
    trace = trace_rules(contract, reqs)
    reasons += ["traceability: " + i for i in trace["issues"]]
    intake = None
    if not intake_path:
        reasons.append("no rules intake (Spec Kit clarify + Quint from-requirements): the generators had no checked reading of the requirements")
    else:
        intake = check_intake(intake_path, reqs, upstream)
        reasons += ["intake: " + i for i in intake["issues"]]
        for rid in intake["high_impact_properties"]:
            if rid not in trace["coverage"]:
                reasons.append("High-impact requirement %s (from-requirements scoring) is not formalized by any property" % rid)
    report = load_report(divergence_path, "fv-rules-divergence")
    distinct = {c["digest"] for c in report["candidates"]}
    if len(distinct) < MIN_CANDIDATES:
        reasons.append("fewer than %d distinct independently generated rule candidates" % MIN_CANDIDATES)
    if report["requirements_digest"] != reqs.digest():
        reasons.append("divergence was computed against another requirement inventory")
    if contract.digest not in distinct:
        reasons.append("the adopted contract was not among the compared candidates; include it and recompute the divergence")
    reasons += _candidates_current(divergence_path, report, load_contract)
    open_items = unresolved(report)
    if open_items:
        reasons.append("divergence items without a ruling: %s" % open_items)
    review = check_review(review_path, contract, reqs, upstream, triage_path)
    reasons += ["review: " + i for i in review["issues"]]
    return {"verdict": "READY" if not reasons else "NOT_READY", "reasons": reasons, "trace": trace, "intake": intake,
            "divergence": {"digest": sha_bytes(Path(divergence_path).read_bytes()), "verdict": report["verdict"],
                           "items": len(report["items"]), "candidates": len(distinct), "unresolved": open_items},
            "review": review, "kind": "rules", "upstream": upstream.verify()["digest"] if upstream is not None else None}


def model_evidence(model, divergence_path, entrance="spec-first", calibration=None, review_path=None, brief=None, upstream=None):
    """brief: {"brief": modeling-brief.md, "ledger": defect-ledger.json, "coverage": brief-coverage.yaml} (code-first)."""
    from .methods import check_brief, check_handoff, check_model_review
    from .receipt import load as load_receipt, validate
    from .spec import load_model
    reasons = []
    if upstream is not None:
        reasons += ["upstream: " + i for i in upstream.verify()["issues"]]
    report = load_report(divergence_path, "fv-model-divergence")
    distinct = {c["digest"] for c in report["candidates"]}
    if len(distinct) < MIN_CANDIDATES:
        reasons.append("fewer than %d distinct independently generated model candidates" % MIN_CANDIDATES)
    if report["contract_digest"] != model.contract.digest:
        reasons.append("model divergence was computed against another contract")
    if model.digest not in distinct:
        reasons.append("the adopted model was not among the compared candidates; include it and recompute the divergence")
    reasons += _candidates_current(divergence_path, report, lambda p: load_model(p, contract=model.contract))
    open_items = unresolved(report)
    if open_items:
        reasons.append("divergence items without a ruling: %s" % open_items)
    cal = None
    if entrance == "code-first":
        if not calibration:
            reasons.append("code-first: the as-is model must be calibrated against traces of the current code before its counterexamples count")
        else:
            try:
                r = load_receipt(calibration)
                validate(r, contract=model.contract, expect_verdicts=["CONFORMS"], min_level="E3")
                cal = {"receipt": str(calibration), "digest": sha_bytes(Path(calibration).read_bytes()),
                       "model_digest": r["inputs"]["model"]["digest"], "head": r["result"]["source"].get("head")}
                if cal["model_digest"] not in distinct:
                    reasons.append("calibration was done on a model that is not one of the compared candidates")
            except (FvError, OSError, KeyError) as error:
                reasons.append("calibration receipt rejected: %s" % error)
    elif entrance != "spec-first":
        raise FvError("entrance must be spec-first|code-first")
    for c in report["candidates"]:
        reasons += ["handoff: " + i for i in check_handoff(candidate_path(divergence_path, c).parent / "notes.md")]
    review = None
    if not review_path:
        reasons.append("no model review (Quint review checks + Specula granularity audit by a fresh reviewer)")
    else:
        review = check_model_review(review_path, model, upstream, entrance)
        reasons += ["model review: " + i for i in review["issues"]]
    analysis = None
    if entrance == "code-first":
        if not (brief and brief.get("brief") and brief.get("ledger") and brief.get("coverage")):
            reasons.append("code-first: the Specula modeling brief, defect-ledger.json and brief coverage are required "
                           "(the model is built from a checked code analysis, not from a skim)")
        else:
            analysis = check_brief(brief["brief"], brief["ledger"], brief["coverage"], model, upstream)
            reasons += ["modeling brief: " + i for i in analysis["issues"]]
    return {"verdict": "READY" if not reasons else "NOT_READY", "reasons": reasons, "kind": "model", "entrance": entrance,
            "divergence": {"digest": sha_bytes(Path(divergence_path).read_bytes()), "verdict": report["verdict"],
                           "items": len(report["items"]), "candidates": len(distinct), "unresolved": open_items},
            "calibration": cal, "review": review, "analysis": analysis,
            "upstream": upstream.verify()["digest"] if upstream is not None else None}
