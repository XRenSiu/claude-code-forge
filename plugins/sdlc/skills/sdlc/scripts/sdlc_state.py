#!/usr/bin/env python3
"""
sdlc_state.py — the compiled Control of /sdlc: the lifecycle state file and its transitions.

Why a script owns this (SKILL.state): the model proposes a transition, the runtime validates and
merges it. A bad proposal cannot corrupt the state — it is rejected, not merged. The state file is the
sufficient statistic for the run (只留状态，不留历史); history lives in ledger.md, which is append-only
and never rolled back (WikiSkill asymmetric rollback: artifacts roll back, judgments and failures don't).

Usage:
  sdlc_state.py init    --slug S --title T [--track psl|task] [--root .sdlc]
  sdlc_state.py show    [--slug S] [--root .sdlc]
  sdlc_state.py set     [--slug S] key=value ...          # dotted keys, whitelisted (see SETTABLE)
  sdlc_state.py advance [--slug S] <stage> [--force --reason R]
  sdlc_state.py gate    [--slug S] <g1|g2|g3> --verdict pass|reject|waived --by NAME
                        [--record PATH] [--attribution derivation_error|rule_error|none]
  sdlc_state.py card    [--slug S] CARD-xx --status todo|doing|done|blocked [--commit SHA]
  sdlc_state.py fail    [--slug S] --signal SIG [--card CARD-xx] [--fingerprint FP | --evidence TEXT]
                        [--routing PATH]                  # -> route decision JSON + counters + ledger
  sdlc_state.py ledger  [--slug S] --kind K --note TEXT [--signal S] [--layer L] [--decision D] [--by B]
  sdlc_state.py archive [--slug S] --to DIR               # copy state + ledger + listed artifacts

Exit codes: 0 ok · 1 rejected (transition invalid / prerequisite unmet / bad key) · 2 usage/IO error.
Every mutating command appends a ledger row. Writes are atomic (tmp + rename).

Mechanical guarantees (the non-waivable half):
  - stage transitions follow ORDER; skipping requires --force + --reason, recorded as a waiver
  - each stage's prerequisites (PREREQS) are checked against the state, not against the model's claim
  - gates are recorded with who/when/verdict; G2 pass requires a lock path; G1 reject requires attribution
  - `fail` consults routing.yaml, bumps the layer counter, detects fingerprint repeats, applies budgets by
    track, and emits an escalation decision the model must not override
Semantic half (a judge / a human, never this script): whether the candidate layer is the RIGHT layer.
"""
import argparse
import datetime as _dt
import hashlib
import json
import os
import shutil
import sys

ROOT_DEFAULT = ".sdlc"
ORDER = ["intake", "track", "issue", "branch", "contract", "g2", "cards", "implement",
         "acceptance", "pr", "review", "g3", "merge", "archive"]
SETTABLE = {
    "track", "title",
    "issue.number", "issue.url", "issue.kind",
    "branch.name", "branch.base",
    "contract.done_when", "contract.contract_yaml", "contract.source",
    "lock.path", "lock.signed_by", "lock.signed_at",
    "cards.dir", "cards.lint_passed",
    "acceptance.evaluation_result", "acceptance.meets_done_when", "acceptance.skipped_reason",
    "pr.number", "pr.url", "pr.size_class",
    "review.done", "review.exit_reason", "review.rounds",
    "merge.sha", "merge.merged_at",
    "gates.g3.required",
}
LAYER_COUNTERS = ["card", "plan", "task", "ontology", "world"]
BUDGET_KEY = {"card": "card_retries", "plan": "plan_reflows", "task": "task_reflows",
              "ontology": "ontology_reflows", "world": "world_reflows"}


def now():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def die(msg, code=2):
    sys.stderr.write(f"sdlc_state: {msg}\n")
    sys.exit(code)


def atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def resolve_slug(root, slug):
    if slug:
        return slug
    if not os.path.isdir(root):
        die(f"no {root}/ directory; run init first")
    dirs = [d for d in os.listdir(root) if os.path.isfile(os.path.join(root, d, "state.json"))]
    if len(dirs) == 1:
        return dirs[0]
    die(f"--slug required (found {len(dirs)} runs under {root}/: {sorted(dirs)})")


