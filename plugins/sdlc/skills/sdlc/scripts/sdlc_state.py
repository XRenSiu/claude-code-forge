#!/usr/bin/env python3
"""
sdlc_state.py — the compiled Control of /sdlc: the lifecycle state file and its transitions.

Why a script owns this (SKILL.state): the model proposes a transition, the runtime validates and
merges it. A bad proposal cannot corrupt the state — it is rejected, not merged. The state file is the
sufficient statistic for the run (只留状态，不留历史); history lives in ledger.md, which is append-only
and never rolled back (WikiSkill asymmetric rollback: artifacts roll back, judgments and failures don't).
Since v0.6.0 every ledger row is mirrored into trace.jsonl with typed edges (caused_by / decided_by /
supersedes / implements / references / depends_on / rejected_alternative) — see trace.py.

Usage:
  sdlc_state.py init    --slug S --title T [--track psl|task] [--root .sdlc]
  sdlc_state.py show    [--slug S] [--root .sdlc]
  sdlc_state.py set     [--slug S] key=value ...          # dotted keys, whitelisted (see SETTABLE)
  sdlc_state.py advance [--slug S] <stage> [--force --reason R]
  sdlc_state.py gate    [--slug S] <g1|g2|g3> --verdict pass|reject|waived --by NAME
                        [--record PATH] [--attribution derivation_error|rule_error|none]
                        [--secondary-attribution derivation_error|rule_error]…  (recorded, never counted)
                        [--signer-kind human|delegated_agent] [--authorization TEXT]   # delegated requires authorization
  sdlc_state.py card    [--slug S] CARD-xx --status todo|doing|done|blocked [--commit SHA] [--ac AC-id ...]
  sdlc_state.py fail    [--slug S] --signal SIG [--card CARD-xx] [--fingerprint FP | --evidence TEXT]
                        [--score X] [--by REPORTER] [--routing PATH]   # -> route decision JSON + counters + ledger
  sdlc_state.py waive   [--slug S] --signal SIG --reason R --by WHO
                        [--signer-kind human|delegated_agent] [--authorization TEXT]
                        [--fingerprint FP] [--card CARD-xx] [--layer L] [--stage S] [--scope TEXT] [--ref type:target ...]
                        # a waiver WITHOUT a transition; prints the event id to cite as a waiver_ref
  sdlc_state.py report  [--slug S] --path FAILURE_REPORT.md            # clears pending.failure_report
  sdlc_state.py check-clean [--slug S] [--as-hook]                     # exit 0 clean / 1 dirty; --as-hook prints Stop-hook JSON
  sdlc_state.py graph   check|next|render [--graph PATH] [--full]      # execution graph as data (assets/graph.yaml)
  sdlc_state.py loops   [--slug S] [--loops PATH] [--pr-watch DIR] [--ratchet-dir DIR]   # budget consumption per loop
  sdlc_state.py ledger  [--slug S] --kind K --note TEXT [--signal S] [--layer L] [--decision D] [--by B]
                        [--fingerprint FP] [--card CARD-xx] [--ref type:target ...]
  sdlc_state.py archive [--slug S] --to DIR               # copy state + ledger + trace + contract + listed artifacts

Exit codes: 0 ok · 1 rejected (transition invalid / prerequisite unmet / bad key / dirty) · 2 usage/IO error.
Every mutating command appends a ledger row (and a trace event). Writes are atomic (tmp + rename).

Mechanical guarantees (the non-waivable half):
  - stage transitions follow ORDER; skipping requires --force + --reason, recorded as a waiver
  - each stage's prerequisites (PREREQS) are checked against the state, not against the model's claim
  - gates are recorded with who/when/verdict; G2 pass requires a lock path; G1 pass requires world.derived_dir
    (psl-derive products exist) and G1 reject requires attribution
  - `fail` consults routing.yaml, bumps the layer counter, keeps a fingerprint history per key and detects
    repeat (same fp N×), oscillation (period-2/3 cycle), plateau (--score stale N rounds) and refuses
    impossible_under_contract from anyone not in routing.impossible_reporters; escalation sets
    pending.failure_report which check-clean / the Stop-hook template refuse to end a session on
  - a waiver is a first-class record: `waive` writes one without a transition and prints its event id, and
    `review.done` is a closed enum whose "waived" (or any exit_reason) must cite that id as review.waiver_ref
  - `graph check` asserts ORDER == assets/graph.yaml stages (data and code watch each other)
Semantic half (a judge / a human, never this script): whether the candidate layer is the RIGHT layer.
"""
import argparse
import datetime as _dt
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT_DEFAULT = ".sdlc"
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
ORDER = ["intake", "track", "issue", "branch", "contract", "g2", "cards", "implement",
         "acceptance", "pr", "review", "g3", "merge", "release", "archive"]
SETTABLE = {
    "track", "title",
    "issue.number", "issue.url", "issue.kind",
    "branch.name", "branch.base",
    "contract.done_when", "contract.contract_yaml", "contract.source",
    "lock.path", "lock.signed_by", "lock.signed_at", "lock.stage",
    "cards.dir", "cards.lint_passed",
    "acceptance.evaluation_result", "acceptance.meets_done_when", "acceptance.skipped_reason",
    "pr.number", "pr.url", "pr.size_class", "pr.pre_review_rounds",
    "review.done", "review.exit_reason", "review.rounds", "review.waiver_ref",
    "merge.sha", "merge.merged_at",
    "gates.g3.required",
    "world.psl", "world.derived_dir", "world.dos", "world.invariants", "world.form_draft_sha256",
    "contract.compile_manifest", "contract.calibration_report", "contract.tests_manifest",
    "release.version", "release.tag", "release.notes", "release.done", "release.skipped_reason",
}
LOCK_STAGES = ("g2", "l5")
# how the review ring exited, as a closed enum instead of a boolean with the qualification in free text
# (dogfood 2026-09-06, I-83). Legacy `true` reads as "done"; "waived" and any exit_reason need a waiver_ref.
REVIEW_EXITS = ("done", "waived")
# the contract set an archive must carry so the run stays readable (and measurable) after the branch is gone
CONTRACT_FILES = ("contract.done_when", "contract.compile_manifest", "contract.tests_manifest",
                  "contract.calibration_report")
