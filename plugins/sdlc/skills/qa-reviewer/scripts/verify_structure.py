#!/usr/bin/env python3
"""verify_structure.py — A 档的结构性质量闸（done_when.constraints.structure 的执行器）。

缺口：A 档现在检测试、lint、类型、secrets、白名单、锁、新增依赖，**不检代码结构**——
圈复杂度增量、重复块、依赖方向。而这三项恰恰是 agent 代码退化最快的维度
（GitClear 2026：复制粘贴 9.4% → 15.7%，重构 21% → 3.8%；arXiv 2608.25241：认知复杂度
+27% vs +53%）。测试全绿、lint 全绿、结构烂掉，是当前这条流水线放行的产物。

本脚本读契约里声明的结构约束，对 **本次 diff 引入的代码** 求值，产出 structure-facts.yaml。

用法：
  verify_structure.py --done-when done_when.yaml [--base <git-ref>] [--repo .]
                      [--out structure-facts.yaml] [--require-analyzers] [--json]

退出码：
  0 = 全部声明的约束都被求值且都满足
  1 = 有约束被违反（A 档一票否决）
  2 = 用法 / IO 错误
  3 = **有约束声明了但无法求值**（分析器缺席 / 语言不支持）——这不是 pass。
      契约承诺了一条判据，没人能证明它成立；调用方必须把它当"未检"记录，不是"通过"。
      `--require-analyzers` 把 3 变成 1（CI 里该这么用）。

设计要点（为什么这样而不是那样）：
  - **只看新增代码**。存量的高复杂度不是本次 PR 的责任；`--base` 给基线，没有 base 时退化为
    绝对值检查并在 facts 里写明 scope=absolute。
  - **分析器缺席 ≠ 通过**。这是整个脚本唯一不能妥协的地方：一把没跑的尺子不能报绿。
  - **内建分析器只做能做准的**：圈复杂度用 Python ast 精确算，其它语言交给 lizard；
    重复检测与语言无关（归一化行窗口哈希）；依赖方向解析 py / js / ts 的 import。
    近似的东西不冒充精确的：不支持就报 unevaluated。

契约形状（done_when.yaml）：
  constraints:
    structure:
      max_function_complexity: 15        # 新增/修改函数的绝对上限
      max_complexity_delta: 5            # 同名函数相对 base 的最大增量
      max_duplicate_block_lines: 30      # 新增代码与仓库其它处最长重复块
      max_duplicate_ratio: 0.10          # 新增行里落在重复块内的比例
      layers:                            # 依赖方向；低层不得 import 高层
        - {name: domain, path: "src/domain/**", may_import: []}
        - {name: app,    path: "src/app/**",    may_import: [domain]}
      exclude: ["**/vendor/**"]          # 三项检查共同的排除
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

try:
    import yaml
except ImportError:
    yaml = None

PY = (".py",)
LIZARD_LANGS = (".c", ".cc", ".cpp", ".h", ".hpp", ".java", ".cs", ".js", ".jsx", ".ts", ".tsx",
                ".go", ".rb", ".php", ".swift", ".rs", ".kt", ".scala", ".m", ".lua")
COMMENT = {".py": "#", ".sh": "#", ".rb": "#", ".yaml": "#", ".yml": "#"}
DEFAULT_EXCLUDE = ["**/node_modules/**", "**/.git/**", "**/dist/**", "**/build/**",
                   "**/__pycache__/**", "**/vendor/**", "**/*.min.js", "**/.venv/**"]


# ---------------------------------------------------------------- helpers
def sh(args, cwd=None):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def excluded(path, patterns):
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def match_glob(path, pattern):
    # "src/domain/**" should match src/domain/x.py and src/domain/a/b.py
    if fnmatch.fnmatch(path, pattern):
        return True
    if pattern.endswith("/**") and (path + "/").startswith(pattern[:-2]):
        return True
    return False


# ---------------------------------------------------------------- complexity
class _Cyclo(ast.NodeVisitor):
    """McCabe 圈复杂度：1 + 判定点。ast 精确，不是正则近似。"""

    def __init__(self):
        self.score = 1

    def _bump(self, n=1):
        self.score += n

    def visit_If(self, node):
        self._bump(); self.generic_visit(node)

    def visit_For(self, node):
        self._bump(); self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self._bump(); self.generic_visit(node)

    def visit_While(self, node):
        self._bump(); self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self._bump(); self.generic_visit(node)

    def visit_With(self, node):
        self.generic_visit(node)

    def visit_Assert(self, node):
        self._bump(); self.generic_visit(node)

    def visit_BoolOp(self, node):
        self._bump(len(node.values) - 1); self.generic_visit(node)

    def visit_IfExp(self, node):
        self._bump(); self.generic_visit(node)

    def visit_comprehension(self, node):
        self._bump(1 + len(node.ifs)); self.generic_visit(node)

    def visit_Match(self, node):
        self._bump(len(node.cases)); self.generic_visit(node)


def py_functions(src, path):
    """→ {qualified_name: complexity}；解析失败返回 None（区别于"没有函数"）。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    out, stack = {}, []

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = f"{prefix}{child.name}"
                c = _Cyclo()
                for sub in ast.iter_child_nodes(child):
                    c.visit(sub)
                out[name] = c.score
                walk(child, name + ".")
            elif isinstance(child, ast.ClassDef):
                walk(child, f"{prefix}{child.name}.")
            else:
                walk(child, prefix)

    walk(tree, "")
    return out


