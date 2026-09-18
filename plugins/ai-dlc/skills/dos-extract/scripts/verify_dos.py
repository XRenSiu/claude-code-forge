#!/usr/bin/env python3
"""
verify_dos.py — the semantic exit for dos-extract.

A schema validator only asks "is this well-formed?"; the guarantee is checking the
PRODUCT against "what a clean DOS looks like". This enforces the mechanical half of the
quality criteria and FLAGS (does not decide) the semantic half.

Usage:
    python verify_dos.py <dos.yaml> [--decisions decisions.md] [--waive Name,Name]
                                    [--terms terms.txt] [--core-only]
                                    [--max-lines 800] [--max-description-chars 200]

Exit 0 = no rejects (may still carry needs_semantic_review flags and warnings).
Exit 1 = >=1 REJECT.

A DOS is two layers, and this script checks both:
  - the CORE MODEL — `objects` (≤7 aggregates, the napkin), `relationships`, `rules`, `composition`;
  - the UBIQUITOUS LANGUAGE — `vocabulary`: every other term the team says (values, enum members,
    artifacts, roles, processes, terms owned by a neighbouring context), each with a kind, an owner
    (`of`), a definition, synonyms and rejected names. Until v0.11.0 the ≤7 cap was the ONLY
    layer, so the ~40 real terms Judgment 1 sorted into value / enum / composition / external
    survived only as decisions.md prose — invisible to every closure check downstream, which is
    what "the DOS extracts a sliver and aligns nothing" looks like from the outside. No ontology
    methodology caps concepts (Ontology 101 step 3 enumerates exhaustively; METHONTOLOGY and NeOn
    start from a glossary); they layer, and so does this file.

Mechanical guarantees (a breach is a REJECT — the non-waivable half):
  - <=7 core objects (else reject; ontology pollution / skipped Judgment 2 or 4 — or a long-tail
    term that belongs in `vocabulary`, not in another object)
  - `vocabulary` present and non-empty (a core model without its language is half a DOS) —
    waivable only by `--core-only` / a `core_only` waiver, for a to-be proposal derived before code
  - every vocabulary entry: `kind` in the closed set (dos_closure.VOCABULARY_KINDS), a non-empty
    `definition`, `of` (required for value / enum) resolving to a declared object / composition /
    term, `context` (required for external), `status` in active | deprecated | proposed
  - no term declared twice: a vocabulary key that is also an object / composition key, a synonym
    that is somebody else's canonical key, a name listed as both synonym and rejected_name
  - `--terms terms.txt` (count_terms.py format, or one label per line): EVERY counted label
    resolves through the closure — objects, compositions, vocabulary, synonyms, rejected names,
    rule ids. This is the coverage gate: a term the docs use N times that the DOS cannot place is
    the extraction's loss, reported by name. Without --terms coverage is reported as `unmeasured`.
  - every relationship subject/object is a declared object (or one of its synonyms)
  - every relationship carries a cardinality
  - no object name COMPOUNDED on a UI/impl suffix (TopicCard, UserRepository, …) —
    non-waivable: the high-risk list forbids promoting those, full stop
  - load-bearing sections present: objects/relationships/rules (omission rejects; the other
    9 sections are reported as info, not rejected)
  - open_questions non-empty (a DOS with none is dishonest)
  - a declared `properties.<p>.derived_from` names its source (blank rejects)

Waivable (REJECT by default, cleared by a recorded human waiver):
  - an object name that IS a whole UI/impl primitive (`Card`, `Modal`, `Service`).
    The heuristic exists for `TopicCard`; a whole word can be a real domain object —
    AI-DLC's 卡/`Card`, a card game's `Card`. Judgment 1 decides, the script errs strict.
    Clear it with `--waive Card` or, better, `--decisions decisions.md` carrying a
    `## Naming waivers` section whose bullets start with the waived name:
        ## Naming waivers
        - `Card` — Judgment 1 step 1 passes: a self-contained unit of work, no screen
          in its definition. Whole word, not a `*Card` compound.
    A waived name is not silently accepted: it is reported under `waived` and flagged
    for the judge.
  - MORE THAN 7 objects. The reject text has always said "exceed only with a human
    waiver in decisions.md", but nothing read one — so the lever it pointed at did not
    exist and the only way past was to ignore a permanently red pre-gate. A gate you
    can only pass by ignoring it is not a gate. The waiver uses the same bullet
    convention, named `object_count`:
        ## Naming waivers
        - `object_count` — 8 objects. Judgment 2 (nothing to merge into) and Judgment 4
          (same bounded context) were both applied; see the entry in decisions.md.
    Reported under `waived` and flagged, never silent — and a waiver that does not say
    which judgment it survived is recorded with "no reason recorded" beside it.

Semantic half — FLAGGED as needs_semantic_review, never auto-passed:
  - a label claimed by two concepts (环 → Ring | Loop) is a HOMONYM: the closure refuses it
    unqualified; confirm the split is real (Judgment 2 / 4) and both entries name their context
  - a vocabulary entry of kind external names a context absent from bounded_contexts
  - each agent_guidelines.must_not should trace to an anti_pattern or rule (judge call)
  - confirm each object is truly a business object, not UI/impl that slipped Judgment 1
  - every declared `derived_from` property is a MATERIALISED view: confirm what keeps it
    in sync with its source

Warnings (never affect the exit code — the size/legibility surrogates from
references/methodology.md §6, which until now lived only in prose):
  - dos.yaml longer than --max-lines (default 800: "sections are likely over-detailed")
  - an object description longer than --max-description-chars, empty, or still a
    template placeholder
"""
import argparse
import json
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("verify_dos.py needs PyYAML: pip install pyyaml\n")
    sys.exit(1)

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dos_closure  # noqa: E402  — the one definition of "what a DOS term resolves to"