LAYER_COUNTERS = ["card", "plan", "task", "ontology", "world"]
BUDGET_KEY = {"card": "card_retries", "plan": "plan_reflows", "task": "task_reflows",
              "ontology": "ontology_reflows", "world": "world_reflows"}
# Append-only logs can only point backwards, so the causal edge is `caused_by` (effect → cause); the rest are
# timeless (artifact anchors) or backwards (decided_by, supersedes). Same seven relations as the graph-engineering
# canon, with `caused` read from the effect's side.
TRACE_EDGE_TYPES = {"caused_by", "decided_by", "supersedes", "implements", "references", "depends_on", "rejected_alternative"}


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


def load_yaml(path):
    try:
        import yaml
    except ImportError:
        die("PyYAML required (pip install pyyaml)")
    if not os.path.isfile(path):
        die(f"not found: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


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


def trace_path(root, slug):
    return os.path.join(root, slug, "trace.jsonl")


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


# ---- ledger (human, append-only) + trace (machine, typed edges) ----------------------------
def next_event_id(root, slug, offset=0):
    tp = trace_path(root, slug)
    n = 0
    if os.path.isfile(tp):
        with open(tp, encoding="utf-8") as f:
            n = sum(1 for line in f if line.strip())
    return f"ev-{n + 1 + offset:04d}"


def trace_append(root, slug, event):
    """Evidence, not control state: a corrupt trace never affects budgets or transitions."""
    tp = trace_path(root, slug)
    os.makedirs(os.path.dirname(tp), exist_ok=True)
    for r in event.get("refs") or []:
        if r.get("type") not in TRACE_EDGE_TYPES:
            die(f"trace edge type {r.get('type')!r} ∉ {sorted(TRACE_EDGE_TYPES)}", 1)
    with open(tp, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event["id"]


def ledger_append(root, slug, kind, note="", stage=None, signal="", layer="", fingerprint="",
                  decision="", by="engine", refs=None, extra=None, event_id=None):
    d, _, lp = paths(root, slug)
    os.makedirs(d, exist_ok=True)
    if not os.path.isfile(lp):
        header = ("# Ledger — %s\n\n> 只增不删。产物可回滚；判据、失败记录、被拒的修复、路由决定不回滚。\n"
                  "> 机器可读的伴生：trace.jsonl（类型边，见 scripts/trace.py）。\n\n"
                  "| at | stage | kind | signal / gate | layer | fingerprint | evidence | decision | by |\n"
                  "|---|---|---|---|---|---|---|---|---|\n") % slug
        atomic_write(lp, header)
    cell = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
    ts = now()
    row = "| %s | %s | %s | %s | %s | %s | %s | %s | %s |\n" % tuple(
        cell(x) for x in (ts, stage or "", kind, signal, layer, fingerprint, note, decision, by))
    with open(lp, "a", encoding="utf-8") as f:
        f.write(row)
    ev = {"id": event_id or next_event_id(root, slug), "at": ts, "stage": stage or "", "kind": kind}
    for k, v in (("signal", signal), ("layer", layer), ("fingerprint", fingerprint), ("note", note),
                 ("decision", decision), ("by", by)):
        if v:
            ev[k] = v
    if extra:
        ev.update(extra)
    ev["refs"] = refs or []
    return trace_append(root, slug, ev)


def trace_event_ids(root, slug):
    """Every event id already written to trace.jsonl — the resolvable target set for a waiver_ref."""
    tp = trace_path(root, slug)
    ids = set()
    if os.path.isfile(tp):
        with open(tp, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ids.add(json.loads(line).get("id"))
                except Exception:
                    continue
    return ids


def gitignore_gap(root):
    """`.sdlc/` is runtime state, not a deliverable: the archive is what gets committed (`archive --to
    specs/<slug>/`). Committing the live state turns the ledger into a merge conflict and lets a stale
    counter travel between branches. Nothing used to tell the operator (dogfood 2026-09-06, I-01)."""
    try:
        r = subprocess.run(["git", "check-ignore", "-q", root], capture_output=True, text=True)
    except (OSError, ValueError):
        return None
    if r.returncode != 1:   # 0 = already ignored · 128 = not a repository, nothing to advise
        return None
    return (f"{root}/ is not ignored by git: it is runtime state, not a deliverable — add a `{root}/` line to "
            f".gitignore and commit the archive instead (`archive --to specs/<slug>/`)")


def resolve_commit(sha):
    """Short sha → the full one, so the same commit cannot be registered twice under two spellings
    (dogfood 2026-09-06, I-66). Outside a repo (or for a sha git does not know) the raw value stands."""
    if not sha:
        return sha
    try:
        r = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (OSError, ValueError):
        pass
    return sha


def parse_refs(items):
    out = []
    for it in items or []:
        if ":" not in it:
            die(f"--ref expects type:target, got {it!r}")
        t, tgt = it.split(":", 1)
        if t not in TRACE_EDGE_TYPES:
            die(f"--ref type {t!r} ∉ {sorted(TRACE_EDGE_TYPES)}", 1)
        out.append({"type": t, "target": tgt})
    return out


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


def review_exit(st):
    """How the review ring exited: "done" | "waived" | None (still open). Legacy `true` == "done"."""
    v = get_path(st, "review.done")
    if v is True:
        return "done"
    return v if v in REVIEW_EXITS else None


def check_review(st, root, slug):
    """The exit kind is the state, not a sentence beside it (I-83).

    `review.done` is a closed enum (legacy boolean true still reads as "done"). A "waived" exit — or any
    `exit_reason` prose qualifying a "done" one — must cite `review.waiver_ref`, a ledger event id that
    resolves in trace.jsonl. That is the difference between "this was waived" being machine-readable and
    it hiding in a free-text field no script reads.
    """
    v = get_path(st, "review.done")
    if v is not None and v is not True and v is not False and v not in REVIEW_EXITS:
        die(f"review.done must be true|false|{'|'.join(REVIEW_EXITS)} (closed enum), got {v!r}", 1)
    kind = review_exit(st)
    if kind is None:
        return
    reason, ref = get_path(st, "review.exit_reason"), get_path(st, "review.waiver_ref")
    if (kind == "waived" or reason) and not ref:
        why = "a waived exit" if kind == "waived" else "an exit_reason qualifying a done exit"
        die(f"{why} requires review.waiver_ref=<ledger event id>: record the waiver first "
            "(`waive --signal review --reason … --by …` prints the id). A qualification no script reads is "
            "not an exit condition (I-83)", 1)
    if ref and ref not in trace_event_ids(root, slug):
        die(f"review.waiver_ref {ref!r} does not resolve to an event in trace.jsonl "
            "(`waive` / `ledger` print the id they wrote)", 1)


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
        if dw and os.path.isfile(dw):
            v2 = os.path.join(HERE, "..", "..", "donewhen-extract", "scripts", "validate_done_when_v2.py")
            if os.path.isfile(v2):
                r = subprocess.run([sys.executable, v2, dw], capture_output=True, text=True)
                need(r.returncode == 0, "contract.done_when validates as schema v2 (validate_done_when_v2.py; v1 → run convert_v1_to_v2.py and complete the ACs) — C1 compiled")
            else:
                need(False, "validate_done_when_v2.py not found next to donewhen-extract — cannot certify the contract shape")
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
        need(not get_path(st, "pending.failure_report"), "pending failure report written (`report --path …`)")
    elif target == "pr":
        ok = get_path(st, "acceptance.evaluation_result") or get_path(st, "acceptance.skipped_reason")
        need(ok, "acceptance.evaluation_result path OR acceptance.skipped_reason (TASK 轨轻量, recorded)")
    elif target == "review":
        need(get_path(st, "pr.number"), "pr.number set")
    elif target == "g3":
        need(review_exit(st), "review.done recorded (true | done | waived; a waived exit needs review.waiver_ref)")
    elif target == "merge":
        if get_path(st, "gates.g3.required", True):
            need(get_path(st, "gates.g3.verdict") in ("pass", "waived"), "G3 verdict pass — run `gate g3`")
        else:
            need(review_exit(st), "review.done recorded (true | done | waived; a waived exit needs review.waiver_ref)")
    elif target == "release":
        need(get_path(st, "merge.sha"), "merge.sha set")
    elif target == "archive":
        need(get_path(st, "merge.sha"), "merge.sha set")
        need(get_path(st, "release.done") is True or get_path(st, "release.skipped_reason"),
             "release.done true (verify_release.py + post-deploy verification) OR release.skipped_reason recorded")
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
        "counters": {k: 0 for k in LAYER_COUNTERS} | {"last_fingerprints": {}, "fingerprint_repeats": {},
                                                       "fingerprint_history": {}, "scores": {}},
        "pending": {"failure_report": False},
        "waivers": [], "assumptions": [], "artifacts": {},
    }
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "init", f"title={a.title} track={st['track']}", stage="intake")
    out = {"ok": True, "state": sp}
    gap = gitignore_gap(a.root)
    if gap:
        out["warning"] = gap
    print(json.dumps(out, ensure_ascii=False))


def cmd_show(a):
    st = load(a.root, a.slug)
    print(json.dumps(st, ensure_ascii=False, indent=2))


def cmd_set(a):
    st = load(a.root, a.slug)
    changed, refs = [], []
    for kv in a.pairs:
        if "=" not in kv:
            die(f"expected key=value, got {kv!r}")
        k, v = kv.split("=", 1)
        if k not in SETTABLE:
            die(f"key not settable: {k} (allowed: {sorted(SETTABLE)})", 1)
        if k == "track" and v not in ("psl", "task"):
            die("track must be psl|task", 1)
        if k == "lock.stage" and v not in LOCK_STAGES:
            die(f"lock.stage must be {'|'.join(LOCK_STAGES)} (the two signing stages)", 1)
        set_path(st, k, coerce(v))
        if k == "track":
            st["gates"]["g1"]["required"] = (v == "psl")
        if k in ("contract.done_when", "lock.path", "acceptance.evaluation_result", "world.derived_dir", "world.dos"):
            refs.append({"type": "references", "target": v})
        changed.append(k)
    if any(k.startswith("review.") for k in changed):
        check_review(st, a.root, a.slug)   # validated before the merge: a rejected proposal never lands
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "set", ", ".join(a.pairs), stage=st["stage"], refs=refs)
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
    refs = []
    if problems:
        if not a.reason:
            die("--force requires --reason (the waiver is recorded, not silent)", 1)
        st.setdefault("waivers", []).append({"stage": a.stage, "reason": a.reason, "at": now(),
                                             "unmet": problems})
        wid = ledger_append(a.root, a.slug, "waiver", f"forced → {a.stage}: {a.reason} | unmet: {problems}",
                            stage=st["stage"], decision="forced", by="human",
                            refs=[{"type": "decided_by", "target": "human:waiver"}])
        refs.append({"type": "decided_by", "target": wid})
    prev = st["stage"]
    st["stage"] = a.stage
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "advance", f"{prev} → {a.stage}", stage=a.stage, refs=refs)
    print(json.dumps({"ok": True, "from": prev, "to": a.stage, "waived": bool(problems)}, ensure_ascii=False))


