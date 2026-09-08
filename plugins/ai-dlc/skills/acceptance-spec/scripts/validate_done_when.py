#!/usr/bin/env python3
"""
validate_done_when.py — the EXIT primitive for the done_when.yaml contract.

acceptance-spec iron rules 7 / 11 / 12 ask the author to "walk the v1 schema by
hand" and "confirm every existence entry has no stray sub-fields". That is exactly
the kind of mechanical correctness skillwise THEORY.md §3 says must be sealed by a
named primitive, not re-improvised in prose every run: a wrong key on an existence
entry, a behavior leaf that is a mapping instead of a bare string, or a stray
`fitness:` block has *no slot to land in* once this script is the gate.

It implements `references/done-when-schema-validator.md` literally (v1.0+ schema:
existence + behavior + rules, post fitness-dissolution). It does NOT mutate the
contract — it locates what is wrong and exits non-zero under --check, the same
contract evaluate-skill's lint_skill.py uses.

Usage:
    python validate_done_when.py <path-to-done_when.yaml> [--spec <spec.md>] [--json]
    python validate_done_when.py <path> --check        # exit 1 on any hard failure (CI / skill gate)

Exit codes: 0 = clean (warnings allowed), 1 = hard failure under --check, 2 = usage error.
"""

import sys
import os
import re
import json
import argparse

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "validate_done_when.py needs PyYAML. Install it: pip install pyyaml\n")
    sys.exit(2)

V1_EXISTENCE_KINDS = {"file", "function", "route", "db_field", "frontend_component"}
PBT_ARCHETYPES = ("invariant", "idempotent", "reversible", "boundary",
                  "monotonic", "state_machine")
BEHAVIOR_TEST_GROUPS = [
    ("unit_tests", "example_based"),
    ("unit_tests", "property_based"),
    ("integration_tests", "example_based"),
    ("integration_tests", "property_based"),
    ("e2e_tests", None),
]


def add(findings, level, code, msg):
    findings.append({"level": level, "code": code, "message": msg})


