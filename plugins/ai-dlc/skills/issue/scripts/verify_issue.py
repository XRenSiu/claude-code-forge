#!/usr/bin/env python3
"""
verify_issue.py — the mechanical pre-gate for /issue: checks the PRODUCT (an issue body) against
"what a falsifiable TASK seed looks like", and FLAGS (never decides) the semantic half.

Usage:
  verify_issue.py <issue-body.md> [--dos dos.yaml] [--require-dos] [--kind feature|bug|escape]

Exit 0 = no rejects (flags may remain). Exit 1 = >=1 REJECT. Exit 2 = IO/usage error.
Output: JSON {rejects, flags, force_track, sections, acceptance_stats}.

Mechanical guarantees (REJECT on breach — the non-waivable half):
  - sections present: Intent / Track / Scope / Acceptance / Assumptions / Depends on DOS
  - Track decided: `track: psl|task`
  - Scope four items non-empty: do / dont / hard_constraints / success_metric
  - Acceptance is a fenced yaml block with `acceptance:` list; every AC has id + req + kind
  - kind: mechanical → observe + given + expect; observe is a boundary (route:/cli:/ui:/db_field:/event:),
    never a file path / source extension / function name
  - kind: human → statement + judge ∈ {product, design, tech} + evidence ∈ {checklist, demo}
  - vague quantifier in expect/statement with no digit anywhere in it → reject (adjectives → thresholds)
  - every ears_type event|state AC has an `unwanted` sibling on the same observe or a paired_with
  - existence entries carry no file paths
  - --kind bug: Repro section with ≥1 numbered step + expected + actual
  - --kind escape: Attribution section with layer ∈ {card, plan, task, ontology, world} + why_gate_missed
  - secrets-looking strings in the body → reject
  - --dos: every Depends-on-DOS object / invariant must resolve in dos.yaml; else reject + force_track: psl
  - --require-dos: 没有 --dos 时不再只出一条 flag。**未检不是通过** —— 「闭包失败 = 客观触发
    PSL 轨」这条判据的全部力量来自闭包真的被算过；没有本体时它退化成自评，而自信而错的人
    正是靠自评绕开 G1 的。给了这个 flag 就先在项目目录里自动找 dos.yaml
    （ai-dlc/scripts/repo_assets.py：仓库根 / docs/ / ontology/），找不到才 reject。
Semantic half (FLAGGED as needs_semantic_review): threshold source traces to KPI/SLO/failure; the unhappy
twin covers the RIGHT edge; these ACs are the narrowest falsifiable conditions for THIS run.
"""
import argparse
import json
import os
import pathlib
import re
import sys

# DOS closure means the same thing here and in lint_cards.py: one resolver, owned by
# dos-extract (the skill that writes dos.yaml). See dos-extract/scripts/dos_closure.py.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "dos-extract" / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "ai-dlc" / "scripts"))
try:
    import dos_closure
except ImportError:  # a neighbour skill may be absent; that is not this script's failure
    # Cross-skill code is an OPTIONAL dependency: this script belongs to its own skill and must run
    # when a neighbour is missing. Hard-exiting at import time killed runs that never passed --dos
    # (PR pre-review, B-tier). Absent, closure checking degrades to a flag where it is asked for.
    dos_closure = None
try:
    import repo_assets   # X1 仓库级制品的发现（与 doctor / prereqs 同一份候选路径表）
except Exception:
    repo_assets = None

VAGUE = ["快", "慢", "稳定", "可靠", "健壮", "高效", "及时", "尽快", "尽量", "大部分", "多数", "合理",
         "友好", "流畅", "顺畅", "良好", "充分", "适当", "足够", "正确处理", "智能",
         "fast", "slow", "stable", "reliable", "robust", "quick", "soon", "most", "reasonable",
         "friendly", "smooth", "adequate", "sufficient", "better", "properly", "correctly", "intelligently"]
BOUNDARY_RE = re.compile(r"^(route|cli|ui|db_field|event|api|topic|queue):", re.I)
FILEPATH_RE = re.compile(r"(\bsrc/|\btests?/|\.(ts|tsx|js|jsx|py|go|rs|java|kt|rb|php|cs|swift|vue)\b|::|\(\))")
SECRET_RE = re.compile(r"(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[baprs]-[A-Za-z0-9-]{10,})")
JUDGES = {"product", "design", "tech"}
EVIDENCE = {"checklist", "demo"}
LAYERS = {"card", "plan", "task", "ontology", "world"}


