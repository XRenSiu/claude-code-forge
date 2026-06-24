#!/usr/bin/env python3
"""
verify_dos.py — the semantic exit for dos-extract.

A schema validator only asks "is this well-formed?"; the guarantee is checking the
PRODUCT against "what a clean DOS looks like". This enforces the mechanical half of the
quality criteria and FLAGS (does not decide) the semantic half.

Usage:
    python verify_dos.py <dos.yaml>

Exit 0 = no rejects (may still carry needs_semantic_review flags). Exit 1 = >=1 REJECT.

Mechanical guarantees (a breach is a REJECT — the non-waivable half):
  - <=7 core objects (else reject; ontology pollution / skipped Judgment 2 or 4)
  - every relationship subject/object is a declared object
  - every relationship carries a cardinality
  - no object name carries a UI/impl suffix (Card/Modal/Repository/Service/Manager/DTO/...)
  - load-bearing sections present: objects/relationships/rules (omission rejects; the other
    9 sections are reported as info, not rejected)
  - open_questions non-empty (a DOS with none is dishonest)

Semantic half — FLAGGED as needs_semantic_review, never auto-passed:
  - each agent_guidelines.must_not should trace to an anti_pattern or rule (judge call)
  - confirm each object is truly a business object, not UI/impl that slipped Judgment 1
"""
import sys
import json

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


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__)
        sys.exit(1)
    try:
        dos = yaml.safe_load(open(sys.argv[1], encoding="utf-8")) or {}
    except Exception as e:
        sys.stderr.write(f"REJECT: cannot read dos: {e}\n")
        sys.exit(1)

    rejects, flags, info = [], [], []

    # sections present
    missing = [s for s in SECTIONS if s not in dos]
    for s in missing:
        # objects/relationships/rules absent is fatal; the softer sections are info
        (rejects if s in ("objects", "relationships", "rules") else info).append(f"section missing: {s}")

    objects = dos.get("objects") or {}
    obj_names = set(objects.keys()) if isinstance(objects, dict) else set()

    # <=7 objects
    if len(obj_names) > 7:
        rejects.append(f"{len(obj_names)} objects > 7 — exceed only with a human waiver in decisions.md "
                       f"(usually a skipped Judgment 2 merge or Judgment 4 split): {sorted(obj_names)}")

    # UI/impl-suffixed object names
    for name in obj_names:
        if str(name).endswith(UI_IMPL_SUFFIXES):
            rejects.append(f"object '{name}' carries a UI/impl suffix — Judgment 1 says it is not a business object")

    # relationships reference declared objects + carry cardinality
    for rel in (dos.get("relationships") or []):
        if not isinstance(rel, dict):
            continue
        subj, obj, verb = rel.get("subject"), rel.get("object"), rel.get("verb")
        tag = f"{subj} {verb} {obj}"
        if subj not in obj_names:
            rejects.append(f"relationship '{tag}': subject '{subj}' not a declared object")
        if obj not in obj_names:
            rejects.append(f"relationship '{tag}': object '{obj}' not a declared object")
        if not rel.get("cardinality"):
            rejects.append(f"relationship '{tag}': missing cardinality")

    # open_questions non-empty
    oq = dos.get("open_questions")
    if not oq:
        rejects.append("open_questions empty — a DOS with none is trivial or dishonest")

    # semantic flags
    ag = dos.get("agent_guidelines") or {}
    for mn in (ag.get("must_not") or []):
        flags.append(f"trace must_not to an anti_pattern/rule (judge call): {str(mn)[:70]}")
    for name in sorted(obj_names):
        flags.append(f"confirm '{name}' is a business object, not UI/impl that slipped Judgment 1")

    report = {
        "dos": sys.argv[1],
        "object_count": len(obj_names),
        "relationship_count": len(dos.get("relationships") or []),
        "rejects": rejects,
        "info": info,
        "needs_semantic_review": flags[:12] + ([f"... +{len(flags)-12} more"] if len(flags) > 12 else []),
        "exit": "REJECT" if rejects else "MECHANICALLY_CLEAN",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
