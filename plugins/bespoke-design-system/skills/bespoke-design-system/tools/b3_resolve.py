#!/usr/bin/env python3
"""
b3_resolve.py — Deterministic B3 conflict-resolution + dependency-closure +
style-island clustering for bespoke-design-system.

Reads:
  - <b2_path>:        a JSON file (B2 output). The file must contain either
                      `candidate_rules` (preferred) or `candidates` as the
                      candidate list field.
  - grammar/graph/rules_graph.json   (relationship graph)

Writes:
  - <output_path>:    a JSON file path (NOT a directory). Conventionally named
                      `<output_dir>/_b3-self-consistent.json` but the script
                      treats `--output` as the literal file to write.

Algorithm (deterministic, no LLM):
  Step 1 — Load graph
  Step 2 — Conflict resolution: for each candidate pair in conflicts_with,
           keep the higher final_score, drop the other.
  Step 3 — Dependency closure with cascade drop (v1.8.1):
           For each kept rule R, walk depends_on[R]. If a dep D would be
           blocked by an already-kept rule K (D in conflicts_with[K] or
           vice versa), CASCADE-DROP R rather than re-adding D. This
           preserves Step 2's score-based authority.
  Step 4 — Style-island clustering (size-aware per b3-conflict-resolution.md)
  Step 5 — Section coverage check + backstop fill
  Step 6 — Emit _b3-self-consistent.json

Usage:
  python3 b3_resolve.py --b2 <b2_file_path> --output <output_file_path> [--graph <path>]

Example:
  python3 b3_resolve.py \\
    --b2    ./bespoke-design/<slug>/_b2-candidates.json \\
    --output ./bespoke-design/<slug>/_b3-self-consistent.json
"""
import os, sys, json, argparse
from collections import defaultdict, Counter


def load_graph(path):
    g = json.load(open(path))
    nodes = g['nodes'] if isinstance(g, dict) and 'nodes' in g else g
    depends_on = defaultdict(list)
    co_occurs = defaultdict(list)
    conflicts = defaultdict(set)
    valid_ids = set()
    for n in nodes:
        if not isinstance(n, dict):
            continue
        rid = n.get('rule_id') or n.get('id')
        if not rid:
            continue
        valid_ids.add(rid)
        rels = n.get('relations', {}) or {}
        for d in rels.get('depends_on', []) or []:
            target = d.get('rule') if isinstance(d, dict) else d
            if target:
                depends_on[rid].append(target)
        for c in rels.get('conflicts_with', []) or []:
            target = c.get('rule') if isinstance(c, dict) else c
            reason = c.get('reason', '') if isinstance(c, dict) else ''
            if target:
                conflicts[rid].add((target, reason))
        co = rels.get('co_occurs_with')
        if isinstance(co, dict):
            for r2, freq in co.items():
                co_occurs[rid].append((r2, freq))
        elif isinstance(co, list):
            for c in co:
                if isinstance(c, dict):
                    co_occurs[rid].append((c.get('rule'), c.get('frequency', 1)))
    return depends_on, co_occurs, conflicts, valid_ids


def conflict_pair(a, b, conflicts):
    """Symmetric check: is (a, b) in conflicts_with relation?"""
    for target, _ in conflicts.get(a, ()):
        if target == b:
            return True
    for target, _ in conflicts.get(b, ()):
        if target == a:
            return True
    return False


def conflict_reason(a, b, conflicts):
    for target, reason in conflicts.get(a, ()):
        if target == b:
            return reason
    for target, reason in conflicts.get(b, ()):
        if target == a:
            return reason
    return ''