def sections(md):
    out, cur, buf = {}, None, []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = m.group(1).strip().lower(), []
        else:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def yaml_block(text):
    m = re.search(r"```ya?ml\s*\n(.*?)```", text, re.S)
    return m.group(1) if m else None


def kv_lines(text):
    d = {}
    for line in text.splitlines():
        m = re.match(r"^\s*[-*]?\s*([a-z_]+)\s*:\s*(.*?)\s*$", line, re.I)
        if m:
            d[m.group(1).lower()] = m.group(2)
    return d


def is_vague(s):
    s = str(s)
    if re.search(r"\d", s):
        return None
    low = s.lower()
    for w in VAGUE:
        if w in low:
            return w
    return None



# —— territory_invariants：已冻结的常驻不变量（不变量卡），不是 DOS 规则 ——
#
# dogfood 2026-09-21（vana）：一条 issue 声明自己受 INV-vana-003 / 004 约束，没有地方可写。
# 塞进 `invariants:` 会被当成 DOS 规则去闭包，于是报「world not built for these」——
# 而它们不是没建，是在**另一份、更权威的**制品里（人签 + 哈希锁死的不变量卡）。
# 一条把已生效的法报成「世界没建」的判据，会把人推向去改 DOS，而那儿本来就不该有它们。
#
# 声明必须被检查，否则就是装饰：卡找得到就逐个核对 id；卡找不到是**未检**，不是通过。
def card_invariant_ids(root):
    """→ (ids, sources)。扫 invariants/ 下每张卡的 hard_invariants / overridable_defaults。"""
    ids, sources = set(), []
    try:
        import repo_assets
    except ImportError:
        return None, []
    try:
        # find(key, root=...) —— 曾写成 find(root, "invariants")，两个位置参数正好调了个个儿：
        # key 收到目录、root 收到字面量 "invariants"。这条腿从来没命中过，于是只剩下面的兜底候选，
        # 而兜底是相对 root 拼的——`--card-root docs/invariants` 这个最自然的取值恰好全部落空，
        # 闸就安静地退化成「未检」。一个最自然的取值会关掉的闸，等于没有闸。
        hit = repo_assets.find("invariants", root=root) if hasattr(repo_assets, "find") else None
    except Exception:
        hit = None
    # root 本身就是卡所在目录（`--card-root docs/invariants`）也要认——帮助文本写的是
    # 「在哪里找不变量卡」，照字面给的人不该拿到一条静默的 flag。
    cand = [hit] if hit else []
    cand += [root] + [os.path.join(root, d) for d in ("invariants", "docs/invariants", ".aidlc/invariants")]
    for d in cand:
        if not d or not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith((".yaml", ".yml")):
                continue
            try:
                import yaml as _yaml
                with open(os.path.join(d, fn), encoding="utf-8") as f:
                    card = _yaml.safe_load(f) or {}
            except Exception:
                continue
            if not isinstance(card, dict):
                continue
            found = False
            for key in ("hard_invariants", "overridable_defaults"):
                for e in (card.get(key) or []):
                    if isinstance(e, dict) and e.get("id"):
                        ids.add(str(e["id"])); found = True
            if found:
                sources.append(os.path.join(d, fn))
        if sources:
            break
    return (ids if sources else None), sources

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("body"); ap.add_argument("--dos"); ap.add_argument("--kind", choices=["feature", "bug", "escape"], default="feature")
    ap.add_argument("--require-dos", dest="require_dos", action="store_true",
                    help="把「闭包未检」从 flag 升成 reject；没给 --dos 时先自动发现 dos.yaml")
    ap.add_argument("--dos-scope", dest="dos_scope", help="monorepo：先在这个目录里找 dos.yaml（如 plugins/ai-dlc），找不到再回落到仓库根")
    ap.add_argument("--card-root", dest="card_root",
                    help="在哪里找不变量卡（默认当前工作目录）。territory_invariants 的 id 要在卡里真的存在")
    ap.add_argument("--g1", help="G1 record; on the PSL track the issue text is checked against the negations it writes down (dogfood I-45)")
    a = ap.parse_args()
    dos_source = "given" if a.dos else None
    if a.require_dos and not a.dos and repo_assets is not None:
        found = repo_assets.find("dos", scope=a.dos_scope)
        if found:
            a.dos, dos_source = found, "discovered"
    try:
        md = open(a.body, encoding="utf-8").read()
    except OSError as e:
        sys.stderr.write(f"verify_issue: {e}\n"); sys.exit(2)
    rejects, flags = [], []
    secs = sections(md)
    need = ["intent", "track", "scope", "acceptance", "assumptions", "depends on dos"]
    for s in need:
        if s not in secs:
            rejects.append(f"section missing: ## {s.title()}")
    if SECRET_RE.search(md):
        rejects.append("secret-looking token in body — remove it")

    # Track
    track = None
    if "track" in secs:
        track = kv_lines(secs["track"]).get("track", "").strip().lower()
        if track not in ("psl", "task"):
            rejects.append("Track: `track:` must be psl|task")
    # Scope
    if "scope" in secs:
        kv = kv_lines(secs["scope"])
        for k in ("do", "dont", "hard_constraints", "success_metric"):
            v = kv.get(k, "").strip()
            if not v or v.startswith("<"):
                rejects.append(f"Scope: `{k}` empty (范围四项非空)")
        if kv.get("success_metric") and not re.search(r"\d", kv.get("success_metric", "")):
            flags.append("Scope.success_metric has no number — is it measurable?")

    # Acceptance
    stats = {"total": 0, "mechanical": 0, "human": 0, "unwanted": 0}
    acs = []
    if "acceptance" in secs:
        yb = yaml_block(secs["acceptance"])
        if not yb:
            rejects.append("Acceptance: no fenced ```yaml block")
        else:
            try:
                import yaml
                doc = yaml.safe_load(yb) or {}
            except ImportError:
                doc, flags = {}, flags + ["PyYAML missing — acceptance block parsed loosely; install pyyaml for the full check"]
                doc = {"acceptance": [], "_loose": True}
            except Exception as e:
                rejects.append(f"Acceptance: yaml parse error: {e}"); doc = {}
            acs = doc.get("acceptance") or []
            if not doc.get("_loose") and not acs:
                rejects.append("Acceptance: `acceptance:` list empty")
            ids = set()
            for ac in acs:
                if not isinstance(ac, dict):
                    rejects.append(f"Acceptance: non-mapping entry {ac!r}"); continue
                stats["total"] += 1
                aid, req, kind = ac.get("id"), ac.get("req"), ac.get("kind")
                if not aid:
                    rejects.append("AC without id"); continue
                if aid in ids:
                    rejects.append(f"{aid}: duplicate id")
                ids.add(aid)
                if not req:
                    rejects.append(f"{aid}: no req")
                if kind not in ("mechanical", "human"):
                    rejects.append(f"{aid}: kind must be mechanical|human"); continue
                stats[kind] += 1
                obs = str(ac.get("observe") or "")
                if kind == "mechanical":
                    for k in ("observe", "given", "expect"):
                        if ac.get(k) in (None, "", {}):
                            rejects.append(f"{aid}: mechanical AC needs `{k}`")
                    if obs and not BOUNDARY_RE.match(obs):
                        rejects.append(f"{aid}: observe `{obs}` is not a boundary (route:/cli:/ui:/db_field:/event:)")
                    if obs and FILEPATH_RE.search(obs):
                        rejects.append(f"{aid}: observe names implementation structure (file/function) — contract must not")
                    w = is_vague(json.dumps(ac.get("expect"), ensure_ascii=False))
                    if w:
                        rejects.append(f"{aid}: expect contains vague `{w}` with no numeric threshold")
                else:
                    if not ac.get("statement"):
                        rejects.append(f"{aid}: human AC needs `statement`")
                    if ac.get("judge") not in JUDGES:
                        rejects.append(f"{aid}: judge must be one of {sorted(JUDGES)}")
                    if ac.get("evidence") not in EVIDENCE:
                        rejects.append(f"{aid}: evidence must be one of {sorted(EVIDENCE)}")
                    w = is_vague(ac.get("statement") or "")
                    if w:
                        flags.append(f"{aid}: human statement uses `{w}` — fine for a human judge, but name the checklist item")
                if ac.get("ears_type") == "unwanted":
                    stats["unwanted"] += 1
            # twin check
            #
            # Three ways a happy AC can have a twin, and the twin must really BE one:
            #   ① an `unwanted` AC shares its observe;
            #   ② this AC's `paired_with` points at an `unwanted` AC;
            #   ③ an `unwanted` AC points back at this one — the placement the template
            #      itself demonstrates (`paired_with` on the unwanted half).
            #
            # ③ used to be missing, so a body written the way the template shows, with the
            # two halves on different observes, was rejected for "no unhappy twin" while
            # carrying the pairing it was asked for (dogfood 2026-09-21, vana).
            #
            # ② used to be `ac.get("paired_with") in ids` — any existing id satisfied it,
            # including another HAPPY AC. Two happy ACs pointing at each other both passed
            # and neither edge was covered: a fence you climb by naming it. The twin must
            # carry `ears_type: unwanted`, and pointing at something that is not one is
            # reported as that, not as a generic "no twin".
            by_obs, by_id = {}, {}
            for ac in acs:
                if isinstance(ac, dict):
                    by_obs.setdefault(str(ac.get("observe")), []).append(ac)
                    if ac.get("id"):
                        by_id[ac.get("id")] = ac

            def _unwanted(x):
                return isinstance(x, dict) and x.get("ears_type") == "unwanted"

            # 悬空引用先报，不管它写在哪一半。打错孪生 id 时，人以为自己声明了配对、
            # 其实没有，而且没有任何声音——本条恰好能过门只是因为两半的 observe 碰巧相同。
            for ac in acs:
                if not isinstance(ac, dict):
                    continue
                pw = ac.get("paired_with")
                if pw and pw not in by_id:
                    rejects.append(f"{ac.get('id')}: `paired_with: {pw}` names no AC in this body")

            for ac in acs:
                if not isinstance(ac, dict) or ac.get("kind") != "mechanical":
                    continue
                et = ac.get("ears_type", "event")
                if et in ("event", "state"):
                    aid = ac.get("id")
                    sib = [x for x in by_obs.get(str(ac.get("observe")), []) if x is not ac and _unwanted(x)]
                    pw = ac.get("paired_with")
                    fwd = _unwanted(by_id.get(pw))
                    back = any(_unwanted(x) and x.get("paired_with") == aid for x in acs)
                    if not sib and not fwd and not back:
                        if pw and pw in by_id:
                            rejects.append(f"{aid}: `paired_with: {pw}` points at an AC that is not `ears_type: unwanted` "
                                           "— a twin has to be the unhappy half, not another happy AC")
                        else:
                            rejects.append(f"{aid}: happy AC has no unhappy twin (add an `unwanted` AC on the same observe, "
                                           "or `paired_with` between the two halves — either direction)")
            for ex in doc.get("existence") or []:
                s = json.dumps(ex, ensure_ascii=False)
                if FILEPATH_RE.search(s) or "file:" in s or "function:" in s:
                    rejects.append(f"existence entry names implementation structure: {s}")
            ts = doc.get("threshold_source")
            if doc.get("thresholds") and (not ts or "needs_threshold_source" in str(ts)):
                flags.append("thresholds present but threshold_source missing/needs — numbers from air are not criteria (needs_semantic_review)")

    # kind-specific
    if a.kind == "bug":
        if "repro" not in secs:
            rejects.append("bug: section missing: ## Repro")
        else:
            r = secs["repro"]
            if not re.search(r"^\s*1[.)]\s+\S", r, re.M):
                rejects.append("bug: Repro needs ≥1 numbered step")
            kv = kv_lines(r)
            for k in ("expected", "actual"):
                if not kv.get(k) or kv[k].startswith("<"):
                    rejects.append(f"bug: Repro.{k} empty")
    if a.kind == "escape":
        if "attribution" not in secs:
            rejects.append("escape: section missing: ## Attribution")
        else:
            kv = kv_lines(secs["attribution"])
            if kv.get("layer", "").strip() not in LAYERS:
                rejects.append(f"escape: Attribution.layer must be one of {sorted(LAYERS)}")
            if not kv.get("why_gate_missed") or kv["why_gate_missed"].startswith("<"):
                rejects.append("escape: Attribution.why_gate_missed empty")

    # DOS closure
    force_track, missing_terms = None, []
    if "depends on dos" in secs:
        kv = kv_lines(secs["depends on dos"])
        objs = [t.strip() for t in re.sub(r"[\[\]]", "", kv.get("objects", "")).split(",") if t.strip() and t.strip().lower() != "none"]
        invs = [t.strip() for t in re.sub(r"[\[\]]", "", kv.get("invariants", "")).split(",") if t.strip() and t.strip().lower() != "none"]
        terr = [t.strip() for t in re.sub(r"[\[\]]", "", kv.get("territory_invariants", "")).split(",") if t.strip() and t.strip().lower() != "none"]
        # 常驻不变量不走 DOS 闭包——它们的家是不变量卡，不是 dos.yaml
        if terr:
            known, srcs = card_invariant_ids(a.card_root or os.getcwd())
            if known is None:
                flags.append(f"territory_invariants {terr} declared but no invariant card found — "
                             "unchecked, not passed. Run /invariant-extract and commit invariants/ to git.")
            else:
                unknown = [t for t in terr if t not in known]
                if unknown:
                    rejects.append(f"territory_invariants {unknown} are in no invariant card ({', '.join(srcs)}) — "
                                   "a frozen invariant this issue claims to obey has to exist")
        if not kv.get("objects"):
            rejects.append("Depends on DOS: `objects:` line missing (write `none` if truly none)")
        if a.dos:
            try:
                if dos_closure is None:
                    flags.append("--dos given but dos-extract/scripts/dos_closure.py is not reachable — "
                                 "closure unchecked; install the neighbour skill or drop --dos")
                    closure = None
                else:
                    closure = dos_closure.load_closure(a.dos)
            except Exception as e:
                sys.stderr.write(f"verify_issue: cannot read dos: {e}\n"); sys.exit(2)
            # A term recorded as an object `synonyms:` / rule `aliases:` entry closes: the
            # DOS's canonical key and the team's word are the same thing (dogfood I-15).
            missing_terms = closure.unresolved(objs, "object") + closure.unresolved(invs, "rule")
            for t in objs:
                if getattr(closure, "via_rejected", lambda x: False)(t):
                    # closes, but the DOS lists the word as REJECTED — the issue speaks a name the team
                    # decided against; a flag here (not a reject: the issue is upstream of the contract)
                    flags.append(f"DOS closure: `{t}` is a rejected name — the DOS says `{closure.resolve_object(t)}`")
                elif closure.via_synonym(t, "object"):
                    flags.append(f"DOS closure: `{t}` closes as a synonym of `{closure.resolve_object(t)}`")
            for t in invs:
                if closure.via_synonym(t, "rule"):
                    flags.append(f"DOS closure: `{t}` closes as an alias of `{closure.resolve_rule(t)}`")
            if missing_terms:
                whys = {t: closure.why_unresolved(t) for t in missing_terms} if hasattr(closure, "why_unresolved") else {}
                amb = [f"{t} ({w})" for t, w in whys.items() if w.startswith("ambiguous")]
                rejects.append(f"DOS closure failed: {missing_terms} not in {a.dos} — world not built for these; force PSL track"
                               + (f"; homonyms to qualify: {amb}" if amb else ""))
                force_track = "psl"
        elif a.require_dos:
            rejects.append(
                "DOS closure unchecked and --require-dos is set: no dos.yaml given or found in the project "
                "(ai-dlc/scripts/repo_assets.py searches the repo root, docs/, ontology/). "
                "「闭包失败 = 客观触发 PSL 轨」只有在闭包真的被算过时才成立——未检不是通过。"
                "Run /dos-extract, commit dos.yaml to git (the team shares one), or drop --require-dos.")
        elif objs or invs:
            flags.append("Depends on DOS declared but no --dos given — closure unchecked")
    if track == "psl":
        # the template writes `- PSL: <p>　G1: <p>　related: <n>` on ONE line, so kv_lines() sees a single `psl` key;
        # pull the three keys out with a regex instead (dogfood 2026-09-05, I-07)
        links_text = secs.get("links", "")
        links = {m.group(1).lower(): m.group(2) for m in re.finditer(r"\b(PSL|G1|related)\s*:\s*([^\s　]+)", links_text)}
        if not links.get("g1") or links["g1"].strip().lower() in ("none", "<path", "<path 或 none>"):
            flags.append("PSL track without a G1 record path in Links — the issue should be created after G1")
        elif a.g1 or os.path.isfile(links["g1"]):
            # The issue restates the signed form in prose, and prose drifts. Three rounds of this run's
            # G1 each caught the issue body using a word the signed form had explicitly rejected — a
            # unit of judgement the form ruled out, or an inference the form ruled invalid. Nothing
            # mechanical was watching, so a human read it three times. Now the negations the G1 record
            # writes down are checked against the text that quotes them (dogfood I-45).
            g1_path = a.g1 or links["g1"]
            # Interpretations issued AFTER the signature live in their own file, because the g2 lock
            # freezes the record and an interpretation changes no signed byte (I-60). A refusal is a
            # refusal whichever of the two it landed in, so read both.
            sources = [g1_path]
            interp = os.path.join(os.path.dirname(g1_path) or ".", "g1-interpretations.md")
            if os.path.isfile(interp):
                sources.append(interp)
            g1_text = ""
            for src in sources:
                try:
                    g1_text += open(src, encoding="utf-8").read() + "\n"
                except OSError as e:
                    flags.append(f"G1 record {src} named but unreadable ({e}) — cross-check incomplete")
            # The negation list must be MECHANICAL. This run's G1 wrote its refusals in prose
            # ("AC-004-b used the rejected word …") and a human had to catch the drift three times.
            # A checker cannot parse prose reliably, so the g1_record template carries a dedicated
            # section and this reads exactly that: one term per list item, nothing inferred.
            banned, in_sec = [], False
            for line in g1_text.splitlines():
                if line.startswith("#"):
                    in_sec = bool(re.search(r"(明确不做|不做的事|否决词表|explicitly not doing|rejected terms)", line, re.I))
                    continue
                if in_sec:
                    m = re.match(r"^\s*[-*]\s+(?:\*\*)?`?([^`*\n]+?)`?(?:\*\*)?\s*(?:—|--|:|：).*$|^\s*[-*]\s+(?:\*\*)?`?([^`*\n]+?)`?(?:\*\*)?\s*$", line)
                    if m:
                        t = (m.group(1) or m.group(2) or "").strip()
                        if len(t) >= 2:
                            banned.append(t)
            if not banned:
                flags.append(f"G1 record{'s' if len(sources) > 1 else ''} {', '.join(sources)} has no machine-readable 「明确不做」 section — the "
                             "issue's wording cannot be checked against what the signed form refused")
            # 扫的是 issue **主张**什么，不是它**否掉**什么。
            # Scope 的 `dont:` 那一行里出现一个被 G1 否决的词，是这份 issue 在**同意**那条否决——
            # 它正该写在那里。把同意报成冲突，会让一份写对的 issue 触发一串 flag，
            # 而一串永远会响的 flag 等于没有 flag（dogfood 2026-09-21：六条全是 dont 里的引用）。
            scope_text = "\n".join(l for l in secs.get("scope", "").splitlines()
                                   if not re.match(r"\s*[-*]\s*dont\s*:", l))
            watched = "\n".join([secs.get(k, "") for k in ("assumptions", "acceptance", "intent")] + [scope_text])
            for term in dict.fromkeys(banned):
                if term and term in watched:
                    flags.append(f"issue text uses `{term}`, which the G1 record lists under 明确不做 "
                                 f"({' + '.join(sources)}) — restate it in the signed form's own words or reopen G1")
    flags.append("needs_semantic_review: are these ACs the narrowest falsifiable conditions for THIS run? does the unhappy twin cover the right edge?")

    out = {"verdict": "REJECT" if rejects else "PASS", "track": track, "force_track": force_track,
           "dos": a.dos, "dos_source": dos_source, "missing_dos_terms": missing_terms, "acceptance_stats": stats, "rejects": rejects, "flags": flags,
           "sections": sorted(secs)}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
