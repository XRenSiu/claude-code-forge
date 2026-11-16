import { existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { pathToFileURL } from 'node:url'
import { spawn } from 'node:child_process'
import { digest, hash, inside, now, projectRoot, safePath, snapshot, writeJson } from './core.mjs'
import { featureEntry, filesDigest } from './features.mjs'

const require = (value, message) => { if (!value) throw new Error(message) }
const phases = ['launch', 'doctor', 'drive', 'observe', 'cleanup']
export function productBinding(root, index, featureId, entryId, candidateDigest) {
  const { entry } = featureEntry(root, index, featureId, entryId)
  return { feature_id: featureId, entry_id: entryId, check_id: entry.check_id, candidate_digest: 'sha256:' + candidateDigest,
    feature_index_digest: 'sha256:' + digest(index), checker_digest: filesDigest(root, [entry.driver, ...entry.checker_files]), fixture_digest: filesDigest(root, entry.fixture_files),
    environment_digest: 'sha256:' + digest({ node: process.versions.node, platform: process.platform, arch: process.arch, node_args: entry.node_args }) }
}
export function evidenceFile(root, name) {
  const path = safePath(root, name)
  let cursor = root
  for (const part of relative(root, path).split('/')) { cursor = join(cursor, part); require(!lstatSync(cursor).isSymbolicLink(), 'Evidence symlinks are not supported') }
  require(lstatSync(path).isFile() && lstatSync(path).size <= 8 * 1024 * 1024, 'Evidence must be a bounded regular file')
  return path
}
export function validateProduct(report, root, expectedClaims) {
  require(report?.schema_version === 1 && report.evidence_kind === 'product-observation' && report.authority === 'project-self-check', 'Unsupported product receipt')
  require(report.binding && ['candidate_digest', 'feature_index_digest', 'checker_digest', 'fixture_digest', 'environment_digest'].every(k => /^sha256:[a-f0-9]{64}$/.test(report.binding[k])), 'Missing product binding')
  require(Array.isArray(report.phases) && new Set(report.phases.map(p => p.name)).size === report.phases.length, 'Invalid lifecycle phases')
  require(Array.isArray(report.claims) && Array.isArray(report.evidence), 'Missing product observations')
  const ids = report.claims.map(c => c.id)
  require(new Set(ids).size === ids.length, 'Duplicate product claim')
  const evidenceIds = new Set()
  for (const item of report.evidence) {
    require(typeof item.id === 'string' && !evidenceIds.has(item.id), 'Duplicate evidence ID'); evidenceIds.add(item.id)
    const data = readFileSync(evidenceFile(root, item.path))
    require(data.length > 0 && item.size_bytes === data.length && item.digest === 'sha256:' + hash(data), 'Product evidence integrity mismatch')
  }
  if (report.status === 'ERROR') return { status: 'ERROR', reason: report.error || 'Product lifecycle incomplete' }
  require(report.phases.length === phases.length && phases.every((name, i) => report.phases[i].name === name && report.phases[i].status === 'PASS'), 'Product lifecycle incomplete')
  require(report.candidate_unchanged === true, 'Candidate changed during product verification')
  require(expectedClaims?.length && ids.length === expectedClaims.length && expectedClaims.every(id => ids.includes(id)), 'Product claim coverage mismatch')
  for (const claim of report.claims) {
    require(['PASS', 'FAIL'].includes(claim.status) && typeof claim.expected === 'string' && claim.expected.trim() && typeof claim.actual === 'string' && claim.actual.trim(), 'Product claim must include observed and expected results')
    require(Array.isArray(claim.evidence_refs) && claim.evidence_refs.length > 0 && claim.evidence_refs.every(id => evidenceIds.has(id)), 'Product claim has no raw evidence')
  }
  const status = report.claims.every(c => c.status === 'PASS') ? 'PASS' : 'FAIL'
  require(report.status === status, 'Product summary contradicts observations')
  return { status, examined: ids.length, passed: report.claims.filter(c => c.status === 'PASS').length, failed: report.claims.filter(c => c.status === 'FAIL').length, binding: report.binding }
}

export async function runProduct(rootPath, index, featureId, entryId, outputDir, { signal } = {}) {
  const root = projectRoot(rootPath), { entry } = featureEntry(root, index, featureId, entryId)
  require(outputDir && !inside(root, resolve(outputDir)), 'Product evidence must be outside the project')
  mkdirSync(outputDir, { recursive: true }); const out = realpathSync(outputDir)
  require(!inside(root, out) && !existsSync(join(out, 'product.json')), 'Evidence output resolves inside project or already contains a receipt')
  const scratch = realpathSync(mkdtempSync(join(tmpdir(), 'product-verification-')))
  const controller = new AbortController(), children = new Set()
  const abort = () => controller.abort()
  signal?.addEventListener('abort', abort, { once: true })
  if (signal?.aborted) abort()
  const timer = setTimeout(abort, entry.timeout_ms)
  const before = snapshot(root)
  const report = { schema_version: 1, evidence_kind: 'product-observation', authority: 'project-self-check', created_at: now(),
    binding: productBinding(root, index, featureId, entryId, before.content_digest),
    phases: [], claims: [], evidence: [], status: 'ERROR', candidate_unchanged: false, limitations: entry.unsupported }
  let instance, driver, closed = false
  const context = { root, scratch, signal: controller.signal, entry,
    spawn(executable, argv, options = {}) {
      require(!closed && !controller.signal.aborted, 'Product lifecycle closed or cancelled')
      const environment = Object.fromEntries(['PATH', 'HOME', 'TMPDIR', 'TMP', 'TEMP', 'LANG', 'LC_ALL', 'TZ', 'SystemRoot'].filter(k => process.env[k] !== undefined).map(k => [k, process.env[k]]))
      const child = spawn(executable, argv, { cwd: root, stdio: ['ignore', 'pipe', 'pipe'], ...options, env: { ...environment, ...options.env }, shell: false, detached: false })
      children.add(child); return child
    },
    capture(type, name, value) {
      require(!closed && !controller.signal.aborted, 'Product lifecycle closed or cancelled')
      require(entry.evidence_types.includes(type), `Undeclared evidence type ${type}`)
      require(/^[a-z0-9][a-z0-9.-]*$/.test(name), 'Invalid evidence name')
      const path = `evidence/${name}.json`, data = Buffer.from(JSON.stringify(value, null, 2) + '\n')
      require(data.length <= 8 * 1024 * 1024, 'Evidence exceeds size limit')
      mkdirSync(join(out, 'evidence'), { recursive: true }); writeFileSync(join(out, path), data, { flag: 'wx', mode: 0o600 })
      const item = { id: name, type, path, digest: 'sha256:' + hash(data), size_bytes: data.length }
      report.evidence.push(item); return name
    }
  }
  async function phase(name, fn) {
    const record = { name, status: 'ERROR' }; report.phases.push(record)
    if (name !== 'cleanup' && controller.signal.aborted) throw new Error('Product run cancelled or timed out')
    let rejectAbort, timeout
    const failure = new Promise((_, reject) => {
      rejectAbort = () => reject(new Error('Product run cancelled or timed out'))
      if (name === 'cleanup') timeout = setTimeout(() => reject(new Error('Cleanup timed out')), 5000)
      else controller.signal.addEventListener('abort', rejectAbort, { once: true })
    })
    try { const result = await Promise.race([Promise.resolve().then(fn), failure]); record.status = 'PASS'; return result }
    finally { clearTimeout(timeout); controller.signal.removeEventListener('abort', rejectAbort) }
  }
  try {
    require(before.complete && !before.unknowns.length, 'Incomplete product candidate scan')
    instance = await phase('launch', async () => {
      driver = await import(pathToFileURL(safePath(root, entry.driver)).href)
      for (const name of phases) require(typeof driver[name] === 'function', `Driver missing ${name}`)
      require(!controller.signal.aborted, 'Product run cancelled during module loading')
      return driver.launch(context)
    })
    await phase('doctor', async () => {
      const health = await driver.doctor(context, instance)
      require(health?.ready === true && typeof health.instance_id === 'string' && health.instance_id, 'Instance is not ready and identified')
    })
    await phase('drive', () => driver.drive(context, instance))
    report.claims = await phase('observe', () => driver.observe(context, instance))
    require(Array.isArray(report.claims), 'Observer must return claims')
    for (const type of entry.evidence_types) require(report.evidence.some(e => e.type === type), `Missing evidence type ${type}`)
    report.status = report.claims.every(c => c.status === 'PASS') ? 'PASS' : 'FAIL'
  } catch (error) { report.status = 'ERROR'; report.error = error.message }
  finally {
    try { await phase('cleanup', () => driver?.cleanup(context, instance)) } catch (error) { report.status = 'ERROR'; report.error = `Cleanup failed: ${error.message}` }
    closed = true
    for (const child of children) if (child.exitCode === null && child.signalCode === null) {
      child.kill('SIGTERM')
      await new Promise(resolve => { const killTimer = setTimeout(() => { child.kill('SIGKILL'); resolve() }, 1000); child.once('close', () => { clearTimeout(killTimer); resolve() }) })
    }
    clearTimeout(timer); signal?.removeEventListener('abort', abort)
    rmSync(scratch, { recursive: true, force: true })
  }
  const after = snapshot(root)
  report.candidate_unchanged = before.content_digest === after.content_digest && after.complete && !after.unknowns.length
  try { validateProduct(report, out, entry.claims) } catch (error) { report.status = 'ERROR'; report.error = error.message }
  writeJson(join(out, 'product.json'), report)
  return report
}
