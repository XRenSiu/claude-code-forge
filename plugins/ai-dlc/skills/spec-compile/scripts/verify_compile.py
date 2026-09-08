#!/usr/bin/env python3
"""
verify_compile.py — the semantic exit for spec-compile.

Structural well-formedness does not certify a compile manifest; the guarantee is a check of
the PRODUCT (the routing) against the decidability ladder. This enforces the mechanical half
(no routing UP the ladder, no example-only battery, no un-compiled G2 rubric) and FLAGS (does
not rubber-stamp) the semantic half.

Usage:
    python verify_compile.py <compile_manifest.yaml> [--dos <dos.yaml>]

Exit 0 = no rejects (manifest may still carry needs_semantic_review flags for a judge).
Exit 1 = at least one REJECT (a discipline was breached) or the manifest is unreadable.

Mechanical guarantees enforced (a breach is a REJECT — the non-waivable half):
  - decidability/line/gate consistent; routing UP the ladder is a reject (keyline violated)
  - behavioral battery with only examples and no property/metamorphic + no justification -> reject
  - judgment dimension free_form, or missing binary/evidence_ref -> reject (un-compiled LLM-judge)
  - every routed standard carries calibration_pending: true (compiled != certified)

Semantic half — FLAGGED as needs_semantic_review, never auto-passed:
  - is this REALLY the narrowest fitness function / right property / sufficient evidence binding
  - did the clause get pushed as far down as it actually could (a judge re-derivation)
"""
import sys
import json

try:
    import yaml
except ImportError:
    sys.stderr.write("verify_compile.py needs PyYAML: pip install pyyaml\n")
    sys.exit(1)

DECIDABILITY_LINE = {"structural": 1, "behavioral": 2, "judgment": 3}
LINE_GATE = {1: "g1", 2: "g1", 3: "g2"}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def check_routed(r):
    rejects, flags = [], []
    ref = str(r.get("clause_ref") or "<no-ref>")
    dec = (r.get("decidability") or "").strip()
    line = r.get("line")
    gate = (r.get("gate") or "").strip()

    if ref == "<no-ref>" or not (r.get("clause_ref") or "").strip():
        rejects.append(f"{ref}: clause_ref empty — nothing routed")
    if not (r.get("statement") or "").strip():
        rejects.append(f"{ref}: statement empty — the source clause is missing")

    if dec not in DECIDABILITY_LINE:
        rejects.append(f"{ref}: decidability must be structural|behavioral|judgment, got {dec!r}")
        return rejects, flags
    expected_line = DECIDABILITY_LINE[dec]

    # routing UP the ladder: a clause decidable lower must not sit higher
    if isinstance(line, int) and line > expected_line:
        rejects.append(
            f"{ref}: routed UP the ladder — decidability '{dec}' belongs on line {expected_line}, "
            f"got line {line} (keyline violated: 能{'静态' if expected_line == 1 else '测试'}判却放更高线)"
        )
    if isinstance(line, int) and line != expected_line and line <= expected_line:
        flags.append(f"{ref}: line {line} below decidability line {expected_line} — confirm it really decides here")

    if not gate:
        rejects.append(f"{ref}: gate not named (expected {LINE_GATE.get(expected_line)} for line {expected_line})")
    elif gate != LINE_GATE.get(expected_line):
        rejects.append(f"{ref}: gate '{gate}' inconsistent with line {expected_line} (expected {LINE_GATE.get(expected_line)})")

    # line ①: a fitness function needs a tool + a principle (principle before tool)
    if expected_line == 1:
        ff = r.get("fitness_function") or {}
        if not (ff.get("tool") or "").strip():
            rejects.append(f"{ref}: structural standard has no fitness_function.tool")
        if not (ff.get("principle") or "").strip():
            rejects.append(f"{ref}: structural standard has no principle (原则先于工具 — what it protects/forbids)")

    # line ②: not example-only
    if expected_line == 2:
        b = r.get("eval_case_battery") or {}
        examples = b.get("example") or []
        prop = b.get("property") or []
        meta = b.get("metamorphic") or []
        just = (b.get("examples_only_justification") or "").strip()
        if examples and not prop and not meta and not just:
            rejects.append(f"{ref}: behavioral battery is example-only with no property/metamorphic backstop and no justification (例子之间的缝)")
        af = b.get("assured_filters") or {}
        if not af.get("catches_injected_fault"):
            flags.append(f"{ref}: assured filter 'catches_injected_fault' not yet shown — calibrate's mutation score must confirm it bites")

    # line ③: compiled, not free-form
    if expected_line == 3:
        jp = r.get("judge_program") or {}
        if jp.get("free_form"):
            rejects.append(f"{ref}: G2 left as free_form LLM-judge prose — compile to PAJAMA program (un-compiled judge)")
        dims = jp.get("dimensions") or []
        if not dims:
            rejects.append(f"{ref}: G2 standard has no dimensions (no per-dimension rubric)")
        for d in dims:
            dn = d.get("name") or "<dim>"
            if not d.get("binary", False):
                rejects.append(f"{ref}/{dn}: dimension not binary (continuous scores drift / are gamed)")
            if not (d.get("evidence_ref") or "").strip():
                rejects.append(f"{ref}/{dn}: dimension has no evidence_ref (RRD: a verdict without evidence is not a verdict)")
        if not jp.get("isolation_ok", False):
            flags.append(f"{ref}: confirm R001 isolation (independent process / read-only snapshot / artifact+rubric only)")

    # compiled != certified
    if r.get("calibration_pending") is not True:
        rejects.append(f"{ref}: calibration_pending must be true — a compiled standard is not load-bearing until calibrate gates it")

    flags.append(f"{ref}: confirm pushed as far down the ladder as it actually goes (judge re-derivation) — needs_semantic_review")
    return rejects, flags


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    try:
        m = load(path)
    except Exception as e:
        sys.stderr.write(f"REJECT: cannot read manifest: {e}\n")
        sys.exit(1)

    rejects, flags = [], []
    routed = m.get("routed") or []
    if not routed:
        rejects.append("manifest has no routed clauses (nothing compiled)")
    for r in routed:
        rj, fl = check_routed(r)
        rejects += rj
        flags += fl

    report = {
        "manifest": path,
        "source_ref": m.get("source_ref"),
        "routed": len(routed),
        "by_line": {str(i): sum(1 for r in routed if r.get("line") == i) for i in (1, 2, 3)},
        "rejects": rejects,
        "needs_semantic_review": flags[:12] + ([f"... +{len(flags) - 12} more"] if len(flags) > 12 else []),
        "exit": "REJECT" if rejects else "MECHANICALLY_CLEAN",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
