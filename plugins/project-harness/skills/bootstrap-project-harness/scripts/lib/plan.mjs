import { VERSION, digest, fileState, hash, now, projectRoot, safePath } from './core.mjs'
import { validate, validateChecks } from './contracts.mjs'

export function planDigest(plan) { const { digest: _ignored, ...body } = plan; return digest(body) }
export function makePlan(path, proposal) {
  const root = projectRoot(path)
  if (!proposal.purpose?.trim() || !proposal.authorization_ref?.trim()) throw new Error('Plan needs purpose and authorization context reference (not proof of authorization)')
  if (!Array.isArray(proposal.operations)) throw new Error('Plan needs operations')
  const names = new Set()
  const operations = proposal.operations.map(op => {
    const file = safePath(root, op.path, { write: true })
    if (names.has(file)) throw new Error(`Duplicate target: ${op.path}`)
    names.add(file)
    if (op.content !== null && typeof op.content !== 'string') throw new Error(`Invalid content: ${op.path}`)
    if (op.content?.length > 16 * 1024 * 1024) throw new Error('Plan operation too large')
    const state = fileState(file)
    if (!Object.hasOwn(op, 'before_hash') || op.before_hash !== state.hash) throw new Error(`Stale proposal for ${op.path}; read current content and rebuild proposal`)
    return { path: op.path, content: op.content, before_hash: state.hash, after_hash: op.content === null ? null : hash(op.content), reason: op.reason, source: op.source }
  })
  const paths = operations.map(op => op.path.replace(/\/$/, ''))
  if (paths.some(p => paths.some(q => p !== q && q.startsWith(`${p}/`)))) throw new Error('Overlapping file/parent paths')
  const plan = { schema_version: 1, factory_version: VERSION, root, created_at: now(), purpose: proposal.purpose, authorization_ref: proposal.authorization_ref, operations, checks: validateChecks(proposal.checks || []), digest: '' }
  plan.digest = planDigest(plan)
  return validate('plan', plan)
}
export function verifyPlan(plan, root) {
  validate('plan', plan); validateChecks(plan.checks)
  if (plan.root !== projectRoot(root)) throw new Error('Plan belongs to a different project')
  if (planDigest(plan) !== plan.digest) throw new Error('Plan digest mismatch')
  const names = new Set()
  for (const op of plan.operations) {
    const file = safePath(root, op.path, { write: true })
    if (names.has(file)) throw new Error(`Duplicate target: ${op.path}`)
    names.add(file)
    if ((op.content === null ? null : hash(op.content)) !== op.after_hash) throw new Error('Operation content digest mismatch')
  }
  return plan
}
