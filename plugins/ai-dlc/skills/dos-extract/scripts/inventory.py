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

Code channel (class/type/struct declarations):
  TypeScript/JavaScript, Python, Go, Rust, Java/Kotlin.

Structured-data channel (YAML/JSON declarations — on by default, `--no-structured`
to turn off): repositories whose objects live in schemas and config rather than in
class declarations (plugin repos, infra repos, schema-first services) score ZERO
nouns on the code channel alone. Four extraction modes, each tagged in the report:
  - `$defs`            JSON Schema `$defs` / `definitions` keys  (strongest signal)
  - `schema-property`  keys under a JSON Schema `properties` mapping
  - `enum-value`       members of an `enum` list — a closed domain vocabulary
  - `kind-value`       string values of a discriminator key (`kind` / `type` / `category`)
  - `key`              plain mapping keys down to `--key-depth` (default 1)
Tooling manifests (package.json, tsconfig*.json, lock files, …) are skipped, and
purely structural keys (`type`, `required`, `items`, …) are pruned.

Exclusions: `--exclude` takes comma-separated *names*, not globs. A file is skipped
when ANY segment of its path equals one of those names, at any depth — `--exclude
fixtures` drops `a/fixtures/b.py` and `deep/nested/fixtures/c.py` alike. Dot-prefixed
directories are always skipped, whether or not they are listed.
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
# Structured-data channel (YAML / JSON)
# -----------------------------------------------------------------------------

STRUCTURED_EXTENSIONS = {".yaml", ".yml", ".json"}

# Tooling manifests: their keys are build vocabulary, never domain vocabulary.
MANIFEST_BASENAMES = {
    "package.json", "package-lock.json", "npm-shrinkwrap.json", "bun.lock",
    "jsconfig.json", "composer.json", "composer.lock", "deno.json", "deno.jsonc",
    "renovate.json", "angular.json", "nx.json", "lerna.json", "turbo.json",
    "tslint.json", "biome.json", "vercel.json", "now.json", "manifest.json",
}
MANIFEST_PREFIXES = ("tsconfig",)          # tsconfig.json, tsconfig.build.json, …
MANIFEST_MARKERS = (".eslintrc", ".prettierrc", ".babelrc", ".markdownlint")

# Keys that describe the SHAPE of the document rather than name a thing in it.
STRUCTURAL_KEYS = {
    # JSON Schema / OpenAPI plumbing
    "$schema", "$id", "$ref", "$defs", "$comment", "definitions", "properties",
    "items", "required", "type", "title", "description", "enum", "default",
    "format", "additionalproperties", "minimum", "maximum", "minlength",
    "maxlength", "pattern", "oneof", "anyof", "allof", "not", "const",
    "examples", "example", "nullable", "readonly", "deprecated",
    # generic document furniture
    "version", "id", "name", "notes", "note", "comment", "comments", "value",
    "values", "key", "keys", "kind", "label", "summary", "url", "uri", "path",
    "paths", "date", "author", "tags", "meta", "metadata", "config", "settings",
    "options", "env", "args", "cmd", "command", "script", "scripts",
    "dependencies", "devdependencies", "category",
    # CI/workflow furniture
    "on", "jobs", "steps", "runs-on", "uses", "with", "if", "else", "then",
    "needs", "matrix", "include", "exclude", "strategy",
}

# A string value under one of these keys names a variety of the thing being declared.
DISCRIMINATOR_KEYS = {"kind", "type", "category"}

# Function words and prose furniture that turn up as plain mapping keys but name
# nothing. Applied ONLY to the weak `key` mode: a JSON-Schema property or an enum
# member actually called `status` IS a declaration, whereas a `status:` key buried
# in a report file is furniture.
STOP_WORDS = {
    "a", "an", "the", "and", "or", "not", "of", "to", "from", "in", "on", "at",
    "by", "for", "with", "as", "is", "are", "was", "were", "be", "been", "it",
    "this", "that", "these", "those", "all", "any", "some", "none", "true",
    "false", "yes", "no", "ok", "na", "tbd",
    "why", "how", "what", "who", "whom", "whose", "where", "which",
    "got", "expected", "actual", "before", "after", "first", "last", "next",
    "text", "content", "body", "line", "lines", "count", "total", "sum",
    "status", "state", "result", "results", "output", "input", "data", "item",
    "file", "files", "dir", "reason", "message", "msg", "detail", "details",
    "sha", "ref", "refs",
}

