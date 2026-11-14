import { spawn } from 'node:child_process'
import { mkdirSync, readFileSync, realpathSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { randomUUID } from 'node:crypto'
import { VERSION, digest, inside, now, projectRoot, safePath, snapshot, writeJson, atomicWrite } from './core.mjs'
import { validate, validateChecks } from './contracts.mjs'
import { parseReport } from './reporters.mjs'
import { describeEnvironment } from './environment.mjs'

export function runProcess(executable, args, { cwd, env, input = '', timeoutMs = 120000, signal, maxOutput = 8 * 1024 * 1024 } = {}) {
  return new Promise(resolveResult => {
    let stdout = '', stderr = '', failure = null, killTimer, done = false
    const started = Date.now()
    const child = spawn(executable === 'node' ? process.execPath : executable, args, { cwd, env: { ...process.env, ...env }, shell: false, detached: process.platform !== 'win32', stdio: ['pipe', 'pipe', 'pipe'] })
    function kill(sig) {
      try { if (process.platform !== 'win32') process.kill(-child.pid, sig); else child.kill(sig) } catch (error) { if (error.code !== 'ESRCH') failure ||= error.message }
    }
    function stop(reason) {
      if (done || failure) return
      failure = reason; kill('SIGTERM')
      killTimer = setTimeout(() => kill('SIGKILL'), 1000)
    }
    const timer = setTimeout(() => stop('Timed out'), timeoutMs)
    const abort = () => stop('Cancelled')
    signal?.addEventListener('abort', abort, { once: true })
    if (signal?.aborted) abort()
    child.stdout.on('data', chunk => { stdout += chunk.toString(); if (Buffer.byteLength(stdout) > maxOutput) { stdout = stdout.slice(0, maxOutput); stop('Output limit exceeded') } })
    child.stderr.on('data', chunk => { stderr += chunk.toString(); if (Buffer.byteLength(stderr) > maxOutput) { stderr = stderr.slice(0, maxOutput); stop('Output limit exceeded') } })
    child.stdin.on('error', error => { if (error.code !== 'EPIPE') failure ||= error.message })
    child.stdin.end(input)
    child.on('error', error => { failure = `Cannot start process: ${error.message}` })
    child.on('close', (code, sig) => {
      done = true; clearTimeout(timer); clearTimeout(killTimer); signal?.removeEventListener('abort', abort)
      // A child may leave grandchildren alive after closing its own pipes.
      kill('SIGKILL')
      resolveResult({ code, signal: sig, stdout, stderr, failure, duration_ms: Date.now() - started })
    })
  })
}
async function runCheck(root, check, runDir, signal) {
  if (check.platforms && !check.platforms.includes(process.platform)) return { id: check.id, status: 'NOT_APPLICABLE', reason: `Declared platform scope: ${check.platforms.join(', ')}` }
  if (signal?.aborted) return { id: check.id, status: 'NOT_RUN', reason: 'Cancelled before start' }
  const dir = join(runDir, check.id)
  mkdirSync(dir, { recursive: true })
  try {
    const cwd = safePath(root, check.cwd, { allowRoot: true })
    const environment = describeEnvironment(cwd, check.env)
    const argv = check.argv.map(arg => arg.replaceAll('{artifact_dir}', dir))
    const processResult = await runProcess(check.executable, argv, { cwd, env: check.env, input: check.stdin, timeoutMs: check.timeout_ms, signal })
    atomicWrite(join(dir, 'stdout.log'), processResult.stdout)
    atomicWrite(join(dir, 'stderr.log'), processResult.stderr)
    let parsed
    if (processResult.failure || processResult.signal) parsed = { status: 'ERROR', reason: processResult.failure || `Terminated by ${processResult.signal}` }
    else {
      const report = check.report_file ? readFileSync(safePath(dir, check.report_file), 'utf8') : processResult.stdout
      parsed = parseReport(check, report, processResult.code)
    }
    return { id: check.id, ...parsed, executable: check.executable, argv, cwd: check.cwd, environment, exit_code: processResult.code, duration_ms: processResult.duration_ms, artifacts: dir }
  } catch (error) { return { id: check.id, status: 'ERROR', reason: error.message, artifacts: dir } }
}
export async function verify(rootPath, manifest, { outputDir, signal } = {}) {
  const root = projectRoot(rootPath)
  validate('manifest', manifest); validateChecks(manifest.checks)
  if (!outputDir || inside(root, resolve(outputDir))) throw new Error('Verification artifacts must be outside the project so receipts do not change candidate hashes')
  mkdirSync(resolve(outputDir), { recursive: true })
  const physicalOutput = realpathSync(resolve(outputDir))
  if (inside(root, physicalOutput)) throw new Error('Verification artifacts resolve inside the project')
  const runDir = join(physicalOutput, `run-${Date.now()}-${randomUUID().slice(0, 8)}`)
  mkdirSync(runDir, { recursive: true })
  const candidate = snapshot(root)
  const results = []
  const pending = new Map(manifest.checks.map(check => [check.id, check]))
  const nodeMajor = Number(process.versions.node.split('.')[0])
  const nodeOk = nodeMajor >= 22 && (manifest.node_major === null || nodeMajor === manifest.node_major)
  if (!nodeOk) {
    for (const check of pending.values()) results.push({ id: check.id, status: 'NOT_RUN', reason: `Node ${manifest.node_major ?? '22+'} required; current ${process.versions.node}` })
    pending.clear()
  }
  while (pending.size) {
    const wave = [...pending.values()].filter(check => check.depends_on.every(id => results.some(r => r.id === id)))
    if (!wave.length) throw new Error('Unresolvable check graph')
    const waveResults = await Promise.all(wave.map(async check => {
      if (check.depends_on.some(id => results.find(r => r.id === id).status !== 'PASS')) return { id: check.id, status: 'NOT_RUN', reason: 'Prerequisite did not pass' }
      return runCheck(root, check, runDir, signal)
    }))
    for (const result of waveResults) { results.push(result); pending.delete(result.id) }
  }
  const candidateAfter = snapshot(root)
  const changed = candidate.content_digest !== candidateAfter.content_digest
  const limitations = [...manifest.limitations]
  if (changed) limitations.push('Project content changed during checks; rerun against the final candidate')
  if (!candidate.complete || !candidateAfter.complete) limitations.push('Candidate scan incomplete; cannot certify this result')
  if (candidate.unknowns.length) limitations.push('Candidate digest excludes submodule contents or unreadable paths; see candidate.unknowns')
  for (const result of results) for (const warning of result.environment?.warnings || []) limitations.push(`${result.id}: ${warning}`)
  const complete = !changed && candidate.complete && candidateAfter.complete && results.some(r => ['PASS', 'FAIL'].includes(r.status)) && results.every(r => ['PASS', 'FAIL', 'NOT_APPLICABLE'].includes(r.status))
  const required = results.filter(r => manifest.checks.find(c => c.id === r.id).required && r.status !== 'NOT_APPLICABLE')
  const receipt = validate('receipt', {
    schema_version: 1, evidence_kind: 'project-self-check', factory_version: VERSION, created_at: now(), candidate, candidate_after: candidateAfter,
    manifest_digest: digest(manifest), environment: { node: process.versions.node, platform: process.platform, arch: process.arch, ...describeEnvironment(root), runner_digest: digest(['verify.mjs', 'reporters.mjs', 'environment.mjs', 'core.mjs', 'contracts.mjs'].map(name => readFileSync(new URL(`./${name}`, import.meta.url), 'utf8'))) },
    expected_checks: manifest.checks.map(c => c.id), results, execution_complete: complete,
    checks_passed: complete && required.length > 0 && required.every(r => r.status === 'PASS'), limitations,
    external_acceptance: { status: 'NOT_REQUESTED' }
  })
  const receiptPath = join(runDir, 'receipt.json')
  writeJson(receiptPath, receipt)
  return { receipt, path: receiptPath }
}
export function isCurrentReceipt(root, manifest, receipt) {
  validate('receipt', receipt)
  return receipt.manifest_digest === digest(manifest) && receipt.candidate_after.content_digest === snapshot(projectRoot(root)).content_digest
}