def cmd_gate(a):
    st = load(a.root, a.slug)
    g = st["gates"].setdefault(a.gate, {"required": True, "verdict": "pending"})
    if a.gate == "g2" and a.verdict == "pass" and not (get_path(st, "lock.path") and os.path.isfile(get_path(st, "lock.path"))):
        die("G2 pass requires lock.path (run lock_done_when.py sign, then `set lock.path=...`)", 1)
    if a.gate == "g1" and a.verdict == "reject" and a.attribution in (None, "none"):
        die("G1 reject requires --attribution derivation_error|rule_error (feeds world-layer routing)", 1)
    if a.gate == "g1" and a.verdict == "pass":
        dd = get_path(st, "world.derived_dir")
        if not (dd and os.path.isdir(dd)):
            die("G1 pass requires world.derived_dir pointing at an existing derived/ directory (psl-derive output: "
                "dos-proposal.yaml / workflow.md / form-draft.md / divergence.md) — G1 adjudicates derivation products, not vibes", 1)
    # a gate is human-only; a delegated signature is legal only with an authorization on record (dogfood 2026-09-05, I-17)
    if a.signer_kind == "delegated_agent" and not a.authorization:
        die("--signer-kind delegated_agent requires --authorization <who/when/what allowed the delegation>", 1)
    g.update({"verdict": a.verdict, "by": a.by, "at": now(), "signer_kind": a.signer_kind})
    if a.authorization:
        g["authorization"] = a.authorization
    if a.record:
        g["record"] = a.record
    if a.attribution:
        g["attribution"] = a.attribution
    elif a.verdict == "pass":
        g.pop("attribution", None)   # a stale reject attribution must not sit beside a pass (dogfood 2026-09-05, I-51)
    # A rejection often has more than one layer of cause — this run had one that was honestly both a
    # rule error and a derivation error. Recording only the primary loses the second; counting both
    # would make the world-layer number stop meaning "how many times the world changed". So secondary
    # causes are recorded here and never reach the counter below (dogfood I-22).
    sec = [x for x in (a.secondary_attribution or []) if x != a.attribution]
    if len(sec) != len(a.secondary_attribution or []):
        die("--secondary-attribution repeats the primary — a duplicate is not a second layer", 1)
    if sec:
        if not a.attribution or a.attribution == "none":
            die("--secondary-attribution needs a primary --attribution: the primary is what routes and counts", 1)
        g["secondary_attribution"] = sec
    elif a.verdict == "pass":
        g.pop("secondary_attribution", None)
    # only a rule_error is a world-layer error (the PSL itself was wrong); a derivation_error re-derives with the
    # same PSL and must not inflate the world counter (dogfood 2026-09-05, I-34)
    if a.gate == "g1" and a.verdict == "reject" and a.attribution == "rule_error":
        st["counters"]["world"] += 1
    save(a.root, a.slug, st)
    signer_ref = f"human:{a.by}" if a.signer_kind == "human" else f"agent:{a.by}"
    refs = [{"type": "decided_by", "target": signer_ref}]
    if a.record:
        refs.append({"type": "references", "target": a.record})
    if a.gate == "g2" and a.verdict == "pass" and get_path(st, "lock.path"):
        refs.append({"type": "references", "target": get_path(st, "lock.path")})
    ledger_append(a.root, a.slug, "gate", a.record or "", stage=st["stage"], signal=a.gate,
                  layer=("world" if a.gate == "g1" else ""), decision=f"{a.verdict}"
                  + (f" ({a.attribution})" if a.attribution else "") + (" [delegated]" if a.signer_kind != "human" else ""),
                  by=a.by, refs=refs, extra={"signer_kind": a.signer_kind, **({"authorization": a.authorization} if a.authorization else {})})
    print(json.dumps({"ok": True, "gate": a.gate, "verdict": a.verdict}, ensure_ascii=False))


