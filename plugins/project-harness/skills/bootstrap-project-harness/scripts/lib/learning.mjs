import { existsSync, mkdirSync, readFileSync, readdirSync, realpathSync, renameSync, rmSync, writeFileSync } from 'node:fs'
import { basename, dirname, join, relative, resolve } from 'node:path'
import { randomUUID } from 'node:crypto'
import { digest, hash, inside, projectRoot, readJson, safePath, snapshot, writeJson } from './core.mjs'
import { featureEntry } from './features.mjs'
import { evidenceFile, productBinding, runProduct, validateProduct } from './product.mjs'
import { doctor } from './doctor.mjs'

const require = (ok, message) => { if (!ok) throw Error(message) }
const same = (a, b) => digest(a) === digest(b)
const keys = ['feature_id', 'entry_id', 'check_id', 'checker_digest', 'fixture_digest', 'feature_index_digest', 'environment_digest']
const compatible = (a, b) => keys.every(k => a[k] === b[k])
const binding = (root, index, feature, entry) => productBinding(root, index, feature, entry, snapshot(root).content_digest)
const descriptor = path => { const file = evidenceFile(dirname(path), basename(path)), bytes = readFileSync(file); return { path: resolve(file), digest: 'sha256:' + hash(bytes), size_bytes: bytes.length } }
function unchanged(item) { require(same(descriptor(item.path), item), 'Learning evidence changed or disappeared: ' + item.path) }
function sequence(value, entry) { require(Array.isArray(value) && value.length > 0 && value.length <= 100 && value.every(a => entry.exploration?.actions.includes(a)), 'Invalid learned action sequence'); return value }

function storePath(root, directory) {
  require(directory && !inside(root, resolve(directory)), 'Learning store must be outside candidate')
  mkdirSync(directory, { recursive: true }); const store = realpathSync(directory)
  require(!inside(root, store), 'Learning store resolves inside candidate'); return store
}
function state(store) {
  const value = existsSync(join(store, 'catalog.json')) ? readJson(join(store, 'catalog.json')) : { schema_version: 1, authority: 'local_advisory', revision: 0, active: [], events: [] }
  require(value.schema_version === 1 && value.authority === 'local_advisory' && Array.isArray(value.active) && Array.isArray(value.events), 'Invalid learning catalog')
  require(value.events.length <= 10000 && value.revision === value.events.length, 'Invalid learning history revision')
  const active = new Set()
  for (let i = 0; i < value.events.length; i++) {
    const { digest: recorded, ...row } = value.events[i]
    require(row.sequence === i + 1 && row.previous_digest === (i ? value.events[i - 1].digest : null) && recorded === 'sha256:' + digest(row), 'Learning history changed')
    if (row.kind === 'promoted') active.add(row.case_id)
    if (row.kind === 'rolled_back') active.delete(row.case_id)
  }
  require(same([...active].sort(), value.active.map(c => c.case_id).sort()), 'Active regressions contradict history')
  require(new Set(value.active.map(x => x.case_id)).size === value.active.length, 'Duplicate active learning case'); return value
}
function edit(store, operation) {
  const lock = join(store, '.learning-lock')
  if (existsSync(lock)) {
    const owner = readJson(join(lock, 'owner.json'))
    try { process.kill(owner.pid, 0); throw Error('Learning store already in use') }
    catch (error) { if (error.code !== 'ESRCH') throw error; rmSync(lock, { recursive: true }) }
  }
  mkdirSync(lock); writeJson(join(lock, 'owner.json'), { pid: process.pid })
  try {
    const catalog = state(store), result = operation(catalog)
    writeJson(join(store, 'catalog.json'), catalog); return result
  } finally { rmSync(lock, { recursive: true, force: true }) }
}
function event(catalog, kind, details) {
  require(catalog.events.length < 10000, 'Learning history budget exhausted; retain and archive this store before starting a new one')
  const record = { sequence: catalog.events.length + 1, at: new Date().toISOString(), kind, ...details, previous_digest: catalog.events.at(-1)?.digest ?? null }
  record.digest = 'sha256:' + digest(record); catalog.events.push(record); catalog.revision++; return record
}

