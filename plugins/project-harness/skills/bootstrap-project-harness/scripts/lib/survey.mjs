import { existsSync, lstatSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { VERSION, git, hash, listFiles, now, projectRoot, safePath, snapshot } from './core.mjs'
import { validate } from './contracts.mjs'

const lockNames = { 'package-lock.json': 'npm', 'npm-shrinkwrap.json': 'npm', 'pnpm-lock.yaml': 'pnpm', 'yarn.lock': 'yarn', 'bun.lock': 'bun', 'bun.lockb': 'bun' }
export function survey(path, { maxFiles = 25000 } = {}) {
  const root = projectRoot(path), scan = listFiles(root, maxFiles)
  const facts = [], conflicts = [], unknowns = [], assets = [], packages = []
  function read(name) {
    try {
      const file = safePath(root, name)
      if (lstatSync(file).size > 2 * 1024 * 1024) throw new Error('Discovery content exceeds 2 MiB')
      return readFileSync(file, 'utf8')
    } catch (error) { unknowns.push({ path: name, reason: error.message }); return null }
  }
  for (const name of scan.files) {
    if (/(^|\/)package\.json$/.test(name)) {
      const content = read(name)
      if (content === null) continue
      try {
        const pkg = JSON.parse(content), dir = dirname(name)
        const locks = Object.keys(lockNames).filter(lock => scan.files.includes(dir === '.' ? lock : `${dir}/${lock}`))
        const managers = [...new Set(locks.map(lock => lockNames[lock]))]
        if (managers.length > 1) conflicts.push({ path: name, reason: 'Multiple package-manager lockfiles', candidates: managers })
        const declared = pkg.packageManager?.split('@')[0]
        if (declared && managers.length && !managers.includes(declared)) conflicts.push({ path: name, reason: 'packageManager conflicts with lockfile', candidates: [...managers, declared] })
        packages.push({ path: name, hash: hash(content), name: pkg.name || null, engines: pkg.engines || {}, package_manager: managers.length > 1 ? null : declared || managers[0] || null, package_manager_version: pkg.packageManager || null, lockfiles: locks, scripts: pkg.scripts || {}, workspaces: pkg.workspaces || null, tools: Object.keys({ ...pkg.dependencies, ...pkg.devDependencies }).filter(k => /eslint|vitest|typescript|playwright|electron|^vue$|^react$|^pinia$/.test(k)) })
      } catch (error) { unknowns.push({ path: name, reason: `Invalid package.json: ${error.message}` }) }
    }
    let kind
    if (/(^|\/)(AGENTS(?:\.override)?|CLAUDE)\.md$/.test(name)) kind = 'instructions'
    else if (/(^|\/)\.claude\/(rules\/|settings(?:\.local)?\.json)|^\.codex\/config\.toml$|^(\.github\/workflows\/|\.gitlab-ci\.yml)|(^|\/)(eslint|vitest|playwright|tsconfig)[^/]*\.|(^|\/)\.eslintrc/.test(name)) kind = 'configuration'
    else if (/(^|\/)(README|DESIGN|CONTRIBUTING)\.md$/.test(name) || /^docs\/.*\.md$/.test(name)) kind = 'documentation'
    else if (/\/SKILL\.md$/.test(name)) kind = 'skill'
    else if (/^(docs\/(guides|architecture)|test\/harness|eval)\//.test(name)) kind = 'existing-harness'
    if (kind) {
      const content = read(name)
      if (content !== null) assets.push({ path: name, kind, hash: hash(content), symlink: lstatSync(join(root, name)).isSymbolicLink() })
    }
  }
  if (!scan.complete) unknowns.push({ reason: 'File scan truncated; do not infer absent assets', scanned: scan.files.length, total: scan.total })
  if (existsSync(join(root, '.nvmrc'))) facts.push({ kind: 'node-pin', path: '.nvmrc', value: read('.nvmrc')?.trim() })
  const status = git(root, ['status', '--porcelain=v1', '-uall'])
  facts.push({ kind: 'working-tree', source: 'git status --porcelain=v1 -uall', dirty_paths: status.status === 0 ? status.stdout.split('\n').filter(Boolean) : [], available: status.status === 0 })
  if (!packages.length) unknowns.push({ reason: 'No readable Node package found; automatic Node bindings unavailable' })
  return validate('inventory', { schema_version: 1, factory_version: VERSION, root, created_at: now(), candidate: snapshot(root), scan: { ...scan, files: scan.files.length }, packages, assets, facts, conflicts, unknowns })
}
