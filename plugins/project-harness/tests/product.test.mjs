import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { spawnSync } from 'node:child_process'
import { fixture, put } from './helpers.mjs'
import { bootstrap } from '../skills/bootstrap-project-harness/scripts/lib/bootstrap.mjs'
import { apply } from '../skills/bootstrap-project-harness/scripts/lib/apply.mjs'
import { validateFeatures } from '../skills/bootstrap-project-harness/scripts/lib/features.mjs'
import { runProduct, validateProduct } from '../skills/bootstrap-project-harness/scripts/lib/product.mjs'
import { calibrate } from '../skills/bootstrap-project-harness/scripts/lib/calibration.mjs'
import { readJson } from '../skills/bootstrap-project-harness/scripts/lib/core.mjs'
import { verify } from '../skills/bootstrap-project-harness/scripts/lib/verify.mjs'

const server = `import {createServer} from 'node:http';let allowed=true;
const app=createServer((req,res)=>{if(req.method==='DELETE'){allowed = false;res.end('revoked')}else{res.statusCode=allowed?200:403;res.end(allowed?'private':'denied')}});
app.listen(0,'127.0.0.1',()=>console.log(app.address().port));`
const driver = `import {once} from 'node:events';
let child,base,observed;
export async function launch(ctx){child=ctx.spawn(process.execPath,['server.mjs']);const [port]=await once(child.stdout,'data');base='http://127.0.0.1:'+port.toString().trim();return {pid:child.pid}}
export async function doctor(){const r=await fetch(base);if(r.status!==200)throw Error('initial read failed');return {ready:true,instance_id:String(child.pid)}}
export async function drive(){const r=await fetch(base,{method:'DELETE'});if(r.status!==200)throw Error('revoke request failed');const after=await fetch(base);observed={status:after.status,body:await after.text()}}
export async function observe(ctx){const ref=ctx.capture('http','readback',observed);return [{id:'denied',status:observed.status===403?'PASS':'FAIL',expected:'403 after revoke',actual:JSON.stringify(observed),evidence_refs:[ref]}]}
export async function cleanup(){if(child&&child.exitCode===null){const closed=once(child,'close');child.kill();await closed}}`
function setup(t) {
  const env = fixture(t, { 'package.json': '{"name":"product-fixture","type":"module"}', 'server.mjs': server, 'driver.mjs': driver, 'fixture.json': '{"initial":"allowed"}', 'README.md': 'Deleting access denies new reads.' })
  const index = { schema_version: 1, features: [{ id: 'access', title: 'Revoke access', sources: ['README.md'], entries: [{ id: 'http', check_id: 'revoke', surface: 'http', location: 'DELETE /', driver: 'driver.mjs', checker_files: ['driver.mjs'], fixture_files: ['fixture.json'], claims: ['denied'], evidence_types: ['http'], prerequisites: ['isolated HTTP server'], unsupported: ['UI'], node_args: [], timeout_ms: 10000 }] }] }
  const { plan } = bootstrap(env.root, { host: 'portable', authorizationRef: 'test', features: index })
  apply(env.root, plan, { stateDir: env.artifacts, acceptedDigest: plan.digest })
  return { ...env, index }
}
test('generated product entry drives HTTP, retains evidence after cleanup and joins the native check graph', async t => {
  const { root, artifacts, index } = setup(t)
  const result = spawnSync(process.execPath, ['scripts/project-verify.mjs', artifacts], { cwd: root, encoding: 'utf8' })
  assert.equal(result.status, 0, result.stdout + result.stderr)
  const receipt = readJson(JSON.parse(result.stdout).receipt)
  assert.equal(receipt.results[0].status, 'PASS')
  assert.equal(receipt.results[0].binding.feature_id, 'access')
  assert.equal(existsSync(join(receipt.results[0].artifacts, 'evidence/readback.json')), true)
  const consumer = new URL('../../ai-dlc/skills/ai-dlc/scripts', import.meta.url).pathname
  const check = `import sys,json;sys.path.insert(0,sys.argv[1]);import verification as v
r=json.load(open(sys.argv[2]));m=json.load(open(sys.argv[3]));f=json.load(open(sys.argv[4]))
issues=v.receipt_issues(r,m,sys.argv[5],f);print(json.dumps(issues));sys.exit(bool(issues))`
  const args = ['-B', '-c', check, consumer, JSON.parse(result.stdout).receipt, join(root, '.harness/project.json'), join(root, '.harness/features.json'), artifacts]
  assert.equal(spawnSync('python3', args).status, 0)
  const again = bootstrap(root, { host: 'portable', authorizationRef: 'test', features: index })
  assert.equal(again.plan.operations.length, 0)
  const broken = structuredClone(index); broken.features[0].entries[0].claims.push('unbound')
  assert.throws(() => validateFeatures(root, broken, readJson(join(root, '.harness/project.json')).checks), /exact claims/)
  // The top-level receipt still matches; the consumer must inspect transitive raw artifacts.
  writeFileSync(join(receipt.results[0].artifacts, 'evidence/readback.json'), '{"status":200}')
  assert.equal(spawnSync('python3', args).status, 1)
})
test('missing evidence, forged lifecycle and cleanup failure cannot pass', async t => {
  const { root, artifacts, index } = setup(t), out = join(artifacts, 'product')
  const result = await runProduct(root, index, 'access', 'http', out)
  assert.equal(result.status, 'PASS')
  const damaged = structuredClone(result); damaged.phases.pop()
  assert.throws(() => validateProduct(damaged, out, ['denied']), /lifecycle/)
  writeFileSync(join(out, result.evidence[0].path), '{}')
  assert.throws(() => validateProduct(result, out, ['denied']), /integrity/)
  put(root, 'broken.mjs', driver.replace('export async function cleanup()', 'export async function teardown()'))
  const broken = structuredClone(index); broken.features[0].entries[0].driver = 'broken.mjs'
  assert.equal((await runProduct(root, broken, 'access', 'http', join(artifacts, 'bad'))).status, 'ERROR')
})
test('native verification rejects a replayed product receipt from another candidate', async t => {
  const { root, artifacts, index } = setup(t), old = join(artifacts, 'old')
  assert.equal((await runProduct(root, index, 'access', 'http', old)).status, 'PASS')
  put(root, 'copy-old.mjs', `import {cpSync} from 'node:fs';cpSync(${JSON.stringify(old)},process.argv[2],{recursive:true})`)
  const manifest = readJson(join(root, '.harness/project.json'))
  manifest.checks[0].argv = ['copy-old.mjs', '{artifact_dir}']
  const result = await verify(root, manifest, { outputDir: join(artifacts, 'replay') })
  assert.equal(result.receipt.checks_passed, false)
  assert.equal(result.receipt.results[0].status, 'ERROR')
  assert.match(result.receipt.results[0].reason, /binding/)
})
test('standalone product command bounds a hung module import and retains an error receipt', t => {
  const { root, artifacts, index } = setup(t)
  put(root, 'driver.mjs', 'setInterval(()=>{},1000); await new Promise(()=>{});')
  index.features[0].entries[0].timeout_ms = 100
  put(root, '.harness/features.json', JSON.stringify(index))
  const result = spawnSync(process.execPath, ['scripts/project-product.mjs', 'access', 'http', join(artifacts, 'timeout')], { cwd: root, encoding: 'utf8', timeout: 4000 })
  assert.equal(result.status, 2, result.stderr)
  assert.equal(readJson(join(artifacts, 'timeout/product.json')).phases[0].status, 'ERROR')
})
test('indexed calibration plan cannot be replaced by an easier fault set', async t => {
  const { root, artifacts, index } = setup(t)
  const plan = { schema_version: 1, feature_id: 'access', entry_id: 'http', dependency_paths: [], required_faults: ['ignored-revoke'], mutations: [{ id: 'ignored-revoke', path: 'server.mjs', before: 'allowed = false', after: 'allowed = true', claim_id: 'denied' }] }
  put(root, 'reviewed-plan.json', JSON.stringify(plan))
  index.features[0].entries[0].calibration_plan = 'reviewed-plan.json'
  put(root, '.harness/features.json', JSON.stringify(index))
  const substituted = structuredClone(plan); substituted.mutations[0].after = 'allowed = 1'
  const path = join(artifacts, 'substituted.json'); writeFileSync(path, JSON.stringify(substituted))
  await assert.rejects(calibrate(root, path, join(artifacts, 'wrong-plan')), /indexed reviewed plan/)
})
test('calibration kills a business fault, rejects startup errors and remains independently verifiable', async t => {
  const { root, artifacts } = setup(t)
  const plan = { schema_version: 1, feature_id: 'access', entry_id: 'http', dependency_paths: [], required_faults: ['ignored-revoke'], mutations: [{ id: 'ignored-revoke', path: 'server.mjs', before: 'allowed = false', after: 'allowed = true', claim_id: 'denied' }] }
  const planPath = join(artifacts, 'plan.json'); writeFileSync(planPath, JSON.stringify(plan))
  const result = await calibrate(root, planPath, join(artifacts, 'calibration'))
  assert.equal(result.status, 'PASS', JSON.stringify(readJson(result.receipt)))
  assert.equal(readFileSync(join(root, 'server.mjs'), 'utf8'), server)
  const validator = new URL('../../trusted-acceptance/skills/accept-change/scripts/acceptance.py', import.meta.url)
  const checked = spawnSync('python3', ['-B', validator.pathname, 'validate-calibration', result.receipt, '--plan', planPath, '--features', join(root, '.harness/features.json')], { encoding: 'utf8' })
  assert.equal(checked.status, 0, checked.stderr + checked.stdout)
  const current = spawnSync('python3', ['-B', '-c', `import sys,json;sys.path.insert(0,sys.argv[1]);from verification_evidence import current_project_binding;print(json.dumps(current_project_binding(sys.argv[2],'access','http')))`, new URL('../../trusted-acceptance/skills/accept-change/scripts', import.meta.url).pathname, root], { encoding: 'utf8' })
  assert.equal(current.status, 0, current.stderr)
  assert.deepEqual(JSON.parse(current.stdout), readJson(join(artifacts, 'calibration/baseline/product.json')).binding)
  assert.equal(readFileSync(new URL('../../ai-dlc/skills/calibrate/scripts/verification_evidence.py', import.meta.url), 'utf8'), readFileSync(new URL('../../trusted-acceptance/skills/accept-change/scripts/verification_evidence.py', import.meta.url), 'utf8'))
  const forbidden = structuredClone(plan); forbidden.mutations[0].path = 'driver.mjs'
  writeFileSync(join(artifacts, 'forbidden.json'), JSON.stringify(forbidden))
  await assert.rejects(calibrate(root, join(artifacts, 'forbidden.json'), join(artifacts, 'forbidden')), /checker/)
  forbidden.mutations[0].path = './driver.mjs'
  writeFileSync(join(artifacts, 'alias.json'), JSON.stringify(forbidden))
  await assert.rejects(calibrate(root, join(artifacts, 'alias.json'), join(artifacts, 'alias')), /canonical/)
  const raw = readJson(result.receipt); raw.killed = 99; writeFileSync(result.receipt, JSON.stringify(raw))
  assert.notEqual(spawnSync('python3', ['-B', validator.pathname, 'validate-calibration', result.receipt, '--plan', planPath, '--features', join(root, '.harness/features.json')]).status, 0)
  plan.mutations[0].after = 'not valid syntax @'; writeFileSync(planPath, JSON.stringify(plan))
  const failed = await calibrate(root, planPath, join(artifacts, 'invalid-mutant'))
  assert.notEqual(failed.status, 'PASS')
  assert.equal(readJson(failed.receipt).cases[1].status, 'ERROR')
})