// Reopen actual observations; a counterexample JSON or a success boolean is insufficient.
function exploration(root, index, path) {
  path = realpathSync(path); const directory = dirname(path), report = readJson(path)
  const { entry } = featureEntry(root, index, report.binding?.feature_id, report.binding?.entry_id)
  require(report.schema_version === 1 && report.authority === 'project-self-check' && compatible(report.binding, binding(root, index, report.binding.feature_id, report.binding.entry_id)), 'Exploration checker, fixture, index or environment is stale')
  require(Array.isArray(report.attempts) && report.attempts.length > 0 && report.attempts.length <= 500, 'Bounded exploration observations required')
  const files = [descriptor(path)], receipts = [], invocations = new Set()
  for (const attempt of report.attempts) {
    sequence(attempt.sequence, entry)
    const file = realpathSync(attempt.receipt); require(inside(directory, file), 'Exploration receipt escapes its evidence directory')
    const raw = readJson(file), result = validateProduct(raw, dirname(file), entry.claims, { binding: report.binding, evidenceTypes: entry.evidence_types })
    require(attempt.digest === 'sha256:' + digest(raw) && result.status === attempt.status && same(attempt.failed_claims, raw.claims.filter(c => c.status === 'FAIL').map(c => c.id)), 'Exploration summary contradicts product evidence')
    require(raw.scenario_digest === 'sha256:' + digest({ sequence: attempt.sequence }) && !invocations.has(raw.invocation_id), 'Exploration sequence or invocation was replayed')
    invocations.add(raw.invocation_id); receipts.push({ ...attempt, invocation_id: raw.invocation_id })
    files.push(descriptor(file), ...raw.evidence.map(e => descriptor(evidenceFile(dirname(file), e.path))))
  }
  require(report.status === 'PASS' ? receipts.every(r => r.status === 'PASS') : ['FAIL', 'ERROR', 'UNSTABLE'].includes(report.status), 'Invalid exploration result')
  return { report, entry, directory, files, receipts }
}
function proposal(store, id) {
  require(/^[a-f0-9]{64}$/.test(id), 'Invalid learning case ID')
  const path = safePath(store, `cases/${id}/case.json`), value = readJson(path)
  require(value.case_id === id && value.evidence?.length && id === digest(value.identity), 'Learning case identity mismatch')
  for (const item of value.evidence) unchanged({ ...item, path: safePath(store, item.path) })
  return value
}

export function collect(rootPath, index, explorationPath, directory) {
  const root = projectRoot(rootPath), store = storePath(root, directory)
  const source = exploration(root, index, explorationPath), { report, entry, receipts } = source
  require(report.status === 'FAIL' && report.counterexamples?.length === 1, 'Only a reproduced product failure can teach a regression')
  const path = realpathSync(report.counterexamples[0]); require(inside(source.directory, path), 'Counterexample escapes exploration')
  const counter = readJson(path); sequence(counter.sequence, entry)
  require(counter.schema_version === 1 && same(counter.binding, report.binding) && entry.claims.includes(counter.claim), 'Counterexample binding or claim changed')
  const failures = receipts.filter(r => r.status === 'FAIL' && r.failed_claims.includes(counter.claim))
  require(failures.some(r => r.purpose === 'reproduce' && same(r.sequence, counter.original_sequence)) && failures.some(r => r.purpose !== 'reproduce' && same(r.sequence, counter.original_sequence)) && failures.some(r => same(r.sequence, counter.sequence)), 'Missing original, repeated or reduced failure evidence')
  const identity = { binding: Object.fromEntries(keys.map(k => [k, report.binding[k]])), claim: counter.claim, sequence: counter.sequence }, id = digest(identity)
  source.files.push(descriptor(path))
  return edit(store, catalog => {
    const destination = join(store, 'cases', id)
    if (!existsSync(destination)) {
      const temporary = join(store, '.case-' + randomUUID()); mkdirSync(temporary)
      try {
        const evidence = [...new Map(source.files.map(f => [f.path, f])).values()].map((file, i) => {
          unchanged(file); const name = `source/${i}-${basename(file.path)}`; mkdirSync(dirname(join(temporary, name)), { recursive: true }); writeFileSync(join(temporary, name), readFileSync(file.path))
          return { ...file, origin_path: file.path, path: `cases/${id}/${name}` }
        })
        // origin_path is informational; all future reads use the retained local copies.
        const value = { schema_version: 1, authority: 'local_advisory', case_id: id, identity, origin_binding: report.binding, evidence: evidence.map(({ origin_path, ...e }) => e), origin: { exploration: explorationPath, source_candidate: report.binding.candidate_digest }, status: 'proposed' }
        writeJson(join(temporary, 'case.json'), value); mkdirSync(dirname(destination), { recursive: true }); renameSync(temporary, destination)
      } finally { rmSync(temporary, { recursive: true, force: true }) }
    } else proposal(store, id)
    const origin = 'sha256:' + digest(report)
    if (!catalog.events.some(e => e.kind === 'collected' && e.case_id === id && e.origin === origin)) event(catalog, 'collected', { case_id: id, origin })
    return { status: 'proposed', case_id: id, store, revision: catalog.revision, authority: 'local_advisory' }
  })
}

