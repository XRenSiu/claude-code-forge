#!/usr/bin/env python3
"""
lint_cards.py — the three mechanical checks on L4 task cards (plus two the reference doc adds).

A card is correct when a context-free agent can finish it alone. That is a judge call; what a script
CAN guarantee is the structural half that, when violated, makes parallel/isolated execution unsafe:

Usage:
  lint_cards.py <cards_dir> [--spec spec.md] [--done-when done_when.yaml] [--dos dos.yaml] [--require-dos]
                [--max-context 40000]

Exit 0 = no rejects (flags may remain for a judge). Exit 1 = ≥1 REJECT. Exit 2 = usage/IO error.

Mechanical guarantees (REJECT on breach — the non-waivable half):
  1. REQ coverage: every REQ in the universe (from --spec `REQ-NNN` scan, else --done-when acceptance[].req,
     else the union of cards) is owned by exactly one card — none missing, none duplicated
  2. no write conflicts: two cards' allowed_files must not overlap (identical globs, literal ⊂ glob, or
     nested directory globs); shared files (lockfiles / package manifests / route tables) must be owned by
     at most one card, and any card that does not own them must forbid them
  3. DOS closure (only with --dos, or auto-discovered under --require-dos):
     every dos_slice.objects term is a declared object, every
     dos_slice.invariants id is a declared rule — structured fields only, never free text
  4. context_estimate_tokens ≤ --max-context (else split — this is a lint, not a remark)
  5. (with --done-when) every ac_ids entry exists in done_when.acceptance[].id
  6. projection ↔ data source: a card that owns a rendering / reporting script must declare `reads_from:`,
     and every declared source that ANOTHER card owns needs `depends_on` on that card plus a seam note in
     `notes`. With --repo-root the script is also read: a path literal in its source that another card owns
     but the card did not declare is an undeclared seam. Rationale in references/splitting.md.
Semantic half (FLAGGED as needs_semantic_review): is the card self-contained? are allowed_files the
minimal set? is context_estimate honest? — a judge / human reads the card for those.
"""
import argparse
import fnmatch
import glob
import json
import os
import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("lint_cards.py needs PyYAML: pip install pyyaml\n")
    sys.exit(2)

# DOS closure means the same thing here and in verify_issue.py: one resolver, owned by
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

SHARED_BASENAMES = {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "Cargo.lock",
                    "Cargo.toml", "go.mod", "go.sum", "requirements.txt", "pyproject.toml", "poetry.lock",
                    "tsconfig.json", "Gemfile.lock", "composer.lock", ".env", "schema.prisma"}
REQ_RE = re.compile(r"\bREQ-\d{3,}\b")
# A projection is code whose whole job is to present someone else's data. Matched on the basename of a
# literal script path only, so `src/views/**` (a UI directory) never trips it.
PROJECTION_DEFAULT = r"render|report|dashboard|chart|plot|summary|digest"
SCRIPT_EXTS = (".py", ".sh", ".bash", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".rb", ".go", ".rs", ".pl", ".php")
# quoted path-like literals inside a projection script: has a dot-extension, no spaces
PATH_LITERAL_RE = re.compile(r"""["'`]([A-Za-z0-9_./\-]+\.[A-Za-z0-9]{1,6})["'`]""")


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


def is_projection(pattern, projection_re):
    """True when the pattern names a literal script file whose basename reads as a projection."""
    base = pattern.split("/")[-1]
    if any(ch in base for ch in "*?["):
        return False
    if not base.lower().endswith(SCRIPT_EXTS):
        return False
    return bool(projection_re.search(base))


def owner_of(path, cards, exclude=None):
    """Which card's allowed_files cover this path (first match; None when nobody owns it)."""
    for cid, c in cards.items():
        if cid == exclude:
            continue
        for pat in c.get("allowed_files") or []:
            if path == pat or path_glob_match(path, pat):
                return cid
    return None


