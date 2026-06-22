#!/usr/bin/env python3
"""
compute_confidence.py — the weighting primitive for meta-judge (M2).

M2 narrates a deterministic arithmetic formula (base 0.5 ± source/vendor/self-
confidence terms). meta-judge's own Models table even labels scoring as
"deterministic computation, no LLM call" — yet leaves the arithmetic to be done by
hand each run. skillwise THEORY.md §3: a deterministic computation is a Capability
gap; ship it as a primitive so a fat-fingered sum has no slot to land in. The LLM
still does the judgment (which findings merged, what severity, dedupe); this script
only turns the agreed sources into a confidence number, identically every time.

Implements `references/synthesis-protocol.md` § "Action 2 — Weight":
    base 0.5
    + 0.2 per additional distinct source role   (cap +0.4)
    + 0.2 per additional distinct vendor         (cap +0.2)
    - 0.2 if single-source AND single-vendor
    - 0.3 if the originating evaluator self-reported confidence: low
    + 0.1 if it self-reported confidence: high
    clamp to [0.0, 1.0]; confidence_boost = confidence - 0.5

Self-confidence rule for a *merged* finding (multiple sources): if the lowest
source self-confidence is "low" → -0.3; else if the highest is "high" → +0.1.

Input JSON: a list of merged findings, each:
    {"merged_finding_id": "mf-001",
     "sources": [{"role": "code-reviewer", "vendor": "claude", "confidence": "high"}, ...]}

Usage:
    python compute_confidence.py merged.json            # human table
    python compute_confidence.py merged.json --json     # adds confidence + confidence_boost
    cat merged.json | python compute_confidence.py -     # read stdin
"""

import sys
import json
import argparse

CONF_RANK = {"low": 0, "medium": 1, "high": 2}


def weight(sources):
    roles = {s.get("role") for s in sources if s.get("role")}
    vendors = {s.get("vendor") for s in sources if s.get("vendor")}
    n_sources = len(sources)

    role_bonus = min(0.4, max(0, len(roles) - 1) * 0.2)
    vendor_bonus = min(0.2, max(0, len(vendors) - 1) * 0.2)
    single_penalty = -0.2 if (n_sources == 1 and len(vendors) <= 1) else 0.0

    confs = [s.get("confidence") for s in sources if s.get("confidence") in CONF_RANK]
    self_adj = 0.0
    if confs:
        lowest = min(confs, key=lambda c: CONF_RANK[c])
        highest = max(confs, key=lambda c: CONF_RANK[c])
        if lowest == "low":
            self_adj = -0.3
        elif highest == "high":
            self_adj = 0.1

    raw = 0.5 + role_bonus + vendor_bonus + single_penalty + self_adj
    confidence = round(max(0.0, min(1.0, raw)), 2)
    return {
        "confidence": confidence,
        "confidence_boost": round(confidence - 0.5, 2),
        "distinct_roles": len(roles),
        "distinct_vendors": len(vendors),
        "terms": {"role_bonus": role_bonus, "vendor_bonus": vendor_bonus,
                  "single_source_single_vendor_penalty": single_penalty,
                  "self_confidence_adj": self_adj},
    }


def main():
    ap = argparse.ArgumentParser(description="Deterministic meta-judge M2 confidence weighting.")
    ap.add_argument("path", help="JSON file of merged findings, or - for stdin")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
    findings = json.loads(raw)
    if isinstance(findings, dict):
        findings = findings.get("deduplicated_findings", [])

    out = []
    for f in findings:
        w = weight(f.get("sources", []))
        merged = dict(f)
        merged["confidence"] = w["confidence"]
        merged["confidence_boost"] = w["confidence_boost"]
        merged["_weight_detail"] = w
        out.append(merged)

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(f"\n  meta-judge M2 confidence (deterministic)\n")
        for m in out:
            w = m["_weight_detail"]
            print(f"  {m.get('merged_finding_id', '?'):>8}  conf={m['confidence']:<4} "
                  f"(boost {m['confidence_boost']:+}) "
                  f"roles={w['distinct_roles']} vendors={w['distinct_vendors']}")
        print("\n  These numbers are arithmetic, not judgment — paste verbatim into "
              "deduplicated_findings[].confidence.\n")


if __name__ == "__main__":
    main()
