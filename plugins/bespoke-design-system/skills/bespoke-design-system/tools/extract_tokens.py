#!/usr/bin/env python3
"""
extract_tokens.py — Programmatic A1 token extraction from DESIGN.md.

Strategy:
- Call scan_dialect.py to get sectioned content + dialect
- Run regex/markdown extractors per section type
- Output tokens/<system>.json with confidence_notes flagging fields that need LLM follow-up

Covers ~70-80% of typical token fields automatically; the LLM
(via scripts/extract-grammar.md A1 step) handles the rest.

Usage:
  python3 extract_tokens.py <path/to/DESIGN.md> [--system-name <name>] [--source <collection>]
    -> writes grammar/tokens/<system_name>.json (or stdout with --stdout)

  python3 extract_tokens.py --batch <path/to/source-design-systems/> [--only-pending]
    -> processes every system, writing each tokens/<name>.json
"""
import sys, os, re, json, argparse, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scan_dialect import scan as scan_design_md  # type: ignore


HEX_RE = re.compile(r'#[0-9a-fA-F]{3,8}\b')
RGBA_RE = re.compile(r'rgba?\([^)]+\)')
HSLA_RE = re.compile(r'hsla?\([^)]+\)')
PX_RE = re.compile(r'(\d+(?:\.\d+)?)\s*px\b', re.IGNORECASE)
PT_RE = re.compile(r'(\d+(?:\.\d+)?)\s*pt\b', re.IGNORECASE)
REM_RE = re.compile(r'(\d+(?:\.\d+)?)\s*rem\b', re.IGNORECASE)
MS_RE = re.compile(r'(\d+(?:\.\d+)?)\s*ms\b', re.IGNORECASE)
WEIGHT_RE = re.compile(r'\b(weight|font-weight)\s*[:=]?\s*(\d{3})\b', re.IGNORECASE)
WEIGHT_LIST_RE = re.compile(r'\b(\d{3})(?:\s*,\s*(\d{3}))+\b')
PERCENT_RE = re.compile(r'(\d+(?:\.\d+)?)\s*%')


def extract_role_color_pairs(text):
    """Find labeled color tokens. Three patterns supported:
       Pattern 1: '- **Primary:** `#FF5701`'   (Dialect B style)
       Pattern 2: 'Background (#08090a)'       (less common)
       Pattern 3: '- **Marketing Black** (`#010102` / `#08090a`)'   (Dialect A prose style)
    Returns dict {role_label: first_color_value}.
    """
    result = {}
    # Pattern 1: **Label:** value  OR  **Label** value (label may include trailing colon)
    for m in re.finditer(
        r'\*\*([A-Za-z][\w &/\-:]+?)\*\*[:\s]*[`"]?(' +
        HEX_RE.pattern + r'|' + RGBA_RE.pattern + r'|' + HSLA_RE.pattern + r')[`"]?',
        text
    ):
        role = m.group(1).strip().rstrip(':').strip().lower().replace(' ', '_')
        if role not in result:
            result[role] = m.group(2)

    # Pattern 3: **Bold Label** (`#hex` / `#hex2`) — Dialect A prose style
    for m in re.finditer(
        r'\*\*([A-Za-z][\w &/\-:]+?)\*\*\s*\(\s*[`"]?(' +
        HEX_RE.pattern + r'|' + RGBA_RE.pattern + r'|' + HSLA_RE.pattern + r')[`"]?',
        text
    ):
        role = m.group(1).strip().rstrip(':').strip().lower().replace(' ', '_')
        if role not in result:
            result[role] = m.group(2)

    # Pattern 2: 'Label (#hex)' bare — Label must be 1-2 capitalized words at line start or after punct
    for m in re.finditer(
        r'(?:^|[\.\n>:\(])\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\s*\((' +
        HEX_RE.pattern + r')\)',
        text, re.MULTILINE
    ):
        role = m.group(1).strip().lower().replace(' ', '_')
        # Skip role names that are obvious verbs/imperatives
        if role in ('favor', 'use', 'keep', 'apply', 'avoid', 'reserve', 'see', 'note', 'see_also', 'continue'):
            continue
        if role not in result:
            result[role] = m.group(2)
    return result


