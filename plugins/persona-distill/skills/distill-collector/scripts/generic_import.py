#!/usr/bin/env python3
"""generic_import.py — Import a plain .txt / .md file into knowledge/.

Implements the "Generic Text" parser from references/text-parsers.md §10
(`distill-collector import --format generic` per cli-spec.md §5).

Heuristics (per text-parsers.md §10):
  1. Blank line = message boundary.
  2. ``^\\s*([^:\\n]{1,40}):\\s`` = speaker prefix; left side becomes speaker.
  3. ``^>`` = quoted prior message (preserved as blockquote).
  4. ``[image] / [video] / [file]`` lines collapse to attachment placeholder.
  5. If no speaker prefix detected anywhere, wrap as a single article under
     ``knowledge/articles/generic/{slug}.md``.

Stdlib-only: argparse, datetime, hashlib, os, re, sys, pathlib.
Always runs the redactor before writing (unless --no-redact, with stderr WARN).

CLI:
    python generic_import.py --source FILE --subject NAME --destination PATH \\
        [--no-redact]

Exit codes per cli-spec.md: 0 ok, 2 usage, 4 input, 5 output.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import sys
from pathlib import Path

# Make `import redactor` work whether run from anywhere.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redactor import redact, _warn_no_redact  # noqa: E402

SPEAKER_RE = re.compile(r"^\s*([^:\n]{1,40}):\s+(.*)$")
QUOTE_RE = re.compile(r"^>\s?(.*)$")
ATTACHMENT_RE = re.compile(r"^\s*\[(image|video|file|audio)\].*$", re.IGNORECASE)


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", s, flags=re.UNICODE)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"


def _today_iso() -> str:
    return _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_tag() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%d")


def _has_speakers(text: str) -> bool:
    for line in text.splitlines():
        if SPEAKER_RE.match(line):
            return True
    return False


def _render_chat(text: str, subject: str) -> str:
    """Convert raw text into chat-style Markdown blocks."""
    blocks = re.split(r"\n\s*\n", text.strip())
    out_lines = []
    for blk in blocks:
        rendered_lines = []
        for raw in blk.splitlines():
            line = raw.rstrip()
            if not line:
                continue
            qm = QUOTE_RE.match(line)
            if qm:
                rendered_lines.append(f"> {qm.group(1)}")
                continue
            am = ATTACHMENT_RE.match(line)
            if am:
                rendered_lines.append(
                    f"_[attachment: {am.group(1).lower()} → redacted]_"
                )
                continue
            sm = SPEAKER_RE.match(line)
            if sm:
                speaker, body = sm.group(1).strip(), sm.group(2).strip()
                rendered_lines.append(f"**{speaker}**: {body}")
                continue
            rendered_lines.append(line)
        if rendered_lines:
            out_lines.append("\n".join(rendered_lines))
    return "\n\n".join(out_lines)


def _render_article(text: str) -> str:
    return text.strip()


def _frontmatter(*, subject: str, kind: str, source_path: str,
                 redaction_tag: str) -> str:
    fields = [
        "---",
        "tier: primary",
        "tier_reason: user-provided generic import",
        "source_policy: user-provided",
        f'author_of_record: "{subject}"',
        f"captured_at: {_today_iso()}",
        "platform: generic",
        f'source_file: "{os.path.basename(source_path)}"',
        f"redaction: {redaction_tag}",
        "---",
        "",
    ]
    return "\n".join(fields)


def _main(argv) -> int:
    p = argparse.ArgumentParser(prog="generic_import.py", description=__doc__)
    p.add_argument("--source", required=True, help="path to .txt / .md file")
    p.add_argument("--subject", required=True,
                   help="canonical display name of the persona subject")
    p.add_argument("--destination", required=True,
                   help="persona-skill root or knowledge/ directory")
    p.add_argument("--salt", default="distill-collector-v1")
    p.add_argument("--no-redact", action="store_true")
    args = p.parse_args(argv)

    src_path = Path(args.source)
    if not src_path.is_file():
        sys.stderr.write(f"exit 4: source not readable: {src_path}\n")
        return 4

    try:
        raw = src_path.read_text(encoding="utf-8")
    except OSError as e:
        sys.stderr.write(f"exit 4: cannot read {src_path}: {e}\n")
        return 4

    is_chat = _has_speakers(raw)

    if args.no_redact:
        _warn_no_redact()
        body_text = raw
        redaction_tag = "disabled"
    else:
        body_text = redact(raw, salt=args.salt)
        redaction_tag = f"applied-v{_today_tag()}"

    body_md = _render_chat(body_text, args.subject) if is_chat \
        else _render_article(body_text)
    fm = _frontmatter(subject=args.subject,
                      kind="chat" if is_chat else "article",
                      source_path=str(src_path),
                      redaction_tag=redaction_tag)
    output = fm + body_md + "\n"

    dest_root = Path(args.destination)
    if dest_root.name == "knowledge":
        knowledge = dest_root
    else:
        knowledge = dest_root / "knowledge"
    sub = "chats/generic" if is_chat else "articles/generic"
    out_dir = knowledge / sub
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        sys.stderr.write(f"exit 5: cannot mkdir {out_dir}: {e}\n")
        return 5

    slug = _slugify(src_path.stem)
    out_path = out_dir / f"{slug}-{_today_tag()}.md"
    try:
        out_path.write_text(output, encoding="utf-8")
    except OSError as e:
        sys.stderr.write(f"exit 5: cannot write {out_path}: {e}\n")
        return 5

    sys.stdout.write(
        f"wrote {out_path}  (redaction: {redaction_tag}, "
        f"shape: {'chat' if is_chat else 'article'})\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
