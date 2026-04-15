#!/usr/bin/env python3
"""telegram_parser.py — Import Telegram Desktop JSON export into knowledge/.

Supports the `result.json` produced by:
  Telegram Desktop → Settings → Advanced → Export Telegram data → JSON

Expected top-level structure:
  {
    "about": "...",
    "personal_information": {"first_name": "...", ...},
    "chats": {
      "list": [
        {
          "name": "Chat name",
          "type": "personal_chat | private_group | ...",
          "id": 12345,
          "messages": [
            {"id": 1, "type": "message", "date": "2024-01-15T10:30:00",
             "from": "Alice", "from_id": "user12345",
             "text": "Hello" | [list of rich parts]},
            ...
          ]
        },
        ...
      ]
    }
  }

Implements the text-parser contract from references/text-parsers.md §7.
Always runs redactor before write unless --no-redact (with stderr WARN).

Stdlib-only: argparse, datetime, json, os, re, sys, pathlib.

CLI:
    python telegram_parser.py --source result.json --subject NAME \\
        --destination PATH [--chat-filter SUBSTRING] [--no-redact]

Exit codes per cli-spec.md: 0 ok, 2 usage, 4 input, 5 output.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redactor import redact, _warn_no_redact  # noqa: E402

POLICY_VERSION = "applied-v20260415"


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", s, flags=re.UNICODE)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:60] or "untitled"


def _today_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_text(msg: Dict[str, Any]) -> str:
    """Telegram text is either a string or a list of {type, text} parts."""
    t = msg.get("text", "")
    if isinstance(t, str):
        return t
    if isinstance(t, list):
        parts: List[str] = []
        for p in t:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict):
                parts.append(str(p.get("text", "")))
        return "".join(parts)
    return ""


def _render_chat(chat: Dict[str, Any], subject: str) -> str:
    name = chat.get("name") or "unnamed-chat"
    chat_type = chat.get("type", "unknown")
    messages = chat.get("messages", []) or []
    header = [
        "---",
        "source: telegram",
        f"chat_name: {json.dumps(name, ensure_ascii=False)}",
        f"chat_type: {chat_type}",
        f"subject: {json.dumps(subject, ensure_ascii=False)}",
        f"captured_at: {_today_iso()}",
        f"tier: primary",
        f"tier_reason: verbatim chat messages authored by participants",
        f"access_level: private",
        f"access_reason: Telegram personal chat / private group (access_level per primary-vs-secondary.md v0.2.0)",
        f"audience: specific_individuals",
        f"redaction: {POLICY_VERSION}",
        "---",
        "",
        f"# Telegram chat: {name}",
        "",
    ]
    lines: List[str] = []
    for m in messages:
        if m.get("type") != "message":
            # service / pinned / action messages are skipped
            continue
        when = m.get("date", "") or m.get("date_unixtime", "")
        who = m.get("from") or m.get("from_id") or "unknown"
        text = _extract_text(m)
        if not text:
            # media-only message
            media_type = m.get("media_type") or m.get("mime_type") or "media"
            text = f"[{media_type}]"
        # one message per bullet; preserve internal linebreaks as <br>-style
        text = text.replace("\n", "\n  ")
        lines.append(f"- **{who}** @ `{when}` — {text}")
    return "\n".join(header + lines) + "\n"


def _run(
    source: str,
    subject: str,
    destination: str,
    chat_filter: Optional[str],
    no_redact: bool,
) -> int:
    try:
        with open(source, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        sys.stderr.write(f"exit 4: cannot read/parse {source}: {e}\n")
        return 4

    chats = (data.get("chats", {}) or {}).get("list", [])
    if not isinstance(chats, list) or not chats:
        sys.stderr.write(f"exit 4: {source} has no chats.list\n")
        return 4

    dest_root = Path(destination) / "knowledge" / "chats" / "telegram"
    try:
        dest_root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        sys.stderr.write(f"exit 5: cannot create {dest_root}: {e}\n")
        return 5

    written = 0
    skipped = 0
    for chat in chats:
        name = chat.get("name") or ""
        if chat_filter and chat_filter.lower() not in name.lower():
            skipped += 1
            continue
        # Skip empty chats
        messages = chat.get("messages", []) or []
        if not any(m.get("type") == "message" for m in messages):
            skipped += 1
            continue
        rendered = _render_chat(chat, subject)
        if no_redact:
            _warn_no_redact()
            out = rendered
            redact_tag = "disabled"
        else:
            out = redact(rendered)
            redact_tag = POLICY_VERSION
        # Swap in real redaction tag in frontmatter (we emitted POLICY_VERSION
        # before redaction since the tag itself must reflect what happened).
        out = out.replace(
            f"redaction: {POLICY_VERSION}",
            f"redaction: {redact_tag}",
            1,
        )
        slug = _slugify(name) or f"chat-{chat.get('id', 'x')}"
        target = dest_root / f"{slug}.md"
        try:
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(out)
        except OSError as e:
            sys.stderr.write(f"exit 5: cannot write {target}: {e}\n")
            return 5
        written += 1
        print(f"wrote {target}", file=sys.stderr)

    print(
        f"telegram_parser: wrote {written} chat files, skipped {skipped}",
        file=sys.stderr,
    )
    return 0


def _main(argv) -> int:
    p = argparse.ArgumentParser(prog="telegram_parser.py", description=__doc__)
    p.add_argument("--source", help="Path to Telegram Desktop result.json")
    p.add_argument("--subject", help="Primary subject name (preserved verbatim)")
    p.add_argument(
        "--destination",
        help="Persona-skill root — knowledge/chats/telegram/ is created under it",
    )
    p.add_argument(
        "--chat-filter",
        dest="chat_filter",
        help="Only export chats whose name contains this substring (case-insensitive)",
    )
    p.add_argument(
        "--no-redact",
        action="store_true",
        help="skip redaction (writes raw text; prints WARN to stderr)",
    )
    p.add_argument("--test", action="store_true", help="run self-tests and exit")
    args = p.parse_args(list(argv))

    if args.test:
        return _run_selftest()

    if not (args.source and args.subject and args.destination):
        p.print_usage(sys.stderr)
        sys.stderr.write("exit 2: --source, --subject, --destination required\n")
        return 2

    return _run(
        args.source,
        args.subject,
        args.destination,
        args.chat_filter,
        args.no_redact,
    )


# --------------------------------------------------------------------------
# Embedded self-test.
# --------------------------------------------------------------------------

import tempfile
import unittest


class _TelegramParserTests(unittest.TestCase):

    FIXTURE = {
        "about": "Telegram Desktop data export",
        "chats": {
            "list": [
                {
                    "name": "Alice",
                    "type": "personal_chat",
                    "id": 1001,
                    "messages": [
                        {
                            "id": 1,
                            "type": "message",
                            "date": "2024-01-15T10:30:00",
                            "from": "Alice",
                            "from_id": "user1001",
                            "text": "Hi there! My number is 13812345678.",
                        },
                        {
                            "id": 2,
                            "type": "service",
                            "date": "2024-01-15T10:31:00",
                        },
                        {
                            "id": 3,
                            "type": "message",
                            "date": "2024-01-15T10:32:00",
                            "from": "Me",
                            "from_id": "user42",
                            "text": [
                                {"type": "plain", "text": "Hello "},
                                {"type": "bold", "text": "Alice"},
                            ],
                        },
                        {
                            "id": 4,
                            "type": "message",
                            "date": "2024-01-15T10:33:00",
                            "from": "Alice",
                            "from_id": "user1001",
                            "media_type": "sticker",
                            "text": "",
                        },
                    ],
                },
                {
                    "name": "Empty Group",
                    "type": "private_group",
                    "id": 1002,
                    "messages": [{"id": 1, "type": "service"}],
                },
            ]
        },
    }

    def _run_fixture(self, no_redact=False):
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "result.json")
            with open(src, "w") as fh:
                json.dump(self.FIXTURE, fh)
            dest = os.path.join(td, "skill")
            rc = _run(src, "Xiao Ming", dest, None, no_redact)
            self.assertEqual(rc, 0)
            out_dir = Path(dest) / "knowledge" / "chats" / "telegram"
            files = sorted(out_dir.iterdir())
            return files, {f.name: f.read_text() for f in files}

    def test_writes_one_file_per_nonempty_chat(self):
        files, _ = self._run_fixture()
        # Alice chat written; Empty Group has only service messages → skipped
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "alice.md")

    def test_rich_text_concatenation(self):
        _, contents = self._run_fixture()
        c = contents["alice.md"]
        self.assertIn("Hello Alice", c)  # rich parts merged

    def test_service_messages_skipped(self):
        _, contents = self._run_fixture()
        c = contents["alice.md"]
        # 3 real messages (1, 3, 4); service message 2 excluded
        self.assertEqual(c.count("- **"), 3)

    def test_media_placeholder(self):
        _, contents = self._run_fixture()
        c = contents["alice.md"]
        self.assertIn("[sticker]", c)

    def test_phone_redacted_by_default(self):
        _, contents = self._run_fixture(no_redact=False)
        c = contents["alice.md"]
        self.assertIn("REDACTED:PHONE-", c)
        self.assertNotIn("13812345678", c)

    def test_no_redact_writes_raw_and_tag_is_disabled(self):
        _, contents = self._run_fixture(no_redact=True)
        c = contents["alice.md"]
        self.assertIn("13812345678", c)
        self.assertIn("redaction: disabled", c)

    def test_access_level_is_private(self):
        _, contents = self._run_fixture()
        c = contents["alice.md"]
        self.assertIn("access_level: private", c)

    def test_redaction_tag_on_success(self):
        _, contents = self._run_fixture()
        c = contents["alice.md"]
        self.assertIn(f"redaction: {POLICY_VERSION}", c)


def _run_selftest() -> int:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(_TelegramParserTests)
    runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