# Modes strong enough that a term is a declaration by construction.
DECLARATION_MODES = ("$defs", "schema-property", "enum-value", "kind-value")

# `type: string` in a JSON Schema declares a primitive, not a domain variety.
JSON_PRIMITIVES = {"string", "integer", "number", "boolean", "array", "object",
                   "null", "timestamp", "date", "datetime"}

# A noun candidate has to look like an identifier, not a sentence or a path.
NOUN_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.\-]{1,39}$")


def is_manifest(path: Path) -> bool:
    base = path.name.lower()
    if base in MANIFEST_BASENAMES or base.startswith(MANIFEST_PREFIXES):
        return True
    return any(m in base for m in MANIFEST_MARKERS)


def is_noun_candidate(token: str, mode: str = "key") -> bool:
    """Identifier-shaped, not structural furniture, not a bare number/date.

    The `key` mode additionally drops STOP_WORDS; declaration modes do not, because
    a property or enum member genuinely named `status` is a declaration.
    """
    if not NOUN_KEY_RE.match(token):
        return False
    if token.lower() in STRUCTURAL_KEYS:
        return False
    if mode not in DECLARATION_MODES and token.lower() in STOP_WORDS:
        return False
    return True


def walk_structured(node, out: list[tuple[str, str]], parent_key: str | None = None,
                    depth: int = 0, key_depth: int = 3) -> None:
    """Collect (term, mode) pairs from a parsed YAML/JSON document.

    A list is not a naming level, so walking into list members does not spend depth;
    only nested mappings do. `$defs` / `properties` / `enum` children are always
    collected — they are declarations by construction, whatever depth they sit at.
    """
    if isinstance(node, dict):
        for raw_key, value in node.items():
            k = str(raw_key)
            pk = (parent_key or "").lower()
            if pk in ("$defs", "definitions"):
                mode = "$defs"
            elif pk == "properties":
                mode = "schema-property"
            else:
                mode = "key"
            if mode != "key" or depth <= key_depth:
                if is_noun_candidate(k, mode):
                    out.append((k, mode))
            if k.lower() in DISCRIMINATOR_KEYS and isinstance(value, str):
                if value.lower() not in JSON_PRIMITIVES and is_noun_candidate(value, "kind-value"):
                    out.append((value, "kind-value"))
            if k.lower() == "enum" and isinstance(value, list):
                for member in value:
                    if isinstance(member, str) and is_noun_candidate(member, "enum-value"):
                        out.append((member, "enum-value"))
            walk_structured(value, out, k, depth + 1, key_depth)
    elif isinstance(node, list):
        for member in node:
            walk_structured(member, out, parent_key, depth, key_depth)