def cmd_card(a):
    st = load(a.root, a.slug)
    items = st.setdefault("cards", {}).setdefault("items", {})
    c = items.setdefault(a.card, {"status": "todo", "retries": 0, "commits": []})
    c["status"] = a.status
    sha = resolve_commit(a.commit)
    if sha:
        commits = c.setdefault("commits", [])
        if sha not in commits:   # one commit, one row — a short sha is the same commit as its full one (I-66)
            commits.append(sha)
    save(a.root, a.slug, st)
    refs = [{"type": "references", "target": a.card}]
    extra = {"card": a.card}
    if sha:
        refs = [{"type": "implements", "target": a.card}] + [{"type": "implements", "target": ac} for ac in (a.ac or [])]
        extra["sha"] = sha
    ledger_append(a.root, a.slug, "card", f"{a.card} → {a.status}" + (f" commit {sha}" if sha else ""),
                  stage=st["stage"], refs=refs, extra=extra)
    out = {"ok": True, "card": a.card, "status": a.status}
    if sha:
        out["commit"] = sha
    print(json.dumps(out, ensure_ascii=False))


def load_routing(path):
    return load_yaml(path)


def trailing_run(hist):
    if not hist:
        return 0
    n, last = 0, hist[-1]
    for x in reversed(hist):
        if x != last:
            break
        n += 1
    return n


def detect_oscillation(hist, periods):
    """Period-p cycle at the tail whose elements are not all identical (that would be a plain repeat)."""
    for p in periods or []:
        p = int(p)
        if p >= 2 and len(hist) >= 2 * p and hist[-p:] == hist[-2 * p:-p] and len(set(hist[-p:])) > 1:
            return p
    return None


