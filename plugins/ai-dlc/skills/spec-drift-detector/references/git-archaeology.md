# git-archaeology.md — tracing drift through git history

Phase D5 of `spec-drift-detector` traces every drift signal to its introducing commit. This document is the operational recipe.

The goal: for each drift signal, fill three fields:

- `commit_introducing_drift: <sha + subject>` — the commit that introduced the divergence.
- `drift_age: <human readable>` — how long the drift has been live.
- `likely_intentional: <true | false | unclear>` — heuristic intent inference.

These three feed the `recommendation:` field via the rules in `SKILL.md` § D6.

---

## Step 1: `git log` to find candidate commits

For the code side of the drift:

```bash
git log --follow --pretty=format:"%H %ad %s" --date=short -L <line_start>,<line_end>:<file>
```

The `-L` form (line-range tracking) is the most precise but slow on large histories. Fall back to `--follow <file>` if `-L` is too slow:

```bash
git log --follow --pretty=format:"%H %ad %s" --date=short <file> | head -<history_depth>
```

Identify candidates — usually 2-5 commits that touched the offending line range.

For the spec side (if it's a separate file):

```bash
git log --pretty=format:"%H %ad %s" --date=short <spec_file>
```

---

## Step 2: `git blame` to narrow to the line-level introducer

```bash
git blame --line-porcelain -L <line_start>,<line_end> <file> | grep "^author-mail\|^author-time\|^summary\|^commit"
```

`git blame` tells you which commit last touched each line. The most recent commit affecting the offending line is the *immediate* author of the divergence — but you need to walk back further to find the *introducer*, since blame moves forward as lines get touched.

Heuristic for picking the introducer when blame and log give different SHAs:

1. Take the SHA from `git blame`.
2. `git show <sha> -- <file>` and check: does the diff at this commit *materially change* the offending behavior, or is it a no-op rename / format change?
3. If material → that's `commit_introducing_drift`.
4. If no-op → walk back: `git log --follow --pretty=format:"%H" --skip=1 <file>` and check the next commit. Iterate.

---

## Step 3: `git show` to read the commit's full context

```bash
git show <commit_sha>
```

Read:
- The commit subject (`%s`).
- The commit body (`%b`).
- The full diff at this commit (not just the file in question — sometimes the body of a commit message references *other* files changed in the same commit, which gives intent).

Look for:
- Was the spec file also modified in this commit? If yes, the author was thinking about the spec; high likelihood `likely_intentional: true`.
- Does the message mention the behavior in question? E.g. "switch cancellation to async" matches a sync→async timing_mismatch → strongly intentional.
- Is the message generic ("fix bug", "wip", "address PR comments")? Low signal toward intentional.
- Was this part of a large refactor? `git show --stat <sha>` — if the commit touched 30 files, the specific behavioral change was probably collateral.

---

## Step 4: Compute `drift_age`

```bash
git show -s --format="%ar" <sha>
```

Output is human-readable: "4 months ago", "2 weeks ago", "yesterday". Use directly in `drift_age:`.

For machine consumers also record the absolute date:

```bash
git show -s --format="%ad" --date=iso <sha>
```

---

## Step 5: Infer `likely_intentional`

Decision tree:

```
def likely_intentional(commit_message, files_touched_in_commit, drift_subject, spec_file):
    if spec_file in files_touched_in_commit:
        # author was thinking about the spec when changing the code
        return "true"

    if drift_subject_keywords in commit_message.lower():
        # commit explicitly described the change
        return "true"

    if commit_message in ["wip", "fix", "address PR comments", ...]:  # generic
        if files_touched_in_commit_count > 10:
            return "false"  # likely collateral, generic-message large refactor
        return "unclear"

    if drift_subject is unrelated to commit_message:
        # commit was about X but the offending change is about Y
        return "false"

    return "unclear"
```

`drift_subject_keywords` are extracted from the divergence type + the offending line content. E.g. a timing_mismatch from sync to async has keywords `[async, queue, defer, schedule, background, worker]`.

This is a heuristic — humans override. The `recommendation:` field uses this as one input; the human decides.

---

## Handling complex cases

### Case: drift was introduced gradually over multiple commits

Sometimes a divergence isn't from one commit — it's from a cascade ("we added 1 day to grace period in commit A, then another 6 days in commit B, total 7 vs spec's 15"). In that case:

- `commit_introducing_drift: <sha_of_most_recent_material_change>`
- `additional_contributing_commits: [<other shas>]`
- `drift_age: <from oldest contributing commit>`

The schema supports the optional `additional_contributing_commits:` list for this case.

### Case: drift was introduced in code that no longer exists at that line

`git log -L` follows movement well, but rewrites (large refactor, file rename) can break the chain. If the chain is broken:

- `commit_introducing_drift: chain_broken_at_<sha>`
- Run `git log --follow --diff-filter=R <file>` to see rename history; if the file was renamed, mention in `drift_notes:`.

### Case: pre-history (drift older than `--history-depth`)

```yaml
commit_introducing_drift: pre_history
drift_age: ">${history_depth} commits ago"
likely_intentional: unclear
```

Recommendation defaults to `needs_human` for pre-history drift — the divergence is so old that the original intent is irrecoverable.

### Case: spec was added AFTER code (chronologically)

Sometimes a doc / spec is added after the code is already in place. The "drift" is actually "the doc never matched the code from day one." Detection:

- Find the first commit that introduced the spec claim: `git log -p <spec_file> | grep -B1 "<spec_text>"`.
- Find the first commit that introduced the offending code: `git log -p <code_file> | grep -B1 "<code_pattern>"`.
- Compare dates.

If spec is newer than code → record `drift_origin: "spec_written_after_code"` and prefer `recommendation: needs_human` (the doc author may have misunderstood the code OR the code was supposed to be updated). Strongly suggest the human check with the spec author.

---

## When `git` is not available

The skill should still emit drift signals if `<spec_source>` and `<code_paths>` disagree — `git` is only needed for archaeology, not for detection. If `git` is unavailable:

```yaml
commit_introducing_drift: git_unavailable
drift_age: unknown
likely_intentional: unclear
```

All recommendations default to `needs_human`. Warn the user that without history, `recommendation:` is degraded.

---

## Commit message keyword library

For inferring `likely_intentional: true`, the skill uses keyword maps per divergence type:

| Type | Keywords that suggest intentional |
|---|---|
| timing_mismatch | async, sync, defer, schedule, queue, background, batch, lazy, eager, debounce, throttle, immediate, real-time |
| behavior_mismatch | change, switch, replace, swap, use ... instead, no longer, now does, was X is Y, removed, added |
| contract_mismatch | rename, refactor api, breaking change, deprecate, new endpoint, new field, drop field, signature, schema, contract |

Match against `commit_message.lower()`. Hit on ≥1 keyword + the keyword's semantics aligns with the drift direction = `likely_intentional: true`.

Keywords are heuristics; false positives are acceptable because the human always reviews `recommendation:`.

---

## Cost / time budget

Per drift signal: ~5-10 git calls, ~2 seconds wall clock. For a project with 50 drift signals, archaeology adds ~2 minutes. Acceptable.

If a project has >200 drift signals, the skill should warn that drift detection is reporting at noise level — the spec is likely catastrophically out of date and a wholesale spec rewrite (via `/acceptance-spec`) is more useful than fixing 200 individual signals.
