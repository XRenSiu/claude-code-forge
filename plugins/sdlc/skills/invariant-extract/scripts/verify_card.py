#!/usr/bin/env python3
"""
verify_card.py — the semantic exit for invariant-extract.

Structural well-formedness does not certify an invariant card; the guarantee is a
check of the PRODUCT against "what a correct invariant looks like". This enforces the
mechanical half of that check and FLAGS (does not rubber-stamp) the semantic half.

Usage:
    python verify_card.py <invariant_card.yaml> [--dos <dos.yaml>] [--near-duplicate 0.6]

Exit code 0 = no rejects (card may still carry needs_semantic_review flags for a judge).
Exit code 1 = at least one REJECT (a hard guarantee was breached) or the card is unreadable.

`R00x` below means an id in the DOS's own `rules` section (in sdlc: R001 single producer,
R002 single contract schema, …). Hard invariants land only behind a human-signed gate —
in sdlc that is **G2**, via a change proposal; the card is a draft, never an installation.

Mechanical guarantees enforced (a breach is a REJECT — the non-waivable half):
  - every invariant has provenance (execution_point OR obstacle_ref) ............ no provenance, no entry
  - strength matches its column (hard_invariants -> hard, overridable_defaults -> overridable)
  - hard invariants are disposition: propose ................................... never auto-install
  - low confidence => disposition: propose, in EITHER column .................... references/abduction.md §5
  - aspect present and statement non-empty ..................................... named-field completeness
  - altitude, where present, is `territory` .................................... one place says "this looks
        constitutional": the top-level constitution_promotion_suspects section (survival-test.md §2.5)
  - no entry id/statement duplicates an existing dos.yaml R00x rule id ......... dedup, don't re-legislate
  - a ◊ candidate kicked to done_when is not also carded ....................... pick one layer
  - channel_2_input.failure_memory_count > 0 requires `sources` ................ a bare integer is
        unfalsifiable; the count has to decompose into named failure-memory sources
  - registered_gaps entries carry a destination in {done_when, issue, backlog} .. a registered gap is
        "not built yet", not "was violated": negating it yields a ◊, never a □

Semantic half — FLAGGED as needs_semantic_review, never auto-passed:
  - survival_test == 'pass' (does it truly survive an unrelated Run under this purpose?)
  - narrowest rule on the right aspect — flagged only where the card gives the judge a reason
    to look: low confidence, or no narrowest_rule_note. A flag on every entry unconditionally
    is 13 lines of noise that hides the two that matter.
  - near-duplicates: an entry whose statement is a re-wording of a DOS rule or of another entry
    on the same card. Exact lowercase equality catches nothing that a paraphrase does not evade.
"""
import argparse
import json
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("verify_card.py needs PyYAML: pip install pyyaml\n")
    sys.exit(1)

LATIN = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
CJK = re.compile(r"[一-鿿]")
# words too common to carry meaning in an EARS statement
STOP = {"the", "a", "an", "of", "to", "in", "on", "at", "by", "for", "with", "and",
        "or", "not", "is", "are", "be", "shall", "system", "when", "while", "if",
        "that", "this", "it", "its", "any", "every", "each", "must", "never"}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def stem(w):
    """Crudest useful stemmer: `picked`/`picks`/`picking` -> `pick`.

    Without it, `auto-pick one` and `never auto-picked` share no token and a paraphrase
    of an existing rule sails through — the exact miss this check exists to close.
    """
    for suf in ("ing", "ied", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)] + ("y" if suf == "ied" else "")
    return w


def tokens(text):
    """Latin word stems + CJK character bigrams — a language-agnostic bag.

    CJK has no whitespace, so bigrams are the cheap standard stand-in for words; mixed
    EN/CJK statements (the normal shape here) get both halves. Bigrams are taken per CJK
    RUN, not over the concatenation, so characters either side of a latin word do not
    fuse into a bigram that appears in neither text.
    """
    t = str(text or "").lower()
    bag = {stem(w) for w in LATIN.findall(t) if w not in STOP and len(w) > 1}
    for run in re.findall(r"[一-鿿]+", t):
        bag |= {run[i:i + 2] for i in range(len(run) - 1)} or {run}
    return bag


