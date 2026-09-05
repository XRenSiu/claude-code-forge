#!/usr/bin/env python3
"""
lint_cards.py — the three mechanical checks on L4 task cards (plus two the reference doc adds).

A card is correct when a context-free agent can finish it alone. That is a judge call; what a script
CAN guarantee is the structural half that, when violated, makes parallel/isolated execution unsafe:

Usage:
  lint_cards.py <cards_dir> [--spec spec.md] [--done-when done_when.yaml] [--dos dos.yaml]
                [--max-context 40000]

Exit 0 = no rejects (flags may remain for a judge). Exit 1 = ≥1 REJECT. Exit 2 = usage/IO error.

Mechanical guarantees (REJECT on breach — the non-waivable half):
  1. REQ coverage: every REQ in the universe (from --spec `REQ-NNN` scan, else --done-when acceptance[].req,
     else the union of cards) is owned by exactly one card — none missing, none duplicated
  2. no write conflicts: two cards' allowed_files must not overlap (identical globs, literal ⊂ glob, or
     nested directory globs); shared files (lockfiles / package manifests / route tables) must be owned by
     at most one card, and any card that does not own them must forbid them
  3. DOS closure (only with --dos): every dos_slice.objects term is a declared object, every
     dos_slice.invariants id is a declared rule — structured fields only, never free text
  4. context_estimate_tokens ≤ --max-context (else split — this is a lint, not a remark)
  5. (with --done-when) every ac_ids entry exists in done_when.acceptance[].id
Semantic half (FLAGGED as needs_semantic_review): is the card self-contained? are allowed_files the
minimal set? is context_estimate honest? — a judge / human reads the card for those.
"""
import argparse
import fnmatch
import glob
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("lint_cards.py needs PyYAML: pip install pyyaml\n")
    sys.exit(2)

SHARED_BASENAMES = {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "Cargo.lock",
                    "Cargo.toml", "go.mod", "go.sum", "requirements.txt", "pyproject.toml", "poetry.lock",
                    "tsconfig.json", "Gemfile.lock", "composer.lock", ".env", "schema.prisma"}
REQ_RE = re.compile(r"\bREQ-\d{3,}\b")


def load_yaml(p):
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def glob_dir_prefix(pattern):
    """directory prefix before the first wildcard, e.g. src/auth/** -> src/auth"""
    parts = pattern.split("/")
    out = []
    for part in parts:
        if any(ch in part for ch in "*?["):
            break
        out.append(part)
    return "/".join(out)


def path_glob_match(path, pat):
    """path-aware glob: `dir/**` covers everything under dir; `**/x` matches basename; else fnmatch on the path."""
    if pat in ("**", "*", "**/*"):
        return True
    if pat.endswith("/**"):
        return path == pat[:-3] or path.startswith(pat[:-3] + "/")
    if pat.startswith("**/"):
        return fnmatch.fnmatch(path.split("/")[-1], pat[3:]) or fnmatch.fnmatch(path, pat[3:])
    return fnmatch.fnmatch(path, pat)


