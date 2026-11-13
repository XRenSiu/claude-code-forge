import test from 'node:test'
import assert from 'node:assert/strict'
import { join } from 'node:path'
import { fixture, check, claim, manifest, put } from './helpers.mjs'
import { verify, isCurrentReceipt, runProcess } from '../skills/bootstrap-project-harness/scripts/lib/verify.mjs'
import { parseReport } from '../skills/bootstrap-project-harness/scripts/lib/reporters.mjs'
import { validateChecks } from '../skills/bootstrap-project-harness/scripts/lib/contracts.mjs'

test('execution graph respects prerequisites and collects independent failure', async t => {
  const { root, artifacts } = fixture(t)
  const bindings = manifest([check('prerequisite', claim('FAIL')), check('dependent', claim(), { depends_on: ['prerequisite'] }), check('independent', claim())])
  const { receipt } = await verify(root, bindings, { outputDir: artifacts })
  assert.deepEqual(Object.fromEntries(receipt.results.map(r => [r.id, r.status])), { prerequisite: 'FAIL', independent: 'PASS', dependent: 'NOT_RUN' })
  assert.equal(receipt.execution_complete, false)
  assert.equal(receipt.checks_passed, false)
})
test('real pass/failure are distinct from execution errors', async t => {
  const { root, artifacts } = fixture(t)
  const bindings = manifest([check('positive', claim()), check('negative', claim('FAIL'))])
  const { receipt } = await verify(root, bindings, { outputDir: artifacts })
  assert.equal(receipt.execution_complete, true)
  assert.equal(receipt.checks_passed, false)
  assert.equal(receipt.results[1].status, 'FAIL')
})
test('candidate writes and old receipts invalidate success', async t => {
  const { root, artifacts } = fixture(t, { 'source.txt': 'before' })
  const bindings = manifest([check('passing', claim())])
  const { receipt } = await verify(root, bindings, { outputDir: artifacts })
  assert.equal(receipt.checks_passed, true)
  assert.equal(isCurrentReceipt(root, bindings, receipt), true)
  put(root, 'source.txt', 'new')
  assert.equal(isCurrentReceipt(root, bindings, receipt), false)
  const changing = manifest([check('formatter', `require('node:fs').writeFileSync('source.txt','formatted');${claim()}`, { effects: 'writes-project' })])
  const result = await verify(root, changing, { outputDir: artifacts })
  assert.equal(result.receipt.execution_complete, false)
  assert.equal(result.receipt.checks_passed, false)
})
test('timeouts, process failures, malformed/missing reports and exit-only never pass', async t => {
  const { root, artifacts } = fixture(t)
  const bindings = manifest([
    check('timeout', 'setInterval(()=>{},100)', { timeout_ms: 60 }),
    check('start-error', '', { executable: '/nonexistent-harness-test-executable' }),
    check('invalid-json', 'console.log("not json")'),
    check('missing-file', claim(), { report_file: 'missing.json' }),
    check('exit-only', '', { reporter: 'exit-code' })
  ])
  const { receipt } = await verify(root, bindings, { outputDir: artifacts })
  assert.deepEqual(receipt.results.map(r => r.status), ['ERROR', 'ERROR', 'ERROR', 'ERROR', 'NOT_RUN'])
  assert.equal(receipt.checks_passed, false)
})
test('cancellation stops active work and suppresses dependent work', async t => {
  const { root, artifacts } = fixture(t)
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 80)
  t.after(() => clearTimeout(timer))
  const { receipt } = await verify(root, manifest([check('long', 'setInterval(()=>{},100)'), check('after', claim(), { depends_on: ['long'] })]), { outputDir: artifacts, signal: controller.signal })
  assert.deepEqual(receipt.results.map(r => r.status), ['ERROR', 'NOT_RUN'])
})
test('zero checks, all inapplicable and wrong Node are incomplete coverage', async t => {
  const { root, artifacts } = fixture(t)
  for (const bindings of [manifest([]), manifest([check('different-platform', claim(), { platforms: ['nonexistent-os'] })]), { ...manifest([check('node', claim())]), node_major: 999 }]) {
    const { receipt } = await verify(root, bindings, { outputDir: artifacts })
    assert.equal(receipt.checks_passed, false)
  }
})
test('JSON and TAP reporters reject missing and zero-denominator evidence', () => {
  const vitest = check('tests', '', { reporter: 'vitest-json' })
  for (const data of [{}, { numTotalTests: 1, numPassedTests: 1, numFailedTests: 0, testResults: [] }]) assert.equal(parseReport(vitest, JSON.stringify(data), 0).status, 'ERROR')
  const empty = { numTotalTests: 0, numPassedTests: 0, numFailedTests: 0, testResults: [] }
  assert.equal(parseReport(vitest, JSON.stringify(empty), 0).status, 'NOT_RUN')
  assert.equal(parseReport(vitest, JSON.stringify({ numTotalTests: 1, numPassedTests: 0, numFailedTests: 0, testResults: [{ assertionResults: [{ status: 'pending' }] }] }), 0).status, 'NOT_RUN')
  assert.equal(parseReport(check('lint', '', { reporter: 'eslint-json' }), '[]', 0).status, 'NOT_RUN')
  assert.equal(parseReport(check('tap', '', { reporter: 'tap' }), '# tests 1\n# pass 1\n', 0).status, 'ERROR')
  assert.equal(parseReport(check('tap', '', { reporter: 'tap' }), '# Subtest: actual behavior\n# tests 1\n# pass 1\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n', 0).status, 'PASS')
  assert.equal(parseReport(check('tap', '', { reporter: 'tap' }), '# Subtest: empty.test.mjs\n# tests 1\n# pass 1\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n', 0).status, 'NOT_RUN')
})
test('claims require exact scheduled matrix and successful process result', () => {
  const binding = check('claims', '')
  for (const claims of [[], [{ id: 'other', status: 'PASS' }], [{ id: 'behavior', status: 'PASS' }, { id: 'behavior', status: 'PASS' }]]) assert.equal(parseReport(binding, JSON.stringify({ schema_version: 1, complete: true, examined: 1, claims }), 0).status, 'ERROR')
  const good = JSON.stringify({ schema_version: 1, complete: true, examined: 1, claims: [{ id: 'behavior', status: 'PASS' }] })
  assert.equal(parseReport(binding, good, 2).status, 'ERROR')
})
test('check DAG rejects missing, cyclic and duplicate dependencies', () => {
  assert.throws(() => validateChecks([check('a', claim()), check('a', claim())]), /Duplicate/)
  assert.throws(() => validateChecks([check('a', claim(), { depends_on: ['missing'] })]), /Missing/)
  assert.throws(() => validateChecks([check('a', claim(), { depends_on: ['b'] }), check('b', claim(), { depends_on: ['a'] })]), /cycle/)
})
