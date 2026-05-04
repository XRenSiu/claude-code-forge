#!/usr/bin/env python3
"""
rebuild_graph.py — Programmatic A4 phase: rebuild the rules relationship graph.

Reads grammar/rules/*.yaml (incl. _generated.yaml) and writes
grammar/graph/rules_graph.json with 4 deterministic relation types:
  - depends_on  (and constrains as reverse)
  - co_occurs_with (with frequency)
  - conflicts_with

Algorithm is fully deterministic (no LLM). Each invocation produces
identical output for identical input.

Usage:
  python3 rebuild_graph.py [--rules-dir <path>] [--output <path>] [--dry-run]
"""
import os, sys, re, json, argparse, datetime
from collections import defaultdict

try:
    import yaml
except ImportError:
    print('ERROR: PyYAML required. Install with: pip install pyyaml', file=sys.stderr)
    sys.exit(2)


# Standard rule-bearing section dependency hierarchy.
# A rule in section S depends on stable foundations from earlier section(s).
SECTION_DEPENDENCY_ORDER = ['color', 'typography', 'spacing', 'layout', 'depth_elevation', 'components', 'motion', 'voice']
DEPENDS_ON_RULES = {
    'components': ['color', 'typography', 'spacing', 'layout', 'depth_elevation'],
    'motion': ['components'],
    'voice': [],          # voice is independent
    'anti_patterns': [],  # cross-cutting
    'depth_elevation': ['color'],
    'layout': ['spacing'],
    'typography': ['color'],   # text color depends on palette
    'spacing': [],
    'color': [],
}


def load_rules(rules_dir):
    """Load every rule from grammar/rules/*.yaml and return {rule_id: rule_obj}."""
    rules = {}
    for fname in sorted(os.listdir(rules_dir)):
        if not fname.endswith('.yaml') and not fname.endswith('.yml'):
            continue
        path = os.path.join(rules_dir, fname)
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except Exception as e:
            print(f'WARN: skipping {fname}: {e}', file=sys.stderr)
            continue
        if not data:
            continue
        rule_list = data.get('rules', [])
        for r in rule_list:
            rid = r.get('rule_id')
            if not rid:
                continue
            r['_source_file'] = fname
            rules[rid] = r
    return rules


def kansei_overlap(rule_a, rule_b):
    """Jaccard overlap of rule.preconditions.kansei sets."""
    ka = set(rule_a.get('preconditions', {}).get('kansei', []) or [])
    kb = set(rule_b.get('preconditions', {}).get('kansei', []) or [])
    if not ka and not kb:
        return 0.0
    return len(ka & kb) / len(ka | kb)


def kansei_words_for_system(rules_by_system, system):
    """All Kansei words used by rules of a single source system."""
    words = set()
    for r in rules_by_system.get(system, []):
        words.update(r.get('preconditions', {}).get('kansei', []) or [])
    return words


# Built-in Kansei antonym pairs — used to detect conflicts_with.
KANSEI_ANTONYMS = [
    ('modern', 'classical'), ('modern', 'ancient'), ('modern', 'traditional'),
    ('minimal', 'ornate'), ('minimal', 'decorative'), ('minimal', 'rich'),
    ('serious', 'playful'), ('serious', 'whimsical'),
    ('cold', 'warm'), ('clinical', 'cozy'),
    ('precise', 'organic'), ('structured', 'organic'),
    ('confident', 'humble'),
    ('energetic', 'calm'),
    ('aggressive', 'gentle'), ('aggressive', 'nurturing'),
]
ANTONYM_LOOKUP = defaultdict(set)
for a, b in KANSEI_ANTONYMS:
    ANTONYM_LOOKUP[a].add(b)
    ANTONYM_LOOKUP[b].add(a)


