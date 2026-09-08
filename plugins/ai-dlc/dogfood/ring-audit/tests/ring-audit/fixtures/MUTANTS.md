# based_on: REQ-001..006, REQ-008..011

One edit per mutant, applied to `complete.yaml` (F-12 read under G1 签字版解释规则 1-3, plus `g1-interpretations.md` rules 4-10 of 2026-09-06). Every mutant must make `check_audit.py` exit 1 (mutation.config.yaml names the killing test and, where the contract or G1 fixed it, the expected predicate token).

Two fixtures need more than one edit, because the shape being tested does not exist in a single line: `mutant_alternatives_of_all_stamped.yaml` (a second producer plus a stamp on each) and `legal_nonexclusive_artifact_ungated.yaml` (a whole artifacts[] record). Each is still one *behaviour* under test.

`legal_*.yaml` files are the other half of the same instrument: variants that must make `check_audit.py` exit **0**. Several G1-interpretation rulings are only decidable with one of these, because the reading being retired and the reading being adopted agree on every rejecting fixture and differ only on what they ACCEPT. They are not mutants and are not scored by `mutation.sh`; they are listed in `mutation.config.yaml` under `accepting_fixtures:` and asserted by name in `test_check_audit.py`.

| file | based_on | edit |
|---|---|---|
| `mutant_ring_missing.yaml` | REQ-001 (AC-001-b) | ring R6 removed → ring_missing |
| `mutant_psl_id_missing.yaml` | REQ-002 (AC-002-b) | R3/calibrate needed.psl_ids = [] → psl_id_missing |
| `mutant_psl_id_unknown.yaml` | REQ-002 (AC-002-a dims_with_unknown_psl_id) | R4/plan-cards naming.psl_ids = [PSL-099] (not in PSL index 001..017) |
| `mutant_evidence_kind_outside_enum.yaml` | REQ-002 (F-01 Evidence enum) | R6/meta-judge implemented.evidence[0].kind = screenshot (enum is file|gate_json|smoke|run_record) |
| `mutant_evidence_ref_empty.yaml` | REQ-002 (F-01 Evidence ref non-empty) | R7/pr needed.evidence[0].ref = '' |
| `mutant_boolean_implemented.yaml` | REQ-003 (AC-003-b) | R4/implement implemented.verdict = true (boolean) → boolean_implemented |
| `mutant_implemented_outside_enum.yaml` | REQ-003 (AC-003-a implemented_outside_enum) | R5/ratchet implemented.verdict = done (enum is declared|compiled|verified) |
| `mutant_rename_true.yaml` | REQ-003 (AC-003-a rename_true) | R8/tune naming.rename = true |
| `mutant_proposal_without_source.yaml` | REQ-004 (AC-004-b) | proposals[P-02] source removed → proposal_without_source |
| `mutant_required_part_missing_R0-R2-spine.yaml` | REQ-008 (AC-008-b) | R2/issue removed (its gap is co-filled by donewhen-extract, so no orphan) → required_part_missing |
| `mutant_required_part_missing_R3-R5.yaml` | REQ-009 (AC-009-b) | R3/calibrate removed (its gap is co-filled by spec-compile) → required_part_missing |
| `mutant_required_part_missing_R6.yaml` | REQ-010 (AC-010-b) | R6/meta-judge removed (both its gaps co-filled) → required_part_missing |
| `mutant_required_part_missing_R7-R8.yaml` | REQ-011 (AC-011-b) | R8/retro removed (its gap is co-filled by tune) → required_part_missing |
| `mutant_orphan_gap.yaml` | REQ-004 (AC-004-a orphan_gaps; rule 2e) | gaps[] gains R5/newly_identified/control/plateau-detection that no part fills and that is absent from R5.missing → orphan_gap |
| `mutant_rings_without_missing_key.yaml` | REQ-004 (AC-004-a rings_without_missing_key) | R5 has no `missing` key |
| `mutant_unknown_gap_ref.yaml` | REQ-004 (AC-004-a; rule 2e) | R5.missing references a gap id that is not in gaps[] → unknown_gap_ref |
| `mutant_overfill_unmarked.yaml` | REQ-004 (AC-004-a; rule 2c) | R3/spec-compile fills = [] while needed.verdict stays necessary (its gap is still filled by calibrate) → overfill_unmarked |
| `mutant_human_gate_without_signer.yaml` | REQ-006 (F-13 human Gate 有 signer; rule 3b) | run_evidence.gates[G2] verdict pass with signer null |
| `mutant_delegated_without_authorization_ref.yaml` | REQ-006 (F-13 delegated_agent 附 authorization_ref; rule 3b) | run_evidence.gates[G2] verdict pass, signer_kind delegated_agent, authorization_ref null |
| `mutant_script_gate_rendered_as_door.yaml` | REQ-006 (F-13 / F-94 script Gate 不渲染为门) | gates[verify_commit.py] kind script but label 门 |
| `mutant_gate_not_declared.yaml` | REQ-006 (F-06 human Gate ∈ {G1,G2,G3}; rule 3d) | gates[] gains human.merge, which is a human_gate Part not a Gate object → gate_not_declared |
| `mutant_double_producer.yaml` | REQ-001 (F-13 无未登记双生产者; rule 1) | artifacts[] gains a second producer (implement) for cards/CARD-*.yaml: no alternatives_of, neither producer merge_candidate → double_producer |
| `mutant_spurious_merge_candidate.yaml` | REQ-001 (rule 1 symmetric face) | R0/psl needed.verdict = merge_candidate although PSL-<feature>.md has a single producer → spurious_merge_candidate |
| `mutant_missing_cross_ring.yaml` | REQ-004 (AC-004-a; interpretation rule 4) | R5.missing declares a Gap that IS in gaps[] but whose ring is R4 → unknown_gap_ref. The branch `mutant_unknown_gap_ref.yaml` never reached (it only removes the id from gaps[] entirely) |
| `mutant_ring_unexpected_R9.yaml` | REQ-001 (AC-001-a rings; interpretation rule 5) | rings[] gains a well-formed R9 outside {R0..R8, spine} → ring_unexpected. Scored twice: with `--rings R6` and without, because the instrument evaluates the ⊇ direction only on the default view |
| `mutant_proposal_source_dangling.yaml` | REQ-004 (AC-004-b; interpretation rule 6) | proposals[] gains P-99 whose `source: A-does-not-exist` is non-empty but resolves to no assessment.id and no gaps[].id → proposal_without_source (same token as the empty-key case, by ruling — the two are told apart in the location suffix) |
| `mutant_alternatives_of_shape.yaml` | REQ-001 (F-05; interpretation rule 7) | artifacts[card diff + commits / agent.card-implementer].alternatives_of = `implement`, not the `stage.<x>` shape → spurious_alternatives_of |
| `mutant_alternatives_of_single_producer.yaml` | REQ-001 (F-05; interpretation rule 7) | artifacts[pull request / pr] gains alternatives_of: stage.pr although that id has one record — nothing to be an alternative of → spurious_alternatives_of |
| `mutant_alternatives_of_all_stamped.yaml` | REQ-001 (F-05; interpretation rule 7) | a real second producer (implement) for cards/CARD-*.yaml AND a stamp on both records: today this drops owners below 2, so double_producer and spurious_merge_candidate both go silent and a genuine contest exits 0 → spurious_alternatives_of |
| `mutant_gate_kind_outside_enum.yaml` | REQ-006 (F-06 / F-94; interpretation rule 8) | gates[] gains `{id: verify_x.py, kind: shell, label: 门}` and `{id: G4, label: 门}` (no kind key) → gate_kind_outside_enum on both, and each must still be convicted by the script rule (label 门) and the human rule (id ∉ G1/G2/G3) |
| `mutant_disposition_outside_enum.yaml` | REQ-005 (F-16; interpretation rule 9) | R0/psl assessment.disposition = escalate, outside {fix_list, issue, none} → disposition_outside_enum |
| `mutant_misfit_disposition_fix_list.yaml` | REQ-005 (F-16 后半; interpretation rule 9) | R8/tune has naming.fit misfit and disposition fix_list; a misfit may dispose only to issue or none → misfit_disposition_outside_enum |
| `mutant_implemented_above_gate_cap.yaml` | REQ-003 (F-06; interpretation rule 10) | R8/tune claims implemented.verdict compiled while its exclusive Artifact has checked_by: [] → implemented_above_gate_cap. The mf-009 record as it stood before G3 ruled it back to declared |
| `mutant_exclusive_artifact_unregistered.yaml` | REQ-003 (F-06; interpretation rule 10) | R0/psl.artifact = dos.yaml — an id that exists in artifacts[] but under producer dos-extract, so no (id, producer) record answers for psl → exclusive_artifact_unregistered |