SECTIONS = ["meta", "scope", "objects", "vocabulary", "relationships", "rules", "composition",
            "behaviors", "bounded_contexts", "agent_guidelines", "anti_patterns",
            "open_questions", "evolution_log"]
UI_IMPL_SUFFIXES = ("Card", "Modal", "Drawer", "Toast", "Panel", "Repository", "DAO",
                    "DTO", "Service", "Manager", "Handler", "Controller", "Provider",
                    "Factory", "Builder", "Helper", "Util", "Adapter", "Mapper")

PLACEHOLDER_RE = re.compile(r"^\s*(#|<|TODO|TBD|例[:：]|\.\.\.)", re.IGNORECASE)


def parse_waivers(path, section_title="naming waivers"):
    """Read `## <section_title>` bullets out of decisions.md.

    A bullet's waived name is the first backticked token, or the first word if the
    bullet has no backticks. Free prose after it is the justification the judge reads.
    `section_title` exists so there is ONE waiver-bullet convention in this skill:
    `verify_dos.py` reads `## Naming waivers`, `verify_vocabulary.py` imports this and
    reads `## Vocabulary waivers` — same shape, same parser, one thing for the human to learn.
    """
    waived = {}
    try:
        text = open(path, encoding="utf-8").read()
    except Exception as e:
        sys.stderr.write(f"verify_dos: cannot read decisions file: {e}\n")
        return waived
    section = None
    for line in text.splitlines():
        if line.startswith("#"):
            section = section_title.lower() in line.lower()
            continue
        if not section:
            continue
        m = re.match(r"\s*[-*]\s+(?:`([^`]+)`|([A-Za-z_][A-Za-z0-9_]*))\s*(.*)$", line)
        if m:
            name = (m.group(1) or m.group(2)).strip()
            waived[name] = (m.group(3) or "").lstrip("—- ").strip()
    return waived


def read_terms(path):
    """Labels out of a count_terms.py terms file (`Label = v1, v2`) or a one-label-per-line list.

    Returns label -> [variants]. Blank lines and `#` comments are skipped. A `/regex/` variant is
    kept as text (it is a counting device, not a word to resolve).
    """
    terms = {}
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            label, rhs = line.split("=", 1)
            variants = [v.strip() for v in rhs.split(",") if v.strip()]
        else:
            label, variants = line, []
        terms[label.strip()] = variants
    return terms


