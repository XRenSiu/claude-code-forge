"""Formal-verification preconditions of the AI-DLC lifecycle (fvkit receipts; see /formal-verify).

What is enforced, and where (never waivable with `advance --force`):
  cards / implement / later   the fv-contract is frozen by the current G2/L5 lock (same bytes)
  implement / later           a QUALIFIED qualification receipt for exactly the current model and
                              contract (re-validated: digests, verdict, counterexample replay)
  pr / merge / release (E3)   a CONFORMS receipt whose mapped source files are still the ones on disk,
                              and a source map that is FRESH right now
Which modules are required is explicit (`formal configure --module`) or derived from git: with a
policy, `fv impact` against branch.base decides; without a base every policy module is required.
A human-signed `formal waive` lowers one module's level; it is recorded and forces G3.
These are local preconditions over files; the protected control service re-checks independently.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FV_SCRIPTS = Path(__file__).resolve().parents[2] / "formal-verify" / "scripts"
sys.path.insert(0, str(FV_SCRIPTS))
from fvkit.policy import impact, load_policy  # noqa: E402
from fvkit.receipt import LEVELS, level_at_least, load as load_receipt, make, validate, write  # noqa: E402
from fvkit.sourcemap import verify as verify_map  # noqa: E402
from fvkit.spec import load_contract, load_model  # noqa: E402
from fvkit.values import FvError, sha_bytes  # noqa: E402

STAGE_ORDER = ["cards", "implement", "acceptance", "pr", "review", "g3", "merge", "release", "archive"]


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _repo():
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if out.returncode != 0:
        raise FvError("formal verification needs a git repository")
    return Path(out.stdout.strip()).resolve()


def _rel(path, root):
    p = Path(path).resolve()
    if not (p == root or root in p.parents):
        raise FvError("formal assets must live inside the repository: %s" % path)
    return str(p.relative_to(root))


def _file_digest(path):
    return sha_bytes(Path(path).read_bytes())


def ensure(st):
    st.setdefault("formal", {"status": "not_configured", "modules": {}, "policy": None,
                             "qualification": {}, "conformance": {}, "waivers": []})
    return st["formal"]


def configure(st, module=None, contract=None, model=None, source_map=None, min_level="E3", policy=None, settings=None):
    f = ensure(st)
    root = _repo()
    if policy:
        pol = load_policy(policy)  # validates the policy (and the per-risk evidence requirements)
        f["policy"] = {"path": _rel(policy, root), "digest": _file_digest(policy), "modules": [m["id"] for m in pol["modules"]]}
    if module:
        if not (contract and model):
            raise FvError("--module needs --contract and --model")
        if min_level not in ("E2", "E3"):
            raise FvError("--min-level must be E2 or E3 (use `formal waive` to go lower, with a signature)")
        if min_level == "E3" and not source_map:
            raise FvError("E3 needs --source-map: implementation evidence must be tied to code")
        m = load_model(model, contract=load_contract(contract))  # lint now, not at the gate
        f["modules"][module] = {"contract": _rel(contract, root), "model": _rel(model, root),
                                "source_map": _rel(source_map, root) if source_map else None,
                                "min_level": min_level, "origin": "explicit", "model_id": m.id}
    if settings:
        f["settings"] = settings
    if not f["modules"] and not f["policy"]:
        raise FvError("configure a --policy or at least one --module")
    f["status"] = "configured"
    return f


def required(st):
    """{module_id: spec} that this change must satisfy (explicit modules + policy impact)."""
    f = st.get("formal") or {}
    if f.get("status") != "configured":
        return {}
    root = _repo()
    out = {k: dict(v) for k, v in f["modules"].items()}
    if f.get("policy"):
        ppath = root / f["policy"]["path"]
        if _file_digest(ppath) != f["policy"]["digest"]:
            raise FvError("verification policy changed during the run; policy cannot drift mid-task")
        pol = load_policy(ppath)
        base = (st.get("branch") or {}).get("base")
        hit = {m["id"] for m in impact(pol, root, base)["modules"]} if base else {m["id"] for m in pol["modules"]}
        for m in pol["modules"]:
            if m["id"] not in hit or m["id"] in out:
                continue
            level = pol["risks"][m["risk"]]["min_level"]
            if not level_at_least(level, "E2"):
                continue
            out[m["id"]] = {"contract": m["contract"], "model": m["model"], "source_map": m.get("source_map"),
                            "min_level": level, "origin": "policy" if base else "policy (no branch.base: all modules)"}
    for w in f.get("waivers", []):
        if w["module"] in out:
            out[w["module"]]["min_level"] = w["level"]
            out[w["module"]]["waived_by"] = w["by"]
    return out


def _load(spec):
    root = _repo()
    contract = load_contract(root / spec["contract"])
    return root, contract, load_model(root / spec["model"], contract=contract)


def _lock_issues(st, mid, spec, root):
    lp = (st.get("lock") or {}).get("path")
    if not lp or not os.path.isfile(lp):
        return ["%s: no G2 lock yet — the fv-contract is signed together with done_when.yaml" % mid]
    try:
        lock = json.load(open(lp, encoding="utf-8"))
    except ValueError:
        return ["%s: lock file unreadable" % mid]
    target = (root / spec["contract"]).resolve()
    entries = [e for e in lock.get("files", []) if Path(e["path"]).resolve() == target]
    if not entries:
        return ["%s: fv-contract %s is not in the %s lock — re-sign with it (`lock_done_when.py sign … %s`)"
                % (mid, spec["contract"], lock.get("stage", "?"), spec["contract"])]
    if entries[0].get("sha256") != _file_digest(target)[7:]:
        return ["%s: fv-contract changed after it was locked (a weakened rule is a change proposal + G2, never a fix)" % mid]
    return []


def _qualification_issues(st, mid, contract, model):
    rec = (st["formal"].get("qualification") or {}).get(mid)
    if not rec:
        return ["%s: no qualification yet — `formal qualify --module %s`" % (mid, mid)]
    try:
        if _file_digest(rec["receipt"]) != rec["digest"]:
            return ["%s: qualification receipt changed after it was recorded" % mid]
        validate(load_receipt(rec["receipt"]), model=model, contract=contract, expect_verdicts=["QUALIFIED"], min_level="E2")
    except (FvError, OSError) as error:
        return ["%s: qualification is not current: %s" % (mid, error)]
    return []


def _conformance_issues(st, mid, spec, contract, model, root):
    rec = (st["formal"].get("conformance") or {}).get(mid)
    if not rec:
        return ["%s: E3 needs implementation evidence — `formal conform --module %s --traces …`" % (mid, mid)]
    try:
        if _file_digest(rec["receipt"]) != rec["digest"]:
            return ["%s: conformance receipt changed after it was recorded" % mid]
        receipt = load_receipt(rec["receipt"])
        validate(receipt, model=model, contract=contract, expect_verdicts=["CONFORMS"], min_level="E3")
        sm = verify_map(root / spec["source_map"], model)
        if sm["status"] != "FRESH":
            return ["%s: source map is %s now: %s" % (mid, sm["status"], "; ".join(sm["issues"] + sm["stale"]) or sm["drifted_files"])]
        if receipt["result"]["source"]["files"] != sm["files"]:
            return ["%s: mapped code changed since the conformance traces were taken — rerun the harness and `formal conform`" % mid]
    except (FvError, OSError, KeyError) as error:
        return ["%s: conformance is not current: %s" % (mid, error)]
    return []


def guard(st, target):
    """Unmet formal preconditions for advancing to `target` (empty = nothing required or all met)."""
    f = st.get("formal") or {}
    if f.get("status") != "configured" or target not in STAGE_ORDER:
        return []
    try:
        mods = required(st)
    except (FvError, OSError) as error:
        return ["formal policy: %s" % error]
    issues = []
    for mid, spec in sorted(mods.items()):
        level = spec["min_level"]
        if not level_at_least(level, "E2"):
            continue
        try:
            root, contract, model = _load(spec)
        except (FvError, OSError) as error:
            issues.append("%s: contract/model do not load: %s" % (mid, error))
            continue
        issues += _lock_issues(st, mid, spec, root)
        if target != "cards":
            issues += _qualification_issues(st, mid, contract, model)
        if level_at_least(level, "E3") and STAGE_ORDER.index(target) >= STAGE_ORDER.index("pr"):
            issues += _conformance_issues(st, mid, spec, contract, model, root)
    return issues


def _out_dir(root_dir, slug, label):
    d = Path(root_dir) / slug / "formal"
    d.mkdir(parents=True, exist_ok=True)
    return d / ("%s-%s.json" % (label, datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")))


def _module(st, mid):
    mods = required(st)
    if mid is None:
        if len(mods) != 1:
            raise FvError("several formal modules are required (%s); pass --module" % sorted(mods))
        mid = next(iter(mods))
    if mid not in mods:
        raise FvError("module %s is not required for this change (required: %s)" % (mid, sorted(mods)))
    return mid, mods[mid]


def qualify_module(st, aidlc_root, slug, mid=None):
    from fvkit.qualify import qualify
    mid, spec = _module(st, mid)
    root, contract, model = _load(spec)
    started = now()
    settings = dict(st["formal"].get("settings") or {})
    q = qualify(model, settings)
    receipt = make("qualify", {"model": dict(model.identity(), path=spec["model"]), "contract": dict(contract.identity(), path=spec["contract"])},
                   q["settings"], q["result"], q["verdict"], "E2", started)
    path = write(_out_dir(aidlc_root, slug, "qualify-" + mid), receipt)
    st["formal"]["qualification"][mid] = {"receipt": str(Path(path).resolve()), "digest": _file_digest(path), "verdict": q["verdict"],
                                          "model_digest": model.digest, "contract_digest": contract.digest, "at": started}
    st.setdefault("artifacts", {})["formal.qualify." + mid] = str(Path(path).resolve())
    return {"module": mid, "verdict": q["verdict"], "reasons": q["result"]["reasons"], "receipt": path}


def conform_module(st, aidlc_root, slug, traces, mid=None, hidden_steps=0):
    from fvkit.qualify import conform
    from fvkit.trace import check_files
    mid, spec = _module(st, mid)
    if not spec.get("source_map"):
        raise FvError("module %s has no source map; E3 evidence must be tied to code" % mid)
    root, contract, model = _load(spec)
    started = now()
    sm = verify_map(root / spec["source_map"], model)
    tr = check_files(model, traces, hidden_steps=hidden_steps) if traces else {"verdict": "INCOMPLETE", "traces": []}
    c = conform(model, sm, tr)
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() or None
    result = {"source_map": {k: sm[k] for k in ("status", "issues", "drifted_files", "stale", "files", "map_digest")},
              "traces": tr, "reasons": c["reasons"], "source": {"head": head, "files": sm["files"]}, "replays": []}
    receipt = make("conform", {"model": dict(model.identity(), path=spec["model"]), "contract": dict(contract.identity(), path=spec["contract"])},
                   {"hidden_steps": hidden_steps}, result, c["verdict"], "E3", started)
    path = write(_out_dir(aidlc_root, slug, "conform-" + mid), receipt)
    st["formal"]["conformance"][mid] = {"receipt": str(Path(path).resolve()), "digest": _file_digest(path), "verdict": c["verdict"],
                                        "head": head, "at": started}
    st.setdefault("artifacts", {})["formal.conform." + mid] = str(Path(path).resolve())
    return {"module": mid, "verdict": c["verdict"], "reasons": c["reasons"], "receipt": path}


def waive(st, mid, level, reason, by, signer_kind, authorization=None):
    if level not in LEVELS[:3]:
        raise FvError("a waiver lowers the requirement to E0, E1 or E2")
    if not (reason and reason.strip() and by and by.strip()):
        raise FvError("a waiver needs --reason and --by")
    if signer_kind == "delegated_agent" and not (authorization and authorization.strip()):
        raise FvError("a delegated waiver must quote the human authorization")
    rec = {"module": mid, "level": level, "reason": reason, "by": by, "signer_kind": signer_kind,
           "authorization": authorization, "at": now()}
    ensure(st)["waivers"].append(rec)
    st.setdefault("gates", {}).setdefault("g3", {})["required"] = True   # an exception is reviewed at G3
    return rec


def status(st):
    f = st.get("formal") or {}
    if f.get("status") != "configured":
        return {"status": "not_configured"}
    out = {"status": "configured", "required": {}, "waivers": f.get("waivers", [])}
    try:
        mods = required(st)
    except (FvError, OSError) as error:
        return {"status": "error", "error": str(error)}
    for mid, spec in mods.items():
        out["required"][mid] = dict(spec, qualification=(f.get("qualification") or {}).get(mid),
                                    conformance=(f.get("conformance") or {}).get(mid))
    out["unmet_for"] = {t: guard(st, t) for t in ("implement", "pr")}
    return out