def parse_structured(path: Path, yaml_mod):
    """Return the parsed document, or None if it cannot be read as YAML/JSON."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    if path.suffix.lower() == ".json":
        import json as _json
        try:
            return _json.loads(text)
        except Exception:
            return None
    if yaml_mod is None:
        return None
    try:
        return yaml_mod.safe_load(text)
    except Exception:
        return None


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
    """A path is excluded when ANY of its segments equals an excluded NAME.

    Names, not globs, and matched at any depth: `--exclude fixtures` drops both
    `a/fixtures/b.py` and `deep/nested/fixtures/c.py`.
    """
    parts = set(path.parts)
    return bool(parts & excludes)


def iter_source_files(root: Path, excludes: set[str], wanted: set[str]) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune in place: excluded names, and every dot-directory (always).
        dirnames[:] = [d for d in dirnames if d not in excludes and not d.startswith(".")]
        for fn in filenames:
            full = Path(dirpath) / fn
            if full.suffix.lower() in wanted and not is_excluded(full, excludes):
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
    noun_modes: dict[str, set[str]] | None = None,
    structured_stats: dict[str, int] | None = None,
) -> str:
    noun_modes = noun_modes or {}
    structured_stats = structured_stats or {}
    lines: list[str] = []
    lines.append(f"# Inventory — {project_root.name}")
    lines.append("")
    lines.append(f"- Project root: `{project_root}`")
    lines.append(f"- Files scanned: {files_scanned}")
    lines.append(f"  - code files: {structured_stats.get('code_files', files_scanned)}")
    lines.append(f"  - structured files (YAML/JSON): {structured_stats.get('structured_files', 0)}"
                 f" ({structured_stats.get('structured_unparsed', 0)} unparsable,"
                 f" {structured_stats.get('structured_manifests', 0)} tooling manifests skipped)")
    lines.append(f"- Distinct nouns: {len(nouns)}")
    lines.append(f"  - from code declarations: {sum(1 for n in nouns if 'code' in noun_modes.get(n, {'code'}))}")
    lines.append(f"  - from structured data: {sum(1 for n in nouns if noun_modes.get(n, set()) - {'code'})}")
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
    lines.append("Source tag: `[code]` = a class/type/struct declaration; `[$defs]`,")
    lines.append("`[schema-property]`, `[enum-value]`, `[kind-value]`, `[key]` = the")
    lines.append("structured-data channel. A term carrying two different tags was")
    lines.append("declared twice — strong signal.")
    lines.append("")

    if not nouns:
        lines.append("_No nouns found. If this repository declares its objects in YAML/JSON")
        lines.append("schemas or in prose rather than in class declarations, the docs channel")
        lines.append("(`assets/docs_extraction_prompt.md` + `scripts/count_terms.py`) is the")
        lines.append("primary source here, and this emptiness is the finding — record it in")
        lines.append("`decisions.md` rather than treating the inventory as complete._")
        lines.append("")

    def render(name: str, count: int) -> str:
        ui_flag = " `[ui?]`" if looks_like_ui(name) else ""
        modes = sorted(noun_modes.get(name, {"code"}))
        mode_str = " " + " ".join(f"`[{m}]`" for m in modes)
        locs = noun_locations.get(name, [])[:3]
        loc_str = ", ".join(f"`{loc}`" for loc in locs) if locs else "—"
        return f"- **{name}** ({count}){ui_flag}{mode_str} — {loc_str}"

    def is_declaration(name: str) -> bool:
        modes = noun_modes.get(name, {"code"})
        return "code" in modes or bool(modes & set(DECLARATION_MODES))

    declared = [(n, c) for n, c in nouns.most_common() if is_declaration(n)]
    keys_only = [(n, c) for n, c in nouns.most_common() if not is_declaration(n)]

    if keys_only:
        lines.append(f"### Declared ({len(declared)}) — class/type declarations, `$defs`, "
                     "schema properties, enum members")
        lines.append("")
        lines.append("Classification starts here. A term in this table was *declared*, not merely used.")
        lines.append("")
    for name, count in declared:
        lines.append(render(name, count))

    if keys_only:
        lines.append("")
        lines.append(f"### Plain mapping keys ({len(keys_only)}) — weak signal, read second")
        lines.append("")
        lines.append("These are YAML/JSON keys that are not declarations. They are here for")
        lines.append("completeness; most are document furniture. Narrow with `--key-depth 0`")
        lines.append("or `--exclude eval,fixtures,reports` if they swamp the table.")
        lines.append("")
        for name, count in keys_only:
            lines.append(render(name, count))

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
                        help="Comma-separated directory/file NAMES (not globs) to exclude. "
                             "A path is skipped when ANY of its segments equals one of these "
                             "names, at any depth: `--exclude fixtures` drops a/fixtures/b.py "
                             "and deep/nested/fixtures/c.py alike. Dot-directories are always "
                             "skipped, listed or not.")
    parser.add_argument("--no-structured", action="store_true",
                        help="Skip the YAML/JSON channel (code declarations only). The "
                             "structured channel is on by default because schema-first and "
                             "plugin repositories score zero nouns without it.")
    parser.add_argument("--key-depth", type=int, default=1,
                        help="Plain mapping keys are collected down to this nesting depth "
                             "(default 1). $defs / properties / enum / discriminator values "
                             "are collected at any depth.")
    args = parser.parse_args()

    if not args.project_root.exists():
        print(f"Error: {args.project_root} does not exist", file=sys.stderr)
        return 1

    excludes = DEFAULT_EXCLUDES | {x.strip() for x in args.exclude.split(",") if x.strip()}

    nouns: Counter[str] = Counter()
    verbs: Counter[str] = Counter()
    noun_locations: dict[str, list[str]] = defaultdict(list)
    verb_locations: dict[str, list[str]] = defaultdict(list)
    noun_modes: dict[str, set[str]] = defaultdict(set)
    pruned: dict[str, list[tuple[str, str]]] = {
        "Implementation suffixes": [],
        "Framework primitives": [],
        "CRUD verbs": [],
    }

    pruned_seen: set[str] = set()
    files_scanned = 0
    stats = {"code_files": 0, "structured_files": 0,
             "structured_unparsed": 0, "structured_manifests": 0}

    yaml_mod = None
    if not args.no_structured:
        try:
            import yaml as yaml_mod  # type: ignore
        except ImportError:
            yaml_mod = None
            print("NOTE: PyYAML not installed — the structured channel reads JSON only.",
                  file=sys.stderr)

    def record_noun(name: str, mode: str, rel: str) -> bool:
        """Apply the shared prune filters, then count. True if it was counted."""
        suf = has_impl_suffix(name)
        if suf:
            if name not in pruned_seen:
                pruned["Implementation suffixes"].append(
                    (name, f"suffix `{suf}`; operates on `{name[:-len(suf)]}`"))
                pruned_seen.add(name)
            return False
        if name in FRAMEWORK_TERMS:
            if name not in pruned_seen:
                pruned["Framework primitives"].append(
                    (name, "common framework/generic name"))
                pruned_seen.add(name)
            return False
        nouns[name] += 1
        noun_modes[name].add(mode)
        if rel not in noun_locations[name] and len(noun_locations[name]) < 3:
            noun_locations[name].append(rel)
        return True

    wanted = set(ALL_EXTENSIONS)
    if not args.no_structured:
        wanted |= STRUCTURED_EXTENSIONS

    for src_file in iter_source_files(args.project_root, excludes, wanted):
        rel = str(src_file.relative_to(args.project_root))
        lang = detect_language(src_file)

        if lang is None:
            # structured-data channel
            if args.no_structured or src_file.suffix.lower() not in STRUCTURED_EXTENSIONS:
                continue
            files_scanned += 1
            if is_manifest(src_file):
                stats["structured_manifests"] += 1
                continue
            doc = parse_structured(src_file, yaml_mod)
            if doc is None:
                stats["structured_unparsed"] += 1
                continue
            stats["structured_files"] += 1
            found: list[tuple[str, str]] = []
            walk_structured(doc, found, None, 0, args.key_depth)
            for term, mode in found:
                record_noun(term, mode, rel)
            continue

        files_scanned += 1
        stats["code_files"] += 1
        try:
            content = src_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        ns, vs = extract_terms(content, lang)

        for n in ns:
            record_noun(n, "code", rel)

        for v in vs:
            if v in CRUD_VERBS:
                if v not in pruned_seen:
                    pruned["CRUD verbs"].append((v, "generic CRUD/lifecycle verb"))
                    pruned_seen.add(v)
                continue
            verbs[v] += 1
            if len(verb_locations[v]) < 3:
                verb_locations[v].append(rel)

    report = format_report(
        nouns, verbs, noun_locations, verb_locations, pruned,
        args.project_root, files_scanned, noun_modes, stats,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")

    print(f"Wrote inventory to {args.output}")
    print(f"  Files scanned: {files_scanned} "
          f"(code {stats['code_files']}, structured {stats['structured_files']})")
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
        if args.no_structured:
            print(
                "  --no-structured was passed: if this repo declares its objects in\n"
                "  YAML/JSON, re-run without it.",
                file=sys.stderr,
            )
        elif stats["structured_files"] == 0 and stats["code_files"] == 0:
            print(
                "  Nothing was parsed at all — check --exclude (it matches path SEGMENT\n"
                "  NAMES at any depth, not globs) and the project root.",
                file=sys.stderr,
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
