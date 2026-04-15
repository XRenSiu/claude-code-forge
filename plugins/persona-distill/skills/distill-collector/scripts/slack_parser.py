#!/usr/bin/env python3
"""slack_parser.py — Import Slack workspace JSON export into knowledge/.

Supports the standard Slack export format:
  Slack workspace → Settings → Import/Export Data → Export

Export directory layout:
  export-root/
    users.json              — array of {id, name, real_name, ...}
    channels.json           — public channels
    groups.json             — (optional) private channels
    mpims.json              — (optional) multi-person DMs
    dms.json                — (optional) 1-on-1 DMs
    <channel-name>/
      YYYY-MM-DD.json       — array of message objects per day
    ...

Per-message JSON fields of interest:
  {
    "type": "message",
    "subtype": "bot_message | file_share | ...",  # optional
    "ts": "1704103200.000100",
    "user": "U12345" | (absent for bots),
    "text": "Hello <@U67890>",
    "thread_ts": "..."  # if threaded
  }

Access level mapping (per primary-vs-secondary.md v0.2.0):
  channels/* → semi-public (internal org)
  groups/*   → private
  mpims/*    → private
  dms/*      → private

Always runs redactor before write unless --no-redact.

Stdlib-only: argparse, datetime, json, os, re, sys, pathlib.

CLI:
    python slack_parser.py --source EXPORT_DIR --subject NAME \\
        --destination SKILL_ROOT [--channel-filter SUBSTRING] [--no-redact]

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


def _ts_to_iso(ts: str) -> str:
    try:
        return _dt.datetime.fromtimestamp(
            float(ts), _dt.timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        return ts or ""


def _load_users(export_dir: Path) -> Dict[str, str]:
    """Return user_id → display_name map."""
    users_file = export_dir / "users.json"
    if not users_file.exists():
        return {}
    try:
        users = json.loads(users_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    m: Dict[str, str] = {}
    for u in users:
        if not isinstance(u, dict):
            continue
        uid = u.get("id")
        name = u.get("real_name") or u.get("name") or uid
        if uid:
            m[uid] = name
    return m


def _resolve_mentions(text: str, user_map: Dict[str, str]) -> str:
    """Replace <@U12345> with readable names."""
    def repl(m):
        uid = m.group(1)
        return f"@{user_map.get(uid, uid)}"
    return re.sub(r"<@([A-Z0-9]+)>", repl, text or "")


def _collect_channel_messages(channel_dir: Path) -> List[Dict[str, Any]]:
    """Slack exports one JSON file per day of messages per channel."""
    day_files = sorted(channel_dir.glob("*.json"))
    messages: List[Dict[str, Any]] = []
    for df in day_files:
        try:
            day = json.loads(df.read_text(encoding="utf-8"))
            if isinstance(day, list):
                messages.extend(day)
        except (OSError, json.JSONDecodeError):
            continue
    return messages


def _classify_access(category: str) -> str:
    """Map Slack channel category to access_level."""
    return {
        "channels": "semi-public",
        "groups": "private",
        "mpims": "private",
        "dms": "private",
    }.get(category, "private")


def _classify_audience(category: str) -> str:
    return {
        "channels": "internal_org",
        "groups": "specific_individuals",
        "mpims": "specific_individuals",
        "dms": "specific_individuals",
    }.get(category, "specific_individuals")


def _render_channel(
    channel_meta: Dict[str, Any],
    messages: List[Dict[str, Any]],
    user_map: Dict[str, str],
    category: str,
    subject: str,
) -> str:
    name = channel_meta.get("name") or channel_meta.get("id") or "unknown"
    access = _classify_access(category)
    audience = _classify_audience(category)
    header = [
        "---",
        "source: slack",
        f"category: {category}",
        f"channel_name: {json.dumps(name, ensure_ascii=False)}",
        f"subject: {json.dumps(subject, ensure_ascii=False)}",
        f"captured_at: {_today_iso()}",
        "tier: primary",
        "tier_reason: verbatim Slack messages authored by participants",
        f"access_level: {access}",
        f"access_reason: Slack {category}/ export (primary-vs-secondary.md v0.2.0)",
        f"audience: {audience}",
        f"redaction: {POLICY_VERSION}",
        "---",
        "",
        f"# Slack {category}: {name}",
        "",
    ]
    lines: List[str] = []
    for m in messages:
        if m.get("type") != "message":
            continue
        # skip messages that are channel join/leave notifications
        subtype = m.get("subtype", "")
        if subtype in {"channel_join", "channel_leave", "channel_topic"}:
            continue
        when = _ts_to_iso(m.get("ts", ""))
        uid = m.get("user") or m.get("bot_id") or "unknown"
        who = user_map.get(uid, uid)
        text = _resolve_mentions(m.get("text", ""), user_map)
        if not text.strip():
            # file-share or other media-only message
            files = m.get("files") or []
            if files:
                text = f"[file-share: {len(files)} attachment(s)]"
            else:
                text = "[empty]"
        text = text.replace("\n", "\n  ")
        lines.append(f"- **{who}** @ `{when}` — {text}")
    return "\n".join(header + lines) + "\n"


def _find_channels(export_dir: Path, category: str) -> List[Dict[str, Any]]:
    """Read `<category>.json` index file."""
    index_file = export_dir / f"{category}.json"
    if not index_file.exists():
        return []
    try:
        arr = json.loads(index_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return arr if isinstance(arr, list) else []


def _run(
    source: str,
    subject: str,
    destination: str,
    channel_filter: Optional[str],
    no_redact: bool,
) -> int:
    export_dir = Path(source)
    if not export_dir.is_dir():
        sys.stderr.write(f"exit 4: {source} is not a directory\n")
        return 4

    user_map = _load_users(export_dir)
    dest_root = Path(destination) / "knowledge" / "chats" / "slack"
    try:
        dest_root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        sys.stderr.write(f"exit 5: cannot create {dest_root}: {e}\n")
        return 5

    categories = ["channels", "groups", "mpims", "dms"]
    written = 0
    skipped = 0
    for cat in categories:
        entries = _find_channels(export_dir, cat)
        for ch in entries:
            name = ch.get("name") or ch.get("id") or ""
            if channel_filter and channel_filter.lower() not in name.lower():
                skipped += 1
                continue
            # Channel directory: export puts msgs under <name>/ for channels,
            # groups; under <id>/ for dms/mpims sometimes. Check both.
            cand = [export_dir / name]
            if ch.get("id"):
                cand.append(export_dir / ch["id"])
            ch_dir = next((d for d in cand if d.is_dir()), None)
            if not ch_dir:
                skipped += 1
                continue
            messages = _collect_channel_messages(ch_dir)
            if not messages:
                skipped += 1
                continue
            rendered = _render_channel(ch, messages, user_map, cat, subject)
            if no_redact:
                _warn_no_redact()
                out = rendered
                redact_tag = "disabled"
            else:
                out = redact(rendered)
                redact_tag = POLICY_VERSION
            out = out.replace(
                f"redaction: {POLICY_VERSION}",
                f"redaction: {redact_tag}",
                1,
            )
            out_dir = dest_root / cat
            out_dir.mkdir(parents=True, exist_ok=True)
            slug = _slugify(name) or f"ch-{ch.get('id','x')}"
            target = out_dir / f"{slug}.md"
            try:
                with open(target, "w", encoding="utf-8") as fh:
                    fh.write(out)
            except OSError as e:
                sys.stderr.write(f"exit 5: cannot write {target}: {e}\n")
                return 5
            written += 1
            print(f"wrote {target}", file=sys.stderr)

    print(
        f"slack_parser: wrote {written} files, skipped {skipped}",
        file=sys.stderr,
    )
    return 0


def _main(argv) -> int:
    p = argparse.ArgumentParser(prog="slack_parser.py", description=__doc__)
    p.add_argument("--source", help="Path to Slack export directory (unzipped)")
    p.add_argument("--subject", help="Primary subject name (preserved verbatim)")
    p.add_argument(
        "--destination",
        help="Persona-skill root — knowledge/chats/slack/ created under it",
    )
    p.add_argument(
        "--channel-filter",
        dest="channel_filter",
        help="Only export channels whose name contains this substring",
    )
    p.add_argument(
        "--no-redact",
        action="store_true",
        help="skip redaction (writes raw text; prints WARN)",
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
        args.channel_filter,
        args.no_redact,
    )


# --------------------------------------------------------------------------
# Embedded self-test (synthesizes a minimal Slack export layout in temp dir).
# --------------------------------------------------------------------------

import tempfile
import unittest


class _SlackParserTests(unittest.TestCase):

    def _setup_fixture(self, td: str) -> None:
        ex = Path(td)
        (ex / "users.json").write_text(json.dumps([
            {"id": "U001", "name": "alice", "real_name": "Alice"},
            {"id": "U002", "name": "bob", "real_name": "Bob"},
        ]))
        (ex / "channels.json").write_text(json.dumps([
            {"id": "C001", "name": "general"},
            {"id": "C002", "name": "empty-channel"},
        ]))
        (ex / "groups.json").write_text(json.dumps([
            {"id": "G001", "name": "private-project"},
        ]))
        (ex / "dms.json").write_text(json.dumps([
            {"id": "D001"},  # DMs have no name
        ]))
        # general channel messages
        (ex / "general").mkdir()
        (ex / "general" / "2024-01-15.json").write_text(json.dumps([
            {
                "type": "message",
                "subtype": "channel_join",
                "user": "U001",
                "ts": "1705300000.000001",
                "text": "has joined",
            },
            {
                "type": "message",
                "user": "U001",
                "ts": "1705300100.000001",
                "text": "Hi <@U002>, my number is 13812345678",
            },
            {
                "type": "message",
                "user": "U002",
                "ts": "1705300200.000001",
                "text": "hey!",
            },
        ]))
        # empty channel (no message files)
        (ex / "empty-channel").mkdir()
        # private group
        (ex / "private-project").mkdir()
        (ex / "private-project" / "2024-01-20.json").write_text(json.dumps([
            {
                "type": "message",
                "user": "U001",
                "ts": "1705708800.000001",
                "text": "top secret",
            },
        ]))
        # DM (uses id as dir name)
        (ex / "D001").mkdir()
        (ex / "D001" / "2024-02-01.json").write_text(json.dumps([
            {
                "type": "message",
                "user": "U001",
                "ts": "1706745600.000001",
                "text": "直接聊聊",
            },
        ]))

    def _run_fixture(self, no_redact=False, channel_filter=None):
        with tempfile.TemporaryDirectory() as td:
            self._setup_fixture(td)
            dest = os.path.join(td, "skill")
            rc = _run(td, "Xiao Ming", dest, channel_filter, no_redact)
            self.assertEqual(rc, 0)
            out = {}
            for cat in ["channels", "groups", "mpims", "dms"]:
                d = Path(dest) / "knowledge" / "chats" / "slack" / cat
                if d.is_dir():
                    out[cat] = {f.name: f.read_text() for f in d.iterdir()}
            return out

    def test_channels_written(self):
        out = self._run_fixture()
        self.assertIn("channels", out)
        self.assertIn("general.md", out["channels"])

    def test_groups_written(self):
        out = self._run_fixture()
        self.assertIn("groups", out)
        self.assertIn("private-project.md", out["groups"])

    def test_dms_written(self):
        out = self._run_fixture()
        self.assertIn("dms", out)
        # DM name falls back to id slug
        self.assertTrue(any("d001" in k for k in out["dms"]))

    def test_empty_channel_skipped(self):
        out = self._run_fixture()
        self.assertNotIn("empty-channel.md", out.get("channels", {}))

    def test_channel_join_skipped(self):
        out = self._run_fixture()
        c = out["channels"]["general.md"]
        self.assertNotIn("has joined", c)

    def test_mentions_resolved(self):
        out = self._run_fixture()
        c = out["channels"]["general.md"]
        self.assertIn("@Bob", c)  # <@U002> resolved
        self.assertNotIn("<@U002>", c)

    def test_phone_redacted_by_default(self):
        out = self._run_fixture()
        c = out["channels"]["general.md"]
        self.assertIn("REDACTED:PHONE-", c)
        self.assertNotIn("13812345678", c)

    def test_channel_access_is_semi_public(self):
        out = self._run_fixture()
        c = out["channels"]["general.md"]
        self.assertIn("access_level: semi-public", c)

    def test_group_access_is_private(self):
        out = self._run_fixture()
        c = out["groups"]["private-project.md"]
        self.assertIn("access_level: private", c)

    def test_dm_access_is_private(self):
        out = self._run_fixture()
        dm_key = next(iter(out["dms"].keys()))
        self.assertIn("access_level: private", out["dms"][dm_key])

    def test_filter(self):
        out = self._run_fixture(channel_filter="general")
        # Only general survives; private-project skipped
        self.assertIn("general.md", out.get("channels", {}))
        self.assertNotIn("groups", out)

    def test_real_name_resolved(self):
        out = self._run_fixture()
        c = out["channels"]["general.md"]
        self.assertIn("**Alice**", c)

    def test_no_redact_preserves_phone(self):
        out = self._run_fixture(no_redact=True)
        c = out["channels"]["general.md"]
        self.assertIn("13812345678", c)
        self.assertIn("redaction: disabled", c)


def _run_selftest() -> int:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(_SlackParserTests)
    runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
