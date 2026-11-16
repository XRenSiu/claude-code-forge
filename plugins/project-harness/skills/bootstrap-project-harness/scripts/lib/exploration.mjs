import { existsSync, mkdirSync, readFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { runProduct, productBinding } from './product.mjs'
import { featureEntry } from './features.mjs'
import { digest, inside, projectRoot, snapshot, writeJson } from './core.mjs'

const require = (condition, message) => { if (!condition) throw Error(message) }
export function sequences(actions, seed, count, length) {
  require(Array.isArray(actions) && actions.length && actions.every(a => typeof a === 'string'), 'Nonempty action alphabet required')
  require([seed, count, length].every(Number.isSafeInteger) && seed >= 0 && seed <= 0xffffffff && count > 0 && count <= 100 && length > 0 && length <= 100, 'Bounded seed/count/length required')
  let value = seed >>> 0
  // Mulberry32 mixes the low bits too; an LCG modulo a power-of-two alphabet
  // silently repeated one path and missed ordering faults.
  const random = () => { value = (value + 0x6d2b79f5) >>> 0; let x = value; x = Math.imul(x ^ x >>> 15, x | 1); x ^= x + Math.imul(x ^ x >>> 7, x | 61); return (x ^ x >>> 14) >>> 0 }
  return Array.from({ length: count }, () => Array.from({ length }, () => actions[random() % actions.length]))
}

// Delta debugging preserves the SAME claim failure, and every trial gets a new instance.
export async function minimize(sequence, fails, maxTrials = 20) {
  let current = [...sequence], size = Math.max(1, Math.floor(current.length / 2)), trials = 0
  while (size >= 1 && trials < maxTrials) {
    let reduced = false
    for (let i = 0; i < current.length && trials < maxTrials; i += size) {
      const candidate = [...current.slice(0, i), ...current.slice(i + size)]
      if (!candidate.length) continue
      trials++
      if (await fails(candidate)) { current = candidate; reduced = true; break }
    }
    if (!reduced) size = Math.floor(size / 2)
  }
  return { sequence: current, trials, minimality: trials >= maxTrials ? 'budget_limited' : 'one_chunk_minimal' }
}

// Bounded exhaustive exploration; assumptions and implementation mapping remain explicit.
export function checkModel({ initial, actions, next, invariant, assumptions, mapping }, { maxStates = 1000, maxDepth = 12 } = {}) {
  require(assumptions?.length && mapping && Object.keys(mapping).length && actions.length, 'Model requires assumptions, action alphabet and implementation mapping')
  require(Number.isInteger(maxStates) && maxStates > 0 && maxStates <= 100000 && Number.isInteger(maxDepth) && maxDepth >= 0 && maxDepth <= 100, 'Invalid model bounds')
  const seen = new Map([[digest(initial), { state: initial, trace: [] }]]), queue = [...seen.values()], violations = []
  let transitions = 0, truncated = false
  for (let i = 0; i < queue.length; i++) {
    const item = queue[i]
    const issue = invariant(item.state)
    if (issue) violations.push({ issue, ...item })
    if (item.trace.length >= maxDepth) { truncated = true; continue }
    for (const action of actions) {
      const state = next(structuredClone(item.state), action), key = digest(state)
      transitions++
      if (!seen.has(key)) {
        if (seen.size >= maxStates) { truncated = true; continue }
        const found = { state, trace: [...item.trace, action] }; seen.set(key, found); queue.push(found)
      }
    }
  }
  return { schema_version: 1, method: 'bounded-state-enumeration', status: violations.length ? 'FAIL' : truncated ? 'INCOMPLETE' : 'PASS',
    max_states: maxStates, max_depth: maxDepth, states: seen.size, transitions, assumptions, mapping, violations, traces: queue.map(x => x.trace) }
}

export async function explore(rootPath, index, feature, entryId, output, options = {}) {
  const maxDurationMs = options.maxDurationMs ?? 600000
  require(Number.isInteger(maxDurationMs) && maxDurationMs > 0 && maxDurationMs <= 3600000, 'Exploration needs a bounded wall-clock budget')
  const controller = new AbortController(), abort = () => controller.abort(), timer = setTimeout(abort, maxDurationMs)
  options.signal?.addEventListener('abort', abort, { once: true })
  if (options.signal?.aborted) abort()
  try { return await exploreBounded(rootPath, index, feature, entryId, output, { ...options, signal: controller.signal }) }
  finally { clearTimeout(timer); options.signal?.removeEventListener('abort', abort) }
}

async function exploreBounded(rootPath, index, feature, entryId, output, { seed = 1, count = 4, length = 8, maxTrials = 12, replay, signal } = {}) {
  const root = projectRoot(rootPath), { entry } = featureEntry(root, index, feature, entryId)
  require(entry.exploration?.actions?.length, 'This entry has no reviewed exploration action alphabet')
  require(!inside(root, resolve(output)) && !existsSync(output), 'Exploration needs a new output directory outside candidate')
  require(Number.isInteger(maxTrials) && maxTrials >= 0 && maxTrials <= 100, 'Invalid reduction budget')
  const before = snapshot(root), binding = productBinding(root, index, feature, entryId, before.content_digest)
  let cases = sequences(entry.exploration.actions, seed, count, length)
  if (replay) {
    const input = JSON.parse(readFileSync(replay, 'utf8'))
    require(input.schema_version === 1 && ['feature_id', 'entry_id', 'checker_digest', 'fixture_digest'].every(k => input.binding?.[k] === binding[k]), 'Replay checker, fixture or feature binding changed')
    require(Array.isArray(input.sequence) && input.sequence.length > 0 && input.sequence.length <= 100 && input.sequence.every(a => entry.exploration.actions.includes(a)), 'Invalid replay sequence')
    cases = [input.sequence]
  }
  mkdirSync(output, { recursive: true })
  const report = { schema_version: 1, authority: 'project-self-check', method: 'seeded-operation-sequences', binding, seed, count: cases.length, length, attempts: [], counterexamples: [], status: 'PASS' }
  async function run(sequence, purpose) {
    const directory = join(output, `attempt-${report.attempts.length + 1}`)
    const result = await runProduct(root, index, feature, entryId, directory, { scenario: { sequence }, signal })
    const observation = { sequence, purpose, receipt: join(directory, 'product.json'), digest: 'sha256:' + digest(result), status: result.status,
      failed_claims: result.claims.filter(c => c.status === 'FAIL').map(c => c.id), error: result.error }
    report.attempts.push(observation)
    // Checkpoint each completed attempt before reducing or launching the next instance.
    writeJson(join(output, 'exploration.json'), { ...report, status: 'RUNNING' })
    return observation
  }
  for (const sequence of cases) {
    const result = await run(sequence, replay ? 'replay' : 'explore')
    if (result.status === 'ERROR') { report.status = 'ERROR'; break }
    if (result.status !== 'FAIL') continue
    report.status = 'FAIL'
    const claim = result.failed_claims[0]
    const confirmed = await run(sequence, 'reproduce')
    if (confirmed.status !== 'FAIL' || !confirmed.failed_claims.includes(claim)) { report.status = confirmed.status === 'ERROR' ? 'ERROR' : 'UNSTABLE'; break }
    let reduced
    try {
      reduced = await minimize(sequence, async candidate => { const trial = await run(candidate, 'reduce'); if (trial.status === 'ERROR') throw Error('Reduction infrastructure failed'); return trial.failed_claims.includes(claim) }, maxTrials)
    } catch (error) { report.status = 'ERROR'; report.error = error.message; break }
    const counterexample = { schema_version: 1, binding, claim, ...reduced, original_sequence: sequence,
      fingerprint: 'sha256:' + digest({ feature, entryId, claim, sequence: reduced.sequence }), regression_status: 'proposal_requires_review' }
    const file = join(output, `counterexample-${report.counterexamples.length + 1}.json`)
    writeJson(file, counterexample); report.counterexamples.push(file)
    break // One reproducible defect per bounded repair task; never bury it under later passing seeds.
  }
  if (snapshot(root).content_digest !== before.content_digest) report.status = 'ERROR'
  writeJson(join(output, 'exploration.json'), report)
  return report
}
