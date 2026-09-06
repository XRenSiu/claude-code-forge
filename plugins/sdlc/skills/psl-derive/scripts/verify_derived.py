#!/usr/bin/env python3
"""
verify_derived.py — the mechanical pre-gate for psl-derive: checks the PRODUCT (a derived/ directory)
against "what G1-ready derivation products look like", and FLAGS (never decides) the semantic half.

Usage:
  verify_derived.py <derived_dir> --psl <PSL-<name>.md> [--n 3] [--round 1]
                    [--verify-dos <path to verify_dos.py>]

Exit 0 = no rejects (flags may remain) · 1 = ≥1 REJECT · 2 = IO/usage error.

Mechanical guarantees (REJECT — non-waivable half):
  - four files present: dos-proposal.yaml, workflow.md, form-draft.md, divergence.md
  - every form-draft decision line `- [F-nn] … ← <anchor>` carries ≥1 anchor and every cited anchor exists in
    the PSL. Legal anchors: `PSL-NNN` (rule index) and `UI-n` / `A-n` / `DP-n` (UI Contract / Acceptance /
    Design Principles). Those three layers are load-bearing too — refusing them forced derivations to borrow
    the nearest rule and produced decorative citations (dogfood 2026-09-05, I-19).
  - workflow.md has no named steps (Step N / 步骤 N / 第 N 步 / 阶段 N); ≥3 sequence words → flag. Blockquotes
    are stripped ONLY in the leading preamble (the template's own guidance quotes the banned tokens); a
    procedure written behind `> ` further down is still a procedure (I-04 over-corrected, fixed per I-77).
  - dos-proposal.yaml passes dos-extract's verify_dos.py (≤7 objects, declared refs, no UI/impl suffix,
    open_questions non-empty) — found at ../../dos-extract/scripts/verify_dos.py unless --verify-dos
  - dos-proposal objects ⊆ PSL Domain-Model vocabulary ∪ divergence "PSL 欠定" candidates (no invented entities)
  - divergence.md declares n; when n>1 the table has ≥1 row or an explicit "no divergence" statement; rows carry
    an agenda cell
  - `--round N` (N ≥ 2, a targeted re-derivation after a G1 ruling): the previous round must be archived at
    `round<N-1>/` with all four files, `round-diff.md` must exist and cite that archive, and divergence.md must
    declare `round: N` and carry a 裁决 → 落点 table instead of the first-round D-table (I-21 / I-32 / I-35 / I-44).

Semantic half (FLAGGED needs_semantic_review): is the form right? which divergence branch is correct? should
the PSL change? — that is G1, a human. Three of those flags are shape hints for G1's agenda: a form-layer rule
nobody cited, a decision that states a computable predicate without a worked example (I-56 / I-58), and a
decision that claims something about a data file's structure without a line-level locator (I-36).
"""
import argparse
import json
import os
import re
import subprocess
import sys

STEP_RE = re.compile(r"(\bStep\s*\d+\b|步骤\s*[一二三四五六七八九十\d]+|第\s*[一二三四五六七八九十\d]+\s*步|阶段\s*[一二三四五六七八九十\d]+|\bPhase\s*\d+\b)", re.I)
SEQ_WORDS = ["首先", "然后", "接着", "最后", "其次", "再", "之后"]
DECISION_RE = re.compile(r"^\s*-\s*\[F-\d+\]\s*(?P<body>.+?)\s*(?:←|<-)\s*(?P<refs>.*)$")
PSL_ID_RE = re.compile(r"\bPSL-\d{3,}\b")

# --- anchors ------------------------------------------------------------------------------------
# A PSL law definition line, optionally carrying a layer marker right after the id (I-20). Rules that
# constrain CONTENT rather than FORM are not supposed to show up in a form draft, so the "never cited"
# flag must not treat them as omissions.
LAW_DEF_RE = re.compile(r"^\s*(?:[-*+]\s+|\|\s*|\d+[.、)]\s+)?(?:\[[^\]]*\]\s*)*(PSL-\d{3,})\b")
LAYER_RE = re.compile(r"[（(]\s*(内容层|形态层|content|form)\s*[)）]|\[\s*layer\s*[:：]\s*(content|form|内容|形态)\s*\]", re.I)
CONTENT_LAYER = {"内容层", "content", "内容"}
# UI Contract / Acceptance / Design Principles items: `- UI-1 …`, `- A1 问…`, `- DP-3 …`
LAYER_ANCHOR_DEF_RE = re.compile(r"^\s*(?:[-*+]\s+|\|\s*)?(?:\*\*)?((?:UI|DP|A)-?\d+)\b")
LAYER_ANCHOR_CITE_RE = re.compile(r"\b(UI|DP|A)\s*-?\s*(\d+)\b")
# `(via UI-1, A7)` — the pre-I-19 workaround; still validated so old drafts keep their guarantee
VIA_RE = re.compile(r"[（(]\s*via\s*([^）)]*)[)）]", re.I)

