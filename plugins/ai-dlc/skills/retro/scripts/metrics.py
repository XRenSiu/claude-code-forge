#!/usr/bin/env python3
"""
metrics.py — X3: export lifecycle metrics from the archive directories, no extra instrumentation.

Baseline first, then see which layer is sick. Metrics the reference doc keeps, and their data sources:
  - lead time (issue → merge)            state.json created_at / merge.merged_at
  - PR rework rounds                     state.json review.rounds
  - reflow distribution by layer         state.json counters.{card,plan,task,ontology,world}
  - gate interceptions G1/G2/G3          ledger.md gate rows (fallback trace.jsonl `kind=gate`) — how many
                                         times a gate REJECTED, not what it finally said. state.json keeps
                                         only the last verdict, so a run that was rejected twice and then
                                         passed reads as 0 interceptions there (I-84).
  - human-AC ratio                       done_when.yaml acceptance[].kind == human (if archived)
  - escape defects                       escape-defects.md rows (if archived)
  - waivers                              state.json waivers (forced transitions — a process smell)
  - escape causal chain (v0.6)           trace.jsonl: escape → caused_by* → root (depth + root kind/layer) — "why did the gate miss"
  - contract rework (v0.6)               trace.jsonl: events with `supersedes done_when.yaml#AC-*` / acceptance count

Usage:
  metrics.py <archive_root> [--json OUT.json] [--md OUT.md]
<archive_root> is the directory whose children are per-feature archives (e.g. specs/), each holding a
state.json produced by `aidlc_state.py archive`. Exit 0 always (reporting tool), 2 on IO error.
"""
import argparse
import datetime as _dt
import glob
import json
import os
import re
import sys

GATE_SIGNALS = ("g1", "g2", "g3")
# gate verdicts are pass | reject | waived (aidlc_state.py gate --verdict); the ledger/trace decision
# string is the verdict plus optional attribution / delegation suffixes, e.g. "reject (rule_error) [delegated]"
REJECT_RE = re.compile(r"^\s*reject\b", re.IGNORECASE)


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


def _empty_gate_counts():
    return {g: 0 for g in GATE_SIGNALS}, {g: 0 for g in GATE_SIGNALS}


def gate_history_from_trace(evs):
    """Count gate REJECT events per signal from trace.jsonl. None when the trace holds no gate event."""
    rejects, decisions = _empty_gate_counts()
    seen = False
    for e in evs:
        if e.get("kind") != "gate":
            continue
        sig = str(e.get("signal") or "").strip().lower()
        if sig not in rejects:
            continue
        seen = True
        decisions[sig] += 1
        if REJECT_RE.match(str(e.get("decision") or "")):
            rejects[sig] += 1
    return (rejects, decisions) if seen else None


def gate_history_from_ledger(path):
    """Count gate REJECT rows per signal from the append-only ledger.md table.

    The ledger is the authoritative history (`只增不删`); trace.jsonl is its machine companion and may be
    absent in older archives. Columns are located by header name, not by position.
    """
    if not os.path.isfile(path):
        return None
    rejects, decisions = _empty_gate_counts()
    idx, seen = None, False
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            low = [c.lower() for c in cells]
            if idx is None:
                if "kind" in low and "decision" in low:
                    idx = {"kind": low.index("kind"), "decision": low.index("decision"),
                           "signal": next((i for i, c in enumerate(low) if c.startswith("signal")), None)}
                continue
            if all(set(c) <= set("-: ") for c in cells):
                continue

            def cell(name, _cells=cells, _idx=idx):
                i = _idx.get(name)
                return _cells[i] if i is not None and i < len(_cells) else ""

            if cell("kind").lower() != "gate":
                continue
            sig = cell("signal").lower()
            if sig not in rejects:
                continue
            seen = True
            decisions[sig] += 1
            if REJECT_RE.match(cell("decision")):
                rejects[sig] += 1
    return (rejects, decisions) if seen else None


def gate_history(d, trace, gates):
    """Gate interception counts for one archive. Ledger first, trace second, final verdict only as a last
    resort — the last resort is exactly the I-84 defect, so it is labelled in `gate_source`."""
    got = gate_history_from_ledger(os.path.join(d, "ledger.md"))
    source = "ledger"
    if got is None:
        got, source = gate_history_from_trace(trace), "trace"
    if got is None:
        rejects, decisions = _empty_gate_counts()
        for g in GATE_SIGNALS:
            v = str((gates.get(g) or {}).get("verdict") or "")
            if v and v != "pending":
                decisions[g] += 1
                if REJECT_RE.match(v):
                    rejects[g] += 1
        return rejects, decisions, "state(final-verdict-only)"
    return got[0], got[1], source


