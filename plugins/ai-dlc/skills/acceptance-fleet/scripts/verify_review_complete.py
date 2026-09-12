#!/usr/bin/env python3
"""verify_review_complete.py — 派发出去的审查「到底跑完了没有」的机械闸。

缺口：不变量 14（声明了但没求值 ≠ 通过）到今天只覆盖**脚本**。`verify_structure.py` 的退出码 3
说的是"分析器缺席不许报绿"；可这条流水线上真正会半路断掉的，是六个 LLM 审查 skill 和五个隔离
子 agent。一次被截断的审查留下的是一份**短而干净**的报告——它和"走完全程、什么也没发现"在字节
层面长得一模一样。`/meta-judge` 读到它，`reviews_loaded[].finding_count: 0`，`state_decision: PASS`。
一次根本没跑完的审查，就这样合成出了一个通过。

**没有一个状态表示"这次审查没跑完"**——本脚本就是那个状态。

契约：每份 fleet 输出必须自带一个显式的完成标记。它可以在文档顶层，也可以在角色块里：

    review_complete:
      status: complete | incomplete      # incomplete = 没跑完，这是一个真实的否定裁决
      findings_count: 3                  # 必须与文件里真实的发现条数一致
      findings_key: qa_report.findings   # 可选；这份报告的发现列表在哪（默认按角色表推）
      reason: <text>                     # status: incomplete 时必填——为什么没跑完
      attempt: 1                         # 可选；第几次派发

`findings_count` 与实到条数对不上，本身就是截断的证据：模型写标记时手里有 N 条，落盘只落了 M 条。
两个数字由**不同时刻**产生，所以它们能互相指证——这就是要求这个字段的全部理由。

用法：
  verify_review_complete.py <fleet-outputs 目录> [--expect a,b,…| --size M|L]
                            [--out review-completeness.yaml] [--require-complete] [--json]
  verify_review_complete.py <file.yaml> [<file.yaml> …] [同上选项]
  verify_review_complete.py <fleet-outputs 目录> --clear <path>   # 重派前清掉陈旧输出

退出码（与 verify_structure.py 同构）：
  0 = 期望集里每一份都在，且都显式声明跑完了
  1 = 有审查**显式声明**没跑完（status: incomplete）——这是真实的否定裁决，不是缺证据
  2 = 用法 / IO 错误
  3 = **unevaluated**：有审查缺席 / 解析不了 / 没有完成标记 / 声明数与实到数不符。
      这不是 pass。契约承诺派发 N 个审查，其中一个没有可用裁决；调用方必须按"未检"记录。
      `--require-complete` 把 3 变成 1（闸 / CI 里该这么用）。
  1 与 3 同时成立时返回 1：显式的否定裁决比"证据缺失"更确定，两者都非零，不影响拦截。

设计要点（为什么这样而不是那样）：
  - **缺标记走严路，不走宽路。** 这是整个脚本唯一不能妥协的地方，也是本插件的极性铁律：
    一个靠遗漏就能打开的门不是门。所以"没写标记"与"写了 incomplete"都非零，只是分成两种退出码——
    前者是"不知道"，后者是"知道它没跑完"。
  - **目录里多出来的文件也要检。** `/meta-judge` M0 对 `<reviews_source>` 做 `*.yaml` glob——
    凡是躺在这个目录里的，它都会读。所以凡是躺在这个目录里的，本闸都要检。只检期望集，等于
    给一份期望之外的截断报告开一条直达 meta-judge 的路。
  - **目录形态必须显式声明期望集。** 没有期望集，"没有缺文件"是一句没人能核对的话——
    这本身就是 unevaluated。位置参数直接给文件时不需要：被点名的那些就是期望集。
  - **`--clear` 移走，不删除。** `references/ratchet-log-format.md` 写着"skill 自己不得删除
    iteration 目录里的任何文件"，不变量 5 写着"账本只增不删；失败记录不回滚"。一份没跑完的
    审查是**失败记录**。所以清的是**槽位**不是字节：文件移到 `stale/<name>.attempt-N.yaml`，
    陈旧裁决再也不会被当成覆盖了新代码的裁决，而"第一次派发没跑完"这件事留在日志里。
    附带好处是 `prior_attempts` 可数——"每份审查最多重派一次"因此是可检查的，不是散文。
  - **skipped 不是 incomplete。** `{skipped: <reason>}` 是显式声明的省略，落在 meta-judge 的
    `caveats.suppressed_skills` 里降权；截断是沉默的。本闸只管沉默的那种。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None

# 角色块 → (角色名, 该角色的发现列表键)。顶层键是这五个 skill 输出里最稳的东西：
# code-reviewer 的 agent_role 写的是 --focus（security / logic / perf），认它会认错人。
ROLE_BLOCKS = {
    "code_review": ("code-reviewer", "findings"),
    "qa_report": ("qa-reviewer", "findings"),
    "pm_review": ("pm-reviewer", "per_req_compliance"),
    "gaming_assessment": ("spec-gaming-detector", "detected_patterns"),
    "drift_signals": ("spec-drift-detector", "signals"),
    "drift_report": ("spec-drift-detector", "signals"),
}
# 角色表认不出来时的兜底：块里第一个叫得出名字的列表。认不出就报 unevaluated，不猜。
LIST_FALLBACK = ("findings", "detected_patterns", "signals", "drift_signals", "per_req_compliance")

SIZE_PRESETS = {
    # 体量分档见 SKILL.md「体量分档与结构闸」。S 档不派发本 fleet，故没有期望集。
    "M": ["qa-reviewer.yaml", "spec-gaming-detector.yaml"],
    "L": ["code-reviewer-security.yaml", "code-reviewer-logic.yaml", "code-reviewer-perf.yaml",
          "qa-reviewer.yaml", "pm-reviewer.yaml", "spec-drift-detector.yaml",
          "spec-gaming-detector.yaml"],
}
# qa-measurements.yaml 是 qa_facts.py 的投影，不是审查报告；它没有裁决，也就没有"跑完了没有"。
NON_REVIEW = {"qa-measurements.yaml", "qa-measurements.yml"}
STALE_DIR = "stale"


def die(msg, code):
    sys.stderr.write("verify_review_complete: %s\n" % msg)
    return code


def norm_name(n):
    """--expect 里既收 `qa-reviewer` 也收 `qa-reviewer.yaml`。"""
    n = n.strip()
    return n if n.endswith((".yaml", ".yml")) else n + ".yaml"


def dig(doc, dotted):
    cur = doc
    for seg in dotted.split("."):
        if not isinstance(cur, dict) or seg not in cur:
            return None
        cur = cur[seg]
    return cur


def find_marker(doc):
    """标记允许在顶层，也允许在角色块里 —— 位置宽松，存在与否严格。"""
    if isinstance(doc.get("review_complete"), dict):
        return doc["review_complete"], "review_complete"
    for key in ROLE_BLOCKS:
        blk = doc.get(key)
        if isinstance(blk, dict) and isinstance(blk.get("review_complete"), dict):
            return blk["review_complete"], "%s.review_complete" % key
    return None, None


def find_skip(doc):
    for holder, prefix in [(doc, "")] + [(doc.get(k), k + ".") for k in ROLE_BLOCKS]:
        if isinstance(holder, dict) and holder.get("skipped"):
            return str(holder["skipped"]), prefix + "skipped"
    return None, None


def resolve_findings(doc, marker):
    """→ (条数, 列表位置, 说不出来的原因)。数不出来就说数不出来，不拿 0 顶。"""
    key = (marker or {}).get("findings_key")
    if isinstance(key, str) and key:
        val = dig(doc, key)
        if isinstance(val, list):
            return len(val), key, None
        return None, key, "findings_key: %s 指向的不是一个列表" % key
    for blk_key, (_role, list_key) in ROLE_BLOCKS.items():
        blk = doc.get(blk_key)
        if isinstance(blk, dict):
            val = blk.get(list_key)
            if isinstance(val, list):
                return len(val), "%s.%s" % (blk_key, list_key), None
            for alt in LIST_FALLBACK:
                if isinstance(blk.get(alt), list):
                    return len(blk[alt]), "%s.%s" % (blk_key, alt), None
            return None, None, "%s 里没有 %s 列表" % (blk_key, list_key)
    for alt in LIST_FALLBACK:
        if isinstance(doc.get(alt), list):
            return len(doc[alt]), alt, None
    return None, None, "认不出这份报告的发现列表（角色块与兜底键都没命中）"


def role_of(doc):
    for key, (role, _) in ROLE_BLOCKS.items():
        if isinstance(doc.get(key), dict):
            return role
    return None


def prior_attempts(directory, name):
    """stale/ 里躺着几次同名的旧尝试 —— 「最多重派一次」因此可数。"""
    stale = os.path.join(directory, STALE_DIR) if directory else None
    if not stale or not os.path.isdir(stale):
        return 0
    stem = os.path.splitext(name)[0]
    return sum(1 for f in os.listdir(stale) if f.startswith(stem + ".attempt-"))


# ---------------------------------------------------------------- 单份检查
def check_one(path, name, directory):
    row = {"file": name, "path": path, "role": None, "status": None,
           "declared_findings": None, "actual_findings": None, "findings_key": None,
           "prior_attempts": prior_attempts(directory, name)}
    if not os.path.isfile(path):
        row["status"] = "missing"
        row["why"] = "期望的审查输出不在——一份什么都没写的审查是最常见的截断形态"
        return row
    try:
        with open(path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except Exception as e:
        row["status"] = "unparseable"
        row["why"] = "YAML 解析失败：%s（半截 YAML 正是被截断的签名）" % e
        return row
    if not isinstance(doc, dict):
        row["status"] = "unparseable"
        row["why"] = "顶层不是映射，读不出角色块"
        return row

    row["role"] = role_of(doc)
    skip_reason, skip_at = find_skip(doc)
    if skip_reason:
        row["status"] = "skipped"
        row["why"] = "%s: %s" % (skip_at, skip_reason)
        return row

    marker, at = find_marker(doc)
    if marker is None:
        row["status"] = "unmarked"
        row["why"] = ("没有 review_complete 标记——一份短报告与「走完全程、什么也没发现」在字节"
                      "层面无法区分，所以缺标记按未检算，不按通过算")
        return row
    row["marker_at"] = at
    status = marker.get("status")
    declared = marker.get("findings_count")
    row["declared_findings"] = declared
    actual, where, why = resolve_findings(doc, marker)
    row["actual_findings"] = actual
    row["findings_key"] = where

    if status not in ("complete", "incomplete"):
        row["status"] = "unmarked"
        row["why"] = "review_complete.status = %r，不是 complete / incomplete" % (status,)
        return row
    if status == "incomplete":
        row["status"] = "incomplete"
        row["why"] = str(marker.get("reason") or "review did not complete within turn budget")
        return row

    # status: complete —— 还要过两道自证：数得出来，且两个数字对得上。
    if not isinstance(declared, int) or isinstance(declared, bool):
        row["status"] = "unmarked"
        row["why"] = "标记声明 complete 但 findings_count 不是整数（%r）——数不出来就核对不了" % (declared,)
        return row
    if actual is None:
        row["status"] = "uncountable"
        row["why"] = why or "数不出实到发现条数"
        return row
    if actual != declared:
        row["status"] = "count_mismatch"
        row["why"] = ("标记声明 %d 条，文件里实到 %d 条（%s）——两个数字产生于不同时刻，"
                      "对不上就是落盘被截断的直接证据" % (declared, actual, where))
        return row
    row["status"] = "complete"
    return row


# ---------------------------------------------------------------- --clear
def do_clear(directory, target, as_json):
    """清槽位，不清字节：移到 stale/ 而不是 unlink（见文件头设计要点）。"""
    if not os.path.isdir(directory):
        return die("%s 不是目录；--clear 的围栏就是这个目录，没有围栏不动手" % directory, 2)
    root = os.path.realpath(directory)
    real = os.path.realpath(target)
    if os.path.dirname(real) != root:
        return die("拒绝：%s 不是 %s 的直接子文件（realpath = %s）。--clear 只在这一个目录里动手。"
                   % (target, directory, real), 2)
    if os.path.basename(real) == STALE_DIR or os.path.isdir(real):
        return die("拒绝：%s 是目录（或就是 stale/ 本身）" % target, 2)
    name = os.path.basename(real)
    if not os.path.isfile(real):
        res = {"mode": "clear", "moved": None, "note": "%s 不在，无需清理" % name}
        print(json.dumps(res, ensure_ascii=False, indent=2) if as_json
              else "verify_review_complete --clear · %s 不在，无需清理" % name)
        return 0
    stale = os.path.join(root, STALE_DIR)
    os.makedirs(stale, exist_ok=True)
    stem, ext = os.path.splitext(name)
    n = prior_attempts(root, name) + 1
    dest = os.path.join(stale, "%s.attempt-%d%s" % (stem, n, ext))
    os.replace(real, dest)
    res = {"mode": "clear", "moved": name, "to": os.path.relpath(dest, root), "attempt": n,
           "note": "陈旧裁决已让出槽位；字节留在 stale/ —— 失败记录不回滚（不变量 5）"}
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("verify_review_complete --clear · 移走 %s → %s/%s（第 %d 次尝试的输出）"
              % (name, STALE_DIR, os.path.basename(dest), n))
        print("  字节没有删除：一份没跑完的审查是失败记录，失败记录不回滚。")
    return 0


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+", help="fleet-outputs 目录，或一到多个审查输出文件")
    ap.add_argument("--expect", help="期望到齐的输出，逗号分隔（qa-reviewer 或 qa-reviewer.yaml 都收）")
    ap.add_argument("--size", choices=["S", "M", "L"], help="按体量分档取期望集（S 不派发本 fleet）")
    ap.add_argument("--size-source", dest="size_source", choices=["default", "manual", "derived", "derived_early"],
                    help="state.intake.size_source。M 档的两人子集是一次豁免，豁免只认推导来的档位："
                         "default / manual 一律按 L 档的全集取期望——一个靠不跑 `size` 就少四个审查者的门不是门")
    ap.add_argument("--out", default="review-completeness.yaml")
    ap.add_argument("--require-complete", action="store_true",
                    help="未检按否定处理（exit 1 而不是 3）——闸 / CI 里该这么用")
    ap.add_argument("--clear", metavar="PATH", help="重派前把陈旧输出移进 stale/；只在给定目录内动手")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.clear:
        if len(a.targets) != 1:
            return die("--clear 要恰好一个目录做围栏", 2)
        return do_clear(a.targets[0], a.clear, a.json)
    if yaml is None:
        return die("needs PyYAML", 2)
    if a.size == "S":
        return die("S 档不派发本 fleet（SKILL.md 体量分档表），没有 fleet 输出可检；"
                   "豁免由 aidlc_state.py size 按 size_source=derived 记录，不由本脚本给", 2)

    facts = {"mode": "verify", "expected": [], "expected_source": None, "reviews": [],
             "incomplete": [], "unevaluated": [], "redispatch_exhausted": []}

    directory, files = None, {}
    if len(a.targets) == 1 and os.path.isdir(a.targets[0]):
        directory = a.targets[0]
        facts["fleet_outputs"] = directory
        if a.expect:
            expected = [norm_name(x) for x in a.expect.split(",") if x.strip()]
            facts["expected_source"] = "--expect"
        elif a.size:
            if a.size == "M" and a.size_source not in ("derived", "derived_early"):
                # 与 aidlc_state.py effective_fleet 同一条极性：子集是豁免，豁免要用推导来的档位换
                expected = list(SIZE_PRESETS["L"])
                facts["expected_source"] = "--size M with size_source=%s → full L set (an undeserved subset is a door opened by omission)" % (a.size_source or "unset")
            else:
                expected = list(SIZE_PRESETS[a.size])
                facts["expected_source"] = "--size %s" % a.size + (" (%s)" % a.size_source if a.size_source else "")
        else:
            expected = []
            facts["expected_source"] = "未声明"
            # 没有期望集，"没有缺文件"是一句没人能核对的话 —— 与退出码 3 同一条道理。
            facts["unevaluated"].append({
                "what": "expected set", "why": "目录形态下没有 --expect / --size，缺文件是看不见的",
                "fix": "传 --expect <逗号分隔> 或 --size M|L（见 skill-dispatch-matrix.md 的派发表）"})
        for f in sorted(os.listdir(directory)):
            if f in NON_REVIEW or f == STALE_DIR or not f.endswith((".yaml", ".yml")):
                continue
            if os.path.isfile(os.path.join(directory, f)):
                files[f] = os.path.join(directory, f)
    else:
        expected = []
        facts["expected_source"] = "位置参数（被点名的就是期望集）"
        for t in a.targets:
            if os.path.isdir(t):
                return die("给了多个目标时不能混目录：%s" % t, 2)
            name = os.path.basename(t)
            expected.append(name)
            files[name] = t
            directory = directory or os.path.dirname(os.path.abspath(t))

    facts["expected"] = expected
    # 期望集 ∪ 目录里实到的：meta-judge 对这个目录做 glob，凡在此处的它都会读，所以都得检。
    for name in sorted(set(expected) | set(files)):
        path = files.get(name) or os.path.join(directory or ".", name)
        row = check_one(path, name, directory)
        row["expected"] = name in expected
        facts["reviews"].append(row)
        st = row["status"]
        if st == "incomplete":
            facts["incomplete"].append({"file": name, "reason": row["why"]})
        elif st in ("missing", "unparseable", "unmarked", "uncountable", "count_mismatch"):
            facts["unevaluated"].append({"what": name, "why": row["why"],
                                         "fix": "重派这一个审查（先 --clear 掉陈旧输出），"
                                                "第二次仍不完整就按 A 档 unevaluated 记录，DONE 不成立"})
        if st != "complete" and st != "skipped" and row["prior_attempts"] >= 1:
            facts["redispatch_exhausted"].append(name)

    facts["counts"] = {
        "expected": len(expected),
        "present": sum(1 for r in facts["reviews"] if r["status"] != "missing"),
        "complete": sum(1 for r in facts["reviews"] if r["status"] == "complete"),
        "skipped": sum(1 for r in facts["reviews"] if r["status"] == "skipped"),
    }
    facts["verdict"] = ("incomplete" if facts["incomplete"]
                        else ("unevaluated" if facts["unevaluated"] else "pass"))
    facts["tier"] = "A"
    out_text = yaml.safe_dump(facts, allow_unicode=True, sort_keys=False, width=120)
    try:
        open(a.out, "w", encoding="utf-8").write(out_text)
    except OSError as e:
        return die("写不了 %s: %s" % (a.out, e), 2)
    if a.json:
        print(json.dumps(facts, ensure_ascii=False, indent=2))
    else:
        c = facts["counts"]
        print("verify_review_complete · verdict = %s · 期望 %d · 到齐 %d · 完成 %d · 跳过 %d"
              % (facts["verdict"].upper(), c["expected"], c["present"], c["complete"], c["skipped"]))
        for i in facts["incomplete"]:
            print("  INCOMPLETE  %s — %s" % (i["file"], i["reason"]))
        for u in facts["unevaluated"]:
            print("  UNEVAL      %s: %s" % (u["what"], u["why"]))
        for n in facts["redispatch_exhausted"]:
            print("  EXHAUSTED   %s 已经重派过一次，这次仍不完整 —— 记 A 档 unevaluated，DONE 不成立" % n)
        print("  facts → %s" % a.out)
    if facts["incomplete"]:
        return 1
    if facts["unevaluated"]:
        return 1 if a.require_complete else 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