def lizard_functions(path):
    code, out, _ = sh(["lizard", "-w", "--csv", path])
    if code not in (0, 1) or not out.strip():
        return None
    res = {}
    for line in out.strip().splitlines():
        parts = line.split(",")
        if len(parts) < 8:
            continue
        try:
            ccn = int(parts[1])
        except ValueError:
            continue
        res[parts[7].strip('"')] = ccn
    return res or None


def complexity_of(path, src, have_lizard):
    ext = os.path.splitext(path)[1]
    if ext in PY:
        f = py_functions(src, path)
        return (f, "builtin-ast") if f is not None else (None, "parse-error")
    if have_lizard and ext in LIZARD_LANGS:
        f = lizard_functions(path)
        return (f, "lizard") if f is not None else (None, "lizard-failed")
    return None, f"no analyzer for {ext or 'ext-less'}"


# ---------------------------------------------------------------- duplication
def normalise(lines, ext):
    """去注释、去空白、去空行；返回 [(归一化行, 原行号)]。"""
    mark, out, in_block = COMMENT.get(ext), [], False
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if ext in (".py",) and (s.startswith('"""') or s.startswith("'''")):
            in_block = not in_block if s.count('"""') % 2 or s.count("'''") % 2 else in_block
            continue
        if in_block:
            continue
        if mark and s.startswith(mark):
            continue
        if ext in (".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".c", ".cpp", ".rs") and (s.startswith("//") or s.startswith("*") or s.startswith("/*")):
            continue
        s = re.sub(r"\s+", " ", s)
        if len(s) < 4:
            continue
        out.append((s, i))
    return out


def dup_runs(added_norm, corpus, min_lines):
    """added_norm: [(line, lineno)] 本次新增；corpus: {hash: [(path, lineno)]} 仓库其它处。
    返回最长重复运行的列表（贪心，不重叠）。"""
    runs, i, n = [], 0, len(added_norm)
    while i < n:
        best = 0
        best_at = None
        # 从 i 起能匹配多长
        j = i
        while j < n:
            h = hashlib.sha1(added_norm[j][0].encode()).hexdigest()[:16]
            if h not in corpus:
                break
            j += 1
        length = j - i
        if length >= min_lines:
            # 确认这一整段确实连续出现在同一个别处文件里
            seq = [hashlib.sha1(x[0].encode()).hexdigest()[:16] for x in added_norm[i:j]]
            for path, start in corpus.get(seq[0], []):
                ok = True
                for k, h in enumerate(seq):
                    if (path, start + k) not in {(p, l) for p, l in corpus.get(h, [])}:
                        ok = False
                        break
                if ok:
                    best, best_at = length, (path, start)
                    break
        if best:
            runs.append({"lines": best, "from_line": added_norm[i][1],
                         "to_line": added_norm[j - 1][1],
                         "also_at": f"{best_at[0]}:{best_at[1]}" if best_at else "unknown"})
            i = j
        else:
            i += 1
    return runs


# ---------------------------------------------------------------- dependency
IMPORT_PY = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M)
IMPORT_JS = re.compile(r"""(?:from\s+|require\(\s*)['"]([^'"]+)['"]""")


