import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, existsSync, symlinkSync } from 'node:fs'
import { join } from 'node:path'
import { spawnSync } from 'node:child_process'
import { fixture, put, check, claim } from './helpers.mjs'
import { survey } from '../skills/bootstrap-project-harness/scripts/lib/survey.mjs'
import { bootstrap } from '../skills/bootstrap-project-harness/scripts/lib/bootstrap.mjs'
import { apply } from '../skills/bootstrap-project-harness/scripts/lib/apply.mjs'
import { doctor } from '../skills/bootstrap-project-harness/scripts/lib/doctor.mjs'
import { snapshot, readJson } from '../skills/bootstrap-project-harness/scripts/lib/core.mjs'

test('survey is read-only, records workspace packages and lock conflicts', t => {
  const { root } = fixture(t, { 'package.json': '{"name":"fixture","workspaces":["packages/*"]}', 'package-lock.json': '{}', 'yarn.lock': '', 'packages/child/package.json': '{"name":"child"}', 'AGENTS.md': 'Human instruction' })
  const before = snapshot(root)
  const result = survey(root)
  assert.equal(result.packages.length, 2)
  assert.equal(result.packages[0].package_manager, null)
  assert.equal(result.conflicts.length, 1)
  assert.equal(snapshot(root).content_digest, before.content_digest)
  assert.throws(() => bootstrap(root, { authorizationRef: 'test' }), /conflicts/)
  assert.equal(survey(root, { maxFiles: 1 }).scan.complete, false)
})
test('bootstrap preserves human instructions, runs independently and is idempotent', t => {
  const { root, artifacts } = fixture(t, { 'package.json': '{"name":"fixture"}', 'AGENTS.md': '# Existing\nHuman source of truth\n' })
  const options = { host: 'codex', authorizationRef: 'test fixture authorized', checks: [check('actual', claim())] }
  const { plan } = bootstrap(root, options)
  assert.equal(existsSync(join(root, '.harness')), false)
  apply(root, plan, { stateDir: artifacts, acceptedDigest: plan.digest })
  assert.match(readFileSync(join(root, 'AGENTS.md'), 'utf8'), /Human source of truth/)
  const run = spawnSync(process.execPath, ['scripts/project-verify.mjs', join(artifacts, 'runs')], { cwd: root, encoding: 'utf8' })
  assert.equal(run.status, 0, run.stderr + run.stdout)
  const receipt = readJson(JSON.parse(run.stdout).receipt)
  assert.equal(receipt.checks_passed, true)
  const second = bootstrap(root, options)
  assert.equal(second.plan.operations.length, 0)
  const report = doctor(root, readJson(join(root, '.harness/project.json')), { receipt })
  assert.equal(report.healthy, true)
  assert.equal(report.verified, false)
  put(root, 'docs/project-harness.md', 'Human edit')
  assert.throws(() => bootstrap(root, options), /manual merge/)
})
test('instruction aliases retain one source and unsafe aliases stop', t => {
  const { root, artifacts } = fixture(t, { 'CLAUDE.md': 'Original authoritative instructions\n' })
  symlinkSync('CLAUDE.md', join(root, 'AGENTS.md'))
  const { plan } = bootstrap(root, { authorizationRef: 'test' })
  assert.equal(plan.operations.filter(op => op.path === 'CLAUDE.md').length, 1)
  assert.equal(plan.operations.some(op => op.path === 'AGENTS.md'), false)
  const { root: other } = fixture(t)
  symlinkSync(join(root, 'CLAUDE.md'), join(other, 'AGENTS.md'))
  assert.throws(() => bootstrap(other, { authorizationRef: 'test' }), /external symlink/)
})
test('unknown stack retains missing checks instead of inventing success', t => {
  const { root, artifacts } = fixture(t, { 'main.py': 'print(1)' })
  const { plan } = bootstrap(root, { host: 'portable', authorizationRef: 'test' })
  apply(root, plan, { stateDir: artifacts, acceptedDigest: plan.digest })
  const manifest = readJson(join(root, '.harness/project.json'))
  assert.equal(manifest.checks.length, 0)
  assert.equal(doctor(root, manifest).healthy, false)
  const run = spawnSync(process.execPath, ['scripts/project-verify.mjs', artifacts], { cwd: root, encoding: 'utf8' })
  assert.notEqual(run.status, 0)
})
