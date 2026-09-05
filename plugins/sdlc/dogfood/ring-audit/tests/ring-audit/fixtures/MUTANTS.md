# based_on: REQ-001..004, REQ-006, REQ-008..011

One edit per mutant, applied to `complete.yaml`. Every mutant must make `check_audit.py` exit 1 (mutation.config.yaml names the killing test).

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
| `mutant_required_part_missing_R0-R2-spine.yaml` | REQ-008 (AC-008-b) | R2/issue removed (its gap G-R2-01 is co-filled by donewhen-extract, so no orphan) → required_part_missing |
| `mutant_required_part_missing_R3-R5.yaml` | REQ-009 (AC-009-b) | R3/calibrate removed (G-R3-02 co-filled by spec-compile) → required_part_missing |
| `mutant_required_part_missing_R6.yaml` | REQ-010 (AC-010-b) | R6/meta-judge removed (G-R6-01/02 co-filled) → required_part_missing |
| `mutant_required_part_missing_R7-R8.yaml` | REQ-011 (AC-011-b) | R8/retro removed (G-R8-01 co-filled by tune) → required_part_missing |
| `mutant_orphan_gap.yaml` | REQ-004 (AC-004-a orphan_gaps) | gaps[] gains G-R5-99 (ring R5) that no part fills and that is absent from R5.missing |
| `mutant_rings_without_missing_key.yaml` | REQ-004 (AC-004-a rings_without_missing_key) | R5 has no `missing` key |
| `mutant_human_gate_without_signer.yaml` | REQ-006 (F-13 human Gate 有 signer) | gates[G2] (exercised) has no signer |
| `mutant_delegated_without_authorization_ref.yaml` | REQ-006 (F-13 delegated_agent 附 authorization_ref) | gates[G3] signer_kind delegated_agent without authorization_ref |
| `mutant_script_gate_rendered_as_door.yaml` | REQ-006 (F-13 / F-94 script Gate 不渲染为门) | gates[verify_commit.py] kind script but label 门 |
| `mutant_double_producer.yaml` | REQ-001 (F-13 无双生产者; thresholds.mutation_kill_rate family) | artifacts[] gains a second producer (implement) for cards/CARD-*.yaml without alternatives_of |
