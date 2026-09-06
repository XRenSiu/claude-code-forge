#!/usr/bin/env python3
"""
tune.py — the hill-climbing loop's generator: read the traces every other loop leaves behind and propose
changes to the HARNESS PARAMETERS (never to code, contracts or the world). Every proposal targets one entry of a
closed set, cites the data it came from, predicts which metric moves, and is delivered as a PR or a gate.json
fix_list entry — never applied here (apply_proposal.py only emits diffs / patch files).

Usage:
  tune.py <archive_root> [--pr-watch DIR] [--ratchet-logs DIR] [--routing ROUTING.yaml] [--loops LOOPS.yaml]
          [--skills-root DIR] [--out OUT.yaml] [--min-features 2] [--json]

Inputs (all optional except archive_root; absent inputs shrink the stats, never crash):
  <archive_root>/*/state.json · ledger.md · trace.jsonl · escape-defects.md      (sdlc_state.py archive output)
  --pr-watch  .sdlc/pr-watch/pr-N.json (evidence logs) + pr-N.counters.json           (/review-loop)
  --ratchet-logs  **/results.tsv                                                        (/ratchet)
  --routing / --loops   the current harness parameters (defaults: sdlc/assets/*.yaml)

Rules of the loop (compiled):
  - fewer than --min-features archives → baseline stats only, proposals: [] , note: insufficient_samples
  - every proposal has target ∈ TARGETS, current, proposed, evidence[≥1], expected_delta, risk, verify_by, delivered_as
  - sycophancy proxy: ACCEPT / (ACCEPT+REJECT+REPLY+ESCALATE) ≥ 0.95 over ≥ 5 threads → review-loop fix_list
  - reviewer precision: 1 - REJECT/judged. 低精确率与 sycophancy 是相反方向的两种病，别混在一个指标里：
    ACCEPT 太高 = 修复方太顺从；REJECT 太高 = 评审方乱开枪（Greptile 实测 82% 召回但 36.5% 精确，
    316 条评论里 111 条挑刺、56 条是错的）。精确率 < 0.6（≥ 5 条已裁决）→ 提案落到评审侧，
    并建议把该槽换成非本家供应商（pick_evaluators.py 的分配是可执行的对象）
  - a budget is proposed lower only if NO feature ever touched it; higher only if ≥ 50% of features exhausted it AND
    no repeat/oscillation/plateau escalation happened at that layer (those escalations were right, not budget-starved)
Exit 0 always (reporting tool); 2 on IO error.
"""
import argparse
import datetime as _dt
import glob
import json
import math
import os
import re
import sys

TARGETS = {
    "routing.budgets.<track>.<key>", "routing.fingerprint_repeat_limit", "routing.plateau_rounds",
    "review-loop.MAX_ROUNDS", "review-loop.MAX_THREAD_STRIKES", "acceptance-fleet.isolation_min",
    "pr-review.b_tier_thresholds", "code-reviewer.focus_allocation", "<skill>.fix_list",
    "acceptance-fleet.evaluators.cross_vendor",
}
LAYER_KEY = {"card": "card_retries", "plan": "plan_reflows", "task": "task_reflows", "ontology": "ontology_reflows"}


def load_yaml(path):
    try:
        import yaml
    except ImportError:
        sys.stderr.write("tune: PyYAML required\n"); sys.exit(2)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


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


