#!/usr/bin/env python3
"""
scan_dialect.py — Identify DESIGN.md dialect + slice into 9 sections.

Used by:
  - extract_tokens.py (A1 phase)
  - rebuild_graph.py (verifying section coverage)
  - register_systems.py (initial classification)

Usage:
  python3 scan_dialect.py <path/to/DESIGN.md>
    -> JSON to stdout: {"dialect": "A|B|C|A-variant|B-variant|other",
                        "section_count": int,
                        "sections": {<internal_slug>: <markdown_text>},
                        "raw_section_titles": [...],
                        "fingerprint_hash": "<sha256>"}

  python3 scan_dialect.py --batch <path/to/source-design-systems/>
    -> JSON object {<system_name>: <result>} for all subdirectories with DESIGN.md
"""
import sys, os, re, json, hashlib, argparse

# Two dominant OD dialects (90% of corpus)
DIALECT_A_TITLES = [
    'Visual Theme & Atmosphere','Color Palette & Roles','Typography Rules',
    'Component Stylings','Layout Principles','Depth & Elevation',
    "Do's and Don'ts",'Responsive Behavior','Agent Prompt Guide'
]
DIALECT_B_TITLES = [
    'Visual Theme & Atmosphere','Color','Typography','Spacing & Grid',
    'Layout & Composition','Components','Motion & Interaction',
    'Voice & Brand','Anti-patterns'
]
# 6-section minimal (some recent additions)
DIALECT_C_TITLES = [
    'Visual Theme & Atmosphere','Color Palette & Roles','Typography Rules',
    'Component Stylings','Spacing & Layout','Motion'
]

# Map each dialect's section titles to internal slugs.
# Internal slugs are what rule.section uses regardless of source dialect.
DIALECT_A_MAP = {
    'Visual Theme & Atmosphere': 'visual_theme',     # meta
    'Color Palette & Roles': 'color',
    'Typography Rules': 'typography',
    'Component Stylings': 'components',
    'Layout Principles': 'layout',                   # absorbs spacing in dialect A
    'Depth & Elevation': 'depth_elevation',
    "Do's and Don'ts": 'dos_donts',                  # meta (anti-pattern derived)
    'Responsive Behavior': 'responsive',             # meta (layout derived)
    'Agent Prompt Guide': 'agent_guide',             # meta (synthetic)
    # Variants seen in cluster scan
    'Layout': 'layout',
    'Depth': 'depth_elevation',
    'Interaction & Motion': 'motion',
    'Dark Mode': 'dark_mode',
    'Accessibility & States': 'accessibility',
    'Responsive Behavior (Extended)': 'responsive',
    'Attribution': 'attribution',
}
DIALECT_B_MAP = {
    'Visual Theme & Atmosphere': 'visual_theme',     # meta
    'Color': 'color',
    'Typography': 'typography',
    'Spacing & Grid': 'spacing',
    'Layout & Composition': 'layout',
    'Components': 'components',
    'Motion & Interaction': 'motion',
    'Voice & Brand': 'voice',
    'Anti-patterns': 'anti_patterns',                # rule-bearing (anti_patterns rule slug)
    # Variants
    'Motion': 'motion',
}
DIALECT_C_MAP = {
    'Visual Theme & Atmosphere': 'visual_theme',
    'Color Palette & Roles': 'color',
    'Typography Rules': 'typography',
    'Component Stylings': 'components',
    'Spacing & Layout': 'layout',
    'Motion': 'motion',
}

# Universal fallback — match any title with these keyword sets
KEYWORD_SLUGS = [
    (['visual theme', 'atmosphere', 'overview', 'aesthetic'], 'visual_theme'),
    (['color', 'palette'], 'color'),
    (['typography', 'type', 'font'], 'typography'),
    (['spacing', 'grid', 'rhythm'], 'spacing'),
    (['layout', 'composition'], 'layout'),
    (['component', 'styling', 'pattern'], 'components'),
    (['motion', 'interaction', 'animation'], 'motion'),
    (['depth', 'elevation', 'shadow'], 'depth_elevation'),
    (['voice', 'brand', 'tone'], 'voice'),
    (['anti-pattern', "don't", 'do and', 'avoid'], 'anti_patterns'),
    (['responsive', 'breakpoint'], 'responsive'),
    (['agent', 'prompt', 'guide'], 'agent_guide'),
    (['dark mode', 'dark theme'], 'dark_mode'),
    (['accessibility', 'a11y', 'wcag'], 'accessibility'),
]