def extract_unique_hexes(text):
    return list(dict.fromkeys(m.group(0) for m in HEX_RE.finditer(text)))


def extract_color(section_text):
    """Extract color palette from a Color section."""
    if not section_text:
        return None
    role_pairs = extract_role_color_pairs(section_text)
    hexes = extract_unique_hexes(section_text)
    rgbas = list(dict.fromkeys(m.group(0) for m in RGBA_RE.finditer(section_text)))
    hslas = list(dict.fromkeys(m.group(0) for m in HSLA_RE.finditer(section_text)))

    return {
        'role_color_pairs': role_pairs,
        'all_hex_colors': hexes,
        'all_rgba_colors': rgbas[:20],
        'all_hsla_colors': hslas[:20],
        'hex_count': len(hexes),
        '_extraction_method': 'regex_role_pairs + hex_enum',
        '_confidence': 'high' if role_pairs else ('medium' if hexes else 'low'),
    }


# Common font families - tells us what a "family name" looks like.
KNOWN_FONT_HINTS = [
    'Inter', 'Geist', 'Roboto', 'Helvetica', 'Arial', 'Times', 'Georgia',
    'Mono', 'Sans', 'Serif', 'Display', 'Variable', 'Playfair',
    'Berkeley', 'Source', 'IBM Plex', 'JetBrains', 'Fira', 'SF Pro',
    'Apple', 'system-ui', 'Segoe', 'Cormorant', 'Lora', 'Merriweather',
    'Open Sans', 'Lato', 'Poppins', 'Montserrat', 'Nunito', 'Raleway',
    'Noto', 'Work Sans', 'Manrope', 'DM Sans', 'Plus Jakarta', 'Outfit',
    'Space Grotesk', 'Karla', 'Rubik', 'Quicksand', 'Spectral',
]


def extract_font_families(text):
    """Find font family declarations."""
    families = []
    # Pattern A: '**Primary:** Inter Variable' or '**Mono:** Berkeley Mono'
    for m in re.finditer(
        r'\*\*(Primary|Body|Display|Heading|Mono|Code|Serif|Sans|Family)[\w\s&/\-]*\*\*[:\s]*[`"]?([A-Z][\w\s\-]+?)[`"]?(?=[,;\n.]|$)',
        text
    ):
        role = m.group(1).strip().lower()
        family = m.group(2).strip()
        # Sanity: family should look like a font name
        if any(hint in family for hint in KNOWN_FONT_HINTS) or len(family) < 40:
            families.append({'role': role, 'family': family})

    # Pattern B: 'primary=Playfair Display, display=Playfair Display, mono=JetBrains Mono'
    for m in re.finditer(r'\b(primary|display|mono|body|heading|serif|sans)\s*=\s*([A-Z][\w\s\-]+?)(?=[,;\n]|$)', text, re.IGNORECASE):
        role = m.group(1).lower()
        family = m.group(2).strip()
        if any(hint in family for hint in KNOWN_FONT_HINTS):
            families.append({'role': role, 'family': family})

    return families


