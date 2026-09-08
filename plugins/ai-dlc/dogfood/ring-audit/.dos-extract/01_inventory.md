# Inventory — sdlc

- Project root: `plugins/sdlc`
- Files scanned: 30
- Distinct nouns: 0
- Distinct verbs: 118

---

## Nouns (frequency)

Each noun is shown with its frequency and up to 3 example file paths.
Terms ending in implementation suffixes (Repository, Service, etc.) and
framework primitives have been moved to the `Pruned` section below.

UI-hint flag: `[ui?]` indicates the term may be a UI primitive —
classification must confirm using Judgment 1.


---

## Verbs (frequency)

Verbs that connect business nouns are candidates for `relationships`.
Generic CRUD verbs (`get`, `create`, `update`, `delete`, ...) have been
moved to `Pruned` since they rarely express domain meaning.

- **main** (30) — `skills/commit/scripts/verify_commit.py`, `skills/invariant-extract/scripts/verify_card.py`, `skills/spec-compile/scripts/verify_compile.py`
- **load_yaml** (6) — `skills/tune/scripts/tune.py`, `skills/tune/scripts/apply_proposal.py`, `skills/sdlc/scripts/verify_loop.py`
- **git** (3) — `skills/commit/scripts/verify_commit.py`, `skills/release/scripts/verify_release.py`, `skills/pr/scripts/verify_pr.py`
- **sections** (2) — `skills/pr/scripts/verify_pr.py`, `skills/issue/scripts/verify_issue.py`
- **read_trace** (2) — `skills/tune/scripts/tune.py`, `skills/retro/scripts/metrics.py`
- **escape_rows** (2) — `skills/tune/scripts/tune.py`, `skills/retro/scripts/metrics.py`
- **read** (2) — `skills/tune/scripts/apply_proposal.py`, `skills/psl-derive/scripts/verify_derived.py`
- **col** (2) — `skills/acceptance-spec/scripts/validate_done_when.py`, `skills/test-suite-generator/scripts/check_verbatim_names.py`
- **die** (2) — `skills/sdlc/scripts/trace.py`, `skills/sdlc/scripts/sdlc_state.py`
- **now** (2) — `skills/sdlc/scripts/lock_done_when.py`, `skills/sdlc/scripts/sdlc_state.py`
- **as_list** (2) — `skills/sdlc/scripts/sdlc_state.py`, `skills/sdlc/scripts/verify_graph.py`
- **matches_any** (1) — `skills/commit/scripts/verify_commit.py`
- **glob_match** (1) — `skills/commit/scripts/verify_commit.py`
- **dos_rule_ids** (1) — `skills/invariant-extract/scripts/verify_card.py`
- **has_provenance** (1) — `skills/invariant-extract/scripts/verify_card.py`
- **check_entry** (1) — `skills/invariant-extract/scripts/verify_card.py`
- **check_routed** (1) — `skills/spec-compile/scripts/verify_compile.py`
- **parse_sections** (1) — `skills/psl/scripts/verify_psl.py`
- **body_lines** (1) — `skills/psl/scripts/verify_psl.py`
- **find_section** (1) — `skills/psl/scripts/verify_psl.py`
- **detect_language** (1) — `skills/dos-extract/scripts/inventory.py`
- **is_excluded** (1) — `skills/dos-extract/scripts/inventory.py`
- **iter_source_files** (1) — `skills/dos-extract/scripts/inventory.py`
- **extract_terms** (1) — `skills/dos-extract/scripts/inventory.py`
- **has_impl_suffix** (1) — `skills/dos-extract/scripts/inventory.py`
- **looks_like_ui** (1) — `skills/dos-extract/scripts/inventory.py`
- **format_report** (1) — `skills/dos-extract/scripts/inventory.py`
- **derived_bump** (1) — `skills/release/scripts/verify_release.py`
- **delta** (1) — `skills/release/scripts/verify_release.py`
- **size_class** (1) — `skills/pr/scripts/verify_pr.py`
- **read_json** (1) — `skills/tune/scripts/tune.py`
- **pct** (1) — `skills/tune/scripts/tune.py`
- **per_layer** (1) — `skills/tune/scripts/tune.py`
- **udiff** (1) — `skills/tune/scripts/apply_proposal.py`
- **routing_budget** (1) — `skills/tune/scripts/apply_proposal.py`
- **routing_scalar** (1) — `skills/tune/scripts/apply_proposal.py`
- **pr_poll_env** (1) — `skills/tune/scripts/apply_proposal.py`
- **gate_fix_list** (1) — `skills/tune/scripts/apply_proposal.py`
- **yaml_block** (1) — `skills/issue/scripts/verify_issue.py`
- **kv_lines** (1) — `skills/issue/scripts/verify_issue.py`
- **is_vague** (1) — `skills/issue/scripts/verify_issue.py`
- **psl_ids_and_vocab** (1) — `skills/psl-derive/scripts/verify_derived.py`
- **score** (1) — `skills/spec-gaming-detector/scripts/compute_score.py`
- **trend** (1) — `skills/spec-gaming-detector/scripts/compute_score.py`
- **weight** (1) — `skills/meta-judge/scripts/compute_confidence.py`
- **parse_ts** (1) — `skills/retro/scripts/metrics.py`
- **human_ac_ratio** (1) — `skills/retro/scripts/metrics.py`
- **escape_chains** (1) — `skills/retro/scripts/metrics.py`
- **contract_rework** (1) — `skills/retro/scripts/metrics.py`
- **arg_float** (1) — `skills/calibrate/scripts/verify_calibration.py`
- **locate** (1) — `skills/sdlc/scripts/trace.py`
- **index** (1) — `skills/sdlc/scripts/trace.py`
- **anchor** (1) — `skills/sdlc/scripts/trace.py`
- **matches** (1) — `skills/sdlc/scripts/trace.py`
- **mentions** (1) — `skills/sdlc/scripts/trace.py`
- **fmt** (1) — `skills/sdlc/scripts/trace.py`
- **cmd_why** (1) — `skills/sdlc/scripts/trace.py`
- **back** (1) — `skills/sdlc/scripts/trace.py`
- **cmd_impact** (1) — `skills/sdlc/scripts/trace.py`
- **fwd** (1) — `skills/sdlc/scripts/trace.py`
- **cmd_render** (1) — `skills/sdlc/scripts/trace.py`
- **graph_node_ids** (1) — `skills/sdlc/scripts/trace.py`
- **cmd_lint** (1) — `skills/sdlc/scripts/trace.py`
- **resolve** (1) — `skills/sdlc/scripts/verify_loop.py`
- **sha256** (1) — `skills/sdlc/scripts/lock_done_when.py`
- **cmd_sign** (1) — `skills/sdlc/scripts/lock_done_when.py`
- **staged_files** (1) — `skills/sdlc/scripts/lock_done_when.py`
- **cmd_verify** (1) — `skills/sdlc/scripts/lock_done_when.py`
- **atomic_write** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **resolve_slug** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **paths** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **trace_path** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **next_event_id** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **trace_append** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **ledger_append** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **parse_refs** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **get_path** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **set_path** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **coerce** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **prereqs** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **next_allowed** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_init** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_show** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_set** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_advance** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_gate** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_card** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **load_routing** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **trailing_run** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **detect_oscillation** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_fail** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_report** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_check_clean** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_graph** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **nid** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_loops** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_ledger** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **cmd_archive** (1) — `skills/sdlc/scripts/sdlc_state.py`
- **edge_pairs** (1) — `skills/sdlc/scripts/verify_graph.py`
- **sccs** (1) — `skills/sdlc/scripts/verify_graph.py`
- **strong** (1) — `skills/sdlc/scripts/verify_graph.py`
- **is_dag** (1) — `skills/sdlc/scripts/verify_graph.py`
- **roles_of** (1) — `skills/sdlc/scripts/verify_graph.py`
- **esc** (1) — `skills/test-suite-generator/scripts/gen_existence.py`
- **emit_check** (1) — `skills/test-suite-generator/scripts/gen_existence.py`
- **counts** (1) — `skills/test-suite-generator/scripts/derive_counts.py`
- **contract_names** (1) — `skills/test-suite-generator/scripts/check_verbatim_names.py`
- **collect_text** (1) — `skills/test-suite-generator/scripts/check_verbatim_names.py`
- **glob_dir_prefix** (1) — `skills/plan-cards/scripts/lint_cards.py`
- **path_glob_match** (1) — `skills/plan-cards/scripts/lint_cards.py`
- **patterns_overlap** (1) — `skills/plan-cards/scripts/lint_cards.py`
- **commentable_lines** (1) — `skills/pr-review/scripts/post_review.py`
- **gh** (1) — `skills/pr-review/scripts/post_review.py`
- **vague** (1) — `skills/donewhen-extract/scripts/validate_done_when_v2.py`
- **has_threshold** (1) — `skills/donewhen-extract/scripts/verify_done_when.py`
- **vague_unpinned** (1) — `skills/donewhen-extract/scripts/verify_done_when.py`
- **polarity** (1) — `skills/donewhen-extract/scripts/verify_done_when.py`
- **is_unhappy** (1) — `skills/donewhen-extract/scripts/verify_done_when.py`

---

## Pruned (framework noise)

Terms removed from the active inventory. Listed for transparency so the
user can object if a term was pruned that should be a domain object.

### CRUD verbs

- `load` — generic CRUD/lifecycle verb
- `parse` — generic CRUD/lifecycle verb
- `add` — generic CRUD/lifecycle verb
- `validate` — generic CRUD/lifecycle verb
- `save` — generic CRUD/lifecycle verb