def validate(doc, spec_text):
    """Return a list of findings. level ∈ {error, warn, ok}."""
    findings = []

    if not isinstance(doc, dict):
        add(findings, "error", "root.not_mapping",
            "Top-level YAML is not a mapping; cannot be a v1 done_when contract.")
        return findings

    # --- Mandatory top-level keys ------------------------------------------
    feature = doc.get("feature")
    if not feature:
        add(findings, "error", "feature.missing", "`feature:` is missing.")
    elif not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(feature)):
        add(findings, "warn", "feature.not_kebab",
            f"`feature: {feature}` is not kebab-case.")

    based_on = doc.get("based_on")
    if not isinstance(based_on, list) or not based_on:
        add(findings, "error", "based_on.missing",
            "`based_on:` must be a non-empty list of REQ IDs (the v1 traceability anchor).")
        based_on = based_on if isinstance(based_on, list) else []

    if "created_at" not in doc:
        add(findings, "error", "created_at.missing", "`created_at:` (ISO-8601) is missing.")
    if "created_by" not in doc:
        add(findings, "error", "created_by.missing", "`created_by:` (skill name) is missing.")

    # --- fitness: must be ABSENT (retired in v1.0.0) -----------------------
    if "fitness" in doc:
        add(findings, "error", "fitness.present",
            "`fitness:` block is present — retired in v1.0.0 (HTML v2 §3.5). "
            "This is a pre-v1 contract; regenerate via /acceptance-spec v1.0+.")

    # --- existence: strict v1 shape ----------------------------------------
    existence = doc.get("existence")
    if existence is None:
        add(findings, "error", "existence.missing",
            "`existence:` key is required (may be an empty list, but must exist).")
    elif not isinstance(existence, list):
        add(findings, "error", "existence.not_list", "`existence:` must be a list.")
    else:
        for i, entry in enumerate(existence):
            where = f"existence[{i}]"
            if not isinstance(entry, dict):
                add(findings, "error", "existence.not_mapping",
                    f"{where} is not a single-key mapping (got {type(entry).__name__}).")
                continue
            keys = list(entry.keys())
            if len(keys) != 1:
                add(findings, "error", "existence.extra_keys",
                    f"{where} has keys {keys} — v1 existence entries are a single key-value "
                    f"pair with NO sub-fields (no based_on/kind/class/description).")
                continue
            kind = keys[0]
            if kind not in V1_EXISTENCE_KINDS:
                add(findings, "error", "existence.bad_kind",
                    f"{where} kind `{kind}` is not one of the five v1 kinds "
                    f"{sorted(V1_EXISTENCE_KINDS)}.")

    # --- behavior: strict v1 shape -----------------------------------------
    behavior = doc.get("behavior")
    test_names = []
    if not isinstance(behavior, dict):
        add(findings, "error", "behavior.missing",
            "`behavior:` is required and must contain at least one of unit_tests/"
            "integration_tests/e2e_tests.")
    else:
        present_groups = [g for g in ("unit_tests", "integration_tests", "e2e_tests")
                          if g in behavior]
        if not present_groups:
            add(findings, "error", "behavior.empty",
                "`behavior:` has none of unit_tests/integration_tests/e2e_tests.")

        for top, sub in BEHAVIOR_TEST_GROUPS:
            container = behavior.get(top)
            if container is None:
                continue
            if sub is None:
                entries, label = container, top
            else:
                if not isinstance(container, dict):
                    continue
                entries, label = container.get(sub), f"{top}.{sub}"
            if entries is None:
                continue
            if not isinstance(entries, list):
                add(findings, "error", "behavior.group_not_list",
                    f"`behavior.{label}` must be a list of bare-string test names.")
                continue
            for j, name in enumerate(entries):
                if not isinstance(name, str):
                    add(findings, "error", "behavior.not_bare_string",
                        f"behavior.{label}[{j}] is a {type(name).__name__}, not a bare string. "
                        f"v1 forbids name:/based_on:/property_type:/dependencies:/tool: sub-fields.")
                    continue
                test_names.append(name)
                if sub == "property_based" and not any(a in name for a in PBT_ARCHETYPES):
                    add(findings, "warn", "behavior.pbt_no_archetype",
                        f"property_based test `{name}` encodes no archetype token "
                        f"{PBT_ARCHETYPES}; 4-B's PBT dispatcher keys off the name — rename or "
                        f"reclassify as example_based.")

        # thresholds
        thresholds = behavior.get("thresholds")
        if not isinstance(thresholds, dict):
            add(findings, "error", "thresholds.missing",
                "`behavior.thresholds:` is required.")
        else:
            if "mutation_kill_rate" not in thresholds:
                add(findings, "error", "thresholds.no_mutation",
                    "`behavior.thresholds.mutation_kill_rate:` is MANDATORY (anti reward-hacking).")
            else:
                m = re.search(r"([0-9]*\.?[0-9]+)", str(thresholds["mutation_kill_rate"]))
                if m and float(m.group(1)) < 0.7:
                    add(findings, "warn", "thresholds.mutation_low",
                        f"mutation_kill_rate {thresholds['mutation_kill_rate']} is below the 0.70 floor.")
            extra = set(thresholds) - {"unit_coverage", "integration_coverage",
                                       "mutation_kill_rate", "pbt_runs_per_property"}
            if extra:
                add(findings, "warn", "thresholds.extra_keys",
                    f"thresholds has non-canonical keys {sorted(extra)} (soft warning).")
            e2e = behavior.get("e2e_tests")
            if isinstance(e2e, list) and len(e2e) > 5:
                add(findings, "warn", "e2e.too_many",
                    f"{len(e2e)} e2e tests (> 5) — likely too E2E-heavy; consider integration.")

    # --- rules: present, flat ----------------------------------------------
    rules = doc.get("rules")
    if rules is None:
        add(findings, "error", "rules.missing",
            "`rules:` key is required (may be an empty list).")
    elif not isinstance(rules, list):
        add(findings, "error", "rules.not_list", "`rules:` must be a list.")
    else:
        for i, r in enumerate(rules):
            if isinstance(r, dict):
                if "rule" not in r:
                    add(findings, "error", "rules.no_rule_key",
                        f"rules[{i}] is a mapping without a `rule:` key.")
                if any(isinstance(v, (dict, list)) for v in r.values()):
                    add(findings, "error", "rules.nested",
                        f"rules[{i}] has a nested object/list — keep rules flat.")
            elif not isinstance(r, str):
                add(findings, "error", "rules.bad_entry",
                    f"rules[{i}] must be a bare string or a flat mapping with `rule:`.")

    # --- spec_drift_threshold: exactly one sub-field -----------------------
    sdt = doc.get("spec_drift_threshold")
    if not isinstance(sdt, dict):
        add(findings, "error", "spec_drift_threshold.missing",
            "`spec_drift_threshold:` with `max_fix_loops_before_escalation:` is required.")
    else:
        if "max_fix_loops_before_escalation" not in sdt:
            add(findings, "error", "spec_drift_threshold.no_field",
                "`spec_drift_threshold.max_fix_loops_before_escalation:` is missing.")
        else:
            val = sdt["max_fix_loops_before_escalation"]
            if not isinstance(val, int):
                add(findings, "error", "spec_drift_threshold.not_int",
                    "`max_fix_loops_before_escalation:` must be an integer.")
            elif val > 5:
                add(findings, "warn", "spec_drift_threshold.high",
                    f"max_fix_loops_before_escalation={val} (>5): ratchet loops long before escalating.")
        extra = set(sdt) - {"max_fix_loops_before_escalation"}
        if extra:
            add(findings, "error", "spec_drift_threshold.extra_keys",
                f"spec_drift_threshold has extra sub-fields {sorted(extra)} — v1 defines only one.")

    # --- cross-ref against spec.md (best-effort) ---------------------------
    if spec_text is not None and based_on:
        spec_reqs = set(re.findall(r"\bREQ-\d{3}\b", spec_text))
        if spec_reqs:
            missing = [r for r in based_on if r not in spec_reqs]
            if missing:
                add(findings, "error", "based_on.unknown_req",
                    f"based_on references REQ IDs absent from spec.md: {missing}.")
            forgotten = [r for r in sorted(spec_reqs) if r not in set(based_on)]
            if forgotten:
                add(findings, "warn", "spec.req_not_in_based_on",
                    f"spec.md has REQ IDs not in based_on: {forgotten} "
                    f"(either untestable — flag upstream — or forgotten).")

    if not any(f["level"] == "error" for f in findings):
        add(findings, "ok", "schema.v1_clean",
            "Contract conforms to v1 schema (existence + behavior + rules); no hard failures.")
    return findings