def cmd_fail(a):
    st = load(a.root, a.slug)
    routing_path = a.routing or os.path.join(ASSETS, "routing.yaml")
    rt = load_routing(routing_path)
    rules = {r.get("signal"): r for r in rt.get("rules", [])}
    rule = rules.get(a.signal)
    if not rule:
        die(f"unknown signal {a.signal}; known: {sorted(rules)}", 1)
    if a.signal == "impossible_under_contract":
        reporters = rt.get("impossible_reporters") or []
        if not a.by or not (a.by in reporters or a.by.startswith("human")):
            die("impossible_under_contract may only be reported by an evaluator or a human "
                f"(--by ∈ {reporters}); an implementer saying 'impossible' is self-assessment, not evidence", 1)

    fp = a.fingerprint or hashlib.sha1((a.evidence or a.signal).encode("utf-8")).hexdigest()[:12]
    orig_layer = rule["layer"]
    key = f"{a.card or orig_layer}:{orig_layer}"
    cnt = st["counters"]
    hist = cnt.setdefault("fingerprint_history", {}).setdefault(key, [])
    hist.append(fp)
    del hist[:-int(rt.get("fingerprint_history", 6))]
    repeat = trailing_run(hist)
    cnt.setdefault("fingerprint_repeats", {})[key] = repeat
    cnt.setdefault("last_fingerprints", {})[key] = fp
    osc_period = detect_oscillation(hist, rt.get("oscillation_periods", [2, 3]))

    plateau, score_info = False, None
    if a.score is not None:
        sc = cnt.setdefault("scores", {}).setdefault(key, {"history": [], "best": None, "stale": 0})
        if sc["best"] is None or a.score > sc["best"]:
            sc["best"], sc["stale"] = a.score, 0
        else:
            sc["stale"] += 1
        sc["history"].append(a.score)
        del sc["history"][:-int(rt.get("fingerprint_history", 6))]
        plateau = sc["stale"] >= int(rt.get("plateau_rounds", 3))
        score_info = dict(sc)

    # derived convergence signal re-resolves the rule (R14 / R15)
    derived = None
    if osc_period and a.signal != "oscillation_detected" and "oscillation_detected" in rules:
        derived = "oscillation_detected"
    elif plateau and a.signal != "plateau" and "plateau" in rules:
        derived = "plateau"
    if derived:
        rule = rules[derived]
    layer = rule["layer"]

    if layer in LAYER_COUNTERS:
        cnt[layer] = cnt.get(layer, 0) + 1
    if a.card:
        c = st.setdefault("cards", {}).setdefault("items", {}).setdefault(a.card, {"status": "doing", "retries": 0, "commits": []})
        if orig_layer == "card":
            c["retries"] = c.get("retries", 0) + 1
        c["last_fingerprint"] = fp

    track = st.get("track") if st.get("track") in ("psl", "task") else "task"
    budgets = rt.get("budgets", {}).get(track, {})
    budget = budgets.get(BUDGET_KEY.get(layer, ""), None)
    used = cnt.get(layer, 0) if layer in LAYER_COUNTERS else None
    limit = int(rt.get("fingerprint_repeat_limit", 2))
    escalate, why = False, []
    if repeat >= limit:
        escalate, why = True, why + [f"same fingerprint {fp} repeated {repeat}× (limit {limit}) — no progress"]
    if osc_period:
        escalate, why = True, why + [f"oscillation: period-{osc_period} cycle in fingerprint history {hist[-2 * osc_period:]} — alternating between solutions, a plan-layer trade-off"]
    if plateau:
        escalate, why = True, why + [f"plateau: score stale {score_info['stale']}× (limit {rt.get('plateau_rounds', 3)}), best={score_info['best']} — stabilising is not the same as being right"]
    if budget is not None and used is not None and used >= budget:
        escalate, why = True, why + [f"{layer} budget exhausted ({used}/{budget}, track={track})"]
    if rule.get("handler") == "human":
        escalate, why = True, why + ["rule handler is human"]
    outer = None
    if layer in LAYER_COUNTERS:
        i = LAYER_COUNTERS.index(layer)
        outer = LAYER_COUNTERS[i + 1] if i + 1 < len(LAYER_COUNTERS) else "human"
    if not escalate:
        escalate_to = None
    elif rule.get("handler") == "human":
        escalate_to = "human"
    elif derived:
        escalate_to = layer
    else:
        escalate_to = outer
    if escalate:
        st.setdefault("pending", {})["failure_report"] = True

    convergence = {"type": ("impossible" if a.signal == "impossible_under_contract" else
                            "oscillation" if osc_period else "plateau" if plateau else
                            "repeat" if repeat >= limit else "budget" if (budget is not None and used is not None and used >= budget) else
                            "handler=human" if rule.get("handler") == "human" else "none"),
                   "fingerprint_history": list(hist), "repeat": repeat, "oscillation_period": osc_period,
                   "score": score_info}
    decision = {
        "rule": rule["id"], "signal": a.signal, "derived_signal": derived, "layer": layer, "handler": rule.get("handler"),
        "action": rule.get("action"), "fingerprint": fp, "fingerprint_repeat": repeat,
        "layer_count": used, "budget": budget, "track": track,
        "escalate": escalate, "escalate_to": escalate_to,
        "why": why, "note": rule.get("note", ""), "convergence": convergence,
        "next": ("write failure report (assets/failure_report.md, paste `convergence`) then `report --path …`; stop for human confirmation" if escalate
                 else f"engine may {rule.get('action')} once more"),
    }
    save(a.root, a.slug, st)
    refs = [{"type": "decided_by", "target": f"routing.{rule['id']}"}]
    if a.card:
        refs.append({"type": "references", "target": a.card})
    if a.by:
        refs.append({"type": "decided_by", "target": f"human:{a.by}" if a.by.startswith("human") else a.by})
    fail_id = ledger_append(a.root, a.slug, "fail", a.evidence or "", stage=st["stage"], signal=a.signal, layer=layer,
                            fingerprint=fp, decision=("ESCALATE→" + str(escalate_to)) if escalate else rule.get("action"),
                            by=a.by or "engine", refs=refs,
                            extra={"convergence": convergence, "card": a.card} if a.card else {"convergence": convergence})
    if escalate:
        # the reflow is the effect; it points back at the failure that caused it (caused_by)
        ledger_append(a.root, a.slug, "reflow", "; ".join(why), stage=st["stage"], signal=derived or a.signal,
                      layer=str(escalate_to), fingerprint=fp, decision=rule.get("action"),
                      refs=[{"type": "caused_by", "target": fail_id}, {"type": "decided_by", "target": f"routing.{rule['id']}"}])
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    sys.exit(0)


