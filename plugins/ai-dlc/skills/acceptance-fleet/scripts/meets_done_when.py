#!/usr/bin/env python3
"""meets_done_when.py — 「达标了没有」由脚本比对阈值得出，不由评估 agent 宣布（ARCHITECTURE 不变量 7 / DOS R010）。

缺口：契约 `behavior.thresholds` 里的每一条（`unit_coverage: ">= 0.80"`、`p95_latency_ms: "<= 300"` …）
都是 G2 签过的判据，而到验收这一步，没有任何脚本把它们和 qa-reviewer 量出来的数摆在一起比一遍。
`/meta-judge` 按 rules 合成四态，`acceptance.meets_done_when` 曾是一个谁都能 set 的布尔——
一把没人量过的尺子，报的绿以证据的形状到达。这个脚本就是那把尺子。

它做什么（只做这一件）：
  1. 读契约的 `behavior.thresholds`：每条形如 `<op> <number>`，op ∈ {>=, <=, >, <, ==}
  2. 读测量值：`qa_facts.py` 投影出来的 `qa-measurements.yaml`（只有事实，没有裁决——所以它能进这里）
     每个阈值按名字在测量文档里找**同名键**（`--map name=dotted.path` 可显式指路）
     找到一处 → 比；找不到 → unevaluated；找到多处且值不同 → unevaluated（机器不该替人挑）
  3. 可选读 `final-state.json`：state_decision 必须是 DONE，unevaluated_reviews 必须为空（不变量 14）
  4. 写报告（默认 meets_done_when.yaml），带契约的 sha256——`aidlc_state.py acceptance --meets` 核它，
     一份量的是**另一份契约**的报告不算数

它不做什么：`rules:` 归 /meta-judge；human AC 归 G3；它不读任何评审者的 findings（那是墙那边的东西）。

用法：
  meets_done_when.py <done_when.yaml> --measurements <qa-measurements.yaml> [--final-state final-state.json]
                     [--map name=dotted.path ...] [--out meets_done_when.yaml] [--json]

退出码（与 verify_structure.py / verify_review_complete.py 同构）：
  0 = met：每条阈值都量到了且都满足（给了 final-state 时它也是 DONE 且无 unevaluated review）
  1 = not_met：至少一条阈值被违反，或 final-state 不是 DONE
  2 = 用法 / IO 错误
  3 = unevaluated：有阈值没量到（没有同名测量、或多处不一致）——**不是通过**。
      契约声明了一条判据而求值者没跑完，结果是「未评估」，一把没跑的尺子不许报绿。
  1 与 3 同时成立时返回 1：显式的违反比证据缺失更确定，两者都非零，不影响拦截。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    yaml = None

OPS = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    "==": lambda a, b: a == b,
}
THRESHOLD_RE = re.compile(r"^\s*(>=|<=|==|>|<)\s*([-+]?\d+(?:\.\d+)?)\s*(%?)\s*$")


def die(msg, code=2):
    sys.stderr.write(f"meets_done_when: {msg}\n")
    return code


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_doc(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if path.endswith(".json"):
        return json.loads(text)
    if yaml is None:
        raise RuntimeError("needs PyYAML")
    return yaml.safe_load(text) or {}


def parse_threshold(spec):
    """'>= 0.80' → ('>=', 0.80). 纯数字视为 '=='（一个没有算子的阈值没有方向，说清楚而不是猜）。"""
    if isinstance(spec, (int, float)) and not isinstance(spec, bool):
        return "==", float(spec)
    m = THRESHOLD_RE.match(str(spec))
    if not m:
        return None, None
    return m.group(1), float(m.group(2))


def walk(node, path=""):
    """(dotted_path, key, value) for every scalar in a nested doc."""
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}" if path else str(k)
            if isinstance(v, (dict, list)):
                yield from walk(v, p)
            else:
                yield p, str(k), v
    elif isinstance(node, list):
        for i, v in enumerate(node):
            p = f"{path}[{i}]"
            if isinstance(v, (dict, list)):
                yield from walk(v, p)
            else:
                yield p, "", v


def get_dotted(doc, dotted):
    cur = doc
    for part in dotted.split("."):
        m = re.match(r"^(.*?)\[(\d+)\]$", part)
        key, idx = (m.group(1), int(m.group(2))) if m else (part, None)
        if key:
            if not isinstance(cur, dict) or key not in cur:
                return None, False
            cur = cur[key]
        if idx is not None:
            if not isinstance(cur, list) or idx >= len(cur):
                return None, False
            cur = cur[idx]
    return cur, True


def to_number(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        m = re.match(r"^\s*([-+]?\d+(?:\.\d+)?)\s*%?\s*$", v)
        if m:
            return float(m.group(1))
    return None


def locate(measurements, name, explicit):
    """→ (value, source_path, note). 显式映射优先；否则按同名键在测量文档里找。"""
    if name in explicit:
        v, ok = get_dotted(measurements, explicit[name])
        if not ok:
            return None, explicit[name], f"--map path {explicit[name]} not found in measurements"
        n = to_number(v)
        return (n, explicit[name], None) if n is not None else (None, explicit[name], f"value at {explicit[name]} is not numeric: {v!r}")
    hits = [(p, v) for p, k, v in walk(measurements) if k == name]
    if not hits:
        return None, None, f"no measurement named `{name}` (pass --map {name}=<dotted.path>)"
    nums = [(p, to_number(v)) for p, v in hits]
    if any(n is None for _, n in nums):
        bad = [p for p, n in nums if n is None]
        return None, ", ".join(bad), f"`{name}` found but not numeric at {bad}"
    if len({n for _, n in nums}) > 1:
        return None, ", ".join(p for p, _ in nums), f"`{name}` found at {len(nums)} places with different values — ambiguous, a machine must not pick"
    return nums[0][1], nums[0][0], None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("done_when")
    ap.add_argument("--measurements", required=True, help="qa_facts.py 的投影（qa-measurements.yaml）")
    ap.add_argument("--final-state", dest="final_state", help="acceptance-fleet 的 final-state.json（可选）")
    ap.add_argument("--map", action="append", default=[], metavar="NAME=DOTTED.PATH",
                    help="阈值名 → 测量文档里的路径；不给就按同名键找")
    ap.add_argument("--out", default="meets_done_when.yaml")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if yaml is None and not (a.done_when.endswith(".json") and a.measurements.endswith(".json")):
        return die("needs PyYAML")
    for p in (a.done_when, a.measurements) + ((a.final_state,) if a.final_state else ()):
        if not os.path.isfile(p):
            return die(f"not a file: {p}")
    try:
        dw = load_doc(a.done_when)
        ms = load_doc(a.measurements)
    except Exception as e:
        return die(f"cannot read inputs: {e}")
    explicit = {}
    for m in a.map:
        if "=" not in m:
            return die(f"--map expects NAME=DOTTED.PATH, got {m!r}")
        k, v = m.split("=", 1)
        explicit[k.strip()] = v.strip()

    thresholds = ((dw.get("behavior") or {}).get("thresholds") or {}) if isinstance(dw, dict) else {}
    rows, violated, unevaluated = [], [], []
    for name, spec in thresholds.items():
        op, want = parse_threshold(spec)
        row = {"name": name, "threshold": str(spec), "observed": None, "source": None, "result": None}
        if op is None:
            row.update(result="unevaluated", note=f"threshold {spec!r} is not `<op> <number>`")
            unevaluated.append(name); rows.append(row); continue
        got, src, note = locate(ms, name, explicit)
        row["source"] = src
        if got is None:
            row.update(result="unevaluated", note=note)
            unevaluated.append(name); rows.append(row); continue
        ok = OPS[op](got, want)
        row.update(observed=got, result="pass" if ok else "fail")
        if not ok:
            violated.append(name)
        rows.append(row)

    fs_block = None
    if a.final_state:
        try:
            fs = load_doc(a.final_state)
        except Exception as e:
            return die(f"cannot read --final-state: {e}")
        sd = fs.get("state_decision") or fs.get("state")
        ur = fs.get("unevaluated_reviews") or []
        fs_block = {"path": a.final_state, "state_decision": sd, "unevaluated_reviews": ur,
                    "result": "pass" if (sd == "DONE" and not ur) else "fail"}
        if sd != "DONE":
            violated.append(f"final-state.state_decision={sd}")
        if ur:
            unevaluated.append(f"final-state.unevaluated_reviews={ur}")

    verdict = "not_met" if violated else ("unevaluated" if unevaluated else "met")
    report = {
        "verdict": verdict,
        "done_when": a.done_when,
        "done_when_sha256": sha256(a.done_when),
        "measurements": a.measurements,
        "final_state": fs_block,
        "thresholds_declared": len(thresholds),
        "thresholds": rows,
        "violated": violated,
        "unevaluated": unevaluated,
        "computed_at": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
        "note": ("rules: are meta-judge's; human ACs are G3's; this report covers behavior.thresholds only. "
                 "unevaluated is not pass: a declared threshold nobody measured has not been met."),
    }
    if not thresholds:
        report["note"] = "the contract declares no behavior.thresholds — nothing to compare; " + report["note"]
    text = json.dumps(report, ensure_ascii=False, indent=2) if (a.out.endswith(".json") or yaml is None) \
        else yaml.safe_dump(report, allow_unicode=True, sort_keys=False)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(text if text.endswith("\n") else text + "\n")
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"meets_done_when: {verdict} · {len(thresholds)} threshold(s) · violated={violated} · unevaluated={unevaluated} → {a.out}")
    return {"met": 0, "not_met": 1, "unevaluated": 3}[verdict]


if __name__ == "__main__":
    sys.exit(main())
