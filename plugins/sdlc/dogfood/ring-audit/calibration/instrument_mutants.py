"""Mirror ①: mutate the INSTRUMENT (check_audit.py) in a detached worktree; do the 34 L5 tests kill each mutant?"""
import json, re, subprocess, sys, time, pathlib
WT = pathlib.Path(sys.argv[1]); D = WT / "plugins/sdlc/dogfood/ring-audit"; SRC = D / "check_audit.py"
orig = SRC.read_text(encoding="utf-8")
M = [
 ("M01","exit always 0",              'return 1 if predicates else 0', 'return 0'),
 ("M02","ring_missing off",           'report.fail("ring_missing", rid)', 'pass'),
 ("M03","ring_unexpected off",        'report.fail("ring_unexpected", f"{rid} is not one of {\'/\'.join(CANONICAL_RINGS)}")', 'pass'),
 ("M04","parts_missing off",          'report.fail("parts_missing", f"{ring.get(\'id\')}/{part.get(\'id\')} lacks {\',\'.join(absent)}")', 'pass'),
 ("M05","psl_id_missing off",         'report.fail("psl_id_missing", where)', 'pass'),
 ("M06","psl_id_unknown off",         'if unknown:', 'if False:'),
 ("M07","evidence_missing off",       'report.fail("evidence_missing", where)', 'pass'),
 ("M08","evidence_kind enum off",     'if item.get("kind") not in EVIDENCE_KINDS:', 'if False:'),
 ("M09","evidence_ref_empty off",     'if not nonempty_str(item.get("ref")):', 'if False:'),
 ("M10","boolean_implemented off",    'if isinstance(verdict, bool):', 'if False:'),
 ("M11","rename_true off",            'if rename is not False:', 'if False:'),
 ("M12","rings_without_missing_key off", 'if "missing" not in ring:', 'if False:'),
 ("M13","unknown_gap_ref (absent) off",  'report.fail("unknown_gap_ref", f"{where} references {gid}, which is not in gaps[]")', 'pass'),
 ("M14","unknown_gap_ref (cross-ring) off", 'elif gap.get("ring") != ring_id:', 'elif False:'),
 ("M15","overfill_unmarked off",      'if verdict != "overfill":', 'if False:'),
 ("M16","orphan_gap off",             'if gid not in declared.get(gap.get("ring"), set()):', 'if False:'),
 ("M17","double_producer always acknowledged", 'if all(needed_verdict(p) == "merge_candidate" for p in producers):', 'if True:'),
 ("M18","alternatives_of no longer exempts", 'owners = [e for e in entries if not nonempty_str(e.get("alternatives_of"))]', 'owners = list(entries)'),
 ("M19","spurious_merge_candidate off", 'if needed_verdict(pid) == "merge_candidate" and pid not in contested_producers:', 'if False:'),
 ("M20","gate_not_declared off",      'elif kind == "human" and gid not in HUMAN_GATES:', 'elif False:'),
 ("M21","script_gate_rendered_as_door off", 'if gate.get("label") == DOOR:', 'if False:'),
 ("M22","gate_verdict_outside_enum off", 'if verdict not in GATE_VERDICTS:', 'if False:'),
 ("M23","signer required only on pass (pre-08238cd)", 'if verdict != "pending":', 'if verdict == "pass":'),
 ("M24","delegated_without_authorization_ref off", 'if record.get("signer_kind") == "delegated_agent" and not nonempty_str(record.get("authorization_ref")):', 'if False:'),
 ("M25","proposal_without_source off", 'if not nonempty_str(proposal.get("source")):', 'if False:'),
 ("M26","required_part_missing off",  'absent = [name for name in required_parts if name not in pool]', 'absent = []'),
 ("M27","--variant delete-ring no-op", 'doc["rings"] = [r for r in as_list(doc.get("rings")) if as_dict(r).get("id") != dropped]', 'doc["rings"] = as_list(doc.get("rings"))'),
 ("M28","--rings view ignored",       'wanted = selected_rings if selected_rings is not None else CANONICAL_RINGS', 'wanted = CANONICAL_RINGS'),
 ("M29","parts_total off by one",     'report.set("parts_total", len(all_parts))', 'report.set("parts_total", len(all_parts) + 1)'),
 ("M30","rings count off by one",     'report.set("rings", len(rings))', 'report.set("rings", len(rings) - 1)'),
]
res = []
for mid, desc, old, new in M:
    n = orig.count(old)
    if n != 1:
        res.append({"id": mid, "desc": desc, "status": "NOT_APPLIED", "matches": n}); continue
    SRC.write_text(orig.replace(old, new, 1), encoding="utf-8")
    t = time.time()
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(D / "tests/ring-audit"), "-p", "test_*.py"],
                       capture_output=True, text=True, cwd=str(WT))
    fails = re.findall(r"^(?:FAIL|ERROR): (test_\w+)", r.stderr, re.M)
    res.append({"id": mid, "desc": desc, "status": "killed" if r.returncode != 0 else "SURVIVED",
                "killed_by": sorted(set(fails))[:4], "n_failing": len(set(fails)), "secs": round(time.time() - t, 1)})
    print(f"{mid} {res[-1]['status']:8} {desc} ({len(set(fails))} tests)", flush=True)
SRC.write_text(orig, encoding="utf-8")
applied = [x for x in res if x["status"] != "NOT_APPLIED"]
killed = [x for x in applied if x["status"] == "killed"]
summary = {"tool": "hand-rolled instrument mutants (mutmut/cosmic-ray not installed)", "worktree": str(WT),
           "total_mutants": len(applied), "killed": len(killed), "survived": [x["id"] for x in applied if x["status"] == "SURVIVED"],
           "not_applied": [x["id"] for x in res if x["status"] == "NOT_APPLIED"],
           "mutation_score": round(len(killed) / len(applied), 3) if applied else 0.0, "results": res}
json.dump(summary, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: summary[k] for k in ("total_mutants", "killed", "survived", "not_applied", "mutation_score")}))