# --- G1 agenda hints ----------------------------------------------------------------------------
# A decision that states a computable predicate must show it computed once on a concrete case — the L5
# author discovering the predicate is under-specified while encoding fixtures is a round too late (I-56).
PREDICATE_RE = re.compile(r"当且仅当|\biff\b|∧|∨|⇔|缺一不算|缺一不可|\bexit\s*[01]\b|若[^，。；]{1,40}则|如果[^，。；]{1,40}则", re.I)
EXAMPLE_RE = re.compile(r"例[：:]|例如|举例|worked example|\be\.g\.|比如")
# A decision that asserts the SHAPE of a data file needs a line-level locator for that claim (I-36)
DATA_FILE_RE = re.compile(r"\b[\w.\-/]+\.(?:ya?ml|json)\b")
STRUCT_CLAIM_RE = re.compile(r"节点|边\b|handled_by|conditional|顶层键|顶层|字段|键\b|schema|Node\.")
LOCATOR_RE = re.compile(r"\bL\s*\d+|第\s*\d+\s*行|#L\d+|§\s*[\d.]+|\bline\s*\d+", re.I)
# The 实体与数据形态 section has to say where each record type lands (I-58)
ENTITY_SECTION_RE = re.compile(r"^##+\s*.*(实体与数据形态|entity and data shape).*$", re.I | re.M)
LANDING_RE = re.compile(r"落位|lands?[_ ]in|落在\s*`|顶层键|top-level key")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def canon_anchor(text):
    """`UI-1` / `UI 1` / `A5` → `UI1` / `A5`, so a citation and its definition compare equal."""
    return re.sub(r"[\s-]", "", text).upper()


def psl_law_layers(psl_text):
    """{PSL-NNN: 'form'|'content'} from the law definition lines. Unmarked = form (I-20)."""
    layers = {}
    for line in psl_text.splitlines():
        m = LAW_DEF_RE.match(line)
        if not m:
            continue
        tail = line[m.end(1):m.end(1) + 40]
        lm = LAYER_RE.search(tail)
        marker = (lm.group(1) or lm.group(2)).lower() if lm else None
        layers.setdefault(m.group(1), "content" if marker in CONTENT_LAYER else "form")
    return layers


def psl_layer_anchors(psl_text):
    """{canonical anchor: as written} for UI Contract / Acceptance / Design Principles items (I-19)."""
    out = {}
    for line in psl_text.splitlines():
        m = LAYER_ANCHOR_DEF_RE.match(line)
        if m:
            out.setdefault(canon_anchor(m.group(1)), m.group(1))
    return out


def strip_leading_guidance(text):
    """Drop blockquotes in the LEADING PREAMBLE only.

    The workflow template opens with `> 禁止 Step 1/2/3 …`, which quotes the very tokens the scan bans
    (I-04). Filtering every blockquote in the file — the first fix — meant a workflow written entirely
    behind `> ` scanned clean, blinding the skill's only mechanical "write Σ/φ, not a procedure" check
    (I-77). So the strip stops at the first line that is neither blank, a heading, nor a blockquote.
    """
    out, in_preamble, seen_heading = [], True, False
    for line in text.splitlines():
        stripped = line.lstrip()
        if in_preamble:
            if stripped.startswith(">"):
                continue                      # 模板自带的引导语
            if stripped == "":
                out.append(line)
                continue
            if stripped.startswith("#") and not seen_heading:
                seen_heading = True           # 只有开篇那个标题算前言的一部分
                out.append(line)
                continue
            in_preamble = False
        out.append(line)
    return "\n".join(out)


