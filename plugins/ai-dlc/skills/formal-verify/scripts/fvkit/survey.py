"""Entrance C — repo survey: from an existing repository to verification targets.

Entrances A and B start from a requirement someone already named. Entrance C starts from a
repository and nothing else, and answers "what here is worth verifying, and with what?".
The procedures are vendored upstream text (see upstream.py), carried out by an agent:

  pstack create-formal-verification-skill   "Choose the target from the code" (a promise the code
                                            makes, where a break harms users and tests rarely reach
                                            the breaking case; the strongest, not the easiest) and
                                            "Let the question choose the tool"
  oss-verify add-project (Theorem)          step 1 "Ask what 'correct' means. Do not guess an
                                            answer." (six topics) and step 3: start from the
                                            project's existing fuzz targets / tests
  FM-Agent workflow_generate_phases         partition the repo into modules; exclude test files

This module does the two parts a script can do honestly:

  scan   deterministic inventory of the repository: languages, test files, existing checks
         (fuzz targets, property tests, formal specs, code proofs), risk signals with verbatim
         line anchors, fix-commit history per file (Specula bug archaeology), the verifiers
         installed here, and per-file clusters ordered by a documented score. The score orders
         reading; it decides nothing.
  check  the agent's `fv-targets` document: every correctness topic observed (with a verbatim
         anchor) or answered by a human, every target true to the code (verbatim anchors), its
         harm and promise in one sentence each, the tool fit for the language and installed (or
         an install line), an honest scope, and every high-scoring cluster and every existing
         fuzz/property test either taken up by a target or dismissed with a reason. Nothing is
         dropped silently. A survey whose repository changed since the scan is STALE.
"""
import fnmatch
import os
import re
import shutil
import subprocess
from pathlib import Path

from .spec import _keys, load_document
from .upstream import REQUIRED, citations
from .values import FvError, require, sha_bytes

KIND = "fv-survey"
TARGETS_KIND = "fv-targets"
MAX_FILE_BYTES = 1024 * 1024
DEFAULT_EXCLUDE = (".git", "node_modules", "vendor", "third_party", "dist", "build", "out", "target", ".venv", "venv",
                   "__pycache__", ".tox", ".mypy_cache", ".pytest_cache", "coverage", ".next", ".turbo", ".cache")

LANGUAGES = {
    "py": "python", "js": "javascript", "mjs": "javascript", "cjs": "javascript", "jsx": "javascript",
    "ts": "typescript", "tsx": "typescript", "mts": "typescript", "cts": "typescript", "go": "go", "rs": "rust",
    "c": "c", "h": "c", "cc": "cpp", "cpp": "cpp", "cxx": "cpp", "hpp": "cpp", "hh": "cpp", "java": "java",
    "kt": "kotlin", "scala": "scala", "rb": "ruby", "php": "php", "cs": "csharp", "swift": "swift",
    "ex": "elixir", "exs": "elixir", "erl": "erlang", "sql": "sql", "dfy": "dafny", "lean": "lean",
}
FORMAL_EXT = {"tla": "tla", "qnt": "quint", "fizz": "fizzbee", "als": "alloy", "pml": "promela", "dfy": "dafny", "lean": "lean"}

# FM-Agent md/workflow_generate_phases.md: "Exclude all test files (e.g., files in test/, tests/, __tests__/
# directories, or files named *_test.*, test_*.*, *_spec.*)" — plus the *.test.* / *.spec.* JS convention.
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "testing", "e2e"}
TEST_NAME = re.compile(r"(^test_.*\.|_test\.|_spec\.|\.test\.|\.spec\.|^conftest\.py$)")

