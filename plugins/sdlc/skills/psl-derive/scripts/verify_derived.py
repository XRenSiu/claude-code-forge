#!/usr/bin/env python3
"""
verify_derived.py — the mechanical pre-gate for psl-derive: checks the PRODUCT (a derived/ directory)
against "what G1-ready derivation products look like", and FLAGS (never decides) the semantic half.

Usage:
  verify_derived.py <derived_dir> --psl <PSL-<name>.md> [--n 3] [--verify-dos <path to verify_dos.py>]

Exit 0 = no rejects (flags may remain) · 1 = ≥1 REJECT · 2 = IO/usage error.

Mechanical guarantees (REJECT — non-waivable half):
  - four files present: dos-proposal.yaml, workflow.md, form-draft.md, divergence.md
  - every form-draft decision line `- [F-nn] … ← PSL-xxx` carries ≥1 PSL-ID, and every cited ID exists in the PSL
  - workflow.md has no named steps (Step N / 步骤 N / 第 N 步 / 阶段 N); ≥3 sequence words → flag
  - dos-proposal.yaml passes dos-extract's verify_dos.py (≤7 objects, declared refs, no UI/impl suffix,
    open_questions non-empty) — found at ../../dos-extract/scripts/verify_dos.py unless --verify-dos
  - dos-proposal objects ⊆ PSL Domain-Model vocabulary ∪ divergence "PSL 欠定" candidates (no invented entities)
  - divergence.md declares n; when n>1 the table has ≥1 row or an explicit "no divergence" statement; rows carry
    an agenda cell
Semantic half (FLAGGED needs_semantic_review): is the form right? which divergence branch is correct? should
the PSL change? — that is G1, a human.
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


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def psl_ids_and_vocab(psl_text):
    ids = set(PSL_ID_RE.findall(psl_text))
    # Domain Model vocabulary: capitalised identifiers / backticked names inside the Domain Model section
    m = re.search(r"^#{1,3}\s*.*(domain\s*model|领域模型).*?$(.*?)(?=^#{1,3}\s|\Z)", psl_text, re.S | re.M | re.I)
    body = m.group(2) if m else psl_text
    vocab = set(re.findall(r"`([A-Za-z][A-Za-z0-9_]{1,40})`", body)) | set(re.findall(r"\b([A-Z][a-zA-Z0-9]{2,40})\b", body))
    return ids, vocab


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("derived_dir"); ap.add_argument("--psl", required=True); ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--verify-dos")
    a = ap.parse_args()
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
    if not ids:
        rejects.append("PSL carries no PSL-NNN rule ids — decisions cannot cite rules (U1: every rule needs an id)")

    # form-draft
    decisions, cited = 0, set()
    if os.path.isfile(files["form-draft.md"]):
        for line in read(files["form-draft.md"]).splitlines():
            if re.match(r"^\s*-\s*\[F-\d+\]", line):
                decisions += 1
                m = DECISION_RE.match(line)
                refs = set(PSL_ID_RE.findall(m.group("refs"))) if m else set()
                if not refs:
                    rejects.append(f"form-draft decision without PSL-ID: {line.strip()[:70]}")
                for r in refs:
                    cited.add(r)
                    if r not in ids:
                        rejects.append(f"form-draft cites {r} which does not exist in the PSL")
        if decisions == 0:
            rejects.append("form-draft.md has no `- [F-nn] … ← PSL-xxx` decisions")

    # workflow
    if os.path.isfile(files["workflow.md"]):
        w = read(files["workflow.md"])
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
                rejects.append(f"divergence row without agenda: {l.strip()[:60]}")
        sec = re.search(r"##\s*PSL\s*欠定(.*?)(?=^##|\Z)", dv, re.S | re.M)
        if sec:
            candidates = set(re.findall(r"`?([A-Z][a-zA-Z0-9]{2,40})`?\s*[—-]", sec.group(1)))
    invented = sorted(o for o in dos_objs if o not in vocab and o not in candidates)
    if invented:
        rejects.append(f"dos-proposal objects not in PSL Domain Model vocabulary nor declared as PSL 欠定 candidates: {invented}")
    uncited = sorted(ids - cited)
    if uncited and decisions:
        flags.append(f"PSL rules never cited by any decision: {uncited[:6]}{'…' if len(uncited) > 6 else ''} — decorative rules or missing decisions? (needs_semantic_review)")
    flags.append("needs_semantic_review: is the form right? which divergence branch is correct? should the PSL change? — G1 (human)")
    out = {"verdict": "REJECT" if rejects else "PASS", "decisions": decisions, "psl_ids": len(ids), "cited": len(cited),
           "dos_objects": sorted(dos_objs), "rejects": rejects, "flags": flags}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