def psl_ids_and_vocab(psl_text):
    ids = set(PSL_ID_RE.findall(psl_text))
    # Domain Model vocabulary: capitalised identifiers / backticked names inside the Domain Model section
    # heading part must stay on one line ([^\n]) — under re.S a greedy `.*` would run to the LAST mention of
    # "Domain Model" anywhere in the file and leave an empty body (found by dogfood 2026-09-05, I-05)
    m = re.search(r"^#{1,3}[^\n]*(domain\s*model|领域模型)[^\n]*$\n(.*?)(?=^#{1,3}\s|\Z)", psl_text, re.S | re.M | re.I)
    body = m.group(2) if m else psl_text
    vocab = set(re.findall(r"`([A-Za-z][A-Za-z0-9_]{1,40})`", body)) | set(re.findall(r"\b([A-Z][a-zA-Z0-9]{2,40})\b", body))
    return ids, vocab


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("derived_dir"); ap.add_argument("--psl", required=True); ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--round", type=int, default=1, dest="round_no",
                    help="derivation round; ≥2 means a targeted re-derivation after a G1 ruling (I-21)")
    ap.add_argument("--verify-dos")
    a = ap.parse_args()
    if a.round_no < 1:
        sys.stderr.write("verify_derived: --round must be ≥ 1\n"); sys.exit(2)
    rejects, flags = [], []
    d = a.derived_dir
    files = {k: os.path.join(d, k) for k in ("dos-proposal.yaml", "workflow.md", "form-draft.md", "divergence.md")}
    for k, p in files.items():
        if not os.path.isfile(p):
            rejects.append(f"missing {k}")
    if not os.path.isfile(a.psl):
        sys.stderr.write(f"verify_derived: PSL not found: {a.psl}\n"); sys.exit(2)
    psl = read(a.psl)
    ids, vocab = psl_ids_and_vocab(psl)
    layers = psl_law_layers(psl)
    layer_anchors = psl_layer_anchors(psl)
    if not ids:
        rejects.append("PSL carries no PSL-NNN rule ids — decisions cannot cite rules (U1: every rule needs an id)")

    # form-draft
    decisions, cited = 0, set()
    cited_layer, no_example, no_locator = set(), [], []
    if os.path.isfile(files["form-draft.md"]):
        fd_text = read(files["form-draft.md"])
        for line in fd_text.splitlines():
            if re.match(r"^\s*-\s*\[F-", line) and not re.match(r"^\s*-\s*\[F-\d+\]", line):
                # a decision-looking line whose id the verifier cannot parse (e.g. F-13a) would otherwise be skipped
                # silently — uncounted and its citation unchecked (dogfood 2026-09-05, I-47)
                rejects.append(f"form-draft decision id not F-<digits>: {line.strip()[:60]} — suffixed ids bypass the pre-gate")
                continue
            if not re.match(r"^\s*-\s*\[F-\d+\]", line):
                continue
            decisions += 1
            fid = re.match(r"^\s*-\s*(\[F-\d+\])", line).group(1)
            m = DECISION_RE.match(line)
            refs = set(PSL_ID_RE.findall(m.group("refs"))) if m else set()
            # UI Contract / Acceptance / Design Principles anchors are first-class citations (I-19); the
            # pre-I-19 `(via UI-1)` parenthetical is validated too so existing drafts keep their guarantee.
            anchor_src = (m.group("refs") if m else "") + " " + " ".join(VIA_RE.findall(line))
            anchors = {canon_anchor(f"{k}{v}") for k, v in LAYER_ANCHOR_CITE_RE.findall(anchor_src)}
            if not refs and not anchors:
                rejects.append(f"form-draft decision without an anchor (PSL-NNN / UI-n / A-n / DP-n): {line.strip()[:70]}")
            for r in refs:
                cited.add(r)
                if r not in ids:
                    rejects.append(f"form-draft cites {r} which does not exist in the PSL")
            for anc in anchors:
                cited_layer.add(anc)
                if anc not in layer_anchors:
                    rejects.append(f"form-draft {fid} cites {anc} which is not an item of the PSL's "
                                   f"UI Contract / Acceptance / Design Principles")
            if PREDICATE_RE.search(line) and not EXAMPLE_RE.search(line):
                no_example.append(fid)
            if DATA_FILE_RE.search(line) and STRUCT_CLAIM_RE.search(line) and not LOCATOR_RE.search(line):
                no_locator.append(fid)
        if decisions == 0:
            rejects.append("form-draft.md has no `- [F-nn] … ← PSL-xxx` decisions")
        # every record type has to say where it lands, or L5 discovers the data shape while writing fixtures (I-58)
        em = ENTITY_SECTION_RE.search(fd_text)
        if em:
            nxt = re.search(r"^##+\s", fd_text[em.end():], re.M)
            body = fd_text[em.end(): em.end() + (nxt.start() if nxt else len(fd_text))]
            if not LANDING_RE.search(body):
                flags.append("form-draft 「实体与数据形态」节没有任何落位说明（每种记录类型落在哪个顶层键、"
                             "被谁怎么引用）——下游写 fixture 时才发现形状欠定就晚了 (needs_semantic_review, I-58)")
        if no_example:
            flags.append(f"form-draft decisions state a computable predicate with no worked example: {no_example[:6]}"
                         f"{'…' if len(no_example) > 6 else ''} — G1 第四问：这条谓词能对一份最小样例算出来吗？"
                         f" (needs_semantic_review, I-56)")
        if no_locator:
            flags.append(f"form-draft decisions assert the shape of a data file without a line-level locator: "
                         f"{no_locator[:6]}{'…' if len(no_locator) > 6 else ''} — 引用数据文件结构的决策要带该文件的"
                         f"一行证据（`graph.yaml L29`），否则字面读法可能与数据不符 (needs_semantic_review, I-36)")

    # workflow
    if os.path.isfile(files["workflow.md"]):
        # only the LEADING preamble's blockquotes are template guidance; a procedure hidden behind `> `
        # further down is still a procedure (I-04 fixed too broadly, corrected per I-77)
        w = strip_leading_guidance(read(files["workflow.md"]))
        hits = STEP_RE.findall(w)
        if hits:
            rejects.append(f"workflow.md contains named steps: {sorted(set(hits))[:4]} — write Σ/φ, not a procedure")
        seq = sum(w.count(x) for x in SEQ_WORDS)
        if seq >= 3:
            flags.append(f"workflow.md has {seq} sequence words (首先/然后/接着/最后…) — pipeline in disguise? (needs_semantic_review)")

    # dos proposal
    dos_objs = set()
    if os.path.isfile(files["dos-proposal.yaml"]):
        vd = a.verify_dos or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dos-extract", "scripts", "verify_dos.py")
        if os.path.isfile(vd):
            r = subprocess.run([sys.executable, vd, files["dos-proposal.yaml"]], capture_output=True, text=True)
            if r.returncode != 0:
                rejects.append("dos-proposal.yaml rejected by verify_dos.py: " + (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[:200]))
        else:
            flags.append("verify_dos.py not found — dos-proposal schema unchecked")
        try:
            import yaml
            dp = yaml.safe_load(read(files["dos-proposal.yaml"])) or {}
            objs = dp.get("objects") or {}
            dos_objs = set(objs.keys()) if isinstance(objs, dict) else {o.get("name") for o in objs if isinstance(o, dict)}
        except Exception as e:
            rejects.append(f"dos-proposal.yaml unreadable: {e}")

    # divergence
    candidates = set()
    if os.path.isfile(files["divergence.md"]):
        dv = read(files["divergence.md"])
        m = re.search(r"^\s*n\s*:\s*(\d+)", dv, re.M)
        n = int(m.group(1)) if m else None
        if n is None:
            rejects.append("divergence.md must declare `n: <runs>`")
        elif n == 1 and "未做分歧检验" not in dv and "no divergence check" not in dv.lower():
            rejects.append("divergence.md n: 1 must state 未做分歧检验 (single-run derivation is legal but must be declared)")
        rows = [l for l in dv.splitlines() if re.match(r"^\|\s*D-\d+", l)]
        if n and n > 1 and not rows and not re.search(r"无分歧|no divergence", dv, re.I):
            rejects.append("divergence.md: n>1 but no D-rows and no explicit 无分歧 statement")
        for l in rows:
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if len(cells) < 7 or not cells[-1] or cells[-1].startswith("<"):
                rejects.append(f"divergence row without agenda: {l.strip()[:60]} "
                               f"— a `| D-n |` row needs 7 cells, the last one being the G1 agenda")

    # rounds: a targeted re-derivation is legal, but the round it replaces must stay reproducible.
    # Round 3 overwrote round 2 in place and only round1/ was archived, so round-diff's left-hand side
    # could not be recomputed by a third party (dogfood 2026-09-05, I-21 / I-32 / I-35 / I-44).
    if a.round_no >= 2:
        prev = os.path.join(d, f"round{a.round_no - 1}")
        missing = [k for k in ("dos-proposal.yaml", "workflow.md", "form-draft.md", "divergence.md")
                   if not os.path.isfile(os.path.join(prev, k))]
        if not os.path.isdir(prev):
            rejects.append(f"round {a.round_no}: previous round not archived at round{a.round_no - 1}/ — "
                           f"archive the four files before overwriting them, or the round it replaces is unreproducible")
        elif missing:
            rejects.append(f"round {a.round_no}: round{a.round_no - 1}/ is missing {missing} — the archive must carry all four files")
        diff_path = os.path.join(d, "round-diff.md")
        if not os.path.isfile(diff_path):
            rejects.append(f"round {a.round_no}: missing round-diff.md — a targeted re-derivation must show, "
                           f"decision by decision, that only the adjudicated points moved")
        else:
            rd = read(diff_path)
            if f"round{a.round_no - 1}" not in rd:
                rejects.append(f"round {a.round_no}: round-diff.md never references round{a.round_no - 1}/ — "
                               f"its left-hand side must name the archive a third party can recompute it from")
        if os.path.isfile(files["divergence.md"]):
            rm = re.search(r"^\s*round\s*:\s*(\d+)", dv, re.M)
            if not rm:
                rejects.append(f"round {a.round_no}: divergence.md must declare `round: {a.round_no}` — "
                               f"the derived/ directory has to say which round it holds")
            elif int(rm.group(1)) != a.round_no:
                rejects.append(f"round {a.round_no}: divergence.md declares round: {rm.group(1)} — mismatch")
            ruling = re.search(r"^#{2,3}[^\n]*(裁决[^\n]*落点|落点[^\n]*裁决|ruling[^\n]*landing)[^\n]*$", dv, re.M | re.I)
            if not ruling:
                rejects.append(f"round {a.round_no}: divergence.md has no 「裁决 → 落点」 table — from round 2 on "
                               f"the D-table is replaced by one row per G1 ruling and where it landed")
        sec = re.search(r"##\s*PSL\s*欠定(.*?)(?=^##|\Z)", dv, re.S | re.M)
        if sec:
            candidates = set(re.findall(r"`?([A-Z][a-zA-Z0-9]{2,40})`?\s*[—-]", sec.group(1)))
    invented = sorted(o for o in dos_objs if o not in vocab and o not in candidates)
    if invented:
        rejects.append(f"dos-proposal objects not in PSL Domain Model vocabulary nor declared as PSL 欠定 candidates: {invented}")
    # only FORM-layer rules are expected in a form draft; a rule that constrains CONTENT is legitimately
    # absent (I-20). And the flag has to say what G1 is supposed to do with it (I-06).
    uncited = sorted(i for i in (ids - cited) if layers.get(i, "form") == "form")
    skipped = sorted(i for i in (ids - cited) if layers.get(i, "form") == "content")
    if uncited and decisions:
        flags.append(f"form-layer PSL rules never cited by any decision: {uncited[:6]}{'…' if len(uncited) > 6 else ''}"
                     f" — decorative rules or missing decisions? → G1 议程：删规律或补决策 (needs_semantic_review)")
    if skipped:
        flags.append(f"content-layer rules not cited (expected, not an omission): {skipped}")
    flags.append("needs_semantic_review: is the form right? which divergence branch is correct? should the PSL change? — G1 (human)")
    out = {"verdict": "REJECT" if rejects else "PASS", "round": a.round_no, "decisions": decisions,
           "psl_ids": len(ids), "cited": len(cited), "layer_anchors": len(layer_anchors),
           "cited_layer_anchors": len(cited_layer), "dos_objects": sorted(dos_objs),
           "rejects": rejects, "flags": flags}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