function nativeEvidence(root, path) {
  path = realpathSync(path); const receipt = readJson(path), manifest = readJson(join(root, '.harness/project.json'))
  require(doctor(root, manifest, { receipt, receiptPath: path }).healthy && receipt.checks_passed && receipt.execution_complete, 'Complete current native verification is required before learning')
  const files = []
  function walk(directory) {
    for (const item of readdirSync(directory, { withFileTypes: true })) {
      require(!item.isSymbolicLink(), 'Native evidence contains a symlink')
      const p = join(directory, item.name)
      if (item.isDirectory()) walk(p); else files.push(descriptor(p))
      require(files.length <= 2000, 'Native evidence exceeds learning file budget')
    }
  }
  walk(dirname(path)); return { receipt: descriptor(path), files }
}
function qualification(path, item) {
  const value = readJson(path)
  require(value.schema_version === 1 && value.status === 'QUALIFIED' && value.case_id === item.case_id && value.case_digest === 'sha256:' + digest(item), 'Missing or stale learning qualification')
  require(value.observations?.length === 3 && value.native?.files?.length, 'Positive, negative, recovery and native evidence required')
  for (const file of value.native.files) unchanged(file)
  unchanged(value.native.receipt)
  for (const observation of value.observations) {
    require(compatible(observation.binding, item.identity.binding) && observation.binding.candidate_digest === (observation.expected === 'FAIL' ? item.origin_binding.candidate_digest : value.candidate_binding.candidate_digest), 'Qualification candidate or checker mismatch')
    unchanged(observation.receipt)
    const raw = readJson(observation.receipt.path)
    const observed = validateProduct(raw, dirname(observation.receipt.path), value.claims, { invocationId: observation.invocation_id, binding: observation.binding, evidenceTypes: value.evidence_types })
    require(observed.status === observation.expected && raw.scenario_digest === 'sha256:' + digest({ sequence: item.identity.sequence }), 'Qualification outcome or sequence changed')
    if (observation.expected === 'FAIL') require(raw.claims.some(c => c.id === item.identity.claim && c.status === 'FAIL'), 'Negative control did not detect the original predicate')
  }
  require(new Set(value.observations.map(o => o.invocation_id)).size === 3 && same(value.observations.map(o => o.expected), ['PASS', 'FAIL', 'PASS']), 'Qualification controls are incomplete or reused')
  return value
}

export async function qualify(rootPath, index, directory, id, negativeRoot, nativeReceipt, output, signal) {
  const root = projectRoot(rootPath), negative = projectRoot(negativeRoot), store = storePath(root, directory), item = proposal(store, id), { feature_id: feature, entry_id: entryId } = item.identity.binding
  require(root !== negative && !inside(root, negative) && !inside(negative, root), 'Negative control needs a separate candidate checkout')
  const { entry } = featureEntry(root, index, feature, entryId), positiveBinding = binding(root, index, feature, entryId)
  const negativeIndex = readJson(join(negative, '.harness/features.json')), negativeBinding = binding(negative, negativeIndex, feature, entryId)
  require(compatible(positiveBinding, item.identity.binding) && compatible(negativeBinding, item.identity.binding), 'Learning checker, fixture, index or environment changed')
  require(negativeBinding.candidate_digest === item.origin_binding.candidate_digest && positiveBinding.candidate_digest !== negativeBinding.candidate_digest, 'Negative control must be the observed failing candidate')
  const native = nativeEvidence(root, nativeReceipt)
  require(!existsSync(output) && !inside(root, resolve(output)) && !inside(negative, resolve(output)), 'Qualification needs a new outside evidence directory')
  mkdirSync(output, { recursive: true }); output = realpathSync(output)
  require(!inside(root, output) && !inside(negative, output), 'Qualification evidence resolves inside a candidate')
  const report = { schema_version: 1, authority: 'local_advisory', case_id: id, case_digest: 'sha256:' + digest(item), candidate_binding: positiveBinding, claims: entry.claims, evidence_types: entry.evidence_types, native, observations: [], status: 'ERROR' }
  const controller = new AbortController(), abort = () => controller.abort(), timer = setTimeout(abort, 600000)
  signal?.addEventListener('abort', abort, { once: true }); if (signal?.aborted) abort()
  try {
    for (const [name, candidate, features, expected] of [['positive', root, index, 'PASS'], ['negative', negative, negativeIndex, 'FAIL'], ['recovery', root, index, 'PASS']]) {
      const folder = join(output, name), observed = await runProduct(candidate, features, feature, entryId, folder, { scenario: { sequence: item.identity.sequence }, signal: controller.signal })
      report.observations.push({ name, expected, invocation_id: observed.invocation_id, binding: observed.binding, receipt: descriptor(join(folder, 'product.json')) })
      require(observed.status === expected && (expected !== 'FAIL' || observed.claims.some(c => c.id === item.identity.claim && c.status === 'FAIL')), 'Learning control failed: ' + name)
    }
    require(same(binding(root, index, feature, entryId), positiveBinding) && same(binding(negative, negativeIndex, feature, entryId), negativeBinding), 'Candidate changed during learning qualification')
    for (const file of native.files) unchanged(file)
    report.status = 'QUALIFIED'
  } catch (error) { report.error = error.message }
  finally { clearTimeout(timer); signal?.removeEventListener('abort', abort) }
  writeJson(join(output, 'qualification.json'), report)
  edit(store, catalog => event(catalog, 'qualified', { case_id: id, status: report.status, evidence: descriptor(join(output, 'qualification.json')) }))
  return { status: report.status, case_id: id, qualification: join(output, 'qualification.json'), error: report.error }
}

