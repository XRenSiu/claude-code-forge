"""Evidence integrity refusal cases. These synthetic records do not prove provenance."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/accept-change/scripts'))
from verification_evidence import sha, validate_product, load


class ProductEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        raw = b'{"status":403}\n'
        (self.root / 'raw.json').write_bytes(raw)
        self.report = {
            'schema_version': 1, 'evidence_kind': 'product-observation', 'authority': 'project-self-check',
            'binding': {**{k: 'sha256:' + 'a' * 64 for k in ('candidate_digest', 'checker_digest', 'fixture_digest', 'feature_index_digest', 'environment_digest')},
                        'feature_id': 'access', 'entry_id': 'http', 'check_id': 'access-product'},
            'candidate_unchanged': True, 'status': 'PASS',
            'phases': [{'name': n, 'status': 'PASS'} for n in ('launch', 'doctor', 'drive', 'observe', 'cleanup')],
            'claims': [{'id': 'denied', 'status': 'PASS', 'expected': '403', 'actual': '403', 'evidence_refs': ['http']}],
            'evidence': [{'id': 'http', 'type': 'http', 'path': 'raw.json', 'digest': sha(raw), 'size_bytes': len(raw)}]}

    def check(self, value=None, **kwargs):
        path = self.root / 'product.json'
        path.write_text(json.dumps(value or self.report))
        return validate_product(path, ['denied'], **kwargs)

    def test_positive_is_only_project_self_check(self):
        self.assertEqual(self.check()['authority'], 'project-self-check')

    def test_missing_failed_or_reordered_lifecycle_is_rejected(self):
        for phases in (self.report['phases'][:-1], list(reversed(self.report['phases'])),
                       [dict(p, status='ERROR') for p in self.report['phases']]):
            report = copy.deepcopy(self.report); report['phases'] = phases
            with self.assertRaisesRegex(ValueError, 'lifecycle'):
                self.check(report)

    def test_raw_tamper_and_symlink_are_rejected(self):
        (self.root / 'raw.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            self.check()
        (self.root / 'raw.json').unlink()
        (self.root / 'raw.json').symlink_to('/etc/hosts')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.check()

    def test_stale_index_and_missing_observation_cannot_pass(self):
        with self.assertRaisesRegex(ValueError, 'binding mismatch'):
            self.check(expected_binding={'feature_index_digest': 'sha256:' + 'b' * 64})
        self.report['claims'][0]['evidence_refs'] = []
        with self.assertRaisesRegex(ValueError, 'raw evidence'):
            self.check()

    def test_unknown_claim_and_declared_success_over_failure_are_rejected(self):
        self.report['claims'][0]['id'] = 'different'
        with self.assertRaisesRegex(ValueError, 'coverage'):
            self.check()
        self.report['claims'][0]['id'] = 'denied'; self.report['claims'][0]['status'] = 'FAIL'
        with self.assertRaisesRegex(ValueError, 'summary'):
            self.check()

    def test_duplicate_keys_are_rejected(self):
        path = self.root / 'duplicate.json'; path.write_text('{"status":"FAIL","status":"PASS"}')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            load(path)


if __name__ == '__main__':
    unittest.main()
