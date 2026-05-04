#!/usr/bin/env python3
"""
prepare_a3_context.py — Assemble A3 (rule extraction) context for an LLM.

This tool does NOT make any design judgment. It only gathers and arranges the
inputs an LLM needs in one place, so the LLM doesn't have to grep across the
filesystem during A3.

What it gathers:
  1. tokens.json key fields for the system (already extracted by A1)
  2. DESIGN.md section slices (already segmented by scan_dialect.py)
  3. references/kansei-theory.md controlled vocabulary (the kansei words A3 may use)
  4. references/brand-archetypes.md 12-archetype list (the archetypes A3 may pick from)
  5. Format examples from existing grammar/rationale/<peer>.md and grammar/rules/<peer>.yaml
     (a similar peer system, picked by `--peer` or auto-detected by category)

What the LLM still does (NOT replaced by this tool):
  - Pick which rationale decisions to extract (semantic judgment)
  - Choose kansei words from the vocabulary (semantic match)
  - Decide brand_archetypes for the system overall AND per-rule (judgment)
  - Write trade_off / intent / avoid (design narrative)
  - Determine confidence values (calibration)
  - Identify known_conflicts with existing rules

Usage:
  python3 prepare_a3_context.py <system_name> [--peer <peer_system>] [--output <path>]
  # Writes a single markdown file at <path> (default: ./a3-context-<system>.md)
  # The LLM then reads that one file as A3 context.

Example:
  python3 prepare_a3_context.py figma --peer linear-app
"""
from __future__ import annotations
import sys
import os
import json
import argparse
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.normpath(os.path.join(HERE, '..'))


