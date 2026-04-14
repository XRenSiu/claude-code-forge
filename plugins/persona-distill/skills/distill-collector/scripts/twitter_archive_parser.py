#!/usr/bin/env python3
"""twitter_archive_parser.py — Parse a Twitter/X "Download your data" ZIP.

Implements references/text-parsers.md §9 "Twitter / X":
  - Accepts either a ``.zip`` archive or a pre-extracted directory.
  - Reads ``data/tweets.js`` (and legacy ``data/tweet.js``) by stripping the
    ``window.YTD.tweets.part0 = `` JS assignment prefix to get valid JSON.
  - Emits one Markdown file per year under
    ``{destination}/knowledge/articles/twitter/{YYYY}.md``.

Stdlib-only: zipfile, json, argparse, datetime, re, os, sys, pathlib.

CLI:
    python twitter_archive_parser.py --archive ZIP_OR_DIR --subject NAME \\
        --destination PATH [--no-redact]

Exit codes per cli-spec.md: 0 ok, 2 usage, 4 input, 5 output, 10 partial.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redactor import redact, _warn_no_redact  # noqa: E402

# Twitter archives use either tweets.js or tweet.js, prefixed with a JS assignment.
_TWEET_FILE_CANDIDATES = ("data/tweets.js", "data/tweet.js",
                          "data/tweets-part0.js")
_JS_PREFIX = re.compile(r"^\s*window\.YTD\.[A-Za-z_]+\.part\d+\s*=\s*")


def _today_tag() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%d")


def _today_iso() -> str:
    return _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_tweet_blob(archive_path: Path) -> str:
    """Return the raw contents of the tweets.js file, whether zip or dir."""
    if archive_path.is_file() and zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path) as zf:
            for cand in _TWEET_FILE_CANDIDATES:
                if cand in zf.namelist():
                    return zf.read(cand).decode("utf-8", errors="replace")
            # Fallback: any file ending with /tweets.js or /tweet.js.
            for name in zf.namelist():
                if name.endswith("tweets.js") or name.endswith("tweet.js"):
                    return zf.read(name).decode("utf-8", errors="replace")
        raise FileNotFoundError(
            f"no tweets.js / tweet.js inside {archive_path}"
        )
    if archive_path.is_dir():
        for cand in _TWEET_FILE_CANDIDATES:
            p = archive_path / cand
            if p.is_file():
                return p.read_text(encoding="utf-8", errors="replace")
        # Recursive fallback.
        for p in archive_path.rglob("tweets.js"):
            return p.read_text(encoding="utf-8", errors="replace")
        for p in archive_path.rglob("tweet.js"):
            return p.read_text(encoding="utf-8", errors="replace")
        raise FileNotFoundError(
            f"no tweets.js / tweet.js under directory {archive_path}"
        )
    raise FileNotFoundError(f"archive not readable: {archive_path}")


def _strip_js_prefix(raw: str) -> str:
    return _JS_PREFIX.sub("", raw, count=1).rstrip().rstrip(";")


def _parse_tweet_date(s: str):
    """Twitter archive format: 'Sat Mar 02 14:32:00 +0000 2024'."""
    if not s:
        return None
    try:
        return _dt.datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        return None


def _normalize_tweet(entry):
    """Archive entries are either {"tweet": {...}} or a bare tweet dict."""
    if isinstance(entry, dict) and "tweet" in entry:
        return entry["tweet"]
    return entry if isinstance(entry, dict) else {}


def _redact_handles(text: str) -> str:
    return re.sub(r"@[A-Za-z0-9_]{1,15}", "[REDACTED-HANDLE]", text)


def _frontmatter(*, subject: str, year: int, redaction_tag: str) -> str:
    return "\n".join([
        "---",
        "tier: primary",
        "tier_reason: public posts by subject",
        "source_policy: public-posts",
        f'author_of_record: "{subject}"',
        f"captured_at: {_today_iso()}",
        "platform: twitter",
        f"year: {year}",
        f"redaction: {redaction_tag}",
        "---",
        "",
    ])


def _main(argv) -> int:
    p = argparse.ArgumentParser(prog="twitter_archive_parser.py",
                                description=__doc__)
    p.add_argument("--archive", required=True,
                   help="Twitter archive .zip OR extracted directory")
    p.add_argument("--subject", required=True)
    p.add_argument("--destination", required=True)
    p.add_argument("--salt", default="distill-collector-v1")
    p.add_argument("--no-redact", action="store_true")
    args = p.parse_args(argv)

    archive_path = Path(os.path.expanduser(args.archive))
    if not archive_path.exists():
        sys.stderr.write(f"exit 4: archive not found: {archive_path}\n")
        return 4

    try:
        raw = _load_tweet_blob(archive_path)
    except (FileNotFoundError, OSError, zipfile.BadZipFile) as e:
        sys.stderr.write(f"exit 4: {e}\n")
        return 4

    try:
        data = json.loads(_strip_js_prefix(raw))
    except json.JSONDecodeError as e:
        sys.stderr.write(f"exit 4: cannot parse tweets.js JSON: {e}\n")
        return 4

    if args.no_redact:
        _warn_no_redact()
        do_redact = False
        redaction_tag = "disabled"
    else:
        do_redact = True
        redaction_tag = f"applied-v{_today_tag()}"

    by_year: dict[int, list] = {}
    skipped = 0
    for entry in data:
        tw = _normalize_tweet(entry)
        if not tw:
            skipped += 1
            continue
        created = _parse_tweet_date(tw.get("created_at", ""))
        if created is None:
            skipped += 1
            continue
        text = tw.get("full_text") or tw.get("text") or ""
        by_year.setdefault(created.year, []).append((created, text, tw))

    out_dir = Path(args.destination) / "knowledge" / "articles" / "twitter"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        sys.stderr.write(f"exit 5: cannot mkdir {out_dir}: {e}\n")
        return 5

    written = 0
    for year in sorted(by_year):
        tweets = sorted(by_year[year], key=lambda t: t[0])
        parts = [_frontmatter(subject=args.subject, year=year,
                              redaction_tag=redaction_tag)]
        for created, text, tw in tweets:
            body = text.replace("\r\n", "\n")
            if do_redact:
                body = redact(body, salt=args.salt)
                body = _redact_handles(body)
            parts.append(f"## {created.strftime('%Y-%m-%d %H:%M')}")
            parts.append("")
            parts.append(body.strip() or "[empty tweet]")
            reply_to = tw.get("in_reply_to_screen_name")
            if reply_to:
                parts.append("")
                parts.append(f"  - reply to: @{reply_to} → [REDACTED-HANDLE]")
            parts.append("")
        out_path = out_dir / f"{year}.md"
        try:
            out_path.write_text("\n".join(parts), encoding="utf-8")
        except OSError as e:
            sys.stderr.write(f"exit 5: cannot write {out_path}: {e}\n")
            return 5
        written += 1
        sys.stdout.write(f"wrote {out_path}\n")

    sys.stdout.write(
        f"twitter import complete: {written} year-files, skipped={skipped}, "
        f"redaction={redaction_tag}\n"
    )
    return 10 if skipped else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