# Risk signals. Each class names a kind of promise that tests rarely reach (pstack: "concurrency, retries,
# state machines, parsers, or unsafe code need more than tests"). A hit is a place to read, not a finding.
SIGNALS = {
    "concurrency": r"\b(threading|Thread\(|Mutex|RwLock|Semaphore|asyncio\.(gather|Lock|create_task)|synchronized|go func|"
                   r"sync\.(Mutex|RWMutex|WaitGroup)|atomic\.|Atomic[A-Z]\w*|compare_?and_?(swap|set)|compareAndSet|"
                   r"Promise\.all|tokio::spawn|std::thread|pthread_\w+|Worker\(|SharedArrayBuffer)",
    "transaction": r"(\b(BEGIN|COMMIT|ROLLBACK|SAVEPOINT)\b|FOR UPDATE|SERIALIZABLE|\btransaction\w*\s*\(|\.transaction\b|"
                   r"@transaction|isolation[_ ]?level|\boutbox\b|optimistic[_ ]?lock|\bversion\s*=\s*version\s*\+)",
    "retry-idempotency": r"(?i)(idempoten|\bretr(y|ies|ied)\b|backoff|dedup|exactly[- ]once|at[- ]least[- ]once|"
                         r"\bredeliver|\brequeue|\breplay)",
    "permission": r"(?i)(authori[sz](e|ation)|\bpermission|\bacl\b|\brbac\b|\brevok|\bgrant(ed|s)?\b|\bis_?admin\b|"
                  r"access[_-]?control|\bcedar\b|\bcasbin\b|\bimpersonat)",
    "state-machine": r"(\b(status|state)\s*(===|==|!=|!==)\s*['\"]\w+['\"]|\b(status|state)\s*[:=]\s*['\"][a-z_]+['\"]|"
                     r"StateMachine|state_machine|\btransition(s|_to)?\b|enum\s+\w*(State|Status)\b|"
                     r"class\s+\w*(State|Status)\b)",
    "quantity": r"(?i)\b(balance|stock|inventory|quantity|quota|budget|refund|ledger|debit|credit|oversell|capacity|"
                r"remaining|allowance)\b",
    "parser": r"\b(parse|decode|deserializ|unmarshal|unpickle|from_bytes|struct\.unpack|yaml\.load|pickle\.loads|"
              r"JSON\.parse|json\.loads|read_exact)\w*",
    "low-level": r"(\bunsafe\s*(\{|fn\b|impl\b)|\bmemcpy\b|\bstrcpy\b|\bmalloc\s*\(|\bfree\s*\(|reinterpret_cast|"
                 r"\bctypes\b|as_mut_ptr|from_raw_parts|\btransmute\b|wrapping_(add|sub|mul)|overflow)",
    "time-lease": r"(?i)(\blease|\bexpir(e|es|ed|y|ation)\b|\bttl\b|\bdeadline\b|\bheartbeat|\bfencing)",
}
SIGNAL_RES = {k: re.compile(v) for k, v in SIGNALS.items()}
STATEFUL = ("concurrency", "transaction", "retry-idempotency", "permission", "state-machine", "time-lease", "quantity")

# Existing checks: oss-verify add-project step 3 starts "from the project's existing fuzz targets"; pstack
# keeps a verification that already exists in step with the code instead of writing a second one.
EXISTING = [
    ("fuzz-target", "libfuzzer", re.compile(r"\bLLVMFuzzerTestOneInput\b")),
    ("fuzz-target", "atheris", re.compile(r"\batheris\.(Setup|instrument_all|instrument_imports)\b")),
    ("fuzz-target", "cargo-fuzz", re.compile(r"\bfuzz_target!\s*\(")),
    ("fuzz-target", "go-fuzz", re.compile(r"\bfunc\s+Fuzz\w*\s*\(\s*\w+\s+\*testing\.F\)")),
    ("fuzz-target", "jazzer", re.compile(r"@FuzzTest\b|\bjazzer\b")),
    ("property-test", "hypothesis", re.compile(r"@given\s*\(")),
    ("property-test", "fast-check", re.compile(r"\bfc\.(assert|property|asyncProperty)\s*\(")),
    ("property-test", "proptest", re.compile(r"\bproptest!\s*[\{(]")),
    ("property-test", "quickcheck", re.compile(r"#\[quickcheck\]|\bquickcheck!\s*[\{(]")),
    ("property-test", "jqwik", re.compile(r"@Property\b")),
    ("property-test", "rapid", re.compile(r"\brapid\.Check\s*\(")),
    ("code-proof", "kani", re.compile(r"#\[kani::(proof|proof_for_contract)")),
    ("code-proof", "verus", re.compile(r"\bverus!\s*\{")),
    ("code-proof", "rust-contracts", re.compile(r"#\[(requires|ensures)\s*\(")),
    ("code-proof", "cbmc", re.compile(r"\b__CPROVER_\w+")),
    ("code-proof", "frama-c", re.compile(r"/\*@\s*(requires|ensures|loop invariant)")),
    ("contract", "python-contracts", re.compile(r"@(icontract\.)?(require|ensure)\s*\(|@deal\.(pre|post|ensure)\b")),
    ("formal-spec", "fvkit", re.compile(r"^kind:\s*fv-(model|contract)(?![\w-])")),
]

