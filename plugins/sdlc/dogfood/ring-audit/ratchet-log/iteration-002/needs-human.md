# needs-human.md — iteration-002 (sdlc-ring-audit)

> /meta-judge state_decision = NEEDS_HUMAN（rule 3：human AC）。以下问题**逐字**取自 meta-judge-output.yaml#needs_human_items。
> 路由：nh-001 / nh-002（human AC）→ G3；其余 → g2-judge（契约签字人）。解码：gaming 4.0 > 先例上界 3.5，且修复轮自身引入 2 条新发现，先例不直接适用，交 g2-judge。

- meta-judge: NEEDS_HUMAN · merged 20 · blocking [] · non-blocking P1 [('mf-001', 0.8), ('mf-003', 0.4), ('mf-004', 0.4), ('mf-005', 0.4), ('mf-006', 0.4), ('mf-007', 0.4)] · recurrences of iteration-001: 7 ['mf-001', 'mf-005', 'mf-006', 'mf-009', 'mf-010', 'mf-011', 'mf-013']
- spec-gaming-detector: 4.0 (iteration-001: 3.5; trend +0.5; < 7, not +2) · spec_robustness_gaps 6
- qa GO 0 regressions · pm 8/1/0/2 block_merge false · perf 0 · drift 11 signals (2 new medium) · 2 findings introduced by the fix commits (audit.yaml exit:1 vs ok:true; replay empty-range crash)

## nh-001  ·  blocking: True  ·  route: G3

```yaml
item_id: nh-001
question: 'AC-005-a (REQ-005, kind human, judge tech, ui:AUDIT.md#ring-tables): do the ring tables satisfy the statement
  — per-Part Gap atoms / exclusive Artifact or role / 闸-vs-门 / Loop; deletion tests naming a concrete error artifact
  (not 流程会断); provenance-then-fit naming with 建议名 + 不重命名 on misfit; the two named duplicate pairs adjudicated; per-ring
  missing rows with source / necessity / deletion? Mechanical support registered by pm-reviewer (script_gates_rendered_as_door
  0, rename_true 0, orphan_gaps 0, 0 grep hits for generic deletion phrases, 不重命名 ×13, 33 missing rows with source
  tag + necessity + deletion sentence, both contract-named pairs present among five recomputed pairs, 门 cells only
  for G1/G2/G3, AUDIT.md byte-identical to a fresh render) and by spec-gaming-detector (deletion_test: 0 empty /
  0 banned phrases / 0 near-duplicates, min length 102 chars; naming 41 fits / 1 misfit tune → harness-tune rename
  false; provenance 23 authored / 19 adopted; 41/42 written fit_reason; 18/42 naming dims cite only provenance-type
  evidence) — but the quality judgment is G3''s. NEW this iteration and squarely inside this AC: mf-009 (confidence
  0.8) — the checked_by column the fix added now prints ''（无闸 → 封顶 declared）'' beside **compiled** for R6/human_gate.G3,
  R7/agent.pr-reviewer, R8/tune (every artifact checked_by []) and for 21 cells in total across 5 producers; spec-drift-detector
  notes human_gate.G3 and review-loop record no deviating reading at all; the registries part.gates and artifacts[].checked_by
  disagree for 8/42 Parts. G3 must rule whether F-06''s ''any artifact'' wording or the fragments'' ''exclusive/primary
  artifact'' reading governs (g3-input.md item 1 covers only the dos-extract partial case). Also read: mf-013 (duplicates
  table is author-controlled: any non-empty alternatives_of exempts a producer), mf-006 (the 缺口·原子 column is an
  unescaped interpolation site — delivered content clean), mf-014 (a gates[] entry with kind outside script|human
  renders ''未在 gates[] 登记'' though registered — delivered gates[] clean), mf-010 (the checker forbids cross-ring
  fills, so no Part in another ring can be recorded as filling a Gap — 0 such edges today).'
surfaced_by: rule_index 3 / pm-reviewer REQ-005; mf-009 (confidence 0.8)
blocking: true
suggested_resolver: 'G3 tech judge — checklist: plugins/sdlc/dogfood/ring-audit/tests/ring-audit/checklist_G3.md
  L9-24 (14 boxes); evidence: AUDIT.md L26-852 (ring tables; R6 L382-410, tune L686), L832-852 (疑似重复的 Part 对); g3-input.md
  item 1 (F-06 granularity); audit.yaml L1348 / L1624 / L1860 + artifacts L3081 / L3088 / L3096'
```