def escape_rows(path):
    rows = []
    if not os.path.isfile(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("|") and not line.startswith("|---") and not line.lower().startswith("| at"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                rows.append(cells)
    return rows


def pct(n, d):
    return round(100.0 * n / d) if d else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archive_root"); ap.add_argument("--pr-watch"); ap.add_argument("--ratchet-logs")
    ap.add_argument("--routing"); ap.add_argument("--loops"); ap.add_argument("--skills-root")
    ap.add_argument("--out"); ap.add_argument("--min-features", type=int, default=2); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(here, "..", "..", "sdlc", "assets")
    routing = load_yaml(a.routing or os.path.join(assets, "routing.yaml"))
    loops = {l["id"]: l for l in (load_yaml(a.loops or os.path.join(assets, "loops.yaml")).get("loops") or [])}
    budgets = routing.get("budgets") or {}
    rl_budget = ((loops.get("review_loop") or {}).get("stop") or {}).get("budget") or {}
    max_rounds = int(rl_budget.get("rounds", 10)); max_strikes = int(rl_budget.get("thread_strikes", 3))

    # ---------------- archives ----------------
    feats = []
    for sp in sorted(glob.glob(os.path.join(a.archive_root, "*", "state.json"))):
        d = os.path.dirname(sp)
        st = read_json(sp, {})
        if not st:
            continue
        cnt = st.get("counters") or {}
        track = st.get("track") if st.get("track") in ("psl", "task") else "task"
        trace = read_trace(os.path.join(d, "trace.jsonl"))
        fails = [e for e in trace if e.get("kind") == "fail"]
        conv = {}
        for e in fails:
            t = ((e.get("convergence") or {}).get("type")) or "none"
            conv[t] = conv.get(t, 0) + 1
        rules = {}
        for e in fails:
            for r in e.get("refs") or []:
                if r.get("type") == "decided_by" and str(r.get("target", "")).startswith("routing."):
                    rid = r["target"].split(".", 1)[1]; rules[rid] = rules.get(rid, 0) + 1
        escapes = escape_rows(os.path.join(d, "escape-defects.md"))
        esc_layers = [row[5] for row in escapes if len(row) > 5]
        feats.append({
            "feature": st.get("slug"), "track": track, "stage": st.get("stage"),
            "counters": {k: int(cnt.get(k, 0) or 0) for k in ("card", "plan", "task", "ontology", "world")},
            "budgets": budgets.get(track, {}),
            "convergence": conv, "rules": rules, "fails": len(fails),
            "reflows": sum(1 for e in trace if e.get("kind") == "reflow"),
            "escapes": len(escapes), "escape_layers": esc_layers,
            "waivers": len(st.get("waivers") or []),
            "g1": ((st.get("gates") or {}).get("g1") or {}).get("verdict"),
            "g1_attribution": ((st.get("gates") or {}).get("g1") or {}).get("attribution"),
            "review_rounds": (st.get("review") or {}).get("rounds"),
            "trace_events": len(trace),
        })

    # ---------------- pr-watch ----------------
    prs = []
    if a.pr_watch and os.path.isdir(a.pr_watch):
        for ej in sorted(glob.glob(os.path.join(a.pr_watch, "pr-*.json"))):
            if ej.endswith(".counters.json"):
                continue
            ev = read_json(ej, {}) or {}
            n = re.search(r"pr-(\d+)\.json$", ej)
            prn = int(n.group(1)) if n else ev.get("pr")
            counters = read_json(os.path.join(a.pr_watch, f"pr-{prn}.counters.json"), {}) or {}
            dist = {"ACCEPT": 0, "REJECT": 0, "REPLY": 0, "ESCALATE": 0, "SKIPPED": 0}
            for c in ev.get("comments") or []:
                v = str(c.get("verdict", "")).upper()
                if v in dist:
                    dist[v] += 1
            judged = dist["ACCEPT"] + dist["REJECT"] + dist["REPLY"] + dist["ESCALATE"]
            accept_rate = round(dist["ACCEPT"] / judged, 3) if judged else None
            strikes = counters.get("strikes") or {}
            prs.append({
                "pr": prn, "rounds": int(counters.get("rounds", len(ev.get("rounds") or []))),
                "verdicts": dist, "judged": judged, "accept_rate": accept_rate,
                # 精确率 = 站得住的主张 / 已裁决的主张。REJECT 意味着这条评审主张被验证后不成立，
                # 那是**评审方**的误报，不是修复方的顺从——两者要分开数，否则一个指标同时被两种病拉扯。
                "precision": round((judged - dist["REJECT"]) / judged, 3) if judged else None,
                "low_precision": bool(judged >= 5 and judged and (judged - dist["REJECT"]) / judged < 0.6),
                "sycophancy_suspect": bool(judged >= 5 and accept_rate is not None and accept_rate >= 0.95),
                "threads_at_strike_limit": sum(1 for v in strikes.values() if int(v) >= max_strikes),
                "strike_threads": len(strikes),
            })

    # ---------------- ratchet ----------------
    ratchet = []
    if a.ratchet_logs and os.path.isdir(a.ratchet_logs):
        for tsv in glob.glob(os.path.join(a.ratchet_logs, "**", "results.tsv"), recursive=True):
            with open(tsv, encoding="utf-8") as f:
                rows = [l for l in f if l.strip()]
            ratchet.append({"file": os.path.relpath(tsv, a.ratchet_logs), "rounds": max(0, len(rows) - 1)})

    # ---------------- stats ----------------
    def per_layer(track):
        fs = [f for f in feats if f["track"] == track]
        out = {}
        for layer, key in LAYER_KEY.items():
            b = (budgets.get(track) or {}).get(key)
            used = [f["counters"][layer] for f in fs]
            exhausted = sum(1 for u in used if isinstance(b, int) and u >= b)
            conv_esc = sum(sum(v for t, v in f["convergence"].items() if t in ("repeat", "oscillation", "plateau")) for f in fs)
            out[key] = {"budget": b, "used": used, "max_used": max(used) if used else None,
                        "features": len(fs), "exhausted_in": exhausted,
                        "utilisation_pct": (pct(sum(used), b * len(fs)) if isinstance(b, int) and fs and b else None),
                        "convergence_escalations": conv_esc}
        return out

    stats = {
        "features": len(feats), "tracks": {t: sum(1 for f in feats if f["track"] == t) for t in ("psl", "task")},
        "layers": {t: per_layer(t) for t in ("psl", "task") if any(f["track"] == t for f in feats)},
        "rule_frequency": {}, "convergence_types": {},
        "escapes": sum(f["escapes"] for f in feats), "escape_layers": {},
        "waivers": sum(f["waivers"] for f in feats), "features_with_waivers": sum(1 for f in feats if f["waivers"]),
        "g1": {"psl_features": sum(1 for f in feats if f["track"] == "psl"),
               "rejects": sum(1 for f in feats if f["g1"] == "reject"),
               "rule_error": sum(1 for f in feats if f["g1_attribution"] == "rule_error"),
               "derivation_error": sum(1 for f in feats if f["g1_attribution"] == "derivation_error")},
        "review": {"prs": len(prs), "max_rounds_param": max_rounds, "max_strikes_param": max_strikes,
                   "rounds": [p["rounds"] for p in prs], "max_rounds_used": max([p["rounds"] for p in prs], default=None),
                   "hit_round_budget": sum(1 for p in prs if p["rounds"] >= max_rounds),
                   "sycophancy_suspects": [p["pr"] for p in prs if p["sycophancy_suspect"]],
                   "low_precision_prs": [p["pr"] for p in prs if p["low_precision"]],
                   "threads_at_strike_limit": sum(p["threads_at_strike_limit"] for p in prs),
                   "verdicts": {k: sum(p["verdicts"][k] for p in prs) for k in ("ACCEPT", "REJECT", "REPLY", "ESCALATE", "SKIPPED")}},
        "ratchet": {"runs": len(ratchet), "rounds": [r["rounds"] for r in ratchet]},
    }
    for f in feats:
        for k, v in f["rules"].items():
            stats["rule_frequency"][k] = stats["rule_frequency"].get(k, 0) + v
        for k, v in f["convergence"].items():
            stats["convergence_types"][k] = stats["convergence_types"].get(k, 0) + v
        for l in f["escape_layers"]:
            stats["escape_layers"][l] = stats["escape_layers"].get(l, 0) + 1

    # ---------------- proposals ----------------
    proposals, notes = [], []
    n_feat = len(feats)

    def add(target, current, proposed, evidence, expected_delta, risk, verify_by, delivered_as, apply):
        proposals.append({"id": f"P-{len(proposals) + 1}", "target": target, "current": current, "proposed": proposed,
                          "evidence": evidence, "expected_delta": expected_delta, "risk": risk, "verify_by": verify_by,
                          "delivered_as": delivered_as, "apply": apply})

    if n_feat < a.min_features:
        notes.append(f"insufficient_samples: {n_feat} archive(s) < --min-features {a.min_features}; baseline only, no proposals")
    else:
        for track, layers in stats["layers"].items():
            for key, s in layers.items():
                b = s["budget"]
                if not isinstance(b, int) or s["features"] < a.min_features:
                    continue
                if s["max_used"] == 0 and b > 1:
                    add(f"routing.budgets.{track}.{key}", b, b - 1,
                        [f"{track} track: {s['features']} features, {key} never touched (max_used=0, budget={b})"],
                        f"{key} escalation count unchanged (was 0); fewer silent retries available", "low — a layer nobody hits loses one retry",
                        f"next retro: {track}.{key} utilisation stays 0 and reflow_distribution.{key.split('_')[0]} does not rise",
                        "PR", {"kind": "routing_budget", "track": track, "key": key, "value": b - 1})
                elif s["exhausted_in"] * 2 >= s["features"] and s["convergence_escalations"] == 0:
                    add(f"routing.budgets.{track}.{key}", b, b + 1,
                        [f"{track} track: {s['exhausted_in']}/{s['features']} features exhausted {key}={b}",
                         "no repeat/oscillation/plateau escalation at that layer — the retries were making progress"],
                        f"budget_exhausted escalations at {key} drop; lead time +1 retry worst case", "medium — more retries on a wrong-layer error burn tokens",
                        f"next retro: features exhausting {key} < 50%", "PR",
                        {"kind": "routing_budget", "track": track, "key": key, "value": b + 1})
                elif s["exhausted_in"] * 2 >= s["features"] and s["convergence_escalations"] > 0:
                    notes.append(f"{track}.{key}: exhausted in {s['exhausted_in']}/{s['features']} features but {s['convergence_escalations']} convergence escalation(s) — budget is not the problem, the layer above is; no change proposed")
        rv = stats["review"]
        if rv["prs"] >= a.min_features:
            if rv["max_rounds_used"] is not None and rv["max_rounds_used"] * 2.5 <= max_rounds and rv["hit_round_budget"] == 0:
                new = max(3, math.ceil(rv["max_rounds_used"] * 1.5))
                add("review-loop.MAX_ROUNDS", max_rounds, new,
                    [f"{rv['prs']} PRs: rounds used {rv['rounds']}, max {rv['max_rounds_used']} ≤ 40% of MAX_ROUNDS={max_rounds}"],
                    "exit 30 still never fires; runaway loops stop sooner", "low — a legitimately long review would need a manual MAX_ROUNDS override",
                    "next tune: hit_round_budget stays 0", "PR", {"kind": "pr_poll_env", "var": "MAX_ROUNDS", "value": new})
            elif rv["hit_round_budget"] * 2 >= rv["prs"]:
                add("review-loop.MAX_ROUNDS", max_rounds, max_rounds + 2,
                    [f"{rv['hit_round_budget']}/{rv['prs']} PRs hit MAX_ROUNDS={max_rounds}"],
                    "fewer hard stops with unconverged threads", "medium — may hide reviewer/contract disagreement that belongs at G3",
                    "next tune: hit_round_budget < 50% and REJECT share unchanged", "PR", {"kind": "pr_poll_env", "var": "MAX_ROUNDS", "value": max_rounds + 2})
            for prn in rv["sycophancy_suspects"]:
                p = next(x for x in prs if x["pr"] == prn)
                add("review-loop.fix_list", None, f"L2: audit ACCEPT verdicts on PR #{prn}",
                    [f"PR #{prn}: ACCEPT {p['verdicts']['ACCEPT']}/{p['judged']} judged threads ({round(100 * p['accept_rate'])}%) — REJECT is legitimate and expected; 95%+ ACCEPT over ≥5 threads is the sycophancy proxy (SWE-Review)"],
                    "REJECT share > 0 on the next PR with ≥5 threads", "none — a fix_list entry", "review-loop gate.json fix_list carries the item until an L2 audit closes it",
                    "gate.json fix_list", {"kind": "gate_fix_list", "skill": "review-loop", "item": f"L2: audit ACCEPT verdicts on PR #{prn} — {p['verdicts']['ACCEPT']}/{p['judged']} ACCEPT; check whether any should have been REJECT/REPLY (sycophancy proxy)"})
            for prn in rv["low_precision_prs"]:
                p_ = next(x for x in prs if x["pr"] == prn)
                add("acceptance-fleet.evaluators.cross_vendor", "rank1/rank2 slots per evaluators.yaml",
                    f"force a non-home vendor on the reviewer slot for PR #{prn}'s focus",
                    [f"PR #{prn}: precision {p_['precision']} — {p_['verdicts']['REJECT']}/{p_['judged']} judged claims did not survive verification; "
                     "a reviewer that is wrong 40%+ of the time costs more attention than it saves (Greptile 2026: 82% recall, 36.5% precision)"],
                    "precision ≥ 0.6 on the next PR with ≥5 judged threads",
                    "low — the assignment is recorded either way; if no other vendor is available the caveat is what changes, not the verdict",
                    "next tune: precision rises above 0.6 or the same-vendor caveat explains why it cannot",
                    "PR", {"kind": "evaluator_assignment", "pr": prn, "prefer_cross_vendor": True})
                add("pr-review.b_tier_thresholds", None, f"raise the evidence bar for PR #{prn}'s focus",
                    [f"PR #{prn}: {p_['verdicts']['REJECT']}/{p_['judged']} claims rejected on verification — "
                     "P0/P1 already require reproduction; the misses are concentrated below that line"],
                    "fewer REJECT verdicts without losing ACCEPTs", "medium — a higher bar drops true findings too",
                    "next tune: REJECT share falls while ACCEPT count holds", "PR",
                    {"kind": "gate_fix_list", "skill": "pr-review",
                     "item": f"precision {p_['precision']} on PR #{prn}: audit which tier the rejected claims came from"})
            if rv["threads_at_strike_limit"] and rv["threads_at_strike_limit"] * 2 >= rv["prs"]:
                add("review-loop.fix_list", None, "strike limit reached on ≥50% of PRs — audit REJECT evidence quality before raising MAX_THREAD_STRIKES",
                    [f"{rv['threads_at_strike_limit']} thread(s) frozen at MAX_THREAD_STRIKES={max_strikes} across {rv['prs']} PRs"],
                    "frozen threads drop without touching the budget", "none", "next tune: threads_at_strike_limit falls",
                    "gate.json fix_list", {"kind": "gate_fix_list", "skill": "review-loop", "item": f"strike limit hit on {rv['threads_at_strike_limit']} threads: are REJECT replies carrying evidence (code line / doc / test)?"})
        if stats["escapes"]:
            route = {"task": "donewhen-extract", "plan": "plan-cards", "card": "implement", "ontology": "dos-extract", "world": "psl"}
            for layer, n in sorted(stats["escape_layers"].items()):
                skill = route.get(layer, "acceptance-fleet")
                add(f"{skill}.fix_list", None, f"{n} escape defect(s) attributed to layer {layer}",
                    [f"escape-defects.md rows attributed to {layer}: {n} across {n_feat} features",
                     "run `trace.py why <AC or card>` on each to see which gate let it through"],
                    "escape rate at that layer falls next period", "none", "next retro: escape_defects at that layer < current",
                    "gate.json fix_list", {"kind": "gate_fix_list", "skill": skill, "item": f"{n} escape defect(s) attributed to {layer} layer — which gate missed? (trace.py why)"})
        if stats["features_with_waivers"] * 2 >= n_feat and stats["waivers"]:
            add("sdlc.fix_list", None, "waivers on ≥50% of features — a prerequisite may be wrong, not the people",
                [f"{stats['waivers']} waiver(s) across {stats['features_with_waivers']}/{n_feat} features"],
                "waiver count falls or a prerequisite is changed by PR", "none", "next retro: waivers < current",
                "gate.json fix_list", {"kind": "gate_fix_list", "skill": "sdlc", "item": f"{stats['waivers']} waivers on {stats['features_with_waivers']}/{n_feat} features — read the reasons; a repeated reason means the prerequisite is mis-specified"})
        g1 = stats["g1"]
        if g1["psl_features"] >= a.min_features and g1["rule_error"] > g1["derivation_error"] and g1["rule_error"]:
            add("psl.fix_list", None, "G1 rejects are mostly rule_error — the PSL is under-specified where derivation diverges",
                [f"G1: {g1['rejects']} reject(s) over {g1['psl_features']} PSL features; rule_error={g1['rule_error']} derivation_error={g1['derivation_error']}"],
                "rule_error share falls after PSL Open Questions are closed", "none", "next retro: G1 rule_error < derivation_error",
                "gate.json fix_list", {"kind": "gate_fix_list", "skill": "psl", "item": f"G1 rule_error dominates ({g1['rule_error']}/{g1['rejects']}) — PSL laws need tightening where derivations disagree"})
        ct = stats["convergence_types"]
        if ct.get("oscillation", 0) and not ct.get("repeat", 0):
            notes.append(f"{ct['oscillation']} oscillation escalation(s) and 0 plain repeats — fingerprint_repeat_limit={routing.get('fingerprint_repeat_limit')} is not what stopped them; keep as is")
        if ct.get("plateau", 0):
            notes.append(f"{ct['plateau']} plateau escalation(s) at plateau_rounds={routing.get('plateau_rounds')} — read the failure reports before changing the threshold")

    for p in proposals:
        base = re.sub(r"^routing\.budgets\.\w+\.\w+$", "routing.budgets.<track>.<key>", p["target"])
        base = re.sub(r"^[\w-]+\.fix_list$", "<skill>.fix_list", base)
        if base not in TARGETS:
            sys.stderr.write(f"tune: internal error — target {p['target']} outside TARGETS\n"); sys.exit(2)

    out = {"generated_at": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
           "inputs": {"archive_root": a.archive_root, "pr_watch": a.pr_watch, "ratchet_logs": a.ratchet_logs,
                      "routing": a.routing or "sdlc/assets/routing.yaml", "min_features": a.min_features},
           "stats": stats, "proposals": proposals, "notes": notes,
           "rules": ["proposals never auto-apply — apply_proposal.py emits a diff / patch, a human opens the PR",
                     "one proposal per target per run; a target proposed in opposite directions on two consecutive runs stops being proposed (hill_climb plateau)"]}
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if a.out:
        try:
            import yaml
            with open(a.out, "w", encoding="utf-8") as f:
                yaml.safe_dump(json.loads(text), f, allow_unicode=True, sort_keys=False, width=120)
        except ImportError:
            with open(a.out, "w", encoding="utf-8") as f:
                f.write(text + "\n")
    if a.json or not a.out:
        print(text)
    else:
        print(json.dumps({"ok": True, "out": a.out, "features": n_feat, "proposals": len(proposals), "notes": notes}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
