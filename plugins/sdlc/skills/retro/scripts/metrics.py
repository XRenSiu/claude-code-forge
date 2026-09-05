#!/usr/bin/env python3
"""
metrics.py — X3: export lifecycle metrics from the archive directories, no extra instrumentation.

Baseline first, then see which layer is sick. Metrics the reference doc keeps, and their data sources:
  - lead time (issue → merge)            state.json created_at / merge.merged_at
  - PR rework rounds                     state.json review.rounds
  - reflow distribution by layer         state.json counters.{card,plan,task,ontology,world}
  - G1 interception rate (PSL track)     state.json gates.g1 (reject / psl runs)
  - human-AC ratio                       done_when.yaml acceptance[].kind == human (if archived)
  - escape defects                       escape-defects.md rows (if archived)
  - waivers                              state.json waivers (forced transitions — a process smell)

Usage:
  metrics.py <archive_root> [--json OUT.json] [--md OUT.md]
<archive_root> is the directory whose children are per-feature archives (e.g. specs/), each holding a
state.json produced by `sdlc_state.py archive`. Exit 0 always (reporting tool), 2 on IO error.
"""
import argparse
import datetime as _dt
import glob
import json
import os
import sys


def parse_ts(s):
    try:
        return _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def human_ac_ratio(dw_path):
    try:
        import yaml
        with open(dw_path, encoding="utf-8") as f:
            dw = yaml.safe_load(f) or {}
        acs = dw.get("acceptance") or []
        if not acs:
            return None
        return round(sum(1 for a in acs if a.get("kind") == "human") / len(acs), 3)
    except Exception:
        return None


def escape_rows(path):
    if not os.path.isfile(path):
        return 0
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("|") and not line.startswith("|---") and not line.lower().startswith("| at"):
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archive_root"); ap.add_argument("--json"); ap.add_argument("--md")
    a = ap.parse_args()
    rows = []
    for sp in sorted(glob.glob(os.path.join(a.archive_root, "*", "state.json"))):
        d = os.path.dirname(sp)
        with open(sp, encoding="utf-8") as f:
            st = json.load(f)
        c0, c1 = parse_ts(st.get("created_at", "")), parse_ts((st.get("merge") or {}).get("merged_at", "") or "")
        lead_h = round((c1 - c0).total_seconds() / 3600, 1) if c0 and c1 else None
        cnt = st.get("counters") or {}
        dw = None
        for cand in ("done_when.yaml", "done_when.yml"):
            if os.path.isfile(os.path.join(d, cand)):
                dw = human_ac_ratio(os.path.join(d, cand))
        rows.append({
            "feature": st.get("slug"), "track": st.get("track"), "stage": st.get("stage"),
            "lead_time_h": lead_h, "review_rounds": (st.get("review") or {}).get("rounds"),
            "reflows": {k: cnt.get(k, 0) for k in ("card", "plan", "task", "ontology", "world")},
            "g1": (st.get("gates") or {}).get("g1", {}).get("verdict"),
            "g3_required": (st.get("gates") or {}).get("g3", {}).get("required"),
            "human_ac_ratio": dw, "escape_defects": escape_rows(os.path.join(d, "escape-defects.md")),
            "waivers": len(st.get("waivers") or []),
        })
    psl = [r for r in rows if r["track"] == "psl"]
    g1_rate = round(sum(1 for r in psl if r["g1"] == "reject") / len(psl), 3) if psl else None
    totals = {
        "features": len(rows),
        "baseline_date": _dt.date.today().isoformat(),
        "g1_interception_rate": g1_rate,
        "reflow_distribution": {k: sum(r["reflows"][k] for r in rows) for k in ("card", "plan", "task", "ontology", "world")},
        "escape_defects": sum(r["escape_defects"] for r in rows),
        "avg_review_rounds": (round(sum(r["review_rounds"] or 0 for r in rows) / len(rows), 2) if rows else None),
        "avg_lead_time_h": (round(sum(r["lead_time_h"] for r in rows if r["lead_time_h"]) / max(1, sum(1 for r in rows if r["lead_time_h"])), 1) if rows else None),
        "human_ac_ratio_over_half": [r["feature"] for r in rows if (r["human_ac_ratio"] or 0) > 0.5],
        "waivers": sum(r["waivers"] for r in rows),
    }
    out = {"totals": totals, "features": rows}
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    md = ["# SDLC metrics — baseline %s" % totals["baseline_date"], "",
          "| feature | track | lead h | review rounds | card/plan/task/onto/world | g1 | human AC | escapes | waivers |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        rf = r["reflows"]
        md.append("| %s | %s | %s | %s | %s/%s/%s/%s/%s | %s | %s | %s | %s |" % (
            r["feature"], r["track"], r["lead_time_h"], r["review_rounds"], rf["card"], rf["plan"], rf["task"],
            rf["ontology"], rf["world"], r["g1"], r["human_ac_ratio"], r["escape_defects"], r["waivers"]))
    md += ["", "**totals**: " + json.dumps(totals, ensure_ascii=False)]
    text = "\n".join(md) + "\n"
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(text)
    print(json.dumps(out, ensure_ascii=False, indent=2) if not a.md else text)


if __name__ == "__main__":
    main()
