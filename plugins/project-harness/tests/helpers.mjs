import { mkdtempSync, mkdirSync, writeFileSync, rmSync, realpathSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, dirname } from 'node:path'
import { spawnSync } from 'node:child_process'
import { fileState } from '../skills/bootstrap-project-harness/scripts/lib/core.mjs'

export function fixture(t, files = {}) {
  const base = realpathSync(mkdtempSync(join(tmpdir(), 'project-harness-test-')))
  const root = join(base, 'repo'), artifacts = join(base, 'artifacts')
  mkdirSync(root); mkdirSync(artifacts)
  spawnSync('git', ['init', '-q', root])
  for (const [file, content] of Object.entries(files)) put(root, file, content)
  t.after(() => rmSync(base, { recursive: true, force: true }))
  return { root, artifacts, base }
}
export function put(root, file, content) { const target = join(root, file); mkdirSync(dirname(target), { recursive: true }); writeFileSync(target, content) }
export function operation(root, path, content) { return { path, content, before_hash: fileState(join(root, path)).hash, source: 'fixture confirmed requirement', reason: 'Exercise a real contract' } }
export const proposal = operations => ({ purpose: 'Test fixture', authorization_ref: 'test-only temporary directory', operations, checks: [] })
export const check = (id, code, extra = {}) => ({ id, executable: 'node', argv: ['-e', code], cwd: '.', reporter: 'claims-json', depends_on: [], timeout_ms: 3000, required: true, effects: 'temporary-artifacts', expected_claims: ['behavior'], ...extra })
export const claim = (status = 'PASS') => `console.log(JSON.stringify({schema_version:1,complete:true,examined:1,claims:[{id:'behavior',status:'${status}'}]}))${status === 'FAIL' ? ';process.exitCode=1' : ''}`
export const manifest = checks => ({ schema_version: 1, factory_version: '0.1.0', host: 'portable', stack: 'node-typescript', node_major: null, assets: [], checks, sources: [], limitations: [] })