def extract_typography(section_text):
    if not section_text:
        return None
    families = extract_font_families(section_text)
    # Filter typography px values: realistic font sizes are 8-200, integer or .5
    raw_pxs = [float(m.group(1)) for m in PX_RE.finditer(section_text)]
    pxs = sorted(set(p for p in raw_pxs if 8 <= p <= 200))
    weights = sorted(set(int(m.group(2)) for m in WEIGHT_RE.finditer(section_text)))
    # Weight list pattern (e.g., 100, 200, 300)
    weight_lists = []
    for m in WEIGHT_LIST_RE.finditer(section_text):
        items = re.findall(r'\d{3}', m.group(0))
        weight_lists.append([int(w) for w in items])
    if weight_lists and not weights:
        weights = sorted(set(w for ws in weight_lists for w in ws))

    # Plain "Scale: 14/16/18/24" or "Scale: [12, 14, 16, ...]"
    scale_match = re.search(r'\*\*[Ss]cale:?\*\*[:\s]*([\[\d/,\s\.]+)', section_text)
    declared_scale = None
    if scale_match:
        nums = re.findall(r'\d+(?:\.\d+)?', scale_match.group(1))
        if nums:
            declared_scale = [float(n) for n in nums]

    return {
        'families': families,
        'all_px_values': pxs,
        'declared_scale_px': declared_scale,
        'weights_seen': weights,
        '_extraction_method': 'regex_family_role_pairs + px_enum + weight_enum',
        '_confidence': 'high' if (families and pxs) else ('medium' if (families or pxs) else 'low'),
    }


def extract_spacing(section_text):
    if not section_text:
        return None
    # Base unit: "Base unit: 8px", "8pt baseline grid", "Spacing scale: 8pt baseline grid"
    base = None
    for m in re.finditer(r'(?:base\s*unit|baseline\s*grid|base\s*=)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:px|pt)?', section_text, re.IGNORECASE):
        base = float(m.group(1))
        break
    if base is None:
        # "8pt baseline" or "8px baseline"
        m = re.search(r'(\d+(?:\.\d+)?)\s*(?:pt|px)\s*baseline', section_text, re.IGNORECASE)
        if m:
            base = float(m.group(1))
    if base is None:
        # Fallback: most common px value
        pxs = [float(m.group(1)) for m in PX_RE.finditer(section_text)]
        if pxs:
            from collections import Counter
            base = Counter(pxs).most_common(1)[0][0]

    # Scale: "[4, 8, 12, 16, ...]" or "8, 16, 24, 32" or "Spacing scale: 4 / 8 / 16 / 24"
    scale = None
    scale_match = re.search(r'\*\*[Ss]cale[\w\s]*:?\*\*[:\s]*([\[\d/,\s\.px]+)', section_text)
    if scale_match:
        nums = re.findall(r'\d+(?:\.\d+)?', scale_match.group(1))
        if nums:
            scale = sorted(set(float(n) for n in nums))

    # Filter spacing px values: realistic spacing is 1-200; exclude max-widths (>200) and pill radii (9999)
    raw_pxs = [float(m.group(1)) for m in PX_RE.finditer(section_text)]
    spacing_pxs = sorted(set(p for p in raw_pxs if 0 < p <= 200))
    return {
        'base_unit_px': base,
        'declared_scale': scale,
        'all_px_values': spacing_pxs,
        '_extraction_method': 'regex_base_unit + scale_enum',
        '_confidence': 'high' if (base and scale) else ('medium' if (base or scale) else 'low'),
    }


def extract_radius(section_text):
    if not section_text:
        return None
    pairs = {}
    # Pattern A: '**Label:** Npx' (dialect B style)
    for m in re.finditer(
        r'\*\*([\w\s]+?)\*\*[:\s]*[`"]?(\d+(?:\.\d+)?)\s*px[`"]?',
        section_text
    ):
        label = m.group(1).strip().lower()
        if 'radius' in label or any(k in label for k in ['micro','small','medium','large','pill','circle','card','panel','comfortable','standard']):
            pairs[label] = float(m.group(2))
    # Pattern B: '- Micro (2px):' or '- Comfortable (6px):' (dialect A prose-list)
    for m in re.finditer(
        r'^[\-*]\s*([A-Z][\w\s]+?)\s*\((\d+(?:\.\d+)?)\s*px\)',
        section_text, re.MULTILINE
    ):
        label = m.group(1).strip().lower()
        if any(k in label for k in ['micro','small','medium','large','pill','circle','card','panel','comfortable','standard','full','image','xl','xs','tab']):
            if label not in pairs:
                pairs[label] = float(m.group(2))
    # Spacing-realistic px values only (radius is typically 0-200)
    raw_pxs = [float(m.group(1)) for m in PX_RE.finditer(section_text)]
    pxs = sorted(set(p for p in raw_pxs if 0 < p <= 200))
    return {
        'role_radius_pairs': pairs,
        'all_px_values': pxs,
        '_extraction_method': 'regex_role_radius (patterns A and B)',
        '_confidence': 'high' if len(pairs) >= 3 else ('medium' if pairs else 'low'),
    }


