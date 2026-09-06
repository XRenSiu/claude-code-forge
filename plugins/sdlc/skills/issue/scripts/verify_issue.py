#!/usr/bin/env python3
"""
verify_issue.py — the mechanical pre-gate for /issue: checks the PRODUCT (an issue body) against
"what a falsifiable TASK seed looks like", and FLAGS (never decides) the semantic half.

Usage:
  verify_issue.py <issue-body.md> [--dos dos.yaml] [--kind feature|bug|escape]

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
Semantic half (FLAGGED as needs_semantic_review): threshold source traces to KPI/SLO/failure; the unhappy
twin covers the RIGHT edge; these ACs are the narrowest falsifiable conditions for THIS run.
"""
import argparse
import json
import os
import re
import sys

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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("body"); ap.add_argument("--dos"); ap.add_argument("--kind", choices=["feature", "bug", "escape"], default="feature")
    ap.add_argument("--g1", help="G1 record; on the PSL track the issue text is checked against the negations it writes down (dogfood I-45)")
    a = ap.parse_args()
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
            by_obs = {}
            for ac in acs:
                if isinstance(ac, dict):
                    by_obs.setdefault(str(ac.get("observe")), []).append(ac)
            for ac in acs:
                if not isinstance(ac, dict) or ac.get("kind") != "mechanical":
                    continue
                et = ac.get("ears_type", "event")
                if et in ("event", "state"):
                    sib = [x for x in by_obs.get(str(ac.get("observe")), []) if x is not ac and x.get("ears_type") == "unwanted"]
                    paired = ac.get("paired_with") in ids
                    if not sib and not paired:
                        rejects.append(f"{ac.get('id')}: happy AC has no unhappy twin (add an `unwanted` AC on the same observe or paired_with)")
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
        if not kv.get("objects"):
            rejects.append("Depends on DOS: `objects:` line missing (write `none` if truly none)")
        if a.dos:
            try:
                import yaml
                dos = yaml.safe_load(open(a.dos, encoding="utf-8")) or {}
            except Exception as e:
                sys.stderr.write(f"verify_issue: cannot read dos: {e}\n"); sys.exit(2)
            do = dos.get("objects") or {}
            names = set(do.keys()) if isinstance(do, dict) else {o.get("name") for o in do if isinstance(o, dict)}
            rules = dos.get("rules") or []
            rids = {r.get("id") for r in rules if isinstance(r, dict)} | {r for r in rules if isinstance(r, str)}
            missing_terms = [o for o in objs if o not in names] + [i for i in invs if i not in rids]
            if missing_terms:
                rejects.append(f"DOS closure failed: {missing_terms} not in {a.dos} — world not built for these; force PSL track")
                force_track = "psl"
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
            try:
                g1_text = open(g1_path, encoding="utf-8").read()
            except OSError as e:
                flags.append(f"G1 record named in Links but unreadable ({e}) — cross-check skipped")
                g1_text = ""
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
                flags.append(f"G1 record {g1_path} has no machine-readable 「明确不做」 section — the "
                             "issue's wording cannot be checked against what the signed form refused")
            watched = "\n".join(secs.get(k, "") for k in ("assumptions", "acceptance", "intent", "scope"))
            for term in dict.fromkeys(banned):
                if term and term in watched:
                    flags.append(f"issue text uses `{term}`, which the G1 record lists under 明确不做 "
                                 f"({g1_path}) — restate it in the signed form's own words or reopen G1")
    flags.append("needs_semantic_review: are these ACs the narrowest falsifiable conditions for THIS run? does the unhappy twin cover the right edge?")

    out = {"verdict": "REJECT" if rejects else "PASS", "track": track, "force_track": force_track,
           "missing_dos_terms": missing_terms, "acceptance_stats": stats, "rejects": rejects, "flags": flags,
           "sections": sorted(secs)}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
