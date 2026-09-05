# diff-mode-protocol.md — comparing iterations

Diff mode is the highest-leverage phase of `/spec-gaming-detector`. Patterns introduced *between* iterations are higher confidence than patterns in absolute mode — the author saw the previous evaluation's result and gamed around it. This document covers how to set up and run the comparison.

## Three ways to provide `--history`

### 1. Git ref

```
/spec-gaming-detector spec.md src/ --history=HEAD~1
```

The skill uses `git archive HEAD~1 | tar -x -C <workdir>/previous-snapshot/` to materialize the previous state. Works if the artifact is git-tracked. Fast.

If `<artifact_source>` is itself a diff or a non-git path, `--history` must be a tarball or directory.

### 2. Tarball

```
/spec-gaming-detector spec.md src/ --history=./snapshots/iteration-2.tar.gz
```

Tarball is extracted to `<workdir>/previous-snapshot/`. Useful when working with snapshots stored outside git (e.g. CI artifact retention).

### 3. Directory

```
/spec-gaming-detector spec.md src/ --history=./snapshots/iteration-2/
```

Direct directory reference. The skill uses the directory as `<workdir>/previous-snapshot/` without copy.

## What "the diff" means

The diff between `<previous-snapshot>` and `<artifact_source>` is computed via:

```bash
diff -ruN <previous-snapshot>/ <artifact_source>/ > <workdir>/iter-diff.patch
```

The skill reads `iter-diff.patch` and normalizes to the PR-Agent structured hunk format (see `code-reviewer/references/diff-format.md` § "Structured hunk format"). Same format used by all diff-consuming skills in this plugin.

For very large diffs (> 1000 hunks), the skill warns: "diff-mode scan over a very large diff produces noise; consider scoping `<artifact_source>` to the changed feature directory only."

## Per-pattern diff scan recipes

### Test Modification (diff mode)

```bash
# 1. Identify tests that exist in both versions
comm -12 <(find <previous-snapshot>/tests -name '*.test.*') <(find <artifact_source>/tests -name '*.test.*')

# 2. For each common test file, diff assertion-level changes
for f in <common_test_files>; do
  diff -u <previous-snapshot>/$f <artifact_source>/$f | grep -E '^[-+].*assert|^[-+].*expect'
done
```

Look for:
- Assertion strength dropped: `assert x == 5` → `assert x is not None` (or in JS: `.toBe(5)` → `.toBeTruthy()`).
- New `@pytest.mark.skip` / `.skip` decorations.
- New mocks where there were none.

### Test Case Targeting (diff mode)

Diff the impl side only (not tests):

```bash
diff -u <previous-snapshot>/<impl_file> <artifact_source>/<impl_file>
```

Look for new `if input == <literal>: return <literal>` patterns or new branches whose literal matches a test fixture value. Cross-reference: did the test for this input previously fail in `<previous-snapshot>/tests/`?

### Coverage Gaming (diff mode)

Two checks:

1. **Coverage delta vs mutation delta.** If both snapshots have a prior `qa-report.yaml` (from `/qa-reviewer`):
   ```
   line_coverage rose, mutation_kill_rate flat → coverage_gaming P0
   ```
2. **Dead code added.** Compare AST node counts:
   ```bash
   ast_parse <previous-snapshot>/<file> > /tmp/old.ast.json
   ast_parse <artifact_source>/<file> > /tmp/new.ast.json
   ```
   If new has more nodes but the *reachable* node count (per dataflow analysis) is the same → dead code added.

### Degenerate Implementation (diff mode)

```bash
# Cyclomatic complexity per function
complexity_analyzer <previous-snapshot>/<file>  # prints per-function CC
complexity_analyzer <artifact_source>/<file>

# Compare per function: if CC grew >2x without REQ change → degenerate impl
```

If a function went from CC=4 to CC=18 between iterations, and the spec didn't add new sub-cases, the impl agent expanded the branching to enumerate test cases.

### Style Manipulation (diff mode)

Compute `comments_added` / `lines_added` ratio:

```python
diff_total_lines = sum(1 for line in diff if line.startswith('+'))
diff_comment_lines = sum(1 for line in diff if line.startswith('+') and is_comment(line, file_extension))
ratio = diff_comment_lines / diff_total_lines
if ratio > 0.5:
    flag "comment_bombing"
```

Also: if the diff has many `+++ /dev/null` for `.md` / `README.md` (docs changed) but no `.ts` / `.py` etc changed, log `docs_only_change_under_fix_pressure`.

### Information Leakage (diff mode)

Walk the diff for new string literals or numeric constants:

```bash
diff -u <previous>/<impl> <current>/<impl> | grep -E '^\+' | grep -oE '"[^"]+"|[0-9]+\.[0-9]+' > /tmp/new-constants.txt
```

For each new constant, grep `spec.md`:

```bash
for const in $(cat /tmp/new-constants.txt); do
  if grep -q "$const" <spec_source>; then
    echo "LEAK: $const appears in spec.md and was newly introduced in impl"
  fi
done
```

## Common pitfalls

### Pitfall: Whitespace / formatting noise

A lint reformat between iterations adds hundreds of `+`/`-` lines that aren't real changes. Strip via `diff -u --ignore-all-space` for the pattern scan, but preserve the raw diff for finding evidence.

### Pitfall: Rename detection

If a file was renamed between iterations, vanilla `diff -ruN` shows it as deleted + added. The skill should use `git diff --find-renames` if both sides are git-tracked, or use a content-similarity check before flagging "file deleted, file added with similar content" as renames.

### Pitfall: Generated code

`dist/` / `build/` / generated proto files / minified JS — these "change" between iterations as a side effect of source changes, not as direct author edits. Exclude via `.gitignore` patterns + common-known generated-code directory names.

### Pitfall: Multi-commit iteration

If the "previous iteration" actually spanned multiple commits, the diff aggregates all of them. The introducing commit for a specific change can be narrowed via `git log -S '<pattern>' --all` within the iteration range. Record both: the iteration-level diff (the contract) and the specific commit (for evidence precision).

## What "iteration N" means

Defined externally. `/spec-gaming-detector` doesn't care whether "iteration N" is a CI build number, a daily snapshot, or a ratchet step in `/acceptance-fleet`. It just needs:
- `<previous-snapshot>` (a coherent prior state)
- `<artifact_source>` (the current state)
- Optionally `--baseline-score` (the previous run's `gaming_risk_score`)

The consumer (typically `/acceptance-fleet`) handles iteration bookkeeping.