def detect_conflicts(rule_a, rule_b):
    """Return (is_conflict, reason) for ordered pair (A, B). Symmetric — caller may dedupe.

    Conservative — auto-detected conflicts only fire when:
    1. Same section AND >=2 antonym pairs (single-antonym false positives explode the graph)
    2. why.avoid mentions establish across same or directly related sections

    Cross-section conflicts should be declared explicitly via known_conflicts in yaml.
    """
    pa = rule_a.get('preconditions', {})
    pb = rule_b.get('preconditions', {})
    ka = set(pa.get('kansei', []) or [])
    kb = set(pb.get('kansei', []) or [])
    sec_a = rule_a.get('section', '')
    sec_b = rule_b.get('section', '')

    # 1. Antonym-based — only fires when SAME SECTION + at least 2 antonym pairs
    # v1.7.1: iterate ka in sorted order so the resulting reason string is
    # deterministic across runs (set iteration order varies → produced
    # different rebuilt_at every invocation, breaking idempotence).
    if sec_a == sec_b and sec_a:
        antonym_hits = []
        for a in sorted(ka):
            if a in ANTONYM_LOOKUP:
                common = ANTONYM_LOOKUP[a] & kb
                if common:
                    antonym_hits.append((a, sorted(common)))
        if len(antonym_hits) >= 2:
            return True, f"same-section ({sec_a}) kansei antonyms: {antonym_hits[:3]}"

    # 2. why.avoid mentions establish — only across same or directly related sections
    related_sections = {sec_a, sec_b}
    if len(related_sections) <= 2:
        why_a = rule_a.get('why', {}) or {}
        why_b = rule_b.get('why', {}) or {}
        avoid_a = set([v.strip() for v in (why_a.get('avoid', []) or [])])
        establ_b = why_b.get('establish', '')
        # require avoid item to be substantial (>= 4 chars, not generic words)
        meaningful_avoids = {v for v in avoid_a if v and len(v) >= 4 and v not in {'true', 'false', 'none', 'null'}}
        if establ_b and any(token in establ_b for token in meaningful_avoids):
            return True, f"A.why.avoid mentions B's establish ({establ_b})"

    return False, None


def detect_co_occurrence(rule_a, rule_b, rules_by_system):
    """v1.5.0 Issue 6 fix: Estimate co-occurrence as a weighted blend of system-level
    Jaccard (emerges_from) and concept-level Kansei overlap. Pre-v1.5.0 the freq was
    pure Jaccard, which collapsed to binary 0/1 when each rule had a single
    emerges_from system — defeating B3.4 weighted clustering.

    New formula:
      freq = 0.4 * jaccard(emerges_from) + 0.4 * kansei_overlap + 0.2 * archetype_overlap

    Returns (frequency 0.0-1.0, both_count, either_count). Frequency is now
    continuous in [0, 1] with meaningful gradient even in single-system corpora."""
    sa = set(rule_a.get('emerges_from', []) or [])
    sb = set(rule_b.get('emerges_from', []) or [])
    if not sa or not sb:
        return None
    both = sa & sb
    either = sa | sb
    if not either:
        return None
    jaccard_systems = len(both) / len(either)

    # Kansei overlap (semantic similarity)
    ka = set((rule_a.get('preconditions', {}) or {}).get('kansei', []) or [])
    kb = set((rule_b.get('preconditions', {}) or {}).get('kansei', []) or [])
    if ka and kb:
        kansei_overlap_score = len(ka & kb) / len(ka | kb)
    else:
        kansei_overlap_score = 0.0

    # Archetype overlap (v1.5.0 — only meaningful after Issue 5 backfill)
    aa = set((rule_a.get('preconditions', {}) or {}).get('brand_archetypes', []) or [])
    ab = set((rule_b.get('preconditions', {}) or {}).get('brand_archetypes', []) or [])
    if aa and ab:
        archetype_overlap_score = len(aa & ab) / len(aa | ab)
    else:
        archetype_overlap_score = 0.0

    freq = (0.4 * jaccard_systems
          + 0.4 * kansei_overlap_score
          + 0.2 * archetype_overlap_score)
    return freq, len(both), len(either)


def detect_semantic_similarity(rule_a, rule_b):
    """Two rules are 'semantically similar' if same section + non-trivial kansei overlap.
       Used to gate co_occurs_with (otherwise every rule in same system would 'co-occur' with every other rule)."""
    if rule_a.get('section') != rule_b.get('section'):
        return False
    if rule_a.get('rule_id') == rule_b.get('rule_id'):
        return False
    return kansei_overlap(rule_a, rule_b) >= 0.2


