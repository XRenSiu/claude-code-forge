#!/usr/bin/env python3
"""
derive_counts.py — the count primitive for test-suite-generator.

The skill's "Counts must be verbatim from done_when.yaml" rule exists because of a
real, recorded bug (iter-2 step2 P2-4: README said 16 unit tests, the YAML listed
14). That divergence is exactly the skillwise THEORY.md §3 failure: a count
re-derived by hand in prose has no named slot to land in, so a wrong number slips
through. This script makes the counts a primitive — the relationship M = E + P is
arithmetic done once, not narrated.

Emit the headline-line counts and the per-group breakdown straight from the
contract. The SKILL body and the generated README must paste these numbers
verbatim; never hand-count test files.

Where the names live
--------------------
v1 contracts carry the test list in `behavior:`. v2 contracts (schema: 2) do NOT:
`behavior:` is an empty seed and the real list is `tests/<feature>/tests-manifest.yaml`.
Pass `--manifest` for those — behaviour counts then come from the manifest and the
`existence:` count from whichever document declares one. A behaviour block that is
empty with no `--manifest` is a config error (exit 2), not "0 tests": a zero count
pasted into a README is the same silent-empty report I-59 killed next door.

Usage:
    python derive_counts.py <path-to-done_when.yaml>            # human line + table
    python derive_counts.py <path-to-done_when.yaml> --json     # machine JSON
    python derive_counts.py <done_when.yaml> --manifest tests/<feature>/tests-manifest.yaml
    python derive_counts.py <tests-manifest.yaml>               # manifest as the only source
    python derive_counts.py <done_when.yaml> --manifest <m.yaml> --strategy minimal|standard|comprehensive

Exit codes: 0 ok · 2 empty behaviour block with no --manifest / bad input
            4 below the test_strategy floor (量不够，不是配置错——两者要分得开)
"""

import sys
import json
import argparse

try:
    import yaml
except ImportError:
    sys.stderr.write("derive_counts.py needs PyYAML: pip install pyyaml\n")
    sys.exit(2)

EMPTY_EXIT = 2   # an empty behaviour block is a failure, never "0 tests" (I-54 / I-59)

EMPTY_HINT = (
    "behavior: is empty in {path} — a v2 contract (schema: 2) keeps it as a seed and the real\n"
    "test list lives in the L5 manifest. Re-run with:\n"
    "    python derive_counts.py {path} --manifest tests/<feature>/tests-manifest.yaml\n"
    "Reporting 0 unit / 0 integration / 0 e2e here would put a fabricated count in the README.\n"
)


def _len(x):
    return len(x) if isinstance(x, list) else 0


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except OSError as e:
        sys.stderr.write(f"derive_counts.py: {e}\n")
        sys.exit(2)


def counts(doc, behavior_doc=None):
    existence = doc.get("existence") or []
    src = behavior_doc if behavior_doc is not None else doc
    if not existence:
        existence = src.get("existence") or []
    b = src.get("behavior") or {}
    unit = b.get("unit_tests") or {}
    integ = b.get("integration_tests") or {}
    e = _len(unit.get("example_based"))
    p = _len(unit.get("property_based"))
    ie = _len(integ.get("example_based"))
    ip = _len(integ.get("property_based"))
    k = _len(b.get("e2e_tests"))
    return {
        "existence": _len(existence),
        "unit_total": e + p,          # M = E + P (arithmetic, not narrative)
        "unit_example": e,            # E
        "unit_property": p,           # P
        "integration_total": ie + ip,
        "integration_example": ie,
        "integration_property": ip,
        "e2e": k,                     # K
    }


# 测试量是**第三个旋钮**，与广度（跑哪些阶段）和深度（每个阶段产出多细）正交（sizing.yaml）。
# 借鉴 AI-DLC 2.0 把这三个拧开的理由：「完整文档 + 最少测试」是合法组合，测试量不该被文档
# 详细度绑架。它的 minimal 档用了个好类比——奈奎斯特：每条已识别需求 1 个测试，是「能重建
# 信号的最低采样率」，外加每个观察边界至少 1 个 happy path。
#
# 这里只把它实现成**下界**，不实现成上界：
#   - 策略是地板，不是天花板。写多了不报错，写少了要说话。
#   - 地板从契约里的 AC 数算出来，不是拍的：minimal = AC 数（每条需求一个采样点）+ 观察边界数
#     （每个边界一条 happy path），standard = minimal × 2（happy 之外要有 unhappy），
#     comprehensive 不设算术地板——它的下界是「五层金字塔每层都非空」，那是 SKILL.md 的判据，
#     不是一个数。
#   - 违反地板 exit 4，与「空 behavior」的 exit 2 分开：一个是配置错误，一个是量不够。
TEST_FLOOR_EXIT = 4