def escape_rows(path):
    if not os.path.isfile(path):
        return 0
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("|") and not line.startswith("|---") and not line.lower().startswith("| at"):
                n += 1
    return n


def size_buckets(archives):
    """按体量分桶（v0.4）：S 档豁免了整体验收，它的逃逸率不低于 M 就说明分档标准定错了。
    分档对不对由逃逸缺陷回答，不由拍脑袋回答。"""
    out = {}
    for a in archives:
        st = a.get("state") or {}
        size = ((st.get("intake") or {}).get("size")) or "unrecorded"
        src = ((st.get("intake") or {}).get("size_source")) or "unrecorded"
        b = out.setdefault(size, {"runs": 0, "derived": 0, "size_exemptions": 0, "escapes": 0})
        b["runs"] += 1
        b["derived"] += 1 if src == "derived" else 0
        b["size_exemptions"] += a.get("size_exemptions", 0)
        b["escapes"] += a.get("escapes", 0)
    return out


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
        gates = st.get("gates") or {}
        g_rejects, g_decisions, g_source = gate_history(d, trace, gates)
        rows.append({
            "feature": st.get("slug"), "track": st.get("track"), "stage": st.get("stage"),
            "lead_time_h": lead_h, "review_rounds": (st.get("review") or {}).get("rounds"),
            "reflows": {k: cnt.get(k, 0) for k in ("card", "plan", "task", "ontology", "world")},
            "g1": gates.get("g1", {}).get("verdict"),
            "g3_required": gates.get("g3", {}).get("required"),
            "gate_rejections": g_rejects, "gate_decisions": g_decisions, "gate_source": g_source,
            "human_ac_ratio": dw, "escape_defects": escape_rows(os.path.join(d, "escape-defects.md")),
            "waivers": len(st.get("waivers") or []),
            "trace_events": len(trace), "escape_chains": chains, "contract_rework": rework,
        })
    gate_rejections = {g: sum(r["gate_rejections"][g] for r in rows) for g in GATE_SIGNALS}
    gate_decisions = {g: sum(r["gate_decisions"][g] for r in rows) for g in GATE_SIGNALS}
    # the rate is rejections per gate SIGNING, counted from the history — not "features whose last verdict
    # was reject", which is structurally blind to every interception but the last one (I-84).
    g1_rate = round(gate_rejections["g1"] / gate_decisions["g1"], 3) if gate_decisions["g1"] else None
    totals = {
        "features": len(rows),
        "baseline_date": _dt.date.today().isoformat(),
        "g1_interceptions": gate_rejections["g1"],
        "gate_rejections": gate_rejections,
        "gate_decisions": gate_decisions,
        "gate_history_unavailable": [r["feature"] for r in rows if r["gate_source"].startswith("state")],
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
          "| feature | track | lead h | review rounds | card/plan/task/onto/world | g1 final | gate rejects g1/g2/g3 (src) | human AC | escapes | waivers | escape chain (depth→root) | AC rework |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        rf = r["reflows"]
        chains = "; ".join(f"{c['depth']}→{c['root_kind']}/{c['root_layer'] or '-'}" for c in r["escape_chains"]) or "-"
        rw = r["contract_rework"]
        rework = f"{len(rw['ac_superseded'])}/{rw['ac_total']}" if rw["ac_total"] else "-"
        gj = r["gate_rejections"]
        gate_cell = "%s/%s/%s (%s)" % (gj["g1"], gj["g2"], gj["g3"], r["gate_source"])
        md.append("| %s | %s | %s | %s | %s/%s/%s/%s/%s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["feature"], r["track"], r["lead_time_h"], r["review_rounds"], rf["card"], rf["plan"], rf["task"],
            rf["ontology"], rf["world"], r["g1"], gate_cell, r["human_ac_ratio"], r["escape_defects"],
            r["waivers"], chains, rework))
    md += ["", "**totals**: " + json.dumps(totals, ensure_ascii=False)]
    text = "\n".join(md) + "\n"
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(text)
    print(json.dumps(out, ensure_ascii=False, indent=2) if not a.md else text)


if __name__ == "__main__":
    main()
