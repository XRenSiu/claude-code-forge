#!/usr/bin/env python3
"""
check_audit.py — the mechanical gate over `audit.yaml`, the machine-readable half of the ring audit.

AUDIT.md is a projection of audit.yaml; this script is the only thing allowed to say whether the audit is
complete.  The auditor may not declare completion in prose — the exit code says it (F-13, PSL-006).

Usage:
  check_audit.py <audit.yaml> [--psl PSL.md] [--rings R0,R1,..] [--required-parts a,b,..]
                 [--variant delete-ring:<id>]

Exit 0 iff every F-13 (+ F-17) predicate holds, read under G1 签字版解释规则 1-3 (g1-record.md, 2026-09-05).
Predicate → the token printed in `error` / `errors` / `failed_predicates`:

  Ring set = {R0..R8, spine}; with --rings only the listed rings must attend      ring_missing
                                                                                 ring_unexpected
  every Part carries all three assessment dimensions                             parts_missing
  every dimension has non-empty psl_ids …                                        psl_id_missing
  … all of them in the PSL 规律索引 (checked only when --psl is given)             psl_id_unknown
  every dimension has non-empty evidence, each entry kind ∈ {file, gate_json,     evidence_missing
  smoke, run_record} with a non-empty ref                                        evidence_kind_outside_enum
                                                                                 evidence_ref_empty
  implemented.verdict ∈ {declared, compiled, verified}, never a boolean           boolean_implemented
  ("已实现 ✓" is forbidden — PSL-010 三态)                                          implemented_outside_enum
  naming.rename is the constant false (建议不等于重命名 — PSL-014)                  rename_true
  every Ring carries a `missing` key (an empty list answers; an absent key is     rings_without_missing_key
  silence — PSL-017)
  rule 2  every id in rings[].missing[] and parts[].fills[] exists in gaps[]      unknown_gap_ref
          with the same ring
          a Gap nobody fills that is absent from its ring's missing               orphan_gap
          fills == [] ⇒ needed.verdict must be overfill (填零缺口 = 过填 — PSL-002)  overfill_unmarked
  rule 1  ≥2 producers of one Artifact id are legal iff `alternatives_of` is set  double_producer
          (同阶段的条件替代不算争) or every producer's needed.verdict is
          merge_candidate (PSL-001); and merge_candidate is only for a producer   spurious_merge_candidate
          that really is an unexempted double producer
  rule 3  human Gate objects in gates[] are only G1 / G2 / G3 — merge and         gate_not_declared
          harness-review are human_gate PARTS, not Gates
          no script Gate is rendered as a 门 (闸 is not a 门 — PSL-006)             script_gate_rendered_as_door
          run_evidence.gates[] verdict ∈ {pending, pass, reject, waived}          gate_verdict_outside_enum
          pass/reject/waived need signer + signer_kind (pending may be null)      human_gate_without_signer
          a delegated_agent signer needs an authorization_ref (代签须有授权记录)     delegated_without_authorization_ref
  every Proposal names a source Assessment or Gap                                proposal_without_source
  with --required-parts: every named Part attends the selected Rings (F-17)      required_part_missing

Exit 1 = at least one predicate failed.  Exit 2 = the input could not be read.

--variant delete-ring:<id> deletes that Ring in memory before checking.  F-14: an exit 0 on the report is
evidence only when the same run recorded an exit 1 on a delete-ring twin; an exit 0 without that twin is
`uncalibrated` and must not be used as evidence.

--rings limits the VIEW: which Rings must attend, which Parts feed parts_without_assessment, and where
--required-parts is looked up.  It narrows no other predicate (F-17: 不改任何既有谓词) — the dimension,
gap, artifact, gate and proposal predicates always read the whole document.
"""
import argparse
import json
import re
import sys

CANONICAL_RINGS = ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "spine"]
DIMENSIONS = ("needed", "implemented", "naming")
EVIDENCE_KINDS = {"file", "gate_json", "smoke", "run_record"}
IMPLEMENTED_VERDICTS = {"declared", "compiled", "verified"}
HUMAN_GATES = {"G1", "G2", "G3"}                 # rule 3d — merge / harness-review are Parts, not Gates
GATE_VERDICTS = {"pending", "pass", "reject", "waived"}
SIGNED_VERDICTS = {"pass", "reject", "waived"}   # pending may still carry nulls
DOOR = "门"                                       # the rendered word reserved for human gates
PSL_ID_RE = re.compile(r"\bPSL-\d+\b")


