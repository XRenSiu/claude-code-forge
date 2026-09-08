#!/usr/bin/env python3
"""
post_review.py — post a findings.yaml as ONE GitHub pull-request review with inline comments.

The primitive the engine otherwise mis-improvises: inline comments must land on lines that exist in the
PR diff (new-file coordinates); everything else must degrade to the summary, not be silently dropped
or pinned to a wrong line. And the event is never APPROVE — approval is a human act.

Usage:
  post_review.py findings.yaml --pr N [--event COMMENT|REQUEST_CHANGES] [--dry-run] [--summary-only]
                 [--repo OWNER/NAME]

Exit 0 posted (or dry-run printed) · 1 refused (schema breach: P0/P1 without reproduction/suggested_change,
event APPROVE, unknown tier) · 2 gh/IO error.

Mechanical guarantees:
  - event ∈ {COMMENT, REQUEST_CHANGES}; if omitted: REQUEST_CHANGES iff any tier A finding, else COMMENT
  - every P0/P1 finding carries reproduction_scenario + suggested_change (else refuse)
  - inline placement validated against `gh pr diff N` (right-side line numbers of added/context lines);
    non-commentable → listed in the summary with path:line
  - summary body: tier counts, mergeable verdict, rationale when findings are empty, caveats
"""
import argparse
import json
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("post_review.py needs PyYAML\n"); sys.exit(2)

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def commentable_lines(diff_text):
    """path -> set of right-side line numbers present in the diff (added + context)."""
    out, path, new_line = {}, None, None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            p = line[4:].strip()
            path = p[2:] if p.startswith("b/") else p
            out.setdefault(path, set())
            continue
        if line.startswith("--- ") or line.startswith("diff --git") or line.startswith("index "):
            continue
        m = HUNK_RE.match(line)
        if m:
            new_line = int(m.group(1)); continue
        if path is None or new_line is None:
            continue
        if line.startswith("+"):
            out[path].add(new_line); new_line += 1
        elif line.startswith("-"):
            pass
        elif line.startswith("\\"):
            pass
        else:
            out[path].add(new_line); new_line += 1
    return out


def gh(*args, input_text=None):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, input=input_text)
    if r.returncode != 0:
        sys.stderr.write(f"post_review: gh {' '.join(args[:3])} failed: {r.stderr.strip()}\n"); sys.exit(2)
    return r.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("findings"); ap.add_argument("--pr", required=True, type=int)
    ap.add_argument("--event", choices=["COMMENT", "REQUEST_CHANGES", "APPROVE"])
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--summary-only", action="store_true")
    ap.add_argument("--repo"); ap.add_argument("--diff-file", help="(testing) use this diff instead of gh pr diff")
    a = ap.parse_args()
    if a.event == "APPROVE":
        sys.stderr.write("post_review: APPROVE refused — approval is a human act\n"); sys.exit(1)
    doc = yaml.safe_load(open(a.findings, encoding="utf-8")) or {}
    rv = doc.get("review") or doc
    findings = rv.get("findings") or []
    problems = []
    for f in findings:
        if f.get("tier") not in ("A", "B", "C"):
            problems.append(f"{f.get('id')}: tier must be A|B|C")
        if f.get("severity") in ("P0", "P1"):
            if not f.get("reproduction_scenario"):
                problems.append(f"{f.get('id')}: {f.get('severity')} without reproduction_scenario")
            if not f.get("suggested_change"):
                problems.append(f"{f.get('id')}: {f.get('severity')} without suggested_change")
        if not f.get("file") or not f.get("line_range"):
            problems.append(f"{f.get('id')}: missing file/line_range")
    if not findings and not rv.get("rationale"):
        problems.append("findings empty but rationale missing")
    if problems:
        print(json.dumps({"refused": True, "problems": problems}, ensure_ascii=False, indent=2)); sys.exit(1)

    has_a = any(f.get("tier") == "A" for f in findings)
    event = a.event or ("REQUEST_CHANGES" if has_a else "COMMENT")
    diff_text = open(a.diff_file, encoding="utf-8").read() if a.diff_file else \
        gh(*(["pr", "diff", str(a.pr)] + (["--repo", a.repo] if a.repo else [])))
    lines_ok = commentable_lines(diff_text)

    inline, degraded = [], []
    for f in findings:
        path, lr = f.get("file"), f.get("line_range") or []
        line = int(lr[-1]) if lr else None
        body = (f"**{f.get('severity')} · tier {f.get('tier')} · {f.get('category')}** ({f.get('id')})\n\n"
                f"{f.get('root_cause')}\n\n"
                + (f"**Repro:** {f.get('reproduction_scenario')}\n\n" if f.get("reproduction_scenario") else "")
                + (f"**Suggested:** {f.get('suggested_change')}\n" if f.get("suggested_change") else "")
                + (f"\n_needs codebase check_" if f.get("needs_codebase_check") else ""))
        if not a.summary_only and path in lines_ok and line in lines_ok[path]:
            inline.append({"path": path, "line": line, "side": "RIGHT", "body": body})
        else:
            degraded.append((f, body))

    ts = rv.get("tier_summary") or {"A": sum(f.get("tier") == "A" for f in findings),
                                    "B": sum(f.get("tier") == "B" for f in findings),
                                    "C": sum(f.get("tier") == "C" for f in findings)}
    summary = [f"## pr-review · focus={rv.get('focus', '?')} · {len(findings)} finding(s)",
               f"**tiers** A={ts.get('A', 0)} B={ts.get('B', 0)} C={ts.get('C', 0)} · **mergeable**: {rv.get('mergeable', 'n/a')}", ""]
    if not findings:
        summary.append(f"No findings. Rationale: {rv.get('rationale')}")
    for f, body in degraded:
        summary.append(f"- `{f.get('file')}:{'-'.join(map(str, f.get('line_range') or []))}` — {body.splitlines()[0]}\n  {f.get('root_cause')}")
    cav = rv.get("caveats") or {}
    for k, v in cav.items():
        if v:
            summary.append(f"> caveat ({k}): {v}")
    payload = {"event": event, "body": "\n".join(summary), "comments": inline}
    if a.dry_run:
        print(json.dumps({"dry_run": True, "pr": a.pr, "payload": payload, "degraded": len(degraded)}, ensure_ascii=False, indent=2))
        sys.exit(0)
    repo = a.repo
    if not repo:
        repo = gh("repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner").strip()
    out = gh("api", f"repos/{repo}/pulls/{a.pr}/reviews", "--method", "POST", "--input", "-", input_text=json.dumps(payload))
    try:
        j = json.loads(out)
        print(json.dumps({"posted": True, "review_id": j.get("id"), "event": event, "inline": len(inline), "degraded": len(degraded), "url": j.get("html_url")}, ensure_ascii=False))
    except Exception:
        print(out)


if __name__ == "__main__":
    main()
