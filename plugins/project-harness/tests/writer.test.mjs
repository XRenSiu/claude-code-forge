import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync, symlinkSync, mkdirSync } from 'node:fs'
import { join } from 'node:path'
import { fixture, operation, proposal, put } from './helpers.mjs'
import { makePlan, planDigest } from '../skills/bootstrap-project-harness/scripts/lib/plan.mjs'
import { apply, recover } from '../skills/bootstrap-project-harness/scripts/lib/apply.mjs'
import { fileState, hash, readJson, writeJson } from '../skills/bootstrap-project-harness/scripts/lib/core.mjs'

test('applies additions/updates/deletions, preserves unrelated content and repeats idempotently', t => {
  const { root, artifacts } = fixture(t, { 'owned.txt': 'before', 'human.txt': 'keep', 'remove.txt': 'obsolete' })
  const plan = makePlan(root, proposal([operation(root, 'owned.txt', 'after'), operation(root, 'new.txt', 'new'), operation(root, 'remove.txt', null)]))
  const opts = { stateDir: artifacts, acceptedDigest: plan.digest }
  assert.equal(apply(root, plan, opts).written, 3)
  assert.equal(readFileSync(join(root, 'human.txt'), 'utf8'), 'keep')
  assert.equal(readFileSync(join(root, 'owned.txt'), 'utf8'), 'after')
  assert.equal(existsSync(join(root, 'remove.txt')), false)
  assert.equal(apply(root, plan, opts).already_applied, 3)
})
test('stale plan rejects all writes before mutation', t => {
  const { root, artifacts } = fixture(t, { 'a': 'a', 'b': 'b' })
  const plan = makePlan(root, proposal([operation(root, 'a', 'new a'), operation(root, 'b', 'new b')]))
  put(root, 'b', 'concurrent user edit')
  assert.throws(() => apply(root, plan, { stateDir: artifacts, acceptedDigest: plan.digest }), /Conflict/)
  assert.equal(readFileSync(join(root, 'a'), 'utf8'), 'a')
  assert.equal(readFileSync(join(root, 'b'), 'utf8'), 'concurrent user edit')
})
test('mid-transaction failure restores only this transaction', t => {
  const { root, artifacts } = fixture(t, { 'a': 'before' })
  const plan = makePlan(root, proposal([operation(root, 'a', 'after'), operation(root, 'b', 'new')]))
  assert.throws(() => apply(root, plan, { stateDir: artifacts, acceptedDigest: plan.digest, failAfter: 1 }), /rolled-back/)
  assert.equal(readFileSync(join(root, 'a'), 'utf8'), 'before')
  assert.equal(existsSync(join(root, 'b')), false)
  assert.equal(readJson(join(artifacts, `journal-${plan.digest}.json`)).status, 'rolled-back')
})
test('crash recovery handles intent and preserves concurrent user edits', t => {
  const { root, artifacts } = fixture(t, { 'a': 'before a', 'b': 'before b' })
  const beforeA = fileState(join(root, 'a')), beforeB = fileState(join(root, 'b'))
  put(root, 'a', 'written a'); put(root, 'b', 'user b')
  const journalFile = join(artifacts, 'crash.json')
  writeJson(journalFile, { schema_version: 1, root, status: 'applying', entries: [
    { path: 'a', before: beforeA, after_hash: hash('written a'), status: 'intent' },
    { path: 'b', before: beforeB, after_hash: hash('written b'), status: 'written' }
  ] })
  const result = recover(root, journalFile)
  assert.equal(result.status, 'recovery-conflict')
  assert.deepEqual(result.recovery_conflicts, ['b'])
  assert.equal(readFileSync(join(root, 'a'), 'utf8'), 'before a')
  assert.equal(readFileSync(join(root, 'b'), 'utf8'), 'user b')
})
test('path escapes, aliases and metadata are not writable', t => {
  const { root, artifacts } = fixture(t)
  for (const path of ['../outside', '/tmp/outside', '.git/config', 'a/../../outside', 'a\\b']) {
    assert.throws(() => makePlan(root, proposal([{ path, content: 'x', before_hash: null, reason: 'x', source: 'x' }])), /path|Path/)
  }
  symlinkSync(artifacts, join(root, 'linked'))
  assert.throws(() => makePlan(root, proposal([{ path: 'linked/a', content: 'x', before_hash: null, reason: 'x', source: 'x' }])), /symlink/)
  assert.throws(() => makePlan(root, proposal([operation(root, 'a', 'one'), operation(root, 'a', 'two')])), /Duplicate/)
  assert.throws(() => makePlan(root, proposal([operation(root, 'a', 'one'), operation(root, 'a/b', 'two')])), /Overlapping/)
})
test('review digest, stale proposal, schema and project lock are enforced', t => {
  const { root, artifacts } = fixture(t, { 'a': 'before' })
  const plan = makePlan(root, proposal([operation(root, 'a', 'after')]))
  assert.throws(() => apply(root, plan, { stateDir: artifacts, acceptedDigest: 'wrong' }), /reviewed/)
  const changed = structuredClone(plan); changed.operations[0].content = 'different'
  assert.throws(() => apply(root, changed, { stateDir: artifacts, acceptedDigest: plan.digest }), /digest/)
  assert.throws(() => makePlan(root, proposal([{ ...operation(root, 'a', 'x'), before_hash: null }])), /Stale/)
  mkdirSync(join(root, '.harness-write-lock'))
  assert.throws(() => apply(root, plan, { stateDir: artifacts, acceptedDigest: plan.digest }), /lock exists/)
  assert.equal(readFileSync(join(root, 'a'), 'utf8'), 'before')
})