## Accepting fixtures (`legal_*.yaml`) — must exit 0

| file | based_on | edit | what it rules out |
|---|---|---|---|
| `legal_cross_ring_fills.yaml` | REQ-004 (AC-004-a; interpretation rule 4) | spine/sdlc also fills the R4 Gap `R4/newly_identified/control/commit-pregate`, still co-filled by its own ring so absent from R4.missing | the over-strict reading that shares one same-ring resolve() between `missing[]` and `fills[]`, under which a correctly recorded audit cannot pass its own check script |
| `legal_disposition_fix_list_assessment.yaml` | REQ-005 (F-16; interpretation rule 9) | R0/psl assessment.disposition = fix_list | compiling `audit.schema.md`'s two-value projection `{none, issue}` instead of 签字版 F-16's three, which rejects a value F-16 allows |
| `legal_disposition_fix_list_gap.yaml` | REQ-005 (F-16; interpretation rule 9) | gaps[R8/newly_identified/knowledge/escape-to-rule].disposition = fix_list | the same narrowing on the Gap side of the field |
| `legal_nonexclusive_artifact_ungated.yaml` | REQ-003 (F-06; interpretation rule 10) | artifacts[] gains a NON-exclusive record decisions.md / dos-extract / checked_by: [], while dos-extract's exclusive dos.yaml keeps verify_dos.py and its verdict stays compiled | the "any artifacts[] row this Part produces" reading of 独占, which demotes dos-extract — the Part G3 named as the one that must not be demoted. Without this fixture that reading passes the whole suite in silence |
