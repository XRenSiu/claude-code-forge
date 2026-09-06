# needs-human.md — iteration-003 (sdlc-ring-audit)

> /meta-judge state_decision = NEEDS_HUMAN（rule 3：human AC）。以下问题**逐字**取自 meta-judge-output.yaml#needs_human_items。
> 路由：nh-001 / nh-002（human AC）→ G3；nh-003 / nh-004 → g2-judge。
> **解码状态**：g2-judge 对 iteration-002 的先例要求 gaming ≤ 3.5 **且**无 fix-induced 发现才自动 PASS-pending-G3；本轮 gaming = 4.0（(3.5, 7) 区间）且有两条 fix_induced 的 P1 → 按先例"带组成回 g2-judge 再解码一次，不再改代码"。

- meta-judge: NEEDS_HUMAN · merged 15 · blocking [] · P1 ['mf-001', 'mf-002'] · P2 ['mf-003', 'mf-004', 'mf-006', 'mf-007', 'mf-009'] · P3 ['mf-005', 'mf-008', 'mf-010', 'mf-011', 'mf-012', 'mf-013', 'mf-014', 'mf-015']
- fix_induced: [('mf-001', 'P1', 1.0), ('mf-002', 'P1', 1.0)]
- recurrences: [('mf-001', 'iteration-002/mf-005'), ('mf-003', 'iteration-002/mf-011'), ('mf-004', 'iteration-002/mf-010'), ('mf-006', 'iteration-002/mf-014'), ('mf-007', 'iteration-002/mf-017'), ('mf-009', 'iteration-002/mf-009'), ('mf-010', 'iteration-002/mf-008'), ('mf-011', 'iteration-002/mf-006'), ('mf-012', 'iteration-002/mf-016'), ('mf-013', 'iteration-002/mf-020'), ('mf-014', 'iteration-002/mf-019')]
- closed from iteration-002: 3 findings / 2 classes (stale-sha, exit-vs-ok)
- gaming 4.0 (trajectory [3.5, 4.0, 4.0]) · qa GO 0 regressions · pm 8/1/0/2 block_merge false · perf skipped by ruling
- known-gap-tagged findings (already waived to change-proposal-002): [('mf-003', 'KG-02'), ('mf-004', 'KG-08')]

## nh-001  ·  route: G3

```yaml
item_id: nh-001
question: 'AC-005-a (REQ-005, ui:AUDIT.md#ring-tables, judge: tech). Two clauses cannot be judged mechanically:
  does every deletion test name a concrete error artifact rather than a 流程会断-class generality, across 42 Part rows
  and 33 missing rows; and does the one suggested name (R8/tune → harness-tune) fit the artifact or position better
  than the original while correctly carrying 不重命名? Mechanical support registered by the fleet, to be weighed not
  re-derived: script_gates_rendered_as_door 0, rename_true 0, orphan_gaps 0, 0 grep hits for generic deletion phrases,
  42/42 deletion tests specific with 0 duplicates (gaming''s content probe), both contract-named duplicate pairs
  adjudicated with artifact comparison, render deterministic, and the ring-table bytes BYTE-IDENTICAL to the page
  iteration-002 already reviewed (the ba7d5e2..4ddb362 diff to AUDIT.md is a single hunk at L965-983, inside run_evidence).
  Open tension for the tech judge: mf-009 — three Parts (R6/human_gate.G3, R7/agent.pr-reviewer, R8/tune) record
  implemented compiled while every artifact they produce has checked_by [], which audit.schema.md:121 says caps
  the producer at declared; 21 cells print the cap note beside **compiled**, so the contradiction is displayed rather
  than resolved, and no predicate exists to catch it.'
surfaced_by: rule_index 3 (+ mf-009, pm-reviewer out_of_scope_observations[3], gaming srg-004)
blocking: true
suggested_resolver: 'G3 tech judge, per done_when.yaml AC-005-a judge: tech; checklist at tests/ring-audit/checklist_G3.md
  L9-24 (14 boxes)'
```

## nh-002  ·  route: G3

