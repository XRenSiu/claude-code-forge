"""fv — command line for fvkit. Every result is local_advisory evidence.

Exit codes: 0 success (PASS / QUALIFIED / CONFORMS / FRESH / NOT_WEAKENED / valid)
            1 negative verdict (counterexample, not qualified, nonconformant, stale, weakened)
            2 usage, input or evaluation error
            3 inconclusive (bounded, incomplete, unknown) — never reported as success
"""
import argparse
import json
import sys
from pathlib import Path

from . import VERSION
from .values import FvError, require

EXIT = {"PASS": 0, "QUALIFIED": 0, "CONFORMS": 0, "FRESH": 0, "NOT_WEAKENED": 0, "SATISFIED": 0, "APPROVED": 0,
        "FAIL": 1, "NOT_QUALIFIED": 1, "NONCONFORMANT": 1, "STALE": 1, "BROKEN": 1, "WEAKENED": 1, "UNSATISFIED": 1,
        "ERROR": 2, "BOUNDED_PASS": 3, "INCOMPLETE": 3, "UNKNOWN": 3, "NO_VIOLATION_SAMPLED": 3}


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def _model(args):
    from .spec import load_contract, load_model
    contract = load_contract(args.contract) if getattr(args, "contract", None) else None
    return load_model(args.model, contract=contract)


def _inputs(model, extra=None):
    out = {"model": dict(model.identity(), path=model.path), "contract": dict(model.contract.identity(), path=model.contract.path)}
    out.update(extra or {})
    return out


def _save(args, receipt):
    if getattr(args, "out", None):
        from .receipt import write
        receipt_path = write(args.out, receipt)
        return receipt_path
    return None


def _summary_check(result):
    lines = []
    for p in result["properties"]:
        lines.append({"id": p["id"], "kind": p["kind"], "origin": p["origin"], "status": p["status"],
                      **({"vacuous": True} if p.get("vacuous") else {}), **({"reason": p["reason"]} if p.get("reason") else {})})
    return lines


def pretty_counterexample(ce):
    if not ce:
        return []
    out = []
    steps = ce.get("steps") or (ce.get("prefix", []) + ce.get("cycle", []))
    for s in steps:
        act = s["action"]
        name = "INIT" if act is None else act["name"] + ("(%s)" % ", ".join("%s=%s" % kv for kv in act["params"].items()) if act["params"] else "")
        out.append("%2d. %-28s %s" % (s["step"], name, json.dumps(s["observed"], ensure_ascii=False, sort_keys=True)))
    if ce.get("kind") == "lasso":
        out.append("    ... then %s forever (back to step %d)" % ("stutters" if ce["stutter"] else "repeats the cycle", ce["loop_to_step"]))
    return out


def cmd_lint(args):
    from .spec import load_contract
    if args.model:
        m = _model(args)
        emit({"ok": True, "model": m.identity(), "contract": m.contract.identity(), "actions": [a.name for a in m.actions],
              "variables": m.variables, "mutants": [x.get("id") for x in m.mutants], "evidence_level": "E0"})
    else:
        require(args.contract, "lint needs --model or --contract")
        c = load_contract(args.contract)
        emit({"ok": True, "contract": c.identity(), "evidence_level": "E0"})
    return 0


def cmd_check(args):
    from .checker import check
    from .receipt import make, now
    started = now()
    m = _model(args)
    result, _, _ = check(m, max_states=args.max_states, max_depth=args.max_depth, time_seconds=args.time,
                         symmetry=not args.no_symmetry, stop_on_first=args.stop_on_first)
    receipt = make("check", _inputs(m), result["settings"], result, result["verdict"], "E2", started)
    path = _save(args, receipt)
    failing = [p for p in result["properties"] if p["status"] == "FAIL"]
    if result["deadlock"]["status"] == "FAIL":
        failing.append({"id": "deadlock", "counterexample": result["deadlock"]["counterexample"]})
    emit({"verdict": result["verdict"], "complete": result["complete"], "exhaustive_depth": result["exhaustive_depth"],
          "truncation": result["truncation"], "stats": result["stats"], "properties": _summary_check(result),
          "dead_actions": result["coverage"]["dead_actions"], "notes": result["notes"], "error": result["error"],
          "receipt": path, "evidence_level": "E2", "may_not_claim": receipt["claims"]["may_not_claim"],
          "counterexamples": {p["id"]: pretty_counterexample(p["counterexample"]) for p in failing[:5]}})
    return EXIT[result["verdict"]]


