import test from 'node:test'
import assert from 'node:assert/strict'
import { join } from 'node:path'
import { readFileSync, writeFileSync } from 'node:fs'
import { fixture, put } from './helpers.mjs'
import { bootstrap } from '../skills/bootstrap-project-harness/scripts/lib/bootstrap.mjs'
import { apply } from '../skills/bootstrap-project-harness/scripts/lib/apply.mjs'
import { readJson, snapshot } from '../skills/bootstrap-project-harness/scripts/lib/core.mjs'
import { explore, sequences } from '../skills/bootstrap-project-harness/scripts/lib/exploration.mjs'
import { collect, qualify, promote, rollback, observe, regressions, learningStatus } from '../skills/bootstrap-project-harness/scripts/lib/learning.mjs'
import { verify } from '../skills/bootstrap-project-harness/scripts/lib/verify.mjs'

const server = `import {createServer} from 'node:http';import {readFileSync} from 'node:fs';const broken=JSON.parse(readFileSync('behavior.json')).broken;let allowed=true;const s=createServer((q,r)=>{if(q.method==='DELETE'){if(!broken)allowed=false;r.end('ok')}else{r.statusCode=allowed?200:403;r.end(allowed?'private':'denied')}});s.listen(0,'127.0.0.1',()=>console.log(s.address().port));`
const driver = `import {once} from 'node:events';
export async function launch(ctx){const child=ctx.spawn(process.execPath,['server.mjs']);const [data]=await once(child.stdout,'data');return {child,url:'http://127.0.0.1:'+data.toString().trim()}}
export async function doctor(ctx,s){return {ready:(await fetch(s.url)).status===200,instance_id:String(s.child.pid)}}
export async function drive(ctx,s){s.steps=[];let revoked=false;for(const a of ctx.scenario?.sequence??['revoke','read']){const r=await fetch(s.url,{method:a==='revoke'?'DELETE':'GET'});if(a==='revoke')revoked=true;s.steps.push({action:a,status:r.status,ok:a==='revoke'||r.status===(revoked?403:200)});await r.text()}}
export async function observe(ctx,s){const ref=ctx.capture('http','trace',s.steps);return [{id:'old-access-denied',status:s.steps.every(x=>x.ok)?'PASS':'FAIL',expected:'old reads denied after revoke',actual:JSON.stringify(s.steps),evidence_refs:[ref]}]}
export async function cleanup(ctx,s){if(s?.child.exitCode===null){const closed=once(s.child,'close');s.child.kill();await closed}}`
function setup(t, broken) {
  const env = fixture(t, { 'package.json': '{"type":"module"}', 'README.md': 'Revoke denies reads', 'behavior.json': JSON.stringify({ broken }), 'server.mjs': server, 'driver.mjs': driver, 'fixture.json': '{}' })
  const index = { schema_version: 1, features: [{ id: 'access', title: 'Access', sources: ['README.md'], entries: [{ id: 'sequence', check_id: 'access-sequence', surface: 'http', location: 'HTTP revoke/read', driver: 'driver.mjs', checker_files: ['driver.mjs'], fixture_files: ['fixture.json'], claims: ['old-access-denied'], evidence_types: ['http'], prerequisites: ['local HTTP'], unsupported: ['production accounts'], node_args: [], timeout_ms: 10000, exploration: { actions: ['read', 'revoke'] } }] }] }
  const { plan } = bootstrap(env.root, { host: 'portable', authorizationRef: 'test', features: index })
  apply(env.root, plan, { stateDir: join(env.artifacts, 'apply'), acceptedDigest: plan.digest })
  return { ...env, index }
}
async function learned(t) {
  const good = setup(t, false), bad = setup(t, true), store = join(good.artifacts, 'learning')
  const failure = join(bad.artifacts, 'failure')
  assert.equal((await explore(bad.root, bad.index, 'access', 'sequence', failure, { seed: 19, count: 4, length: 8, maxTrials: 12 })).status, 'FAIL')
  const captured = collect(good.root, good.index, join(failure, 'exploration.json'), store)
  const native = await verify(good.root, readJson(join(good.root, '.harness/project.json')), { outputDir: join(good.artifacts, 'native') })
  assert.equal(native.receipt.checks_passed, true)
  const policy = join(good.artifacts, 'policy.json')
  put(good.artifacts, 'policy.json', JSON.stringify({ schema_version: 1, authority: 'local_advisory', project_root: good.root, store, entries: ['access/sequence'], allowed_operations: ['append-regression', 'rollback-regression'], max_active_cases: 2, expires_at: Date.now() / 1000 + 3600, authorization_ref: 'temporary fixture only' }))
  return { good, bad, store, captured, native, failure, policy }
}
test('real failure learns an additive regression, improves detection, records recurrence and rolls back without deleting history', async t => {
  const { good, bad, store, captured, native, failure, policy } = await learned(t)
  const before = snapshot(good.root)
  const repeated = collect(good.root, good.index, join(failure, 'exploration.json'), store)
  assert.equal(repeated.case_id, captured.case_id); assert.equal(repeated.revision, captured.revision)
  const qualified = await qualify(good.root, good.index, store, captured.case_id, bad.root, native.path, join(good.artifacts, 'qualification'))
  assert.equal(qualified.status, 'QUALIFIED', qualified.error)
  const activated = promote(good.root, good.index, store, qualified.qualification, policy)
  assert.equal(promote(good.root, good.index, store, qualified.qualification, policy).revision, activated.revision)
  let seed = 0; while (sequences(['read', 'revoke'], seed, 1, 1)[0][0] !== 'read') seed++
  const options = { seed, count: 1, length: 1, maxTrials: 0 }
  assert.equal((await explore(bad.root, bad.index, 'access', 'sequence', join(bad.artifacts, 'before-learning'), options)).status, 'PASS')
  const afterDir = join(bad.artifacts, 'after-learning'), fixedDir = join(good.artifacts, 'after-learning')
  const after = await explore(bad.root, bad.index, 'access', 'sequence', afterDir, { ...options, corpus: store })
  assert.equal(after.status, 'FAIL'); assert.equal(after.attempts[0].purpose, 'learned-regression')
  assert.equal(observe(bad.root, bad.index, store, join(afterDir, 'exploration.json')).active_cases, 1)
  const fixed = await explore(good.root, good.index, 'access', 'sequence', fixedDir, { ...options, corpus: store })
  assert.equal(fixed.status, 'PASS'); assert.equal(fixed.attempts.length, 2, 'new random exploration was not replaced')
  const fixedPath = join(fixedDir, 'exploration.json'), original = readFileSync(fixedPath)
  const forged = readJson(fixedPath); forged.corpus.cases[0].sequence = ['read']; writeFileSync(fixedPath, JSON.stringify(forged))
  assert.throws(() => observe(good.root, good.index, store, fixedPath), /regression changed/)
  writeFileSync(fixedPath, original)
  observe(good.root, good.index, store, join(fixedDir, 'exploration.json'))
  assert.equal(learningStatus(good.root, store).metrics.observed_runs, 2)
  rollback(good.root, store, captured.case_id, policy, 'Temporary fixture rollback rehearsal')
  assert.equal(regressions(good.root, good.index, 'access', 'sequence', store).cases.length, 0)
  const status = learningStatus(good.root, store)
  assert.equal(status.metrics.rollbacks, 1); assert.equal(status.events.filter(e => e.kind === 'observed').length, 2)
  assert.equal(readJson(join(store, 'cases', captured.case_id, 'case.json')).evidence.length > 0, true)
  assert.equal(snapshot(good.root).content_digest, before.content_digest)
})
test('unqualified, stale, tampered and out-of-scope learning cannot become active', async t => {
  const { good, bad, store, captured, native, failure, policy } = await learned(t)
  const qualified = await qualify(good.root, good.index, store, captured.case_id, bad.root, native.path, join(good.artifacts, 'qualification'))
  const grant = readJson(policy)
  for (const change of [{ expires_at: 1 }, { entries: ['other/entry'] }, { allowed_operations: [] }, { authority: 'accepted_for_stage' }]) {
    writeFileSync(policy, JSON.stringify({ ...grant, ...change }))
    assert.throws(() => promote(good.root, good.index, store, qualified.qualification, policy), /authorization|scope|outside policy/)
  }
  writeFileSync(policy, JSON.stringify(grant))
  put(good.root, 'behavior.json', '{"broken":true}')
  assert.throws(() => promote(good.root, good.index, store, qualified.qualification, policy), /exact qualified candidate/)
  put(good.root, 'behavior.json', '{"broken":false}')
  promote(good.root, good.index, store, qualified.qualification, policy)
  put(good.root, 'driver.mjs', driver + '\n// changed checker')
  assert.throws(() => regressions(good.root, good.index, 'access', 'sequence', store), /stale/)
  put(good.root, 'driver.mjs', driver)
  const q = readJson(qualified.qualification), raw = q.observations[1].receipt.path
  writeFileSync(raw, '{}')
  assert.throws(() => regressions(good.root, good.index, 'access', 'sequence', store), /changed/)
  assert.equal(learningStatus(good.root, store).active.length, 1, 'corruption never silently deactivates a regression')
  const old = readJson(join(failure, 'exploration.json')); old.attempts[1].purpose = 'explore'; writeFileSync(join(failure, 'exploration.json'), JSON.stringify(old))
  assert.throws(() => collect(good.root, good.index, join(failure, 'exploration.json'), join(good.artifacts, 'unconfirmed')), /Missing original/)
  assert.throws(() => regressions(good.root, good.index, 'access', 'sequence', join(good.artifacts, 'missing')), /missing/)
})
test('wrong negative candidate and changed source observations are rejected before qualification', async t => {
  const { good, bad, store, captured, native, failure } = await learned(t)
  put(bad.root, 'README.md', 'changed failed candidate')
  await assert.rejects(qualify(good.root, good.index, store, captured.case_id, bad.root, native.path, join(good.artifacts, 'wrong-negative')), /observed failing candidate/)
  const report = readJson(join(failure, 'exploration.json')), first = readJson(report.attempts[0].receipt)
  const raw = join(report.attempts[0].receipt, '..', first.evidence[0].path)
  writeFileSync(raw, 'tampered')
  assert.throws(() => collect(good.root, good.index, join(failure, 'exploration.json'), join(good.artifacts, 'tampered-source')), /integrity/)
})