def cmd_report(a):
    st = load(a.root, a.slug)
    if not os.path.isfile(a.path):
        die(f"failure report not found: {a.path}", 1)
    st.setdefault("pending", {})["failure_report"] = False
    save(a.root, a.slug, st)
    refs = [{"type": "references", "target": a.path}]
    # the report is caused by the most recent reflow: `trace.py why` walks report → reflow → fail
    tp = trace_path(a.root, a.slug)
    last = None
    if os.path.isfile(tp):
        with open(tp, encoding="utf-8") as f:
            for line in f:
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if ev.get("kind") == "reflow":
                    last = ev.get("id")
    if last:
        refs.append({"type": "caused_by", "target": last})
    ledger_append(a.root, a.slug, "failure_report", a.path, stage=st["stage"], by=a.by or "engine", refs=refs)
    print(json.dumps({"ok": True, "pending_cleared": True, "report": a.path}, ensure_ascii=False))


def cmd_check_clean(a):
    st = load(a.root, a.slug)
    problems = []
    if get_path(st, "pending.failure_report"):
        problems.append("failure report pending after an escalation — write it from assets/failure_report.md and run `report --path <file>`")
    doing = sorted(k for k, v in (get_path(st, "cards.items", {}) or {}).items() if v.get("status") == "doing")
    if doing:
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            root = a.root.rstrip("/").lstrip("./")
            # the state dir itself (.sdlc/) is bookkeeping, not work left uncommitted
            dirty = [l for l in r.stdout.splitlines() if l.strip() and not l[3:].lstrip("./").startswith(root + "/") and l[3:].lstrip("./") != root + "/"]
            if dirty:
                problems.append(f"cards {doing} are `doing` and the working tree has {len(dirty)} uncommitted path(s) — commit through /commit (or stash) and register the card state")
    if a.as_hook:
        if problems:
            print(json.dumps({"decision": "block", "reason": "sdlc check-clean: " + " | ".join(problems)}, ensure_ascii=False))
        else:
            print(json.dumps({"ok": True, "clean": True}, ensure_ascii=False))
        sys.exit(0)
    print(json.dumps({"clean": not problems, "problems": problems}, ensure_ascii=False, indent=2))
    sys.exit(1 if problems else 0)


# ---- graph as data -------------------------------------------------------------------------
def as_list(x):
    return [] if x is None else (list(x) if isinstance(x, (list, tuple)) else [x])


def cmd_graph(a):
    g = load_yaml(a.graph or os.path.join(ASSETS, "graph.yaml"))
    nodes = {n["id"]: n for n in g.get("nodes") or []}
    edges = g.get("edges") or []
    if a.action == "check":
        stages = list(g.get("stages") or [])
        seq = {f: t for e in edges if e.get("type") == "sequential" for f in as_list(e.get("from")) for t in as_list(e.get("to"))
               if str(f).startswith("stage.") and str(t).startswith("stage.")}
        chain, cur = [], f"stage.{ORDER[0]}"
        while cur:
            chain.append(cur.split(".", 1)[1]); cur = seq.get(cur)
        problems = []
        if stages != ORDER:
            problems.append(f"graph.yaml stages {stages} ≠ sdlc_state.py ORDER {ORDER}")
        if chain != ORDER:
            problems.append(f"sequential stage chain {chain} ≠ ORDER {ORDER}")
        for s in ORDER:
            if f"stage.{s}" not in nodes:
                problems.append(f"stage.{s} node missing")
        print(json.dumps({"ok": not problems, "problems": problems, "stages": len(stages), "edges": len(edges)}, ensure_ascii=False, indent=2))
        sys.exit(1 if problems else 0)
    if a.action == "next":
        st = load(a.root, a.slug)
        cur = f"stage.{st['stage']}"
        out = []
        for e in edges:
            if cur in as_list(e.get("from")):
                for t in as_list(e.get("to")):
                    item = {"to": t, "type": e.get("type")}
                    for k in ("guard", "when", "signal", "loop", "carries"):
                        if e.get(k) is not None:
                            item[k] = e[k]
                    if e.get("type") in ("sequential", "conditional") and str(t).startswith("stage."):
                        item["unmet"] = prereqs(st, t.split(".", 1)[1])
                    out.append(item)
        print(json.dumps({"stage": st["stage"], "handled_by": nodes.get(cur, {}).get("handled_by"), "edges": out}, ensure_ascii=False, indent=2))
        return
    # render
    def nid(x):
        return str(x).replace(".", "_").replace("-", "_")
    keep = set(nodes) if a.full else {n for n in nodes if n.startswith("stage.") or nodes[n].get("kind") == "human"}
    if not a.full:
        for e in edges:
            if e.get("type") in ("loop_back", "fan_out", "fan_in"):
                keep.update(as_list(e.get("from"))); keep.update(as_list(e.get("to")))
    lines = ["flowchart TD"]
    for n in sorted(keep):
        node = nodes.get(n, {})
        label = n.split(".", 1)[1] if n.startswith("stage.") else n
        if node.get("kind") == "human":
            lines.append(f"  {nid(n)}{{{{{label}}}}}")
        elif node.get("kind") == "stage":
            lines.append(f"  {nid(n)}[{label}]")
        else:
            lines.append(f"  {nid(n)}([{label}])")
    style = {"sequential": "-->", "conditional": "-.->", "fan_out": "==>", "fan_in": "==>", "loop_back": "-.->", "interrupt": "-->", "handoff": "-->"}
    for e in edges:
        for f in as_list(e.get("from")):
            for t in as_list(e.get("to")):
                if f in keep and t in keep:
                    lab = e.get("signal") or e.get("when") or e.get("guard") or e.get("type")
                    if e.get("loop"):
                        lab = f"{lab} [{e['loop']}]"
                    lines.append(f"  {nid(f)} {style.get(e.get('type'), '-->')}|{lab}| {nid(t)}")
    print("\n".join(lines))


