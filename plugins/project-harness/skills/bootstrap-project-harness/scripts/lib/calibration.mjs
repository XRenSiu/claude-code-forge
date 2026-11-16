import { chmodSync, existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, readlinkSync, realpathSync, rmSync, symlinkSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve, relative } from 'node:path'
import { tmpdir } from 'node:os'
import { digest, hash, inside, listFiles, readJson, safePath, snapshot, writeJson } from './core.mjs'
import { featureEntry } from './features.mjs'
import { validateProduct } from './product.mjs'
import { runProcess } from './verify.mjs'

const require = (value, message) => { if (!value) throw new Error(message) }
const descriptor = (root, path) => { const bytes = readFileSync(join(root, path)); return { path, digest: 'sha256:' + hash(bytes), size_bytes: bytes.length } }
function copyCandidate(root, target, dependencies) {
  const listing = listFiles(root, 100000)
  require(listing.complete, 'Cannot calibrate a truncated candidate')
  for (const path of listing.files) {
    if (dependencies.some(d => path === d || path.startsWith(d + '/'))) continue
    const source = safePath(root, path), dest = safePath(target, path, { write: true })
    if (!existsSync(source)) continue
    const stat = lstatSync(source)
    mkdirSync(dirname(dest), { recursive: true })
    if (stat.isSymbolicLink()) { require(inside(root, realpathSync(source)), 'External source symlink'); symlinkSync(readlinkSync(source), dest) }
    else { require(stat.isFile(), 'Submodules need an explicit calibration adapter'); writeFileSync(dest, readFileSync(source)); chmodSync(dest, stat.mode & 0o777) }
  }
  for (const path of dependencies) {
    const source = safePath(root, path), dest = safePath(target, path, { write: true })
    require(lstatSync(source).isDirectory(), 'Dependency link must name a directory')
    mkdirSync(dirname(dest), { recursive: true }); symlinkSync(source, dest, 'dir')
  }
}

