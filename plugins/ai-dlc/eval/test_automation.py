"""Execution-regression tests: real subprocesses and real lifecycle guards."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/ai-dlc/scripts'
sys.path.insert(0, str(SCRIPTS))
import automation

ADAPTER = '''import hashlib,json,os
from pathlib import Path
q=json.loads(Path(os.environ['AIDLC_REQUEST']).read_text())
digest='sha256:'+hashlib.sha256(json.dumps(q,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
out=Path(os.environ['AIDLC_ATTEMPT'])
log=Path(os.environ['AIDLC_ROOT'])/'effects.json'
effects=json.loads(log.read_text()) if log.exists() else []
effects.append(q['stage']);log.write_text(json.dumps(effects))
(out/'raw.json').write_text(json.dumps({'observed':q['stage']}))
Path(os.environ['AIDLC_RESPONSE']).write_text(json.dumps({'schema_version':1,'request_digest':digest,'status':'complete','domain':'none','evidence':['raw.json'],'cost_microunits':0,'outcome':'confirmed'}))
'''


class AutomationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.repo = self.base / 'repo'; self.repo.mkdir()
        self.runtime = self.base / 'runtime'; self.adapter = self.base / 'adapter.py'; self.adapter.write_text(ADAPTER)
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        (self.repo / 'README.md').write_text('Synthetic unit fixture, no real issue provider.\n')
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        self.config = self.base / 'config.json'
        self.cfg = {'schema_version': 1, 'budget': {'max_attempts': 10, 'max_code_repairs': 2, 'max_environment_retries': 2, 'max_seconds': 60, 'max_same_failure': 2},
            'adapters': {name: {'argv': [sys.executable, str(self.adapter)], 'files': [str(self.adapter)], 'effect': 'external' if name == 'issue' else 'read', 'timeout_seconds': 10} for name in ['issue', 'discover', 'feedback']}}
        self.config.write_text(json.dumps(self.cfg))

    def command(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPTS / 'aidlc_state.py'), *args, '--root', str(self.runtime), '--slug', 'fixture-run'], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_completed_external_action_is_not_repeated_after_guard_rejects(self):
        self.command('init', '--title', 'Synthetic fixture', '--track', 'task')
        self.command('advance', 'track'); self.command('advance', 'issue')
        first = automation.run(self.repo, self.runtime, 'fixture-run', self.config)
        self.assertEqual(first['status'], 'waiting')
        self.assertIn('existing lifecycle guard', first['reason'])
        self.assertIn('issue.number set', first['attempts'][0]['advance']['unmet'])
        second = automation.run(self.repo, self.runtime, 'fixture-run', self.config)
        self.assertEqual(len(second['attempts']), 1)
        self.assertEqual(json.loads((self.runtime / 'effects.json').read_text()), ['issue'])

    def test_interrupted_external_action_without_reconciler_is_not_repeated(self):
        self.command('init', '--title', 'Synthetic fixture', '--track', 'task')
        self.command('advance', 'track'); self.command('advance', 'issue')
        self.adapter.write_text(ADAPTER.replace("'status':'complete'", "'status':'error'").replace("'domain':'none'", "'domain':'environment'"))
        first = automation.run(self.repo, self.runtime, 'fixture-run', self.config)
        self.assertIn('unknown', first['reason'])
        second = automation.run(self.repo, self.runtime, 'fixture-run', self.config)
        self.assertIn('reconciliation', second['reason'])
        self.assertEqual(len(second['attempts']), 1)

    def test_read_adapter_cannot_change_candidate(self):
        self.adapter.write_text(ADAPTER + "\nPath('README.md').write_text('changed')\n")
        result = automation.run(self.repo, self.runtime, 'fixture-run', self.config, 'cycle')
        self.assertEqual(result['status'], 'needs_review')

    def test_resume_consumes_same_attempt_budget(self):
        self.cfg['budget']['max_attempts'] = 1; self.config.write_text(json.dumps(self.cfg))
        first = automation.run(self.repo, self.runtime, 'fixture-run', self.config, 'cycle', 1)
        self.assertEqual(len(first['attempts']), 1)
        second = automation.run(self.repo, self.runtime, 'fixture-run', self.config, 'cycle')
        self.assertEqual(second['status'], 'budget_exhausted')
        self.assertEqual(len(second['attempts']), 1)

    def test_empty_response_and_replayed_digest_fail_closed(self):
        for suffix in ["Path(os.environ['AIDLC_RESPONSE']).write_text('{}')", "r=json.loads(Path(os.environ['AIDLC_RESPONSE']).read_text());r['request_digest']='sha256:'+'0'*64;Path(os.environ['AIDLC_RESPONSE']).write_text(json.dumps(r))"]:
            self.adapter.write_text(ADAPTER + '\n' + suffix + '\n')
            run_root = self.base / ('runtime-' + str(len(list(self.base.iterdir()))))
            result = automation.run(self.repo, run_root, 'fixture-run', self.config, 'cycle')
            self.assertEqual(result['status'], 'waiting'); self.assertEqual(result['attempts'][0]['result']['domain'], 'checker')

    def test_cli_preserves_nonzero_exit_for_waiting(self):
        self.cfg['adapters'] = {}; self.config.write_text(json.dumps(self.cfg))
        result = subprocess.run([sys.executable, str(SCRIPTS / 'aidlc_state.py'), 'automation', 'run', '--root', str(self.runtime), '--slug', 'fixture-run', '--repo', str(self.repo), '--config', str(self.config), '--mode', 'cycle'], capture_output=True)
        self.assertEqual(result.returncode, 1, result.stderr)

    def test_unpinned_entry_cannot_hide_behind_a_pinned_placeholder(self):
        mutable = self.repo / 'mutable.py'; mutable.write_text(ADAPTER)
        self.cfg['adapters']['discover']['argv'][1] = str(mutable)
        self.config.write_text(json.dumps(self.cfg))
        with self.assertRaisesRegex(ValueError, 'pinned operator file'):
            automation.run(self.repo, self.runtime, 'fixture-run', self.config, 'cycle')

    def test_pinning_interpreter_does_not_authorize_candidate_code(self):
        mutable = self.repo / 'mutable.py'; mutable.write_text(ADAPTER)
        self.cfg['adapters']['discover'].update(argv=[sys.executable, str(mutable)], files=[sys.executable])
        self.config.write_text(json.dumps(self.cfg))
        with self.assertRaisesRegex(ValueError, 'pinned operator file'):
            automation.run(self.repo, self.runtime, 'fixture-run', self.config, 'cycle')

    def test_safe_python_flags_preserve_frozen_script_entry(self):
        for value in self.cfg['adapters'].values(): value['argv'].insert(1, '-B')
        self.config.write_text(json.dumps(self.cfg))
        result = automation.run(self.repo, self.runtime, 'fixture-run', self.config, 'cycle')
        self.assertEqual(result['status'], 'complete')


if __name__ == '__main__': unittest.main()