def cmd_simulate(args):
    from .receipt import make, now
    from .simulate import simulate
    started = now()
    m = _model(args)
    result = simulate(m, seed=args.seed, runs=args.runs, depth=args.depth, time_seconds=args.time)
    receipt = make("simulate", _inputs(m), {"seed": args.seed, "runs": args.runs, "depth": args.depth}, result, result["verdict"], "E1", started)
    path = _save(args, receipt)
    emit({"verdict": result["verdict"], "receipt": path, "evidence_level": "E1",
          "note": "simulation samples behaviours; it never proves absence of violations",
          "violation": result["violation"] and {"property": result["violation"]["property"],
                                                 "trace": pretty_counterexample(result["violation"]["counterexample"])}})
    return EXIT[result["verdict"]]


def cmd_mutate(args):
    from .mutate import run_mutants
    from .receipt import make, now
    started = now()
    m = _model(args)
    settings = {k: v for k, v in (("max_states", args.max_states), ("time_seconds", args.time)) if v is not None}
    result = run_mutants(m, auto=args.auto, settings=settings)
    ok = not result["declared_summary"]["required_survivors"] and result["declared"]
    verdict = "PASS" if ok else "FAIL"
    receipt = make("mutate", _inputs(m), dict(settings, auto=args.auto), result, verdict, "E2", started)
    path = _save(args, receipt)
    emit({"verdict": verdict, "receipt": path, "declared": [{k: r.get(k) for k in ("id", "status", "killed_by", "reason")} for r in result["declared"]],
          "auto": result.get("auto_summary")})
    return 0 if ok else 1


def cmd_qualify(args):
    from .qualify import qualify
    from .receipt import make, now
    started = now()
    m = _model(args)
    settings = {"max_states": args.max_states, "time_seconds": args.time, "allow_bounded": args.allow_bounded,
                "min_depth": args.min_depth, "auto_mutants": args.auto_mutants, "symmetry": not args.no_symmetry}
    q = qualify(m, settings)
    receipt = make("qualify", _inputs(m), q["settings"], q["result"], q["verdict"], "E2", started)
    path = _save(args, receipt)
    emit({"verdict": q["verdict"], "reasons": q["result"]["reasons"], "check": q["result"]["check"]["verdict"],
          "states": q["result"]["check"]["stats"]["states"],
          "mutants": [{k: r.get(k) for k in ("id", "status", "killed_by")} for r in q["result"]["mutants"]["declared"]],
          "auto_mutants": q["result"]["mutants"].get("auto_summary"), "receipt": path, "evidence_level": "E2"})
    return EXIT[q["verdict"]]


def cmd_diff(args):
    from .contract_diff import diff, sample_universe
    from .policy import approved
    from .spec import load_contract, load_model
    old, new = load_contract(args.old), load_contract(args.new)
    consts, sample = {}, None
    if args.model:
        m = load_model(args.model, contract=new)
        consts = m.constants
        sample = sample_universe(m)
    result = diff(old, new, consts, sample)
    if result["verdict"] == "WEAKENED" and args.approvals:
        rec = approved(args.approvals, new.digest)
        if rec:
            result["approval"] = rec
            result["verdict"] = "APPROVED"
    emit(result)
    return EXIT[result["verdict"]]


def cmd_approve(args):
    from .policy import approve
    from .spec import load_contract
    c = load_contract(args.contract)
    prev = load_contract(args.previous).digest if args.previous else None
    rec = approve(args.approvals, c, args.by, args.reason, args.signer_kind, args.authorization, prev)
    emit({"ok": True, "approval": rec})
    return 0


def cmd_trace(args):
    from .receipt import make, now
    from .trace import check_files
    started = now()
    m = _model(args)
    result = check_files(m, args.traces, hidden_steps=args.hidden_steps, max_candidates=args.max_candidates)
    receipt = make("trace", _inputs(m), {"hidden_steps": args.hidden_steps, "max_candidates": args.max_candidates}, result, result["verdict"], "E3", started)
    path = _save(args, receipt)
    emit({"verdict": result["verdict"], "receipt": path, "evidence_level": "E3",
          "traces": [{"path": t["trace"]["path"], "verdict": t["verdict"], "failed_at_line": t["failed_at_line"],
                      "reason": t["reason"], "property_violations": t["property_violations"],
                      **({"diagnostic": t["diagnostic"]} if t.get("diagnostic") else {})} for t in result["traces"]]})
    return EXIT[result["verdict"]]


