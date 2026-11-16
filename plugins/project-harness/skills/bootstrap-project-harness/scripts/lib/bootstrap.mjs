import { existsSync, readFileSync, realpathSync, readdirSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { VERSION, digest, fileState, hash, projectRoot, safePath } from './core.mjs'
import { validate } from './contracts.mjs'
import { makePlan } from './plan.mjs'
import { survey } from './survey.mjs'
import { validateFeatures, featureChecks, renderFeatures } from './features.mjs'
import { contextPath, contextLockPath, contextCheck, renderContext, extractBlock, replaceBlock, sourceFingerprint, instructionDirectories } from './context.mjs'

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
export function bootstrap(rootPath, { host, authorizationRef, checks, context, features, purpose = 'Adopt a project development harness with native verification' } = {}) {
  const reviewedContext = context !== undefined
  const root = projectRoot(rootPath), inventory = survey(root)
  if (!inventory.scan.complete) throw new Error('Cannot automatically bootstrap with a truncated survey')
  if (inventory.conflicts.length) throw new Error('Resolve package-manager conflicts before bootstrap')
  const manifestPath = '.harness/project.json'
  const previous = existsSync(join(root, manifestPath)) ? validate('manifest', JSON.parse(readFileSync(safePath(root, manifestPath), 'utf8'))) : null
  features ||= previous?.features ? JSON.parse(readFileSync(safePath(root, previous.features), 'utf8')) : null
  if (features) validateFeatures(root, features)
  host ||= previous?.host || (context ? 'dual' : 'codex')
  context ||= existsSync(join(root, contextPath)) ? JSON.parse(readFileSync(safePath(root, contextPath), 'utf8')) : null
  if (!['codex', 'claude-code', 'dual', 'portable'].includes(host)) throw new Error(`Unsupported host: ${host}`)
  const operations = []
  function put(path, content, reason, source = `bootstrap-project-harness/${VERSION}`) {
    const state = fileState(safePath(root, path, { write: true }))
    if (state.hash === hash(content)) return
    const old = previous?.assets.find(asset => asset.path === path)
    if (state.hash !== null && (!old || old.hash !== state.hash)) throw new Error(`Existing or locally modified asset requires a manual merge plan: ${path}`)
    operations.push({ path, content, before_hash: state.hash, reason, source })
  }
  const generated = new Map()
  const owners = new Map()
  function asset(path, content, reason, owner = 'project-harness-runtime') { generated.set(path, content); owners.set(path, owner); put(path, content, reason) }
  const entries = new Map()
  const oldLock = previous?.context ? JSON.parse(readFileSync(safePath(root, contextLockPath), 'utf8')) : null
  const resolvedEntry = name => existsSync(join(root, name)) ? relative(root, realpathSync(safePath(root, name))).split('\\').join('/') : name
  function entryBlock(name, id, block) {
    const path = resolvedEntry(name)
    if (!entries.has(path)) {
      const state = fileState(safePath(root, path, { write: true }))
      entries.set(path, { state, content: state.content === null ? '# Project development\n' : Buffer.from(state.content, 'base64').toString('utf8') })
    }
    const entry = entries.get(path), current = extractBlock(entry.content, id)
    const old = oldLock?.blocks?.find(b => b.path === path && b.id === id)
    if (id !== 'verification' && (old ? current === null || hash(current) !== old.hash : current !== null) && current !== block) throw new Error(`Locally modified instruction block requires a manual merge plan: ${path} (${id})`)
    entry.content = replaceBlock(entry.content, id, block)
    return path
  }
  const runner = `#!/usr/bin/env node\nimport { dirname, resolve } from 'node:path'\nimport { fileURLToPath } from 'node:url'\nimport { readJson } from '../.harness/runtime/core.mjs'\nimport { verify } from '../.harness/runtime/verify.mjs'\nconst root = resolve(dirname(fileURLToPath(import.meta.url)), '..')\nconst outputDir = process.argv[2]\nif (!outputDir) { console.error('Usage: node scripts/project-verify.mjs <artifact-directory-outside-project>'); process.exit(2) }\nconst controller = new AbortController()\nfor (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => controller.abort())\ntry {\n  const { receipt, path } = await verify(root, readJson(resolve(root, '.harness/project.json')), { outputDir, signal: controller.signal })\n  console.log(JSON.stringify({ receipt: path, checks_passed: receipt.checks_passed, results: receipt.results.map(({ id, status }) => ({ id, status })) }, null, 2))\n  process.exitCode = receipt.checks_passed ? 0 : receipt.execution_complete ? 1 : 2\n} catch (error) { console.error(error.message); process.exitCode = 2 }\n`
  asset('scripts/project-verify.mjs', runner, 'Project-owned verification entry without a factory runtime dependency')
  for (const name of ['core.mjs', 'contracts.mjs', 'reporters.mjs', 'environment.mjs', 'verify.mjs', 'context.mjs', 'doctor.mjs', 'features.mjs', 'product.mjs', 'calibration.mjs', 'exploration.mjs', 'learning.mjs']) asset(`.harness/runtime/${name}`, readFileSync(join(libDir, name), 'utf8'), 'Pinned runtime; upgrade with the factory')
  let selectedChecks = checks || previous?.checks || defaultChecks(inventory)
  if (features) {
    const path = '.harness/features.json', state = fileState(safePath(root, path, { write: true })), content = JSON.stringify(features, null, 2) + '\n'
    if (hash(content) !== state.hash) operations.push({ path, content, before_hash: state.hash, reason: 'Reviewed project-owned feature verification index', source: 'Product sources and existing checks' })
    for (const check of featureChecks(features)) {
      const existing = selectedChecks.find(c => c.id === check.id)
      if (!existing) selectedChecks = [...selectedChecks, check]
    }
    validateFeatures(root, features, selectedChecks)
    asset('docs/verification-features.md', renderFeatures(features), 'Render user entry points and verification coverage', 'project-harness-features')
    const productEntry = `#!/usr/bin/env node\nimport { dirname, resolve } from 'node:path'\nimport { fileURLToPath } from 'node:url'\nimport { readJson } from '../.harness/runtime/core.mjs'\nimport { runProduct } from '../.harness/runtime/product.mjs'\nconst root = resolve(dirname(fileURLToPath(import.meta.url)), '..')\nconst [feature, entry, output] = process.argv.slice(2)\nconst controller = new AbortController()\nfor (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => controller.abort())\ntry {\n  const result = await runProduct(root, readJson(resolve(root, '.harness/features.json')), feature, entry, output, { signal: controller.signal, invocationId: process.env.PROJECT_HARNESS_INVOCATION })\n  console.log(JSON.stringify({ status: result.status, receipt: resolve(output, 'product.json') }))\n  process.exitCode = result.status === 'PASS' ? 0 : result.status === 'FAIL' ? 1 : 2\n  process.stdout.write('', () => process.exit(process.exitCode))\n} catch (error) { console.error(error.message); process.exitCode = 2 }\n`
    asset('scripts/project-product.mjs', productEntry, 'Run an indexed real product entry and retain observations after cleanup')
    const calibrationEntry = `#!/usr/bin/env node\nimport { dirname, resolve } from 'node:path'\nimport { fileURLToPath } from 'node:url'\nimport { calibrate } from '../.harness/runtime/calibration.mjs'\nconst root = resolve(dirname(fileURLToPath(import.meta.url)), '..')\ntry {\n  const result = await calibrate(root, process.argv[2], process.argv[3])\n  console.log(JSON.stringify(result))\n  process.exitCode = result.status === 'PASS' ? 0 : 1\n} catch (error) { console.error(error.message); process.exitCode = 2 }\n`
    asset('scripts/project-calibrate.mjs', calibrationEntry, 'Run representative product faults in disposable source copies')
    asset('scripts/project-impact.mjs', `#!/usr/bin/env node\nimport { resolve } from 'node:path'\nimport { readJson } from '../.harness/runtime/core.mjs'\nimport { impact } from '../.harness/runtime/features.mjs'\nconst root = resolve(import.meta.dirname, '..')\ntry { console.log(JSON.stringify(impact(root, readJson(resolve(root, '.harness/features.json')), process.argv[2] || 'HEAD'), null, 2)) } catch (e) { console.error(e.message); process.exitCode = 2 }\n`, 'Select affected product entries and expose unmapped changes')
    asset('scripts/project-explore.mjs', `#!/usr/bin/env node\nimport { resolve } from 'node:path'\nimport { readJson } from '../.harness/runtime/core.mjs'\nimport { explore } from '../.harness/runtime/exploration.mjs'\nconst root = resolve(import.meta.dirname, '..')\nconst [feature, entry, output, options] = process.argv.slice(2)\nconst controller = new AbortController()\nfor (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => controller.abort())\ntry { const result = await explore(root, readJson(resolve(root, '.harness/features.json')), feature, entry, output, { ...(options ? readJson(options) : {}), signal: controller.signal }); console.log(JSON.stringify(result)); process.exitCode = result.status === 'PASS' ? 0 : 1 } catch (e) { console.error(e.message); process.exitCode = 2 }\n`, 'Seed, reproduce and reduce operation sequences using fresh product instances')
    asset('docs/verification-learning.md', readFileSync(join(libDir, '../../references/learning.md'), 'utf8'), 'Qualification, observation and rollback of learned regression data')
    asset('scripts/project-learn.mjs', `#!/usr/bin/env node\nimport { resolve } from 'node:path'\nimport { learningCommand } from '../.harness/runtime/learning.mjs'\nconst root = resolve(import.meta.dirname, '..'), controller = new AbortController()\nfor (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => controller.abort())\ntry { const result = await learningCommand(root, process.argv.slice(2), controller.signal); console.log(JSON.stringify(result)); process.exitCode = ['ERROR','FAIL'].includes(result.status) ? 1 : 0 } catch (e) { console.error(e.message); process.exitCode = 2 }\n`, 'Evidence-qualified additive regression learning with scoped promotion and rollback')
    const projectSkill = `---\nname: verify-project\ndescription: Run this project's indexed real product paths, diagnose failures, and retain current candidate evidence.\n---\n\nRead AGENTS.md and docs/project-harness.md, then docs/verification-features.md. Use the required Node/package manager. Read each selected driver's prerequisites and unsupported scope.\n\n1. Run node scripts/project-impact.mjs <base-commit>. Review unmapped files and index drift; selections do not replace full regression.\n2. Follow an indexed scripts/project-product.mjs command with a NEW outside evidence directory. Inspect all five phases and per-claim raw evidence. A screenshot alone is not a semantic oracle.\n3. For entries with exploration.actions, run scripts/project-explore.mjs <feature> <entry> <new-outside-directory> [options.json] with the entry's node_args. Options: seed/count/length/maxTrials, replay:<counterexample.json>, or corpus:<outside-learning-store> to run qualified regressions before new random cases. Retain reproduced and reduced failures before repair. An ERROR is infrastructure/checker failure, not a product counterexample.\n4. Repair product code without changing frozen predicates. Replay the same counterexample; run the listed calibration plan where bound. Distinguish stale index, broken driver, environment failure and product regression.\n5. Run the complete scripts/project-verify.mjs graph on the final candidate. Independent acceptance requires the configured protected control; local PASS grants no delivery authority.\n6. For a reproduced failure, use project-learn.mjs collect, qualify against the unchanged failing checkout and fixed candidate with full native evidence, then promote under an explicit outside learning policy. Observe the next corpus run; rollback retains all evidence. See docs/verification-learning.md. A product failure must never automatically disable its regression.\n\nDo not pass credentials to logs, screenshots or model prompts. This skill is generated from the project feature index; edit the source profile and regenerate.\n`
    if (['dual', 'codex'].includes(host)) asset('.agents/skills/verify-project/SKILL.md', projectSkill, 'Cold-start Codex product verification entry')
    if (['dual', 'claude-code'].includes(host)) asset('.claude/skills/verify-project/SKILL.md', projectSkill, 'Cold-start Claude product verification entry')
  }
  const doc = `# Project verification\n\nRun with the project's required Node version:\n\n\`\`\`sh\nnode scripts/project-verify.mjs /tmp/project-harness-results\n\`\`\`\n\nThe authoritative command bindings are in [.harness/project.json](../.harness/project.json). Review their effects before running. The JSON receipt names the candidate digest, expected checks, actual counts, errors and skipped scope. Exit 0 requires a nonempty set of applicable required checks with evidence. Exit 1 means completed checks failed. Exit 2 means execution was incomplete.\n\nKeep native lint, test, CI and module documentation as their existing sources of truth. Update bindings when those commands change. Generated runtime assets are versioned with this repository. Use the bootstrap-project-harness skill to survey, diagnose or propose a reviewed upgrade. It preserves local changes and reports merge conflicts.\n\nKeep the system temporary directory outside repositories and package trees. Evidence output is not a replacement for TMPDIR: temporary fixtures may otherwise inherit an enclosing Git root or JavaScript module scope. Receipts record effective Node/temp context and environment fingerprints; they do not certify all machine state.\n\nA local receipt is a self-check, not external acceptance. Desktop behavior and host loading require their own real-session evidence.\n`
  asset('docs/project-harness.md', doc + (features ? '\nProduct routes, expected observations and unverified surfaces: [verification-features.md](verification-features.md). Each entry owns launch/doctor/drive/observe/cleanup. Run `node scripts/project-calibrate.mjs <reviewed-plan.json> <new-outside-directory>` to check representative faults; this is local evidence, not protected qualification.\n' : '') + (context ? '\nDevelopment rules, workflows and adoption decisions: [development/README.md](development/README.md). Run `node scripts/project-context.mjs` to check generated guidance, source drift and host wiring; run `node scripts/project-doctor.mjs [receipt.json]` for full static diagnostics. These commands work without the factory installation.\n' : '\nThis is a verification-only installation. To adopt a development harness, prepare a source-backed context profile using the skill and rerun bootstrap with `--context`.\n'), 'Verification usage and maintenance ownership')
  const hostEntries = host === 'dual' ? ['AGENTS.md', 'CLAUDE.md'] : host === 'portable' ? [] : [host === 'claude-code' ? 'CLAUDE.md' : 'AGENTS.md']
  for (const hostEntry of hostEntries) {
    const block = `${startMarker}\nProject verification: see [docs/project-harness.md](docs/project-harness.md).\nRun \`node scripts/project-verify.mjs <artifact-directory-outside-project>\` after reviewing the bound checks.\n${endMarker}`
    entryBlock(hostEntry, 'verification', block)
  }
  const contextSources = [], nextBlocks = []
  if (context) {
    const rendered = renderContext(root, context, host)
    for (const scope of instructionDirectories(rendered.scopes)) if (['dual', 'codex'].includes(host) && existsSync(join(root, scope, 'AGENTS.override.md'))) throw new Error(`AGENTS.override.md shadows generated guidance: ${scope}; reconcile the existing instructions first`)
    const state = fileState(safePath(root, contextPath, { write: true })), content = JSON.stringify(context, null, 2) + '\n'
    if (hash(content) !== state.hash) operations.push({ path: contextPath, content, before_hash: state.hash, reason: 'Project-owned source-backed rule and workflow definition', source: 'Reviewed project context' })
    for (const [path, content] of rendered.files) asset(path, content, 'Render project guidance from the shared profile', 'project-harness-context')
    for (const block of rendered.blocks) {
      const path = entryBlock(block.path, block.id, block.content)
      nextBlocks.push({ path, id: block.id, hash: hash(block.content) })
    }
    contextSources.push(...new Set([...context.rules, ...context.workflows, ...context.assessment].flatMap(x => x.sources)))
    const sourceHashes = Object.fromEntries(contextSources.sort().map(path => [path, sourceFingerprint(root, path)]))
    if (oldLock && !reviewedContext && (oldLock.profile_digest !== digest(context) || digest(oldLock.sources) !== digest(sourceHashes))) throw new Error('Context or sources changed; review them and pass --context explicitly before refreshing fingerprints')
    const lock = { schema_version: 1, profile_digest: digest(context), sources: sourceHashes, blocks: nextBlocks }
    asset(contextLockPath, JSON.stringify(lock, null, 2) + '\n', 'Bind reviewed sources and generated instruction blocks', 'project-harness-context')
    const inspector = `#!/usr/bin/env node\nimport { dirname, resolve } from 'node:path'\nimport { fileURLToPath } from 'node:url'\nimport { inside, readJson, writeJson } from '../.harness/runtime/core.mjs'\nimport { contextReport } from '../.harness/runtime/context.mjs'\nconst root = resolve(dirname(fileURLToPath(import.meta.url)), '..')\nconst report = contextReport(root, readJson(resolve(root, '.harness/project.json')))\nif (process.argv[2]) {\n  const output = resolve(process.argv[2])\n  if (inside(root, output)) throw new Error('Context evidence must be outside the project')\n  writeJson(resolve(output, 'claims.json'), report)\n}\nconsole.log(JSON.stringify(report, null, 2))\nprocess.exitCode = report.claims.every(c => c.status === 'PASS') ? 0 : 1\n`
    asset('scripts/project-context.mjs', inspector, 'Standalone context validation without the factory')
    const collision = selectedChecks.find(c => c.id === contextCheck.id)
    if (collision && digest(collision) !== digest(contextCheck)) throw new Error('harness-context is a reserved binding; reconcile the existing check explicitly')
    selectedChecks = [...selectedChecks.filter(c => c.id !== contextCheck.id), contextCheck]
  }
  const doctorEntry = `#!/usr/bin/env node\nimport { dirname, resolve } from 'node:path'\nimport { fileURLToPath } from 'node:url'\nimport { readJson } from '../.harness/runtime/core.mjs'\nimport { doctor } from '../.harness/runtime/doctor.mjs'\nconst root = resolve(dirname(fileURLToPath(import.meta.url)), '..')\nconst report = doctor(root, readJson(resolve(root, '.harness/project.json')), { receipt: process.argv[2] ? readJson(resolve(process.argv[2])) : undefined, receiptPath: process.argv[2] ? resolve(process.argv[2]) : undefined })\nconsole.log(JSON.stringify(report, null, 2))\nprocess.exitCode = report.healthy ? 0 : 1\n`
  asset('scripts/project-doctor.mjs', doctorEntry, 'Project-owned diagnostics without the factory')
  for (const old of oldLock?.blocks || []) if (!nextBlocks.some(b => b.path === old.path && b.id === old.id)) entryBlock(old.path, old.id, null)
  for (const [path, { state, content }] of entries) if (hash(content) !== state.hash) operations.push({ path, content, before_hash: state.hash, reason: 'Maintain generated instruction blocks; preserve human content', source: 'Reviewed host adapter' })
  const removed = new Set()
  for (const old of previous?.assets || []) if (old.owner === 'project-harness-context' && !generated.has(old.path)) {
    const state = fileState(safePath(root, old.path, { write: true }))
    if (state.hash !== old.hash) throw new Error(`Locally modified obsolete asset requires a manual merge plan: ${old.path}`)
    operations.push({ path: old.path, content: null, before_hash: state.hash, reason: 'Remove obsolete generated guidance after scope/host change', source: contextPath }); removed.add(old.path)
  }
  const pinnedNode = inventory.facts.find(f => f.kind === 'node-pin')?.value
  const sources = [...new Set([...(previous?.sources || []), ...inventory.assets.filter(a => a.kind === 'instructions' || a.kind === 'configuration').map(a => a.path), ...hostEntries, ...contextSources, ...(context ? [contextPath] : []), ...(features ? ['.harness/features.json'] : [])])].filter(p => !removed.has(p) && !generated.has(p) && !nextBlocks.some(b => b.path === p && p !== 'AGENTS.md' && p !== 'CLAUDE.md')).sort()
  const tools = inventory.packages.flatMap(p => p.tools)
  const stack = [tools.includes('typescript') ? 'typescript' : 'node', ...(tools.includes('vue') ? ['vue'] : []), ...(tools.includes('electron') ? ['electron'] : [])].join('-')
  const manifest = validate('manifest', { schema_version: 1, factory_version: VERSION, host, stack, node_major: /^v?\d+/.test(pinnedNode || '') ? Number(pinnedNode.match(/\d+/)[0]) : previous?.node_major ?? null, assets: [...generated].map(([path, content]) => ({ path, hash: hash(content), owner: owners.get(path) })), checks: selectedChecks, sources, limitations: [...new Set([...(previous?.limitations || []), 'Host discovery requires a real new-session smoke test', 'Desktop/native runtime is not certified by static or unit checks', 'Submodule and installed dependency contents are outside the project candidate digest', 'External CI acceptance is not configured by this local generator', ...(context ? [] : ['Verification-only installation: development rules and workflows are not configured'])])], ...(context ? { context: { profile: contextPath, lock: contextLockPath } } : {}) })
  if (features) manifest.features = '.harness/features.json'
  const manifestState = fileState(join(root, manifestPath))
  const content = JSON.stringify(manifest, null, 2) + '\n'
  if (manifestState.hash !== hash(content)) operations.push({ path: manifestPath, content, before_hash: manifestState.hash, reason: 'Bind existing tools, generated asset ownership and declared coverage', source: 'survey + selected checks' })
  return { inventory, plan: makePlan(root, { purpose, authorization_ref: authorizationRef, operations, checks: selectedChecks }) }
}
