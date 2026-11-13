import { existsSync, readFileSync, realpathSync, readdirSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { VERSION, fileState, hash, projectRoot, safePath } from './core.mjs'
import { validate } from './contracts.mjs'
import { makePlan } from './plan.mjs'
import { survey } from './survey.mjs'

const libDir = dirname(fileURLToPath(import.meta.url))
const startMarker = '<!-- project-harness:verification:start -->'
const endMarker = '<!-- project-harness:verification:end -->'
export function defaultChecks(inventory) {
  const rootPackage = inventory.packages.find(p => p.path === 'package.json')
  if (!rootPackage) return []
  const common = { cwd: '.', depends_on: [], timeout_ms: 180000, required: true, effects: 'temporary-artifacts' }
  if (rootPackage.tools.includes('vitest')) return [{ ...common, id: 'unit-tests', executable: 'node', argv: ['node_modules/vitest/vitest.mjs', 'run', '--reporter=json', '--outputFile={artifact_dir}/vitest.json'], reporter: 'vitest-json', report_file: 'vitest.json' }]
  return []
}
export function bootstrap(rootPath, { host = 'codex', authorizationRef, checks, purpose = 'Adopt a minimal, independently runnable project harness' } = {}) {
  const root = projectRoot(rootPath), inventory = survey(root)
  if (!inventory.scan.complete) throw new Error('Cannot automatically bootstrap with a truncated survey')
  if (inventory.conflicts.length) throw new Error('Resolve package-manager conflicts before bootstrap')
  const manifestPath = '.harness/project.json'
  const previous = existsSync(join(root, manifestPath)) ? validate('manifest', JSON.parse(readFileSync(safePath(root, manifestPath), 'utf8'))) : null
  const operations = []
  function put(path, content, reason, source = `bootstrap-project-harness/${VERSION}`) {
    const state = fileState(safePath(root, path, { write: true }))
    if (state.hash === hash(content)) return
    const old = previous?.assets.find(asset => asset.path === path)
    if (state.hash !== null && (!old || old.hash !== state.hash)) throw new Error(`Existing or locally modified asset requires a manual merge plan: ${path}`)
    operations.push({ path, content, before_hash: state.hash, reason, source })
  }
  const generated = new Map()
  function asset(path, content, reason) { generated.set(path, content); put(path, content, reason) }
  const runner = `#!/usr/bin/env node\nimport { dirname, resolve } from 'node:path'\nimport { fileURLToPath } from 'node:url'\nimport { readJson } from '../.harness/runtime/core.mjs'\nimport { verify } from '../.harness/runtime/verify.mjs'\nconst root = resolve(dirname(fileURLToPath(import.meta.url)), '..')\nconst outputDir = process.argv[2]\nif (!outputDir) { console.error('Usage: node scripts/project-verify.mjs <artifact-directory-outside-project>'); process.exit(2) }\nconst controller = new AbortController()\nfor (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => controller.abort())\ntry {\n  const { receipt, path } = await verify(root, readJson(resolve(root, '.harness/project.json')), { outputDir, signal: controller.signal })\n  console.log(JSON.stringify({ receipt: path, checks_passed: receipt.checks_passed, results: receipt.results.map(({ id, status }) => ({ id, status })) }, null, 2))\n  process.exitCode = receipt.checks_passed ? 0 : receipt.execution_complete ? 1 : 2\n} catch (error) { console.error(error.message); process.exitCode = 2 }\n`
  asset('scripts/project-verify.mjs', runner, 'Project-owned verification entry without a factory runtime dependency')
  for (const name of ['core.mjs', 'contracts.mjs', 'reporters.mjs', 'environment.mjs', 'verify.mjs']) asset(`.harness/runtime/${name}`, readFileSync(join(libDir, name), 'utf8'), 'Pinned verification runtime; upgrade with the factory')
  const selectedChecks = checks || previous?.checks || defaultChecks(inventory)
  const doc = `# Project verification\n\nRun with the project's required Node version:\n\n\`\`\`sh\nnode scripts/project-verify.mjs /tmp/project-harness-results\n\`\`\`\n\nThe authoritative command bindings are in [.harness/project.json](../.harness/project.json). Review their effects before running. The JSON receipt names the candidate digest, expected checks, actual counts, errors and skipped scope. Exit 0 requires a nonempty set of applicable required checks with evidence. Exit 1 means completed checks failed. Exit 2 means execution was incomplete.\n\nKeep native lint, test, CI and module documentation as their existing sources of truth. Update bindings when those commands change. Generated runtime assets are versioned with this repository. Use the bootstrap-project-harness skill to survey, diagnose or propose a reviewed upgrade. It preserves local changes and reports merge conflicts.\n\nKeep the system temporary directory outside repositories and package trees. Evidence output is not a replacement for TMPDIR: temporary fixtures may otherwise inherit an enclosing Git root or JavaScript module scope. Receipts record effective Node/temp context and environment fingerprints; they do not certify all machine state.\n\nA local receipt is a self-check, not external acceptance. Desktop behavior and host loading require their own real-session evidence.\n`
  asset('docs/project-harness.md', doc, 'Verification usage and maintenance ownership')
  const hostEntry = host === 'claude-code' ? 'CLAUDE.md' : 'AGENTS.md'
  if (host !== 'portable') {
    const block = `${startMarker}\nProject verification: see [docs/project-harness.md](docs/project-harness.md).\nRun \`node scripts/project-verify.mjs <artifact-directory-outside-project>\` after reviewing the bound checks.\n${endMarker}`
    const entry = existsSync(join(root, hostEntry)) ? relative(root, realpathSync(safePath(root, hostEntry))).split('\\').join('/') : hostEntry
    const state = fileState(safePath(root, entry, { write: true }))
    const old = state.content === null ? `# Project development\n\nRead package scripts, native configuration and the relevant module documentation before changing code.\n` : Buffer.from(state.content, 'base64').toString('utf8')
    const start = old.indexOf(startMarker), end = old.indexOf(endMarker)
    if ((start < 0) !== (end < 0) || (start >= 0 && (end < start || old.indexOf(startMarker, start + 1) >= 0 || old.indexOf(endMarker, end + 1) >= 0))) throw new Error('Malformed managed instruction block')
    const content = start >= 0 ? old.slice(0, start) + block + old.slice(end + endMarker.length) : old.trimEnd() + '\n\n' + block + '\n'
    if (content !== old) operations.push({ path: entry, content, before_hash: state.hash, reason: 'Link the existing instruction entry to project-owned verification; preserve all other content', source: hostEntry })
  }
  const pinnedNode = inventory.facts.find(f => f.kind === 'node-pin')?.value
  const sources = [...new Set([...inventory.assets.filter(a => a.kind === 'instructions' || a.kind === 'configuration').map(a => a.path), ...(host === 'portable' ? [] : [hostEntry])])].sort()
  const manifest = validate('manifest', { schema_version: 1, factory_version: VERSION, host, stack: inventory.packages.some(p => p.tools.includes('electron')) ? 'vue-electron' : 'node-typescript', node_major: /^v?\d+/.test(pinnedNode || '') ? Number(pinnedNode.match(/\d+/)[0]) : null, assets: [...generated].map(([path, content]) => ({ path, hash: hash(content), owner: 'project-harness-runtime' })), checks: selectedChecks, sources, limitations: ['Host discovery requires a real new-session smoke test', 'Desktop/native runtime is not certified by static or unit checks', 'Submodule and installed dependency contents are outside the project candidate digest', 'External CI acceptance is not configured by this local generator'] })
  const manifestState = fileState(join(root, manifestPath))
  const content = JSON.stringify(manifest, null, 2) + '\n'
  if (manifestState.hash !== hash(content)) operations.push({ path: manifestPath, content, before_hash: manifestState.hash, reason: 'Bind existing tools, generated asset ownership and declared coverage', source: 'survey + selected checks' })
  return { inventory, plan: makePlan(root, { purpose, authorization_ref: authorizationRef, operations, checks: selectedChecks }) }
}