def paths(root, slug):
    d = os.path.join(root, slug)
    return d, os.path.join(d, "state.json"), os.path.join(d, "ledger.md")


def load(root, slug):
    _, sp, _ = paths(root, slug)
    if not os.path.isfile(sp):
        die(f"state not found: {sp}")
    with open(sp, encoding="utf-8") as f:
        return json.load(f)


def save(root, slug, st):
    _, sp, _ = paths(root, slug)
    st["updated_at"] = now()
    atomic_write(sp, json.dumps(st, ensure_ascii=False, indent=2) + "\n")


def ledger_append(root, slug, kind, note="", stage=None, signal="", layer="", fingerprint="",
                  decision="", by="engine"):
    d, _, lp = paths(root, slug)
    os.makedirs(d, exist_ok=True)
    if not os.path.isfile(lp):
        header = ("# Ledger — %s\n\n> 只增不删。产物可回滚；判据、失败记录、被拒的修复、路由决定不回滚。\n\n"
                  "| at | stage | kind | signal / gate | layer | fingerprint | evidence | decision | by |\n"
                  "|---|---|---|---|---|---|---|---|---|\n") % slug
        atomic_write(lp, header)
    cell = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
    row = "| %s | %s | %s | %s | %s | %s | %s | %s | %s |\n" % tuple(
        cell(x) for x in (now(), stage or "", kind, signal, layer, fingerprint, note, decision, by))
    with open(lp, "a", encoding="utf-8") as f:
        f.write(row)


def get_path(st, dotted, default=None):
    cur = st
    for k in dotted.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def set_path(st, dotted, value):
    parts = dotted.split(".")
    cur = st
    for k in parts[:-1]:
        cur = cur.setdefault(k, {})
    cur[parts[-1]] = value


def coerce(v):
    if v in ("true", "false"):
        return v == "true"
    if v == "null":
        return None
    try:
        return int(v)
    except ValueError:
        return v


# ---- prerequisites: checked against state, never against the model's claim ------------------
def prereqs(st, target):
    unmet = []
    need = lambda cond, msg: (None if cond else unmet.append(msg))
    if target == "track":
        need(st.get("title"), "title set")
    elif target == "issue":
        need(st.get("track") in ("psl", "task"), "track decided (psl|task)")
        if st.get("track") == "psl":
            need(get_path(st, "gates.g1.verdict") in ("pass", "waived"),
                 "G1 recorded as pass (PSL track) — run `gate g1`")
    elif target == "branch":
        need(get_path(st, "issue.number"), "issue.number set")
    elif target == "contract":
        need(get_path(st, "branch.name"), "branch.name set")
    elif target == "g2":
        dw = get_path(st, "contract.done_when")
        need(dw and os.path.isfile(dw), "contract.done_when points at an existing file")
    elif target == "cards":
        need(get_path(st, "gates.g2.verdict") == "pass", "G2 verdict pass — run `gate g2`")
        need(get_path(st, "lock.path") and os.path.isfile(get_path(st, "lock.path")), "lock.path exists")
    elif target == "implement":
        need(get_path(st, "cards.lint_passed") is True, "cards.lint_passed true (lint_cards.py)")
        need(get_path(st, "cards.items"), "at least one card registered (`card CARD-xx --status todo`)")
    elif target == "acceptance":
        items = get_path(st, "cards.items", {}) or {}
        pending = [k for k, v in items.items() if v.get("status") != "done"]
        need(not pending, f"all cards done (pending: {pending})")
    elif target == "pr":
        ok = get_path(st, "acceptance.evaluation_result") or get_path(st, "acceptance.skipped_reason")
        need(ok, "acceptance.evaluation_result path OR acceptance.skipped_reason (TASK 轨轻量, recorded)")
    elif target == "review":
        need(get_path(st, "pr.number"), "pr.number set")
    elif target == "g3":
        need(get_path(st, "review.done") is True, "review.done true")
    elif target == "merge":
        if get_path(st, "gates.g3.required", True):
            need(get_path(st, "gates.g3.verdict") in ("pass", "waived"), "G3 verdict pass — run `gate g3`")
        else:
            need(get_path(st, "review.done") is True, "review.done true")
    elif target == "archive":
        need(get_path(st, "merge.sha"), "merge.sha set")
    return unmet