```yaml
item_id: nh-002
question: 'AC-006-a (REQ-006, ui:AUDIT.md#run-evidence, judge: product). Does the page hold for a reader on the
  two clauses no instrument can check — a delegated_agent gate is never rendered as 人签, and the external evidence
  substitute is never rendered as user verification? Mechanical support: G1/G2 render 代签（delegated） through a closed
  map with authorization_ref, G3 pending, 0 未知 cells, 0 rendered 人签 (all 15 occurrences of 人签 in AUDIT.md are prohibitions,
  explanations or gap names), the substitute label present at L1044-1048, both check-audit runs listed and reproduced,
  and the Card-footer diff-stat empty and reproducible. What the judge must weigh against that, all inside this
  same section: mf-002 (the footer-less row is labelled 自第一个 Card 提交起 while the yaml''s window is merge-base(main,HEAD)..HEAD,
  and the page names none of the four touching commits, so it reads as if four post-Card commits touched the audited
  dirs when the true count under that label is zero); mf-005 (skill_issues_count rendered as 67 against 69 rows
  at 4ddb362); mf-011 (the holdout witness cell echoes attested_by_kind raw instead of through the closed map, on
  the very F-15 surface this AC asks the judge to read); and qa-reviewer''s non-finding observation that the explanatory
  blockquote which told a reader why the recorded counts drift was removed in this iteration and replaced by a flag
  that fires only on exit/ok disagreement. Note for the judge: the two iteration-002 record defects ARE fixed (see
  closed_from_previous) — this is a shorter list than last round, and pm-reviewer states that none of the three
  remaining items contradicts a clause of the AC statement.'
surfaced_by: rule_index 3 (+ mf-002, mf-005, mf-011, qa-reviewer caveats.other[1])
blocking: true
suggested_resolver: 'G3 product judge, per done_when.yaml AC-006-a judge: product; checklist at tests/ring-audit/checklist_G3.md
  L26-40 (11 boxes)'
```

## nh-003  ·  route: g2-judge

```yaml
item_id: nh-003
question: 'Which side wins on each signed-form-vs-code divergence? Six merged findings are disagreements between
  a signed or written rule and the compiled predicate, where no AC decides and the spec side sits in done_when.yaml
  constraints.forbidden_paths for this Run, so no Card commit could amend it: mf-004 (G1 rule 2(e) states same-ring
  for missing[] only, the code applies it to fills[] too — drift recommends update_spec, the code-reviewer offers
  either direction, and KG-08 would lock the stricter reading if the mutant lands first); mf-010 (--rings disables
  ring_unexpected against F-17''s 不改任何既有谓词; drift explicitly separates this from KG-05); mf-007 and mf-008 (six
  declared registries vs eight carried, and the assembly note claiming completeness); mf-012 (audit.schema.md says
  stdout is always one JSON object, die() writes none on exit 2); mf-013 (F-16''s three-member disposition enum
  vs the schema''s two, with no predicate on either); mf-014 (the schema''s supersedes preamble describes card divergences
  that 5a6889c removed). Each needs a ruling before change-proposal-002 compiles a predicate that would freeze whichever
  reading the code happens to hold.'
surfaced_by: mf-004, mf-007, mf-008, mf-010, mf-012, mf-013, mf-014
blocking: false
suggested_resolver: G1 interpretation round then G2, via change-proposal-002 (the status_legend known_gaps.yaml
  already declares for KG-01..11)
```

## nh-004  ·  route: g2-judge

```yaml
item_id: nh-004
question: 'Should this iteration''s fixes ship without a locked test? pm-reviewer records that NONE of the iteration-003
  changes has one — the empty-range guard, core.quotePath=false, the case-insensitive footer match, the merge-base
  non-card window, the files[] field, the exit/ok mismatch flag, the recorded_at_head rendering and the ten new
  code() sites — because tests/** is l5-locked and every change landed outside it. qa-reviewer independently reports
  the same gap for render_audit.py, the file most changed this round, and says it closed the gap by hand-reading
  rather than by test. This is the mechanism by which both iteration-003 P1s exist: the case-insensitive matcher
  was added without a twin test that would have shown the two passes no longer partition the range. g3-input.md
  nh-004 and gaming''s srg-002/srg-003 already list the natural additions (golden-file AUDIT.md byte compare; a
  fixture with a pipe in atoms; a signer_kind 人签 variant; a twin repo with a CJK path and a rename out of plugins/sdlc/skills/;
  an empty main..HEAD range; a lowercase-footer commit that must appear in exactly one pass).'
surfaced_by: pm-reviewer out_of_scope_observations[2], qa-reviewer caveats.other[2], spec-gaming-detector srg-002
  / srg-003
blocking: false
suggested_resolver: /test-suite-generator via change-proposal-002, then /calibrate for the mutation mirror
```