TOOLS = {   # name -> (executables, python module, languages it verifies or models)
    "fvkit": ((), None, ("*",)),
    "project-tests": ((), None, ("*",)),   # the repository's own test runner: lifted properties run there
    "tlc": (("tlc",), None, ("*",)),
    "apalache": (("apalache-mc",), None, ("*",)),
    "quint": (("quint",), None, ("*",)),
    "fizzbee": (("fizz",), None, ("*",)),
    "kani": (("cargo-kani", "kani"), None, ("rust",)),
    "verus": (("verus",), None, ("rust",)),
    "crosshair": (("crosshair",), "crosshair", ("python",)),
    "hypothesis": ((), "hypothesis", ("python",)),
    "esbmc": (("esbmc",), None, ("c", "cpp", "python")),
    "cbmc": (("cbmc",), None, ("c", "cpp")),
    "dafny": (("dafny",), None, ("dafny",)),
    "lean": (("lake", "lean"), None, ("lean",)),
}
MODEL_TOOLS = ("fvkit", "tlc", "apalache", "quint", "fizzbee")
CODE_VERIFIERS = ("kani", "verus", "crosshair", "esbmc", "cbmc", "dafny", "lean")
INPUT_GENERATORS = ("hypothesis", "fast-check", "proptest", "libfuzzer", "atheris", "cargo-fuzz", "go-fuzz", "jazzer")

FIX_SUBJECT = re.compile(r"(?i)(\b(fix(e[sd])?|bug|race|deadlock|duplicate|double|idempot\w*|retry|leak|overflow|crash|"
                         r"revert|regress\w*|hotfix|lost update|stale)\b|修复|竞态|重复|死锁|丢失)")


def _git(root, *args):
    try:
        p = subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout if p.returncode == 0 else None


def _excluded(rel, exclude):
    parts = rel.split("/")
    for pat in exclude:
        if pat in parts or fnmatch.fnmatch(rel, pat) or any(fnmatch.fnmatch(x, pat) for x in parts):
            return True
    return False


def list_files(root, exclude=()):
    """Repository files relative to root: `git ls-files` (respects .gitignore) when root is in a work tree."""
    root = Path(root).resolve()
    exclude = tuple(DEFAULT_EXCLUDE) + tuple(exclude)
    listed = _git(root, "ls-files", "-co", "--exclude-standard", "-z", "--", ".")
    if listed is not None:
        rels = sorted({x for x in listed.split("\0") if x})
    else:
        rels = []
        for dirpath, dirnames, filenames in os.walk(root):
            rel_dir = os.path.relpath(dirpath, root)
            dirnames[:] = sorted(d for d in dirnames if not _excluded(os.path.normpath(os.path.join(rel_dir, d)).replace(os.sep, "/"), exclude))
            for f in filenames:
                rels.append(os.path.normpath(os.path.join(rel_dir, f)).replace(os.sep, "/"))
        rels.sort()
    return [r for r in rels if not _excluded(r, exclude) and (root / r).is_file() and not (root / r).is_symlink()]


# Code that runs the project rather than ships with it. Its clusters are listed after product code and are not
# owed a decision: pstack's target is "a promise the code makes, where a break harms users".
TOOLING_DIRS = {"scripts", "script", "tools", "bin", "examples", "example", "bench", "benches", "benchmarks", "fixtures",
                "docs", "demo", "demos", "migrations"}
TOOLING_NAME = re.compile(r"(?i)(smoke|benchmark|harness|^setup\.py$|^conftest|^build\.|\.config\.)")


def role_of(rel):
    parts = rel.split("/")
    return "tooling" if any(p in TOOLING_DIRS for p in parts[:-1]) or TOOLING_NAME.search(parts[-1]) else "product"


def is_test_file(rel):
    parts = rel.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME.search(parts[-1]))


def _text(path):
    data = path.read_bytes()
    if len(data) > MAX_FILE_BYTES or b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", "replace")


