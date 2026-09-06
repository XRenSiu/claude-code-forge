# needs-human.md — iteration-001 (sdlc-ring-audit)

> /meta-judge state_decision = NEEDS_HUMAN（classifier rule A）。以下问题**逐字**取自 meta-judge-output.yaml#needs_human_items。
> 本 Run 的「人」= 代签 agent（用户 2026-09-05 授权）：nh-001 / nh-002 归 G3（stage g3，g3-judge）；nh-003 由契约签字人 g2-judge 裁。

- meta-judge: NEEDS_HUMAN · merged findings 14 · blocking [] · non-blocking P1 warnings ['mf-001', 'mf-002', 'mf-003', 'mf-004']
- spec-gaming-detector: gaming_risk_score 3.5 (< 7 → not GAMING_RISK; ≥ 3 → not DONE by rule E; S3 has no rule for this band — I-68) · spec_robustness_gaps 7
- qa-reviewer GO · pm-reviewer 8 fully / 1 partial (REQ-004 = KG-02) / 2 requires_human · code-reviewer perf 0 findings

## nh-001  ·  blocking: True  ·  route: G3

```yaml
item_id: nh-001
question: 'AC-005-a (REQ-005, kind human, judge tech, ui:AUDIT.md#ring-tables): do the ring tables satisfy the statement
  — per-Part Gap atoms / exclusive Artifact or role / 闸-vs-门 / Loop; deletion tests naming a concrete error artifact
  (not 流程会断); provenance-then-fit naming with 建议名 + 不重命名 on misfit; the two named duplicate pairs adjudicated; per-ring
  missing rows with source / necessity / deletion? pm-reviewer registered mechanical support (script_gates_rendered_as_door
  0, rename_true 0, orphan_gaps 0, 0 grep hits for generic deletion phrases, 不重命名 ×13, 33 missing rows, both contract-named
  pairs present, AUDIT.md byte-identical to a fresh render) and spec-gaming-detector cleared deletion_test_boilerplate
  / naming_all_fits / missing_only_easy_blanks — but the quality judgment is G3''s. Findings G3 should read alongside:
  mf-007 (闸·门 column ignores artifacts[].checked_by; disagrees for 8/42 Parts), mf-011 (tune judged compiled with
  every artifact checked_by [] — detector asks G3 to read tune / human_gate.G3 / agent.pr-reviewer as declared-with-argument),
  mf-004 (double_producer instrument accepts unverified alternatives_of; duplicates table is author-controlled),
  mf-010 (F-10 / F-11 empty-case wording never emitted — unexercised in shipped AUDIT.md).'
surfaced_by: rule_index 3 / pm-reviewer REQ-005
blocking: true
suggested_resolver: 'G3 tech judge — checklist: plugins/sdlc/dogfood/ring-audit/tests/ring-audit/checklist_G3.md
  L9-24 (14 boxes); evidence: AUDIT.md L26-852 (ring tables), L832-852 (疑似重复的 Part 对), L686-718 (tune misfit)'
```

## nh-002  ·  blocking: True  ·  route: G3

```yaml
item_id: nh-002
question: 'AC-006-a (REQ-006, kind human, judge product, ui:AUDIT.md#run-evidence): (1) does a replay table whose
  first two rows cite shas e5ffbbd / 1f1916e that are not reachable from docs/1-sdlc-ring-audit (they are the pre-rebase,
  patch-id-identical twins of 6326123 / 3441ba4 on the card/CARD-06 worktree branch) still count as "列出 Card-footer
  提交对三个被审目录的 git diff --stat 记录（为空）"? Both spec-gaming-detector (mf-012, ''stale evidence, not a false claim'')
  and pm-reviewer state the load-bearing empty diff-stat IS reproducible at 843c3ee and the sha table is NOT. (2)
  does "signer_kind = delegated_agent 的门不渲染为人签" hold as a reader experiences the page, given mf-001 demonstrates
  a check-clean injection path that renders a delegated gate as 人签 (not exploited by the delivered content per every
  reviewer''s live run), mf-005 hard-codes "本次三道门没有一道是人签" as a literal rather than projecting it, and mf-013 shows
  the "exit 0 可作证据" sentence derives from the document''s own self-report of the twin run (code-reviewer-security
  asks G3 to independently re-run check-audit + the delete-ring twin and replay_card_commits.sh)? (3) is the substitute-tier
  external evidence rendered as substitute, not user verification? pm-reviewer: AUDIT.md L914-1040 renders every
  clause; 人签 occurs only in prohibitions; substitute labelled.'
surfaced_by: rule_index 3 / pm-reviewer REQ-006; mf-012 (confidence 0.8)
blocking: true
suggested_resolver: 'G3 product judge — checklist: tests/ring-audit/checklist_G3.md L26-40 (11 boxes); evidence:
  AUDIT.md L914-1040, audit.yaml L3353-3520 (run_evidence); independent re-run of check_audit.py (exit 0) + --variant
  delete-ring:R6 (exit 1) + replay_card_commits.sh; CARD-06 doc-only refresh of the snapshot shas is the fix pm-reviewer
  suggests'
```