# ---- loops: budget consumption in one screen ----------------------------------------------
def cmd_loops(a):
    loops = load_yaml(a.loops or os.path.join(ASSETS, "loops.yaml")).get("loops") or []
    rt = load_yaml(a.routing or os.path.join(ASSETS, "routing.yaml"))
    st = None
    if a.slug or (os.path.isdir(a.root) and any(os.path.isfile(os.path.join(a.root, d, "state.json")) for d in os.listdir(a.root))):
        try:
            st = load(a.root, resolve_slug(a.root, a.slug))
        except SystemExit:
            st = None   # ambiguous slug etc.: report contracts without live consumption
    track = (st or {}).get("track") if (st or {}).get("track") in ("psl", "task") else "task"
    budgets = rt.get("budgets", {}).get(track, {})
    cnt = (st or {}).get("counters", {})
    rows = []
    for l in loops:
        lid = l["id"]
        used, budget, note = None, None, ""
        if lid == "card_retry":
            used, budget = cnt.get("card"), budgets.get("card_retries")
            items = get_path(st or {}, "cards.items", {}) or {}
            note = "per card: " + ", ".join(f"{k}={v.get('retries', 0)}" for k, v in items.items()) if items else "no cards"
        elif lid == "ratchet":
            if a.ratchet_dir:
                tsv = glob.glob(os.path.join(a.ratchet_dir, "**", "results.tsv"), recursive=True)
                rounds = 0
                for t in tsv:
                    with open(t, encoding="utf-8") as f:
                        rounds += max(0, sum(1 for _ in f) - 1)
                used, note = rounds, f"{len(tsv)} results.tsv"
            budget = budgets.get("card_retries")
        elif lid == "acceptance_ratchet":
            used, budget = cnt.get("task"), budgets.get("task_reflows")
            note = f"plan={cnt.get('plan')}/{budgets.get('plan_reflows')}"
        elif lid == "review_loop":
            budget = (l.get("stop", {}).get("budget") or {}).get("rounds", 10)
            if a.pr_watch and os.path.isdir(a.pr_watch):
                tot, strikes, n = 0, 0, 0
                for cj in glob.glob(os.path.join(a.pr_watch, "pr-*.counters.json")):
                    try:
                        d = json.load(open(cj, encoding="utf-8"))
                    except Exception:
                        continue
                    n += 1; tot += int(d.get("rounds", 0)); strikes += sum(int(v) for v in (d.get("strikes") or {}).values())
                used, note = tot, f"{n} PR(s), strikes={strikes}"
            elif st is not None:
                used = get_path(st, "review.rounds")
        elif lid == "lifecycle":
            used = sum(int(cnt.get(k, 0) or 0) for k in LAYER_COUNTERS)
            budget = sum(int(v) for v in budgets.values() if isinstance(v, int))
            note = f"stage={(st or {}).get('stage')} pending_report={get_path(st or {}, 'pending.failure_report')}"
        elif lid == "hill_climb":
            props = glob.glob("tune/harness-proposals-*.yaml")
            used, note = len(props), "proposal files under tune/"
        pct = (round(100.0 * used / budget) if isinstance(used, (int, float)) and isinstance(budget, (int, float)) and budget else None)
        rows.append({"loop": lid, "level": l.get("level"), "timescale": l.get("timescale"), "generator": l.get("generator"),
                     "verifier": l.get("verifier"), "used": used, "budget": budget, "pct": pct, "trigger": l.get("trigger"), "note": note})
    if a.json:
        print(json.dumps({"track": track, "loops": rows}, ensure_ascii=False, indent=2)); return
    print(f"loops (track={track})")
    print("| loop | level | scale | generator → verifier | used/budget | % | trigger | note |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['loop']} | {r['level']} | {r['timescale']} | {r['generator']} → {r['verifier']} | {r['used']}/{r['budget']} | {r['pct'] if r['pct'] is not None else '-'} | {r['trigger']} | {r['note']} |")


def cmd_waive(a):
    """A waiver without a transition to hang it on (dogfood 2026-09-06, I-67).

    `advance --force` couples the waiver to a stage skip, so the commonest case — a budget is spent, a
    signal is accepted as a ratchet item, the stage does not move — had no way to be recorded. dos.yaml and
    the G1 rules both cite "a waiver record in state.json"; this is the command that writes one, and it
    prints the event id so `review.waiver_ref` / audit.yaml `verdict: waived` can point at it.
    """
    st = load(a.root, a.slug)
    if a.signer_kind == "delegated_agent" and not a.authorization:
        die("--signer-kind delegated_agent requires --authorization <who/when/what allowed the delegation>", 1)
    stage = a.stage or st["stage"]
    rec = {"stage": stage, "signal": a.signal, "reason": a.reason, "at": now(),
           "signer": a.by, "signer_kind": a.signer_kind}
    for k, v in (("layer", a.layer), ("card", a.card), ("fingerprint", a.fingerprint),
                 ("authorization", a.authorization), ("scope", a.scope)):
        if v:
            rec[k] = v
    st.setdefault("waivers", []).append(rec)
    save(a.root, a.slug, st)
    signer_ref = f"human:{a.by}" if a.signer_kind == "human" else f"agent:{a.by}"
    refs = [{"type": "decided_by", "target": signer_ref}] + parse_refs(a.ref)
    if a.card:
        refs.append({"type": "references", "target": a.card})
    extra = {"signer_kind": a.signer_kind}
    for k, v in (("card", a.card), ("authorization", a.authorization), ("scope", a.scope)):
        if v:
            extra[k] = v
    wid = ledger_append(a.root, a.slug, "waiver", a.reason, stage=stage, signal=a.signal, layer=a.layer or "",
                        fingerprint=a.fingerprint or "", decision="waived", by=a.by, refs=refs, extra=extra)
    print(json.dumps({"ok": True, "event": wid, "signal": a.signal, "stage": stage,
                      "waivers": len(st["waivers"])}, ensure_ascii=False))


