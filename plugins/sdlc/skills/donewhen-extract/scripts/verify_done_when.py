#!/usr/bin/env python3
"""
verify_done_when.py — the semantic exit for donewhen-extract.

Structural well-formedness does not certify a done_when card; the guarantee is a check of
the PRODUCT against "what a falsifiable ◊ acceptance condition looks like". This enforces
the mechanical half of that check (the three HTML disciplines) and FLAGS (does not
rubber-stamp) the semantic half.

Usage:
    python verify_done_when.py <done_when_card.yaml> [--dos <dos.yaml>]

Exit 0 = no rejects (card may still carry needs_semantic_review flags for a judge).
Exit 1 = at least one REJECT (a discipline was breached) or the card is unreadable.

Mechanical guarantees enforced (a breach is a REJECT — the non-waivable half):
  - 纪律① every clause is falsifiable: a banned vague quantifier with no threshold -> reject
  - 纪律② every event/state happy clause has a paired unhappy clause (paired_with) -> reject
  - id present, REQ-ID/DW-shaped, unique within the card
  - statement non-empty (EARS grammar niceties are a judge call — flagged, not rejected)
  - 纪律③-a contradiction: two clauses, same trigger, opposite polarity -> reject (suspected)
  - 纪律③-b coverage: an event happy clause with zero unwanted sibling -> reject

Semantic half — FLAGGED as needs_semantic_review, never auto-passed:
  - threshold actually traces to kpi/slo/failure_memory (not pulled from air)
  - the unhappy twin covers the RIGHT edge; the SMT-grade satisfiability of all thresholds
  - whether a clause is really the narrowest falsifiable condition for this Run
"""
import re
import sys
import json

try:
    import yaml
except ImportError:
    sys.stderr.write("verify_done_when.py needs PyYAML: pip install pyyaml\n")
    sys.exit(1)

# 形容词/模糊量词黑名单(中英)。命中且无 threshold -> 不可证伪 -> reject。
VAGUE = [
    "快", "慢", "稳定", "可靠", "健壮", "高效", "及时", "尽快", "尽量", "大部分",
    "多数", "合理", "友好", "流畅", "顺畅", "良好", "充分", "适当", "足够",
    "fast", "slow", "stable", "reliable", "robust", "quick", "soon", "most",
    "reasonable", "friendly", "smooth", "adequate", "sufficient", "better",
]
ID_RE = re.compile(r"^(REQ-|DW-|[A-Z][A-Z0-9]*-)?\w+[-_]?\d+$|^DW-\d+$")
NEG = ("not", "never", "no ", "拒绝", "禁止", "不得", "不能", "不应", "非", "shall not", "shall never")


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def has_threshold(c):
    t = (c.get("threshold") or "").strip()
    # a number anywhere in threshold OR in the statement counts as pinned
    if t:
        return True
    stmt = (c.get("statement") or "")
    return bool(re.search(r"\d", stmt)) and bool(re.search(r"[<>≤≥=%]|ms\b|s\b|次|秒|毫秒", stmt))


def vague_unpinned(c):
    stmt = (c.get("statement") or "")
    hit = [w for w in VAGUE if w in stmt]
    return hit if (hit and not has_threshold(c)) else []


