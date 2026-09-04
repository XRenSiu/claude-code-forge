# voice-profile — evaluation marker

**gate_pass: `static_only`** · tier: production · date: 2026-09-05

Author-run L0 (`lint_skill.py`: 0 blocking) and smoke of `verify_voice.py`: the filled example
(`fixtures/voice.example.md`) passes; the empty template rejects on placeholder rhythm data, 忌口 without
replacement, and fewer than three positive examples.

Not independent; not behavioral. The example profile's "samples" are the humanize fixtures written by the same
author, so it demonstrates the *shape* of a passing profile, not a real person's voice. Whether a profile measurably
moves `/humanize` output toward its author is unmeasured (needs consented third-party samples and a blind ranking).
