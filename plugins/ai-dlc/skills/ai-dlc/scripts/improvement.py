"""Project observations into scoped improvement proposals, without executing log text.

This is a view of existing automation journals, not another task state machine.
One task's retries are one sample. Only qualified Harness counterexamples can
become active regression inputs; rule, budget and contract changes stay proposals.
"""
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import sys
import tempfile

import verification as v

ROUTES = {
    'implementation': ('project-regression', 'Reproduce the original predicate, run positive/negative/recovery controls, then qualify an additive regression.'),
    'environment': ('project-harness-environment', 'Repair the measured fixture or tool precondition; verify a fresh isolated launch and the full native graph.'),
    'checker': ('project-harness-evolve', 'Calibrate the checker against legitimate and invalid behavior before proposing a versioned checker change.'),
    'product': ('contract-change', 'Resolve the product promise through its existing requirements/contract change process.'),
    'unknown': ('triage', 'Obtain a reproducible cause before changing code, rules or budgets.'),
}


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.feedback-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def inspect(path):
    path = Path(path).resolve()
    v.require(path.stat().st_size <= 64 * 1024 * 1024, 'automation journal too large')
    journal = v.read_json(path)
    v.require(journal.get('schema_version') == 1 and isinstance(journal.get('attempts'), list), 'invalid automation journal')
    v.require(len(journal['attempts']) <= 10000, 'too many attempts to inspect')
    attempts, errors = [], []
    seen = set()
    for attempt in journal['attempts']:
        aid = attempt.get('attempt_id')
        v.require(isinstance(aid, str) and aid not in seen, 'duplicate or missing attempt identity'); seen.add(aid)
        result = attempt.get('result', {})
        raw, issues = [], []
        directory = path.parent / 'attempts' / aid
        for item in result.get('evidence', []):
            try:
                file = Path(item['path'])
                v.require(v.under(file, directory) and file.is_file() and not file.is_symlink(), 'evidence outside recorded attempt')
                v.require(0 < item['size_bytes'] == file.stat().st_size <= 64 * 1024 * 1024 and v.file_digest(file) == item['digest'], 'evidence bytes changed')
                raw.append(item)
            except (ValueError, OSError, KeyError, TypeError) as error:
                issues.append(str(error))
        status = result.get('status', 'unknown')
        if status in ('failure', 'error') and not raw: issues.append('no verified raw failure evidence')
        domain = result.get('domain', 'unknown')
        if domain not in ROUTES and domain != 'none': domain = 'unknown'
        if issues:
            errors.append({'attempt_id': aid, 'issues': issues}); domain = 'unknown'
        source = attempt.get('source', {})
        # Stable task identities deduplicate copied journals and repeated attempts.
        task = source.get('task_id') or journal.get('slug')
        v.require(isinstance(task, str) and task, 'task identity required for improvement sampling')
        fingerprint = result.get('fingerprint') or attempt.get('fingerprint') or v.digest({'stage': attempt.get('stage'), 'domain': domain, 'reason': result.get('reason')})
        attempts.append({'attempt_id': aid, 'task_id': task, 'stage': attempt.get('stage'), 'status': status, 'domain': domain,
            'fingerprint': v.digest({'domain': domain, 'value': fingerprint}), 'evidence': raw, 'evidence_valid': not issues and bool(raw),
            'cost_microunits': result.get('cost_microunits'), 'human_seconds': result.get('human_seconds'),
            'source': source, 'incomplete': attempt.get('state') != 'complete'})
    return {'journal': str(path), 'journal_digest': v.file_digest(path), 'slug': journal.get('slug'), 'status': journal.get('status'), 'attempts': attempts, 'evidence_errors': errors}


def summarize(paths):
    v.require(len(paths) <= 1000, 'too many journals')
    sources, rejected, attempts, duplicates = [], [], {}, 0
    for path in sorted(set(map(str, paths))):
        try: source = inspect(path)
        except (ValueError, OSError, KeyError, TypeError) as error:
            rejected.append({'journal': path, 'reason': str(error)}); continue
        sources.append({k: source[k] for k in ('journal', 'journal_digest', 'slug', 'status', 'evidence_errors')})
        for item in source['attempts']:
            key = (item['task_id'], item['attempt_id'])
            if key in attempts:
                duplicates += 1
                if attempts[key] != item:
                    rejected.append({'journal': path, 'reason': 'conflicting copy of the same attempt'})
                    attempts[key]['evidence_valid'] = False; attempts[key]['domain'] = 'unknown'
            else: attempts[key] = item
    values = list(attempts.values()); failures = [a for a in values if a['status'] in ('failure', 'error')]
    groups = {}
    for item in failures:
        key = item['domain'] + '/' + item['fingerprint']
        group = groups.setdefault(key, {'domain': item['domain'], 'fingerprint': item['fingerprint'], 'tasks': set(), 'attempts': [], 'evidence': [], 'valid': True})
        group['tasks'].add(item['task_id']); group['attempts'].append(item['attempt_id']); group['evidence'].extend(item['evidence']); group['valid'] &= item['evidence_valid']
    proposals = []
    for key, group in sorted(groups.items()):
        route, verification = ROUTES.get(group['domain'], ROUTES['unknown'])
        samples = len(group['tasks'])
        proposals.append({'id': v.digest({'route': route, 'fingerprint': group['fingerprint']}), 'route': route,
            'domain': group['domain'], 'independent_tasks': samples, 'attempts': len(group['attempts']), 'task_ids': sorted(group['tasks']),
            'status': 'needs_evidence' if not group['valid'] else 'recurring_proposal' if samples >= 2 else 'single_task_observation',
            'evidence': list({e['digest'] + e['path']: e for e in group['evidence']}.values()),
            'verify_by': verification, 'activation': 'qualified additive regression only, otherwise existing reviewed change workflow',
            'budget_change_authorized': False, 'formal_criteria_change_authorized': False})
    costs = [a['cost_microunits'] for a in values]
    cost_known = lambda c: type(c) is int and c >= 0
    human = [a['human_seconds'] for a in values]
    human_known = lambda x: type(x) in (int, float) and math.isfinite(x) and x >= 0
    return {'schema_version': 1, 'authority': 'local_advisory', 'sources': sources, 'rejected_sources': rejected, 'duplicate_attempts_ignored': duplicates,
        'metrics': {'independent_tasks': len({a['task_id'] for a in values}), 'attempts': len(values), 'failed_attempts': len(failures),
            'failure_domains': dict(Counter(a['domain'] for a in failures)), 'incomplete_attempts': sum(a['incomplete'] for a in values),
            'known_cost_microunits': sum(c for c in costs if cost_known(c)), 'total_cost_microunits': sum(costs) if costs and all(cost_known(c) for c in costs) else None,
            'human_seconds_reported': sum(x for x in human if human_known(x)), 'human_time_complete': bool(human) and all(human_known(x) for x in human),
            'production_escape_rate': None, 'autonomous_model_repair_rate': None},
        'proposals': proposals, 'changes_applied': [], 'delivery_authorization': 'not_granted'}


def write_feedback(journal_path):
    value = summarize([journal_path]); write(Path(journal_path).with_name('improvement-feedback.json'), value); return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True); parser.add_argument('--out')
    args = parser.parse_args(); root = Path(args.root).resolve()
    paths = list(root.glob('*/automation/journal.json'))
    if (root / 'journal.json').is_file(): paths.append(root / 'journal.json')
    value = summarize(paths)
    if args.out: write(args.out, value)
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 1 if value['rejected_sources'] else 0


if __name__ == '__main__': sys.exit(main())
