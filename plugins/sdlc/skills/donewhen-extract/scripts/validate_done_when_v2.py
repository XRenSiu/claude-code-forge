#!/usr/bin/env python3
"""
validate_done_when_v2.py — the schema-v2 exit for the contract of record (sdlc's done_when.yaml).

v2 = v1 superset: `schema: 2` + `acceptance` (AC-first, what G2 signs) + boundary-only `existence` +
optional `behavior` (tests-manifest seed) + `rules` + `constraints` + `budgets`. This script is what
`sdlc_state.py advance g2` runs — the C1 decision ("the contract holds criteria, not test names") compiled.

Usage:
  validate_done_when_v2.py <done_when.yaml> [--spec spec.md] [--require-behavior] [--json]

Exit 0 = valid v2 (flags may remain) · 1 = REJECT · 2 = IO error.

Mechanical guarantees (REJECT):
  - schema: 2 ; feature ; based_on non-empty ; acceptance non-empty
  - every AC: id unique, req ∈ based_on (and ∈ spec.md REQ ids when --spec), kind mechanical|human
  - mechanical: observe boundary (route:|cli:|ui:|db_field:|event:|api:), given, expect present; no vague
    quantifier in expect without a number; no file path / function in observe
  - human: statement + judge ∈ {product, design, tech} + evidence ∈ {checklist, demo}
  - event/state happy AC has an unwanted sibling on the same observe or paired_with resolves to one
  - existence entries: only route / db_field / ui / cli / event / frontend_component keys (no file / function)
  - constraints.forbidden_paths (if present) contains tests/** and done_when.yaml
  - --require-behavior (L5 stage): behavior has ≥1 test name
Flags: thresholds without threshold_source; REQ in based_on with no AC; behavior empty (fine at G2).
"""
import argparse
import json
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("validate_done_when_v2.py needs PyYAML\n"); sys.exit(2)

VAGUE = ["快", "慢", "稳定", "可靠", "健壮", "高效", "及时", "尽快", "大部分", "多数", "合理", "友好", "流畅", "良好", "充分", "适当", "足够", "正确处理", "智能",
         "fast", "slow", "stable", "reliable", "robust", "quick", "soon", "most", "reasonable", "friendly", "smooth", "adequate", "sufficient", "better", "properly", "correctly"]
BOUNDARY_RE = re.compile(r"^(route|cli|ui|db_field|event|api|topic|queue):", re.I)
FILEPATH_RE = re.compile(r"(\bsrc/|\btests?/|\.(ts|tsx|js|jsx|py|go|rs|java|kt|rb|php|cs|swift|vue)\b|::|\(\))")
EXIST_KEYS = {"route", "db_field", "ui", "cli", "event", "frontend_component", "api", "topic", "queue"}
JUDGES, EVIDENCE = {"product", "design", "tech"}, {"checklist", "demo"}