def _counterexample_steps(path):
    from .spec import load_document
    doc = load_document(path)
    if doc.get("kind") == "fv-receipt":
        res = doc["result"].get("check", doc["result"])
        out = []
        for p in res.get("properties", []):
            ce = p.get("counterexample")
            if p["status"] == "FAIL" and ce and ce.get("steps"):
                out.append((Path(path).stem + ":" + p["id"], ce["steps"]))
        if not out and res.get("violation"):
            out.append((Path(path).stem + ":" + res["violation"]["property"], res["violation"]["counterexample"]["steps"]))
        require(out, "%s holds no safety counterexample to replay" % path)
        return out
    require(isinstance(doc.get("steps"), list), "%s: expected a receipt or {id, steps}" % path)
    return [(doc.get("id") or Path(path).stem, doc["steps"])]


def cmd_gen_tests(args):
    from .mbt import build
    m = _model(args)
    ces = []
    for p in args.counterexample or []:
        ces += _counterexample_steps(p)
    strategies = [s.strip() for s in args.strategy.split(",") if s.strip()]
    if "counterexamples" in strategies:
        require(ces, "--strategy counterexamples needs --counterexample <receipt|json>")
    doc = build(m, strategies, ces, seed=args.seed, count=args.count, length=args.length, max_states=args.max_states)
    out = Path(args.out)
    require(not out.exists(), "output exists; vectors are never overwritten: %s" % out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    emit({"ok": True, "vectors": len(doc["vectors"]), "out": str(out), "notes": doc["notes"],
          "refused_steps": sum(1 for v in doc["vectors"] for s in v["steps"] if not s["enabled"])})
    return 0


def cmd_source_map(args):
    from .sourcemap import sync, verify
    m = _model(args)
    if args.action == "verify":
        r = verify(args.map, m, args.root)
        emit({k: r[k] for k in ("status", "issues", "drifted_files", "stale", "map_digest", "model_digest")})
        return EXIT[r["status"]]
    lock = sync(args.map, m, args.by, args.reason, args.signer_kind, args.authorization, args.root)
    emit({"ok": True, "lock": lock})
    return 0


def source_binding(root, sm):
    from .sourcemap import git
    head = git(root, "rev-parse", "HEAD", check=False).stdout.strip() or None
    return {"head": head, "files": sm["files"] if sm else {}}


def cmd_conform(args):
    from .qualify import conform
    from .receipt import make, now
    from .sourcemap import repo_root, verify
    from .trace import check_files
    started = now()
    m = _model(args)
    sm = verify(args.map, m, args.root) if args.map else None
    traces = check_files(m, args.traces, hidden_steps=args.hidden_steps) if args.traces else {"verdict": "INCOMPLETE", "traces": []}
    c = conform(m, sm, traces, args.replay)
    root = Path(args.root) if args.root else repo_root(Path(args.map or args.model).resolve().parent)
    result = {"source_map": sm and {k: sm[k] for k in ("status", "issues", "drifted_files", "stale", "files", "map_digest")},
              "traces": traces, "reasons": c["reasons"], "source": source_binding(root, sm), "replays": args.replay or []}
    receipt = make("conform", _inputs(m), {"hidden_steps": args.hidden_steps}, result, c["verdict"], "E3", started)
    path = _save(args, receipt)
    emit({"verdict": c["verdict"], "reasons": c["reasons"], "source": result["source"]["head"], "receipt": path, "evidence_level": "E3"})
    return EXIT[c["verdict"]]


def cmd_impact(args):
    from .policy import impact, load_policy
    from .sourcemap import repo_root
    pol = load_policy(args.policy)
    root = Path(args.root).resolve() if args.root else repo_root(Path(args.policy).resolve().parent)
    emit(impact(pol, root, args.base))
    return 0


def cmd_ci(args):
    from .ci import run_ci
    result = run_ci(args.policy, args.base, args.out, tier=args.tier, all_modules=args.all, root=args.root)
    emit(result)
    return EXIT[result["verdict"]]


def cmd_external(args):
    from .external import run
    from .receipt import write
    receipt = run(args.engine, args.spec, args.out, tool=args.tool, config=args.config, invariants=args.invariant or [],
                  bound=args.bound, samples=args.samples, seed=args.seed, timeout=args.timeout)
    path = write(Path(args.out) / "receipt.json", receipt)
    emit({"verdict": receipt["verdict"], "evidence_level": receipt["evidence_level"], "receipt": path,
          "parsed": receipt["result"]["parsed"], "error": receipt["result"]["error"]})
    return EXIT.get(receipt["verdict"], 2)


def cmd_validate(args):
    from .receipt import load, validate
    from .spec import load_contract, load_model
    r = load(args.receipt)
    contract = load_contract(args.contract) if args.contract else None
    model = load_model(args.model, contract=contract) if args.model else None
    if model is not None and contract is None:
        contract = model.contract
    out = validate(r, model=model, contract=contract, rerun=args.rerun, min_level=args.min_level,
                   expect_verdicts=args.expect, base_dir=str(Path(args.receipt).resolve().parent))
    emit(out)
    return 0


def cmd_report(args):
    from .receipt import CLAIMS, load
    lines = ["# Formal verification evidence", "", "| receipt | command | verdict | level | may claim | may NOT claim |",
             "|---|---|---|---|---|---|"]
    for p in args.receipts:
        r = load(p)
        lines.append("| %s | %s | %s | %s | %s | %s |" % (Path(p).name, r["command"], r["verdict"], r["evidence_level"],
                                                       r["claims"]["may_claim"] or "—", r["claims"]["may_not_claim"]))
    lines += ["", "Evidence levels:", ""] + ["- **%s**: may claim %s; may not claim %s." % (k, v[0], v[1]) for k, v in CLAIMS.items()]
    lines += ["", "All fvkit receipts are `local_advisory`: integrity evidence, not authenticated acceptance."]
    print("\n".join(lines))
    return 0


def cmd_init(args):
    from .scaffold import init
    emit({"ok": True, "written": init(args.dir, args.name, args.entrance)})
    return 0


def cmd_vendor(args):
    from .scaffold import vendor
    emit({"ok": True, "vendored": vendor(args.to)})
    return 0


def parser():
    p = argparse.ArgumentParser(prog="fv", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version="fvkit " + VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)

    def model_args(s, required=True):
        s.add_argument("--model", required=required)
        s.add_argument("--contract", help="defaults to the model's `contract:` reference")

    s = sub.add_parser("lint", help="static checks of a contract and/or model (E0)")
    model_args(s, required=False)
    s.set_defaults(fn=cmd_lint)
    s = sub.add_parser("check", help="exhaustive model check (E2)")
    model_args(s)
    s.add_argument("--max-states", type=int); s.add_argument("--max-depth", type=int); s.add_argument("--time", type=int)
    s.add_argument("--no-symmetry", action="store_true"); s.add_argument("--stop-on-first", action="store_true")
    s.add_argument("--out", help="new receipt path (never overwritten)")
    s.set_defaults(fn=cmd_check)
    s = sub.add_parser("simulate", help="seeded random simulation (E1, never PASS)")
    model_args(s)
    s.add_argument("--seed", type=int, default=1); s.add_argument("--runs", type=int, default=200)
    s.add_argument("--depth", type=int, default=50); s.add_argument("--time", type=int); s.add_argument("--out")
    s.set_defaults(fn=cmd_simulate)
    s = sub.add_parser("mutate", help="run declared (and --auto) mutants")
    model_args(s)
    s.add_argument("--auto", action="store_true"); s.add_argument("--max-states", type=int); s.add_argument("--time", type=int); s.add_argument("--out")
    s.set_defaults(fn=cmd_mutate)
    s = sub.add_parser("qualify", help="design gate: complete check + witnesses + coverage + killed mutants")
    model_args(s)
    s.add_argument("--max-states", type=int); s.add_argument("--time", type=int)
    s.add_argument("--allow-bounded", action="store_true"); s.add_argument("--min-depth", type=int)
    s.add_argument("--auto-mutants", action="store_true"); s.add_argument("--no-symmetry", action="store_true"); s.add_argument("--out")
    s.set_defaults(fn=cmd_qualify)
    s = sub.add_parser("diff-contract", help="detect weakened rules between two contract versions")
    s.add_argument("old"); s.add_argument("new"); s.add_argument("--model", help="model of the NEW contract (constants, sampling)")
    s.add_argument("--approvals", help="approvals JSONL; an approval of the new digest turns WEAKENED into APPROVED")
    s.set_defaults(fn=cmd_diff)
    s = sub.add_parser("approve", help="record an explicit approval of a contract digest (append-only)")
    s.add_argument("--contract", required=True); s.add_argument("--approvals", required=True)
    s.add_argument("--by", required=True); s.add_argument("--reason", required=True)
    s.add_argument("--signer-kind", choices=["human", "delegated_agent"], required=True); s.add_argument("--authorization")
    s.add_argument("--previous", help="the contract version this one replaces")
    s.set_defaults(fn=cmd_approve)
    s = sub.add_parser("trace-check", help="check implementation traces against the model (E3)")
    model_args(s)
    s.add_argument("traces", nargs="+"); s.add_argument("--hidden-steps", type=int, default=0)
    s.add_argument("--max-candidates", type=int, default=10000); s.add_argument("--out")
    s.set_defaults(fn=cmd_trace)
    s = sub.add_parser("gen-tests", help="model-based test vectors for the real implementation")
    model_args(s)
    s.add_argument("--strategy", default="transitions"); s.add_argument("--counterexample", action="append")
    s.add_argument("--seed", type=int, default=1); s.add_argument("--count", type=int, default=8); s.add_argument("--length", type=int, default=12)
    s.add_argument("--max-states", type=int); s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_gen_tests)
    s = sub.add_parser("source-map", help="verify or (after review) sync the model<->code mapping")
    s.add_argument("action", choices=["verify", "sync"]); model_args(s)
    s.add_argument("--map", required=True); s.add_argument("--root")
    s.add_argument("--by"); s.add_argument("--reason"); s.add_argument("--signer-kind", choices=["human", "delegated_agent"], default="human")
    s.add_argument("--authorization")
    s.set_defaults(fn=cmd_source_map)
    s = sub.add_parser("conform", help="implementation gate: fresh source map + conforming traces (E3)")
    model_args(s)
    s.add_argument("--map"); s.add_argument("--traces", nargs="*"); s.add_argument("--replay", action="append",
                   help="vector id of a counterexample regression that must have a conforming trace")
    s.add_argument("--hidden-steps", type=int, default=0); s.add_argument("--root"); s.add_argument("--out")
    s.set_defaults(fn=cmd_conform)
    s = sub.add_parser("impact", help="which formally verified modules a change touches")
    s.add_argument("--policy", required=True); s.add_argument("--base"); s.add_argument("--root")
    s.set_defaults(fn=cmd_impact)
    s = sub.add_parser("ci", help="tiered verification of impacted modules; writes receipts")
    s.add_argument("--policy", required=True); s.add_argument("--base"); s.add_argument("--out", required=True)
    s.add_argument("--tier", default="auto", choices=["auto", "fast", "core", "deep"]); s.add_argument("--all", action="store_true")
    s.add_argument("--root")
    s.set_defaults(fn=cmd_ci)
    s = sub.add_parser("external", help="run TLC / Apalache / Quint / FizzBee and keep raw evidence")
    s.add_argument("--engine", required=True, choices=["tlc", "apalache", "quint-verify", "quint-run", "fizzbee"])
    s.add_argument("--spec", action="append", required=True); s.add_argument("--config"); s.add_argument("--tool")
    s.add_argument("--invariant", action="append"); s.add_argument("--bound", type=int); s.add_argument("--samples", type=int)
    s.add_argument("--seed", type=int); s.add_argument("--timeout", type=int, default=600); s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_external)
    s = sub.add_parser("validate", help="re-verify a receipt (digests, verdict, counterexample replay, --rerun)")
    s.add_argument("receipt"); s.add_argument("--model"); s.add_argument("--contract"); s.add_argument("--rerun", action="store_true")
    s.add_argument("--min-level", choices=["E0", "E1", "E2", "E3", "E4"]); s.add_argument("--expect", action="append")
    s.set_defaults(fn=cmd_validate)
    s = sub.add_parser("report", help="markdown summary with what each receipt may and may not claim")
    s.add_argument("receipts", nargs="+")
    s.set_defaults(fn=cmd_report)
    s = sub.add_parser("init", help="scaffold project assets for entrance A (spec-first) or B (code-first)")
    s.add_argument("--dir", required=True); s.add_argument("--name", required=True)
    s.add_argument("--entrance", choices=["spec-first", "code-first"], required=True)
    s.set_defaults(fn=cmd_init)
    s = sub.add_parser("vendor", help="copy this engine into a project (self-contained CI)")
    s.add_argument("--to", required=True)
    s.set_defaults(fn=cmd_vendor)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return args.fn(args)
    except FvError as error:
        print(json.dumps({"error": str(error), "authority": "local_advisory"}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"error": "%s: %s" % (type(error).__name__, error)}, ensure_ascii=False), file=sys.stderr)
        return 2