def similarity(a, b):
    """max(Jaccard, overlap coefficient).

    Jaccard alone punishes a restatement for being shorter, which is how most
    re-legislation actually looks: the same rule said again in fewer words. The overlap
    coefficient catches that; taking the max keeps both. This is a FLAG threshold, so it
    is tuned for recall — a false "these look alike" costs a judge one glance.
    """
    ta, tb = tokens(a), tokens(b)
    if len(ta) < 3 or len(tb) < 3:
        return 0.0
    inter = len(ta & tb)
    return max(inter / len(ta | tb), inter / min(len(ta), len(tb)))


def dos_rules(dos_path):
    """Collect rule ids + statements from a dos.yaml, for dedup."""
    if not dos_path:
        return set(), []
    dos = load(dos_path)
    ids, stmts = set(), []
    for r in (dos.get("rules") or []):
        if isinstance(r, dict):
            if r.get("id"):
                ids.add(str(r["id"]).strip())
            if r.get("statement"):
                stmts.append((str(r.get("id") or "?"), str(r["statement"]).strip()))
    return ids, stmts


def has_provenance(entry):
    p = entry.get("provenance") or {}
    return bool((p.get("execution_point") or "").strip()) or bool((p.get("obstacle_ref") or "").strip())


def check_entry(entry, expected_strength, dos_ids, dos_stmts, threshold):
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

    disposition = (entry.get("disposition") or "").strip()
    if expected_strength == "hard" and disposition != "propose":
        rejects.append(f"{eid}: hard invariant must be disposition: propose (never auto-install; "
                       f"it lands only behind the human-signed G2 gate)")
    if (entry.get("confidence") or "").strip() == "low" and disposition != "propose":
        rejects.append(f"{eid}: confidence low must be disposition: propose even in the overridable "
                       f"column (references/abduction.md §5: wide / assumption-chained abductions "
                       f"are proposed, not carded)")

    altitude = (entry.get("altitude") or "").strip()
    if altitude and altitude != "territory":
        rejects.append(f"{eid}: altitude '{altitude}' — a carded entry is territory-level. Record the "
                       f"constitutional suspicion once, in constitution_promotion_suspects "
                       f"(survival-test.md §2.5); the narrowed territory form stays carded here.")

    stmt = (entry.get("statement") or "").strip()
    if eid in dos_ids:
        rejects.append(f"{eid}: id collides with an existing dos.yaml R00x rule — dedup, don't re-legislate")
    for rid, rstmt in dos_stmts:
        sim = similarity(stmt, rstmt)
        if sim >= 0.95:
            flags.append(f"{eid}: statement matches dos.yaml {rid} — likely already constitution, dedup")
        elif sim >= threshold:
            flags.append(f"{eid}: statement is {sim:.2f} similar to dos.yaml {rid} "
                         f"(\"{rstmt[:60]}…\") — a re-wording of an existing rule is still re-legislation")

    if (entry.get("survival_test") or "") != "pass":
        flags.append(f"{eid}: survival_test != pass — needs_semantic_review (□/◊ judge call)")
    # targeted, not unconditional: flag only where the card itself gives a reason to look
    if not (entry.get("narrowest_rule_note") or "").strip():
        flags.append(f"{eid}: no narrowest_rule_note — confirm this is the narrowest rule on the "
                     f"right aspect, or write why (judge call)")
    elif (entry.get("confidence") or "").strip() == "low":
        flags.append(f"{eid}: low confidence — re-check the narrowest-rule reasoning before signing")
    return rejects, flags


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("card")
    ap.add_argument("--dos")
    ap.add_argument("--near-duplicate", type=float, default=0.6,
                    help="Jaccard threshold for the near-duplicate flag (default 0.6)")
    a = ap.parse_args()

    try:
        card = load(a.card)
    except Exception as e:  # unreadable card is a hard fail — an exit cannot certify what it cannot read
        sys.stderr.write(f"REJECT: cannot read card: {e}\n")
        sys.exit(1)

    dos_ids, dos_stmts = dos_rules(a.dos)
    rejects, flags = [], []

    hard = card.get("hard_invariants") or []
    over = card.get("overridable_defaults") or []
    for entry in hard:
        r, f = check_entry(entry, "hard", dos_ids, dos_stmts, a.near_duplicate)
        rejects += r
        flags += f
    for entry in over:
        r, f = check_entry(entry, "overridable", dos_ids, dos_stmts, a.near_duplicate)
        rejects += r
        flags += f

    # near-duplicates WITHIN the card: two entries re-stating one rule
    all_entries = list(hard) + list(over)
    for i in range(len(all_entries)):
        for j in range(i + 1, len(all_entries)):
            sim = similarity(all_entries[i].get("statement"), all_entries[j].get("statement"))
            if sim >= a.near_duplicate:
                flags.append(f"{all_entries[i].get('id')} / {all_entries[j].get('id')}: statements "
                             f"{sim:.2f} similar — same rule twice, or genuinely two rules?")

    # ◊ leakage: anything kicked to done_when must NOT also be carded
    carded_ids = {str(e.get("id")) for e in all_entries if e.get("id")}
    kicked = card.get("kicked_to_done_when") or []
    for k in kicked:
        kid = k.get("id")
        if kid is None:
            flags.append("a kicked_to_done_when entry has no id — the ◊-leakage check compares ids "
                         "and cannot see this entry")
            continue
        if str(kid) in carded_ids:
            rejects.append(f"{kid}: a ◊ candidate is also carded as □ — pick one layer")

    # channel 2: a count with no sources is unfalsifiable
    c2 = card.get("channel_2_input") or {}
    count = c2.get("failure_memory_count") or 0
    sources = c2.get("sources") or []
    if count and not c2.get("dry") and not sources:
        rejects.append(f"channel_2_input.failure_memory_count={count} with no `sources` — an integer "
                       f"nobody can check. Break it down by failure-memory source (ledger fail / "
                       f"deviation rows, escape defects, skill-issues, G3 records).")
    if sources:
        total = sum((s or {}).get("entries") or 0 for s in sources if isinstance(s, dict))
        if count and total != count:
            flags.append(f"channel_2_input: sources sum to {total} but failure_memory_count={count} — "
                         f"overlap between sources, or a stale count?")
        if not (c2.get("snapshot_at") or "").strip():
            flags.append("channel_2_input: no snapshot_at — failure memory grows during a run, so the "
                         "count is not reproducible without the point it was taken at")

    # registered gaps must declare where they go
    gaps = card.get("registered_gaps") or []
    for g in gaps:
        dest = (g or {}).get("destination")
        if dest not in ("done_when", "issue", "backlog"):
            rejects.append(f"registered_gaps entry {str((g or {}).get('gap'))[:40]!r}: destination "
                           f"{dest!r} not one of done_when|issue|backlog — a registered gap is 'not "
                           f"built yet', not 'was violated'; negating it yields a ◊, never a □")

    report = {
        "card": a.card,
        "territory_id": card.get("territory_id"),
        "hard": len(hard),
        "overridable": len(over),
        "kicked_to_done_when": len(kicked),
        "projected_out_obstacles": len(card.get("projected_out_obstacles") or []),
        "registered_gaps": len(gaps),
        "deduped_against_constitution": len(card.get("deduped_against_constitution") or []),
        "constitution_promotion_suspects": len(card.get("constitution_promotion_suspects") or []),
        "conflicts_for_legislation": len(card.get("conflicts_for_legislation") or []),
        "channel_2": {"failure_memory_count": count, "dry": bool(c2.get("dry")),
                      "sources": len(sources), "snapshot_at": c2.get("snapshot_at") or None},
        "rejects": rejects,
        "needs_semantic_review": flags,
        "exit": "REJECT" if rejects else "MECHANICALLY_CLEAN",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