def vague(s):
    s = json.dumps(s, ensure_ascii=False) if not isinstance(s, str) else s
    if re.search(r"\d", s):
        return None
    low = s.lower()
    return next((w for w in VAGUE if w in low), None)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path"); ap.add_argument("--spec"); ap.add_argument("--require-behavior", action="store_true"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        d = yaml.safe_load(open(a.path, encoding="utf-8")) or {}
    except Exception as e:
        sys.stderr.write(f"validate_done_when_v2: {e}\n"); sys.exit(2)
    rejects, flags = [], []
    if d.get("schema") != 2:
        rejects.append("schema must be 2 (v1 contracts: run convert_v1_to_v2.py, then complete `acceptance`)")
    if not d.get("feature"):
        rejects.append("feature missing")
    based = d.get("based_on") or []
    if not based:
        rejects.append("based_on empty")
    spec_reqs = None
    if a.spec:
        try:
            spec_reqs = set(re.findall(r"\bREQ-\d{3,}\b", open(a.spec, encoding="utf-8").read()))
        except OSError as e:
            sys.stderr.write(f"validate_done_when_v2: {e}\n"); sys.exit(2)
    acs = d.get("acceptance") or []
    if not acs:
        rejects.append("acceptance empty — the contract of record is AC-first (C1)")
    ids, by_obs = set(), {}
    for ac in acs:
        if not isinstance(ac, dict):
            rejects.append(f"non-mapping AC {ac!r}"); continue
        aid, req, kind = ac.get("id"), ac.get("req"), ac.get("kind")
        if not aid:
            rejects.append("AC without id"); continue
        if aid in ids:
            rejects.append(f"{aid}: duplicate id")
        ids.add(aid)
        if req not in based:
            rejects.append(f"{aid}: req {req} not in based_on")
        if spec_reqs is not None and req not in spec_reqs:
            rejects.append(f"{aid}: req {req} not in spec.md")
        if kind not in ("mechanical", "human"):
            rejects.append(f"{aid}: kind must be mechanical|human"); continue
        obs = str(ac.get("observe") or "")
        by_obs.setdefault(obs, []).append(ac)
        if kind == "mechanical":
            for k in ("observe", "given", "expect"):
                if ac.get(k) in (None, "", {}):
                    rejects.append(f"{aid}: mechanical AC needs `{k}`")
            if obs and not BOUNDARY_RE.match(obs):
                rejects.append(f"{aid}: observe `{obs}` is not a boundary")
            if obs and FILEPATH_RE.search(obs):
                rejects.append(f"{aid}: observe names implementation structure")
            w = vague(ac.get("expect"))
            if w:
                rejects.append(f"{aid}: expect contains vague `{w}` with no number")
        else:
            if not ac.get("statement"):
                rejects.append(f"{aid}: human AC needs statement")
            if ac.get("judge") not in JUDGES:
                rejects.append(f"{aid}: judge must be one of {sorted(JUDGES)}")
            if ac.get("evidence") not in EVIDENCE:
                rejects.append(f"{aid}: evidence must be one of {sorted(EVIDENCE)}")
    for ac in acs:
        if isinstance(ac, dict) and ac.get("kind") == "mechanical" and ac.get("ears_type", "event") in ("event", "state"):
            sib = [x for x in by_obs.get(str(ac.get("observe")), []) if x is not ac and x.get("ears_type") == "unwanted"]
            if not sib and ac.get("paired_with") not in ids:
                rejects.append(f"{ac.get('id')}: happy AC without an unhappy twin")
    for req in based:
        if not any(isinstance(x, dict) and x.get("req") == req for x in acs):
            flags.append(f"{req} in based_on has no AC")
    for ex in d.get("existence") or []:
        if not isinstance(ex, dict) or len(ex) != 1:
            rejects.append(f"existence entry must be a single key-value: {ex!r}"); continue
        k = next(iter(ex))
        if k not in EXIST_KEYS:
            rejects.append(f"existence key `{k}` not allowed in v2 (file/function go to cards.allowed_files) — C2")
        if FILEPATH_RE.search(str(ex[k])):
            rejects.append(f"existence `{k}: {ex[k]}` names a file/function")
    beh = d.get("behavior") or {}
    names = []
    for top in ("unit_tests", "integration_tests"):
        g = beh.get(top) or {}
        for sub in ("example_based", "property_based"):
            names += [n for n in (g.get(sub) or []) if isinstance(n, str)]
    names += [n for n in (beh.get("e2e_tests") or []) if isinstance(n, str)]
    if a.require_behavior and not names:
        rejects.append("--require-behavior: behavior has no test names (L5 not done)")
    elif not names:
        flags.append("behavior empty — fine at G2; test-suite-generator / spec-compile fill it at L5")
    th = beh.get("thresholds") or d.get("thresholds") or {}
    if th and not (beh.get("threshold_source") or d.get("threshold_source")):
        flags.append("thresholds present but no threshold_source (needs_semantic_review)")
    fp = (d.get("constraints") or {}).get("forbidden_paths")
    if fp is not None:
        for must in ("tests/**", "done_when.yaml"):
            if must not in fp:
                rejects.append(f"constraints.forbidden_paths must include {must}")
    out = {"verdict": "REJECT" if rejects else "PASS", "acceptance": len(acs), "mechanical": sum(1 for x in acs if isinstance(x, dict) and x.get("kind") == "mechanical"),
           "human": sum(1 for x in acs if isinstance(x, dict) and x.get("kind") == "human"), "tests_in_manifest": len(names), "rejects": rejects, "flags": flags}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
