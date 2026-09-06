# Ledger — feat-b

> 只增不删。G1 拒了两次、G2 拒了一次才过；state.json 只留最后一次 pass。
> 两行诱饵：非 gate 行的 decision / evidence 里也带 "reject" 字样，逐字子串匹配会多数。

| at | stage | kind | signal / gate | layer | fingerprint | evidence | decision | by |
|---|---|---|---|---|---|---|---|---|
| 2026-09-04T10:00:00+00:00 | intake | init |  |  |  | title=b track=psl |  | engine |
| 2026-09-04T11:00:00+00:00 | track | gate | g1 | world |  | g1-record.md | reject (rule_error) | pm |
| 2026-09-04T12:00:00+00:00 | track | gate | g1 | world |  | g1-record.md | reject (derivation_error) | pm |
| 2026-09-04T13:00:00+00:00 | track | gate | g1 | world |  | g1-record.md | pass | pm |
| 2026-09-04T13:30:00+00:00 | g2 | deviation | skill_defect | card |  | commit landed although verify_commit.py returned REJECT (exit code swallowed by a pipe) |  | engine |
| 2026-09-04T14:00:00+00:00 | g2 | gate | g2 |  |  | g2-record.md | reject | pm |
| 2026-09-04T15:00:00+00:00 | g2 | gate | g2 |  |  | g2-record.md | pass | pm |
| 2026-09-04T16:00:00+00:00 | implement | reflow | lock_hash_mismatch | human | c8026b5b38d0 | rule handler is human | reject_diff_unless_change_proposal | engine |
| 2026-09-05T08:00:00+00:00 | review | gate | g3 |  |  | g3-record.md | pass | pm |
