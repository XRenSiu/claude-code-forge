"""
Cross-plugin integration checks for done-when-pipeline.

Verifies the existence of the OTHER skills our INTEGRATION.md mentions,
and that our doc claims about them match reality.

Run: python3 tests/done-when-skills/integration/test_cross_plugin.py
"""

from __future__ import annotations
import json, re, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DWP = REPO_ROOT / "plugins" / "done-when-pipeline"


# ---------- REQ-012 ----------
def test_ratchet_skill_exists_in_marketplace_at_referenced_path():
    """Confirm the ratchet plugin we hand off to is actually present."""
    mp = json.loads((REPO_ROOT / ".claude-plugin/marketplace.json").read_text())
    entry = [p for p in mp["plugins"] if p["name"] == "ratchet"]
    assert entry, "ratchet not in marketplace"
    skillmd = REPO_ROOT / "plugins/ratchet/skills/ratchet/SKILL.md"
    assert skillmd.exists(), f"ratchet SKILL.md missing at {skillmd}"


def test_ratchet_skillmd_does_not_mention_done_when_yaml_consumption():
    """
    Our INTEGRATION.md now claims ratchet does NOT auto-consume our done_when.yaml.
    Confirm that claim: ratchet's own SKILL.md should not advertise such consumption.
    (If a future ratchet update adds this, this test fails — then we re-examine.)
    """
    text = (REPO_ROOT / "plugins/ratchet/skills/ratchet/SKILL.md").read_text(encoding="utf-8")
    # ratchet should NOT advertise parsing of done_when.yaml or done-when-pipeline output
    forbidden_patterns = [
        r"done_when\.yaml",
        r"done-when-pipeline",
        r"acceptance-spec",
        r"test-suite-generator",
    ]
    found = [p for p in forbidden_patterns if re.search(p, text)]
    assert not found, (
        f"ratchet SKILL.md mentions {found} — if ratchet actually integrates with done-when-pipeline,"
        f" our INTEGRATION.md needs to be updated to describe automated consumption instead of manual hand-off."
    )


# ---------- REQ-013 ----------
def test_persona_distill_plugin_exists_in_marketplace():
    mp = json.loads((REPO_ROOT / ".claude-plugin/marketplace.json").read_text())
    entry = [p for p in mp["plugins"] if p["name"] == "persona-distill"]
    assert entry, "persona-distill not in marketplace"


def test_persona_judge_skill_exists_inside_persona_distill():
    skillmd = REPO_ROOT / "plugins/persona-distill/skills/persona-judge/SKILL.md"
    assert skillmd.exists(), f"persona-judge skill missing at {skillmd}"
    text = skillmd.read_text(encoding="utf-8")
    # confirm its scope is what we documented: persona-skill quality, not arbitrary artifacts
    assert re.search(r"persona\s*skill", text, re.I), \
        "persona-judge SKILL.md does not mention 'persona skill' — our category-error claim may be wrong"


# ---------- runner ----------
def _run():
    failed = []
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"✓ {name}")
                passed += 1
            except AssertionError as e:
                print(f"✗ {name}: {e}", file=sys.stderr)
                failed.append(name)
            except Exception as e:
                print(f"✗ {name}: ERROR {type(e).__name__}: {e}", file=sys.stderr)
                failed.append(name)
    print("─────────────────────────────────")
    print(f"Integration checks: {passed} passed · {len(failed)} failed")
    if failed:
        print("Failed:")
        for n in failed:
            print(f"  - {n}")
        sys.exit(1)


if __name__ == "__main__":
    _run()
