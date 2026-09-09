#!/usr/bin/env python3
"""
aidlc_state.py — the compiled Control of /ai-dlc: the lifecycle state file and its transitions.

Why a script owns this (SKILL.state): the model proposes a transition, the runtime validates and
merges it. A bad proposal cannot corrupt the state — it is rejected, not merged. The state file is the
sufficient statistic for the run (只留状态，不留历史); history lives in ledger.md, which is append-only
and never rolled back (WikiSkill asymmetric rollback: artifacts roll back, judgments and failures don't).
Since v0.6.0 every ledger row is mirrored into trace.jsonl with typed edges (caused_by / decided_by /
supersedes / implements / references / depends_on / rejected_alternative) — see trace.py.

Usage:
  aidlc_state.py init    --slug S --title T [--track psl|task] [--root .aidlc]
  aidlc_state.py show    [--slug S] [--root .aidlc]
  aidlc_state.py set     [--slug S] key=value ...          # dotted keys, whitelisted (see SETTABLE)
  aidlc_state.py size    [--slug S] [--files N --acs M --human-acs K | --base REF | --from-issue BODY.md]
                        [--early] [--commit]                # --early: 还没 diff 时定档，永远够不到 S
  aidlc_state.py plan    [--slug S] [--json]                 # 启动前的有效规模：跑几个阶段、几道门、跳了什么
  aidlc_state.py doctor  [--slug S] [--json]                 # 装置健康度；建议性，从不阻断门禁
  aidlc_state.py repo    [--slug S] [--json] [--path dos|agent_map|invariants]
                        # X1 仓库级制品（dos.yaml / agent-map.md / invariants/）在不在、进没进 git
  aidlc_state.py note    [--slug S] --kind interpretation|deviation|tradeoff|open_question --text T
  aidlc_state.py note    [--slug S] --promote n-0001 --to project --by NAME    # Open questions 不可晋升
  aidlc_state.py notes   [--slug S] [--for-gate g1|g2|g3] [--json]             # 门禁仪式：逐字呈现
  aidlc_state.py autonomy [--slug S] --level ask_each|auto_until_gate|auto_until_failure --by NAME
  aidlc_state.py advance [--slug S] <stage> [--force --reason R]
  aidlc_state.py gate    [--slug S] <g1|g2|g3> --verdict pass|reject|waived --by NAME
                        [--record PATH] [--attribution derivation_error|rule_error|none]
                        [--secondary-attribution derivation_error|rule_error]…  (recorded, never counted)
                        [--signer-kind human|delegated_agent] [--authorization TEXT]   # delegated requires authorization
  aidlc_state.py card    [--slug S] CARD-xx --status todo|doing|done|blocked|skipped [--reason R]
                        [--commit SHA] [--ac AC-id ...]     # skipped 必须给理由，并列出会被拖累的卡
  aidlc_state.py fail    [--slug S] --signal SIG [--card CARD-xx] [--fingerprint FP | --evidence TEXT]
                        [--score X] [--by REPORTER] [--routing PATH]   # -> route decision JSON + counters + ledger
  aidlc_state.py waive   [--slug S] --signal SIG --reason R --by WHO
                        [--signer-kind human|delegated_agent] [--authorization TEXT]
                        [--fingerprint FP] [--card CARD-xx] [--layer L] [--stage S] [--scope TEXT] [--ref type:target ...]
                        # a waiver WITHOUT a transition; prints the event id to cite as a waiver_ref
  aidlc_state.py report  [--slug S] --path FAILURE_REPORT.md            # clears pending.failure_report
  aidlc_state.py check-clean [--slug S] [--as-hook]                     # exit 0 clean / 1 dirty; --as-hook prints Stop-hook JSON
  aidlc_state.py graph   check|next|render [--graph PATH] [--full]      # execution graph as data (assets/graph.yaml)
  aidlc_state.py loops   [--slug S] [--loops PATH] [--pr-watch DIR] [--ratchet-dir DIR]   # budget consumption per loop
  aidlc_state.py ledger  [--slug S] --kind K --note TEXT [--signal S] [--layer L] [--decision D] [--by B]
                        [--fingerprint FP] [--card CARD-xx] [--ref type:target ...]
  aidlc_state.py archive [--slug S] --to DIR               # copy state + ledger + trace + contract + listed artifacts

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
  - the breadth knob is a grid, not an if: `assets/sizing.yaml.stages` says which stages a tier skips,
    `never_skippable` says which no tier may, and a skip is only granted to a tier derived from evidence
    (size_source ∈ derived / derived_early) — `set intake.size=S` opens nothing. verify_sizing.py asserts
    the grid against ORDER and against the prerequisites this file implements
  - X1 的仓库级制品（dos.yaml / agent-map.md / invariants/）是**发现**来的，不是手 set 的：
    `repo_assets.py` 按候选路径序在项目目录里找，并用 `git ls-files` 核对它们进没进版本库
    （没进 = 队友 clone 下来是空的 = 不是「有本体」，是「你有本体」）。`sizing.yaml.repo_assets`
    说每档 / 每轨要求到哪一级，`prereqs("issue")` 把 required 那级编译成拦得住的前置——
    缺席时下游闭包是**未检**不是通过，而未检以前是一条静默的 flag
  - learning is compiled at `init`, never mid-run: notes promoted to project rules take effect on the NEXT
    run (the gates you already signed correspond to one stable rule set — same reason as invariant 13)
Semantic half (a judge / a human, never this script): whether the candidate layer is the RIGHT layer.
"""
import argparse
import datetime as _dt
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repo_assets  # noqa: E402  —— X1 仓库级制品的发现与 git 核对（同目录）

ROOT_DEFAULT = ".aidlc"
LEGACY_ROOT = ".sdlc"   # 改名前的运行时目录；见 resolve_root
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
ORDER = ["intake", "track", "issue", "branch", "contract", "g2", "cards", "implement",
         "acceptance", "pr", "review", "g3", "merge", "release", "archive"]