def extract_motion(section_text):
    if not section_text:
        return None
    durations_ms = sorted(set(float(m.group(1)) for m in MS_RE.finditer(section_text)))
    easings = list(dict.fromkeys(m.group(0) for m in re.finditer(r'cubic-bezier\([^)]+\)', section_text)))
    keywords = list(dict.fromkeys(m.group(0).lower() for m in re.finditer(r'\b(ease|ease-in|ease-out|ease-in-out|linear|emphasized|spring)\b', section_text, re.IGNORECASE)))
    return {
        'durations_ms': durations_ms,
        'cubic_bezier_curves': easings,
        'easing_keywords': keywords,
        '_extraction_method': 'regex_ms + bezier + keyword',
        '_confidence': 'high' if durations_ms else 'low',
    }


def extract_breakpoints(section_text):
    if not section_text:
        return None
    # Look for explicit breakpoint table entries
    bps = {}
    for m in re.finditer(
        r'\b(Mobile(?:\s+Small)?|Tablet(?:\s+Small)?|Desktop(?:\s+Small)?|Large\s+Desktop|Wide|Phone|XS|SM|MD|LG|XL|XXL|2XL)\s*[:|]\s*[<>~]?\s*(\d+)\s*(?:px|–|-|to|\s)\s*(\d+)?\s*px?',
        section_text, re.IGNORECASE
    ):
        name = m.group(1).strip().lower().replace(' ', '_')
        lower = int(m.group(2))
        upper = int(m.group(3)) if m.group(3) else None
        bps[name] = {'min': lower, 'max': upper}
    return {
        'breakpoints_named': bps,
        '_extraction_method': 'regex_breakpoint_table',
        '_confidence': 'high' if bps else 'low',
    }


def extract_dos_donts(section_text):
    """Extract Do's and Don'ts as raw bullet lists for downstream Kansei tagging."""
    if not section_text:
        return None
    # Find "Do" and "Don't" subsection bodies
    dos = []
    donts = []
    # Try ### Do / ### Don't
    do_match = re.search(r'^###\s*Do\s*$\n(.+?)(?=^###|\Z)', section_text, re.MULTILINE | re.DOTALL)
    dont_match = re.search(r"^###\s*Don'?t\s*$\n(.+?)(?=^###|\Z)", section_text, re.MULTILINE | re.DOTALL)
    if do_match:
        dos = re.findall(r'^[\-*]\s*(.+?)$', do_match.group(1), re.MULTILINE)
    if dont_match:
        donts = re.findall(r'^[\-*]\s*(.+?)$', dont_match.group(1), re.MULTILINE)
    # If no headers found, treat entire body as flat bullets
    if not dos and not donts:
        bullets = re.findall(r'^[\-*]\s*(.+?)$', section_text, re.MULTILINE)
        # Heuristic: if a bullet starts with "Don't" or "Avoid", it's a don't
        for b in bullets:
            if re.match(r"^\s*(Don'?t|Avoid|Never|No\s)", b, re.IGNORECASE):
                donts.append(b)
            else:
                dos.append(b)
    return {
        'dos': dos,
        'donts': donts,
        '_extraction_method': 'subsection_bullet_parse',
        '_confidence': 'high' if (dos or donts) else 'low',
    }