def tool_availability():
    import importlib.util
    out = {}
    for name, (exes, module, langs) in sorted(TOOLS.items()):
        found = next((shutil.which(e) for e in exes if shutil.which(e)), None)
        if name in ("fvkit", "project-tests"):
            out[name] = {"available": True, "how": "bundled" if name == "fvkit" else "the repository's own tests",
                         "languages": list(langs)}
            continue
        how = found
        if not how and module and importlib.util.find_spec(module) is not None:
            how = "python module %s (this interpreter)" % module
        if name == "tlc" and not how and os.environ.get("TLA2TOOLS_JAR"):
            how = "TLA2TOOLS_JAR"
        out[name] = {"available": bool(how), "how": how, "languages": list(langs)}
    return out


def _history(root, limit):
    shallow = (_git(root, "rev-parse", "--is-shallow-repository") or "").strip() == "true"
    log = _git(root, "log", "-n", str(limit), "--relative", "--name-only", "--format=%x1e%s", "--", ".")
    if log is None:
        return {"available": False, "reason": "not a git work tree", "files": {}}
    files, scanned, fixes = {}, 0, 0
    for block in log.split("\x1e")[1:]:
        lines = [x for x in block.split("\n") if x.strip()]
        if not lines:
            continue
        scanned += 1
        if FIX_SUBJECT.search(lines[0]):
            fixes += 1
            for f in lines[1:]:
                files[f] = files.get(f, 0) + 1
    out = {"available": True, "shallow": shallow, "commits_scanned": scanned, "fix_commits": fixes, "files": dict(sorted(files.items()))}
    if shallow:
        out["note"] = "shallow clone: history is truncated, fix counts are lower bounds"
    return out


def score(classes, fixes):
    """Reading order only: distinct risk kinds weigh most, then hit volume (capped), then fix history."""
    stateful = sum(1 for c in classes if c in STATEFUL)
    return 3 * len(classes) + 2 * stateful + min(sum(classes.values()), 20) + 2 * min(fixes, 10)


def scan(root, exclude=(), history=500):
    root = Path(root).resolve()
    require(root.is_dir(), "survey root is not a directory: %s" % root)
    files = list_files(root, exclude)
    langs, tests, sources, skipped = {}, [], [], []
    existing, signals, texts = [], [], {}
    for rel in files:
        ext = rel.rsplit(".", 1)[-1].lower() if "." in rel.rsplit("/", 1)[-1] else ""
        lang = LANGUAGES.get(ext)
        formal = FORMAL_EXT.get(ext)
        yaml_like = ext in ("yaml", "yml")
        if not (lang or formal or yaml_like):
            continue
        text = _text(root / rel)
        if text is None:
            skipped.append(rel)
            continue
        test = is_test_file(rel)
        lines = text.splitlines()
        if lang:
            entry = langs.setdefault(lang, {"files": 0, "lines": 0, "test_files": 0})
            entry["files"] += 1
            entry["lines"] += len(lines)
            entry["test_files"] += 1 if test else 0
            (tests if test else sources).append(rel)
            texts[rel] = text
        if formal:
            existing.append({"kind": "formal-spec", "tool": formal, "file": rel, "line": 1, "text": lines[0].strip()[:200] if lines else ""})
        for n, line in enumerate(lines, 1):
            for kind, tool, rx in EXISTING:
                if (tool == "fvkit") != yaml_like:
                    continue
                if rx.search(line):
                    existing.append({"kind": kind, "tool": tool, "file": rel, "line": n, "text": line.strip()[:200]})
            if lang and not test:
                for cls, rx in SIGNAL_RES.items():
                    m = rx.search(line)
                    if m:
                        signals.append({"class": cls, "match": m.group(0)[:60], "file": rel, "line": n, "text": line.strip()[:200]})
    for i, e in enumerate(existing, 1):
        e["id"] = "X%d" % i
    for i, s in enumerate(signals, 1):
        s["id"] = "S%d" % i
    hist = _history(root, history) if history else {"available": False, "reason": "history disabled", "files": {}}
    test_texts = {t: texts[t] for t in tests}
    clusters = {}
    for s in signals:
        c = clusters.setdefault(s["file"], {"file": s["file"], "classes": {}, "signals": []})
        c["classes"][s["class"]] = c["classes"].get(s["class"], 0) + 1
        c["signals"].append(s["id"])
    out_clusters = []
    for f, c in clusters.items():
        stem = Path(f).stem
        word = re.compile(r"\b%s\b" % re.escape(stem)) if len(stem) >= 3 else None
        mentioned = sorted(t for t, body in test_texts.items() if word and word.search(body))
        fixes = hist["files"].get(f, 0)
        c.update({"classes": dict(sorted(c["classes"].items())), "fix_commits": fixes, "tests_mentioning": mentioned,
                  "score": score(c["classes"], fixes), "role": role_of(f)})
        out_clusters.append(c)
    out_clusters.sort(key=lambda c: (c["role"] != "product", -c["score"], c["file"]))
    for i, c in enumerate(out_clusters, 1):
        c["id"] = "C%d" % i
    head = _git(root, "rev-parse", "HEAD")
    dirty = _git(root, "status", "--porcelain", "--untracked-files=no", "--", ".")
    return {"schema_version": 1, "kind": KIND,
            "root": str(root),
            "git": {"head": head.strip() if head else None, "dirty": bool(dirty.strip()) if dirty is not None else None},
            "settings": {"exclude": list(exclude), "default_exclude": list(DEFAULT_EXCLUDE), "history": history,
                         "max_file_bytes": MAX_FILE_BYTES, "signal_patterns": SIGNALS},
            "inventory": {"languages": dict(sorted(langs.items())), "source_files": len(sources), "test_files": len(tests),
                          "skipped_binary_or_large": skipped},
            "existing_checks": existing, "signals": signals, "history": hist, "clusters": out_clusters,
            "tools": tool_availability(),
            "notes": ["signals and clusters order reading; they are not findings",
                      "tests_mentioning is a textual mention of the file's name, not coverage",
                      "role tooling (scripts, tools, examples, smoke, benchmarks) is listed after product code"]}


