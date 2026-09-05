#!/usr/bin/env python3
"""
inventory.py — the mechanical scan the dos-extract engine can do on its own.

Scans a code repository and produces frequency tables of:
  - Business nouns (class names, type names, table names, API path segments)
  - Business verbs (function/method names, API verbs)

Output is a Markdown file: the raw noun/verb frequency tables that the
classification work consumes as its starting material.

This script is intentionally conservative — it stops short of any semantic
judgment:
  - It does NOT classify (object vs. UI vs. impl vs. rule — that's a human/LLM call).
  - It does NOT merge synonyms (that judgment comes later).
  - It DOES filter framework noise heuristically, with a `## Pruned` section
    showing what was removed for transparency.

Supports: TypeScript/JavaScript, Python, Go, Rust, Java/Kotlin.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

# -----------------------------------------------------------------------------
# Language configuration
# -----------------------------------------------------------------------------

LANGUAGE_EXTENSIONS = {
    "typescript": {".ts", ".tsx"},
    "javascript": {".js", ".jsx", ".mjs", ".cjs"},
    "python": {".py"},
    "go": {".go"},
    "rust": {".rs"},
    "java": {".java"},
    "kotlin": {".kt", ".kts"},
}

ALL_EXTENSIONS = {ext for exts in LANGUAGE_EXTENSIONS.values() for ext in exts}

# Patterns to extract noun-shaped identifiers (PascalCase) and verb-shaped
# function/method names (camelCase or snake_case starting with verb).
#
# Each pattern returns the captured identifier in group 1.
NOUN_PATTERNS = {
    "typescript": [
        # class Foo, interface Foo, type Foo, enum Foo
        re.compile(r"\b(?:class|interface|type|enum)\s+([A-Z][A-Za-z0-9_]*)"),
        # React component: const Foo = (props) => or function Foo(...)
        re.compile(r"\b(?:const|function)\s+([A-Z][A-Za-z0-9_]*)"),
    ],
    "javascript": [
        re.compile(r"\bclass\s+([A-Z][A-Za-z0-9_]*)"),
        re.compile(r"\b(?:const|function)\s+([A-Z][A-Za-z0-9_]*)"),
    ],
    "python": [
        re.compile(r"^class\s+([A-Z][A-Za-z0-9_]*)", re.MULTILINE),
        # Pydantic / dataclass / NamedTuple — picked up by `class` rule
    ],
    "go": [
        re.compile(r"\btype\s+([A-Z][A-Za-z0-9_]*)\s+(?:struct|interface)"),
    ],
    "rust": [
        re.compile(r"\b(?:struct|enum|trait)\s+([A-Z][A-Za-z0-9_]*)"),
    ],
    "java": [
        re.compile(r"\b(?:class|interface|enum|record)\s+([A-Z][A-Za-z0-9_]*)"),
    ],
    "kotlin": [
        re.compile(r"\b(?:class|interface|object|data class)\s+([A-Z][A-Za-z0-9_]*)"),
    ],
}

VERB_PATTERNS = {
    "typescript": [
        # function fooBar() / async function fooBar()
        re.compile(r"\b(?:async\s+)?function\s+([a-z][A-Za-z0-9_]*)"),
        # method shorthand: fooBar(args) {
        re.compile(r"^\s*(?:async\s+)?([a-z][A-Za-z0-9_]*)\s*\([^)]*\)\s*[:{]", re.MULTILINE),
    ],
    "javascript": [
        re.compile(r"\b(?:async\s+)?function\s+([a-z][A-Za-z0-9_]*)"),
    ],
    "python": [
        re.compile(r"^\s*(?:async\s+)?def\s+([a-z][a-z0-9_]*)", re.MULTILINE),
    ],
    "go": [
        re.compile(r"\bfunc\s+(?:\([^)]+\)\s+)?([a-zA-Z][A-Za-z0-9_]*)"),
    ],
    "rust": [
        re.compile(r"\bfn\s+([a-z][a-z0-9_]*)"),
    ],
    "java": [
        re.compile(r"\b(?:public|private|protected|static)\s+(?:[A-Za-z<>,\s]+\s+)?([a-z][A-Za-z0-9_]*)\s*\("),
    ],
    "kotlin": [
        re.compile(r"\bfun\s+([a-z][A-Za-z0-9_]*)"),
    ],
}

# -----------------------------------------------------------------------------
# Noise filters
# -----------------------------------------------------------------------------

# Implementation suffixes — stripped from inventory and recorded as "pruned".
# These are the terms Judgment 1 step 2 would catch; doing it mechanically here
# saves the user time when classifying.
IMPL_SUFFIXES = {
    "Repository", "Repo", "Service", "Manager", "Handler", "Controller",
    "Provider", "Factory", "Builder", "Helper", "Util", "Utils", "Utility",
    "DAO", "DTO", "VO", "Adapter", "Resolver", "Mapper", "Serializer",
    "Wrapper", "Proxy", "Decorator", "Middleware", "Interceptor",
    "Validator", "Filter", "Listener", "Observer", "Subscriber", "Publisher",
}

# Framework/library terms that should never enter business vocabulary.
FRAMEWORK_TERMS = {
    # React / web
    "App", "Page", "Layout", "Provider", "Context", "Component", "Element",
    "Props", "State", "Ref", "Fragment", "Portal", "Suspense", "ErrorBoundary",
    # Common test
    "Test", "Spec", "Fixture", "Mock", "Stub", "Setup", "Teardown",
    # CRUD generics — rarely meaningful as objects
    "Request", "Response", "Result", "Error", "Exception", "Config", "Options",
    "Settings", "Params", "Query", "Body", "Header", "Cookie", "Session",
}

# Common CRUD verbs that appear everywhere and rarely express domain semantics.
CRUD_VERBS = {
    "get", "set", "fetch", "load", "save", "store", "find", "create", "update",
    "delete", "remove", "add", "insert", "list", "search", "query", "render",
    "format", "parse", "serialize", "deserialize", "validate", "transform",
    "convert", "init", "setup", "configure", "build", "compile", "execute",
    "run", "start", "stop", "pause", "resume", "open", "close", "begin", "end",
    "handle", "process", "dispatch", "subscribe", "unsubscribe", "emit",
    "log", "debug", "trace", "warn", "error",
    # React-specific
    "use", "useState", "useEffect", "useMemo", "useCallback", "useRef",
}

# UI primitive names that should be flagged as likely UI already in the scan.
# Classification makes the final call; this just helps the user see the candidates.
UI_HINTS = {
    "Card", "Modal", "Dialog", "Drawer", "Toast", "Snackbar", "Banner",
    "Panel", "Tab", "Tabs", "Tooltip", "Popover", "Dropdown", "Menu",
    "Bubble", "Pill", "Chip", "Badge", "Avatar", "Spinner", "Skeleton",
    "Button", "Input", "Form", "Field", "Checkbox", "Radio", "Toggle",
    "Slider", "Stepper", "Accordion", "Carousel", "Grid", "Stack", "Box",
    "Container", "Section", "Header", "Footer", "Sidebar", "Navbar",
    "Layout", "View", "Screen", "Page",
}

DEFAULT_EXCLUDES = {
    "node_modules", "dist", "build", ".next", "out", "target", "vendor",
    "__pycache__", ".venv", "venv", ".git", ".idea", ".vscode",
    "coverage", ".cache", ".turbo",
}


# -----------------------------------------------------------------------------
# Scanning
# -----------------------------------------------------------------------------

def detect_language(path: Path) -> str | None:
    ext = path.suffix.lower()
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        if ext in exts:
            return lang
    return None


def is_excluded(path: Path, excludes: set[str]) -> bool:
    parts = set(path.parts)
    return bool(parts & excludes)


def iter_source_files(root: Path, excludes: set[str]) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories in place
        dirnames[:] = [d for d in dirnames if d not in excludes and not d.startswith(".")
                       or d in {"."}]
        for fn in filenames:
            full = Path(dirpath) / fn
            if full.suffix.lower() in ALL_EXTENSIONS and not is_excluded(full, excludes):
                yield full


def extract_terms(content: str, lang: str) -> tuple[list[str], list[str]]:
    nouns: list[str] = []
    verbs: list[str] = []
    for pat in NOUN_PATTERNS.get(lang, []):
        nouns.extend(pat.findall(content))
    for pat in VERB_PATTERNS.get(lang, []):
        verbs.extend(pat.findall(content))
    return nouns, verbs


def has_impl_suffix(name: str) -> str | None:
    for suf in IMPL_SUFFIXES:
        if name.endswith(suf) and name != suf:
            return suf
    return None


def looks_like_ui(name: str) -> bool:
    """
    Conservative UI heuristic: a term is flagged as `[ui?]` if it ENDS in a UI
    primitive (TopicCard, MessageBubble, PageLayout) or IS a UI primitive
    (Modal, Card). Judgment 1 makes the final call during classification.
    """
    if name in UI_HINTS:
        return True
    return any(name.endswith(hint) and name != hint for hint in UI_HINTS)


# -----------------------------------------------------------------------------
# Output
# -----------------------------------------------------------------------------

def format_report(
    nouns: Counter[str],
    verbs: Counter[str],
    noun_locations: dict[str, list[str]],
    verb_locations: dict[str, list[str]],
    pruned: dict[str, list[tuple[str, str]]],
    project_root: Path,
    files_scanned: int,
) -> str:
    lines: list[str] = []
    lines.append(f"# Inventory — {project_root.name}")
    lines.append("")
    lines.append(f"- Project root: `{project_root}`")
    lines.append(f"- Files scanned: {files_scanned}")
    lines.append(f"- Distinct nouns: {len(nouns)}")
    lines.append(f"- Distinct verbs: {len(verbs)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Nouns (frequency)")
    lines.append("")
    lines.append("Each noun is shown with its frequency and up to 3 example file paths.")
    lines.append("Terms ending in implementation suffixes (Repository, Service, etc.) and")
    lines.append("framework primitives have been moved to the `Pruned` section below.")
    lines.append("")
    lines.append("UI-hint flag: `[ui?]` indicates the term may be a UI primitive —")
    lines.append("classification must confirm using Judgment 1.")
    lines.append("")

    for name, count in nouns.most_common():
        ui_flag = " `[ui?]`" if looks_like_ui(name) else ""
        locs = noun_locations.get(name, [])[:3]
        loc_str = ", ".join(f"`{loc}`" for loc in locs) if locs else "—"
        lines.append(f"- **{name}** ({count}){ui_flag} — {loc_str}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Verbs (frequency)")
    lines.append("")
    lines.append("Verbs that connect business nouns are candidates for `relationships`.")
    lines.append("Generic CRUD verbs (`get`, `create`, `update`, `delete`, ...) have been")
    lines.append("moved to `Pruned` since they rarely express domain meaning.")
    lines.append("")

    for name, count in verbs.most_common():
        locs = verb_locations.get(name, [])[:3]
        loc_str = ", ".join(f"`{loc}`" for loc in locs) if locs else "—"
        lines.append(f"- **{name}** ({count}) — {loc_str}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Pruned (framework noise)")
    lines.append("")
    lines.append("Terms removed from the active inventory. Listed for transparency so the")
    lines.append("user can object if a term was pruned that should be a domain object.")
    lines.append("")

    for category, items in pruned.items():
        if not items:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for name, reason in items[:50]:  # cap to keep file readable
            lines.append(f"- `{name}` — {reason}")
        if len(items) > 50:
            lines.append(f"- _(...{len(items) - 50} more)_")
        lines.append("")

    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path, help="Path to project root")
    parser.add_argument("--output", "-o", type=Path, required=True,
                        help="Output Markdown file path")
    parser.add_argument("--exclude", default="",
                        help="Comma-separated extra directory names to exclude")
    args = parser.parse_args()

    if not args.project_root.exists():
        print(f"Error: {args.project_root} does not exist", file=sys.stderr)
        return 1

    excludes = DEFAULT_EXCLUDES | {x.strip() for x in args.exclude.split(",") if x.strip()}

    nouns: Counter[str] = Counter()
    verbs: Counter[str] = Counter()
    noun_locations: dict[str, list[str]] = defaultdict(list)
    verb_locations: dict[str, list[str]] = defaultdict(list)
    pruned: dict[str, list[tuple[str, str]]] = {
        "Implementation suffixes": [],
        "Framework primitives": [],
        "CRUD verbs": [],
    }

    pruned_seen: set[str] = set()
    files_scanned = 0

    for src_file in iter_source_files(args.project_root, excludes):
        files_scanned += 1
        try:
            content = src_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lang = detect_language(src_file)
        if lang is None:
            continue
        ns, vs = extract_terms(content, lang)
        rel = src_file.relative_to(args.project_root)

        for n in ns:
            suf = has_impl_suffix(n)
            if suf:
                if n not in pruned_seen:
                    pruned["Implementation suffixes"].append(
                        (n, f"suffix `{suf}`; operates on `{n[:-len(suf)]}`"))
                    pruned_seen.add(n)
                continue
            if n in FRAMEWORK_TERMS:
                if n not in pruned_seen:
                    pruned["Framework primitives"].append(
                        (n, "common framework/generic name"))
                    pruned_seen.add(n)
                continue
            nouns[n] += 1
            if len(noun_locations[n]) < 3:
                noun_locations[n].append(str(rel))

        for v in vs:
            if v in CRUD_VERBS:
                if v not in pruned_seen:
                    pruned["CRUD verbs"].append((v, "generic CRUD/lifecycle verb"))
                    pruned_seen.add(v)
                continue
            verbs[v] += 1
            if len(verb_locations[v]) < 3:
                verb_locations[v].append(str(rel))

    report = format_report(
        nouns, verbs, noun_locations, verb_locations, pruned,
        args.project_root, files_scanned,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")

    print(f"Wrote inventory to {args.output}")
    print(f"  Files scanned: {files_scanned}")
    print(f"  Distinct nouns: {len(nouns)}")
    print(f"  Distinct verbs: {len(verbs)}")
    print(f"  Pruned: {sum(len(v) for v in pruned.values())} terms")

    if len(nouns) < 10:
        print(
            "\nWARNING: fewer than 10 distinct nouns found.\n"
            "  This may indicate a small project or a language parser miss.\n"
            "  Consider expanding the input scope before moving on to classification.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
