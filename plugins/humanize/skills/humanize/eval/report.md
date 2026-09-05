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

## v0.2.0 (2026-09-05) — bugs found while dogfooding on a real report

| what | before | after |
|---|---|---|
| factdiff on a rewrite that only changed spacing (`1.4 s` → `1.4s`, `1,000` → `1000`) | hard FAIL | PASS — number anchors compared after whitespace / thousands-comma normalisation |
| factdiff on a number+unit at sentence end (`10GB.`) | anchor `1` (the `.` in the trailing lookahead class forced a backtrack) | anchor `10GB` |
| factdiff on `1.4` | counted as a version, dropped from numbers | number; VERSION needs `v` or `x.y.z` |
| factdiff on `~~~` fences | counted | stripped, same as ``` |
| factdiff proper nouns | sentence-initial `Two`, `Rollout` flagged | excluded when the lowercase form also occurs |
| humanlint emoji_count on ✓ / ✗ table marks | WARN | ok (colour ✅ ❌ still count) |
| cold-reader verdict | declarative rules only | `verify_coldread.py` recomputes the verdict from the five rules, rejects mismatches, refuses `--round 3` |

Calibration unchanged after the patch: ai-zh 60 FLAG · human-zh 2 · ai-en 63 FLAG · human-en 0.

## v0.3.0 (2026-09-05) — genre decides whether structure may move

Trigger: a research report humanized under the default (narrative) criteria came back as 40 paragraphs of ~200 characters; the reader
could not scan it. The criteria were right for a proposal and wrong for a report.

| change | evidence |
|---|---|
| humanlint `--genre report` (bullet 0.55/0.75 · headings 11k/18k · bold 5k/9k) | fixtures under report: ai-zh 54 FLAG · human-zh 2 · ai-en 60 FLAG · human-en 0 (direction holds; narrative unchanged) |
| `--keep-structure` contract, default on for report / readme / reference | SKILL.md Σ/φ/γ/绝不 + human-voice.md + discourse.md §4 |
| `structdiff.py` compiles it | rephrase-only copy PASS · one bullet removed FAIL · heading renamed WARN · paragraph split PASS · prose report vs restructured html FAIL |
| cold-reader / verify_coldread: `report` joins the decision-buried and told-not-shown genre sets; keep_structure input | example fixture still consistent |

## Honest residuals

- Calibration is circular: the fixtures and thresholds share an author. Add third-party samples before trusting the
  absolute index; the *direction* (AI ≫ human) is robust across all 23 metrics (v0.1.1 added short_sentence_presence / flat_run_max / same_opener_ratio; ai-en flat run = 8 consecutive same-length sentences).
- The discourse layer (the skill's actual contribution) has no script; it is judged by the isolated `cold-reader`
  agent, whose rules are declarative. A schema check on `cold-read.yaml` is the highest-ROI hardening.
- Effect layer not run. Certification requires held-out drafts and an isolated reader, per `fix_list`.