def _comparable(doc):
    return ([(s["class"], s["file"], s["line"], s["text"]) for s in doc["signals"]],
            [(e["kind"], e["tool"], e["file"], e["line"], e["text"]) for e in doc["existing_checks"]])


def load_survey(path):
    doc = load_document(path)
    require(isinstance(doc, dict) and doc.get("kind") == KIND and doc.get("schema_version") == 1, "%s is not an fv-survey" % path)
    return doc


# ---- the agent's targets ---------------------------------------------------------------------
# oss-verify .claude/skills/add-project/SKILL.md step 1 "Ask what 'correct' means", generalised from fuzz targets to
# any verification target: entry points, untrusted input, input size, expected outcomes, refused resources
# (allocation, but also time-outs and quota), and properties beyond "no crash".
CORRECTNESS = ("entry_points", "untrusted_input", "input_size", "expected_outcomes", "refused_resources", "properties")
CORRECTNESS_STATUS = ("observed", "answered", "not_applicable")
MAX_QUESTIONS = 5   # Spec Kit clarify quota, already used by the rules intake
RISK_CLASSES = tuple(SIGNALS) + ("other",)
ROUTES = ("stateful-model", "code-verifier", "property-lift", "function-contracts", "generated-inputs")
NEXT = {"stateful-model": "entrance B: fv init --entrance code-first, then G-1..G-8 (Specula brief first)",
        "code-verifier": "fv external --engine <tool>, keep the raw output",
        "property-lift": "fv props check, then fv props run (each check reached and seen failing)",
        "function-contracts": "fv contracts check (FM-Agent specs, probes re-run)",
        "generated-inputs": "fv props check / run on the generated-input tests (E1 at best)"}
TWO_SENTENCES = re.compile(r"[.!?]\s+\S|[。！？；]\s*\S")
ABBREVIATIONS = re.compile(r"(?i)\b(e\.g|i\.e|etc|vs|cf)\.")


def _ruled(q):
    return isinstance(q, dict) and isinstance(q.get("answer"), str) and q["answer"].strip() and isinstance(q.get("by"), str) and \
        q["by"].strip() and (q.get("signer_kind") == "human" or (q.get("signer_kind") == "delegated_agent" and
                                                                  isinstance(q.get("authorization"), str) and q["authorization"].strip()))