def extract_tokens_full(scan_result, system_name=None, source=None):
    """Run all extractors against a scan_dialect result."""
    sections = scan_result.get('sections', {})
    out = {
        'system_name': system_name,
        'source': source,
        'extracted_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'dialect': scan_result.get('dialect'),
        'fingerprint_hash': scan_result.get('fingerprint_hash'),
        'extraction_method': 'programmatic_a1',
        'tool_version': '1.0.0',
    }

    if 'color' in sections:
        out['color'] = extract_color(sections['color'])
    if 'typography' in sections:
        out['typography'] = extract_typography(sections['typography'])
    if 'spacing' in sections:
        out['spacing'] = extract_spacing(sections['spacing'])
    elif 'layout' in sections:
        # Dialect A: spacing rules live inside Layout Principles
        out['spacing'] = extract_spacing(sections['layout'])
    if 'layout' in sections:
        out['layout'] = {
            '_extraction_method': 'kept_section_text_for_a3',
            '_confidence': 'low',
            '_section_size': len(sections['layout']),
        }
        # Try to extract radius scale from layout (dialect A often has radius here)
        out['radius'] = extract_radius(sections['layout'])
    if 'depth_elevation' in sections:
        # Just enumerate shadow/rgba expressions — full philosophy needs LLM
        text = sections['depth_elevation']
        out['depth_elevation'] = {
            'rgba_shadows': list(dict.fromkeys(m.group(0) for m in RGBA_RE.finditer(text)))[:30],
            'inset_shadows': re.findall(r'inset[^,;\n]+', text, re.IGNORECASE)[:10],
            '_extraction_method': 'regex_rgba_inset',
            '_confidence': 'medium',
        }
    if 'motion' in sections:
        out['motion'] = extract_motion(sections['motion'])
    if 'responsive' in sections:
        out['responsive'] = extract_breakpoints(sections['responsive'])
    elif 'layout' in sections:
        # Dialect B: breakpoints often inside Layout & Composition
        bp = extract_breakpoints(sections['layout'])
        if bp and bp.get('breakpoints_named'):
            out['responsive'] = bp
    if 'dos_donts' in sections:
        out['dos_donts'] = extract_dos_donts(sections['dos_donts'])
    elif 'anti_patterns' in sections:
        out['anti_patterns'] = extract_dos_donts(sections['anti_patterns'])
    if 'voice' in sections:
        # Voice is mostly prose - extract bulleted CTA-style examples
        text = sections['voice']
        cta_examples = re.findall(r'["\'""]([^"\'""\n]{2,40})["\'""]', text)
        out['voice'] = {
            'cta_or_phrase_examples': cta_examples[:20],
            'section_text_size': len(text),
            '_extraction_method': 'regex_quoted_phrase',
            '_confidence': 'low',
            '_needs_llm': 'tone_personality_archetype_inference',
        }

    # What sections did we have but didn't extract? They need LLM.
    handled = {'color','typography','spacing','layout','depth_elevation','motion','responsive','dos_donts','anti_patterns','voice','radius'}
    out['sections_present'] = list(sections.keys())
    out['sections_unhandled'] = [s for s in sections.keys() if s not in handled and s != 'visual_theme']
    out['sections_meta_for_llm'] = ['visual_theme','agent_guide']

    # Add LLM follow-up hints
    out['llm_followup_hints'] = []
    for k, v in out.items():
        if isinstance(v, dict) and v.get('_confidence') == 'low':
            out['llm_followup_hints'].append(f'{k} extraction has low confidence — recommend LLM review')

    return out


def process_one(design_md_path, system_name=None, source='open-design'):
    if system_name is None:
        # infer from parent dir
        system_name = os.path.basename(os.path.dirname(os.path.abspath(design_md_path)))
    scan = scan_design_md(design_md_path)
    return extract_tokens_full(scan, system_name=system_name, source=source)