## nh-002  ·  blocking: True  ·  route: G3

```yaml
item_id: nh-002
question: 'AC-006-a (REQ-006, kind human, judge product, ui:AUDIT.md#run-evidence): (1) mf-001 (0.8) — the re-recorded
  replay snapshot names branch fix/iter-002 @ 9ad5b9c and lists 9ad5b9c as CARD-01; that sha is not reachable from
  docs/1-sdlc-ring-audit (patch-id twin of 7cb1f55) and the record says 12 Card commits where the branch has 13.
  The snapshot_note discloses sha_scope: branch-specific and says ''do not copy this table''. pm-reviewer calls
  the disclosure honest and says re-running on this branch and pasting the output would make the table self-consistent
  (CARD-06 doc-only); spec-gaming- detector calls it disclaimer_in_place_of_fix, a recurrence of the iteration-001
  stale-sha class after a fix that claimed to cure it, and a breach of the g2-judge no-cherry-pick ruling quoted
  in pr-body.md L116. Does a disclosed-but-unresolvable table satisfy ''列出 Card-footer 提交对三个被审目录的 git diff --stat
  记录（为空）''? All reviewers agree the load-bearing empty diff-stat reproduces at ba7d5e2. (2) mf-002 (1.0, three roles
  + qa caveat) — the same block records exit: 1 beside ok: true / 0 touching / 0 rejected, a combination replay_card_commits.sh
  cannot emit; the exit key was introduced by the fix commit ba7d5e2 and F-12 makes the yaml authoritative, so the
  truth source contradicts itself; mf-012 shows the renderer never projects cmd/exit, so the page shows only ok:
  true. pm-reviewer: ''the one item in this review that a CARD-06 doc-only refresh could remove before G3 reads
  the page.'' (3) ''signer_kind = delegated_agent 的门不渲染为人签'': the closed SIGNER_KIND_RENDER map renders 代签（delegated）
  for G1/G2, — for pending G3, **未知** for anything else (pm, gaming verified on a ''人签'' variant); mf-007 shows
  the checker still accepts signer_kind values outside {human, delegated_agent} without authorization_ref (KG-04).
  (4) mf-005 — AUDIT.md''s PSL-003 section answers A8 ''审计动过被审目录吗'' only for the Card window (自第一个 Card 提交起); three
  footer-less same-Run commits before it (587f371, ebe270d, c729f76 — c729f76 edited verify_commit.py, the replay''s
  oracle) touched plugins/sdlc/skills/** and are visible only in commit-table.md / pr-body.md, which classify them
  as PSL γ L122-123 deviation commits. (5) mf-003 — AUDIT.md tells readers ''换分支或 rebase 之后必须重跑''; on an empty main..HEAD
  range (after merge) the fixed script aborts with no JSON. (6) substitute-tier external evidence: pm and gaming
  both report it rendered as substitute, never as user verification; calibration wording never says unqualified
  ''calibrated''; 0 **verified** cells. Reviewer-derived recommendation: G3 should re-run check_audit.py, the delete-ring
  variant and replay_card_commits.sh on the shipped branch rather than trust the typed record (gaming, pm, drift,
  qa all did: exit 0 / 13 / 0 / 0; twin exit 1 ring_missing: R6).'
surfaced_by: rule_index 3 / pm-reviewer REQ-006; mf-001 (0.8), mf-002 (1.0)
blocking: true
suggested_resolver: 'G3 product judge — checklist: tests/ring-audit/checklist_G3.md L26-40 (11 boxes); evidence:
  AUDIT.md L912-1046 (run_evidence; gates table L926-935, PSL-003 replay L961-998), audit.yaml L3366-3447 (run_evidence;
  audited_dirs_diff L3412-3440); independent re-run of check_audit.py (exit 0) + --variant delete-ring:R6 (exit
  1) + replay_card_commits.sh on docs/1-sdlc-ring-audit. Orchestrator option before G3 reads: regenerate run_evidence.audited_dirs_diff
  on the shipping branch as the last commit (pm-reviewer / spec-gaming-detector suggested fix) — note gaming''s
  warning that another disclaimer instead of a resolving record ''should be read as convergence on gaming''.'
```

