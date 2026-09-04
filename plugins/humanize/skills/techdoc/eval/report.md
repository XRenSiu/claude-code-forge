# techdoc — evaluation marker

**gate_pass: `static_only`** · tier: production · date: 2026-09-05

Author-run L0 (`lint_skill.py`: 0 blocking, routes by gap, 0 procedural hits, exit surface present) and author-run
smoke of `verify_techdoc.py` on the four humanize fixtures: both AI drafts REJECT (4–5 rejects each: generic opening,
no decision in the first three paragraphs, no killed alternative, summary closer), both human drafts PASS.

Not an independent read; not a behavioral run. The skeleton (`references/skeleton.md`) is sourced from public
design-doc cultures and named writers; whether a doc written *with* this skill passes an isolated cold-reader more
often than one written without it is unmeasured. See `gate.json.fix_list`.