def imports_of(path, src, repo):
    ext = os.path.splitext(path)[1]
    targets = []
    if ext in PY:
        for m in IMPORT_PY.finditer(src):
            mod = (m.group(1) or m.group(2) or "").split(".")
            if not mod or not mod[0]:
                continue
            cand = os.path.join(*mod)
            for suffix in (".py", "/__init__.py"):
                p = cand + suffix
                if os.path.isfile(os.path.join(repo, p)):
                    targets.append(p)
                    break
    elif ext in (".js", ".jsx", ".ts", ".tsx", ".mjs"):
        base = os.path.dirname(path)
        for m in IMPORT_JS.finditer(src):
            spec = m.group(1)
            if spec.startswith("."):
                cand = os.path.normpath(os.path.join(base, spec))
            else:
                cand = spec
            for suffix in ("", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.js"):
                p = cand + suffix
                if os.path.isfile(os.path.join(repo, p)):
                    targets.append(p)
                    break
    return targets


def layer_of(path, layers):
    for lay in layers:
        if match_glob(path, lay.get("path", "")):
            return lay.get("name")
    return None


# ---------------------------------------------------------------- git
def changed_files(repo, base):
    code, out, err = sh(["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD"], cwd=repo)
    if code != 0:
        code, out, err = sh(["git", "diff", "--name-only", "--diff-filter=ACMR", base], cwd=repo)
    if code != 0:
        return None, err.strip()
    return [l for l in out.splitlines() if l.strip()], None


def added_lines(repo, base, path):
    """→ [(内容, 新文件里的行号)]"""
    code, out, _ = sh(["git", "diff", "-U0", f"{base}...HEAD", "--", path], cwd=repo)
    if code != 0:
        code, out, _ = sh(["git", "diff", "-U0", base, "--", path], cwd=repo)
    res, lineno = [], 0
    for line in out.splitlines():
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)", line)
        if m:
            lineno = int(m.group(1))
            continue
        if line.startswith("+") and not line.startswith("+++"):
            res.append((line[1:], lineno))
            lineno += 1
        elif not line.startswith("-") and not line.startswith("\\"):
            lineno += 1
    return res


def file_at(repo, ref, path):
    code, out, _ = sh(["git", "show", f"{ref}:{path}"], cwd=repo)
    return out if code == 0 else None