def normalize_title(title):
    """Strip leading numbering and trailing punctuation."""
    title = re.sub(r'^\d+\.\s*', '', title).strip()
    return title.rstrip('.: ')


def classify_dialect(titles):
    """Return one of: A, B, C-6section, A-variant, B-variant, other."""
    titles_t = tuple(titles[:9])
    if titles_t == tuple(DIALECT_A_TITLES):
        return 'A'
    if titles_t == tuple(DIALECT_B_TITLES):
        return 'B'
    if titles_t == tuple(DIALECT_C_TITLES) or (len(titles) == 6 and titles_t[:6] == tuple(DIALECT_C_TITLES)):
        return 'C-6section'

    # variant detection: dialect A signature with 1-2 sections swapped
    a_overlap = sum(1 for t in DIALECT_A_TITLES if t in titles)
    b_overlap = sum(1 for t in DIALECT_B_TITLES if t in titles)
    if a_overlap >= 6 and a_overlap > b_overlap:
        return 'A-variant'
    if b_overlap >= 6 and b_overlap > a_overlap:
        return 'B-variant'
    return 'other'


def title_to_slug(title, dialect):
    """Map a section title to an internal slug, dialect-aware."""
    if dialect.startswith('A'):
        m = DIALECT_A_MAP
    elif dialect.startswith('B'):
        m = DIALECT_B_MAP
    elif dialect.startswith('C'):
        m = DIALECT_C_MAP
    else:
        m = {}

    if title in m:
        return m[title]

    # fallback: keyword match
    title_l = title.lower()
    for keywords, slug in KEYWORD_SLUGS:
        if any(k in title_l for k in keywords):
            return slug
    # ultimate fallback: kebab-case title
    return re.sub(r'[^a-z0-9]+', '_', title_l).strip('_')


def slice_sections(content):
    """Split markdown content into top-level (## ...) sections.
    Returns list of (raw_title, body_text) tuples in order."""
    # Find all '## ' headers and their positions
    headers = list(re.finditer(r'^## (.+)$', content, re.MULTILINE))
    sections = []
    for i, h in enumerate(headers):
        title = normalize_title(h.group(1))
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
        body = content[start:end].strip('\n')
        sections.append((title, body))
    return sections


def scan(path):
    """Scan a single DESIGN.md file."""
    with open(path) as f:
        content = f.read()

    sections_raw = slice_sections(content)
    titles = [t for t, _ in sections_raw]
    dialect = classify_dialect(titles)

    sections_by_slug = {}
    for title, body in sections_raw:
        slug = title_to_slug(title, dialect)
        # if duplicate slug (e.g. multiple "responsive" variants), append _N
        base_slug = slug
        suffix = 1
        while slug in sections_by_slug:
            slug = f'{base_slug}_{suffix}'
            suffix += 1
        sections_by_slug[slug] = body

    fingerprint = hashlib.sha256(content.encode('utf-8')).hexdigest()

    return {
        'dialect': dialect,
        'section_count': len(sections_raw),
        'sections': sections_by_slug,
        'raw_section_titles': titles,
        'fingerprint_hash': fingerprint,
        'size_bytes': len(content),
    }


def scan_batch(root):
    """Scan every <root>/<system>/DESIGN.md."""
    results = {}
    for entry in sorted(os.listdir(root)):
        path = os.path.join(root, entry, 'DESIGN.md')
        if os.path.isfile(path):
            try:
                results[entry] = scan(path)
            except Exception as e:
                results[entry] = {'error': str(e)}
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('path', help='Path to a DESIGN.md file or (with --batch) a directory')
    p.add_argument('--batch', action='store_true', help='Treat path as a directory of <system>/DESIGN.md')
    p.add_argument('--include-bodies', action='store_true', help='Include section bodies in batch mode (default: omit for size)')
    args = p.parse_args()

    if args.batch:
        result = scan_batch(args.path)
        if not args.include_bodies:
            for r in result.values():
                if isinstance(r, dict) and 'sections' in r:
                    r['sections'] = list(r['sections'].keys())
    else:
        result = scan(args.path)

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == '__main__':
    main()