def patterns_overlap(a, b):
    if a == b:
        return True
    wa, wb = any(c in a for c in "*?["), any(c in b for c in "*?[")
    if not wa and not wb:
        return a == b
    if not wa and wb:
        return fnmatch.fnmatch(a, b) or fnmatch.fnmatch(a, b.replace("**/", "").replace("**", "*"))
    if wa and not wb:
        return patterns_overlap(b, a)
    # both wildcards: conservative — nested directory prefixes overlap
    pa, pb = glob_dir_prefix(a), glob_dir_prefix(b)
    if pa == pb:
        return True
    return pa.startswith(pb + "/") or pb.startswith(pa + "/") or pa == "" or pb == ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards_dir")
    ap.add_argument("--spec")
    ap.add_argument("--done-when")
    ap.add_argument("--dos")
    ap.add_argument("--max-context", type=int, default=40000)
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.cards_dir, "CARD-*.y*ml")))
    if not files:
        sys.stderr.write(f"lint_cards: no CARD-*.yaml under {a.cards_dir}\n")
        sys.exit(2)
    cards = {}
    rejects, flags, info = [], [], []
    for p in files:
        c = load_yaml(p)
        cid = c.get("id") or os.path.splitext(os.path.basename(p))[0]
        if cid in cards:
            rejects.append(f"duplicate card id {cid} ({p})")
        cards[cid] = c

    # REQ universe
    universe, source = set(), "cards-union"
    if a.spec:
        with open(a.spec, encoding="utf-8") as f:
            universe = set(REQ_RE.findall(f.read())); source = "spec"
    elif a.done_when:
        dw = load_yaml(a.done_when)
        universe = {ac.get("req") for ac in (dw.get("acceptance") or []) if ac.get("req")}; source = "done_when"
    if not universe:
        for c in cards.values():
            universe |= set(c.get("req_ids") or [])
        flags.append("REQ universe taken from the cards themselves — coverage is unverifiable without --spec/--done-when")

    # 1. coverage
    owner = {}
    for cid, c in cards.items():
        for r in c.get("req_ids") or []:
            owner.setdefault(r, []).append(cid)
    for r, cs in owner.items():
        if len(cs) > 1:
            rejects.append(f"{r} owned by {len(cs)} cards {cs} — one REQ, one card")
    missing = sorted(universe - set(owner))
    if missing:
        rejects.append(f"REQs not covered by any card ({source}): {missing}")
    extra = sorted(set(owner) - universe)
    if extra and source != "cards-union":
        flags.append(f"cards reference REQs absent from {source}: {extra}")

    # 2. write conflicts + shared files
    ids = list(cards)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            A, B = cards[ids[i]], cards[ids[j]]
            for pa in A.get("allowed_files") or []:
                for pb in B.get("allowed_files") or []:
                    if patterns_overlap(pa, pb):
                        rejects.append(f"write conflict: {ids[i]} `{pa}` overlaps {ids[j]} `{pb}`")
    for cid, c in cards.items():
        for pat in c.get("allowed_files") or []:
            if pat == "**" or pat == "*" or pat.endswith("/**") and glob_dir_prefix(pat) == "":
                rejects.append(f"{cid} allows everything (`{pat}`) — a card must name its files")
    shared_owner = {}
    for cid, c in cards.items():
        for pat in c.get("allowed_files") or []:
            for sb in SHARED_BASENAMES:
                # a root-level shared file is writable by a card only if a pattern actually matches that path
                if path_glob_match(sb, pat):
                    shared_owner.setdefault(sb, set()).add(cid)
    for sb, owners in shared_owner.items():
        if len(owners) > 1:
            rejects.append(f"shared file {sb} writable by {sorted(owners)} — own it in one card or forbid everywhere")
        for cid, c in cards.items():
            if cid not in owners:
                forb = c.get("forbidden_files") or []
                if not any(path_glob_match(sb, f) for f in forb):
                    flags.append(f"{cid} neither owns nor forbids shared file {sb}")

    # 3. DOS closure
    if a.dos:
        dos = load_yaml(a.dos)
        objs = set((dos.get("objects") or {}).keys()) if isinstance(dos.get("objects"), dict) else \
            {o.get("name") for o in (dos.get("objects") or []) if isinstance(o, dict)}
        rules = dos.get("rules") or []
        rule_ids = {r.get("id") for r in rules if isinstance(r, dict)} | {r for r in rules if isinstance(r, str)}
        for cid, c in cards.items():
            sl = c.get("dos_slice") or {}
            for o in sl.get("objects") or []:
                if o not in objs:
                    rejects.append(f"{cid} dos_slice.objects `{o}` not declared in dos.yaml (closure)")
            for r in sl.get("invariants") or []:
                if r not in rule_ids:
                    rejects.append(f"{cid} dos_slice.invariants `{r}` not a declared rule id (closure)")
    else:
        info.append("DOS closure unchecked (no --dos)")

    # 4. context estimate; 5. ac ids
    ac_ids = None
    if a.done_when:
        dw = load_yaml(a.done_when)
        ac_ids = {ac.get("id") for ac in (dw.get("acceptance") or [])}
    for cid, c in cards.items():
        ce = c.get("context_estimate_tokens")
        if ce is None or ce == 0:
            flags.append(f"{cid} context_estimate_tokens missing/0 — estimate honestly")
        elif ce > a.max_context:
            rejects.append(f"{cid} context_estimate_tokens {ce} > {a.max_context} — split the card")
        if not c.get("allowed_files"):
            rejects.append(f"{cid} has no allowed_files — whitelist executor has nothing to enforce")
        if not c.get("ac_ids"):
            flags.append(f"{cid} has no ac_ids — card-level acceptance will be empty")
        elif ac_ids is not None:
            for x in c["ac_ids"]:
                if x not in ac_ids:
                    rejects.append(f"{cid} ac_ids `{x}` not in done_when.acceptance")
        if not (c.get("title") or "").strip():
            flags.append(f"{cid} has no title")
    flags.append("needs_semantic_review: self-containment / minimal allowed_files / honest context estimate (judge)")

    out = {"cards": len(cards), "req_universe": sorted(universe), "source": source,
           "rejects": rejects, "flags": flags, "info": info, "verdict": "REJECT" if rejects else "PASS"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