def next_allowed(st, target):
    cur = st["stage"]
    ci, ti = ORDER.index(cur), ORDER.index(target)
    if ti == ci + 1:
        return True
    # legal skip: g3 not required → review → merge
    if cur == "review" and target == "merge" and get_path(st, "gates.g3.required", True) is False:
        return True
    return False


# ---- commands ------------------------------------------------------------------------------
def cmd_init(a):
    d, sp, _ = paths(a.root, a.slug)
    if os.path.isfile(sp):
        die(f"already initialised: {sp} (use show / advance)", 1)
    os.makedirs(d, exist_ok=True)
    st = {
        "version": 1, "slug": a.slug, "title": a.title, "track": a.track or "unset",
        "stage": "intake", "created_at": now(), "updated_at": now(),
        "gates": {"g1": {"required": a.track == "psl", "verdict": "pending"},
                  "g2": {"required": True, "verdict": "pending"},
                  "g3": {"required": True, "verdict": "pending"}},
        "counters": {k: 0 for k in LAYER_COUNTERS} | {"last_fingerprints": {}, "fingerprint_repeats": {}},
        "waivers": [], "assumptions": [], "artifacts": {},
    }
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "init", f"title={a.title} track={st['track']}", stage="intake")
    print(json.dumps({"ok": True, "state": sp}, ensure_ascii=False))


def cmd_show(a):
    st = load(a.root, a.slug)
    print(json.dumps(st, ensure_ascii=False, indent=2))


def cmd_set(a):
    st = load(a.root, a.slug)
    changed = []
    for kv in a.pairs:
        if "=" not in kv:
            die(f"expected key=value, got {kv!r}")
        k, v = kv.split("=", 1)
        if k not in SETTABLE:
            die(f"key not settable: {k} (allowed: {sorted(SETTABLE)})", 1)
        if k == "track" and v not in ("psl", "task"):
            die("track must be psl|task", 1)
        set_path(st, k, coerce(v))
        if k == "track":
            st["gates"]["g1"]["required"] = (v == "psl")
        changed.append(k)
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "set", ", ".join(a.pairs), stage=st["stage"])
    print(json.dumps({"ok": True, "changed": changed}, ensure_ascii=False))


def cmd_advance(a):
    st = load(a.root, a.slug)
    if a.stage not in ORDER:
        die(f"unknown stage {a.stage}; stages: {ORDER}", 1)
    problems = []
    if not next_allowed(st, a.stage):
        problems.append(f"not the next stage after {st['stage']} (order: {' → '.join(ORDER)})")
    problems += prereqs(st, a.stage)
    if problems and not a.force:
        print(json.dumps({"ok": False, "stage": st["stage"], "target": a.stage, "unmet": problems},
                         ensure_ascii=False, indent=2))
        sys.exit(1)
    if problems:
        if not a.reason:
            die("--force requires --reason (the waiver is recorded, not silent)", 1)
        st.setdefault("waivers", []).append({"stage": a.stage, "reason": a.reason, "at": now(),
                                             "unmet": problems})
        ledger_append(a.root, a.slug, "waiver", f"forced → {a.stage}: {a.reason} | unmet: {problems}",
                      stage=st["stage"], decision="forced", by="human")
    prev = st["stage"]
    st["stage"] = a.stage
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "advance", f"{prev} → {a.stage}", stage=a.stage)
    print(json.dumps({"ok": True, "from": prev, "to": a.stage, "waived": bool(problems)}, ensure_ascii=False))