def main():
    ap = argparse.ArgumentParser(description="Validate a done_when.yaml against v1 schema.")
    ap.add_argument("path", help="path to done_when.yaml")
    ap.add_argument("--spec", help="sibling spec.md for based_on cross-reference")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    ap.add_argument("--check", action="store_true", help="exit 1 on any hard failure")
    args = ap.parse_args()

    if not os.path.isfile(args.path):
        sys.stderr.write(f"No such file: {args.path}\n")
        sys.exit(2)
    with open(args.path, encoding="utf-8") as fh:
        try:
            doc = yaml.safe_load(fh)
        except yaml.YAMLError as e:
            print(json.dumps({"findings": [{"level": "error", "code": "yaml.parse_error",
                  "message": str(e)}]}) if args.json else f"✗ YAML parse error: {e}")
            sys.exit(1 if args.check else 0)

    spec_text = None
    spec_path = args.spec
    if spec_path is None:
        guess = os.path.join(os.path.dirname(os.path.abspath(args.path)), "spec.md")
        if os.path.isfile(guess):
            spec_path = guess
    if spec_path and os.path.isfile(spec_path):
        with open(spec_path, encoding="utf-8") as fh:
            spec_text = fh.read()

    findings = validate(doc, spec_text)
    n_err = sum(1 for f in findings if f["level"] == "error")
    n_warn = sum(1 for f in findings if f["level"] == "warn")

    if args.json:
        print(json.dumps({"path": args.path, "errors": n_err, "warnings": n_warn,
                          "findings": findings}, indent=2, ensure_ascii=False))
    else:
        tty = sys.stdout.isatty()
        def col(s, c): return f"\033[{c}m{s}\033[0m" if tty else s
        icon = {"error": col("✗", "31"), "warn": col("▲", "33"), "ok": col("✓", "32")}
        print(f"\n  done_when validator · {args.path}")
        for f in findings:
            print(f"  {icon[f['level']]} [{f['code']}] {f['message']}")
        verdict = (col(f"{n_err} hard failure(s)", "31") if n_err else col("0 hard failures", "32"))
        print(f"\n  {verdict} · {n_warn} warning(s)\n")

    if args.check and n_err:
        sys.exit(1)


if __name__ == "__main__":
    main()