def suffix_hit(name):
    """('compound', suffix) | ('whole-word', suffix) | None."""
    for suf in UI_IMPL_SUFFIXES:
        if name == suf:
            return ("whole-word", suf)
    for suf in UI_IMPL_SUFFIXES:
        if name.endswith(suf):
            return ("compound", suf)
    return None


def object_names(objects):
    """Declared object keys plus every declared synonym.

    `synonyms:` exists so a DOS can record the team's real vocabulary next to the
    canonical key (I-11). Relationship refs and the downstream closure checks resolve
    through it; see scripts/dos_closure.py, which the closure consumers import.
    """
    canonical, alias = set(), {}
    if isinstance(objects, dict):
        items = objects.items()
    else:
        items = [(o.get("name"), o) for o in (objects or []) if isinstance(o, dict)]
    for name, body in items:
        if not name:
            continue
        canonical.add(str(name))
        syns = (body or {}).get("synonyms") if isinstance(body, dict) else None
        for s in (syns or []):
            if s:
                alias[str(s)] = str(name)
    return canonical, alias


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dos")
    ap.add_argument("--decisions", help="decisions.md carrying a `## Naming waivers` section")
    ap.add_argument("--waive", default="", help="comma-separated object names to waive ad hoc")
    ap.add_argument("--terms", help="count_terms.py terms file (or one label per line): every "
                                    "label must resolve through the closure — the coverage gate")
    ap.add_argument("--core-only", action="store_true",
                    help="accept a DOS without `vocabulary` (a to-be proposal derived before code); "
                         "reported as mode core_only, never silent")
    ap.add_argument("--max-lines", type=int, default=800,
                    help="warn above this many lines (methodology.md §6; default 800)")
    ap.add_argument("--max-description-chars", type=int, default=200,
                    help="warn above this description length (default 200)")
    a = ap.parse_args()

    try:
        raw = open(a.dos, encoding="utf-8").read()
        dos = yaml.safe_load(raw) or {}
    except Exception as e:
        sys.stderr.write(f"REJECT: cannot read dos: {e}\n")
        sys.exit(1)

    waivers = parse_waivers(a.decisions) if a.decisions else {}
    for n in (x.strip() for x in a.waive.split(",")):
        if n:
            waivers.setdefault(n, "--waive on the command line (no decisions.md entry)")

    rejects, flags, info, warnings, waived_used = [], [], [], [], []

    missing = [s for s in SECTIONS if s not in dos]
    for s in missing:
        # objects/relationships/rules absent is fatal; the softer sections are info
        (rejects if s in ("objects", "relationships", "rules") else info).append(f"section missing: {s}")

    objects = dos.get("objects") or {}
    obj_names, synonyms = object_names(objects)
    resolvable = obj_names | set(synonyms)

    # <=7 objects. 超过 7 个仍然默认 reject——它十有八九是漏做的一次合并或一次拆分。
    # 但豁免必须**可表达**：原来这条 reject 的措辞指向 decisions.md 的一条人签豁免，而没有
    # 任何代码去读它，于是唯一的出路是忽略一个永远红的预门。一个只能靠忽略才能过的门不是门
    # （与 sizing.yaml 的极性同源：豁免是一等记录，不是沉默）。
    if len(obj_names) > 7:
        if "object_count" in waivers:
            waived_used.append(f"'object_count': {len(obj_names)} objects > 7 waived — "
                               f"{waivers['object_count'] or 'no reason recorded'}")
            flags.append(f"waived object_count: {len(obj_names)} objects — confirm Judgment 2 "
                         f"(nothing to merge into) and Judgment 4 (one context, not two) really "
                         f"were applied: {sorted(obj_names)}")
        else:
            rejects.append(f"{len(obj_names)} objects > 7 — exceed only with a human waiver in decisions.md "
                           f"(a `## Naming waivers` bullet named `object_count`); usually a skipped "
                           f"Judgment 2 merge or Judgment 4 split, or a long-tail term that belongs in "
                           f"`vocabulary` (value / enum / artifact / role / process / external), not in "
                           f"another object: {sorted(obj_names)}")

    # UI/impl-suffixed object names
    for name in sorted(obj_names):
        hit = suffix_hit(str(name))
        if not hit:
            continue
        kind, suf = hit
        if kind == "compound":
            rejects.append(f"object '{name}' is compounded on the UI/impl primitive '{suf}' — "
                           f"Judgment 1 says it is not a business object (non-waivable)")
        elif name in waivers:
            waived_used.append(f"'{name}': whole-word '{suf}' waived — {waivers[name] or 'no reason recorded'}")
            flags.append(f"waived name '{name}': confirm Judgment 1 step 1 really passes "
                         f"(it is a whole word, not a '*{suf}' compound)")
        else:
            rejects.append(
                f"object '{name}' IS the UI/impl primitive '{suf}' — waivable: if Judgment 1 "
                f"says this is a real domain object, record it under `## Naming waivers` in "
                f"decisions.md and pass --decisions (or --waive {name}). Renaming a legitimate "
                f"domain word to satisfy this heuristic breaks downstream closure.")

    # ---- the ubiquitous-language layer -----------------------------------------------------
    closure = dos_closure.closure_from_dos(dos, a.dos)
    vocab = dos.get("vocabulary")
    core_only = a.core_only or ("core_only" in waivers)
    if not vocab:
        if core_only:
            why = waivers.get("core_only") if "core_only" in waivers else "--core-only on the command line"
            waived_used.append(f"'core_only': no `vocabulary` section — {why or 'no reason recorded'}")
            flags.append("core_only: this DOS is a core model without its ubiquitous language — "
                         "downstream closure resolves only object / composition names and rule ids")
        else:
            rejects.append("`vocabulary` missing or empty — a DOS is the core model AND the team's "
                           "whole language. Every term Judgment 1 sorted into value / enum / artifact / "
                           "role / process / external belongs here with kind, of, definition and "
                           "synonyms; a term that lives only in decisions.md resolves nowhere. "
                           "(--core-only / a `core_only` waiver for a to-be proposal derived before code.)")
        vocab = {}
    if not isinstance(vocab, dict):
        rejects.append("`vocabulary` must be a mapping of term -> entry")
        vocab = {}
    compositions = dos.get("composition") or {}
    comp_names = set(compositions) if isinstance(compositions, dict) else set()
    contexts = set()
    bc = dos.get("bounded_contexts") or {}
    if isinstance(bc, dict):
        if bc.get("current_context"):
            contexts.add("current")
        for side in ("upstream_contexts", "downstream_contexts"):
            for c in (bc.get(side) or []):
                if isinstance(c, dict) and c.get("name"):
                    contexts.add(str(c["name"]))
    for tname, body in vocab.items():
        tname = str(tname)
        body = body if isinstance(body, dict) else {}
        if tname in obj_names or tname in comp_names:
            rejects.append(f"vocabulary '{tname}' is also declared as an object / composition — one home per term")
        kind = str(body.get("kind") or "")
        if kind not in dos_closure.VOCABULARY_KINDS:
            rejects.append(f"vocabulary '{tname}': kind {kind!r} not in "
                           f"{' | '.join(dos_closure.VOCABULARY_KINDS)}")
        desc = str(body.get("definition") or "").strip()
        if not desc:
            rejects.append(f"vocabulary '{tname}': definition empty — a term without a definition "
                           f"is a word, not a concept (ISO 1087: the concept is what the term designates)")
        elif PLACEHOLDER_RE.match(desc):
            warnings.append(f"vocabulary '{tname}': definition is still a template placeholder ({desc[:40]!r})")
        elif len(desc) > a.max_description_chars:
            warnings.append(f"vocabulary '{tname}': definition {len(desc)} chars > "
                            f"{a.max_description_chars} — one sentence, the rest is a scope_note")
        of = body.get("of")
        if kind in ("value", "enum") and not of:
            rejects.append(f"vocabulary '{tname}': kind {kind} needs `of` — which object / term owns it")
        if of:
            for owner in (of if isinstance(of, list) else [of]):
                owner = str(owner).strip()
                if owner == tname or closure.resolve_object(owner) is None:
                    rejects.append(f"vocabulary '{tname}': `of: {owner}` does not resolve to a declared "
                                   f"object / composition / term ({closure.why_unresolved(owner)})")
        ctx = body.get("context")
        if kind == "external":
            if not ctx:
                rejects.append(f"vocabulary '{tname}': kind external needs `context` — the bounded "
                               f"context that owns the concept")
            elif str(ctx) not in contexts and str(ctx) != "current":
                flags.append(f"vocabulary '{tname}': context {ctx!r} is not named in bounded_contexts — "
                             f"declare the neighbour or fix the name")
        status = str(body.get("status") or "active")
        if status not in dos_closure.VOCABULARY_STATUSES:
            rejects.append(f"vocabulary '{tname}': status {status!r} not in "
                           f"{' | '.join(dos_closure.VOCABULARY_STATUSES)}")
        for ref in (body.get("see_also") or []):
            if closure.resolve_object(str(ref)) is None and closure.resolve_rule(str(ref)) is None:
                flags.append(f"vocabulary '{tname}': see_also {ref!r} resolves to nothing")
        syns = {str(x).strip() for x in (body.get("synonyms") or []) if x}
        rejs = {str(x).strip() for x in (body.get("rejected_names") or []) if x}
        for both in sorted(syns & rejs):
            rejects.append(f"vocabulary '{tname}': {both!r} is both a synonym and a rejected name")
    # a name claimed as synonym / rejected_name by one concept and canonical for another
    canonical_all = obj_names | comp_names | {str(k) for k in vocab}
    for label, canons in sorted(closure.ambiguous.items()):
        if label in canonical_all:
            others = [c for c in canons if c != label]
            rejects.append(f"'{label}' is a canonical key and also listed under {others} — a synonym "
                           f"cannot be somebody else's name (Judgment 2: merge, or pick one home)")
        else:
            flags.append(f"homonym '{label}' → {' | '.join(canons)}: the closure refuses it unqualified. "
                         f"Confirm the split is real (Judgment 2/4) and record how the team qualifies it")
    for layer in (objects if isinstance(objects, dict) else {}, compositions if isinstance(compositions, dict) else {}, vocab):
        for name, body in layer.items():
            if not isinstance(body, dict):
                continue
            syns = {str(x).strip() for x in (body.get("synonyms") or []) if x}
            rejs = {str(x).strip() for x in (body.get("rejected_names") or []) if x}
            for both in sorted(syns & rejs):
                if name not in vocab:
                    rejects.append(f"'{name}': {both!r} is both a synonym and a rejected name")

    # ---- coverage: every counted term must land somewhere ----------------------------------
    coverage = {"status": "unmeasured", "terms": 0, "resolved": 0, "unplaced": []}
    if a.terms:
        try:
            terms = read_terms(a.terms)
        except OSError as e:
            sys.stderr.write(f"REJECT: cannot read --terms: {e}\n")
            sys.exit(1)
        unplaced = []
        for label, variants in terms.items():
            cands = [label] + [v for v in variants if not (v.startswith("/") and v.endswith("/"))]
            hit = next((c for c in cands if closure.resolve_object(c) or closure.resolve_rule(c)), None)
            if hit is None:
                unplaced.append(label)
        coverage = {"status": "measured", "terms": len(terms), "resolved": len(terms) - len(unplaced),
                    "unplaced": unplaced}
        if unplaced:
            rejects.append(f"coverage: {len(unplaced)}/{len(terms)} counted terms resolve nowhere in the "
                           f"DOS — {unplaced}. Each needs a home: an object, a composition, a vocabulary "
                           f"entry, a synonym or a rejected_name. A term the team counts and the DOS "
                           f"cannot place is the extraction's loss, not the team's noise.")

    # relationships reference declared objects (or a synonym) + carry cardinality
    for rel in (dos.get("relationships") or []):
        if not isinstance(rel, dict):
            continue
        subj, obj, verb = rel.get("subject"), rel.get("object"), rel.get("verb")
        tag = f"{subj} {verb} {obj}"
        for role, val in (("subject", subj), ("object", obj)):
            if val in obj_names:
                continue
            if val in synonyms:
                flags.append(f"relationship '{tag}': {role} '{val}' resolves through a synonym "
                             f"of '{synonyms[val]}' — prefer the canonical name in relationships")
                continue
            rejects.append(f"relationship '{tag}': {role} '{val}' not a declared object")
        if not rel.get("cardinality"):
            rejects.append(f"relationship '{tag}': missing cardinality")

    # derived_from: a materialised derived view names its source
    derived_props = []
    if isinstance(objects, dict):
        for oname, body in objects.items():
            props = (body or {}).get("properties") if isinstance(body, dict) else None
            if not isinstance(props, dict):
                continue
            for pname, pbody in props.items():
                if not isinstance(pbody, dict) or "derived_from" not in pbody:
                    continue
                src = pbody.get("derived_from")
                srcs = src if isinstance(src, list) else [src]
                if not any(str(s).strip() for s in srcs if s is not None):
                    rejects.append(f"{oname}.{pname}: `derived_from` present but empty — "
                                   f"a materialised derived view must name what it derives from")
                    continue
                derived_props.append(f"{oname}.{pname}")
                flags.append(f"{oname}.{pname} is a materialised derived view (derived_from: "
                             f"{'; '.join(str(s) for s in srcs)}) — confirm what keeps it in "
                             f"sync with its source, and that it is not really pure `composition`")

    # open_questions non-empty
    oq = dos.get("open_questions")
    if not oq:
        rejects.append("open_questions empty — a DOS with none is trivial or dishonest")

    # size / legibility surrogates (methodology.md §6) — warnings, never the exit code
    n_lines = len(raw.splitlines())
    budget = 100 * max(len(obj_names), 1)   # methodology.md §6: ~300-500 lines for 6 objects
    if n_lines > a.max_lines:
        warnings.append(f"{n_lines} lines > {a.max_lines} — methodology.md §6: sections are likely "
                        f"over-detailed (properties listed field-by-field instead of at the "
                        f"conceptual level)")
    elif n_lines > budget:
        warnings.append(f"{n_lines} lines over a {budget}-line budget for {len(obj_names)} objects "
                        f"— methodology.md §6 expects ~300-500 at 6 objects (~100/object). Not yet "
                        f"the {a.max_lines}-line bloat threshold, but check whether properties are "
                        f"listed field-by-field instead of at the conceptual level.")
    if isinstance(objects, dict):
        for oname, body in objects.items():
            desc = ((body or {}).get("description") if isinstance(body, dict) else None) or ""
            desc = str(desc).strip()
            if not desc:
                warnings.append(f"object '{oname}': description empty")
            elif PLACEHOLDER_RE.match(desc):
                warnings.append(f"object '{oname}': description is still a template placeholder "
                                f"({desc[:40]!r})")
            elif len(desc) > a.max_description_chars:
                warnings.append(f"object '{oname}': description {len(desc)} chars > "
                                f"{a.max_description_chars} — a one-sentence definition, not a spec")

    # semantic flags
    ag = dos.get("agent_guidelines") or {}
    for mn in (ag.get("must_not") or []):
        flags.append(f"trace must_not to an anti_pattern/rule (judge call): {str(mn)[:70]}")
    for name in sorted(obj_names):
        flags.append(f"confirm '{name}' is a business object, not UI/impl that slipped Judgment 1")

    report = {
        "dos": a.dos,
        "line_count": n_lines,
        "object_count": len(obj_names),
        "synonym_count": len(synonyms),
        "vocabulary_count": len(vocab),
        "resolvable_labels": len(closure.vocabulary("both")),
        "homonyms": {k: v for k, v in sorted(closure.ambiguous.items())},
        "mode": "core_only" if core_only and not dos.get("vocabulary") else "two_layer",
        "coverage": coverage,
        "derived_properties": derived_props,
        "relationship_count": len(dos.get("relationships") or []),
        "rejects": rejects,
        "waived": waived_used,
        "warnings": warnings,
        "info": info,
        "needs_semantic_review": flags[:12] + ([f"... +{len(flags)-12} more"] if len(flags) > 12 else []),
        "exit": "REJECT" if rejects else "MECHANICALLY_CLEAN",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
