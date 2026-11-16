import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from demo import make_case
from protocol import digest, ProtocolError
from service import Control


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'control.json').write_text(json.dumps({'schema_version': 1, 'mode': 'local-pilot', 'principals': [
            {'id': 'submitter', 'token_sha256': hashlib.sha256(b'submit').hexdigest(), 'roles': ['submit', 'cancel'], 'projects': ['synthetic-sharing']},
            {'id': 'collector', 'token_sha256': hashlib.sha256(b'collect').hexdigest(), 'roles': ['collect'], 'projects': ['synthetic-sharing']}]}))
        self.control = Control(self.root)
        self.case, self.request = make_case(self.root / 'evidence')
        bundle = self.root / 'bundle'; bundle.mkdir(); checker = bundle / 'checker.py'; checker.write_text('# synthetic control fixture\n')
        files = [str(checker)]
        binding = self.request['binding']
        binding['check_bundle_digest'] = digest({str(checker): hashlib.sha256(checker.read_bytes()).hexdigest()})
        recipe = {'candidate_argv': ['node', 'fixture.mjs'], 'candidate_workdir': '/app', 'collector_argv': ['python3', str(checker)], 'observer_image': binding['artifact_digest']}
        import service
        binding['adapter_digest'] = digest({**recipe, 'worker_sha256': hashlib.sha256(Path(service.__file__).with_name('docker_worker.py').read_bytes()).hexdigest()})
        self.case['policy'].update(check_bundle_digest=binding['check_bundle_digest'], adapter_digest=binding['adapter_digest'])
        self.spec = {'binding': binding, 'contract': self.case['contract'], 'policy': self.case['policy'],
            'image': binding['artifact_digest'], 'collector_files': files, **recipe,
            'authorization_expires_at': int(time.time()) + 3600,
            'budget': {'max_code_repairs': 2, 'max_environment_retries': 2, 'max_cost_microunits': 10, 'deadline_at': int(time.time()) + 3600}}
        self.control.register(self.spec)

    def submit(self, key='one'):
        self.request['idempotency_key'] = key
        return self.control.submit(self.request, 'submit')

    def collect(self, passed=True):
        job = self.control.claim('collect', 'synthetic-sharing')
        attempt = copy.deepcopy(self.case['run']['attempts'][0]); attempt['binding'] = copy.deepcopy(self.request['binding'])
        if not passed:
            attempt['checks'][1].update(status='fail', failure_type='implementation', reproduction_ref='fixture#revoke')
        return self.control.complete(job['run_id'], job['fence'], 'collect', attempt, 0)

    def test_durable_idempotency_and_conflicting_payload(self):
        first = self.submit(); self.control = Control(self.root)
        self.assertEqual(first['run_id'], self.submit()['run_id'])
        self.request['binding']['candidate_sha'] = 'a' * 40
        with self.assertRaisesRegex(ProtocolError, 'idempotency conflict'):
            self.submit()

    def test_role_and_project_isolation(self):
        with self.assertRaises(ProtocolError): self.control.submit(self.request, 'collect')
        with self.assertRaises(ProtocolError): self.control.claim('submit', 'synthetic-sharing')
        with self.assertRaises(ProtocolError): self.control.claim('collect', 'foreign-project')

    def test_complete_is_local_only_and_cancel_revokes_readback(self):
        run = self.submit()['run_id']; decision = self.collect()
        self.assertEqual(decision['verification_decision'], 'eligible')
        self.assertEqual(self.control.result(run, 'submit')['verification_decision'], 'blocked')
        self.assertEqual(self.control.result(run, 'submit', True)['authority'], 'local_advisory')
        self.control.cancel('synthetic-sharing', 'SHARE-123', 'submit')
        self.assertEqual(self.control.result(run, 'submit')['verification_decision'], 'obsolete')

    def test_cancellation_fences_late_collector(self):
        self.submit(); job = self.control.claim('collect', 'synthetic-sharing')
        self.control.cancel('synthetic-sharing', 'SHARE-123', 'submit')
        with self.assertRaisesRegex(ProtocolError, 'stale worker'):
            self.control.complete(job['run_id'], job['fence'], 'collect', self.case['run']['attempts'][0], 0)

    def test_expired_lease_is_reassigned_with_fence_and_budget(self):
        self.submit(); old = self.control.claim('collect', 'synthetic-sharing')
        with self.control.transaction() as db: db.execute('UPDATE runs SET lease_until=0')
        new = self.control.claim('collect', 'synthetic-sharing')
        self.assertGreater(new['fence'], old['fence'])
        with self.assertRaises(ProtocolError): self.control.complete(old['run_id'], old['fence'], 'collect', self.case['run']['attempts'][0], 0)
        with self.control.transaction() as db:
            self.assertEqual(db.execute('SELECT retries FROM tasks').fetchone()['retries'], 1)

    def test_same_binding_failure_cannot_be_washed_by_new_request(self):
        self.submit('failure'); self.assertEqual(self.collect(False)['verification_decision'], 'needs_repair')
        self.submit('lucky-rerun'); self.assertEqual(self.collect(True)['verification_decision'], 'needs_review')

    def test_raw_evidence_is_reopened(self):
        self.submit(); (self.root / 'evidence/revoke-new-read.json').write_text('tampered')
        self.assertEqual(self.collect()['verification_decision'], 'blocked')

    def test_policy_or_bundle_cannot_change_under_same_binding(self):
        altered = copy.deepcopy(self.spec); altered['budget']['max_code_repairs'] = 100
        with self.assertRaises(ProtocolError): self.control.register(altered)
        Path(self.spec['collector_files'][0]).write_text('changed')
        with self.assertRaises(ProtocolError): self.control.register(self.spec)

    def test_candidate_cannot_supply_collector_or_approval(self):
        request = {**self.request, 'case': self.case}
        with self.assertRaises(ProtocolError): self.control.submit(request, 'submit')

    def test_http_body_rejects_ambiguous_json(self):
        from service import parse_body
        for body in ['{"binding":1,"binding":2}', '{"cost":NaN}', '[]']:
            with self.assertRaises(ProtocolError): parse_body(body)

    def test_unknown_cost_cannot_publish(self):
        self.submit(); job = self.control.claim('collect', 'synthetic-sharing')
        with self.assertRaisesRegex(ProtocolError, 'measured cost'):
            self.control.complete(job['run_id'], job['fence'], 'collect', self.case['run']['attempts'][0], None)

    def test_mutable_collector_entry_is_rejected(self):
        altered = copy.deepcopy(self.spec)
        altered['collector_argv'] = ['python3', '/candidate/mutable.py']
        with self.assertRaisesRegex(ProtocolError, 'frozen bundle'):
            self.control.register(altered)

    def test_worker_preflight_failure_is_durable_environment_evidence(self):
        import docker_worker
        run = self.submit()['run_id']
        with patch.object(docker_worker, 'docker', side_effect=ProtocolError('image missing')), patch.object(docker_worker.subprocess, 'run'):
            result = docker_worker.run_job(self.control, 'collect', 'synthetic-sharing')
        self.assertEqual(result['evaluation']['verification_decision'], 'infrastructure_blocked')
        self.assertEqual(self.control.result(run, 'submit')['state'], 'complete')
        with self.control.transaction() as db:
            self.assertEqual(db.execute('SELECT retries FROM tasks').fetchone()['retries'], 1)


if __name__ == '__main__': unittest.main()