def polarity(text):
    t = (text or "").lower()
    return -1 if any(n in t for n in NEG) else 1


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__)
        sys.exit(1)
    card_path = sys.argv[1]
    try:
        card = load(card_path)
    except Exception as e:  # an exit cannot certify what it cannot read
        sys.stderr.write(f"REJECT: cannot read card: {e}\n")
        sys.exit(1)

    clauses = card.get("clauses") or []
    rejects, flags = [], []
    seen_ids = set()
    by_id = {str(c.get("id")): c for c in clauses if c.get("id")}

    def is_unhappy(clause):
        if clause is None:
            return False
        return (clause.get("ears_type") or "") == "unwanted" or polarity(clause.get("then") or clause.get("statement")) == -1

    for c in clauses:
        cid = str(c.get("id") or "<no-id>")
        if cid in seen_ids:
            rejects.append(f"{cid}: duplicate id within the card")
        seen_ids.add(cid)
        if cid == "<no-id>" or not ID_RE.match(cid):
            rejects.append(f"{cid}: id missing or not REQ-ID/DW-NNN shaped")
        if not (c.get("statement") or "").strip():
            rejects.append(f"{cid}: statement empty")
        # 纪律①
        v = vague_unpinned(c)
        if v:
            rejects.append(f"{cid}: vague quantifier {v} with no numeric threshold — not falsifiable (纪律①)")
        # 纪律② happy needs unhappy twin —— 解析引用,不只查非空(悬空指针/两 happy 互指都要拒)
        et = (c.get("ears_type") or "").strip()
        if et in ("event", "state") and polarity(c.get("then") or c.get("statement")) == 1:
            pw = (c.get("paired_with") or "").strip()
            if not pw:
                rejects.append(f"{cid}: happy {et} clause has no paired_with unhappy twin (纪律②)")
            elif pw not in by_id:
                rejects.append(f"{cid}: paired_with '{pw}' references no existing clause — dangling unhappy twin (纪律②)")
            elif not is_unhappy(by_id[pw]):
                rejects.append(f"{cid}: paired_with '{pw}' is not an unhappy/unwanted twin (points at a happy clause) (纪律②)")
        # threshold provenance flag
        if (c.get("threshold") or "").strip() and not (c.get("threshold_source") or "").strip():
            flags.append(f"{cid}: threshold has no recorded source — confirm it traces to kpi/slo/failure_memory (not air)")
        flags.append(f"{cid}: confirm narrowest-falsifiable-condition + right unhappy edge (judge call) — needs_semantic_review")

    # 纪律③-a 成对矛盾扫描(同 when,相反极性) —— 但 happy/unhappy 孪生句按设计同触发、反极性、
    # 靠前置条件区分,不是矛盾;故排除互为 paired_with 的孪生对。
    paired = set()
    for c in clauses:
        pw = (c.get("paired_with") or "").strip()
        if pw:
            paired.add(frozenset({str(c.get("id")), pw}))
    by_trigger = {}
    for c in clauses:
        key = ((c.get("when") or "").strip().lower(), (c.get("given") or "").strip().lower())
        by_trigger.setdefault(key, []).append(c)
    for key, group in by_trigger.items():
        if key == ("", ""):
            continue
        pos = [str(c.get("id")) for c in group if polarity(c.get("then") or c.get("statement")) == 1]
        neg = [str(c.get("id")) for c in group if polarity(c.get("then") or c.get("statement")) == -1]
        clashing = [(p, n) for p in pos for n in neg if frozenset({p, n}) not in paired]
        if clashing:
            ps = sorted({p for p, _ in clashing})
            ns = sorted({n for _, n in clashing})
            rejects.append(f"suspected contradiction on trigger {key[0]!r}: {ps} (SHALL) vs {ns} (SHALL NOT) — reject, disambiguate (not a declared happy/unhappy pair)")

    # 纪律③-b 覆盖:每条 event happy 必须被一个真实的 unwanted 兄弟覆盖(解析引用,
    # 双向:它自己 paired_with 指向真 unhappy,或某 unwanted 的 paired_with 解析回它)。
    covered_event = set()
    for c in clauses:
        pw = (c.get("paired_with") or "").strip()
        if not pw or pw not in by_id:
            continue
        if is_unhappy(by_id[pw]):                       # happy → resolved unhappy twin
            covered_event.add(str(c.get("id")))
        if is_unhappy(c):                               # unwanted → the happy clause it covers
            covered_event.add(pw)
    for c in clauses:
        if (c.get("ears_type") or "") == "event" and polarity(c.get("then") or c.get("statement")) == 1:
            cid = str(c.get("id"))
            if cid not in covered_event:
                rejects.append(f"{cid}: event happy clause has no resolved unwanted sibling covering it (纪律③ coverage)")
    # 孤儿 unwanted:paired_with 设了却解析不到 → 假配对,拒
    for c in clauses:
        if (c.get("ears_type") or "") == "unwanted":
            pw = (c.get("paired_with") or "").strip()
            if pw and pw not in by_id:
                rejects.append(f"{c.get('id')}: unwanted clause paired_with '{pw}' resolves to nothing — orphan/fake pairing (纪律③ coverage)")

    report = {
        "card": card_path,
        "issue_ref": card.get("issue_ref"),
        "clauses": len(clauses),
        "kicked_to_invariant": len(card.get("kicked_to_invariant") or []),
        "rejects": rejects,
        "needs_semantic_review": flags[:12] + ([f"... +{len(flags) - 12} more"] if len(flags) > 12 else []),
        "exit": "REJECT" if rejects else "MECHANICALLY_CLEAN",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(1 if rejects else 0)


if __name__ == "__main__":
    main()
