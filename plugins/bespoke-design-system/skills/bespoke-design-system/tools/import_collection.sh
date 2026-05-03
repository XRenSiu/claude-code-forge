#!/usr/bin/env bash
# import_collection.sh — Bulk import DESIGN.md from a remote git collection.
#
# Supports three preset collections (--source open-design / --source awesome-design-md)
# or a custom GitHub repo + glob pattern.
#
# Pipeline (after fetch):
#   1. Copy/curl DESIGN.md files into source-design-systems/<name>/
#   2. Call register_systems.py to update source-registry.json (dialects + hashes)
#   3. Call extract_tokens.py --batch (programmatic A1 across all newly imported)
#   4. Suggest next step (LLM A2/A3 + rebuild_graph)
#
# Usage:
#   ./import_collection.sh --source open-design
#   ./import_collection.sh --source awesome-design-md
#   ./import_collection.sh --custom-repo https://github.com/owner/repo --pattern 'design-systems/*/DESIGN.md'
#   ./import_collection.sh --source open-design --only-new   # skip existing
#   ./import_collection.sh --source open-design --systems linear-app,vercel,stripe   # subset

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
SRC_ROOT="$SKILL_ROOT/source-design-systems"

SOURCE_PRESET=""
CUSTOM_REPO=""
PATTERN=""
ONLY_NEW=false
SYSTEMS_FILTER=""
PARALLEL=8

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SOURCE_PRESET="$2"; shift 2 ;;
    --custom-repo) CUSTOM_REPO="$2"; shift 2 ;;
    --pattern) PATTERN="$2"; shift 2 ;;
    --only-new) ONLY_NEW=true; shift ;;
    --systems) SYSTEMS_FILTER="$2"; shift 2 ;;
    --parallel) PARALLEL="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

# Resolve source preset
case "$SOURCE_PRESET" in
  open-design)
    REPO="nexu-io/open-design"
    BASE_PATH="design-systems"
    ;;
  awesome-design-md)
    REPO="VoltAgent/awesome-design-md"
    BASE_PATH=""
    ;;
  "")
    if [[ -z "$CUSTOM_REPO" ]]; then
      echo "ERROR: must specify --source <preset> or --custom-repo <url>" >&2
      exit 2
    fi
    REPO="${CUSTOM_REPO#https://github.com/}"
    REPO="${REPO%.git}"
    BASE_PATH=""
    ;;
  *)
    echo "ERROR: unknown source preset: $SOURCE_PRESET" >&2
    exit 2
    ;;
esac

if ! command -v gh &> /dev/null; then
  echo "ERROR: 'gh' CLI required. Install from https://cli.github.com" >&2
  exit 2
fi

echo "Importing from: $REPO ($BASE_PATH)"
echo "Skill root:     $SKILL_ROOT"

# Step 1: enumerate available systems
TMP_LIST="$(mktemp)"
trap "rm -f $TMP_LIST" EXIT

if [[ -n "$BASE_PATH" ]]; then
  gh api "repos/$REPO/contents/$BASE_PATH" --jq '.[] | select(.type == "dir") | .name' > "$TMP_LIST"
else
  # awesome-design-md is flat; would need different glob. For now warn.
  echo "ERROR: non-OD presets not yet implemented (need glob pattern)" >&2
  exit 2
fi

echo "Found $(wc -l < $TMP_LIST | tr -d ' ') systems in remote."

# Apply filter
if [[ -n "$SYSTEMS_FILTER" ]]; then
  IFS=',' read -ra REQUESTED <<< "$SYSTEMS_FILTER"
  : > "${TMP_LIST}.filtered"
  for s in "${REQUESTED[@]}"; do
    grep -F -x "$s" "$TMP_LIST" >> "${TMP_LIST}.filtered" || echo "WARN: $s not in remote list" >&2
  done
  mv "${TMP_LIST}.filtered" "$TMP_LIST"
  echo "After --systems filter: $(wc -l < $TMP_LIST | tr -d ' ') systems."
fi

if $ONLY_NEW; then
  : > "${TMP_LIST}.new"
  while read -r s; do
    if [[ ! -f "$SRC_ROOT/$s/DESIGN.md" ]]; then
      echo "$s" >> "${TMP_LIST}.new"
    fi
  done < "$TMP_LIST"
  mv "${TMP_LIST}.new" "$TMP_LIST"
  echo "After --only-new filter: $(wc -l < $TMP_LIST | tr -d ' ') systems."
fi

if [[ ! -s "$TMP_LIST" ]]; then
  echo "Nothing to import."
  exit 0
fi

mkdir -p "$SRC_ROOT"

# Step 2: parallel curl
echo "Fetching DESIGN.md files (parallel=$PARALLEL)..."

while read -r system; do
  printf '%s\n' "$system"
done < "$TMP_LIST" | xargs -I {} -P "$PARALLEL" sh -c '
  s="{}"
  mkdir -p "'"$SRC_ROOT"'/$s"
  if curl -sLf "https://raw.githubusercontent.com/'"$REPO"'/main/'"$BASE_PATH"'/$s/DESIGN.md" -o "'"$SRC_ROOT"'/$s/DESIGN.md.tmp"; then
    mv "'"$SRC_ROOT"'/$s/DESIGN.md.tmp" "'"$SRC_ROOT"'/$s/DESIGN.md"
    echo "  ✓ $s"
  else
    rm -rf "'"$SRC_ROOT"'/$s"
    echo "  ✗ $s (fetch failed)" >&2
  fi
'

# Step 3: register
echo
echo "Registering imported systems..."
python3 "$SCRIPT_DIR/register_systems.py" --source-collection "$SOURCE_PRESET" --skill-root "$SKILL_ROOT" --repo "$REPO" --base-path "$BASE_PATH"

# Step 4: A1 extraction
echo
echo "Running programmatic A1 extraction..."
python3 "$SCRIPT_DIR/extract_tokens.py" --batch "$SRC_ROOT" --only-pending

# Step 5: state report
echo
python3 "$SCRIPT_DIR/check_state.py"

echo
echo "Import complete. Next steps:"
echo "  1. Review token extraction quality:  ls $SKILL_ROOT/grammar/tokens/"
echo "  2. Run LLM-driven A2/A3 on pending systems (Claude reads scripts/extract-grammar.md)"
echo "  3. Once rules exist for new systems, run: python3 tools/rebuild_graph.py"