## nh-003  ·  blocking: False  ·  route: g2-judge (contract scope)

```yaml
item_id: nh-003
question: 'Process / contract-scope question that no mechanical AC covers and four reviewers independently flagged
  for the record: (a) before the first Card commit, footer-less commits 587f371, bf3f13e, ebe270d, c729f76 (outside
  57ebf2b..843c3ee) edited 7 files / +90-14 under plugins/sdlc/skills|agents|docs — c729f76 changed plugins/sdlc/skills/commit/scripts/verify_commit.py,
  the oracle replay_card_commits.sh calls (code-reviewer-security cr-002; pm-reviewer out_of_scope_observations[1]);
  (b) inside the range, footer-less commits e217d10 (l5 lock re-sign: 32 test files + .done_when.lock + g1-record.md,
  signed by g2-judge delegated_agent 12 minutes after CARD-01 landed), fafcad7 and 5a6889c (cards/*.yaml) edited
  paths in done_when.yaml constraints.forbidden_paths and never passed verify_commit.py --card (pm-reviewer out_of_scope_observations[2];
  qa-reviewer caveats.other[2]; spec-gaming-detector srg-006). Every reviewer agrees none violates AC-007-a as written;
  qa-reviewer and spec-gaming-detector both judge e217d10 legitimate (strengthened the suite 30→34 methods / 20→24
  mutants; RED_BASELINE rev 2 shows the impl moved to the tests, not the reverse). Question for G3 / the contract
  author: should the pre-Card audited-object edits get a G3 note, and should change-proposal-002 add the rule spec-gaming-detector
  proposes (a lock re-sign after the first Card commit needs a signer outside the implementer''s session/vendor)
  plus the instrument fix in mf-002 (count footer-less commits touching audited dirs under a separate field)?'
surfaced_by: mf-002 (confidence 0.8); pm-reviewer out_of_scope_observations[1..2]; qa-reviewer caveats.other[2];
  spec-gaming-detector srg-003 / srg-006
blocking: false
suggested_resolver: G3 (note) + contract author via change-proposal-002 + /spec-drift-detector at iteration 2 (pm-reviewer's
  routing)
```

## Orchestrator's factual notes for nh-003 (evidence, not a ruling)

- (a) 587f371 / ebe270d / c729f76 are the non-Card `fix(sdlc)` verifier fixes recorded as ledger `deviation` events (skill-issues I-04/05/07/17/34/38/39/47/51/52) and made BEFORE the first Card commit; c729f76 changed verify_commit.py (the oracle the replay calls) to compare locked content by hash (I-52), smoke +1. bf3f13e is the peer session's report commit and is not on the PR branch.
- (b) e217d10 is the change-proposal-001 re-lock (task layer, R04, confirmed 9/9 by g2-judge; ledger decision + lock events); fafcad7 / 5a6889c appended the G1 签字版解释规则 readings to cards/*.yaml (plan layer; lint_cards PASS; ledger decision). Neither carried a Card footer because neither was card work; done_when.yaml#constraints.forbidden_paths binds card implementers — whether it also binds orchestrator plan-layer edits after G2 is the question put to g2-judge.
- Fix round: the four P1 warnings + two P2s fixable inside the frozen contract are being addressed by a fresh implementer from `fix-prompt.md` (card layer, card_retry); rule-1 trust in artifacts[] and rule-2e's fills reading are deferred to change-proposal-002.
