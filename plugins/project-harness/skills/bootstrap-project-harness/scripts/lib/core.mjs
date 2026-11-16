import { createHash, randomUUID } from 'node:crypto'
import { existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, readlinkSync, realpathSync, renameSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path'
import { spawnSync } from 'node:child_process'

export const VERSION = '0.3.0'
export const hash = value => createHash('sha256').update(value).digest('hex')
export const canonical = value => JSON.stringify(value, (_, v) => v && !Array.isArray(v) && typeof v === 'object' ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b))) : v)
export const digest = value => hash(canonical(value))
export const readJson = file => JSON.parse(readFileSync(file, 'utf8'))
export const now = () => new Date().toISOString()
export function atomicWrite(file, content, mode = 0o644) {
  mkdirSync(dirname(file), { recursive: true })
  const temp = `${file}.${randomUUID()}.tmp`
  try {
    writeFileSync(temp, content, { mode, flag: 'wx' })
    renameSync(temp, file)
  } finally { rmSync(temp, { force: true }) }
}
export const writeJson = (file, value) => atomicWrite(file, JSON.stringify(value, null, 2) + '\n')
export const git = (root, args) => spawnSync('git', ['-C', root, ...args], { encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 })
export const inside = (root, target) => { const rel = relative(root, target); return rel === '' || (!isAbsolute(rel) && rel !== '..' && !rel.startsWith(`..${sep}`)) }
export function safePath(root, name, { write = false, allowRoot = false } = {}) {
  if (typeof name !== 'string' || name.includes('\0') || name.includes('\\') || isAbsolute(name) || name.split('/').some(p => p === '..' || p === '.git') || (!name && !allowRoot)) throw new Error(`Unsafe path: ${name}`)
  const target = resolve(root, name)
  if (!inside(root, target) || (target === root && !allowRoot)) throw new Error(`Path escapes project: ${name}`)
  let cursor = root
  for (const part of relative(root, target).split(sep).filter(Boolean)) {
    cursor = join(cursor, part)
    let stat
    try { stat = lstatSync(cursor) } catch (error) { if (error.code === 'ENOENT') continue; throw error }
    if (stat.isSymbolicLink()) {
      if (write) throw new Error(`Write path contains symlink: ${name}`)
      if (!inside(root, realpathSync(cursor))) throw new Error(`Read path contains external symlink: ${name}`)
    }
  }
  return target
}
export function fileState(file) {
  try {
    const stat = lstatSync(file)
    if (!stat.isFile()) throw new Error(`Expected regular file: ${file}`)
    const buffer = readFileSync(file)
    return { hash: hash(buffer), content: buffer.toString('base64'), mode: stat.mode & 0o777 }
  } catch (error) { if (error.code === 'ENOENT') return { hash: null, content: null, mode: 0o644 }; throw error }
}
const excludedDirs = new Set(['.git', 'node_modules', '.harness-runs', 'dist', 'out', 'coverage', '.DS_Store'])
export function listFiles(root, maxFiles = 25000) {
  const result = git(root, ['ls-files', '--cached', '--others', '--exclude-standard', '-z'])
  if (result.status === 0) {
    const all = [...new Set(result.stdout.split('\0').filter(Boolean))].sort()
    return { files: all.slice(0, maxFiles), total: all.length, complete: all.length <= maxFiles, method: 'git-index-and-untracked', excluded: ['gitignored paths', 'submodule contents'] }
  }
  const files = []
  let truncated = false
  function walk(dir) {
    for (const entry of readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      if (excludedDirs.has(entry.name)) continue
      if (files.length >= maxFiles) { truncated = true; return }
      const file = join(dir, entry.name)
      if (entry.isDirectory()) walk(file)
      else files.push(relative(root, file).split(sep).join('/'))
    }
  }
  walk(root)
  return { files, total: truncated ? null : files.length, complete: !truncated, method: 'filesystem', excluded: [...excludedDirs] }
}
export function snapshot(root, { exclude = [], maxFiles = 100000 } = {}) {
  const listing = listFiles(root, maxFiles)
  const entries = [], unknowns = []
  for (const name of listing.files) {
    const file = resolve(root, name)
    if (exclude.some(path => inside(resolve(path), file))) continue
    try {
      const stat = lstatSync(file)
      if (stat.isSymbolicLink()) entries.push([name, 'symlink', readlinkSync(file)])
      else if (stat.isFile()) entries.push([name, stat.mode & 0o777, hash(readFileSync(file))])
      else unknowns.push({ path: name, reason: 'Submodule/directory contents excluded from candidate digest' })
    } catch (error) {
      if (error.code === 'ENOENT') entries.push([name, 'deleted'])
      else unknowns.push({ path: name, reason: error.message })
    }
  }
  return { commit: git(root, ['rev-parse', 'HEAD']).stdout?.trim() || null, content_digest: digest(entries), complete: listing.complete, files: entries.length, excluded: listing.excluded, unknowns }
}
export function projectRoot(path) { const root = realpathSync(resolve(path)); if (!lstatSync(root).isDirectory()) throw new Error('Project root must be a directory'); return root }
