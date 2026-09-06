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
  - discipline 1 (adjective→threshold) applies to a human AC's `statement` too, not only `expect` —
    a vague word with no number is boilerplate wherever it sits (dogfood I-08 / I-40)
  - discipline 2 (twins) is not satisfied by existing alone: an `unwanted` twin's `given` must be
    SELF-SUFFICIENT — it must cover its happy sibling's given keys, so the unhappy path can be
    falsified without inheriting context from elsewhere (dogfood I-55)
  - --form-draft <form-draft.md>: every key used in a mechanical AC's `expect` must appear in the
    signed form draft, i.e. the contract may only assert predicates the form actually names, and an
    AC may not invent a count the instrument was never designed to emit (dogfood I-40)
Flags: thresholds without threshold_source; REQ in based_on with no AC; behavior empty (fine at G2);
a human AC whose section mixes judges (split it — dogfood I-41).
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
    ap.add_argument("--form-draft", help="signed form draft; every expect key must be a predicate it names (dogfood I-40)")

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
            else:
                # discipline 1 holds for judgment clauses too: an adjective with no number is
                # boilerplate whether a script or a person reads it (dogfood I-08 / I-40)
                w = vague(ac.get("statement"))
                if w:
                    rejects.append(f"{aid}: statement contains vague `{w}` with no number — "
                                   "discipline 1 (adjective→threshold) holds for human ACs too")
            if ac.get("judge") not in JUDGES:
                rejects.append(f"{aid}: judge must be one of {sorted(JUDGES)}")
            if ac.get("evidence") not in EVIDENCE:
                rejects.append(f"{aid}: evidence must be one of {sorted(EVIDENCE)}")
    for ac in acs:
        if isinstance(ac, dict) and ac.get("kind") == "mechanical" and ac.get("ears_type", "event") in ("event", "state"):
            aid = ac.get("id")            # local to this pass: the outer loop's `aid` is long stale
            sib = [x for x in by_obs.get(str(ac.get("observe")), []) if x is not ac and x.get("ears_type") == "unwanted"]
            paired = [x for x in acs if isinstance(x, dict) and x.get("id") == ac.get("paired_with")]
            if not sib and ac.get("paired_with") not in ids:
                rejects.append(f"{ac.get('id')}: happy AC without an unhappy twin")
            # the twin must be falsifiable ON ITS OWN: a `given` that only states the difference
            # forces the reader to inherit context from the happy sibling, and a checker handed only
            # the twin cannot tell what was removed (dogfood I-55). Pair each twin with ITS OWN happy
            # AC — `paired_with` in either direction — never with any twin sharing the observe, or a
            # contract with several happy ACs on one boundary reports the same twin many times over.
            mine = [x for x in paired if x.get("ears_type") == "unwanted"]
            mine += [x for x in sib if x.get("paired_with") == aid and x not in mine]
            for twin in mine:
                hg, tg = ac.get("given"), twin.get("given")
                # A `given` that is not a mapping cannot be compared key by key, and silently skipping
                # the comparison is how the check gets disarmed: write the twin's given as a string and
                # the same contract the fixture rejects sails through (PR pre-review, B-tier). A
                # mechanical AC's given must be a mapping, so say so instead of looking away.
                for who, g in ((aid, hg), (twin.get("id"), tg)):
                    if g is not None and not isinstance(g, dict):
                        rejects.append(f"{who}: given must be a mapping of named preconditions, got "
                                       f"{type(g).__name__} — a free-form given cannot be compared "
                                       "against its twin's, which disarms the self-sufficiency check")
                if isinstance(hg, dict) and isinstance(tg, dict):
                    missing = [k for k in hg if k not in tg]
                    if missing:
                        rejects.append(
                            f"{twin.get('id')}: unwanted twin's given is not self-sufficient — "
                            f"missing {sorted(missing)} that its pair {aid} states; restate the happy "
                            "given, then write the difference")
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
    # C1's other half: the contract may only assert what the signed form actually names. An `expect`
    # key the form never mentions is a count the instrument was never designed to emit, and the gap
    # only surfaces when someone writes the test (dogfood I-40).
    if a.form_draft:
        try:
            form = open(a.form_draft, encoding="utf-8").read()
        except OSError as e:
            sys.stderr.write(f"validate_done_when_v2: cannot read form draft: {e}\n"); sys.exit(2)
        for ac in acs:
            if not isinstance(ac, dict) or ac.get("kind") != "mechanical":
                continue
            for k in (ac.get("expect") or {}):
                if str(k) not in form:
                    rejects.append(f"{ac.get('id')}: expect key `{k}` is named nowhere in the signed "
                                   "form draft — the contract asserts a predicate the form does not define")

    # a human-AC section that mixes judges cannot be routed to one adjudicator (dogfood I-41)
    by_obs_h = {}
    for ac in acs:
        if isinstance(ac, dict) and ac.get("kind") == "human":
            by_obs_h.setdefault(str(ac.get("observe")), set()).add(ac.get("judge"))
    for obs, judges in by_obs_h.items():
        if len(judges) > 1:
            flags.append(f"human ACs on {obs} carry mixed judges {sorted(judges)} — split the section "
                         "so each observation goes to one adjudicator")

    # ---- constraints.structure：形状对不对（值本身由 verify_structure.py 在 A 档求值）----
    STRUCT_NUM = {"max_function_complexity": int, "max_complexity_delta": int,
                  "max_duplicate_block_lines": int, "max_duplicate_ratio": float}
    st = (d.get("constraints") or {}).get("structure")
    if st is None:
        flags.append("constraints.structure 缺席：这次交付没有承诺任何结构性质量判据"
                     "（复杂度增量 / 重复率 / 依赖方向）。A 档不检它 = 测试全绿而结构退化可以合入")
    elif not isinstance(st, dict):
        rejects.append("constraints.structure 必须是映射")
    else:
        known = set(STRUCT_NUM) | {"layers", "exclude"}
        for k in st:
            if k not in known:
                rejects.append(f"constraints.structure 未知键 {k}（封闭集：{sorted(known)}）")
        for k, typ in STRUCT_NUM.items():
            if k in st and not isinstance(st[k], (int, float)):
                rejects.append(f"constraints.structure.{k} 必须是数字，得到 {st[k]!r}")
        for lay in (st.get("layers") or []):
            if not isinstance(lay, dict) or not lay.get("name") or not lay.get("path"):
                rejects.append(f"constraints.structure.layers 每条要有 name 与 path：{lay!r}")
            elif "may_import" not in lay:
                rejects.append(f"layer {lay.get('name')} 没写 may_import —— 不写等于不检，"
                               "允许什么必须显式列出（空列表 = 谁都不许 import）")
        # layer_names，不是 names —— 第 175 行的 names 是 behavior 的测试名列表。
        # 2026-09-06：这里曾写成 names，把测试名清单覆盖成层名集合，于是 tests_in_manifest 报的是层数。
        # 由 effect harness 的 sdlc arm 在跑 T01 时读源码发现（它自己的契约声明了 2 个层、11 个测试名，报了 2）。
        layer_names = {l.get("name") for l in (st.get("layers") or []) if isinstance(l, dict)}
        for lay in (st.get("layers") or []):
            for t in (lay.get("may_import") or []) if isinstance(lay, dict) else []:
                if t not in layer_names:
                    rejects.append(f"layer {lay.get('name')}.may_import 指向未声明的层 {t}")
        if not any(k in st for k in STRUCT_NUM) and not st.get("layers"):
            rejects.append("constraints.structure 是空壳：一条阈值或一个 layers 都没有")

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