def update_registry_state(system_name, state, registry_path=None):
    """v1.5.0 Issue 1 fix: Sync source-registry.json extraction_state with disk truth
    after each extraction. Valid states: 'pending' / 'tokens_only' / 'rationale_only' / 'rules' / 'full'.
    Computes the correct state from on-disk grammar/tokens/, /rationale/, /rules/ presence."""
    if registry_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        registry_path = os.path.normpath(
            os.path.join(here, '..', 'grammar', 'meta', 'source-registry.json'))
    if not os.path.isfile(registry_path):
        return  # no registry yet, nothing to sync
    try:
        with open(registry_path) as f:
            registry = json.load(f)
        systems = registry.setdefault('systems', {})
        entry = systems.get(system_name)
        if entry is None:
            return  # system not registered, skip
        entry['extraction_state'] = state
        entry['last_extracted_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # don't break extraction if registry write fails


def derive_extraction_state(system_name, grammar_root=None):
    """Look at disk: tokens/<name>.json exists? rationale/<name>.md? rules/<name>.yaml?
    Return canonical state for source-registry."""
    if grammar_root is None:
        here = os.path.dirname(os.path.abspath(__file__))
        grammar_root = os.path.normpath(os.path.join(here, '..', 'grammar'))
    has_tokens = os.path.isfile(os.path.join(grammar_root, 'tokens', f'{system_name}.json'))
    has_rationale = os.path.isfile(os.path.join(grammar_root, 'rationale', f'{system_name}.md'))
    has_rules = os.path.isfile(os.path.join(grammar_root, 'rules', f'{system_name}.yaml'))
    if has_tokens and has_rationale and has_rules:
        return 'full'
    if has_rationale and has_rules:
        return 'rules'
    if has_rationale:
        return 'rationale_only'
    if has_tokens:
        return 'tokens_only'
    return 'pending'


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('path', help='Path to DESIGN.md or (with --batch) source-design-systems/ root')
    p.add_argument('--batch', action='store_true')
    p.add_argument('--system-name', help='Override system name (single mode)')
    p.add_argument('--source', default='open-design', help='Source collection tag')
    p.add_argument('--output-dir', help='Output directory for tokens/<name>.json (default: ../grammar/tokens relative to this script)')
    p.add_argument('--stdout', action='store_true', help='Print to stdout instead of writing file')
    p.add_argument('--only-pending', action='store_true', help='Batch mode: skip systems whose token file already exists')
    args = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    default_out = os.path.normpath(os.path.join(here, '..', 'grammar', 'tokens'))
    out_dir = args.output_dir or default_out
    os.makedirs(out_dir, exist_ok=True)

    if args.batch:
        root = args.path
        results = {}
        for entry in sorted(os.listdir(root)):
            design_md = os.path.join(root, entry, 'DESIGN.md')
            if not os.path.isfile(design_md):
                continue
            out_file = os.path.join(out_dir, f'{entry}.json')
            if args.only_pending and os.path.isfile(out_file):
                continue
            try:
                tokens = process_one(design_md, system_name=entry, source=args.source)
                with open(out_file, 'w') as f:
                    json.dump(tokens, f, indent=2, ensure_ascii=False)
                results[entry] = {'ok': True, 'sections': len(tokens.get('sections_present', []))}
                # v1.5.0 Issue 1: sync registry extraction_state
                update_registry_state(entry, derive_extraction_state(entry))
            except Exception as e:
                results[entry] = {'ok': False, 'error': str(e)}
        print(json.dumps({
            'processed': len(results),
            'ok_count': sum(1 for r in results.values() if r.get('ok')),
            'fail_count': sum(1 for r in results.values() if not r.get('ok')),
            'failures': {k: v for k, v in results.items() if not v.get('ok')},
        }, indent=2))
    else:
        tokens = process_one(args.path, system_name=args.system_name, source=args.source)
        if args.stdout:
            json.dump(tokens, sys.stdout, indent=2, ensure_ascii=False)
            print()
        else:
            name = tokens['system_name']
            out_file = os.path.join(out_dir, f'{name}.json')
            with open(out_file, 'w') as f:
                json.dump(tokens, f, indent=2, ensure_ascii=False)
            print(f'Wrote {out_file}')
            # v1.5.0 Issue 1: sync registry extraction_state
            update_registry_state(name, derive_extraction_state(name))


if __name__ == '__main__':
    main()