def cmd_ledger(a):
    st = load(a.root, a.slug)
    extra = {"card": a.card} if a.card else None
    eid = ledger_append(a.root, a.slug, a.kind, a.note, stage=st["stage"], signal=a.signal or "", layer=a.layer or "",
                        fingerprint=a.fingerprint or "", decision=a.decision or "", by=a.by or "engine",
                        refs=parse_refs(a.ref), extra=extra)
    print(json.dumps({"ok": True, "event": eid}, ensure_ascii=False))


def cmd_archive(a):
    st = load(a.root, a.slug)
    d, sp, lp = paths(a.root, a.slug)
    os.makedirs(a.to, exist_ok=True)
    copied = []
    srcs = [sp, lp] + ([trace_path(a.root, a.slug)] if os.path.isfile(trace_path(a.root, a.slug)) else [])
    # the contract is not an "artifact" entry, yet retro/metrics.py reads done_when.yaml FROM the archive to
    # compute the human-AC ratio — leaving it behind made that metric empty for every run (I-85)
    srcs += [p for p in (get_path(st, k) for k in CONTRACT_FILES) if p and os.path.isfile(p)]
    srcs += [p for p in (st.get("artifacts") or {}).values() if p and os.path.isfile(p)]
    seen, uniq = set(), []
    for s in srcs:
        r = os.path.abspath(s)
        if r not in seen:
            seen.add(r); uniq.append(s)
    for src in uniq:
        dst = os.path.join(a.to, os.path.basename(src))
        shutil.copy2(src, dst)
        copied.append(dst)
    manifest = {"slug": a.slug, "archived_at": now(), "stage": st["stage"], "files": copied,
                "counters": st.get("counters"), "gates": st.get("gates")}
    atomic_write(os.path.join(a.to, "archive-manifest.json"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    ledger_append(a.root, a.slug, "archive", f"→ {a.to} ({len(copied)} files)", stage=st["stage"],
                  refs=[{"type": "references", "target": a.to}])
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
    s.add_argument("--secondary-attribution", action="append", choices=["derivation_error", "rule_error"], default=[],
                   help="a further cause that also holds; recorded, never counted (dogfood I-22)")
    s.add_argument("--signer-kind", choices=["human", "delegated_agent"], default="human"); s.add_argument("--authorization")
    s = P("card"); s.add_argument("card"); s.add_argument("--status", required=True, choices=["todo", "doing", "done", "blocked"]); s.add_argument("--commit"); s.add_argument("--ac", action="append")
    s = P("fail"); s.add_argument("--signal", required=True); s.add_argument("--card"); s.add_argument("--fingerprint"); s.add_argument("--evidence")
    s.add_argument("--score", type=float); s.add_argument("--by"); s.add_argument("--routing")
    s = P("waive"); s.add_argument("--signal", required=True); s.add_argument("--reason", required=True); s.add_argument("--by", required=True)
    s.add_argument("--signer-kind", choices=["human", "delegated_agent"], default="human"); s.add_argument("--authorization")
    s.add_argument("--fingerprint"); s.add_argument("--card"); s.add_argument("--layer"); s.add_argument("--stage"); s.add_argument("--scope")
    s.add_argument("--ref", action="append")
    s = P("report"); s.add_argument("--path", required=True); s.add_argument("--by")
    s = P("check-clean"); s.add_argument("--as-hook", action="store_true")
    s = P("graph"); s.add_argument("action", choices=["check", "next", "render"]); s.add_argument("--graph"); s.add_argument("--full", action="store_true")
    s = P("loops"); s.add_argument("--loops"); s.add_argument("--routing"); s.add_argument("--pr-watch"); s.add_argument("--ratchet-dir"); s.add_argument("--json", action="store_true")
    s = P("ledger"); s.add_argument("--kind", required=True); s.add_argument("--note", required=True); s.add_argument("--signal"); s.add_argument("--layer"); s.add_argument("--decision"); s.add_argument("--by"); s.add_argument("--ref", action="append")
    s.add_argument("--fingerprint"); s.add_argument("--card")
    s = P("archive"); s.add_argument("--to", required=True)

    a = p.parse_args()
    if a.cmd == "init":
        if not a.slug:
            die("init requires --slug")
        return cmd_init(a)
    if a.cmd == "graph" and a.action in ("check", "render"):
        return cmd_graph(a)
    if a.cmd == "loops":
        return cmd_loops(a)
    a.slug = resolve_slug(a.root, a.slug)
    return {"show": cmd_show, "set": cmd_set, "advance": cmd_advance, "gate": cmd_gate, "card": cmd_card,
            "fail": cmd_fail, "waive": cmd_waive, "report": cmd_report, "check-clean": cmd_check_clean,
            "graph": cmd_graph, "ledger": cmd_ledger, "archive": cmd_archive}[a.cmd](a)


if __name__ == "__main__":
    main()