def resolve(b2_path, graph_path, output_path):
    b2 = json.load(open(b2_path))
    # Schema-tolerant: accept either 'candidate_rules' (canonical) or 'candidates' (legacy)
    if 'candidate_rules' in b2:
        candidates = b2['candidate_rules']
    elif 'candidates' in b2:
        candidates = b2['candidates']
    else:
        raise KeyError(
            "b2 input must contain either 'candidate_rules' (preferred) or 'candidates'. "
            f"Found keys: {list(b2.keys())}"
        )
    cand_ids = {r['rule_id'] for r in candidates}
    score_map = {r['rule_id']: r['final_score'] for r in candidates}
    rule_lookup = {r['rule_id']: r for r in candidates}
    sec_of = {r['rule_id']: r['section'] for r in candidates}

    depends_on, co_occurs, conflicts, valid_ids = load_graph(graph_path)

    # Step 2: Conflict resolution
    kept = set(cand_ids)
    dropped = []
    for rid in sorted(cand_ids):
        if rid not in kept:
            continue
        for target, reason in list(conflicts.get(rid, ())):
            if target in kept and target != rid:
                # Keep higher final_score
                if score_map.get(rid, 0) >= score_map.get(target, 0):
                    kept.discard(target)
                    dropped.append({
                        'rule_id': target,
                        'reason': f'conflicts_with {rid} ({reason})',
                        'phase': 'step2_score_resolution',
                    })
                else:
                    kept.discard(rid)
                    dropped.append({
                        'rule_id': rid,
                        'reason': f'conflicts_with {target} ({reason})',
                        'phase': 'step2_score_resolution',
                    })
                    break

    # Step 3 — Dependency closure with cascade drop (v1.8.1)
    to_add = set()
    cascade_dropped = set()
    broken_deps = []

    def walk_deps(R):
        """Return (set_of_deps_to_add, blocking_dep_or_None)."""
        deps_to_add = set()
        queue = [R]
        seen = set()
        while queue:
            x = queue.pop()
            if x in seen:
                continue
            seen.add(x)
            for D in depends_on.get(x, []):
                if D in kept or D in to_add or D in deps_to_add:
                    continue
                if D not in valid_ids:
                    broken_deps.append({'from': x, 'missing': D})
                    continue
                # Check if adding D would re-introduce a conflict with any
                # already-kept rule K
                blockers = [K for K in (kept | to_add | deps_to_add)
                            if K != D and conflict_pair(D, K, conflicts)]
                if blockers:
                    return None, (D, blockers[0])  # signal cascade
                deps_to_add.add(D)
                queue.append(D)
        return deps_to_add, None

    # Process in score-sorted order so we drop low-score dependents first
    for R in sorted(kept, key=lambda r: score_map.get(r, 0)):
        if R in cascade_dropped:
            continue
        deps_to_add, cascade_signal = walk_deps(R)
        if cascade_signal is not None:
            D, K = cascade_signal
            cascade_dropped.add(R)
            dropped.append({
                'rule_id': R,
                'reason': f'cascade-drop: requires {D} which conflicts with already-kept {K}',
                'phase': 'step3_cascade_drop',
            })
        else:
            to_add |= deps_to_add

    kept -= cascade_dropped
    kept |= to_add

    # Step 4 — Style-island clustering (size-aware)
    library_size = len(set(r.split('-')[0] for r in valid_ids))  # rough proxy
    library_total_rules = len(valid_ids)
    edges = []
    for rid in kept:
        for other, freq in co_occurs.get(rid, []):
            if other in kept and other > rid:
                edges.append((rid, other, freq))

    main_clusters = []
    cluster_metadata = {}
    isolated_kept_set = set()
    isolated_dropped_set = set()

    if library_total_rules < 30:
        # Too small — skip clustering
        cluster_metadata = {'skipped_reason': 'small_library', 'library_size': library_total_rules}
    elif edges:
        freqs = [e[2] for e in edges]
        mu = sum(freqs) / len(freqs)
        sigma = (sum((f - mu) ** 2 for f in freqs) / len(freqs)) ** 0.5
        threshold = max(0.0, mu - sigma) if library_total_rules < 100 else mu
        high_edges = [e for e in edges if e[2] >= threshold]

        adj = defaultdict(set)
        for a, b, _ in high_edges:
            adj[a].add(b)
            adj[b].add(a)
        visited = set()
        clusters = []
        for n in adj.keys():
            if n in visited:
                continue
            cluster = []
            stk = [n]
            while stk:
                x = stk.pop()
                if x in visited:
                    continue
                visited.add(x)
                cluster.append(x)
                stk.extend(adj[x])
            clusters.append(cluster)

        clusters_scored = sorted(
            ((sum(score_map.get(r, 0) for r in c) / len(c), c) for c in clusters),
            reverse=True
        )
        # Take top 1-2 (larger libraries get up to 5)
        max_clusters = 5 if library_total_rules > 300 else 2
        main_clusters = clusters_scored[:max_clusters]

        main_member_set = set()
        for _, c in main_clusters:
            main_member_set |= set(c)

        isolated = kept - main_member_set
        median_score = sorted(score_map.values())[len(score_map) // 2] if score_map else 0
        isolated_kept_set = {r for r in isolated if score_map.get(r, 0) > median_score}
        isolated_dropped_set = isolated - isolated_kept_set

        # Drop low-score isolated, but keep deps (they were added for a reason)
        kept = main_member_set | isolated_kept_set | to_add
        for r in isolated_dropped_set:
            if r not in kept:
                dropped.append({
                    'rule_id': r,
                    'reason': 'low_score_isolated_after_clustering',
                    'phase': 'step4_clustering',
                })

    # Step 5 — Section coverage check
    required_sections = ['color', 'typography', 'components', 'layout', 'depth_elevation']
    sec_counts = Counter(sec_of.get(r, 'unknown') for r in kept)
    degraded = []
    recovered = []
    for s in required_sections:
        if sec_counts.get(s, 0) == 0:
            recovery_pool = [r for r in candidates
                             if r['section'] == s and r['rule_id'] not in {d['rule_id'] for d in dropped}]
            recovery = sorted(recovery_pool, key=lambda x: -x['final_score'])
            if recovery:
                top_r = recovery[0]
                kept.add(top_r['rule_id'])
                recovered.append({'section': s, 'rule_id': top_r['rule_id'], 'score': top_r['final_score']})
            else:
                degraded.append(s)

    # Recompute final section counts
    sec_counts_final = Counter(sec_of.get(r, 'unknown') for r in kept)

    def kept_reason(rid):
        if rid in to_add:
            return 'dependency'
        if any(rid in c for _, c in main_clusters):
            return 'cluster_main'
        if rid in isolated_kept_set:
            return 'supplementary'
        if any(d['rule_id'] == rid for d in recovered):
            return 'recovered_for_coverage'
        return 'unknown'

    output = {
        'self_consistent_subset': {
            'rules': [
                {
                    'rule_id': rid,
                    'section': sec_of.get(rid, 'unknown'),
                    'final_score': score_map.get(rid, 0),
                    'kept_reason': kept_reason(rid),
                    'system': rule_lookup.get(rid, {}).get('system', 'unknown'),
                    'archetypes': rule_lookup.get(rid, {}).get('archetypes', []),
                    'kansei': rule_lookup.get(rid, {}).get('kansei', []),
                    'why': rule_lookup.get(rid, {}).get('why', {}),
                    'action': rule_lookup.get(rid, {}).get('action', {}),
                    'emerges_from': rule_lookup.get(rid, {}).get('emerges_from', []),
                }
                for rid in sorted(kept, key=lambda r: -score_map.get(r, 0))
            ],
            'clusters': [
                {
                    'id': f'main_cluster_{i+1}',
                    'mean_score': round(s, 4),
                    'member_count': len(c),
                    'members': c[:20] + (['...'] if len(c) > 20 else []),
                    'dominant_systems': [sys for sys, _ in
                        Counter(rule_lookup.get(r, {}).get('system', '?') for r in c).most_common(5)],
                }
                for i, (s, c) in enumerate(main_clusters)
            ],
            'cluster_metadata': cluster_metadata,
            'dropped': dropped,
            'cascade_dropped': sorted(cascade_dropped),
            'recovered_for_coverage': recovered,
            'section_coverage': dict(sec_counts_final),
            'degraded_sections': degraded,
            'broken_dependencies': broken_deps,
        },
        'stats': {
            'b2_input': len(candidates),
            'after_step2_conflict_resolution': len(kept) - len(to_add),
            'step3_dep_added': len(to_add),
            'step3_cascade_dropped': len(cascade_dropped),
            'final_subset_size': len(kept),
            'main_clusters': len(main_clusters),
        }
    }

    if os.path.isdir(output_path):
        # Friendly error: docstring used to suggest --output is a directory.
        # Now make the failure explicit instead of IsADirectoryError mid-write.
        raise IsADirectoryError(
            f"--output expects a file path, got a directory: {output_path!r}. "
            f"Suggested: pass {os.path.join(output_path, '_b3-self-consistent.json')!r}"
        )

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f'Wrote {output_path}')
    print(f"  B2 input: {len(candidates)}")
    print(f"  After step 2 conflict resolution: {len(kept) - len(to_add)} kept, {sum(1 for d in dropped if d['phase']=='step2_score_resolution')} dropped")
    print(f"  Step 3 deps added: {len(to_add)}, cascade dropped: {len(cascade_dropped)}")
    print(f"  Final: {len(kept)} rules across {len(sec_counts_final)} sections")
    print(f"  Section coverage: {dict(sec_counts_final)}")
    if degraded:
        print(f"  DEGRADED sections: {degraded}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    p.add_argument('--b2', required=True, help='Path to _b2-candidates.json')
    p.add_argument('--output', required=True, help='Path to write _b3-self-consistent.json')
    p.add_argument('--graph', default=os.path.normpath(os.path.join(here, '..', 'grammar', 'graph', 'rules_graph.json')))
    args = p.parse_args()
    resolve(args.b2, args.graph, args.output)


if __name__ == '__main__':
    main()