def _anchor_issues(anchors, root, where):
    issues = []
    if not isinstance(anchors, list) or not anchors:
        return ["%s: anchors [{file, quote}] point to code a reviewer can open (pstack: true to the code)" % where]
    for i, a in enumerate(anchors):
        if not (isinstance(a, dict) and isinstance(a.get("file"), str) and isinstance(a.get("quote"), str)):
            issues.append("%s.anchors[%d] must be {file, quote}" % (where, i))
            continue
        if len(a["quote"].strip()) < 8:
            issues.append("%s.anchors[%d]: quote at least a whole statement, not a token" % (where, i))
            continue
        p = (root / a["file"]).resolve()
        if root not in p.parents or not p.is_file():
            issues.append("%s.anchors[%d]: %s is not a file in the repository" % (where, i, a["file"]))
        elif a["quote"] not in p.read_text(encoding="utf-8", errors="replace"):
            issues.append("%s.anchors[%d]: the quote is not verbatim in %s" % (where, i, a["file"]))
    return issues


def _one_sentence(v):
    if not (isinstance(v, str) and v.strip() and "\n" not in v.strip() and len(v) <= 400):
        return False
    return not TWO_SENTENCES.search(ABBREVIATIONS.sub("", v.strip()))


def draft(survey_path, upstream=None, top=10):
    """A targets skeleton: every topic open, every top cluster and existing check waiting for a decision."""
    s = load_survey(survey_path)
    proc = []
    if upstream is not None:
        proc = [upstream.cite(p, f) for p, f in REQUIRED[TARGETS_KIND]]
    return {"schema_version": 1, "kind": TARGETS_KIND,
            "survey": {"path": str(survey_path), "digest": sha_bytes(Path(survey_path).read_bytes())},
            "procedure": proc,
            "correctness": {k: {"status": "TODO", "answer": "TODO"} for k in CORRECTNESS},
            "questions": [],
            "targets": [],
            "dismissed": [{"cluster": c["id"], "file": c["file"], "reason": "TODO"}
                          for c in [c for c in s["clusters"] if c.get("role", "product") == "product"][:top]] +
                         [{"existing_check": e["id"], "file": e["file"], "reason": "TODO"} for e in s["existing_checks"]
                          if e["kind"] in ("fuzz-target", "property-test")]}