def repo_files(repo, exclude):
    """git ls-files 优先；不是 git 仓库（或空仓库）时退回文件系统遍历。

    这里曾经 `return []` —— 于是"数不出文件"和"没有违反"变成同一个结果，闸对着一个空列表报绿。
    2026-09-06 的孪生用例抓到：fixture 目录不是 git 仓库，三条约束全声明了，verdict = PASS。
    与退出码 3 同一条道理：数不出来不是通过。"""
    code, out, _ = sh(["git", "ls-files"], cwd=repo)
    files = [p for p in out.splitlines() if p.strip()] if code == 0 else []
    if not files:
        for root, dirs, names in os.walk(repo):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", ".venv")]
            for nm in names:
                files.append(os.path.relpath(os.path.join(root, nm), repo))
    return [p for p in files if not excluded(p, exclude)]


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--done-when", required=True)
    ap.add_argument("--base", help="git ref 作为基线；缺省则只做绝对值检查（facts 里 scope=absolute）")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default="structure-facts.yaml")
    ap.add_argument("--require-analyzers", action="store_true", help="无法求值的约束按违反处理（exit 1 而不是 3）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if yaml is None:
        sys.stderr.write("verify_structure.py needs PyYAML\n")
        return 2
    try:
        dw = yaml.safe_load(open(a.done_when, encoding="utf-8")) or {}
    except Exception as e:
        sys.stderr.write(f"verify_structure: {e}\n")
        return 2
    cs = ((dw.get("constraints") or {}).get("structure")) or {}
    repo = os.path.abspath(a.repo)
    facts = {"done_when": a.done_when, "base": a.base, "scope": "delta" if a.base else "absolute",
             "declared": sorted(k for k in cs if k != "exclude"),
             "checks": {}, "breaches": [], "unevaluated": [], "analyzers": {}}
    if not cs:
        facts["note"] = ("契约没有声明 constraints.structure —— 本闸无对象。"
                         "这不是通过，是没有判据：结构性质量在这次交付里没有被任何人承诺。")
        out_text = yaml.safe_dump(facts, allow_unicode=True, sort_keys=False)
        open(a.out, "w", encoding="utf-8").write(out_text)
        print(json.dumps(facts, ensure_ascii=False, indent=2) if a.json else out_text)
        return 0

    exclude = DEFAULT_EXCLUDE + list(cs.get("exclude") or [])
    have_lizard = shutil.which("lizard") is not None
    facts["analyzers"]["lizard"] = "present" if have_lizard else "absent"

    files, err = (changed_files(repo, a.base) if a.base else (repo_files(repo, exclude), None))
    if files is None:
        facts["unevaluated"].append({"what": "changed files", "why": f"git diff failed: {err}"})
        files = []
    files = [f for f in files if not excluded(f, exclude) and os.path.isfile(os.path.join(repo, f))]
    facts["files_considered"] = len(files)
    if not files:
        # 声明了约束却一个文件都没数出来 = 没有求值，不是通过（与退出码 3 同一条道理）
        facts["unevaluated"].append({
            "what": "file enumeration", "why": f"{repo} 下没有可分析的文件（不是 git 仓库？base ref 之间无改动？exclude 太宽？）",
            "fix": "确认 --repo 指对了、--base 之间确有改动；空文件列表下的 PASS 是假绿"})

    # ---- 1. 复杂度 -------------------------------------------------------
    cap = cs.get("max_function_complexity")
    delta_cap = cs.get("max_complexity_delta")
    if cap is not None or delta_cap is not None:
        rows, unev = [], []
        for path in files:
            try:
                src = open(os.path.join(repo, path), encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            now_fns, how = complexity_of(path, src, have_lizard)
            if now_fns is None:
                if os.path.splitext(path)[1] in PY + LIZARD_LANGS or have_lizard:
                    unev.append({"file": path, "why": how})
                continue
            base_fns = {}
            if a.base and delta_cap is not None:
                old = file_at(repo, a.base, path)
                if old is not None:
                    base_fns = complexity_of(path, old, have_lizard)[0] or {}
            for fn, score in sorted(now_fns.items()):
                before = base_fns.get(fn)
                delta = None if before is None else score - before
                row = {"file": path, "function": fn, "complexity": score,
                       "base": before, "delta": delta, "analyzer": how}
                if cap is not None and score > cap and (before is None or score > before):
                    row["breach"] = f"complexity {score} > max_function_complexity {cap}"
                    facts["breaches"].append(row)
                elif delta_cap is not None and delta is not None and delta > delta_cap:
                    row["breach"] = f"delta +{delta} > max_complexity_delta {delta_cap}"
                    facts["breaches"].append(row)
                rows.append(row)
        facts["checks"]["complexity"] = {
            "functions_measured": len(rows),
            "worst": sorted(rows, key=lambda r: -r["complexity"])[:5],
        }
        if unev:
            facts["unevaluated"].append({"what": "complexity", "why": "no analyzer for these files",
                                         "files": unev[:20],
                                         "fix": "pip install lizard（覆盖 C/Java/JS/TS/Go/Rust…），或把这些路径写进 constraints.structure.exclude 并说明理由"})

    # ---- 2. 重复 ---------------------------------------------------------
    dup_cap = cs.get("max_duplicate_block_lines")
    ratio_cap = cs.get("max_duplicate_ratio")
    if dup_cap is not None or ratio_cap is not None:
        min_lines = int(dup_cap or 30)
        corpus = {}
        for path in repo_files(repo, exclude):
            if path in files:
                continue
            try:
                lines = open(os.path.join(repo, path), encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                continue
            for norm, ln in normalise(lines, os.path.splitext(path)[1]):
                corpus.setdefault(hashlib.sha1(norm.encode()).hexdigest()[:16], []).append((path, ln))
        total_added, dup_added, all_runs = 0, 0, []
        for path in files:
            if a.base:
                pairs = added_lines(repo, a.base, path)
                if not pairs:
                    continue
                norm = normalise([c for c, _ in pairs], os.path.splitext(path)[1])
            else:
                try:
                    norm = normalise(open(os.path.join(repo, path), encoding="utf-8", errors="replace").read().splitlines(),
                                     os.path.splitext(path)[1])
                except OSError:
                    continue
            total_added += len(norm)
            runs = dup_runs(norm, corpus, min_lines)
            for r in runs:
                r["file"] = path
                dup_added += r["lines"]
                all_runs.append(r)
                if dup_cap is not None and r["lines"] > dup_cap:
                    facts["breaches"].append({**r, "breach": f"duplicate run {r['lines']} lines > max_duplicate_block_lines {dup_cap}"})
        ratio = (dup_added / total_added) if total_added else 0.0
        facts["checks"]["duplication"] = {"added_lines_normalised": total_added,
                                          "duplicated_lines": dup_added,
                                          "ratio": round(ratio, 4),
                                          "runs": all_runs[:10],
                                          "analyzer": "builtin-line-window"}
        if ratio_cap is not None and ratio > float(ratio_cap):
            facts["breaches"].append({"breach": f"duplicate ratio {ratio:.3f} > max_duplicate_ratio {ratio_cap}",
                                      "duplicated_lines": dup_added, "added_lines": total_added})

    # ---- 3. 依赖方向 ------------------------------------------------------
    layers = cs.get("layers") or []
    if layers:
        edges, unev = [], []
        for path in files:
            ext = os.path.splitext(path)[1]
            if ext not in PY + (".js", ".jsx", ".ts", ".tsx", ".mjs"):
                if layer_of(path, layers):
                    unev.append({"file": path, "why": f"import 解析不支持 {ext or 'ext-less'}"})
                continue
            src_layer = layer_of(path, layers)
            if src_layer is None:
                continue
            try:
                src = open(os.path.join(repo, path), encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            allowed = next((set(l.get("may_import") or []) for l in layers if l.get("name") == src_layer), set())
            for target in imports_of(path, src, repo):
                tl = layer_of(target, layers)
                if tl is None or tl == src_layer:
                    continue
                edge = {"from": path, "from_layer": src_layer, "to": target, "to_layer": tl}
                edges.append(edge)
                if tl not in allowed:
                    facts["breaches"].append({**edge, "breach": f"{src_layer} may_import {sorted(allowed)}, imports {tl}"})
        facts["checks"]["dependency"] = {"cross_layer_edges": len(edges), "edges": edges[:20],
                                         "analyzer": "builtin-import-scan"}
        if unev:
            facts["unevaluated"].append({"what": "dependency", "why": "import 解析不支持这些语言",
                                         "files": unev[:20],
                                         "fix": "装 dependency-cruiser 并在 constraints 里声明，或把这些路径写进 exclude"})

    facts["verdict"] = ("breach" if facts["breaches"] else ("unevaluated" if facts["unevaluated"] else "pass"))
    facts["tier"] = "A"
    out_text = yaml.safe_dump(facts, allow_unicode=True, sort_keys=False, width=120)
    open(a.out, "w", encoding="utf-8").write(out_text)
    if a.json:
        print(json.dumps(facts, ensure_ascii=False, indent=2))
    else:
        print(f"verify_structure · verdict = {facts['verdict'].upper()} · 声明 {facts['declared']} · 文件 {facts['files_considered']} · scope {facts['scope']}")
        for b in facts["breaches"][:20]:
            where = b.get("from") or b.get("file") or ""
            if b.get("function"):
                where = f"{where}:{b['function']}"
            elif b.get("from_line"):
                where = f"{where}:{b['from_line']}-{b.get('to_line')}"
            print(f"  BREACH  {where or '(whole diff)'} — {b['breach']}")
        for u in facts["unevaluated"]:
            print(f"  UNEVAL  {u['what']}: {u['why']}（{len(u.get('files', []))} 个文件）→ {u.get('fix', '')}")
        print(f"  facts → {a.out}")
    if facts["breaches"]:
        return 1
    if facts["unevaluated"]:
        return 1 if a.require_analyzers else 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
