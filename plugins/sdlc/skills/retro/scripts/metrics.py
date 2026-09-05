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
  - escape causal chain (v0.6)           trace.jsonl: escape → caused_by* → root (depth + root kind/layer) — "why did the gate miss"
  - contract rework (v0.6)               trace.jsonl: events with `supersedes done_when.yaml#AC-*` / acceptance count

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


def read_trace(path):
    evs = []
    if not os.path.isfile(path):
        return evs
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    evs.append(json.loads(line))
                except Exception:
                    pass
    return evs


def escape_chains(evs, max_depth=12):
    """For each escape event walk caused_by to the root: depth + what the root was (kind / layer / rule)."""
    byid = {e.get("id"): e for e in evs}
    out = []
    for e in evs:
        if e.get("kind") != "escape" and e.get("signal") != "escape_defect":
            continue
        cur, depth, seen = e, 0, set()
        while depth < max_depth:
            nxt = next((r.get("target") for r in cur.get("refs") or [] if r.get("type") == "caused_by"), None)
            if not nxt or nxt in seen or nxt not in byid:
                break
            seen.add(nxt); cur = byid[nxt]; depth += 1
        rule = next((r["target"] for r in cur.get("refs") or [] if r.get("type") == "decided_by" and str(r.get("target", "")).startswith("routing.")), None)
        out.append({"escape": e.get("id"), "depth": depth, "root": cur.get("id"), "root_kind": cur.get("kind"),
                    "root_layer": cur.get("layer"), "root_signal": cur.get("signal"), "root_rule": rule})
    return out


def contract_rework(evs, dw_path):
    superseded = sorted({str(r.get("target")).split("@")[0].split("#")[-1] for e in evs for r in e.get("refs") or []
                         if r.get("type") == "supersedes" and "done_when" in str(r.get("target", ""))})
    total = None
    try:
        import yaml
        with open(dw_path, encoding="utf-8") as f:
            total = len((yaml.safe_load(f) or {}).get("acceptance") or [])
    except Exception:
        pass
    return {"ac_superseded": superseded, "ac_total": total,
            "ratio": (round(len(superseded) / total, 3) if total else None)}


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
        dw, dw_path = None, None
        for cand in ("done_when.yaml", "done_when.yml"):
            if os.path.isfile(os.path.join(d, cand)):
                dw_path = os.path.join(d, cand); dw = human_ac_ratio(dw_path)
        trace = read_trace(os.path.join(d, "trace.jsonl"))
        chains = escape_chains(trace)
        rework = contract_rework(trace, dw_path) if dw_path else {"ac_superseded": [], "ac_total": None, "ratio": None}
        rows.append({
            "feature": st.get("slug"), "track": st.get("track"), "stage": st.get("stage"),
            "lead_time_h": lead_h, "review_rounds": (st.get("review") or {}).get("rounds"),
            "reflows": {k: cnt.get(k, 0) for k in ("card", "plan", "task", "ontology", "world")},
            "g1": (st.get("gates") or {}).get("g1", {}).get("verdict"),
            "g3_required": (st.get("gates") or {}).get("g3", {}).get("required"),
            "human_ac_ratio": dw, "escape_defects": escape_rows(os.path.join(d, "escape-defects.md")),
            "waivers": len(st.get("waivers") or []),
            "trace_events": len(trace), "escape_chains": chains, "contract_rework": rework,
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
        "escape_chains": sum(len(r["escape_chains"]) for r in rows),
        "avg_escape_chain_depth": (round(sum(c["depth"] for r in rows for c in r["escape_chains"]) / max(1, sum(len(r["escape_chains"]) for r in rows)), 2)
                                   if any(r["escape_chains"] for r in rows) else None),
        "escape_root_layers": {},
        "contract_rework_ratio": (round(sum(len(r["contract_rework"]["ac_superseded"]) for r in rows) /
                                        max(1, sum(r["contract_rework"]["ac_total"] or 0 for r in rows)), 3)
                                  if any(r["contract_rework"]["ac_total"] for r in rows) else None),
    }
    for r in rows:
        for c in r["escape_chains"]:
            k = c.get("root_layer") or c.get("root_kind") or "?"
            totals["escape_root_layers"][k] = totals["escape_root_layers"].get(k, 0) + 1
    out = {"totals": totals, "features": rows}
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    md = ["# SDLC metrics — baseline %s" % totals["baseline_date"], "",
          "| feature | track | lead h | review rounds | card/plan/task/onto/world | g1 | human AC | escapes | waivers | escape chain (depth→root) | AC rework |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        rf = r["reflows"]
        chains = "; ".join(f"{c['depth']}→{c['root_kind']}/{c['root_layer'] or '-'}" for c in r["escape_chains"]) or "-"
        rw = r["contract_rework"]
        rework = f"{len(rw['ac_superseded'])}/{rw['ac_total']}" if rw["ac_total"] else "-"
        md.append("| %s | %s | %s | %s | %s/%s/%s/%s/%s | %s | %s | %s | %s | %s | %s |" % (
            r["feature"], r["track"], r["lead_time_h"], r["review_rounds"], rf["card"], rf["plan"], rf["task"],
            rf["ontology"], rf["world"], r["g1"], r["human_ac_ratio"], r["escape_defects"], r["waivers"], chains, rework))
    md += ["", "**totals**: " + json.dumps(totals, ensure_ascii=False)]
    text = "\n".join(md) + "\n"
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(text)
    print(json.dumps(out, ensure_ascii=False, indent=2) if not a.md else text)


if __name__ == "__main__":
    main()
