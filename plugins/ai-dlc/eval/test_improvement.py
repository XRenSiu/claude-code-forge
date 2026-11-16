import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/ai-dlc/scripts'))
import improvement
import verification as v


class ImprovementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.root = Path(self.tmp.name)

    def journal(self, name, task, attempts=1, domain='environment', fingerprint='same-fixture-failure', cost=None):
        directory = self.root / name / 'automation'; directory.mkdir(parents=True)
        rows = []
        for i in range(attempts):
            aid = name + '-' + str(i); raw = directory / 'attempts' / aid / 'raw.json'; raw.parent.mkdir(parents=True); raw.write_text('{"observed":"fixture unavailable"}')
            rows.append({'attempt_id': aid, 'stage': 'verify', 'state': 'complete', 'source': {'task_id': task}, 'result': {'status': 'error', 'domain': domain, 'fingerprint': fingerprint, 'cost_microunits': cost,
                'evidence': [{'path': str(raw), 'digest': v.file_digest(raw), 'size_bytes': raw.stat().st_size}]}})
        path = directory / 'journal.json'; path.write_text(json.dumps({'schema_version': 1, 'slug': name, 'status': 'waiting', 'attempts': rows})); return path

    def test_retries_are_one_sample_and_environment_does_not_propose_more_code_retries(self):
        one = self.journal('first', 'task-one', 3)
        value = improvement.summarize([one]); self.assertEqual(value['proposals'][0]['independent_tasks'], 1)
        self.assertEqual(value['proposals'][0]['status'], 'single_task_observation')
        two = self.journal('second', 'task-two')
        value = improvement.summarize([one, two]); self.assertEqual(value['proposals'][0]['status'], 'recurring_proposal')
        self.assertEqual(value['proposals'][0]['route'], 'project-harness-environment')
        self.assertFalse(value['proposals'][0]['budget_change_authorized']); self.assertEqual(value['changes_applied'], [])
        self.assertIsNone(value['metrics']['total_cost_microunits']); self.assertIsNone(value['metrics']['production_escape_rate'])

    def test_damaged_raw_data_cannot_teach_a_rule(self):
        path = self.journal('first', 'task-one', cost=0)
        value = improvement.write_feedback(path); self.assertEqual(value['metrics']['total_cost_microunits'], 0)
        raw = next(path.parent.glob('attempts/*/raw.json')); raw.write_text('changed')
        value = improvement.write_feedback(path)
        self.assertEqual(value['proposals'][0]['status'], 'needs_evidence')
        self.assertEqual(value['proposals'][0]['route'], 'triage')
        self.assertTrue(value['sources'][0]['evidence_errors'])
        self.assertTrue((path.parent / 'improvement-feedback.json').is_file())

    def test_copied_task_identity_is_not_an_independent_sample(self):
        first = self.journal('first', 'same-task'); second = self.journal('second', 'same-task')
        value = improvement.summarize([first, second])
        self.assertEqual(value['metrics']['independent_tasks'], 1)
        self.assertEqual(value['proposals'][0]['status'], 'single_task_observation')

    def test_different_failure_domains_are_never_merged(self):
        paths = [self.journal('environment', 'one'), self.journal('checker', 'two', domain='checker'), self.journal('product', 'three', domain='product')]
        value = improvement.summarize(paths)
        self.assertEqual(len(value['proposals']), 3)
        self.assertEqual(set(value['metrics']['failure_domains']), {'environment', 'checker', 'product'})


if __name__ == '__main__': unittest.main()
