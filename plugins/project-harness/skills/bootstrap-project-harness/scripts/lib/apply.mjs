import { existsSync, mkdirSync, realpathSync, rmSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { atomicWrite, fileState, inside, now, projectRoot, readJson, safePath, writeJson } from './core.mjs'
import { verifyPlan } from './plan.mjs'

function stateDirectory(root, stateDir) {
  if (!stateDir) throw new Error('Transaction state directory required')
  const target = resolve(stateDir)
  if (inside(root, target)) throw new Error('Transaction state must be outside the target project')
  mkdirSync(target, { recursive: true })
  const physical = realpathSync(target)
  if (inside(root, physical)) throw new Error('Transaction state resolves inside the target project')
  return physical
}
function withLock(root, stateDir, callback) {
  const lock = join(root, '.harness-write-lock')
  try { mkdirSync(lock) } catch (error) { if (error.code === 'EEXIST') throw new Error(`Project write lock exists: ${lock}; inspect owner.json and recover before retrying`); throw error }
  writeJson(join(lock, 'owner.json'), { pid: process.pid, state_dir: stateDir, started_at: now() })
  try { return callback() } finally { rmSync(lock, { recursive: true, force: true }) }
}
function restore(root, journal, journalFile) {
  const conflicts = []
  for (const entry of [...journal.entries].reverse()) {
    if (!['intent', 'written'].includes(entry.status)) continue
    try {
      const target = safePath(root, entry.path, { write: true })
      const current = fileState(target)
      if (current.hash === entry.before.hash) { entry.status = 'restored'; continue }
      if (current.hash !== entry.after_hash) { conflicts.push(entry.path); continue }
      if (entry.before.content === null) rmSync(target, { force: true })
      else atomicWrite(target, Buffer.from(entry.before.content, 'base64'), entry.before.mode)
      entry.status = 'restored'
    } catch { conflicts.push(entry.path) }
  }
  journal.status = conflicts.length ? 'recovery-conflict' : 'rolled-back'
  journal.recovery_conflicts = conflicts
  writeJson(journalFile, journal)
  return journal
}
export function apply(rootPath, plan, { stateDir, acceptedDigest, failAfter = null } = {}) {
  const root = projectRoot(rootPath)
  verifyPlan(plan, root)
  if (acceptedDigest !== plan.digest) throw new Error('Apply requires the exact reviewed plan digest; it does not grant authorization')
  const state = stateDirectory(root, stateDir)
  const journalFile = join(state, `journal-${plan.digest}.json`)
  if (existsSync(journalFile) && !['complete', 'rolled-back'].includes(readJson(journalFile).status)) throw new Error(`Unfinished transaction: recover ${journalFile}`)
  return withLock(root, state, () => {
    // Validate every precondition before the first mutation.
    for (const op of plan.operations) {
      const current = fileState(safePath(root, op.path, { write: true })).hash
      if (current !== op.before_hash && current !== op.after_hash) throw new Error(`Conflict: ${op.path}`)
    }
    const journal = { schema_version: 1, root, plan_digest: plan.digest, created_at: now(), status: 'applying', entries: [] }
    writeJson(journalFile, journal)
    try {
      let written = 0
      for (const op of plan.operations) {
        const target = safePath(root, op.path, { write: true })
        const before = fileState(target)
        if (before.hash === op.after_hash) { journal.entries.push({ path: op.path, status: 'already-applied' }); continue }
        if (before.hash !== op.before_hash) throw new Error(`Concurrent edit: ${op.path}`)
        const entry = { path: op.path, before, after_hash: op.after_hash, status: 'intent' }
        journal.entries.push(entry); writeJson(journalFile, journal)
        if (op.content === null) rmSync(target)
        else {
          mkdirSync(dirname(target), { recursive: true })
          safePath(root, op.path, { write: true })
          if (fileState(target).hash !== before.hash) throw new Error(`Concurrent edit: ${op.path}`)
          atomicWrite(target, op.content, before.mode)
        }
        entry.status = 'written'; writeJson(journalFile, journal)
        written++
        if (failAfter !== null && written >= failAfter) throw new Error('Injected transaction interruption')
      }
      journal.status = 'complete'; writeJson(journalFile, journal)
      return { status: 'complete', journal: journalFile, written: journal.entries.filter(e => e.status === 'written').length, already_applied: journal.entries.filter(e => e.status === 'already-applied').length }
    } catch (error) {
      const recovered = restore(root, journal, journalFile)
      throw new Error(`${error.message}; ${recovered.status}; journal ${journalFile}`)
    }
  })
}
export function recover(rootPath, journalFile) {
  const root = projectRoot(rootPath), journal = readJson(journalFile)
  if (journal.schema_version !== 1 || journal.root !== root || !Array.isArray(journal.entries)) throw new Error('Journal schema/root mismatch')
  if (['complete', 'rolled-back'].includes(journal.status)) throw new Error(`Journal is ${journal.status}; recovery only handles unfinished transactions`)
  const lock = join(root, '.harness-write-lock')
  if (existsSync(lock)) {
    const owner = readJson(join(lock, 'owner.json'))
    try { process.kill(owner.pid, 0); throw new Error('Lock owner is still alive') } catch (error) { if (error.code !== 'ESRCH') throw error }
    rmSync(lock, { recursive: true })
  }
  return withLock(root, dirname(journalFile), () => restore(root, journal, journalFile))
}