def cmd_gate(a):
    st = load(a.root, a.slug)
    g = st["gates"].setdefault(a.gate, {"required": True, "verdict": "pending"})
    if a.gate == "g2" and a.verdict == "pass" and not (get_path(st, "lock.path") and os.path.isfile(get_path(st, "lock.path"))):
        die("G2 pass requires lock.path (run lock_done_when.py sign, then `set lock.path=...`)", 1)
    if a.gate == "g1" and a.verdict == "reject" and a.attribution in (None, "none"):
        die("G1 reject requires --attribution derivation_error|rule_error (feeds world-layer routing)", 1)
    g.update({"verdict": a.verdict, "by": a.by, "at": now()})
    if a.record:
        g["record"] = a.record
    if a.attribution:
        g["attribution"] = a.attribution
    if a.gate == "g1" and a.verdict == "reject":
        st["counters"]["world"] += 1
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "gate", a.record or "", stage=st["stage"], signal=a.gate,
                  layer=("world" if a.gate == "g1" else ""), decision=f"{a.verdict}"
                  + (f" ({a.attribution})" if a.attribution else ""), by=a.by)
    print(json.dumps({"ok": True, "gate": a.gate, "verdict": a.verdict}, ensure_ascii=False))


def cmd_card(a):
    st = load(a.root, a.slug)
    items = st.setdefault("cards", {}).setdefault("items", {})
    c = items.setdefault(a.card, {"status": "todo", "retries": 0, "commits": []})
    c["status"] = a.status
    if a.commit:
        c.setdefault("commits", []).append(a.commit)
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "card", f"{a.card} → {a.status}" + (f" commit {a.commit}" if a.commit else ""),
                  stage=st["stage"])
    print(json.dumps({"ok": True, "card": a.card, "status": a.status}, ensure_ascii=False))


def load_routing(path):
    try:
        import yaml
    except ImportError:
        die("PyYAML required to read routing.yaml (pip install pyyaml)")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def cmd_fail(a):
    st = load(a.root, a.slug)
    routing_path = a.routing or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "routing.yaml")
    rt = load_routing(routing_path)
    rule = next((r for r in rt.get("rules", []) if r.get("signal") == a.signal), None)
    if not rule:
        die(f"unknown signal {a.signal}; known: {[r['signal'] for r in rt.get('rules', [])]}", 1)
    fp = a.fingerprint or hashlib.sha1((a.evidence or a.signal).encode("utf-8")).hexdigest()[:12]
    layer = rule["layer"]
    key = f"{a.card or layer}:{layer}"
    cnt = st["counters"]
    repeats = cnt.setdefault("fingerprint_repeats", {})
    last = cnt.setdefault("last_fingerprints", {})
    repeat = repeats.get(key, 0) + 1 if last.get(key) == fp else 1
    repeats[key] = repeat
    last[key] = fp
    if layer in LAYER_COUNTERS:
        cnt[layer] = cnt.get(layer, 0) + 1
    if a.card:
        c = st.setdefault("cards", {}).setdefault("items", {}).setdefault(a.card, {"status": "doing", "retries": 0, "commits": []})
        if layer == "card":
            c["retries"] = c.get("retries", 0) + 1
        c["last_fingerprint"] = fp

    track = st.get("track") if st.get("track") in ("psl", "task") else "task"
    budgets = rt.get("budgets", {}).get(track, {})
    budget = budgets.get(BUDGET_KEY.get(layer, ""), None)
    used = cnt.get(layer, 0) if layer in LAYER_COUNTERS else None
    limit = rt.get("fingerprint_repeat_limit", 2)
    escalate, why = False, []
    if repeat >= limit:
        escalate, why = True, why + [f"same fingerprint {fp} repeated {repeat}× (limit {limit}) — no progress"]
    if budget is not None and used is not None and used >= budget:
        escalate, why = True, why + [f"{layer} budget exhausted ({used}/{budget}, track={track})"]
    if rule.get("handler") == "human":
        escalate, why = True, why + ["rule handler is human"]
    outer = None
    if layer in LAYER_COUNTERS:
        i = LAYER_COUNTERS.index(layer)
        outer = LAYER_COUNTERS[i + 1] if i + 1 < len(LAYER_COUNTERS) else "human"
    decision = {
        "rule": rule["id"], "signal": a.signal, "layer": layer, "handler": rule.get("handler"),
        "action": rule.get("action"), "fingerprint": fp, "fingerprint_repeat": repeat,
        "layer_count": used, "budget": budget, "track": track,
        "escalate": escalate, "escalate_to": (outer if escalate and rule.get("handler") != "human" else "human") if escalate else None,
        "why": why, "note": rule.get("note", ""),
        "next": ("write failure report (assets/failure_report.md) and stop for human confirmation" if escalate
                 else f"engine may {rule.get('action')} once more"),
    }
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "fail", a.evidence or "", stage=st["stage"], signal=a.signal, layer=layer,
                  fingerprint=fp, decision=("ESCALATE→" + str(decision["escalate_to"])) if escalate else rule.get("action"))
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    sys.exit(0)