## nh-003  ·  blocking: False  ·  route: g2-judge

```yaml
item_id: nh-003
question: 'Contract / interpretation questions the spec-drift-detector (first real run) routes needs_human because
  likely_intentional is unclear and both sides were written in the same commit (0be2770): mf-008 (0.8, new, unregistered)
  — does --rings legitimately disable ring_unexpected and narrow ring_missing, or does F-17 ''不改任何既有谓词'' bind (check_audit.py
  docstring says one thing, audit.schema.md:26-28 the other)? mf-015 — must the six registries be present (schema.md
  ''缺一不可'') when neither F-13 nor the code requires it? mf-016 — must exit-2 paths emit a JSON object (schema.md
  ''恒为一个 JSON 对象'')? mf-020 — is the disposition enum {fix_list, issue, none} (F-16) or {none, issue} (schema.md)?
  mf-011 (KG-02) — which of the three readings of ''lacking a source'' does AC-004-b compile (already routed to
  change-proposal-002). Plus the four update_spec recommendations for the same proposal: mf-010 (rule 2(e) fills[]
  same-ring — three downstream readers agree against the signed sentence), mf-017 (eight registries vs six; assembly
  notes omit unenforced_rules), mf-018 (whitelist_overflow vs replay_reject tokens), mf-019 (schema.md:11-14 describes
  a CARD-01 state 5a6889c removed). The spec-side files (g1-record.md, derived/form-draft.md, done_when.yaml) are
  constraints.forbidden_paths for this Run, so none of these can be settled inside the Card range.'
surfaced_by: mf-008; spec-drift-detector recommendations (needs_human ×6 incl. SD-03 → nh-001 and SD-01 → nh-002;
  update_spec ×4)
blocking: false
suggested_resolver: contract author via change-proposal-002 (+ G1 interpretation line where the signed form is the
  side to change); /spec-drift-detector at iteration 3 to confirm closure
```

## nh-004  ·  blocking: False  ·  route: g2-judge

```yaml
item_id: nh-004
question: 'Test-coverage of the iteration-002 fixes: none of the six in-contract fixes has a locked test — cell()/code()
  escaping, the closed SIGNER_KIND_RENDER map, the checked_by column, --no-renames, the non_card_commits_* fields,
  the computed assembly-note counts all live outside tests/** (pm-reviewer out_of_scope_observations[3]); render_audit.py
  has no test at all and existence.sh checks structure only (qa-reviewer caveats.other[0], who closed the gap by
  hand this iteration with a byte-diff of a fresh render). mf-003 (regression in the fixed replay script) sits exactly
  in that untested surface, and mf-004 / mf-006 / mf-014 each name a fixture that would pin them. Should change-proposal-002
  reopen the l5 lock to add: a golden-file byte-diff for AUDIT.md; fixture values containing ''|'' (atoms, ids);
  signer_kind ''人签'' / ''agent'' mutants; a twin repo with a file renamed out of and a non-ASCII file added under
  plugins/sdlc/skills/; an empty main..HEAD range expecting exit 0 + card_commits 0; a gates[] entry with kind:
  human_gate?'
surfaced_by: pm-reviewer out_of_scope_observations[3]; qa-reviewer caveats.other[0]; mf-003, mf-004, mf-006, mf-014
blocking: false
suggested_resolver: /test-suite-generator + /calibrate via change-proposal-002 (l5 lock re-sign); /qa-reviewer at
  iteration 3
```

## Orchestrator's candidate fix round (fix-prompt.md, 6 in-contract bullets) — pending g2-judge decode
- replay empty-range guard · core.quotePath · non-Card pass over merge-base..HEAD · generic cell escaping · run_evidence recorded at a shipping-branch sha before commits, exit corrected · cmd/exit rendered. Deferred: signer_kind enum, alternatives_of, --rings attendance, gates[].kind enum, cross-ring fills, F-06 cap (G3).
- card budget: counters.card 2 / psl card_retries 3 — a further round needs an explicit grant.