def die(msg):
    sys.stderr.write(f"check_audit: {msg}\n")
    sys.exit(2)


def load_yaml(path, what):
    try:
        import yaml
    except ImportError:
        die("pyyaml is required (pip install pyyaml)")
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except FileNotFoundError:
        die(f"cannot read {what}: {path} does not exist")
    except Exception as exc:                     # unparseable YAML is unreadable input, not a failed predicate
        die(f"cannot read {what}: {path}: {exc}")


def load_psl_index(path):
    """The closed set of PSL ids the audit may cite: the `- PSL-NNN …` entries of the 规律索引 section."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except FileNotFoundError:
        die(f"cannot read PSL: {path} does not exist")
    except Exception as exc:
        die(f"cannot read PSL: {path}: {exc}")
    ids, in_index = set(), False
    for line in text.splitlines():
        if line.startswith("#"):
            if in_index:
                break                            # the next heading closes the index
            in_index = "规律索引" in line
            continue
        if in_index:
            m = re.match(r"^\s*[-*]\s*(PSL-\d+)\b", line)
            if m:
                ids.add(m.group(1))
    if not ids:                                  # no index section: fall back to every id the PSL mentions
        ids = set(PSL_ID_RE.findall(text))
    return ids


def as_list(value):
    return value if isinstance(value, list) else []


def as_dict(value):
    return value if isinstance(value, dict) else {}


def nonempty_str(value):
    return isinstance(value, str) and value.strip() != ""


class Report:
    """Counts + failed predicates.  A predicate token is always the first word of an error string."""

    def __init__(self):
        self.counts = {}
        self.errors = []

    def bump(self, key, delta=1):
        self.counts[key] = self.counts.get(key, 0) + delta

    def set(self, key, value):
        self.counts[key] = value

    def fail(self, predicate, location=""):
        self.errors.append(f"{predicate}: {location}" if location else predicate)

    def predicates(self):
        seen = []
        for e in self.errors:
            name = e.split(":", 1)[0]
            if name not in seen:
                seen.append(name)
        return seen


def check_rings(doc, selected_rings, report):
    """Ring attendance (F-13) + the view --rings selects (F-17).  Returns (all rings, viewed rings)."""
    rings = [as_dict(r) for r in as_list(doc.get("rings"))]
    by_id = {}
    for ring in rings:
        rid = ring.get("id")
        if nonempty_str(rid):
            by_id.setdefault(rid, ring)
    report.set("rings", len(rings))

    wanted = selected_rings if selected_rings is not None else CANONICAL_RINGS
    for rid in wanted:
        if rid not in by_id:
            report.fail("ring_missing", rid)
    if selected_rings is None:
        for rid in by_id:
            if rid not in CANONICAL_RINGS:
                report.fail("ring_unexpected", f"{rid} is not one of {'/'.join(CANONICAL_RINGS)}")

    return rings, [by_id[r] for r in wanted if r in by_id]


def check_parts(rings, view, report):
    """Three dimensions per Part, psl_ids and evidence per dimension, the implemented three-state, rename."""
    all_parts = [(ring.get("id"), as_dict(p)) for ring in rings for p in as_list(ring.get("parts"))]
    report.set("parts_total", len(all_parts))

    view_part_ids, parts_without_assessment = set(), 0
    for ring in view:
        for part in as_list(ring.get("parts")):
            part = as_dict(part)
            if nonempty_str(part.get("id")):
                view_part_ids.add(part["id"])
            assessment = as_dict(part.get("assessment"))
            absent = [d for d in DIMENSIONS if not isinstance(assessment.get(d), dict)]
            if absent:
                parts_without_assessment += 1
                report.fail("parts_missing", f"{ring.get('id')}/{part.get('id')} lacks {','.join(absent)}")
    report.set("parts_without_assessment", parts_without_assessment)
    return all_parts, view_part_ids


def check_dimensions(all_parts, psl_ids, report):
    for key in ("dims_without_psl_id", "dims_with_unknown_psl_id", "dims_without_evidence",
                "evidence_kind_outside_enum", "evidence_ref_empty",
                "boolean_implemented", "implemented_outside_enum", "rename_true"):
        report.set(key, 0)

    for rid, part in all_parts:
        pid = part.get("id")
        assessment = as_dict(part.get("assessment"))

        for dim in DIMENSIONS:
            body = as_dict(assessment.get(dim))
            where = f"{rid}/{pid}.{dim}"

            ids = [i for i in as_list(body.get("psl_ids")) if nonempty_str(i)]
            if not ids:
                report.bump("dims_without_psl_id")
                report.fail("psl_id_missing", where)
            elif psl_ids:
                unknown = [i for i in ids if i not in psl_ids]
                if unknown:
                    report.bump("dims_with_unknown_psl_id")
                    report.fail("psl_id_unknown", f"{where} cites {','.join(unknown)}")

            evidence = as_list(body.get("evidence"))
            if not evidence:
                report.bump("dims_without_evidence")
                report.fail("evidence_missing", where)
            for n, item in enumerate(evidence):
                item = as_dict(item)
                if item.get("kind") not in EVIDENCE_KINDS:
                    report.bump("evidence_kind_outside_enum")
                    report.fail("evidence_kind_outside_enum", f"{where}[{n}] kind={item.get('kind')!r}")
                if not nonempty_str(item.get("ref")):
                    report.bump("evidence_ref_empty")
                    report.fail("evidence_ref_empty", f"{where}[{n}]")

        # 已实现 is a three-state, never a boolean (PSL-010)
        if "implemented" in assessment:
            verdict = as_dict(assessment.get("implemented")).get("verdict")
            if isinstance(verdict, bool):
                report.bump("boolean_implemented")
                report.fail("boolean_implemented", f"{rid}/{pid} verdict={verdict}")
            elif verdict not in IMPLEMENTED_VERDICTS:
                report.bump("implemented_outside_enum")
                report.fail("implemented_outside_enum", f"{rid}/{pid} verdict={verdict!r}")

        # a naming suggestion is not a rename (PSL-014)
        if "naming" in assessment:
            rename = as_dict(assessment.get("naming")).get("rename")
            if rename is not False:
                report.bump("rename_true")
                report.fail("rename_true", f"{rid}/{pid} rename={rename!r}")


def check_gaps(doc, rings, all_parts, report):
    """Rule 2: gaps[] is the registry, parts[].fills[] the FILLS edge, rings[].missing[] the declared blanks."""
    gaps = {}
    for gap in as_list(doc.get("gaps")):
        gap = as_dict(gap)
        if nonempty_str(gap.get("id")):
            gaps.setdefault(gap["id"], gap)

    unknown_refs = 0

    def resolve(gid, ring_id, where):
        """A gap reference must name a gaps[] entry that sits in the same ring (rule 2e)."""
        nonlocal unknown_refs
        gap = gaps.get(gid)
        if gap is None:
            unknown_refs += 1
            report.fail("unknown_gap_ref", f"{where} references {gid}, which is not in gaps[]")
        elif gap.get("ring") != ring_id:
            unknown_refs += 1
            report.fail("unknown_gap_ref", f"{where} references {gid}, whose ring is {gap.get('ring')!r}")
        return gap

    # FILLS edges + 过填 (a Part that fills no Gap must say so — PSL-002)
    overfill_unmarked = 0
    filled = set()
    for rid, part in all_parts:
        pid = part.get("id")
        fills = as_list(part.get("fills"))
        for gid in fills:
            filled.add(gid)
            resolve(gid, rid, f"{rid}/{pid}.fills")
        if not fills and as_dict(part.get("assessment")).get("needed") is not None:
            verdict = as_dict(as_dict(part["assessment"]).get("needed")).get("verdict")
            if verdict != "overfill":
                overfill_unmarked += 1
                report.fail("overfill_unmarked", f"{rid}/{pid} fills no Gap but needed.verdict={verdict!r}")
    report.set("overfill_unmarked", overfill_unmarked)

    # declared blanks
    declared = {}
    without_missing_key = 0
    for ring in rings:
        rid = ring.get("id")
        if "missing" not in ring:
            without_missing_key += 1
            report.fail("rings_without_missing_key", str(rid))
            declared[rid] = set()
            continue
        ids = set()
        for gid in as_list(ring.get("missing")):
            if not nonempty_str(gid):
                continue
            ids.add(gid)
            resolve(gid, rid, f"{rid}.missing")
        declared[rid] = ids
    report.set("rings_without_missing_key", without_missing_key)
    report.set("unknown_gap_refs", unknown_refs)

    # 空白诚实登记：a Gap nobody fills must be declared missing by its ring (PSL-017)
    orphans = 0
    for gid, gap in gaps.items():
        if gid in filled:
            continue
        if gid not in declared.get(gap.get("ring"), set()):
            orphans += 1
            report.fail("orphan_gap", f"{gid} has no FILLS edge and is not in {gap.get('ring')}.missing")
    report.set("orphan_gaps", orphans)


def check_artifacts(doc, all_parts, report):
    """Rule 1: 一个产物只有一个生产者 (PSL-001), unless the second is acknowledged."""
    part_by_id = {}
    for _, part in all_parts:
        if nonempty_str(part.get("id")):
            part_by_id.setdefault(part["id"], part)

    def needed_verdict(producer):
        return as_dict(as_dict(as_dict(part_by_id.get(producer)).get("assessment")).get("needed")).get("verdict")

    grouped = {}
    for entry in as_list(doc.get("artifacts")):
        entry = as_dict(entry)
        grouped.setdefault(entry.get("id"), []).append(entry)

    doubles, contested_producers = 0, set()
    for aid, entries in grouped.items():
        owners = [e for e in entries if not nonempty_str(e.get("alternatives_of"))]
        if len(owners) < 2:
            continue                              # 同阶段的条件替代分支不算争
        producers = [e.get("producer") for e in owners]
        contested_producers.update(p for p in producers if nonempty_str(p))
        if all(needed_verdict(p) == "merge_candidate" for p in producers):
            continue                              # 两个配件争同一产物，都认领为合并候选 = 已登记
        doubles += 1
        report.fail("double_producer", f"{aid} is produced by {', '.join(str(p) for p in producers)}"
                                       " with neither alternatives_of nor merge_candidate on every producer")
    report.set("double_producer", doubles)

    # the symmetric face: merge_candidate only means something on a real, unexempted double producer
    spurious = 0
    for rid, part in all_parts:
        pid = part.get("id")
        if needed_verdict(pid) == "merge_candidate" and pid not in contested_producers:
            spurious += 1
            report.fail("spurious_merge_candidate",
                        f"{rid}/{pid} claims merge_candidate but produces no contested Artifact")
    report.set("spurious_merge_candidate", spurious)


def check_gates(doc, report):
    """Rule 3: gates[] is the design view (门 / 闸); run_evidence.gates[] carries the F-07 signer triplet."""
    for key in ("gates_not_declared", "script_gates_rendered_as_door",
                "gate_verdict_outside_enum", "human_gates_without_signer",
                "delegated_without_authorization_ref"):
        report.set(key, 0)

    for gate in as_list(doc.get("gates")):
        gate = as_dict(gate)
        gid, kind = gate.get("id"), gate.get("kind")
        if kind == "script":
            if gate.get("label") == DOOR:
                report.bump("script_gates_rendered_as_door")
                report.fail("script_gate_rendered_as_door", f"{gid} is a script rendered as {DOOR}")
        elif kind == "human" and gid not in HUMAN_GATES:
            report.bump("gates_not_declared")
            report.fail("gate_not_declared", f"{gid} is not one of {'/'.join(sorted(HUMAN_GATES))}"
                                             " — merge and harness-review are human_gate Parts, not Gates")

    for record in as_list(as_dict(doc.get("run_evidence")).get("gates")):
        record = as_dict(record)
        gid, verdict = record.get("gate"), record.get("verdict")
        if verdict not in GATE_VERDICTS:
            report.bump("gate_verdict_outside_enum")
            report.fail("gate_verdict_outside_enum", f"run_evidence.gates[{gid}] verdict={verdict!r}")
        if verdict in SIGNED_VERDICTS:
            absent = [f for f in ("signer", "signer_kind") if not nonempty_str(record.get(f))]
            if absent:
                report.bump("human_gates_without_signer")
                report.fail("human_gate_without_signer",
                            f"run_evidence.gates[{gid}] is {verdict} with no {' and no '.join(absent)}")
        if record.get("signer_kind") == "delegated_agent" and not nonempty_str(record.get("authorization_ref")):
            report.bump("delegated_without_authorization_ref")
            report.fail("delegated_without_authorization_ref",
                        f"run_evidence.gates[{gid}] is signed by a delegated_agent with no authorization_ref")


def check_proposals(doc, report):
    """补的理由只能是一个已识别的 Gap 或 Assessment (DP-2)."""
    without_source = 0
    for proposal in as_list(doc.get("proposals")):
        proposal = as_dict(proposal)
        if not nonempty_str(proposal.get("source")):
            without_source += 1
            report.fail("proposal_without_source", str(proposal.get("id")))
    report.set("proposals_without_source", without_source)


def check_required_parts(required_parts, selected_rings, view_part_ids, all_parts, report):
    """F-17: the Parts a given ring group must field."""
    if required_parts is None:
        report.set("required_parts_missing", 0)
        return
    pool = view_part_ids if selected_rings is not None else {p.get("id") for _, p in all_parts}
    absent = [name for name in required_parts if name not in pool]
    report.set("required_parts_missing", len(absent))
    scope = ",".join(selected_rings) if selected_rings is not None else "any ring"
    for name in absent:
        report.fail("required_part_missing", f"{name} is not a Part of {scope}")


def check(doc, psl_ids, selected_rings, required_parts, report):
    rings, view = check_rings(doc, selected_rings, report)
    all_parts, view_part_ids = check_parts(rings, view, report)
    check_dimensions(all_parts, psl_ids, report)
    check_gaps(doc, rings, all_parts, report)
    check_artifacts(doc, all_parts, report)
    check_gates(doc, report)
    check_proposals(doc, report)
    check_required_parts(required_parts, selected_rings, view_part_ids, all_parts, report)

    # F-14, reported and never gated: is this exit code usable as evidence at all?
    runs = as_list(as_dict(doc.get("run_evidence")).get("check_runs"))
    report.set("calibration_twin_recorded",
               any("delete-ring" in str(as_dict(r).get("cmd")) and as_dict(r).get("exit") == 1 for r in runs))


def split_csv(value):
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audit", help="path to audit.yaml")
    ap.add_argument("--psl", help="PSL-<feature>.md — its 规律索引 is the closed set of citable psl_ids")
    ap.add_argument("--rings", help="comma-separated ring ids to view (default: R0..R8,spine)")
    ap.add_argument("--required-parts", help="comma-separated Part names that must attend the view")
    ap.add_argument("--variant", help="delete-ring:<id> — drop that ring in memory, then check (F-14)")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    doc = load_yaml(args.audit, "audit")
    if not isinstance(doc, dict):
        die(f"cannot read audit: {args.audit} is not a YAML mapping")

    psl_ids = load_psl_index(args.psl) if args.psl else set()
    selected_rings = split_csv(args.rings) if args.rings else None
    required_parts = split_csv(args.required_parts) if args.required_parts else None

    if args.variant:
        if not args.variant.startswith("delete-ring:"):
            die(f"unknown --variant {args.variant!r} (supported: delete-ring:<id>)")
        dropped = args.variant.split(":", 1)[1].strip()
        doc = dict(doc)
        doc["rings"] = [r for r in as_list(doc.get("rings")) if as_dict(r).get("id") != dropped]

    report = Report()
    check(doc, psl_ids, selected_rings, required_parts, report)

    predicates = report.predicates()
    out = dict(report.counts)
    out.update({
        "audit": args.audit,
        "psl": args.psl,
        "psl_index_size": len(psl_ids),
        "rings_viewed": selected_rings if selected_rings is not None else CANONICAL_RINGS,
        "variant": args.variant,
        "ok": not predicates,
        "error": report.errors[0] if report.errors else None,
        "errors": report.errors,
        "failed_predicates": predicates,
    })
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if predicates else 0


if __name__ == "__main__":
    sys.exit(main())