def build_graph(rules):
    """Return {'nodes': [...], edge counts} given rules dict."""
    rule_ids = sorted(rules.keys())
    relations = defaultdict(lambda: {
        'depends_on': [],
        'constrains': [],
        'co_occurs_with': [],
        'conflicts_with': [],
    })

    # 1. Section-driven depends_on / constrains
    for rid, r in rules.items():
        section = r.get('section', '')
        deps_sections = DEPENDS_ON_RULES.get(section, [])
        for dep_section in deps_sections:
            # Find rules from same source systems with that dep_section
            for other_rid, other in rules.items():
                if other.get('section') == dep_section and other_rid != rid:
                    # Co-system match boosts dependency relevance
                    sa = set(r.get('emerges_from', []) or [])
                    sb = set(other.get('emerges_from', []) or [])
                    if sa & sb:
                        relations[rid]['depends_on'].append({
                            'rule': other_rid,
                            'reason': f'{section} depends on {dep_section} foundation (same source: {sorted(sa & sb)[0]})'
                        })
                        relations[other_rid]['constrains'].append({'rule': rid})
                        break  # one dep per section is enough

    # 2. Pairwise co_occurs_with (semantically similar pairs only)
    for i, rid_a in enumerate(rule_ids):
        rule_a = rules[rid_a]
        for rid_b in rule_ids[i+1:]:
            rule_b = rules[rid_b]
            if not detect_semantic_similarity(rule_a, rule_b):
                continue
            co = detect_co_occurrence(rule_a, rule_b, None)
            if co is None:
                continue
            freq, both, either = co
            if freq >= 0.3:  # threshold from spec
                relations[rid_a]['co_occurs_with'].append({
                    'rule': rid_b, 'frequency': round(freq, 2)
                })
                relations[rid_b]['co_occurs_with'].append({
                    'rule': rid_a, 'frequency': round(freq, 2)
                })

    # 3a. Explicit known_conflicts in rule yaml (LLM-declared during A3)
    for rid, r in rules.items():
        for kc in (r.get('known_conflicts', []) or []):
            target_id = kc.get('rule') if isinstance(kc, dict) else kc
            reason = kc.get('reason', 'declared in rule yaml') if isinstance(kc, dict) else 'declared in rule yaml'
            if target_id in rules:
                # Add symmetric edge
                if not any(c['rule'] == target_id for c in relations[rid]['conflicts_with']):
                    relations[rid]['conflicts_with'].append({'rule': target_id, 'reason': reason})
                if not any(c['rule'] == rid for c in relations[target_id]['conflicts_with']):
                    relations[target_id]['conflicts_with'].append({'rule': rid, 'reason': reason})

    # 3b. Auto-detected pairwise conflicts (Kansei antonyms / why.avoid mention)
    for i, rid_a in enumerate(rule_ids):
        rule_a = rules[rid_a]
        for rid_b in rule_ids[i+1:]:
            rule_b = rules[rid_b]
            is_conflict, reason = detect_conflicts(rule_a, rule_b)
            if is_conflict:
                # Skip if already declared
                if any(c['rule'] == rid_b for c in relations[rid_a]['conflicts_with']):
                    continue
                relations[rid_a]['conflicts_with'].append({'rule': rid_b, 'reason': reason})
                relations[rid_b]['conflicts_with'].append({'rule': rid_a, 'reason': reason})

    # Materialize nodes
    nodes = []
    for rid in rule_ids:
        nodes.append({'rule_id': rid, 'relations': dict(relations[rid])})

    edge_counts = {
        'depends_on': sum(len(n['relations']['depends_on']) for n in nodes),
        'constrains': sum(len(n['relations']['constrains']) for n in nodes),
        'co_occurs_with': sum(len(n['relations']['co_occurs_with']) for n in nodes) // 2,  # symmetric
        'conflicts_with': sum(len(n['relations']['conflicts_with']) for n in nodes) // 2,  # symmetric
    }

    return nodes, edge_counts


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    p.add_argument('--rules-dir', default=os.path.normpath(os.path.join(here, '..', 'grammar', 'rules')))
    p.add_argument('--output', default=os.path.normpath(os.path.join(here, '..', 'grammar', 'graph', 'rules_graph.json')))
    p.add_argument('--rules-version', default=None, help='Stamp version field on output (default: read from version.json)')
    p.add_argument('--dry-run', action='store_true', help='Print summary only, do not write')
    p.add_argument('--skip-validate', action='store_true', help='Skip validate_rules.py preflight (v1.6.0+ runs it by default)')
    p.add_argument('--skip-sync', action='store_true', help='Skip sync_registry preflight (v1.6.0+ runs it by default)')
    args = p.parse_args()

    if not os.path.isdir(args.rules_dir):
        print(f'ERROR: rules dir not found: {args.rules_dir}', file=sys.stderr)
        sys.exit(2)

    # v1.6.0: preflight — sync registry + validate rules before rebuilding
    if not args.skip_sync:
        try:
            sys.path.insert(0, here)
            from sync_registry import sync as _sync_registry  # type: ignore
            r = _sync_registry(dry_run=False)
            changed = len(r.get('changes', []))
            if changed:
                print(f'[preflight] sync_registry: updated {changed} entries')
        except Exception as e:
            print(f'[preflight] sync_registry skipped: {e}')

    if not args.skip_validate:
        try:
            sys.path.insert(0, here)
            from validate_rules import validate_file as _validate_file, _collect_all_rule_ids, _load_kansei_vocab  # type: ignore
            import glob as _glob
            all_ids = _collect_all_rule_ids()
            vocab = _load_kansei_vocab()
            files = sorted(_glob.glob(os.path.join(args.rules_dir, '*.yaml')))
            blockers = 0
            warnings = 0
            for fp in files:
                if os.path.basename(fp).startswith('.'):
                    continue
                r = _validate_file(fp, all_ids, vocab)
                blockers += len(r['blockers'])
                warnings += len(r['warnings'])
            if blockers:
                print(f'[preflight] validate_rules: {blockers} BLOCKER(s) found — run `python3 tools/validate_rules.py --all` for details. Aborting rebuild.', file=sys.stderr)
                sys.exit(3)
            print(f'[preflight] validate_rules: 0 blockers, {warnings} warnings ({len(files)} files)')

            # v1.7.0 F7: also validate rationale.md schema
            try:
                from validate_rationale import validate_file as _validate_rationale  # type: ignore
                rdir = os.path.normpath(os.path.join(here, '..', 'grammar', 'rationale'))
                rfiles = sorted(_glob.glob(os.path.join(rdir, '*.md')))
                rblockers = 0
                rwarnings = 0
                for fp in rfiles:
                    if os.path.basename(fp).startswith('.'):
                        continue
                    r = _validate_rationale(fp)
                    rblockers += len(r['blockers'])
                    rwarnings += len(r['warnings'])
                if rblockers:
                    print(f'[preflight] validate_rationale: {rblockers} BLOCKER(s) found — run `python3 tools/validate_rationale.py --all` for details. Aborting rebuild.', file=sys.stderr)
                    sys.exit(3)
                print(f'[preflight] validate_rationale: 0 blockers, {rwarnings} warnings ({len(rfiles)} files)')
            except SystemExit:
                raise
            except Exception as e:
                print(f'[preflight] validate_rationale skipped: {e}')
        except SystemExit:
            raise
        except Exception as e:
            print(f'[preflight] validate_rules skipped: {e}')

    rules = load_rules(args.rules_dir)
    if not rules:
        print('No rules found. Graph will be empty.')

    nodes, edge_counts = build_graph(rules)

    rules_version = args.rules_version
    if rules_version is None:
        version_json = os.path.normpath(os.path.join(here, '..', 'grammar', 'meta', 'version.json'))
        try:
            with open(version_json) as f:
                rules_version = json.load(f).get('rules_version', '0.0.0')
        except Exception:
            rules_version = '0.0.0'

    # v1.7.1: idempotent timestamp — only update rebuilt_at when the actual
    # node content changes. Without this, every consecutive `rebuild_graph`
    # call produces a new timestamp and the file's sha1 churns even when
    # rules didn't change. Breaks reproducibility and noisy diffs.
    new_now = datetime.datetime.utcnow().isoformat() + 'Z'
    rebuilt_at = new_now
    try:
        if os.path.isfile(args.output):
            with open(args.output) as f:
                prev = json.load(f)
            prev_nodes = prev.get('nodes')
            prev_edges = prev.get('edge_counts')
            if prev_nodes == nodes and prev_edges == edge_counts:
                rebuilt_at = prev.get('rebuilt_at', new_now)
    except Exception:
        pass

    output = {
        '$schema_description': 'Rules relationship graph. Rebuilt by tools/rebuild_graph.py.',
        'version': rules_version,
        'rebuilt_at': rebuilt_at,
        'node_count': len(nodes),
        'edge_counts': edge_counts,
        'nodes': nodes,
    }

    summary = {
        'rules_loaded': len(rules),
        'edge_counts': edge_counts,
        'avg_degree': round(sum(edge_counts.values()) * 2 / max(len(rules), 1), 2),
        'sections_seen': sorted(set(r.get('section', 'unknown') for r in rules.values())),
        'systems_seen': sorted(set(s for r in rules.values() for s in (r.get('emerges_from', []) or []))),
    }

    if args.dry_run:
        print(json.dumps(summary, indent=2))
        return

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f'Wrote {args.output}')
    print(json.dumps(summary, indent=2))

    # v1.7.1: also rebuild provenance-index.json. extract-grammar.md step
    # collection 256 says "更新 grammar/meta/provenance-index.json：登记新规则
    # 的 rule_ids → system 映射" — but nothing was actually doing it. The file
    # was stuck at 0 entries even after 275 rules were extracted. B4
    # generation reads this index for inheritance.source_systems lookup.
    provenance_index_path = os.path.normpath(
        os.path.join(here, '..', 'grammar', 'meta', 'provenance-index.json')
    )
    try:
        try:
            with open(provenance_index_path) as f:
                pi = json.load(f)
        except Exception:
            pi = {}
        pi.setdefault(
            '$schema_description',
            'Reverse index: rule_id -> source system(s). Rebuilt automatically '
            'by tools/rebuild_graph.py from each rule\'s emerges_from + provenance.'
        )
        pi['_template'] = {
            '<rule_id>': {
                'system': '<primary source system>',
                'co_emerges_from': ['<other systems this rule pattern was found in>'],
                'provenance': 'original | generated | merged',
                'added_at': '<ISO 8601>'
            }
        }
        # v1.7.1: idempotent — preserve previous added_at for unchanged rules
        prev_rules = pi.get('rules', {}) if isinstance(pi.get('rules'), dict) else {}
        rules_index = {}
        for rid, r in rules.items():
            ef = r.get('emerges_from') or []
            primary = ef[0] if ef else None
            co = ef[1:] if len(ef) > 1 else []
            entry = {
                'system': primary,
                'co_emerges_from': co,
                'provenance': r.get('provenance', 'original'),
            }
            prev = prev_rules.get(rid, {})
            # If the lookup-relevant fields match the previous record, keep
            # the original added_at (so the file is byte-stable when nothing
            # changed). Otherwise stamp with current time.
            if (prev.get('system') == entry['system']
                    and prev.get('co_emerges_from') == entry['co_emerges_from']
                    and prev.get('provenance') == entry['provenance']
                    and prev.get('added_at')):
                entry['added_at'] = prev['added_at']
            else:
                entry['added_at'] = rebuilt_at
            rules_index[rid] = entry
        pi['rules'] = rules_index
        # Idempotent rebuilt_at — only bump if rules_index actually changed.
        if prev_rules != rules_index:
            pi['rebuilt_at'] = rebuilt_at
        else:
            pi.setdefault('rebuilt_at', rebuilt_at)
        pi['rule_count'] = len(rules_index)
        with open(provenance_index_path, 'w') as f:
            json.dump(pi, f, indent=2, ensure_ascii=False)
        print(f'Wrote {provenance_index_path} ({len(rules_index)} rule mappings)')
    except Exception as e:
        print(f'[warn] provenance-index update skipped: {e}', file=sys.stderr)

    # v1.7.1: refresh version.json's automatic counters. total_rules,
    # extracted_systems, last_updated drift any time we add/remove rules
    # without remembering to bump version.json. rules_version + notes stay
    # human-maintained (semantic content); the three counters are mechanical.
    version_json_path = os.path.normpath(
        os.path.join(here, '..', 'grammar', 'meta', 'version.json')
    )
    try:
        with open(version_json_path) as f:
            vj = json.load(f)
        rules_dir = args.rules_dir
        # Count extracted_systems = non-_generated yaml files
        extracted_count = sum(
            1 for fn in os.listdir(rules_dir)
            if fn.endswith('.yaml') and not fn.startswith('_') and not fn.startswith('.')
        )
        # registered_systems comes from source-registry.json
        registered_count = vj.get('registered_systems')
        try:
            with open(os.path.normpath(os.path.join(here, '..', 'grammar', 'meta', 'source-registry.json'))) as f:
                sr = json.load(f)
                registered_count = len(sr.get('systems', {}))
        except Exception:
            pass
        before = (vj.get('total_rules'), vj.get('extracted_systems'), vj.get('registered_systems'))
        vj['total_rules'] = len(rules)
        vj['extracted_systems'] = extracted_count
        if registered_count is not None:
            vj['registered_systems'] = registered_count
            vj['total_systems'] = registered_count  # legacy alias
        after = (vj['total_rules'], vj['extracted_systems'], vj.get('registered_systems'))
        # Idempotent — only bump last_updated when counters actually changed.
        if before != after:
            vj['last_updated'] = rebuilt_at
        with open(version_json_path, 'w') as f:
            json.dump(vj, f, indent=2, ensure_ascii=False)
        if before != after:
            print(f'Refreshed {version_json_path}: counters {before} -> {after}, last_updated={rebuilt_at}')
        else:
            print(f'{version_json_path} unchanged (counters and last_updated preserved)')
    except Exception as e:
        print(f'[warn] version.json refresh skipped: {e}', file=sys.stderr)


if __name__ == '__main__':
    main()