def check_targets(targets_path, survey_path, root=None, upstream=None, top=10, rescan=True):
    s = load_survey(survey_path)
    doc = load_document(targets_path)
    require(isinstance(doc, dict) and doc.get("kind") == TARGETS_KIND and doc.get("schema_version") == 1,
            "%s is not an fv-targets document (schema_version 1)" % targets_path)
    _keys(doc, ["schema_version", "kind", "survey", "procedure", "correctness", "questions", "targets", "dismissed"], ["notes"], "targets")
    root = Path(root).resolve() if root else (Path(survey_path).resolve().parent / s["root"]).resolve()
    issues, stale = [], []
    if (doc["survey"] or {}).get("digest") != sha_bytes(Path(survey_path).read_bytes()):
        issues.append("targets were written against another survey (survey.digest)")
    issues += citations(doc["procedure"], TARGETS_KIND, upstream)
    if rescan:
        again = scan(root, s["settings"]["exclude"], history=0)
        if _comparable(again) != _comparable(s):
            stale.append("the repository changed since the survey: rerun `fv survey scan` (signals or existing checks differ)")
    questions = doc["questions"] or []
    qids = set()
    if len(questions) > MAX_QUESTIONS:
        issues.append("%d questions; ask at most %d, the ones the code cannot answer (pstack: ask only what you cannot observe)"
                      % (len(questions), MAX_QUESTIONS))
    for i, q in enumerate(questions):
        _keys(q, ["id", "topic", "question"], ["answer", "by", "signer_kind", "authorization"], "questions[%d]" % i)
        qids.add(q["id"])
        if q["topic"] not in CORRECTNESS:
            issues.append("question %s: topic must be one of %s" % (q["id"], ", ".join(CORRECTNESS)))
        if not str(q["question"]).strip().endswith(("?", "？")):
            issues.append("question %s must be a question ending with '?'" % q["id"])
        if not _ruled(q):
            issues.append("question %s: answered by the maintainer (human, or a delegated agent quoting the authorization); "
                          "oss-verify step 1: do not guess an answer" % q["id"])
    corr = doc["correctness"] or {}
    for k in sorted(set(corr) - set(CORRECTNESS)):
        issues.append("correctness.%s is not one of the six topics" % k)
    for k in CORRECTNESS:
        e = corr.get(k)
        where = "correctness.%s" % k
        if not (isinstance(e, dict) and e.get("status") in CORRECTNESS_STATUS and isinstance(e.get("answer"), str) and e["answer"].strip()
                and e["answer"].strip() != "TODO"):
            issues.append("%s needs status observed|answered|not_applicable and an answer (oss-verify step 1: ask what "
                          "'correct' means; do not guess)" % where)
            continue
        if e["status"] == "observed":
            issues += _anchor_issues(e.get("evidence"), root, where)
        elif e["status"] == "answered":
            q = next((x for x in questions if x["id"] == e.get("question")), None)
            if q is None or not _ruled(q):
                issues.append("%s: answered means a question id whose answer the maintainer gave" % where)
    signals = {x["id"]: x for x in s["signals"]}
    existing = {x["id"]: x for x in s["existing_checks"]}
    clusters = {x["id"]: x for x in s["clusters"]}
    tools = s["tools"]
    targets = doc["targets"] or []
    if not targets:
        issues.append("no target: name at least one promise, or say in notes why nothing in this repository needs more than tests")
    ids, ranks, cited, lifted = set(), [], set(), set()
    for i, t in enumerate(targets):
        _keys(t, ["id", "rank", "promise", "harm", "risk_class", "anchors", "why_tests_miss", "route", "tool", "scope"],
              ["signals", "source", "lifts", "why_first", "route_reason", "no_verifier_reason", "next", "notes"], "targets[%d]" % i)
        w = "target %s" % t["id"]
        if t["id"] in ids:
            issues.append("%s is duplicated" % w)
        ids.add(t["id"])
        ranks.append(t["rank"])
        for f in ("promise", "harm"):
            if not _one_sentence(t[f]):
                issues.append("%s: %s in one plain sentence (pstack: readable without the tool)" % (w, f))
        if t["risk_class"] not in RISK_CLASSES:
            issues.append("%s: risk_class must be one of %s" % (w, ", ".join(RISK_CLASSES)))
        issues += _anchor_issues(t["anchors"], root, w)
        sig = t.get("signals") or []
        unknown = [x for x in sig if x not in signals]
        if unknown:
            issues.append("%s cites signals that are not in the survey: %s" % (w, unknown))
        src = t.get("source")
        if not sig and not (isinstance(src, dict) and src.get("kind") == "user" and isinstance(src.get("quote"), str) and src["quote"].strip()):
            issues.append("%s: cite the survey signals it comes from, or source {kind: user, quote} when the user named it "
                          "(pstack: if the user named an area or a bug, start there)" % w)
        cited |= {signals[x]["file"] for x in sig if x in signals}
        if not (isinstance(t["why_tests_miss"], str) and t["why_tests_miss"].strip()):
            issues.append("%s: why_tests_miss — a good target is one tests rarely reach (pstack)" % w)
        route = t["route"]
        if route not in ROUTES:
            issues.append("%s: route must be one of %s" % (w, ", ".join(ROUTES)))
        tool = t["tool"] if isinstance(t["tool"], dict) else {}
        name = tool.get("name")
        if not (isinstance(tool.get("why"), str) and tool["why"].strip()):
            issues.append("%s: tool.why — tell the user why you chose it (pstack: let the question choose the tool)" % w)
        known = tools.get(name)
        if known is not None and bool(tool.get("available")) != known["available"]:
            issues.append("%s: tool.available says %s but the survey found %s %s" % (w, tool.get("available"), name,
                                                                                     "installed" if known["available"] else "missing"))
        if not (known or {}).get("available") and not (isinstance(tool.get("install"), str) and tool["install"].strip()):
            issues.append("%s: %s is not installed here; give tool.install (prefer a tool the developers can install and run)" % (w, name))
        anchor_langs = {LANGUAGES.get(str(a.get("file", "")).rsplit(".", 1)[-1].lower()) for a in t["anchors"] or [] if isinstance(a, dict)} - {None}
        if route == "stateful-model" and name not in MODEL_TOOLS:
            issues.append("%s: a stateful model is checked by %s" % (w, "/".join(MODEL_TOOLS)))
        if route == "code-verifier":
            if name not in CODE_VERIFIERS:
                issues.append("%s: code-verifier route needs one of %s" % (w, ", ".join(CODE_VERIFIERS)))
            elif anchor_langs and not anchor_langs & set(TOOLS[name][2]):
                issues.append("%s: %s verifies %s, but the anchored code is %s" % (w, name, "/".join(TOOLS[name][2]), "/".join(sorted(anchor_langs))))
        if route == "generated-inputs" and not (isinstance(t.get("no_verifier_reason"), str) and t["no_verifier_reason"].strip()):
            issues.append("%s: generated inputs instead of a verifier — say why no verifier runs here (pstack: if no verifier "
                          "runs on this language, say so)" % w)
        if route == "property-lift":
            bad = [x for x in t.get("lifts") or [] if x not in existing]
            if bad:
                issues.append("%s lifts checks that are not in the survey: %s" % (w, bad))
            lifted |= set(t.get("lifts") or [])
        if t["risk_class"] in STATEFUL and route not in ("stateful-model",) and not (isinstance(t.get("route_reason"), str) and t["route_reason"].strip()):
            issues.append("%s: a %s promise usually needs a model checker over a small model of the design (pstack: whether "
                          "events can happen in a bad order); give route_reason for %s" % (w, t["risk_class"], route))
        sc = t["scope"] if isinstance(t["scope"], dict) else {}
        if not (isinstance(sc.get("verified"), str) and sc["verified"].strip() and isinstance(sc.get("bounds"), str) and sc["bounds"].strip()
                and isinstance(sc.get("assumptions"), list) and isinstance(sc.get("not_covered"), list) and sc["not_covered"]):
            issues.append("%s: scope {verified, bounds, assumptions[], not_covered[≥1]} (pstack: honest about scope; oss-verify "
                          "what-gets-proven lists every exception)" % w)
        if t["rank"] == 1 and not (isinstance(t.get("why_first"), str) and t["why_first"].strip()):
            issues.append("%s: why_first — the strongest target in the repo, not the easiest to verify (pstack)" % w)
    if not all(isinstance(r, int) and not isinstance(r, bool) for r in ranks) or sorted(ranks) != list(range(1, len(ranks) + 1)):
        issues.append("ranks must be 1..%d without gaps or ties" % len(ranks))
    dismissed_c, dismissed_x = {}, {}
    for i, d in enumerate(doc["dismissed"] or []):
        _keys(d, ["reason"], ["cluster", "existing_check", "file"], "dismissed[%d]" % i)
        if not (isinstance(d["reason"], str) and d["reason"].strip() and d["reason"].strip() != "TODO"):
            issues.append("dismissed[%d] needs a reason" % i)
            continue
        if d.get("cluster"):
            dismissed_c[d["cluster"]] = d
        if d.get("existing_check"):
            dismissed_x[d["existing_check"]] = d
    uncovered = []
    for c in [c for c in s["clusters"] if c.get("role", "product") == "product"][:top]:
        if c["file"] not in cited and c["id"] not in dismissed_c:
            uncovered.append(c["id"])
            issues.append("cluster %s (%s, score %d) is neither cited by a target nor dismissed with a reason" % (c["id"], c["file"], c["score"]))
    for x in s["existing_checks"]:
        if x["kind"] in ("fuzz-target", "property-test") and x["id"] not in lifted and x["id"] not in dismissed_x:
            uncovered.append(x["id"])
            issues.append("existing %s %s (%s:%d) is neither lifted by a target nor dismissed (oss-verify step 3: start from the "
                          "project's existing fuzz targets)" % (x["kind"], x["id"], x["file"], x["line"]))
    for k in dismissed_c:
        if k not in clusters:
            issues.append("dismissed cluster %s is not in the survey" % k)
    verdict = "STALE" if stale else ("READY" if not issues else "NOT_READY")
    return {"verdict": verdict, "issues": stale + issues, "uncovered": uncovered,
            "targets": [{"id": t["id"], "rank": t["rank"], "route": t["route"], "tool": (t["tool"] or {}).get("name"),
                         "next": t.get("next") or NEXT.get(t["route"])} for t in sorted(targets, key=lambda t: t["rank"] if isinstance(t["rank"], int) else 0)],
            "digest": sha_bytes(Path(targets_path).read_bytes())}


__all__ = ["scan", "draft", "check_targets", "load_survey", "list_files", "is_test_file", "tool_availability"]