SETTABLE = {
    "track", "title",
    "intake.size",   # size_source 不可 set：只有 cmd_size 能写 derived，手设的档位拿不到豁免
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
    "world.psl", "world.derived_dir", "world.dos", "world.invariants", "world.agent_map",
    "world.form_draft_sha256",
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
# 体量分档（assets/sizing.yaml）。极性不可反转：缺省是 M（较严），S 的豁免必须用证据换。
SIZES = ("S", "M", "L")
BUDGET_KEY = {"card": "card_retries", "plan": "plan_reflows", "task": "task_reflows",
              "ontology": "ontology_reflows", "world": "world_reflows"}
# Append-only logs can only point backwards, so the causal edge is `caused_by` (effect → cause); the rest are
# timeless (artifact anchors) or backwards (decided_by, supersedes). Same seven relations as the graph-engineering
# canon, with `caused` read from the effect's side.
TRACE_EDGE_TYPES = {"caused_by", "decided_by", "supersedes", "implements", "references", "depends_on", "rejected_alternative"}


def now():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def die(msg, code=2):
    sys.stderr.write(f"aidlc_state: {msg}\n")
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


def resolve_root(root):
    """→ (root, note)。插件在 2026-09-08 从 `sdlc` 改名 AI-DLC，运行时目录随之 `.sdlc/` → `.aidlc/`。

    改名不该让一次跑到一半的运行失联：默认根不存在而旧根还在时，继续用旧根，并把这件事**说出来**
    （note 会进命令的 JSON 输出）。静默回退会让人以为自己在写新目录，下一次归档就找不到东西。
    只在用了默认值时回退——显式 `--root` 是显式意图，不替它改。新建（init）永远用新根：
    一次新的运行没有理由留在旧名字上。
    """
    if root != ROOT_DEFAULT or os.path.isdir(root) or not os.path.isdir(LEGACY_ROOT):
        return root, None
    return LEGACY_ROOT, (f"using the pre-rename runtime directory `{LEGACY_ROOT}/` — this plugin was called "
                         f"`sdlc` until 2026-09-08 and new runs write `{ROOT_DEFAULT}/`. Finish or archive this "
                         f"run, or move the directory yourself; nothing is migrated behind your back.")


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
    """`.aidlc/` is runtime state, not a deliverable: the archive is what gets committed (`archive --to
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


# ---- the breadth knob: which stages this run actually executes -------------------------------
# 借鉴 AWS AI-DLC 2.0 的 scope grid（11 种 scope × 33 stage 编译成网格，bugfix 只跑 9 个）。
# 这里的网格小得多（3 档 × 15 阶段），但性质相同：**跑哪些阶段是数据，不是散在 prereqs() 里的 if**。
# 极性与整个插件一致：跳过要用证据换。default / manual 的档位一个阶段也跳不掉。
def effective_skips(st, sizing=None):
    """→ {stage: why}。这次运行实际跳过的阶段，附每条的理由。

    三重保险，任何一重不成立就跳不了：
      ① 档位必须是**推导**来的（size_source ∈ derived / derived_early）。`set intake.size=S`
         把来源打成 manual，一扇门也打不开——手设的档位拿不到豁免（v0.10.0 的极性，原样保留）。
      ② 阶段不能在 never_skippable 里。三道门与不可逆动作在那张表里，即使 sizing.yaml 被改错
         也拦得住——数据出错时脚本站在严的那一侧。
      ③ 每条 skip 必须写 why。没有理由的跳过在复盘时无法被质疑，也就无法被撤销。
    """
    if sizing is None:
        try:
            sizing = load_sizing()
        except SystemExit:
            return {}
    if (st.get("intake") or {}).get("size_source") not in ("derived", "derived_early"):
        return {}
    tier = (st.get("intake") or {}).get("size")
    never = set(((sizing.get("never_skippable") or {}).get("stages")) or [])
    out = {}
    for row in ((sizing.get("stages") or {}).get(tier) or {}).get("skip") or []:
        s, why = row.get("stage"), (row.get("why") or "").strip()
        if s in ORDER and s not in never and why:
            out[s] = why
    return out


def jumped_stages(st, target, skips):
    """从当前阶段跳到 target 时被越过的阶段（不含两端）。"""
    ci, ti = ORDER.index(st["stage"]), ORDER.index(target)
    return [s for s in ORDER[ci + 1:ti] if s in skips] if ti > ci else []


# ---- prerequisites: checked against state, never against the model's claim ------------------
def prereqs(st, target, skips=None):
    skips = effective_skips(st) if skips is None else skips
    unmet = []
    need = lambda cond, msg: (None if cond else unmet.append(msg))
    if target == "track":
        need(st.get("title"), "title set")
    elif target == "issue":
        need(st.get("track") in ("psl", "task"), "track decided (psl|task)")
        if st.get("track") == "psl":
            need(get_path(st, "gates.g1.verdict") in ("pass", "waived"),
                 "G1 recorded as pass (PSL track) — run `gate g1`")
        # X1：本体在 issue 之前就位，因为 `/issue --dos` 的词表闭包是**客观触发 PSL 轨**那条
        # 判据的全部依据。没有 dos.yaml 时闭包不是失败也不是通过，是没算——而没算过的判据
        # 挡不住「自信而错的人绕开 G1」。要求到哪一级由 sizing.yaml.repo_assets 说了算。
        unmet.extend(repo_asset_unmet(st))
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
        # 卡的前置只在 cards 阶段真的跑了的时候要求。cards 被网格跳掉时，实现者的输入是契约的
        # AC 本身——那是 S 档 skip 的 why 里写明的交换条件，不是这里悄悄放松。
        if "cards" not in skips:
            need(get_path(st, "cards.lint_passed") is True, "cards.lint_passed true (lint_cards.py)")
            need(get_path(st, "cards.items"), "at least one card registered (`card CARD-xx --status todo`)")
    elif target == "acceptance":
        if "cards" not in skips:
            items = get_path(st, "cards.items", {}) or {}
            pending = [k for k, v in items.items() if v.get("status") not in ("done", "skipped")]
            need(not pending, f"all cards done or skipped (pending: {pending})")
        need(not get_path(st, "pending.failure_report"), "pending failure report written (`report --path …`)")
    elif target == "pr":
        # 整体验收要么真跑了、要么被显式留痕跳过、要么被网格跳掉（网格的跳过在 advance 里
        # 会写成一条有类型的 size_exemption 账本行，不是无声的空白）。
        ok = (get_path(st, "acceptance.evaluation_result") or get_path(st, "acceptance.skipped_reason")
              or "acceptance" in skips)
        need(ok, "acceptance.evaluation_result path OR acceptance.skipped_reason "
                 "(or a derived tier whose grid skips acceptance — `size --files N --acs M --commit`)")
        need(not get_path(st, "pending.failure_report"), "pending failure report written (`report --path …`)")
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


def next_allowed(st, target, skips=None):
    cur = st["stage"]
    ci, ti = ORDER.index(cur), ORDER.index(target)
    if ti == ci + 1:
        return True
    # legal skip: g3 not required → review → merge
    if cur == "review" and target == "merge" and get_path(st, "gates.g3.required", True) is False:
        return True
    # legal skip: 体量网格。中间被越过的每一个阶段都必须在这一档的 skip 集合里——
    # 越过一个不在网格里的阶段仍然是越级，仍然要 --force + --reason，仍然记成 waiver。
    skips = effective_skips(st) if skips is None else skips
    if ti > ci + 1 and all(s in skips for s in ORDER[ci + 1:ti]):
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
        # 缺省 M：漏填得到较严的路径。S 档的豁免只能由 `size --commit` 用证据换（sizing.yaml）。
        "intake": {"size": "M", "size_source": "default", "size_evidence": {}},
        "waivers": [], "assumptions": [], "artifacts": {},
        "notes": {"promoted": []},
    }
    # X1 仓库级制品在这里被**发现**，不是被 set。它们在项目目录里、进 git、全组共用一份，
    # 而 state.json 是 per-feature 的：每个 slug 手抄一遍仓库级事实，抄错一份没人会发现。
    disc = repo_assets.discover()
    world = {k: disc[k]["path"] for k in ("dos", "agent_map", "invariants") if disc[k].get("found")}
    if world:
        st["world"] = world

    # 学习**下轮生效**：上一轮晋升到 project 的规则在这里被编译进来（记下路径 + 内容哈希 + 条数）。
    # 跑动中晋升的规则不影响本轮——你前面批准过的门对应的是当时那套规则集合，框架不在跑动中抽掉地基。
    lp = learnings_path(a.root)
    if os.path.isfile(lp):
        body = open(lp, encoding="utf-8").read()
        st["learnings"] = {"path": lp, "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                           "rules": len([l for l in body.splitlines() if l.startswith("- [n-")]),
                           "compiled_at": now()}
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "init", f"title={a.title} track={st['track']}"
                  + (f" | learnings compiled: {st['learnings']['rules']} rules from {lp}" if st.get("learnings") else ""),
                  stage="intake")
    out = {"ok": True, "state": sp}
    if st.get("learnings"):
        out["learnings"] = st["learnings"]
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
        if k == "intake.size" and v not in SIZES:
            die(f"intake.size must be {'|'.join(SIZES)}; prefer `size --files N --acs M --commit` so the "
                "evidence is recorded with it (a tier set by hand grants exemptions nobody can audit)", 1)
        if k == "lock.stage" and v not in LOCK_STAGES:
            die(f"lock.stage must be {'|'.join(LOCK_STAGES)} (the two signing stages)", 1)
        set_path(st, k, coerce(v))
        if k == "intake.size":
            set_path(st, "intake.size_source", "manual")   # 手设 = 无证据 = 不给豁免
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
    skips = effective_skips(st)
    jumped = jumped_stages(st, a.stage, skips)
    problems = []
    if not next_allowed(st, a.stage, skips):
        problems.append(f"not the next stage after {st['stage']} (order: {' → '.join(ORDER)}"
                        + (f"; this tier may skip {sorted(skips)}" if skips else "") + ")")
    problems += prereqs(st, a.stage, skips)
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
    # 网格跳过的每一个阶段都写成一条有类型、可数的记录（不是一句自由文本的借口）——
    # /retro 按档分桶数逃逸缺陷，靠的就是这些行。豁免不留痕就不是豁免，是遗漏。
    ev = get_path(st, "intake.size_evidence", {}) or {}
    tier = get_path(st, "intake.size")
    # 被越过的阶段之外，还有一种豁免：**进了这个阶段却空手走人**。整体验收是唯一有下游可见产物的
    # 可跳阶段，所以 stage=acceptance 却既没有 evaluation_result 也没有 skipped_reason 就去 pr 时，
    # 用的同样是网格的豁免，同样要留痕。少了这一条，「走到验收再空手离开」是一条不留任何记录的路
    # ——而 /retro 正是靠这些行按档分桶数逃逸缺陷的（既有用例在这里抓到了本轮的回归）。
    if (a.stage == "pr" and prev == "acceptance" and "acceptance" in skips
            and not get_path(st, "acceptance.evaluation_result")
            and not get_path(st, "acceptance.skipped_reason")):
        jumped = jumped + ["acceptance"]
    exempted = []
    for s in jumped:
        note = (f"size={tier} grid skips `{s}` (rule {ev.get('rule', '?')}: files={ev.get('files')} "
                f"acs={ev.get('acs')} human_acs={ev.get('human_acs')}) — {skips[s]}")
        exempted.append({"stage": s, "note": note})
        if s == "acceptance":   # 下游（metrics.py / verify_pr.py）读这两个字段判"验收去哪了"
            set_path(st, "acceptance.skipped_reason", note)
            set_path(st, "acceptance.skipped_by", "size_tier")
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "advance", f"{prev} → {a.stage}", stage=a.stage, refs=refs)
    for x in exempted:
        ledger_append(a.root, a.slug, "size_exemption", x["note"], stage=a.stage, decision=tier)
    print(json.dumps({"ok": True, "from": prev, "to": a.stage, "waived": bool(problems),
                      **({"size_exemption": [x["note"] for x in exempted]} if exempted else {})},
                     ensure_ascii=False))


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


def card_dependents(cards_dir, card):
    """→ 声明 depends_on 里含 card 的卡。跳过一张卡时，依赖它的那些多半也会失败——
    这句警告必须**当场**给出，而不是等它们一张张红给你看（AWS AI-DLC 的 [S] 标记：
    跳过是三选一里最贵的一个，因为它的代价不落在被跳的那张卡上）。"""
    out = []
    if not cards_dir or not os.path.isdir(cards_dir):
        return out
    for p in sorted(glob.glob(os.path.join(cards_dir, "*.yaml")) + glob.glob(os.path.join(cards_dir, "*.yml"))):
        d = load_yaml(p) or {}
        dep = d.get("depends_on") or []
        if isinstance(dep, str):
            dep = [dep]
        if card in dep:
            out.append(d.get("id") or os.path.splitext(os.path.basename(p))[0])
    return out


def cmd_card(a):
    st = load(a.root, a.slug)
    items = st.setdefault("cards", {}).setdefault("items", {})
    c = items.setdefault(a.card, {"status": "todo", "retries": 0, "commits": []})
    if a.status == "skipped" and not a.reason:
        die("`--status skipped` requires --reason. 跳过是失败三选一（重试 / 跳过 / 中止）里最贵的一个："
            "它把代价推给依赖它的卡，而那笔代价没有理由就无法在复盘时被追回", 1)
    c["status"] = a.status
    if a.status == "skipped":
        c["skip_reason"] = a.reason
    dependents = card_dependents(get_path(st, "cards.dir"), a.card) if a.status == "skipped" else []
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
    ledger_append(a.root, a.slug, "card",
                  f"{a.card} → {a.status}" + (f": {a.reason}" if a.reason else "") + (f" commit {sha}" if sha else "")
                  + (f" | dependents likely to fail: {dependents}" if dependents else ""),
                  stage=st["stage"], refs=refs, extra=extra)
    out = {"ok": True, "card": a.card, "status": a.status}
    if sha:
        out["commit"] = sha
    if a.status == "skipped":
        out["reason"] = a.reason
        out["dependents_likely_to_fail"] = dependents
        if dependents:
            out["warning"] = (f"{len(dependents)} card(s) declare depends_on {a.card} — skipping it means they "
                              "will most likely fail too. Skip them deliberately or fix this one.")
    print(json.dumps(out, ensure_ascii=False))


def load_sizing(path=None):
    p = path or os.path.join(ASSETS, "sizing.yaml")
    d = load_yaml(p)
    if not d or not d.get("rules"):
        die(f"sizing table missing or empty: {p}", 2)
    return d


def repo_asset_requirements(st, sizing=None):
    """→ {asset_key: optional|recommended|required}。档位一条、轨道一条，取更严的那条。

    要求是**数据**（`sizing.yaml.repo_assets`）不是散在 prereqs 里的 if，理由与阶段网格相同：
    一条只写在代码里的要求，改的时候没人会连同它的理由一起改。

    极性同网格：缺省得到较严的那条。`intake.size` 缺省是 M，M 档 dos 是 recommended——
    不拦，但 doctor 会 warn，且 `/issue` 的闭包会被记成**未检**而不是通过。
    """
    try:
        sizing = sizing if sizing is not None else load_sizing()
    except SystemExit:
        return {}
    conf = sizing.get("repo_assets") or {}
    levels = list(conf.get("levels") or repo_assets.LEVELS)
    tier = get_path(st, "intake.size") or "M"
    track = st.get("track")
    by_track = (conf.get("by_track") or {}).get(track) or {}
    out = {}
    for key in repo_assets.KEYS:
        lv = ((conf.get("by_tier") or {}).get(key) or {}).get(tier, "optional")
        tr = by_track.get(key)
        if tr in levels and (lv not in levels or levels.index(tr) > levels.index(lv)):
            lv = tr
        out[key] = lv if lv in levels else "optional"
    return out


def repo_asset_unmet(st):
    """→ [str]。只有 required 那一级进 unmet；recommended / optional 归 doctor 的 warn / info。

    绿地仓库（没有存量代码，本体无处可抽）走 `--force --reason greenfield`——那是一条记进
    waivers 与账本的豁免，不是一片空白。这正是「缺席要用证据换」在 X1 上的形态。
    """
    req = repo_asset_requirements(st)
    if not any(v == "required" for v in req.values()):
        return []
    disc = repo_assets.discover()
    out = []
    for key, level in req.items():
        if level != "required":
            continue
        rec = disc.get(key) or {}
        if rec.get("found"):
            continue
        spec = repo_assets.SPEC[key]
        out.append(
            f"X1 仓库级 `{spec['filename']}` 不在（找过 {', '.join(rec.get('searched') or [])}）——"
            f"跑 {spec['produced_by']}，写到 `{rec.get('canonical')}` 并**提交进 git**（全组共用一份，"
            f"不放 .aidlc/）。没有它，{spec['consumers'][0] if spec.get('consumers') else '下游闭包'}；"
            f"看 `aidlc_state.py repo`。绿地仓库：`advance issue --force --reason greenfield`")
    return out


def derive_size(sizing, *, track, files, acs, human_acs):
    """→ (tier, rule_id, why)。规则按顺序求值，第一条命中即定档；没有形容词，只有可数的量。

    缺一个量的规则不会命中：`files_max: 3` 在 files=None 时求值为假，不是为真。这条性质是
    「早定档给不出 S」的全部依据——S 的唯一入口 SZ-05 要 files，而 intake / issue 阶段没有 diff。
    sizing.yaml 的 `needs:` 把这件事写成可检的声明，`verify_sizing.py` 会核它与 `when:` 一致。
    """
    for r in sizing["rules"]:
        w = r.get("when") or {}
        ok = True
        if "track" in w and w["track"] != track:
            ok = False
        for key, val, actual in (("files_min", w.get("files_min"), files),
                                 ("acs_min", w.get("acs_min"), acs),
                                 ("human_acs_min", w.get("human_acs_min"), human_acs)):
            if val is not None and not (actual is not None and actual >= val):
                ok = False
        for key, val, actual in (("files_max", w.get("files_max"), files),
                                 ("acs_max", w.get("acs_max"), acs),
                                 ("human_acs_max", w.get("human_acs_max"), human_acs)):
            if val is not None and not (actual is not None and actual <= val):
                ok = False
        if ok:
            return r["tier"], r["id"], r.get("why", "")
    return "M", "fallback", "no rule matched"


def count_acs(done_when):
    """从契约里数 AC —— 这是可核对的来源，不是引擎报的数。→ (总数, human 数) 或 (None, None)。"""
    d = load_yaml(done_when)
    if not d:
        return None, None
    acc = d.get("acceptance") or []
    if not isinstance(acc, list):
        return None, None
    return len(acc), sum(1 for x in acc if isinstance(x, dict) and x.get("kind") == "human")


def acs_from_issue(path):
    """→ (total, human) 或 die。数 AC 的**同一次读**要同时给出数字和它的来路。

    不自己解析 issue 的 markdown：verify_issue.py 已经解析并校验了那个 AC v2 块，它的
    `acceptance_stats` 就是权威。一个自己写的第二个解析器迟早与它分叉，而分叉出来的那个数
    会被用来换豁免。issue 本身没过 verify_issue.py 时拒绝取数——形状不对的块数出来的数不可信。
    """
    vi = os.path.join(HERE, "..", "..", "issue", "scripts", "verify_issue.py")
    if not os.path.isfile(vi):
        die(f"verify_issue.py not found at {vi} — cannot count ACs from an issue body", 2)
    r = subprocess.run([sys.executable, vi, path], capture_output=True, text=True)
    try:
        doc = json.loads(r.stdout)
    except Exception:
        die(f"verify_issue.py produced no parsable JSON for {path}:\n{r.stderr.strip() or r.stdout.strip()}", 2)
    if doc.get("rejects"):
        die(f"{path} does not pass verify_issue.py ({len(doc['rejects'])} rejects) — an AC count read out of a "
            "malformed acceptance block is a guess, and a guess must not buy a tier. Fix the issue first:\n  - "
            + "\n  - ".join(doc["rejects"][:5]), 1)
    s = doc.get("acceptance_stats") or {}
    return s.get("total"), s.get("human")


def cmd_size(a):
    st = load(a.root, a.slug)
    sizing = load_sizing(a.sizing)
    files, acs, human = a.files, a.acs, a.human_acs
    src = {"files": "--files", "acs": "--acs", "human_acs": "--human-acs"}
    if (acs is None or human is None) and a.from_issue:
        i_acs, i_human = acs_from_issue(a.from_issue)
        if acs is None and i_acs is not None:
            acs, src["acs"] = i_acs, f"verify_issue:{a.from_issue}"
        if human is None and i_human is not None:
            human, src["human_acs"] = i_human, f"verify_issue:{a.from_issue}"
    dw = get_path(st, "contract.done_when")
    if (acs is None or human is None) and dw and os.path.isfile(dw):
        c_acs, c_human = count_acs(dw)
        if acs is None and c_acs is not None:
            acs, src["acs"] = c_acs, f"contract:{dw}"
        if human is None and c_human is not None:
            human, src["human_acs"] = c_human, f"contract:{dw}"
    if files is None and a.base:
        code, out, _ = run_git(["diff", "--name-only", f"{a.base}...HEAD"])
        if code == 0:
            files, src["files"] = len([l for l in out.splitlines() if l.strip()]), f"git diff {a.base}...HEAD"
    missing = [k for k, v in (("files", files), ("acs", acs)) if v is None]
    # 早定档（v0.12.0）：intake / issue 阶段还没有 diff，files 必然缺。允许在这里定档，但
    # 来源记成 derived_early —— 而 S 档的唯一入口 SZ-05 需要 files，所以早定档在结构上
    # 只能把你推向 L 或留在 M，给不出任何豁免。这不是额外加的限制，是这组规则本来的形状。
    if missing and not (a.early or a.allow_unknown):
        die(f"cannot derive a tier without {missing} — pass --files/--acs, --from-issue <body.md>, or "
            "--base <ref> with a contract; use --early to size before there is a diff (a tier derived "
            "without files can never reach S), or --allow-unknown to record the fallback tier. "
            "An unmeasured tier is a guess, and a guess that grants exemptions is worse than the default.", 1)
    tier, rule_id, why = derive_size(sizing, track=st.get("track"), files=files, acs=acs, human_acs=human)
    source = "derived_early" if (a.early and missing) else "derived"
    ev = {"files": files, "acs": acs, "human_acs": human, "sources": src,
          "rule": rule_id, "why": why, "at": now()}
    tconf = sizing["tiers"].get(tier) or {}
    probe = dict(st)
    probe["intake"] = {**(st.get("intake") or {}), "size": tier, "size_source": source}
    grid = effective_skips(probe, sizing)
    out = {"ok": True, "tier": tier, "rule": rule_id, "why": why, "evidence": ev, "size_source": source,
           "skips": grid, "depth": tconf.get("depth"), "test_strategy": tconf.get("test_strategy"),
           "committed": False}
    if a.commit:
        prev_tier, prev_src = get_path(st, "intake.size"), get_path(st, "intake.size_source")
        # 飞行中重定档：只能改尚未开始的阶段。落在身后的 skip 一律丢弃并留痕——
        # 一次已经付过的 G2 不会因为重定档被追认为"其实不用签"（sizing.yaml recompose）。
        ci = ORDER.index(st["stage"])
        stale = sorted(s for s in grid if ORDER.index(s) <= ci)
        if stale:
            out["recompose_refused"] = stale
            for s in stale:
                grid.pop(s, None)
            st.setdefault("intake", {})["skips_frozen"] = stale
        st.setdefault("intake", {})
        st["intake"].update({"size": tier, "size_source": source, "size_evidence": ev})
        save(a.root, a.slug, st)
        ledger_append(a.root, a.slug, "size",
                      f"tier={tier} by {rule_id} ({why}) | files={files} acs={acs} human_acs={human} | source={source}",
                      stage=st["stage"], decision=tier)
        if prev_tier and prev_src != "default" and prev_tier != tier:
            ledger_append(a.root, a.slug, "size_recompose",
                          f"{prev_tier} → {tier} at stage={st['stage']}"
                          + (f" | skips refused because already passed: {stale}" if stale else ""),
                          stage=st["stage"], decision=tier)
        out["committed"], out["skips"] = True, grid
    print(json.dumps(out, ensure_ascii=False, indent=2))


# ---- plan: 启动前把这次运行的有效规模算出来，而不是跑到一半才知道 ------------------------
# 借鉴 AWS AI-DLC 2.0：它从编译网格算出本次跑几个 stage、几道门禁、几处扇出，**启动前**告诉你。
# 这里同样从网格算，不是估的。一个说不出自己要花多少道门的流程，人只能靠猜决定要不要走它。
def cmd_plan(a):
    st = load(a.root, a.slug)
    sizing = load_sizing(a.sizing)
    skips = effective_skips(st, sizing)
    tier = get_path(st, "intake.size")
    tconf = (sizing.get("tiers") or {}).get(tier) or {}
    cur = ORDER.index(st["stage"])
    run = [s for s in ORDER if s not in skips]
    gates = [g for g in ("g1", "g2", "g3") if get_path(st, f"gates.{g}.required", False)]
    out = {
        "slug": st["slug"], "track": st.get("track"), "stage": st["stage"],
        "tier": tier, "size_source": get_path(st, "intake.size_source"),
        "depth": tconf.get("depth"), "test_strategy": tconf.get("test_strategy"),
        "autonomy": get_path(st, "autonomy.level", "unset"),
        "stages_total": len(run), "stages_done": len([s for s in run if ORDER.index(s) < cur]),
        "stages_remaining": [s for s in run if ORDER.index(s) > cur],
        "skipped": skips,
        "human_gates": gates, "human_gates_count": len(gates),
        "gate_verdicts": {g: get_path(st, f"gates.{g}.verdict") for g in gates},
        "fleet_subset": tconf.get("fleet_subset"),
    }
    if get_path(st, "intake.size_source") in (None, "default", "manual"):
        out["note"] = ("tier is not derived — no stage is skipped and no exemption applies. "
                       "Run `size --from-issue <body.md> --early --commit` (before there is a diff) or "
                       "`size --base <ref> --commit` (after) to earn a tier with evidence.")
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(f"slug={out['slug']} track={out['track']} stage={out['stage']}")
    print(f"tier={tier} ({out['size_source']}) · depth={out['depth']} · test_strategy={out['test_strategy']} "
          f"· autonomy={out['autonomy']}")
    print(f"stages: {out['stages_total']} to run ({out['stages_done']} done) · human gates: {len(gates)} "
          f"{ {g: out['gate_verdicts'][g] for g in gates} }")
    if skips:
        print("skipped by the size grid:")
        for s, why in sorted(skips.items(), key=lambda kv: ORDER.index(kv[0])):
            print(f"  - {s}: {why}")
    if out.get("note"):
        print(f"note: {out['note']}")
    print("remaining: " + " → ".join(out["stages_remaining"]))


# ---- doctor / repo: 装置健康度与仓库就绪度（都建议性，都不阻断） --------------------------
# doctor 借鉴 AWS AI-DLC 的 --doctor：按需查漂移，从不阻断门禁。它不进 advance 的前置条件——
# 一个会阻断的 doctor 会变成第四道门，而这个插件只有三道门。
# repo 报的是 X1 仓库级制品的落地（一次性，全组共用一份）：它同样只报不拦——真正拦得住的是
# prereqs("issue") 里的 required 那一级，而那一条是 sizing.yaml 的数据说了算，不是这里。
def state_or_empty(root, slug):
    """→ state dict，读不到就给 {}，且**不往 stderr 写**。

    doctor / repo 查的是装置与仓库，「这个仓库还没有任何 run」是它们最常见的正常入口
    （第一次把 /ai-dlc 带进一个仓库时正是如此）。让 die() 的 stderr 漏出去，会把一条
    正常路径印成一条错误。
    """
    if not (slug or os.path.isdir(root)):
        return {}
    err = sys.stderr
    try:
        sys.stderr = io.StringIO()
        return load(root, resolve_slug(root, slug))
    except SystemExit:
        return {}
    finally:
        sys.stderr = err


def cmd_repo(a):
    """X1 仓库级制品的落地报告 + 缺席时的一次性补法。

    为什么与 doctor 分开：doctor 报的是「这一次运行的装置健不健康」，每次跑都看；
    仓库落地是**一次性**的事——做一次，之后每个 slug 自动发现它。第一次把 /ai-dlc 带进一个
    仓库时看这一条，之后不用再看。两者共用 repo_assets 的同一份事实与同一套措辞。

    退出码：0 = 要求都满足且位置 / 版本库没问题 · 1 = 有 error / warn（可用作 CI 的就绪检查）。
    """
    st = state_or_empty(a.root, a.slug)
    disc = repo_assets.discover(refresh=True)
    if getattr(a, "path", None):
        rec = disc.get(a.path) or {}
        if not rec.get("found"):
            sys.exit(1)
        print(os.path.join(disc["_root"]["path"], rec["path"]))
        return
    req = repo_asset_requirements(st)
    fs = repo_assets.findings(disc, req)
    bad = [f for f in fs if f["severity"] in ("error", "warn")]
    if a.json:
        print(json.dumps({"ok": not bad, "root": disc["_root"], "requirements": req,
                          "assets": {k: disc[k] for k in repo_assets.KEYS}, "findings": fs},
                         ensure_ascii=False, indent=2))
    else:
        print(repo_assets.render(disc, req))
        if fs:
            print()
            for f in fs:
                print(f"[{f['severity']}] {f['check']}: {f['hint']}")
        if any(not disc[k].get("found") for k in repo_assets.KEYS):
            print(repo_assets.ONBOARDING)
        req_missing = [k for k, v in req.items() if v == "required" and not disc[k].get("found")]
        if req_missing:
            print(f"这一档（{get_path(st, 'intake.size') or 'M'} / track={st.get('track') or 'unset'}）"
                  f"把 {req_missing} 列为 required：`advance issue` 会拦。"
                  f"绿地仓库用 `--force --reason greenfield`，豁免记进账本。")
    sys.exit(1 if bad else 0)


def cmd_doctor(a):
    findings = []
    def add(sev, what, hint):
        findings.append({"severity": sev, "check": what, "hint": hint})
    try:
        import yaml  # noqa: F401
    except ImportError:
        add("error", "pyyaml", "pip install pyyaml — 契约校验、图 / 环 / 网格 lint 全都要它")
    for name, rel in (("verify_graph", "verify_graph.py"), ("verify_loop", "verify_loop.py"),
                      ("verify_sizing", "verify_sizing.py"), ("trace", "trace.py"),
                      ("lock_done_when", "lock_done_when.py")):
        if not os.path.isfile(os.path.join(HERE, rel)):
            add("error", name, f"missing script: {os.path.join(HERE, rel)}")
    for name, rel in (("validate_done_when_v2", "../../donewhen-extract/scripts/validate_done_when_v2.py"),
                      ("lint_cards", "../../plan-cards/scripts/lint_cards.py"),
                      ("verify_issue", "../../issue/scripts/verify_issue.py"),
                      ("verify_commit", "../../commit/scripts/verify_commit.py"),
                      ("metrics", "../../retro/scripts/metrics.py")):
        if not os.path.isfile(os.path.join(HERE, rel)):
            add("error", name, f"missing sibling script: {rel}")
    for label, script, args in (("graph", "verify_graph.py", [os.path.join(ASSETS, "graph.yaml")]),
                                ("loops", "verify_loop.py", [os.path.join(ASSETS, "loops.yaml")]),
                                ("sizing", "verify_sizing.py", [os.path.join(ASSETS, "sizing.yaml")])):
        p = os.path.join(HERE, script)
        if os.path.isfile(p):
            r = subprocess.run([sys.executable, p] + args, capture_output=True, text=True)
            if r.returncode != 0:
                add("error", f"{label} lint", (r.stdout or r.stderr).strip().splitlines()[-1][:200] if (r.stdout or r.stderr) else "non-zero exit")
    for tool, hint in (("git", "这条流水线的每一步都在 git 里"), ("gh", "issue / PR / review 都走 gh；`gh auth login`")):
        if not shutil.which(tool):
            add("warn", tool, f"not on PATH — {hint}")
    settings = os.path.join(os.getcwd(), ".claude", "settings.json")
    hook_ok = False
    if os.path.isfile(settings):
        try:
            hook_ok = "check-clean" in open(settings, encoding="utf-8").read()
        except OSError:
            pass
    if not hook_ok:
        add("info", "stop hook", "check-clean 的 Stop hook 没装（assets/hooks/stop-clean-state.json 是模板，"
                                 "有意不自动安装）。装上之后，卡还 doing 且工作区脏、或升级后没写失败报告，就结束不了 session")
    st = state_or_empty(a.root, a.slug)
    if st:
        if get_path(st, "pending.failure_report"):
            add("warn", "pending failure report", "有一次升级还没写失败报告（`report --path …`）")
        if get_path(st, "intake.size_source") in ("default", None):
            add("info", "tier", "档位还是缺省 M（没有证据）。`plan` 会告诉你这意味着一个阶段也跳不掉")
    # 仓库侧就绪度（X1）。doctor 原来只查装置——pyyaml、兄弟脚本、git / gh、Stop hook——
    # 一条也查不到「这个仓库有没有本体」，而缺席时下游是**静默降级**（未检 ≠ 通过）。
    # 严重度由 sizing.yaml.repo_assets 的档位给；「找到了但没进 git / 落在 .aidlc」一律 warn，
    # 与档位无关：团队共享不是可以按档放宽的偏好。
    for f in repo_assets.findings(repo_assets.discover(), repo_asset_requirements(st)):
        add(f["severity"], f["check"], f["hint"])
    order = {"error": 0, "warn": 1, "info": 2}
    findings.sort(key=lambda f: order[f["severity"]])
    bad = [f for f in findings if f["severity"] == "error"]
    if a.json:
        print(json.dumps({"ok": not bad, "findings": findings}, ensure_ascii=False, indent=2))
    else:
        if not findings:
            print("doctor: 无发现。")
        for f in findings:
            print(f"[{f['severity']}] {f['check']}: {f['hint']}")
        print(f"\ndoctor 是建议性的，从不阻断门禁（{len(bad)} error / "
              f"{len([f for f in findings if f['severity'] == 'warn'])} warn）。")
    sys.exit(1 if bad else 0)


# ---- notes: 解释日记（四格）+ 门禁仪式 + 下轮生效 ------------------------------------------
# 借鉴 AWS AI-DLC 2.0 的 memory.md：账本记的是**已经发生的错**（失败 / 回流 / 裁决 / 豁免），
# 记不到"规格含糊处 agent 当场做了什么选择"。那一条通道这个插件原来一条都没有：
# divergence.py 抓的是事前 N 份草案的分歧，抓不到实现中途的默认填充。
#
# 四个格子的分法照抄，因为它分得对：前三个是可固化的知识，第四个明确**不晋升**——
# open question 是研究项，不是规则。作用域默认最窄，且**没有 org 通道**（也照抄）。
NOTE_KINDS = ("interpretation", "deviation", "tradeoff", "open_question")
NOTE_HEADINGS = {"interpretation": "Interpretations", "deviation": "Deviations",
                 "tradeoff": "Tradeoffs", "open_question": "Open questions"}
PROMOTABLE = ("interpretation", "deviation", "tradeoff")
NOTE_RE = re.compile(r"^- \[(n-\d{4,})\] (\S+) · stage=(\S+) · (.*)$")


def notes_path(root, slug):
    return os.path.join(paths(root, slug)[0], "notes.md")


def learnings_path(root):
    return os.path.join(root, "learnings", "project.md")


def read_notes(root, slug):
    p = notes_path(root, slug)
    if not os.path.isfile(p):
        return []
    out, cur = [], None
    for line in open(p, encoding="utf-8").read().splitlines():
        if line.startswith("## "):
            cur = {v: k for k, v in NOTE_HEADINGS.items()}.get(line[3:].strip())
        m = NOTE_RE.match(line)
        if m and cur:
            out.append({"id": m.group(1), "at": m.group(2), "stage": m.group(3),
                        "text": m.group(4), "kind": cur})
    return out


def cmd_note(a):
    st = load(a.root, a.slug)
    if a.promote:
        return promote_note(a, st)
    if not a.kind or not a.text:
        die("note requires --kind and --text (or --promote <id> --to project --by <human>)", 2)
    existing = read_notes(a.root, a.slug)
    nid = f"n-{len(existing) + 1:04d}"
    p = notes_path(a.root, a.slug)
    if not os.path.isfile(p):
        body = ("# notes — 本次运行的观察日志（脚本追加，不手工编辑）\n\n"
                "> 四个格子的分法是有意的：前三格是可固化的知识，**Open questions 不晋升**——\n"
                "> 它是研究项，不是规则。门禁前 `notes --for-gate <g>` 把每一行逐字念给签字人，\n"
                "> 不改写、不做「有趣度」筛选；分类是签字人唯一要做的事。\n\n"
                + "".join(f"## {NOTE_HEADINGS[k]}\n\n" for k in NOTE_KINDS))
        atomic_write(p, body)
    text = open(p, encoding="utf-8").read()
    head = f"## {NOTE_HEADINGS[a.kind]}\n"
    if head not in text:
        text += f"\n{head}\n"
    row = f"- [{nid}] {now()} · stage={st['stage']} · {a.text.strip()}\n"
    i = text.index(head) + len(head)
    j = text.find("\n## ", i)
    j = len(text) if j == -1 else j
    block = text[i:j].rstrip("\n")
    atomic_write(p, text[:i] + (block + "\n" if block else "") + row + "\n" + text[j:].lstrip("\n"))
    ledger_append(a.root, a.slug, "note", f"[{nid}] {a.kind}: {a.text.strip()}", stage=st["stage"],
                  refs=[{"type": "references", "target": nid}])
    print(json.dumps({"ok": True, "id": nid, "kind": a.kind, "file": p}, ensure_ascii=False))


def promote_note(a, st):
    if not a.to or not a.by:
        die("--promote requires --to project and --by <human> (作用域默认最窄；没有 org 通道)", 2)
    if a.to != "project":
        die("--to must be `project` — 这里没有 team / org 通道。一条学习先在最窄的作用域上被用过，"
            "才谈得上往外提；提升是人在仓库之间做的事，不是这个脚本的权限", 1)
    rows = {n["id"]: n for n in read_notes(a.root, a.slug)}
    n = rows.get(a.promote)
    if not n:
        die(f"unknown note {a.promote} (see `notes`)", 1)
    if n["kind"] not in PROMOTABLE:
        die(f"{a.promote} is an open question — open questions do not get promoted. 它是研究项，不是规则；"
            "要它变成规则，先把它答了，再作为 interpretation / deviation / tradeoff 记一条", 1)
    already = set(get_path(st, "notes.promoted", []) or [])
    if a.promote in already:
        die(f"{a.promote} already promoted", 1)
    lp = learnings_path(a.root)
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    if not os.path.isfile(lp):
        atomic_write(lp, "# project learnings — 下一轮生效的规则\n\n"
                         "> 本轮不生效：这一轮你已经在对话里纠正过了。新规则写在盘上，等下一次 `init`\n"
                         "> 编译进去，从第一个阶段起生效。理由与不变量 13 同源——跑动中改规则会让\n"
                         "> 前面已经批准过的门失去意义，你当时批准的是另一套前提。\n\n")
    with open(lp, "a", encoding="utf-8") as fh:
        fh.write(f"- [{n['id']}] ({n['kind']}) {n['text']}  \n"
                 f"  <sub>promoted by {a.by} at {now()} from {st['slug']} stage={n['stage']}</sub>\n")
    st.setdefault("notes", {}).setdefault("promoted", []).append(a.promote)
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "note_promoted", f"[{a.promote}] → project ({n['kind']}): {n['text']}",
                  stage=st["stage"], by=a.by, decision="project",
                  refs=[{"type": "decided_by", "target": f"human:{a.by}"}])
    print(json.dumps({"ok": True, "promoted": a.promote, "to": lp,
                      "effective": "next run (init compiles it)"}, ensure_ascii=False))


def cmd_notes(a):
    st = load(a.root, a.slug)
    rows = read_notes(a.root, a.slug)
    promoted = set(get_path(st, "notes.promoted", []) or [])
    if a.json:
        print(json.dumps({"notes": [dict(r, promoted=(r["id"] in promoted)) for r in rows],
                          "for_gate": a.for_gate}, ensure_ascii=False, indent=2))
        return
    if not rows:
        print("notes: 空。`note --kind interpretation|deviation|tradeoff|open_question --text …` 记一条。")
        print("空不等于没发生——规格含糊处的选择没被记下来，只是没人看见它。")
        return
    if a.for_gate:
        print(f"# {a.for_gate.upper()} 门禁仪式 — 逐字呈现，不改写、不筛选\n")
    for k in NOTE_KINDS:
        sel = [r for r in rows if r["kind"] == k]
        print(f"## {NOTE_HEADINGS[k]} ({len(sel)})"
              + ("   ← 不晋升：研究项，不是规则" if k == "open_question" else ""))
        for r in sel:
            mark = " [已晋升]" if r["id"] in promoted else ""
            print(f"  [{r['id']}] stage={r['stage']} · {r['text']}{mark}")
        print()
    if a.for_gate:
        print("签字人要做的唯一分类：上面哪几条该变成下一轮的规则？")
        print("  晋升：`note --promote n-000X --to project --by <你>`（Open questions 不可晋升）")
        print("还有什么要留给下次的吗？（自由文本通道，永远问一次）")
        print("  `note --kind interpretation|deviation|tradeoff|open_question --text \"…\"`")


def cmd_autonomy(a):
    """自治阶梯：整个流程只问一次，答案记进 state，`--resume` 之后仍然有效。

    借鉴 AWS AI-DLC 的坑一修法：别每一步都问（保姆），也别攒到最后（审不动）。
    与原来的 `--autopilot` 的差别是它**不是一个 CLI flag**：flag 每次调用都要重给，
    恢复会话就丢；记进 state 的答案跨会话活着，而且能被 /retro 数。

    三档都不改门：G1/G2/G3 永远要人签（不变量 6）。自治调的是"逐步确认"，不是"谁签字"。
    """
    st = load(a.root, a.slug)
    st.setdefault("autonomy", {}).update({"level": a.level, "by": a.by, "at": now()})
    save(a.root, a.slug, st)
    ledger_append(a.root, a.slug, "autonomy", f"level={a.level}", stage=st["stage"], by=a.by,
                  decision=a.level, refs=[{"type": "decided_by", "target": f"human:{a.by}"}])
    print(json.dumps({"ok": True, "level": a.level,
                      "gates_still_human": ["g1", "g2", "g3"],
                      "failure_still_interrupts": True}, ensure_ascii=False))


def run_git(args):
    r = subprocess.run(["git"] + args, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


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
    budgets = dict(rt.get("budgets", {}).get(track, {}) or {})
    size = get_path(st, "intake.size")
    if size:
        try:
            budgets.update((load_sizing().get("budget_overrides", {}) or {}).get(size, {}) or {})
        except SystemExit:
            pass
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
            # the state dir itself (.aidlc/) is bookkeeping, not work left uncommitted
            dirty = [l for l in r.stdout.splitlines() if l.strip() and not l[3:].lstrip("./").startswith(root + "/") and l[3:].lstrip("./") != root + "/"]
            if dirty:
                problems.append(f"cards {doing} are `doing` and the working tree has {len(dirty)} uncommitted path(s) — commit through /commit (or stash) and register the card state")
    if a.as_hook:
        if problems:
            print(json.dumps({"decision": "block", "reason": "ai-dlc check-clean: " + " | ".join(problems)}, ensure_ascii=False))
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
            problems.append(f"graph.yaml stages {stages} ≠ aidlc_state.py ORDER {ORDER}")
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
    # notes.md 归档：解释日记是 /retro 唯一能读到"规格含糊处当时怎么选的"的地方。
    # 不归档它，下一次复盘就只剩下失败记录——只知道撞了墙，不知道当初为什么往那边走。
    srcs += [p for p in [notes_path(a.root, a.slug)] if os.path.isfile(p)]
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
    s.add_argument("--signer-kind", choices=["human", "delegated_agent"], required=True,
                   help="who is signing. No default: omitting it used to record an agent as a person, "
                        "and a discipline bypassable by omission is not a discipline (re-audit 2026-09-06)")
    s.add_argument("--authorization")
    s = P("size"); s.add_argument("--files", type=int); s.add_argument("--acs", type=int)
    s.add_argument("--human-acs", type=int, dest="human_acs"); s.add_argument("--base",
                   help="git ref: 用 diff 数改动文件数，而不是引擎报一个数")
    s.add_argument("--from-issue", dest="from_issue",
                   help="issue body 文件：AC 数与 human AC 数从 verify_issue.py 的 acceptance_stats 里读，"
                        "数字和它的来路由同一次读产生；issue 没过 verify_issue.py 就拒绝取数")
    s.add_argument("--early", action="store_true",
                   help="还没有 diff 时定档（source=derived_early）。S 的唯一入口需要 files，"
                        "所以早定档在结构上只能推向 L 或留在 M，给不出豁免")
    s.add_argument("--commit", action="store_true", help="把档位与证据写进 state（否则只推荐）")
    s.add_argument("--allow-unknown", action="store_true"); s.add_argument("--sizing")
    s = P("plan"); s.add_argument("--sizing"); s.add_argument("--json", action="store_true")
    s = P("doctor"); s.add_argument("--json", action="store_true")
    s = P("repo"); s.add_argument("--json", action="store_true")
    s.add_argument("--path", choices=repo_assets.KEYS,
                   help="只打印这个制品命中的绝对路径（没找到 exit 1 且不打印）——"
                        "给 `--dos $(… repo --path dos)` 这类接线用")
    s = P("note"); s.add_argument("--kind", choices=list(NOTE_KINDS)); s.add_argument("--text")
    s.add_argument("--promote", help="note id，晋升成下一轮的项目规则（Open questions 不可晋升）")
    s.add_argument("--to", choices=["project"], help="作用域只有 project：没有 team / org 通道")
    s.add_argument("--by")
    s = P("notes"); s.add_argument("--for-gate", dest="for_gate", choices=["g1", "g2", "g3"],
                                   help="门禁仪式：逐字念每一行，不改写不筛选")
    s.add_argument("--json", action="store_true")
    s = P("autonomy"); s.add_argument("--level", required=True,
                                      choices=["ask_each", "auto_until_gate", "auto_until_failure"])
    s.add_argument("--by", required=True)
    s = P("card"); s.add_argument("card"); s.add_argument("--status", required=True, choices=["todo", "doing", "done", "blocked", "skipped"]); s.add_argument("--commit"); s.add_argument("--ac", action="append")
    s.add_argument("--reason", help="`--status skipped` 必填：跳过把代价推给依赖它的卡")
    s = P("fail"); s.add_argument("--signal", required=True); s.add_argument("--card"); s.add_argument("--fingerprint"); s.add_argument("--evidence")
    s.add_argument("--score", type=float); s.add_argument("--by"); s.add_argument("--routing")
    s = P("waive"); s.add_argument("--signal", required=True); s.add_argument("--reason", required=True); s.add_argument("--by", required=True)
    s.add_argument("--signer-kind", choices=["human", "delegated_agent"], required=True,
                   help="who is signing. No default: omitting it used to record an agent as a person, "
                        "and a discipline bypassable by omission is not a discipline (re-audit 2026-09-06)")
    s.add_argument("--authorization")
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
    # 改名后的根解析：init 永远写新根，其余命令在新根不存在时回退到旧根并说明（resolve_root）
    if a.cmd != "init":
        a.root, root_note = resolve_root(a.root)
        # doctor / repo 查的是装置与仓库，不是「这一次运行」——第一次把 /ai-dlc 带进一个仓库时
        # 恰恰还没有任何 run，那时候「run init first」是噪音而不是提示。
        if root_note and a.cmd not in ("doctor", "repo"):
            sys.stderr.write(f"aidlc_state: {root_note}\n")
    if a.cmd in ("doctor", "repo") and not (a.slug or os.path.isdir(a.root)):
        # 这两条在没有任何 run 的仓库里也要能跑：doctor 查的是装置，repo 查的是仓库——
        # 都不是「这一次运行」。第一次把 /ai-dlc 带进一个仓库时，恰恰还没有任何 run。
        return cmd_doctor(a) if a.cmd == "doctor" else cmd_repo(a)
    a.slug = resolve_slug(a.root, a.slug)
    return {"show": cmd_show, "set": cmd_set, "advance": cmd_advance, "gate": cmd_gate, "card": cmd_card,
            "size": cmd_size, "plan": cmd_plan, "doctor": cmd_doctor, "repo": cmd_repo,
            "note": cmd_note, "notes": cmd_notes, "autonomy": cmd_autonomy,
            "fail": cmd_fail, "waive": cmd_waive, "report": cmd_report, "check-clean": cmd_check_clean,
            "graph": cmd_graph, "ledger": cmd_ledger, "archive": cmd_archive}[a.cmd](a)


if __name__ == "__main__":
    main()
