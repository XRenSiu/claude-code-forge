#!/usr/bin/env python3
"""
verify_dos.py — the semantic exit for dos-extract.

A schema validator only asks "is this well-formed?"; the guarantee is checking the
PRODUCT against "what a clean DOS looks like". This enforces the mechanical half of the
quality criteria and FLAGS (does not decide) the semantic half.

Usage:
    python verify_dos.py <dos.yaml> [--decisions decisions.md] [--waive Name,Name]
                                    [--max-lines 800] [--max-description-chars 200]

Exit 0 = no rejects (may still carry needs_semantic_review flags and warnings).
Exit 1 = >=1 REJECT.

Mechanical guarantees (a breach is a REJECT — the non-waivable half):
  - <=7 core objects (else reject; ontology pollution / skipped Judgment 2 or 4)
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
    sdlc's 卡/`Card`, a card game's `Card`. Judgment 1 decides, the script errs strict.
    Clear it with `--waive Card` or, better, `--decisions decisions.md` carrying a
    `## Naming waivers` section whose bullets start with the waived name:
        ## Naming waivers
        - `Card` — Judgment 1 step 1 passes: a self-contained unit of work, no screen
          in its definition. Whole word, not a `*Card` compound.
    A waived name is not silently accepted: it is reported under `waived` and flagged
    for the judge.

Semantic half — FLAGGED as needs_semantic_review, never auto-passed:
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

SECTIONS = ["meta", "scope", "objects", "relationships", "rules", "composition",
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

    # <=7 objects
    if len(obj_names) > 7:
        rejects.append(f"{len(obj_names)} objects > 7 — exceed only with a human waiver in decisions.md "
                       f"(usually a skipped Judgment 2 merge or Judgment 4 split): {sorted(obj_names)}")

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
