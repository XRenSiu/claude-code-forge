#!/usr/bin/env python3
"""repo_assets.py — X1 的仓库级制品：在项目目录里找它们，并核对它们进没进 git。

缺口（2026-09-09）：`dos.yaml` / `agent-map.md` / `invariants/` 被文档写成「横切 X1」，
但代码里没有任何东西查它们在不在——`ORDER` 里没有它们，`prereqs()` 一个分支也不提它们，
`doctor` 查的全是工具链（pyyaml / 兄弟脚本 / git / gh）。后果是三处**静默降级**：

  - `/issue --dos` 的词表闭包：有本体时闭包失败 = **客观触发 PSL 轨**；没有本体时只出一条
    `closure unchecked` 的 flag 然后放行——SKILL.md 宣称的「不靠自评」当场退回自评；
  - `lint_cards.py --dos` 的 `dos_slice` 闭包：没有本体时降级成一条 info，而卡里出现一个
    本体解析不了的名词是整条流水线上代价最高的一次漂移（实现者自己挑个意思，验收才对上）；
  - `verify_vocabulary.py`：exit 3 = **未检**，不是通过。

第二个缺口是**位置**。这三样是仓库级、一次性、全组共享的制品，而 `.aidlc/<slug>/state.json`
是 per-feature 的运行时状态。把它们放进 `.aidlc/` 会同时错两次——换个 feature 找不到，
换个人更找不到。它们该在**项目目录里、进 git**：本体是团队的共同词表，
一份没进版本库的词表不是「有本体」，是「你有本体」。

这个模块只回答两个可核对的问题，不判断内容对不对（内容是 `verify_dos.py` /
`verify_agent_map.py` / `verify_card.py` 的活）：

  1. **在不在** —— 按候选路径序找，第一个命中即用。canonical 在最前，`.aidlc/` 在最后
     且命中即告警（它是运行时目录，不是共享位置）。
     **monorepo 走 `--scope`**：一个仓库多个 package 时，本体是**每个 package 一份**
     （dos-extract 的 edge case：一个 package 一个 bounded context）。把只覆盖某一个
     package 的本体放在仓库根，是拿 scope 撒谎。`--scope plugins/ai-dlc` 先在那个目录里找，
     找不到再回落到仓库根——所以「一份仓库级 agent-map + 每个 package 一份 dos」是可表达的。
  2. **进没进 git** —— `git ls-files`。找到了但没 tracked（或被 .gitignore 吃掉），
     队友 clone 下来是空的。这是「团队共享」这件事唯一可机械核对的形式。

用法：
  repo_assets.py [--repo-root .] [--scope plugins/ai-dlc] [--json]

退出码：0 = 三样齐全且都进了 git · 1 = 有缺失 / 未 tracked / 位置不共享 · 2 = 用法 / IO
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

# 运行时目录：命中这里的制品能用，但共享不到——单独标注，不是静默接受。
RUNTIME_DIRS = (".aidlc/", ".sdlc/")

# 候选路径按序求值，第一个命中即用。canonical = 列表第一项，也是缺失时建议写入的位置。
SPEC = {
    "dos": {
        "label": "DOS 本体",
        "filename": "dos.yaml",
        "kind": "file",
        "candidates": ["dos.yaml", "docs/dos.yaml", "ontology/dos.yaml",
                       "docs/ontology/dos.yaml", ".aidlc/dos.yaml"],
        "produced_by": "/dos-extract",
        "consumers": [
            "/issue --dos 的词表闭包（缺席 = 客观触发 PSL 轨退回自评）",
            "lint_cards.py --dos 的 dos_slice 闭包（缺席 = 卡里的名词无人解析）",
            "verify_vocabulary.py 的散文传感器（缺席 = exit 3 未检，不是通过）",
        ],
    },
    "decisions": {
        "label": "本体决策轨",
        "filename": "decisions.md",
        "kind": "file",
        "sibling_of": "dos",
        "produced_by": "/dos-extract",
        "consumers": ["verify_dos.py --decisions 的命名豁免", "verify_vocabulary.py 的词表豁免"],
    },
    "agent_map": {
        "label": "仓库地图",
        "filename": "agent-map.md",
        "kind": "file",
        "candidates": ["agent-map.md", "docs/agent-map.md", "AGENT-MAP.md", ".aidlc/agent-map.md"],
        "produced_by": "/dos-extract（assets/agent_map_template.md + verify_agent_map.py --probe）",
        "consumers": [
            "slice_agent_map.py → card_context.md 的「仓库怎么干活」一节"
            "（缺席 = 实现者拿到零行，自己猜命令 / 禁区 / 陷阱）",
        ],
    },
    "invariants": {
        "label": "□ 常驻不变量卡",
        "filename": "invariants/",
        "kind": "dir",
        "glob": "*.y*ml",
        "candidates": ["invariants", "docs/invariants", ".aidlc/invariants"],
        "produced_by": "/invariant-extract",
        "consumers": ["/spec-compile 编成 fitness fn / property 测试的输入"],
    },
}
KEYS = list(SPEC)
LEVELS = ("optional", "recommended", "required")


# ---- git ------------------------------------------------------------------------------------
def repo_root(start: str = ".") -> str:
    """git toplevel，拿不到就退回给定目录的绝对路径（非 git 仓库仍然可用）。"""
    r = subprocess.run(["git", "-C", start, "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else os.path.abspath(start)


def _in_git(root: str) -> bool:
    return subprocess.run(["git", "-C", root, "rev-parse", "--git-dir"],
                          capture_output=True).returncode == 0


def _tracked(root: str, rel: str):
    """→ True tracked · False 未 tracked · None 不在 git 仓库里（无法判定，不算失败）。"""
    if not _in_git(root):
        return None
    r = subprocess.run(["git", "-C", root, "ls-files", "--", rel], capture_output=True, text=True)
    return bool(r.stdout.strip())


def _ignored(root: str, rel: str) -> bool:
    if not _in_git(root):
        return False
    return subprocess.run(["git", "-C", root, "check-ignore", "-q", "--", rel],
                          capture_output=True).returncode == 0


# ---- discovery ------------------------------------------------------------------------------
def scoped(scope: str | None, rel: str) -> str:
    """→ scope 下的候选路径（scope 为空就是原路径）。"""
    return os.path.join(scope, rel) if scope else rel


def candidates_for(spec: dict, scope: str | None) -> list[str]:
    """→ 求值序：先 scope 内，再仓库根。

    回落是有意的，不是兜底：`agent-map.md`（这个仓库怎么干活）天然是仓库级的一份，
    而 `dos.yaml`（这个 package 的本体）是 package 级的。两者用同一张表表达，
    靠的就是「scope 里没有就用仓库根那份」。
    """
    base = list(spec["candidates"])
    if not scope:
        return base
    return [scoped(scope, c) for c in base] + base


def _exists(root: str, rel: str, spec: dict):
    """→ (found, count)。目录 kind 还要至少有一个匹配 glob 的文件才算数。"""
    p = os.path.join(root, rel)
    if spec["kind"] == "file":
        return os.path.isfile(p), None
    if not os.path.isdir(p):
        return False, None
    import glob as _g
    n = len(_g.glob(os.path.join(p, spec.get("glob", "*"))))
    return True, n


_CACHE: dict[str, dict] = {}


def discover(root: str | None = None, refresh: bool = False, scope: str | None = None) -> dict:
    """→ {key: record}。记录只陈述可核对的事实，不做要求判断（要求在 sizing.yaml 里）。

    结果按仓库根缓存：`prereqs()` 与 `doctor` 在一次进程里会反复问同一个问题，而每次问都要
    起若干个 git 子进程。缓存的是**一次运行内**的事实——`--refresh` 或换个进程就重新读。
    """
    root = repo_root(root or ".")
    scope = (scope or "").strip("/") or None
    cache_key = f"{root}::{scope or ''}"
    if not refresh and cache_key in _CACHE:
        return _CACHE[cache_key]
    out: dict[str, dict] = {}
    for key, spec in SPEC.items():
        rec = {"key": key, "label": spec["label"], "kind": spec["kind"],
               "canonical": None, "path": None, "found": False, "tracked": None,
               "ignored": False, "runtime_dir": False, "count": None,
               "produced_by": spec["produced_by"], "searched": []}
        if "sibling_of" in spec:
            # decisions.md 跟着 dos.yaml 走：本体在哪就去哪找它。但**建议写到哪**跟的是本体的
            # canonical 而不是它碰巧所在的目录——本体落在 .aidlc/ 时，再建议把审计轨也写进
            # .aidlc/ 就是把一个错误位置传染给第二份制品。
            sib = out.get(spec["sibling_of"]) or {}
            good = sib.get("found") and not sib.get("runtime_dir")
            look = os.path.dirname(sib.get("path") or "") if sib.get("found") else ""
            want = os.path.dirname(sib.get("canonical") or "") if good else ""
            cands = [os.path.join(look, spec["filename"]) if look else spec["filename"]]
            canonical_override = os.path.join(want, spec["filename"]) if want else scoped(scope, spec["filename"])
        else:
            cands = candidates_for(spec, scope)
        rec["canonical"] = (canonical_override if "sibling_of" in spec
                            else cands[0] + ("/" if spec["kind"] == "dir" else ""))
        rec["searched"] = cands
        for rel in cands:
            found, count = _exists(root, rel, spec)
            if found:
                rec.update(path=rel, found=True, count=count,
                           tracked=_tracked(root, rel), ignored=_ignored(root, rel),
                           runtime_dir=rel.startswith(RUNTIME_DIRS))
                break
        out[key] = rec
    out["_root"] = {"path": root, "is_git": _in_git(root), "scope": scope}
    _CACHE[cache_key] = out
    return out


def find(key: str, root: str | None = None, scope: str | None = None) -> str | None:
    """→ 命中的绝对路径，没找到给 None。给 verify_issue.py / lint_cards.py 的自动发现用。"""
    disc = discover(root, scope=scope)
    rec = disc.get(key) or {}
    return os.path.join(disc["_root"]["path"], rec["path"]) if rec.get("found") else None


# ---- findings（doctor / repo 共用的一份措辞）----------------------------------------------
def findings(disc: dict, requirements: dict | None = None) -> list[dict]:
    """→ [{severity, key, check, hint}]。requirements: {key: optional|recommended|required}。

    严重度的两条来源分开算，取最重的那条：
      ① 缺失 —— 按 requirements 给的档位（required → error，recommended → warn，其余 info）；
      ② 位置 / 版本库 —— 找到了但没进 git，或落在 .aidlc/ 这类运行时目录里：一律 warn，
         与档位无关。这一条是「团队共享」那个要求的机械形态，不是可以按档放宽的偏好。
    """
    req = requirements or {}
    sev_of = {"required": "error", "recommended": "warn"}
    out = []
    for key in KEYS:
        rec = disc.get(key) or {}
        level = req.get(key, "optional")
        if not rec.get("found"):
            out.append({
                "severity": sev_of.get(level, "info"), "key": key,
                "check": f"{rec.get('label', key)} ({SPEC[key]['filename']})",
                "hint": f"找不到（找过：{', '.join(rec.get('searched') or [])}）。"
                        f"跑 {rec.get('produced_by')}，写到 `{rec.get('canonical')}` 并提交进 git。"
                        f"缺席时下游是**未检**不是通过：{'；'.join(SPEC[key].get('consumers') or []) or '—'}",
            })
            continue
        if (rec.get("tracked") is False or rec.get("ignored")) and not rec.get("runtime_dir"):
            why = "被 .gitignore 吃掉了" if rec.get("ignored") else "没进 git"
            out.append({
                "severity": "warn", "key": key,
                "check": f"{rec['label']} 未共享",
                "hint": f"`{rec['path']}` 在，但{why}——队友 clone 下来是空的。"
                        f"这不是「有本体」，是「你有本体」。`git add {rec['path']}`",
            })
        if rec.get("runtime_dir"):
            out.append({
                "severity": "warn", "key": key,
                "check": f"{rec['label']} 位置不共享",
                "hint": f"`{rec['path']}` 落在运行时目录里（.aidlc / .sdlc 是 per-run 状态，"
                        f"不是共享位置）。移到 `{rec['canonical']}` 并提交",
            })
        if rec["kind"] == "dir" and rec.get("count") == 0:
            out.append({
                "severity": "info", "key": key,
                "check": f"{rec['label']} 是空目录",
                "hint": f"`{rec['path']}` 里没有 {SPEC[key].get('glob')} —— 目录在不等于卡在",
            })
    return out


# ---- CLI ------------------------------------------------------------------------------------
def render(disc: dict, req: dict | None = None) -> str:
    sc = disc["_root"].get("scope")
    lines = ["仓库级 X1 制品（进 git、全组共享——不放 .aidlc/）",
             f"  仓库根 {disc['_root']['path']}" + ("" if disc["_root"]["is_git"] else "  [不是 git 仓库]")
             + (f"\n  scope  {sc}/  （找不到时回落到仓库根）" if sc else ""), ""]
    mark = {True: "✓", False: "✗"}
    for key in KEYS:
        r = disc[key]
        state = f"→ 该写到 {r['canonical']}"
        if r["found"]:
            state = {True: "tracked", False: "未进 git", None: "无法判定"}[r["tracked"]]
            if r["ignored"]:
                state = "被 gitignore"
            if r["runtime_dir"]:
                state += " · 运行时目录"
            if r["kind"] == "dir" and r["count"] is not None:
                state += f" · {r['count']} 张卡"
        level = (req or {}).get(key, "optional")
        lines.append(f"  {mark[r['found']]} {SPEC[key]['filename']:<16} "
                     f"{(r['path'] or '缺'):<26} {state:<34} [{level}]")
    return "\n".join(lines)


ONBOARDING = """
一次性落地（跑完提交进 git，全组共用一份）：
  1. /dos-extract        → dos.yaml + decisions.md          （闭包检查与 dos_slice 的解析源）
  2. /dos-extract 的仓库地图 → agent-map.md                  （verify_agent_map.py --probe 逐条实跑）
  3. /invariant-extract  → invariants/*.yaml                （□ 常驻不变量，给 /spec-compile）
本体不随 feature 变：做一次，之后每个 slug 自动发现它，不必重跑，也不必手动 set 路径。
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--scope", help="monorepo：先在这个仓库根相对目录里找（如 plugins/ai-dlc），"
                                    "找不到再回落到仓库根。一个 package 一个 bounded context")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--path", choices=KEYS, help="只打印这个制品命中的路径（没找到 exit 1，不打印）")
    a = ap.parse_args()
    disc = discover(a.repo_root, scope=a.scope)
    if a.path:
        rec = disc[a.path]
        if not rec["found"]:
            sys.exit(1)
        print(os.path.join(disc["_root"]["path"], rec["path"]))
        return
    fs = findings(disc)
    if a.json:
        print(json.dumps({"root": disc["_root"], "assets": {k: disc[k] for k in KEYS},
                          "findings": fs}, ensure_ascii=False, indent=2))
    else:
        print(render(disc))
        missing = [k for k in KEYS if not disc[k]["found"]]
        if missing:
            print(ONBOARDING)
    bad = [k for k in KEYS if not disc[k]["found"] or disc[k]["tracked"] is False
           or disc[k]["ignored"] or disc[k]["runtime_dir"]]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