export async function calibrate(rootPath, planPath, outputDir) {
  const root = realpathSync(rootPath), plan = readJson(resolve(planPath))
  require(plan?.schema_version === 1 && Array.isArray(plan.mutations) && plan.mutations.length > 0, 'Nonempty calibration plan v1 required')
  require(Array.isArray(plan.required_faults) && plan.required_faults.length > 0 && new Set(plan.required_faults).size === plan.required_faults.length, 'Required fault IDs must be explicit and unique')
  require(Array.isArray(plan.dependency_paths), 'Explicit dependency paths required')
  const ids = plan.mutations.map(m => m.id)
  require(new Set(ids).size === ids.length && ids.every(id => /^[a-z0-9][a-z0-9-]*$/.test(id)) && plan.required_faults.every(id => ids.includes(id)), 'Invalid or missing fault IDs')
  const index = readJson(join(root, '.harness/features.json')), { entry } = featureEntry(root, index, plan.feature_id, plan.entry_id)
  if (entry.calibration_plan) require(digest(plan) === digest(readJson(safePath(root, entry.calibration_plan))), 'Calibration plan differs from the indexed reviewed plan')
  const protectedFiles = new Set([entry.driver, ...entry.checker_files, ...entry.fixture_files, 'scripts/project-product.mjs'].map(p => realpathSync(safePath(root, p))))
  for (const mutation of plan.mutations) {
    const target = safePath(root, mutation.path)
    require(relative(root, target).split('\\').join('/') === mutation.path && realpathSync(target) === target, 'Mutation source path must be canonical without symlinks')
    require(!mutation.path.startsWith('.harness/') && !protectedFiles.has(target), 'Mutation may not edit the checker, driver, fixture or harness')
    require(entry.claims.includes(mutation.claim_id), 'Fault must name an existing business assertion')
    const content = readFileSync(safePath(root, mutation.path), 'utf8')
    require(typeof mutation.before === 'string' && mutation.before.length > 0 && typeof mutation.after === 'string' && mutation.before !== mutation.after && content.split(mutation.before).length === 2, 'Mutation preimage must match exactly once')
  }
  require(outputDir && !inside(root, resolve(outputDir)), 'Calibration evidence must be outside the project')
  mkdirSync(outputDir, { recursive: false }); const out = realpathSync(outputDir)
  require(!inside(root, out), 'Calibration output resolves inside project')
  const initial = snapshot(root)
  require(initial.complete && !initial.unknowns.length, 'Incomplete source snapshot')
  writeJson(join(out, 'plan.json'), plan)
  const report = { schema_version: 1, evidence_kind: 'checker-calibration', authority: 'local_advisory',
    source_digest: 'sha256:' + initial.content_digest, plan: descriptor(out, 'plan.json'), cases: [],
    required_faults: plan.required_faults, status: 'ERROR', total_mutants: plan.mutations.length, killed: 0, mutation_score: 0,
    limitations: ['Local execution does not establish protected provenance or a hidden holdout', 'Dependency directory links are reused read-only; installed dependency contents are outside the source digest'] }
  async function run(name, candidate, mutation) {
    const folder = join(out, name); mkdirSync(folder)
    const result = await runProcess(process.execPath, [...entry.node_args, 'scripts/project-product.mjs', plan.feature_id, plan.entry_id, folder], { cwd: candidate, timeoutMs: entry.timeout_ms })
    writeFileSync(join(folder, 'stdout.log'), result.stdout); writeFileSync(join(folder, 'stderr.log'), result.stderr)
    const row = { id: name, kind: mutation ? 'mutant' : 'positive', exit_code: result.code, status: 'ERROR',
      stdout: descriptor(out, `${name}/stdout.log`), stderr: descriptor(out, `${name}/stderr.log`) }
    if (mutation) row.mutation = mutation
    try {
      require(!result.failure && !result.signal, result.failure || 'Run interrupted')
      const receipt = readJson(join(folder, 'product.json'))
      validateProduct(receipt, folder, entry.claims)
      const baselineBinding = report.cases[0]?.binding
      if (baselineBinding) require(Object.entries(baselineBinding).every(([key, value]) => key === 'candidate_digest' || receipt.binding[key] === value), 'Calibration checker, index, fixture or environment changed')
      require(receipt.binding.candidate_digest === 'sha256:' + snapshot(candidate).content_digest, 'Calibration receipt does not describe the executed candidate')
      if (!mutation) require(receipt.binding.candidate_digest === report.source_digest, 'Positive control candidate changed')
      else require(receipt.binding.candidate_digest !== report.source_digest, 'Fault did not change candidate')
      row.binding = receipt.binding
      row.receipt = descriptor(out, `${name}/product.json`)
      row.status = !mutation ? (receipt.status === 'PASS' && result.code === 0 ? 'PASS' : 'ERROR')
        : receipt.status === 'FAIL' && result.code === 1 && receipt.claims.some(c => c.id === mutation.claim_id && c.status === 'FAIL') ? 'KILLED'
          : receipt.status === 'PASS' && result.code === 0 ? 'SURVIVED' : 'ERROR'
    } catch (error) { row.error = error.message }
    report.cases.push(row)
    return row
  }
  try {
    const baseline = await run('baseline', root)
    require(baseline.status === 'PASS', 'Positive baseline failed; faults were not run')
    for (const mutation of plan.mutations) {
      const scratch = realpathSync(mkdtempSync(join(tmpdir(), 'harness-calibration-')))
      try {
        copyCandidate(root, scratch, plan.dependency_paths)
        const path = safePath(scratch, mutation.path, { write: true }), before = readFileSync(path, 'utf8'), after = before.replace(mutation.before, mutation.after)
        writeFileSync(path, after)
        const patchPath = `patches/${mutation.id}.json`
        writeJson(join(out, patchPath), { path: mutation.path, before, after })
        await run(mutation.id, scratch, { ...mutation, before_digest: 'sha256:' + hash(before), after_digest: 'sha256:' + hash(after), patch: descriptor(out, patchPath) })
      } finally { rmSync(scratch, { recursive: true, force: true }) }
    }
    await run('recovery', root)
    report.killed = report.cases.filter(c => c.status === 'KILLED').length
    report.mutation_score = report.killed / report.total_mutants
    report.status = report.cases.length === plan.mutations.length + 2 && report.cases.every(c => ['PASS', 'KILLED'].includes(c.status)) ? 'PASS' : 'FAIL'
  } catch (error) { report.status = 'ERROR'; report.error = error.message }
  if (snapshot(root).content_digest !== initial.content_digest) { report.status = 'ERROR'; report.error = 'Original candidate changed during calibration' }
  writeJson(join(out, 'calibration.json'), report)
  return { status: report.status, receipt: join(out, 'calibration.json'), killed: report.killed, total: report.total_mutants, authority: report.authority }
}