def strategy_floor(doc, strategy):
    """→ (floor, why) 或 (None, why)。地板从契约算，不是从策略名猜。"""
    acs = [x for x in (doc.get("acceptance") or []) if isinstance(x, dict)]
    mech = [x for x in acs if x.get("kind") == "mechanical"]
    boundaries = {str(x.get("observe")) for x in mech if x.get("observe")}
    if strategy == "minimal":
        n = len(mech) + len(boundaries)
        return n, (f"minimal = {len(mech)} mechanical AC（每条需求一个采样点，奈奎斯特）"
                   f" + {len(boundaries)} 个观察边界（每个边界至少一条 happy path）")
    if strategy == "standard":
        n = 2 * len(mech) + len(boundaries)
        return n, (f"standard = 2 × {len(mech)} mechanical AC（happy 之外要有 unhappy）"
                   f" + {len(boundaries)} 个观察边界")
    return None, ("comprehensive 不设算术地板：它的下界是「五层金字塔每层都非空」，"
                  "那是 SKILL.md 的判据，不是一个数")


def main():
    ap = argparse.ArgumentParser(description="Derive canonical test counts from done_when.yaml.")
    ap.add_argument("path")
    ap.add_argument("--manifest", help="tests-manifest.yaml holding the v2 test list "
                                       "(v2 `behavior:` is an empty seed)")
    ap.add_argument("--strategy", choices=["minimal", "standard", "comprehensive"],
                    help="测试量旋钮（sizing.yaml 的 tiers.<档>.test_strategy）。策略是**下界**："
                         "写多了不报错，写少了 exit 4。与深度正交——完整文档 + 最少测试是合法组合")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    doc = load(args.path)
    behavior_doc = load(args.manifest) if args.manifest else None
    c = counts(doc, behavior_doc)

    if not args.manifest and c["unit_total"] + c["integration_total"] + c["e2e"] == 0:
        sys.stderr.write("derive_counts.py: " + EMPTY_HINT.format(path=args.path))
        sys.exit(EMPTY_EXIT)

    written = c["unit_total"] + c["integration_total"] + c["e2e"]
    short = None
    if args.strategy:
        floor, why = strategy_floor(doc, args.strategy)
        c["strategy"] = args.strategy
        c["floor"] = floor
        c["floor_why"] = why
        c["behaviour_written"] = written
        if floor is not None and written < floor:
            short = (f"test_strategy={args.strategy} 的地板是 {floor} 个行为测试，manifest 里只有 {written}。\n"
                     f"  {why}\n"
                     "  策略是地板不是天花板：写多了不报错，写少了说明有需求没有采样点。\n"
                     "  要么补测试，要么把 test_strategy 调低并在契约里说明为什么这次的采样率够。")

    if args.json:
        print(json.dumps(c, indent=2, ensure_ascii=False))
        if short:
            sys.stderr.write("derive_counts.py: " + short + "\n")
            sys.exit(TEST_FLOOR_EXIT)
        return

    source = args.path if not args.manifest else f"{args.path} + {args.manifest}"
    print(f"\n  Canonical counts from {source}\n")
    print(f"  {c['existence']} existence checks · "
          f"{c['unit_total']} unit tests ({c['unit_example']} example / {c['unit_property']} PBT) · "
          f"{c['integration_total']} integration tests · {c['e2e']} e2e tests")
    if args.strategy:
        print(f"\n  test_strategy={args.strategy} · floor={c['floor']} · written={written}")
        print(f"  {c['floor_why']}")
    print("\n  Paste this line verbatim into the user summary AND tests/<feature>/README.md.")
    print("  Never hand-count generated files — M = E + P is arithmetic, not narrative.\n")
    if short:
        sys.stderr.write("derive_counts.py: " + short + "\n")
        sys.exit(TEST_FLOOR_EXIT)


if __name__ == "__main__":
    main()
