import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'
import { fixture, check, claim, manifest } from './helpers.mjs'
import { describeEnvironment } from '../skills/bootstrap-project-harness/scripts/lib/environment.mjs'
import { verify } from '../skills/bootstrap-project-harness/scripts/lib/verify.mjs'

test('nested temporary directories expose enclosing Git and package scope', t => {
  const { root } = fixture(t, { 'package.json': '{"type":"module"}' })
  const temporary = join(root, 'tmp')
  mkdirSync(temporary)
  const result = describeEnvironment(root, { TMPDIR: temporary })
  assert.equal(result.temp_git_root, root)
  assert.deepEqual(result.temp_package_scope, { path: join(root, 'package.json'), type: 'module' })
  assert.equal(result.warnings.length, 2)
})
test('Git and module boundaries are distinct and environment values stay private', t => {
  const { root } = fixture(t, { 'package.json': '{"type":"module"}' })
  const temporary = join(root, 'tmp')
  mkdirSync(temporary)
  const initial = describeEnvironment(root, { TMPDIR: temporary, TEST_SECRET: 'do-not-leak' })
  const changed = describeEnvironment(root, { TMPDIR: temporary, GIT_CEILING_DIRECTORIES: root, TEST_SECRET: 'do-not-leak' })
  assert.equal(changed.temp_git_root, null)
  assert.equal(changed.temp_package_scope.type, 'module')
  assert.notEqual(initial.context_digest, changed.context_digest)
  assert.equal(JSON.stringify(initial).includes('do-not-leak'), false)
})
test('receipts bind per-check environment and surface nested temp limitations', async t => {
  const { root, artifacts } = fixture(t, { 'package.json': '{"type":"module"}' })
  const temporary = join(root, 'tmp')
  mkdirSync(temporary)
  const configured = check('behavior', claim(), { env: { TMPDIR: temporary, TEST_SECRET: 'private-value' } })
  const { receipt } = await verify(root, manifest([configured]), { outputDir: artifacts })
  assert.equal(receipt.checks_passed, true)
  assert.equal(receipt.results[0].environment.temporary_directory, temporary)
  assert.equal(receipt.results[0].environment.temp_git_root, root)
  assert.equal(receipt.limitations.filter(text => text.startsWith('behavior:')).length, 2)
  assert.equal(JSON.stringify(receipt).includes('private-value'), false)
})
