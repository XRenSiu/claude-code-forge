import { existsSync, readFileSync, realpathSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { spawnSync } from 'node:child_process'
import { digest } from './core.mjs'

// Only diagnostic paths are emitted. Other process context and explicit
// environment values are hashed, so credentials do not enter the receipt.
export function describeEnvironment(cwd, overrides = {}) {
  const env = { ...process.env, ...overrides }
  const configuredTemp = process.platform === 'win32' ? env.TEMP || env.TMP || tmpdir() : env.TMPDIR || tmpdir()
  let temporaryDirectory = resolve(cwd, configuredTemp)
  try { temporaryDirectory = realpathSync(temporaryDirectory) } catch {}
  const repository = spawnSync('git', ['-C', temporaryDirectory, 'rev-parse', '--show-toplevel'], { env, encoding: 'utf8', timeout: 5000 })
  let packageScope = null
  for (let dir = temporaryDirectory; ; dir = dirname(dir)) {
    const path = join(dir, 'package.json')
    if (existsSync(path)) {
      try {
        const pkg = JSON.parse(readFileSync(path, 'utf8'))
        packageScope = { path, type: pkg.type || 'commonjs' }
      } catch { packageScope = { path, type: 'unreadable' } }
      break
    }
    if (dirname(dir) === dir) break
  }
  const gitRoot = repository.status === 0 ? repository.stdout.trim() : null
  const influences = ['PATH', 'TMPDIR', 'TMP', 'TEMP', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_CEILING_DIRECTORIES', 'NODE_OPTIONS', 'NODE_PATH', 'CI', 'TZ']
  const fingerprint = Object.fromEntries(influences.map(name => [name, env[name] ?? null]))
  const warnings = []
  if (gitRoot) warnings.push('Temporary fixtures can inherit an enclosing Git repository; prefer the system temp directory outside repositories')
  if (packageScope) warnings.push(`Temporary JavaScript fixtures inherit package scope (${packageScope.type}); keep test temp outside package trees unless intentionally configured`)
  return {
    node_executable: process.execPath,
    temporary_directory: temporaryDirectory,
    temp_git_root: gitRoot,
    temp_package_scope: packageScope,
    explicit_env_keys: Object.keys(overrides).sort(),
    explicit_env_digest: digest(overrides),
    context_digest: digest({ fingerprint, gitRoot, packageScope, node: process.version, executable: process.execPath }),
    warnings
  }
}
