#!/usr/bin/env python3
"""imessage_parser.py — Parse macOS iMessage chat.db into per-contact Markdown.

Reads ``~/Library/Messages/chat.db`` (or a user-supplied copy) via sqlite3
stdlib, groups messages by contact (handle), and emits one Markdown file per
contact under ``{destination}/knowledge/chats/imessage/{contact-slug}.md``.

Quirks handled:
  - Core Data timestamps: nanoseconds since 2001-01-01 UTC (Catalina+) OR
    seconds since 2001-01-01 UTC (older). Auto-detected by magnitude.
  - Message text can live in ``text`` column OR inside ``attributedBody``
    (NSArchiver blob). For attributedBody we best-effort byte-scan for the
    UTF-8 run following the known ``NSString`` marker; on failure we emit
    ``[UNREADABLE-ATTRIBUTED-BODY]`` and continue.

Stdlib-only: sqlite3, argparse, datetime, hashlib, os, re, sys, pathlib.

CLI:
    python imessage_parser.py --db PATH --subject NAME --destination PATH \\
        [--since YYYY-MM-DD] [--no-redact]

Exit codes per cli-spec.md: 0 ok, 2 usage, 4 input, 5 output, 10 partial.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redactor import redact, _warn_no_redact  # noqa: E402

# 2001-01-01 00:00:00 UTC = iMessage epoch (Apple Core Data reference date).
APPLE_EPOCH = _dt.datetime(2001, 1, 1, tzinfo=_dt.timezone.utc)


def _slugify(s: str) -> str:
    s = (s or "unknown").strip().lower()
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", s, flags=re.UNICODE)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "unknown"


def _today_tag() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%d")


def _today_iso() -> str:
    return _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _apple_ts_to_dt(raw: int):
    """Convert a Core Data timestamp to a timezone-aware datetime.

    Catalina+ stores nanoseconds; older schemas store seconds. Detect by
    magnitude: values > 10**11 are nanoseconds.
    """
    if raw is None:
        return None
    try:
        raw = int(raw)
    except (TypeError, ValueError):
        return None
    seconds = raw / 1e9 if raw > 10**11 else float(raw)
    try:
        return APPLE_EPOCH + _dt.timedelta(seconds=seconds)
    except (OverflowError, OSError, ValueError):
        return None


# Known NSString marker inside attributedBody NSArchiver blobs.
_NSSTRING_MARKER = b"NSString"


def _extract_attributed_body(blob) -> str:
    """Best-effort UTF-8 text recovery from an attributedBody blob.

    NSArchiver encoding lays the string after an NSString class reference and
    a length byte (or 0x81 + two-byte length for longer strings). We scan for
    the marker and try to decode a trailing UTF-8 run.
    """
    if not blob:
        return "[UNREADABLE-ATTRIBUTED-BODY]"
    try:
        data = bytes(blob)
    except Exception:
        return "[UNREADABLE-ATTRIBUTED-BODY]"
    idx = data.find(_NSSTRING_MARKER)
    if idx < 0:
        return "[UNREADABLE-ATTRIBUTED-BODY]"
    # After NSString marker: skip ahead past class-ref bytes; try a range of
    # offsets and pick the first that yields >3 printable chars.
    search_from = idx + len(_NSSTRING_MARKER)
    window = data[search_from:search_from + 4096]
    for start in range(0, min(64, len(window))):
        tail = window[start:]
        # Heuristic: find first byte that looks like ASCII printable.
        m = re.search(rb"[\x20-\x7e\xc0-\xff][\x20-\x7e\x80-\xff]{2,}", tail)
        if not m:
            continue
        candidate = tail[m.start():]
        # Trim at first NUL or known control trailer.
        end = candidate.find(b"\x00")
        if end > 0:
            candidate = candidate[:end]
        try:
            decoded = candidate.decode("utf-8", errors="strict").strip()
        except UnicodeDecodeError:
            continue
        # Filter out short or class-name-ish decodes.
        if len(decoded) >= 2 and not decoded.startswith(("NS", "iI", "$")):
            # Drop trailing NSArchiver bookkeeping if any ASCII class ref sneaks in.
            decoded = re.split(r"iI\\+|NSDictionary|NSAttributes", decoded)[0]
            decoded = decoded.strip()
            if decoded:
                return decoded
    return "[UNREADABLE-ATTRIBUTED-BODY]"


def _frontmatter(*, subject: str, contact: str, captured: str,
                 redaction_tag: str) -> str:
    return "\n".join([
        "---",
        "tier: primary",
        "tier_reason: direct conversation with subject",
        "source_policy: private-chat",
        f'author_of_record: "{subject}"',
        f"captured_at: {captured}",
        "platform: imessage",
        f'contact: "{contact}"',
        f"redaction: {redaction_tag}",
        "---",
        "",
    ])


def _render_messages(rows, subject: str, salt: str, do_redact: bool):
    """Render message rows grouped by day.

    Rows: list of (datetime, is_from_me, text)
    """
    out, current_date = [], None
    skipped = 0
    for ts, is_from_me, text in rows:
        if ts is None:
            skipped += 1
            continue
        date = ts.strftime("%Y-%m-%d")
        if date != current_date:
            if current_date is not None:
                out.append("")
            out.append(f"## {date}")
            out.append("")
            current_date = date
        hhmm = ts.strftime("%H:%M")
        speaker = subject if is_from_me else "PersonA"
        body = text or ""
        if do_redact:
            body = redact(body, salt=salt)
        out.append(f"**{hhmm} · {speaker}**: {body}")
    return "\n".join(out) + "\n", skipped


def _query(db_path: Path, since: _dt.datetime | None):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    sql = (
        "SELECT h.id AS contact, m.date AS raw_date, m.is_from_me, "
        "       m.text AS text, m.attributedBody AS attr "
        "FROM message m "
        "LEFT JOIN handle h ON m.handle_id = h.ROWID "
        "ORDER BY m.date ASC"
    )
    grouped: dict[str, list] = {}
    skipped = 0
    for row in cur.execute(sql):
        ts = _apple_ts_to_dt(row["raw_date"])
        if ts is None:
            skipped += 1
            continue
        if since and ts.replace(tzinfo=None) < since:
            continue
        text = row["text"]
        if not text:
            text = _extract_attributed_body(row["attr"])
        contact = row["contact"] or "unknown"
        grouped.setdefault(contact, []).append((ts, int(row["is_from_me"] or 0), text))
    con.close()
    return grouped, skipped


def _main(argv) -> int:
    p = argparse.ArgumentParser(prog="imessage_parser.py", description=__doc__)
    p.add_argument("--db", required=True, help="path to chat.db")
    p.add_argument("--subject", required=True)
    p.add_argument("--destination", required=True)
    p.add_argument("--since", help="YYYY-MM-DD lower bound (inclusive)")
    p.add_argument("--salt", default="distill-collector-v1")
    p.add_argument("--no-redact", action="store_true")
    args = p.parse_args(argv)

    db_path = Path(os.path.expanduser(args.db))
    if not db_path.is_file():
        sys.stderr.write(f"exit 4: chat.db not found: {db_path}\n")
        sys.stderr.write("        (macOS requires Full Disk Access for ~/Library/Messages)\n")
        return 4

    since_dt = None
    if args.since:
        try:
            since_dt = _dt.datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            sys.stderr.write("exit 2: --since must be YYYY-MM-DD\n")
            return 2

    if args.no_redact:
        _warn_no_redact()
        redaction_tag = "disabled"
        do_redact = False
    else:
        redaction_tag = f"applied-v{_today_tag()}"
        do_redact = True

    try:
        grouped, skipped_rows = _query(db_path, since_dt)
    except sqlite3.DatabaseError as e:
        sys.stderr.write(f"exit 4: cannot open/query chat.db: {e}\n")
        return 4

    out_dir = Path(args.destination) / "knowledge" / "chats" / "imessage"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        sys.stderr.write(f"exit 5: cannot mkdir {out_dir}: {e}\n")
        return 5

    partial = skipped_rows > 0
    written = 0
    for contact, rows in grouped.items():
        if not rows:
            continue
        body_md, skipped_inside = _render_messages(
            rows, args.subject, args.salt, do_redact,
        )
        if skipped_inside:
            partial = True
        # Per text-parsers.md §6: phone/email in the `contact` field is
        # redacted (the slug uses a hash so the file path doesn't leak PII).
        slug_basis = contact
        if do_redact:
            display_contact = redact(contact, salt=args.salt)
        else:
            display_contact = contact
        fm = _frontmatter(subject=args.subject,
                          contact=display_contact,
                          captured=_today_iso(),
                          redaction_tag=redaction_tag)
        slug = _slugify(display_contact if do_redact else slug_basis)
        out_path = out_dir / f"{slug}.md"
        try:
            out_path.write_text(fm + body_md, encoding="utf-8")
        except OSError as e:
            sys.stderr.write(f"exit 5: cannot write {out_path}: {e}\n")
            return 5
        written += 1
        sys.stdout.write(f"wrote {out_path}\n")

    sys.stdout.write(
        f"iMessage import complete: {written} contacts, "
        f"skipped_rows={skipped_rows}, redaction={redaction_tag}\n"
    )
    if partial:
        return 10
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
