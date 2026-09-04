# humanize — evaluation marker

**gate_pass: `static_only`** · tier: production · evaluated_layers: `[structural, script-smoke]` · date: 2026-09-05

## What this is (and is not)

Author-run L0 (skillwise `lint_skill.py`: routes by gap, 0 procedural hits, exit surface present, scripts present,
161 lines) plus author-run smoke of the two primitives on four self-written fixtures. It is **not** an independent
judge read and **not** a behavioral (with-skill vs no-skill) run. Machine-readable verdict is `gate.json`.

## Script smoke

| fixture | humanlint index | verdict |
|---|---|---|
| ai-zh.md | 60 | FLAG (stock 33/1k, signpost-start 56%, 0 anchors, summary closer, generic opening) |
| human-zh.md | 2 | WARN (paragraph_len_cv only) |
| ai-en.md | 63 | FLAG (stock 74/1k, nominalization 111/1k, bold-label bullets, summary closer) |
| human-en.md | 0 | PASS |

factdiff: clean paraphrase → pass; number/identifier tampering (en, zh) → FAIL with the exact anchors listed.

## Honest residuals

- Calibration is circular: the fixtures and thresholds share an author. Add third-party samples before trusting the
  absolute index; the *direction* (AI ≫ human) is robust across all 23 metrics (v0.1.1 added short_sentence_presence / flat_run_max / same_opener_ratio; ai-en flat run = 8 consecutive same-length sentences).
- The discourse layer (the skill's actual contribution) has no script; it is judged by the isolated `cold-reader`
  agent, whose rules are declarative. A schema check on `cold-read.yaml` is the highest-ROI hardening.
- Effect layer not run. Certification requires held-out drafts and an isolated reader, per `fix_list`.
