#!/usr/bin/env python3
"""
verify_card.py — the semantic exit for invariant-extract.

Structural well-formedness does not certify an invariant card; the guarantee is a
check of the PRODUCT against "what a correct invariant looks like". This enforces the
mechanical half of that check and FLAGS (does not rubber-stamp) the semantic half.

Usage:
    python verify_card.py <invariant_card.yaml> [--dos <dos.yaml>]

Exit code 0 = no rejects (card may still carry needs_semantic_review flags for a judge).
Exit code 1 = at least one REJECT (a hard guarantee was breached) or the card is unreadable.

Mechanical guarantees enforced (a breach is a REJECT — the non-waivable half):
  - every invariant has provenance (execution_point OR obstacle_ref) ............ no provenance, no entry
  - strength matches its column (hard_invariants -> hard, overridable_defaults -> overridable)
  - hard invariants are disposition: propose ................................... never auto-install (R002)
  - aspect present and statement non-empty ..................................... named-field completeness
  - no entry id/statement duplicates an existing dos.yaml R00x rule id ......... dedup, don't re-legislate

Semantic half — FLAGGED as needs_semantic_review, never auto-passed:
  - survival_test == 'pass' (does it truly survive an unrelated Run under this purpose?)
  - narrowest rule on the right aspect (a judge call, not mechanical)
"""
import sys
import json

try:
    import yaml
except ImportError:
    sys.stderr.write("verify_card.py needs PyYAML: pip install pyyaml\n")
    sys.exit(1)


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def dos_rule_ids(dos_path):
    """Collect R00x rule ids + statements from a dos.yaml, for dedup."""
    if not dos_path:
        return set(), []
    dos = load(dos_path)
    ids, stmts = set(), []
    for r in (dos.get("rules") or []):
        if isinstance(r, dict):
            if r.get("id"):
                ids.add(str(r["id"]).strip())
            if r.get("statement"):
                stmts.append(str(r["statement"]).strip().lower())
    return ids, stmts


def has_provenance(entry):
    p = entry.get("provenance") or {}
    return bool((p.get("execution_point") or "").strip()) or bool((p.get("obstacle_ref") or "").strip())


def check_entry(entry, expected_strength, dos_ids, dos_stmts):
    rejects, flags = [], []
    eid = str(entry.get("id") or "<no-id>")

    if not has_provenance(entry):
        rejects.append(f"{eid}: no provenance (execution_point or obstacle_ref) — no provenance, no entry")
    if (entry.get("strength") or "") != expected_strength:
        rejects.append(f"{eid}: strength must be '{expected_strength}' in this column, got '{entry.get('strength')}'")
    if not (entry.get("aspect") or "").strip():
        rejects.append(f"{eid}: aspect missing (purpose projection not recorded)")
    if not (entry.get("statement") or "").strip():
        rejects.append(f"{eid}: statement empty")
    if expected_strength == "hard" and (entry.get("disposition") or "") != "propose":
        rejects.append(f"{eid}: hard invariant must be disposition: propose (never auto-install, R002)")

    stmt = (entry.get("statement") or "").strip().lower()
    if eid in dos_ids:
        rejects.append(f"{eid}: id collides with an existing dos.yaml R00x rule — dedup, don't re-legislate")
    if stmt and stmt in dos_stmts:
        flags.append(f"{eid}: statement matches an existing R00x rule — likely already constitution, dedup")

    if (entry.get("survival_test") or "") != "pass":
        flags.append(f"{eid}: survival_test != pass — needs_semantic_review (□/◊ judge call)")
    flags.append(f"{eid}: confirm narrowest-rule-on-right-aspect (judge call) — needs_semantic_review")
    return rejects, flags


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__)
        sys.exit(1)
    card_path = sys.argv[1]
    dos_path = None
    if "--dos" in sys.argv:
        i = sys.argv.index("--dos")
        if i + 1 < len(sys.argv):
            dos_path = sys.argv[i + 1]

    try:
        card = load(card_path)
    except Exception as e:  # unreadable card is a hard fail — an exit cannot certify what it cannot read
        sys.stderr.write(f"REJECT: cannot read card: {e}\n")
        sys.exit(1)

    dos_ids, dos_stmts = dos_rule_ids(dos_path)
    rejects, flags = [], []

    for entry in (card.get("hard_invariants") or []):
        r, f = check_entry(entry, "hard", dos_ids, dos_stmts)
        rejects += r
        flags += f
    for entry in (card.get("overridable_defaults") or []):
        r, f = check_entry(entry, "overridable", dos_ids, dos_stmts)
        rejects += r
        flags += f

    # ◊ leakage: anything kicked to done_when must NOT also be carded
    carded_ids = {str(e.get("id")) for e in (card.get("hard_invariants") or []) + (card.get("overridable_defaults") or [])}
    for k in (card.get("kicked_to_done_when") or []):
        if str(k.get("id")) in carded_ids:
            rejects.append(f"{k.get('id')}: a ◊ candidate is also carded as □ — pick one layer")

    report = {
        "card": card_path,
        "territory_id": card.get("territory_id"),
        "hard": len(card.get("hard_invariants") or []),
        "overridable": len(card.get("overridable_defaults") or []),
        "kicked_to_done_when": len(card.get("kicked_to_done_when") or []),
        "rejects": rejects,
        "needs_semantic_review": flags,
        "exit": "REJECT" if rejects else "MECHANICALLY_CLEAN",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
