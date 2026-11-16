import test from 'node:test'
import assert from 'node:assert/strict'
import { join } from 'node:path'
import { readFileSync } from 'node:fs'
import { fixture } from './helpers.mjs'
import { bootstrap } from '../skills/bootstrap-project-harness/scripts/lib/bootstrap.mjs'
import { apply } from '../skills/bootstrap-project-harness/scripts/lib/apply.mjs'
import { impact } from '../skills/bootstrap-project-harness/scripts/lib/features.mjs'
import { checkModel, explore, minimize, sequences } from '../skills/bootstrap-project-harness/scripts/lib/exploration.mjs'

test('deterministic sequences and bounded reduction preserve the observed predicate', async () => {
  assert.deepEqual(sequences(['read', 'revoke'], 37, 4, 8), sequences(['read', 'revoke'], 37, 4, 8))
  for (const size of [4, 8]) assert.ok(new Set(sequences(Array.from({ length: size }, (_, i) => 'action-' + i), 1, 100, 8).map(JSON.stringify)).size > 90)
  const result = await minimize(['noise', 'revoke', 'noise', 'read', 'noise'], async s => s.includes('revoke') && s.indexOf('read') > s.indexOf('revoke'))
  assert.deepEqual(result.sequence, ['revoke', 'read'])
  assert.equal((await minimize(['a', 'b'], async () => true, 0)).minimality, 'budget_limited')
})

test('state enumeration reports truncation and exposes shortest counterexample', () => {
  const model = { initial: 0, actions: ['increment'], next: s => s + 1, invariant: s => s > 2 ? 'bound exceeded' : null, assumptions: ['single counter'], mapping: { increment: 'fixture.increment' } }
  assert.equal(checkModel(model, { maxDepth: 1 }).status, 'INCOMPLETE')
  assert.deepEqual(checkModel(model, { maxDepth: 3 }).violations[0].trace, ['increment', 'increment', 'increment'])
  assert.equal(checkModel({ ...model, next: s => Math.min(2, s + 1) }).status, 'PASS')
})

test('real sequence runs retain failures, reduction, replay and binary evidence', async t => {
  const driver = `export async function launch(){return {}}
export async function doctor(){return {ready:true,instance_id:'isolated-sequence'}}
export async function drive(ctx,s){s.sequence=ctx.scenario.sequence;s.failed=s.sequence.includes('revoke')&&s.sequence.indexOf('read')>s.sequence.indexOf('revoke')}
export async function observe(ctx,s){const a=ctx.capture('trace','steps',s.sequence);const b=ctx.captureBytes('binary','raw',Buffer.from([1,2,3]));return [{id:'deny-old',status:s.failed?'FAIL':'PASS',expected:'read denied after revoke',actual:JSON.stringify(s),evidence_refs:[a,b]}]}
export async function cleanup(){}`
  const env = fixture(t, { 'package.json': '{"type":"module"}', 'README.md': 'revoke denies old read', 'driver.mjs': driver, 'fixture.json': '{}' })
  const index = { schema_version: 1, features: [{ id: 'access', title: 'Revoke', sources: ['README.md'], watch_paths: ['src/'], entries: [{ id: 'sequence', check_id: 'access-sequence', surface: 'http', location: 'synthetic driver boundary', driver: 'driver.mjs', checker_files: ['driver.mjs'], fixture_files: ['fixture.json'], claims: ['deny-old'], evidence_types: ['trace', 'binary'], prerequisites: ['synthetic fixture'], unsupported: ['real product'], node_args: [], timeout_ms: 10000, exploration: { actions: ['revoke', 'read'] } }] }] }
  const { plan } = bootstrap(env.root, { host: 'dual', authorizationRef: 'test', features: index })
  apply(env.root, plan, { stateDir: join(env.artifacts, 'apply'), acceptedDigest: plan.digest })
  const result = await explore(env.root, index, 'access', 'sequence', join(env.artifacts, 'explore'), { seed: 1, count: 2, length: 8, maxTrials: 12 })
  assert.equal(result.status, 'FAIL'); assert.equal(result.counterexamples.length, 1)
  const counterexample = JSON.parse(readFileSync(result.counterexamples[0], 'utf8'))
  assert.deepEqual(counterexample.sequence, ['revoke', 'read'])
  const replay = await explore(env.root, index, 'access', 'sequence', join(env.artifacts, 'replay'), { replay: result.counterexamples[0], maxTrials: 0 })
  assert.equal(replay.status, 'FAIL')
  const selected = impact(env.root, index, 'HEAD')
  assert.equal(selected.requires_full_verification, true)
  assert.ok(readFileSync(join(env.root, '.agents/skills/verify-project/SKILL.md'), 'utf8').includes('project-explore'))
})