def cmd_ledger(a):
    st = load(a.root, a.slug)
    ledger_append(a.root, a.slug, a.kind, a.note, stage=st["stage"], signal=a.signal or "", layer=a.layer or "",
                  decision=a.decision or "", by=a.by or "engine")
    print(json.dumps({"ok": True}, ensure_ascii=False))


def cmd_archive(a):
    st = load(a.root, a.slug)
    d, sp, lp = paths(a.root, a.slug)
    os.makedirs(a.to, exist_ok=True)
    copied = []
    for src in [sp, lp] + [p for p in (st.get("artifacts") or {}).values() if p and os.path.isfile(p)]:
        dst = os.path.join(a.to, os.path.basename(src))
        shutil.copy2(src, dst)
        copied.append(dst)
    manifest = {"slug": a.slug, "archived_at": now(), "stage": st["stage"], "files": copied,
                "counters": st.get("counters"), "gates": st.get("gates")}
    atomic_write(os.path.join(a.to, "archive-manifest.json"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    ledger_append(a.root, a.slug, "archive", f"→ {a.to} ({len(copied)} files)", stage=st["stage"])
    print(json.dumps({"ok": True, "to": a.to, "files": copied}, ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    # --root/--slug live on every subcommand (argparse subparser defaults would clobber top-level values)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=ROOT_DEFAULT)
    common.add_argument("--slug")
    sub = p.add_subparsers(dest="cmd", required=True)
    P = lambda name: sub.add_parser(name, parents=[common])

    s = P("init"); s.add_argument("--title", required=True); s.add_argument("--track", choices=["psl", "task"])
    P("show")
    s = P("set"); s.add_argument("pairs", nargs="+")
    s = P("advance"); s.add_argument("stage"); s.add_argument("--force", action="store_true"); s.add_argument("--reason")
    s = P("gate"); s.add_argument("gate", choices=["g1", "g2", "g3"]); s.add_argument("--verdict", required=True, choices=["pass", "reject", "waived"])
    s.add_argument("--by", required=True); s.add_argument("--record"); s.add_argument("--attribution", choices=["derivation_error", "rule_error", "none"])
    s = P("card"); s.add_argument("card"); s.add_argument("--status", required=True, choices=["todo", "doing", "done", "blocked"]); s.add_argument("--commit")
    s = P("fail"); s.add_argument("--signal", required=True); s.add_argument("--card"); s.add_argument("--fingerprint"); s.add_argument("--evidence"); s.add_argument("--routing")
    s = P("ledger"); s.add_argument("--kind", required=True); s.add_argument("--note", required=True); s.add_argument("--signal"); s.add_argument("--layer"); s.add_argument("--decision"); s.add_argument("--by")
    s = P("archive"); s.add_argument("--to", required=True)

    a = p.parse_args()
    if a.cmd == "init":
        if not a.slug:
            die("init requires --slug")
        return cmd_init(a)
    a.slug = resolve_slug(a.root, a.slug)
    return {"show": cmd_show, "set": cmd_set, "advance": cmd_advance, "gate": cmd_gate, "card": cmd_card,
            "fail": cmd_fail, "ledger": cmd_ledger, "archive": cmd_archive}[a.cmd](a)


if __name__ == "__main__":
    main()