def read_path_literals(repo_root, script_path):
    p = os.path.join(repo_root, script_path) if repo_root else script_path
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return sorted(set(PATH_LITERAL_RE.findall(f.read())))
    except OSError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards_dir")
    ap.add_argument("--spec")
    ap.add_argument("--done-when")
    ap.add_argument("--dos")
    ap.add_argument("--require-dos", dest="require_dos", action="store_true",
                    help="把「dos_slice 闭包未检」从 info 升成 reject；没给 --dos 时先自动发现 dos.yaml。"
                         "卡里出现一个本体解析不了的名词是整条流水线上代价最高的一次漂移")
    ap.add_argument("--max-context", type=int, default=40000)
    ap.add_argument("--repo-root", help="resolve allowed_files against this root to read projection scripts")
    ap.add_argument("--projection-pattern", default=PROJECTION_DEFAULT,
                    help="basename regex that marks a script as a projection (default: %(default)s)")
    a = ap.parse_args()
    if a.require_dos and not a.dos and repo_assets is not None:
        a.dos = repo_assets.find("dos")
    projection_re = re.compile(a.projection_pattern, re.IGNORECASE)

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

    # 3. DOS closure — resolved through dos-extract's shared closure module, so a term
    #    recorded as an object `synonyms:` / rule `aliases:` entry closes (dogfood I-15/I-49:
    #    the cards spoke the docs' vocabulary, the DOS keyed the objects differently, and the
    #    linter had to be pointed at a hand-picked proposal file instead).
    if a.dos:
        if dos_closure is None:
            flags.append("--dos given but dos-extract/scripts/dos_closure.py is not reachable — "
                         "closure unchecked; install the neighbour skill or drop --dos")
            closure = None
        else:
            closure = dos_closure.closure_from_dos(load_yaml(a.dos), a.dos)
        for cid, c in cards.items():
            sl = c.get("dos_slice") or {}
            for o in sl.get("objects") or []:
                canon = closure.resolve_object(o)
                if canon is None:
                    rejects.append(f"{cid} dos_slice.objects `{o}` not declared in dos.yaml (closure)")
                elif canon != o:
                    flags.append(f"{cid} dos_slice.objects `{o}` closes as a synonym of `{canon}`")
            for r in sl.get("invariants") or []:
                canon = closure.resolve_rule(r)
                if canon is None:
                    rejects.append(f"{cid} dos_slice.invariants `{r}` not a declared rule id (closure)")
                elif canon != r:
                    flags.append(f"{cid} dos_slice.invariants `{r}` closes as an alias of `{canon}`")
    elif a.require_dos:
        rejects.append(
            "dos_slice closure unchecked and --require-dos is set: no dos.yaml given or found in the "
            "project (ai-dlc/scripts/repo_assets.py searches the repo root, docs/, ontology/). "
            "卡里出现一个本体解析不了的名词，实现者会自己给它挑一个意思，而这个意思要到验收才对得上——"
            "未检不是通过。Run /dos-extract and commit dos.yaml to git.")
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
    # 6. projection ↔ data source must not straddle a card seam
    for cid, c in sorted(cards.items()):
        projections = [p for p in (c.get("allowed_files") or []) if is_projection(p, projection_re)]
        if not projections:
            continue
        declared = c.get("reads_from")
        if declared is None:
            rejects.append(f"{cid} owns projection script(s) {projections} but declares no `reads_from:` — "
                           f"name the data it renders (empty list = renders nothing another card owns)")
            declared = []
        elif not isinstance(declared, list):
            rejects.append(f"{cid} reads_from must be a list of paths, got {type(declared).__name__}")
            declared = []
        deps = set(c.get("depends_on") or [])
        note = (c.get("notes") or "").strip()
        for src in declared:
            if any(path_glob_match(src, pat) or src == pat for pat in c.get("allowed_files") or []):
                continue  # same card — the atomic case, nothing to check
            other = owner_of(src, cards, exclude=cid)
            if other is None:
                info.append(f"{cid} reads `{src}`, which no card owns — external input")
                continue
            if other not in deps:
                rejects.append(f"{cid} renders `{src}` but {other} owns it and {cid} does not depends_on "
                               f"{other} — a projection and its data source belong in one card, or the "
                               f"seam must be declared")
            elif not note or (src not in note and other not in note):
                rejects.append(f"{cid} depends_on {other} for `{src}` but its notes do not describe the "
                               f"seam — say what breaks if only one side changes")
        if a.repo_root:
            for script in projections:
                literals = read_path_literals(a.repo_root, script)
                if literals is None:
                    flags.append(f"{cid} projection `{script}` not readable under --repo-root — "
                                 f"reads_from is unverified")
                    continue
                for lit in literals:
                    if lit in declared or lit == os.path.basename(script):
                        continue
                    if any(path_glob_match(lit, pat) for pat in c.get("allowed_files") or []):
                        continue
                    other = owner_of(lit, cards, exclude=cid)
                    if other:
                        rejects.append(f"{cid} projection `{script}` reads `{lit}`, owned by {other}, and "
                                       f"`{lit}` is not in {cid}.reads_from — undeclared seam")
    flags.append("needs_semantic_review: self-containment / minimal allowed_files / honest context estimate (judge)")

    out = {"cards": len(cards), "req_universe": sorted(universe), "source": source,
           "rejects": rejects, "flags": flags, "info": info, "verdict": "REJECT" if rejects else "PASS"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
