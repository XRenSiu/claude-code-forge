#!/usr/bin/env python3
"""Package integration checks; not a Skill behavior evaluation."""

import json
import re
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
REPO = PLUGIN.parents[1]
SKILL = PLUGIN / "skills/accept-change"
sys.path.insert(0, str(SKILL / "scripts"))
from protocol import CONFIG, REQUEST, load, validate, validate_contract


def main():
    manifest = load(PLUGIN / ".claude-plugin/plugin.json")
    marketplace = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    entries = [item for item in marketplace["plugins"] if item["name"] == manifest["name"]]
    assert len(entries) == 1, "plugin must be registered exactly once"
    entry = entries[0]
    text = (SKILL / "SKILL.md").read_text()
    frontmatter = text.split("---", 2)[1]
    version = re.search(r"^version: (.+)$", frontmatter, re.M).group(1)
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    assert version == manifest["version"] == entry["version"], "three versions must match"
    assert entry["source"] == "./plugins/trusted-acceptance"
    assert re.search(r"^name: accept-change$", frontmatter, re.M)
    assert "description:" in frontmatter
    for markdown in PLUGIN.rglob("*.md"):
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown.read_text()):
            if "://" in link or link.startswith("#"):
                continue
            assert (markdown.parent / link.split("#")[0]).exists(), f"broken link: {markdown}: {link}"
    validate(load(SKILL / "assets/request.example.json"), REQUEST)
    validate_contract(load(SKILL / "assets/contract.example.json"))
    validate(load(SKILL / "assets/control-config.example.json"), CONFIG)
    sys.path.insert(0, str(PLUGIN / "acceptance-control"))
    from gate import POLICY_V2
    validate(load(SKILL / "assets/formal-policy.example.json"), POLICY_V2)
    # fvkit is shipped twice so each plugin closes its own loop; the copies must not drift.
    twin = REPO / "plugins/ai-dlc/skills/formal-verify/scripts"
    if twin.is_dir():
        mine = sorted(p.name for p in (SKILL / "scripts/fvkit").glob("*.py"))
        theirs = sorted(p.name for p in (twin / "fvkit").glob("*.py"))
        assert mine == theirs, "fvkit module sets differ between trusted-acceptance and ai-dlc"
        for name in mine:
            assert (SKILL / "scripts/fvkit" / name).read_bytes() == (twin / "fvkit" / name).read_bytes(), "fvkit copy drifted: " + name
        assert (SKILL / "scripts/fv.py").read_bytes() == (twin / "fv.py").read_bytes(), "fv.py copy drifted"
    print("Plugin registration, version sync, local links, protocol/policy examples and fvkit copy: OK")


if __name__ == "__main__":
    main()
