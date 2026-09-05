# diff-format.md — PR-Agent structured hunk format

All skills in this plugin that consume a diff (code-reviewer, pm-reviewer, spec-gaming-detector, spec-drift-detector) use the same structured representation. Standardizing means a finding from one skill can be cross-referenced by another with exact `file:line` coordinates.

## Why structured

Plain `git diff` output gives an LLM headaches:
- `+`/`-` prefixes get visually confused with code operators.
- No explicit line numbers means the LLM hallucinates them.
- Multi-hunk files have ambiguous "current" vs "before" context.

PR-Agent (Qodo) introduced the structured hunk format that the model can parse without guessing. We adopt it verbatim.

## Structured hunk format

Each hunk is split into two named blocks: `__new_hunk__` (post-change) and `__old_hunk__` (pre-change).

```
## File: src/billing/cancel.ts

@@ -40,8 +40,12 @@

__old_hunk__
function cancelSubscription(sub_id: string) {
  const sub = db.subscriptions.find(sub_id);
  if (sub.status !== 'active') return;
  sub.status = 'cancelled';
  return sub;
}

__new_hunk__
42  function cancelSubscription(sub_id: string, user_id: string) {
43    const sub = db.subscriptions.find(sub_id);
44    if (sub.status !== 'active') return;
45    sub.status = 'cancelled';
46    sub.cancelled_at = new Date().toString();
47    sub.cancelled_by = user_id;
48    return sub;
49  }
```

Rules for the format:

1. **Every `__new_hunk__` line is prefixed with its absolute line number in the new file.** The number is space-padded to a fixed width within the hunk (e.g. 2 chars if the hunk is in the 10s, 3 chars if in the 100s).
2. **`__old_hunk__` lines have NO line numbers.** Reason: when the LLM emits a finding, it must reference the new file's coordinates. Old line numbers invite confusion.
3. **No leading `+`/`-` prefixes inside the hunk blocks.** The block name itself disambiguates new vs old. This is the most important departure from raw `git diff` — the prefixes are noise once the blocks are named.
4. **Hunk separator `@@ -X,Y +A,B @@` precedes both blocks**, identifying the line ranges in both files. The skill emitting the finding uses the `+A,B` range to anchor `line_range:` in the YAML output.
5. **A diff with no `__old_hunk__`** (pure addition, e.g. new file) emits only `__new_hunk__` with `@@ -0,0 +1,N @@`.
6. **A diff with no `__new_hunk__`** (pure deletion) emits only `__old_hunk__`. Findings on deleted code reference the *previous* file path with a `deleted_in_diff: true` flag (rare; mostly relevant for spec-drift-detector when checking "this safety check was removed").

## Normalizer pseudo-code

Skills that receive raw `git diff` output run this normalizer first:

```python
def normalize_diff(raw_diff: str) -> list[Hunk]:
    hunks = parse_unified_diff(raw_diff)
    out = []
    for hunk in hunks:
        new_lines = []
        for line_no, line in zip_with_line_numbers(hunk.new_block):
            new_lines.append(f"{line_no:>4} {line}")
        out.append(Hunk(
            file=hunk.file,
            old_range=hunk.old_range,
            new_range=hunk.new_range,
            new_block="\n".join(new_lines),
            old_block=hunk.old_block,   # unchanged
        ))
    return out
```

## How findings reference the format

A finding's `line_range` always refers to the **new file's coordinates**. Example:

```yaml
findings:
  - finding_id: cr-001
    file: src/billing/cancel.ts
    line_range: [46, 47]            # new file's coordinates
    root_cause: "cancelled_at uses local time, not UTC"
```

This matches what the user sees when they open the file at `HEAD` (post-merge) or in their editor.

If a finding is about *removed* code, use `deleted_in_diff: true` and reference the old file's coordinates with a comment:

```yaml
findings:
  - finding_id: cr-002
    file: src/billing/cancel.ts
    line_range: [44, 44]
    deleted_in_diff: true
    deleted_from_old_lines: [42, 42]
    root_cause: "Authorization check was removed without replacement"
```

## Maximum hunk size

If a hunk is >100 lines, split it at the largest unchanged block in the middle and emit as two hunks with the same file header. This keeps the LLM's attention focused and avoids context dilution. Most skills will warn if a hunk exceeds 200 lines; past 500, the diff is too large for the reviewer regardless of format and the skill should refuse the run (see `code-reviewer/SKILL.md` § "When to refuse").
