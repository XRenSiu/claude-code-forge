#!/usr/bin/env python3
"""mbox_parser.py — Parse .mbox mail archives into per-thread Markdown.

Implements references/text-parsers.md §8 "Email":
  - stdlib ``mailbox`` + ``email`` modules.
  - Filters to threads the subject participates in (sender OR recipient
    matches ``--email-address``).
  - Emits one Markdown file per thread under
    ``{destination}/knowledge/articles/email/{YYYY-MM}-{subject-slug}.md``.
  - Simple quoted-reply stripping: strips repeated ``>`` lines beyond one
    level of quote context (keeps the first-level quote for readability).

Stdlib-only: mailbox, email, argparse, datetime, re, os, sys, pathlib.

CLI:
    python mbox_parser.py --mbox FILE --subject NAME --email-address ADDR \\
        --destination PATH [--no-redact]

Exit codes per cli-spec.md: 0 ok, 2 usage, 4 input, 5 output, 10 partial.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import email.utils
import mailbox
import os
import re
import sys
from email.header import decode_header, make_header
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redactor import redact, _warn_no_redact  # noqa: E402


def _today_tag() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%d")


def _today_iso() -> str:
    return _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _slugify(s: str, maxlen: int = 60) -> str:
    s = (s or "untitled").strip().lower()
    # Strip common reply/forward prefixes.
    s = re.sub(r"^(re|fwd|fw|回复|转发)[:：]\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", s, flags=re.UNICODE)
    s = re.sub(r"-+", "-", s).strip("-")
    return (s or "untitled")[:maxlen]


def _decode(value) -> str:
    if value is None:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)


def _normalize_subject(subj: str) -> str:
    s = re.sub(r"^(re|fwd|fw|回复|转发)[:：]\s*", "", subj or "",
               flags=re.IGNORECASE)
    return s.strip().lower()


def _addrs(value) -> list[str]:
    if not value:
        return []
    parts = email.utils.getaddresses([value])
    return [p[1].lower() for p in parts if p[1]]


def _extract_plaintext(msg) -> str:
    """Best-effort plain-text body extractor."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    payload = part.get_payload(decode=True) or b""
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
                except Exception:
                    continue
        # Fall back to any text/* payload.
        for part in msg.walk():
            if part.get_content_maintype() == "text":
                try:
                    payload = part.get_payload(decode=True) or b""
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
                except Exception:
                    continue
        return ""
    try:
        payload = msg.get_payload(decode=True) or b""
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    except Exception:
        return ""


def _strip_nested_quotes(body: str) -> str:
    """Keep one-level quotes (``>``) and strip deeper levels (``>>`` and up).

    Also drops bottom-signature boilerplate of the form ``-- \\n``.
    """
    out = []
    for line in body.splitlines():
        # Strip lines with 2+ leading '>' chars (nested quoted replies).
        if re.match(r"^\s*>{2,}", line):
            continue
        out.append(line)
    text = "\n".join(out)
    # Drop sig blocks: "-- \n...".
    text = re.split(r"\n-- \n", text, maxsplit=1)[0]
    return text.rstrip() + "\n"


def _parse_date(raw) -> _dt.datetime | None:
    if not raw:
        return None
    try:
        return email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None


def _frontmatter(*, subject: str, thread_subject: str,
                 redaction_tag: str) -> str:
    # YAML-safe subject string.
    safe_subject = thread_subject.replace('"', "'")
    return "\n".join([
        "---",
        "tier: primary",
        "tier_reason: private correspondence involving subject",
        "source_policy: private-correspondence",
        f'author_of_record: "{subject}"',
        f"captured_at: {_today_iso()}",
        "platform: email",
        f'thread_subject: "{safe_subject}"',
        f"redaction: {redaction_tag}",
        "---",
        "",
    ])


def _render_message(*, from_: str, date, body: str,
                    do_redact: bool, salt: str) -> str:
    date_str = date.strftime("%Y-%m-%d %H:%M") if date else "unknown"
    rendered_body = body.strip() or "[empty body]"
    if do_redact:
        from_ = redact(from_, salt=salt)
        rendered_body = redact(rendered_body, salt=salt)
    return (f"**From**: {from_}\n"
            f"**Date**: {date_str}\n\n"
            f"{rendered_body}\n")


def _main(argv) -> int:
    p = argparse.ArgumentParser(prog="mbox_parser.py", description=__doc__)
    p.add_argument("--mbox", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--email-address", required=True,
                   help="subject's email address (case-insensitive match)")
    p.add_argument("--destination", required=True)
    p.add_argument("--salt", default="distill-collector-v1")
    p.add_argument("--no-redact", action="store_true")
    args = p.parse_args(argv)

    mbox_path = Path(args.mbox)
    if not mbox_path.is_file():
        sys.stderr.write(f"exit 4: mbox not found: {mbox_path}\n")
        return 4

    subject_addr = args.email_address.lower()
    do_redact = not args.no_redact
    if args.no_redact:
        _warn_no_redact()
        redaction_tag = "disabled"
    else:
        redaction_tag = f"applied-v{_today_tag()}"

    try:
        box = mailbox.mbox(str(mbox_path))
    except (OSError, mailbox.Error) as e:
        sys.stderr.write(f"exit 4: cannot open mbox: {e}\n")
        return 4

    threads: dict[str, list[dict]] = {}
    skipped = 0
    for msg in box:
        from_ = _decode(msg.get("From"))
        to_ = _decode(msg.get("To"))
        cc_ = _decode(msg.get("Cc"))
        subj_raw = _decode(msg.get("Subject"))
        participants = set(_addrs(from_)) | set(_addrs(to_)) | set(_addrs(cc_))
        if subject_addr not in participants:
            continue
        body = _extract_plaintext(msg)
        if not body and not subj_raw:
            skipped += 1
            continue
        body = _strip_nested_quotes(body)
        date = _parse_date(msg.get("Date"))
        key = _normalize_subject(subj_raw)
        if not key:
            key = "no-subject"
        threads.setdefault(key, []).append({
            "from": from_,
            "date": date,
            "body": body,
            "subject": subj_raw or "(no subject)",
        })

    out_dir = Path(args.destination) / "knowledge" / "articles" / "email"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        sys.stderr.write(f"exit 5: cannot mkdir {out_dir}: {e}\n")
        return 5

    written = 0
    for key, msgs in threads.items():
        # Sort messages within thread chronologically.
        msgs.sort(key=lambda m: m["date"] or _dt.datetime.min)
        first_date = next((m["date"] for m in msgs if m["date"]), None)
        ymd = first_date.strftime("%Y-%m") if first_date else "unknown-date"
        thread_subject = msgs[0]["subject"]
        slug = _slugify(thread_subject)
        out_path = out_dir / f"{ymd}-{slug}.md"

        parts = [_frontmatter(subject=args.subject,
                              thread_subject=thread_subject,
                              redaction_tag=redaction_tag)]
        for i, m in enumerate(msgs):
            if i > 0:
                parts.append("\n---\n")
            parts.append(_render_message(
                from_=m["from"], date=m["date"], body=m["body"],
                do_redact=do_redact, salt=args.salt,
            ))
        try:
            out_path.write_text("\n".join(parts), encoding="utf-8")
        except OSError as e:
            sys.stderr.write(f"exit 5: cannot write {out_path}: {e}\n")
            return 5
        written += 1
        sys.stdout.write(f"wrote {out_path}\n")

    sys.stdout.write(
        f"mbox import complete: {written} threads, skipped={skipped}, "
        f"redaction={redaction_tag}\n"
    )
    return 10 if skipped else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