function policy(root, store, path, item, operation) {
  path = realpathSync(path); require(!inside(root, path) && !inside(store, path), 'Learning policy must be outside candidate and learning store')
  const value = readJson(path)
  require(value.schema_version === 1 && value.authority === 'local_advisory' && value.authorization_ref?.trim() && value.expires_at > Date.now() / 1000, 'Current explicit learning authorization required')
  require(realpathSync(value.store) === store && realpathSync(value.project_root) === root, 'Learning policy scope mismatch')
  require(value.allowed_operations?.includes(operation) && value.entries?.includes(item.identity.binding.feature_id + '/' + item.identity.binding.entry_id), 'Learning operation or feature outside policy')
  require(Number.isSafeInteger(value.max_active_cases) && value.max_active_cases > 0 && value.max_active_cases <= 100, 'Bounded learning budget required')
  return { ...value, digest: descriptor(path).digest }
}
export function promote(rootPath, index, directory, qualificationPath, policyPath) {
  const root = projectRoot(rootPath), store = storePath(root, directory), q = readJson(qualificationPath), item = proposal(store, q.case_id), proof = qualification(qualificationPath, item)
  const grant = policy(root, store, policyPath, item, 'append-regression'), current = binding(root, index, item.identity.binding.feature_id, item.identity.binding.entry_id)
  require(same(current, proof.candidate_binding), 'Promotion requires the exact qualified candidate')
  nativeEvidence(root, proof.native.receipt.path)
  return edit(store, catalog => {
    if (!catalog.active.some(c => c.case_id === item.case_id)) {
      require(catalog.active.length < grant.max_active_cases, 'Active regression budget exhausted')
      catalog.active.push({ case_id: item.case_id, case_digest: 'sha256:' + digest(item), qualification: descriptor(realpathSync(qualificationPath)), policy_digest: grant.digest })
      event(catalog, 'promoted', { case_id: item.case_id, policy_digest: grant.digest, authorization_ref: grant.authorization_ref })
    }
    return { status: 'active', case_id: item.case_id, revision: catalog.revision, authority: 'local_advisory' }
  })
}
export function rollback(rootPath, directory, id, policyPath, reason) {
  const root = projectRoot(rootPath), store = storePath(root, directory), item = proposal(store, id), grant = policy(root, store, policyPath, item, 'rollback-regression')
  require(typeof reason === 'string' && reason.trim().length >= 5, 'Rollback needs a concrete reason')
  return edit(store, catalog => {
    if (catalog.active.some(c => c.case_id === id)) { catalog.active = catalog.active.filter(c => c.case_id !== id); event(catalog, 'rolled_back', { case_id: id, reason, policy_digest: grant.digest }) }
    return { status: 'rolled_back', case_id: id, revision: catalog.revision, evidence_retained: true }
  })
}
export function regressions(root, index, feature, entry, directory) {
  require(existsSync(join(directory, 'catalog.json')), 'Configured learning corpus is missing; do not silently skip regressions')
  const store = storePath(root, directory), catalog = state(store), current = binding(root, index, feature, entry), cases = []
  require(catalog.active.length <= 100, 'Learning corpus exceeds execution budget')
  for (const active of catalog.active) {
    const item = proposal(store, active.case_id)
    if (item.identity.binding.feature_id !== feature || item.identity.binding.entry_id !== entry) continue
    require(active.case_digest === 'sha256:' + digest(item) && compatible(item.identity.binding, current), 'Active regression is stale; requalify instead of silently skipping it')
    unchanged(active.qualification); qualification(active.qualification.path, item)
    cases.push({ case_id: item.case_id, sequence: item.identity.sequence })
  }
  return { revision: catalog.revision, cases }
}
export function observe(rootPath, index, directory, explorationPath) {
  const root = projectRoot(rootPath), store = storePath(root, directory), checked = exploration(root, index, explorationPath), report = checked.report
  require(report.corpus && Array.isArray(report.corpus.cases), 'Exploration did not use a learned corpus')
  return edit(store, catalog => {
    const identity = 'sha256:' + digest(report)
    if (!catalog.events.some(e => e.kind === 'observed' && e.observation === identity)) {
      require(Number.isSafeInteger(report.corpus.revision) && report.corpus.revision <= catalog.revision, 'Unknown learning corpus revision')
      const expected = new Map(report.corpus.cases.map(c => [c.case_id, proposal(store, c.case_id)]))
      require(expected.size === report.corpus.cases.length, 'Duplicate learned regression identity')
      for (const c of report.corpus.cases) require(same(c.sequence, expected.get(c.case_id).identity.sequence) && compatible(expected.get(c.case_id).identity.binding, report.binding), 'Reported learned regression changed')
      const observed = checked.receipts.filter(r => r.purpose === 'learned-regression')
      require(observed.length && observed.every(r => expected.has(r.case_id) && same(r.sequence, expected.get(r.case_id).identity.sequence)), 'Missing or mismatched learned regression observations')
      require(new Set(observed.map(r => r.case_id)).size === observed.length && (report.status !== 'PASS' || observed.length === expected.size), 'Incomplete or repeated learned regression observations')
      const seen = observed.map(r => ({ case_id: r.case_id, status: r.status }))
      event(catalog, 'observed', { observation: identity, corpus_revision: report.corpus.revision, candidate_digest: report.binding.candidate_digest, outcomes: seen, evidence: checked.files })
    }
    return { status: report.status, revision: catalog.revision, active_cases: catalog.active.length, note: 'A product failure stays a failure; it does not deactivate the regression.' }
  })
}
export function learningStatus(rootPath, directory) {
  const root = projectRoot(rootPath), store = storePath(root, directory), catalog = state(store)
  return { ...catalog, metrics: { collected: catalog.events.filter(e => e.kind === 'collected').length, qualification_failures: catalog.events.filter(e => e.kind === 'qualified' && e.status !== 'QUALIFIED').length, active_cases: catalog.active.length, rollbacks: catalog.events.filter(e => e.kind === 'rolled_back').length, observed_runs: catalog.events.filter(e => e.kind === 'observed').length, production_escape_rate: null }, authority: 'local_advisory' }
}

export async function learningCommand(root, argv, signal) {
  const [action, ...args] = argv, opts = {}, allowed = new Set(['store', 'exploration', 'case', 'negative-root', 'native-receipt', 'out', 'qualification', 'policy', 'reason'])
  for (let i = 0; i < args.length; i += 2) { const key = args[i].replace(/^--/, ''); require(args[i].startsWith('--') && allowed.has(key) && args[i + 1] && !Object.hasOwn(opts, key), 'Invalid learning option'); opts[key] = args[i + 1] }
  const index = readJson(join(root, '.harness/features.json'))
  if (action === 'collect') return collect(root, index, opts.exploration, opts.store)
  if (action === 'qualify') return qualify(root, index, opts.store, opts.case, opts['negative-root'], opts['native-receipt'], opts.out, signal)
  if (action === 'promote') return promote(root, index, opts.store, opts.qualification, opts.policy)
  if (action === 'rollback') return rollback(root, opts.store, opts.case, opts.policy, opts.reason)
  if (action === 'observe') return observe(root, index, opts.store, opts.exploration)
  if (action === 'status') return learningStatus(root, opts.store)
  throw Error('Unknown learning command')
}