def _read_text(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return f.read()


def _load_json(path: str) -> dict | None:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _design_md_sections(system_name: str) -> dict[str, str]:
    """Re-run scan_dialect to get section slices. Already used by A1; we just read its output."""
    design_md_path = os.path.join(SKILL_ROOT, 'source-design-systems', system_name, 'DESIGN.md')
    if not os.path.isfile(design_md_path):
        return {}
    # v1.7.1: only insert tools dir into sys.path once. Repeated calls used to
    # accumulate duplicate entries.
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    try:
        from scan_dialect import scan as scan_design_md  # type: ignore
        scan = scan_design_md(design_md_path)
        return scan.get('sections', {})
    except Exception:
        return {}


def _kansei_vocab() -> str:
    """Pull the controlled vocabulary table from references/kansei-theory.md."""
    path = os.path.join(SKILL_ROOT, 'references', 'kansei-theory.md')
    text = _read_text(path) or ''
    # Extract the "Controlled Vocabulary" section if present
    m = re.search(r'(?:^|\n)## Controlled Vocabulary\b.*?(?=\n## |\Z)', text, re.DOTALL)
    if m:
        return m.group(0).strip()
    # Fallback: include the whole file (LLM can scan)
    return text[:6000] if text else '(kansei-theory.md not found)'


def _archetype_list() -> str:
    """Pull the 12-archetype list from references/brand-archetypes.md."""
    path = os.path.join(SKILL_ROOT, 'references', 'brand-archetypes.md')
    text = _read_text(path) or ''
    m = re.search(r'## 12 原型.*?(?=\n## |\Z)', text, re.DOTALL)
    if m:
        return m.group(0).strip()
    return text[:5000] if text else '(brand-archetypes.md not found)'


def _detect_category(system_name: str) -> str | None:
    """Read DESIGN.md `> Category: <X>` line for the system, return normalized category."""
    design_md = os.path.join(SKILL_ROOT, 'source-design-systems', system_name, 'DESIGN.md')
    if not os.path.isfile(design_md):
        return None
    try:
        with open(design_md) as f:
            text = f.read(2000)
    except Exception:
        return None
    m = re.search(r'^>\s*Category:\s*([^\n]+)', text, re.MULTILINE)
    if m:
        return m.group(1).strip().lower()
    return None


def _detect_archetypes_for_system(system_name: str) -> set[str]:
    """If the system already has rules.yaml, harvest the most common
    brand_archetypes. Else infer from category. Used to find semantic peer."""
    rules_path = os.path.join(SKILL_ROOT, 'grammar', 'rules', f'{system_name}.yaml')
    if os.path.isfile(rules_path):
        try:
            import yaml
            d = yaml.safe_load(open(rules_path))
            if d and 'rules' in d:
                from collections import Counter
                archs = Counter()
                for r in d['rules']:
                    for a in (r.get('preconditions',{}) or {}).get('brand_archetypes',[]) or []:
                        archs[a] += 1
                return set(a for a,_ in archs.most_common(3))
        except Exception:
            pass
    return set()


def _peer_examples(peer_system: str | None, this_system: str) -> tuple[str, str, str]:
    """Find a peer system's rationale + rules to use as format examples (NOT content templates).

    v1.7.0 F4 fix: peer selection is now semantic (same category + closest archetype overlap),
    not alphabetical. Falls back to alphabetical only when no semantic match exists."""
    selection_reason = ''
    if peer_system is None:
        # Discover candidates with extracted rules
        rules_dir = os.path.join(SKILL_ROOT, 'grammar', 'rules')
        candidates = [f.replace('.yaml', '') for f in sorted(os.listdir(rules_dir))
                      if f.endswith('.yaml') and not f.startswith('_') and not f.startswith('.')]
        candidates = [c for c in candidates if c != this_system]
        if candidates:
            # Try semantic match: same DESIGN.md Category
            this_category = _detect_category(this_system)
            same_cat = [c for c in candidates if _detect_category(c) == this_category] if this_category else []
            if same_cat:
                # Among same-category, prefer the one with closest archetype overlap if known
                this_archs = _detect_archetypes_for_system(this_system)
                if this_archs:
                    scored = sorted(same_cat,
                                     key=lambda c: -len(this_archs & _detect_archetypes_for_system(c)))
                    peer_system = scored[0]
                    selection_reason = f'auto-selected by category=`{this_category}` + archetype overlap'
                else:
                    peer_system = same_cat[0]
                    selection_reason = f'auto-selected by category=`{this_category}`'
            else:
                peer_system = candidates[0]
                selection_reason = '(fallback: alphabetical — no category/archetype match found)'
    else:
        selection_reason = '(user-specified via --peer)'
    if not peer_system:
        return '(no peer found — start from blank)', '(no peer found — start from blank)', '(none)'
    rationale_path = os.path.join(SKILL_ROOT, 'grammar', 'rationale', f'{peer_system}.md')
    rules_path = os.path.join(SKILL_ROOT, 'grammar', 'rules', f'{peer_system}.yaml')
    return (_read_text(rationale_path) or '(missing)',
            _read_text(rules_path) or '(missing)',
            f'{peer_system} ({selection_reason})')


def _summarize_tokens(tokens: dict) -> str:
    """Render a compact view of tokens.json keys/values an LLM can scan."""
    if not tokens:
        return '(tokens.json not found)'
    out = []
    interesting = ['color', 'typography', 'spacing', 'radius', 'depth_elevation',
                   'motion', 'responsive', 'voice', 'dos_donts', 'anti_patterns']
    for k in interesting:
        if k not in tokens:
            continue
        v = tokens[k]
        if isinstance(v, dict):
            keys = list(v.keys())
            sample = {kk: v[kk] for kk in keys[:6]}
            out.append(f'### tokens.{k}\n```json\n{json.dumps(sample, indent=2, ensure_ascii=False)[:600]}\n```')
        else:
            out.append(f'### tokens.{k}\n```\n{json.dumps(v, ensure_ascii=False)[:300]}\n```')
    return '\n\n'.join(out)


def _existing_rule_id_prefix(this_system: str) -> str:
    """Show the LLM what rule_id prefix to use, and existing rule_id sequences in this system (if any)."""
    rules_path = os.path.join(SKILL_ROOT, 'grammar', 'rules', f'{this_system}.yaml')
    if not os.path.isfile(rules_path):
        return f'rule_id format: `{this_system}-<section>-<keyword>-<NNN>` (e.g., `{this_system}-color-dark-canvas-001`). No existing rules — start from 001.'
    text = _read_text(rules_path) or ''
    ids = re.findall(rf'rule_id:\s*({re.escape(this_system)}-[\w-]+)', text)
    return f'rule_id format: `{this_system}-<section>-<keyword>-<NNN>`. Existing rule_ids in this system:\n  ' + '\n  '.join(ids[:20])


def assemble_context(system_name: str, peer_system: str | None = None) -> str:
    """Build the full A3 context markdown."""
    tokens_path = os.path.join(SKILL_ROOT, 'grammar', 'tokens', f'{system_name}.json')
    rationale_path = os.path.join(SKILL_ROOT, 'grammar', 'rationale', f'{system_name}.md')
    tokens = _load_json(tokens_path)
    rationale_existing = _read_text(rationale_path) or '(rationale.md not yet written — write A2 first or in tandem with A3)'
    sections = _design_md_sections(system_name)
    peer_rationale, peer_rules, peer_label = _peer_examples(peer_system, system_name)
    kansei = _kansei_vocab()
    archetypes = _archetype_list()
    rule_id_hint = _existing_rule_id_prefix(system_name)

    parts = [
        f'# A3 context for `{system_name}`',
        '',
        '> Auto-generated by `tools/prepare_a3_context.py`. This is **input prep only** — the LLM still makes all design judgments (which decisions to extract, which kansei words apply, which archetypes fit, what trade_off/intent/avoid to write, what confidence to assign).',
        '',
        '## 0. Mission (read this first)',
        '',
        'Write `grammar/rationale/{0}.md` (A2) and `grammar/rules/{0}.yaml` (A3) for the system **{0}**. Follow `scripts/extract-grammar.md` step-by-step. The materials below are gathered for your convenience.'.format(system_name),
        '',
        '## 1. tokens.json (already extracted by A1)',
        '',
        _summarize_tokens(tokens or {}),
        '',
        '## 2. DESIGN.md sections (segmented by A1)',
        '',
    ]
    for section_slug, section_text in sections.items():
        if not section_text:
            continue
        parts.append(f'### DESIGN.md > `{section_slug}` ({len(section_text)} chars)')
        parts.append('')
        parts.append('```')
        parts.append(section_text[:2000].strip())
        if len(section_text) > 2000:
            parts.append('...(truncated, read full at source-design-systems/{0}/DESIGN.md)'.format(system_name))
        parts.append('```')
        parts.append('')

    parts += [
        '## 3. Kansei controlled vocabulary (`references/kansei-theory.md`)',
        '',
        '> A3 must pick `preconditions.kansei` words from this vocabulary. Words outside this list will be flagged by `tools/validate_rules.py`.',
        '',
        kansei,
        '',
        '## 4. Brand archetype list (`references/brand-archetypes.md`)',
        '',
        '> A3 must pick `preconditions.brand_archetypes` (1-3 entries) from these 12. Per `scripts/extract-grammar.md` v1.5.0+ this is mandatory.',
        '',
        archetypes,
        '',
        '## 5. Rule_id format',
        '',
        rule_id_hint,
        '',
        f'## 6. Format example — peer system rationale ({peer_label})',
        '',
        '> Use the **structure** as your template. Do NOT copy content.',
        '',
        '```markdown',
        peer_rationale[:2500] + ('\n...(truncated)' if len(peer_rationale) > 2500 else ''),
        '```',
        '',
        '## 7. Format example — peer system rules',
        '',
        '```yaml',
        peer_rules[:3000] + ('\n# ...(truncated)' if len(peer_rules) > 3000 else ''),
        '```',
        '',
        '## 8. Existing A2 rationale (if you wrote it already)',
        '',
        rationale_existing[:2500] if isinstance(rationale_existing, str) else '(none)',
        '',
        '## 9. Reminders (v1.7.0 — read all five; each has cost a real round-trip in prior batches)',
        '',
        '- **No lazy archetype stamping (F6)**: don\'t copy system-level archetypes to every rule. anti_patterns rules often span MORE archetypes than rule-bearing sections (they guard boundaries multiple archetypes can cross); voice rules often span FEWER (the imperative voice has a narrow stance). validate_rules.py warns at >90% archetype uniformity.',
        '- **No phantom rule_ids in known_conflicts**: if you cite a conflict, the target rule_id MUST exist. Run `python3 tools/validate_rules.py` after writing.',
        '- **Stay within kansei vocab (F2)**: see §3 above. Off-vocab words are warnings by default; CI runs `--strict-vocab` which makes them blockers. Do NOT add new vocab in the same PR — split vocab change from rules change.',
        '- **Confidence calibration (F8)**: use the 5-tier rubric in `scripts/extract-grammar.md` A3 step 5: 0.4–0.5 = stub/template; 0.5–0.6 = real product single source (THE DEFAULT FOR FIRST-EXTRACTION); 0.6–0.7 = 2 peers; 0.7–0.8 = 3+ peers + co_occurrence ≥0.6; 0.8+ = 5+ peers industry consensus. **First-extraction rules CANNOT exceed 0.7** — validator warns on confidence>0.7 with single emerges_from.',
        '- **YAML pitfalls (F1)**: when writing the .yaml, watch for: (a) parenthetical after unquoted list `[50,80] (warm)` → wrap whole value in quotes; (b) unquoted colon `5:1 ratio` → wrap in quotes; (c) string starting with `"..."` then continuing → use single quotes or block scalar; (d) multi-line reason without `|` → use `reason: |`; (e) version/numeric strings parsed as float — quote them.',
        '- **Verbatim DESIGN.md citation (F9)**: every `### decision:` in rationale.md must contain at least one `>` blockquote citing the original DESIGN.md prose. validate_rationale.py warns if missing. This is what lets downstream B4 trace through paraphrase chains.',
        '- **Run BOTH validators before claiming done**:',
        '    `python3 tools/validate_rationale.py grammar/rationale/{0}.md`'.format(system_name),
        '    `python3 tools/validate_rules.py grammar/rules/{0}.yaml`'.format(system_name),
        '',
    ]
    return '\n'.join(parts)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('system_name', help='System to prepare context for (e.g. figma, ant, agentic)')
    p.add_argument('--peer', help='Peer system whose rationale/rules to show as format example. Auto-pick if omitted.')
    p.add_argument('--output', help='Output path (default: ./a3-context-<system>.md)')
    p.add_argument('--allow-missing', action='store_true',
                    help='Bypass the DESIGN.md existence check (use only when starting a fresh extraction with files about to be created).')
    args = p.parse_args()

    # v1.7.1 fail-loud guard: refuse to silently fabricate context for a system
    # that has neither a DESIGN.md nor extracted tokens. A typo'd system_name
    # used to produce a 23k-char "context" the LLM would dutifully consume.
    design_md = os.path.join(SKILL_ROOT, 'source-design-systems',
                              args.system_name, 'DESIGN.md')
    tokens = os.path.join(SKILL_ROOT, 'grammar', 'tokens',
                           f'{args.system_name}.json')
    if not args.allow_missing and not os.path.isfile(design_md) and not os.path.isfile(tokens):
        sys.stderr.write(
            f'error: system `{args.system_name}` has neither '
            f'`source-design-systems/{args.system_name}/DESIGN.md` nor '
            f'`grammar/tokens/{args.system_name}.json` — refusing to '
            f'fabricate context. Pass --allow-missing to override (only '
            f'sensible if files are about to be created), or check the '
            f'system name for typos via `python3 tools/check_state.py`.\n'
        )
        sys.exit(1)

    # v1.7.1 (#34): also fail loud when --peer points to a non-existent
    # extracted system. Silently emitting "(missing)" peer rationale + rules
    # leaves the LLM without a usable format example — worse than no peer
    # at all. Auto-pick (peer=None) is fine because we fall back to a real
    # peer or alphabetical default.
    if args.peer:
        peer_rationale = os.path.join(SKILL_ROOT, 'grammar', 'rationale',
                                       f'{args.peer}.md')
        peer_rules = os.path.join(SKILL_ROOT, 'grammar', 'rules',
                                   f'{args.peer}.yaml')
        if not os.path.isfile(peer_rationale) and not os.path.isfile(peer_rules):
            sys.stderr.write(
                f'error: --peer `{args.peer}` does not have any extracted '
                f'rationale or rules in grammar/. Drop --peer to auto-pick '
                f'a semantic peer, or pick from existing extracted systems '
                f'(see `ls grammar/rules/`).\n'
            )
            sys.exit(1)

    out = args.output or f'./a3-context-{args.system_name}.md'
    text = assemble_context(args.system_name, peer_system=args.peer)
    with open(out, 'w') as f:
        f.write(text)
    print(f'Wrote A3 context: {out} ({len(text)} chars)')
    print(f'Hand it to your LLM: "Read {out} and write A2/A3 outputs per scripts/extract-grammar.md"')


if __name__ == '__main__':
    main()
