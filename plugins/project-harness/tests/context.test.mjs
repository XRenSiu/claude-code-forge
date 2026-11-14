import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync, symlinkSync } from 'node:fs'
import { join } from 'node:path'
import { spawnSync } from 'node:child_process'
import { fixture, put, check, claim } from './helpers.mjs'
import { bootstrap } from '../skills/bootstrap-project-harness/scripts/lib/bootstrap.mjs'
import { apply } from '../skills/bootstrap-project-harness/scripts/lib/apply.mjs'
import { readJson, snapshot } from '../skills/bootstrap-project-harness/scripts/lib/core.mjs'
import { assessmentAreas, contextReport } from '../skills/bootstrap-project-harness/scripts/lib/context.mjs'

function setup(t, extra = {}) {
  const f = fixture(t, { 'package.json': '{"name":"fixture","devDependencies":{"typescript":"*","electron":"*"}}', 'README.md': 'Architecture and verification requirements', 'src/ui/main.ts': 'export const label = "hi"', 'src/api/main.ts': 'export const route = "/"', 'AGENTS.md': '# Human entry\nKeep this decision.\n', ...extra })
  const context = { schema_version: 1, project: 'Fixture', summary: 'A project with UI and API boundaries.',
    rules: [
      { id: 'toolchain', title: 'Toolchain', scopes: ['.'], sources: ['package.json', 'AGENTS.md'], body: 'Read the native package scripts before changing dependencies.' },
      { id: 'ui', title: 'UI boundary', scopes: ['src/ui'], sources: ['README.md'], body: 'Use the UI adapter; do not import server internals.' }
    ],
    workflows: [{ id: 'feature', title: 'Feature', when: 'Changing behavior', steps: ['Read the relevant source.', 'Run native checks and inspect failures.'], sources: ['README.md'] }],
    assessment: assessmentAreas.map(area => ({ area, status: 'manual', detail: `Reviewed ${area}; real execution is separate.`, sources: ['README.md'] })) }
  const options = { host: 'dual', authorizationRef: 'Fixture-only change', checks: [check('native', claim())], context }
  function install(optionsOverride = {}) {
    const { plan } = bootstrap(f.root, { ...options, ...optionsOverride })
    apply(f.root, plan, { stateDir: f.artifacts, acceptedDigest: plan.digest })
    return readJson(join(f.root, '.harness/project.json'))
  }
  return { ...f, context, options, install }
}

test('dual host adoption preserves human guidance, scopes rules and runs standalone', t => {
  const f = setup(t)
  const before = snapshot(f.root).content_digest
  const { plan } = bootstrap(f.root, f.options)
  assert.equal(snapshot(f.root).content_digest, before)
  assert(plan.operations.some(o => o.path === '.claude/rules/project-harness-ui.md'))
  const manifest = f.install()
  assert.equal(manifest.stack, 'typescript-electron') // Never infer Vue from Electron.
  const rootEntry = readFileSync(join(f.root, 'AGENTS.md'), 'utf8')
  assert.match(rootEntry, /Keep this decision/)
  assert.match(rootEntry, /src\/ui/)
  assert.match(rootEntry, /docs\/development\/rules\/ui.md/)
  assert.doesNotMatch(rootEntry, /do not import server internals/)
  assert.match(readFileSync(join(f.root, 'src/ui/AGENTS.md'), 'utf8'), /do not import server internals/)
  assert.equal(existsSync(join(f.root, 'src/api/AGENTS.md')), false)
  assert.match(readFileSync(join(f.root, '.claude/rules/project-harness-ui.md'), 'utf8'), /^---\npaths:\n  - "src\/ui\/\*\*\/\*"/)
  assert.doesNotMatch(readFileSync(join(f.root, '.claude/rules/project-harness-toolchain.md'), 'utf8'), /^---/)
  const run = spawnSync(process.execPath, ['scripts/project-verify.mjs', f.artifacts], { cwd: f.root, encoding: 'utf8' })
  assert.equal(run.status, 0, run.stderr + run.stdout)
  const receipt = readJson(JSON.parse(run.stdout).receipt)
  assert.deepEqual(receipt.expected_checks, ['native', 'harness-context'])
  const result = contextReport(f.root, manifest)
  assert.equal(result.claims[0].status, 'PASS')
  assert.equal(result.findings.some(x => x.status === 'WARN'), false, JSON.stringify(result.findings))
  assert.equal(result.host_behavior_verified, false)
  const doctor = spawnSync(process.execPath, ['scripts/project-doctor.mjs'], { cwd: f.root, encoding: 'utf8' })
  assert.equal(doctor.status, 0, doctor.stderr + doctor.stdout)
  assert.equal(bootstrap(f.root, f.options).plan.operations.length, 0)
})

test('context edits regenerate both hosts; human instruction edits are preserved', t => {
  const f = setup(t); f.install()
  put(f.root, 'src/ui/AGENTS.md', 'Human module introduction\n' + readFileSync(join(f.root, 'src/ui/AGENTS.md'), 'utf8'))
  f.context.rules[1].body = 'UI requests must use the checked adapter.'
  const manifest = f.install()
  assert.match(readFileSync(join(f.root, 'src/ui/AGENTS.md'), 'utf8'), /Human module introduction/)
  assert.match(readFileSync(join(f.root, '.claude/rules/project-harness-ui.md'), 'utf8'), /checked adapter/)
  assert.equal(contextReport(f.root, manifest).claims[0].status, 'PASS')
})

test('manual edits in generated rules or managed blocks stop upgrade and fail checks', t => {
  for (const path of ['.claude/rules/project-harness-ui.md', 'src/ui/AGENTS.md']) {
    const f = setup(t); const manifest = f.install()
    put(f.root, path, readFileSync(join(f.root, path), 'utf8').replace('do not import server internals', 'import server internals'))
    assert.equal(contextReport(f.root, manifest).claims[0].status, 'FAIL')
    assert.throws(() => bootstrap(f.root, f.options), /manual merge/)
  }
})

test('removed or moved scope retires obsolete rules without removing human content', t => {
  const f = setup(t); f.install()
  put(f.root, 'src/ui/AGENTS.md', 'Human module introduction\n' + readFileSync(join(f.root, 'src/ui/AGENTS.md'), 'utf8'))
  f.context.rules[1].scopes = ['src/api']
  f.context.rules[1].id = 'api'
  const manifest = f.install()
  assert.equal(existsSync(join(f.root, '.claude/rules/project-harness-ui.md')), false)
  assert.equal(existsSync(join(f.root, 'docs/development/rules/ui.md')), false)
  assert.doesNotMatch(readFileSync(join(f.root, 'src/ui/AGENTS.md'), 'utf8'), /server internals/)
  assert.match(readFileSync(join(f.root, 'src/ui/AGENTS.md'), 'utf8'), /Human module introduction/)
  assert.match(readFileSync(join(f.root, 'src/api/AGENTS.md'), 'utf8'), /server internals/)
  assert.equal(contextReport(f.root, manifest).claims[0].status, 'PASS')
  assert.equal(bootstrap(f.root, f.options).plan.operations.length, 0)
})

test('source drift is visible; missing sources and shadowing overrides fail', t => {
  const f = setup(t); const manifest = f.install()
  put(f.root, 'README.md', 'A changed architectural decision')
  const changed = contextReport(f.root, manifest)
  assert(changed.findings.some(x => x.status === 'WARN' && x.id === 'context-source:README.md'))
  put(f.root, 'src/ui/AGENTS.override.md', 'Shadowing instructions')
  assert.equal(contextReport(f.root, manifest).claims[0].status, 'FAIL')
  assert.throws(() => bootstrap(f.root, f.options), /shadows/)
  f.context.rules[0].sources = ['missing.md']
  assert.throws(() => bootstrap(f.root, f.options), /ENOENT/)
})

test('unsafe, duplicate, nonexistent and falsely globbed scopes are rejected before writes', t => {
  for (const scope of ['../outside', '/absolute', 'src/**/*.ts', 'missing', 'src/ui/main.ts', 'src//ui']) {
    const f = setup(t); f.context.rules[1].scopes = [scope]
    assert.throws(() => bootstrap(f.root, f.options))
    assert.equal(existsSync(join(f.root, '.harness/project.json')), false)
  }
  const f = setup(t); f.context.rules.push(f.context.rules[0])
  assert.throws(() => bootstrap(f.root, f.options), /Duplicate rule/)
})

test('incomplete assessment and context-only checks cannot masquerade as a full harness', t => {
  const f = setup(t); f.context.assessment.pop()
  assert.throws(() => bootstrap(f.root, f.options), /Missing assessment/)
  const g = setup(t); const manifest = g.install({ checks: [] })
  assert.equal(contextReport(g.root, manifest).claims[0].status, 'FAIL')
  const run = spawnSync(process.execPath, ['scripts/project-verify.mjs', g.artifacts], { cwd: g.root, encoding: 'utf8' })
  assert.equal(run.status, 1)
})

test('host switch cleans owned adapters and preserves custom rules', t => {
  const f = setup(t, { '.claude/rules/custom.md': 'Human rule' }); f.install()
  const manifest = f.install({ host: 'codex' })
  assert.equal(existsSync(join(f.root, '.claude/rules/project-harness-ui.md')), false)
  assert.equal(readFileSync(join(f.root, '.claude/rules/custom.md'), 'utf8'), 'Human rule')
  assert.doesNotMatch(readFileSync(join(f.root, 'CLAUDE.md'), 'utf8'), /context-claude/)
  assert.equal(contextReport(f.root, manifest).claims[0].status, 'PASS')
  assert.equal(bootstrap(f.root, { ...f.options, host: 'codex' }).plan.operations.length, 0)
})

test('dual aliases resolve to one file without duplicate operations', t => {
  const f = setup(t)
  symlinkSync('AGENTS.md', join(f.root, 'CLAUDE.md'))
  const manifest = f.install()
  assert.equal(contextReport(f.root, manifest).claims[0].status, 'PASS')
  assert.equal(bootstrap(f.root, f.options).plan.operations.length, 0)
})

test('portable context has docs and verification without pretending to activate a host', t => {
  const f = setup(t); const manifest = f.install({ host: 'portable' })
  assert.equal(existsSync(join(f.root, '.claude/rules')), false)
  assert.equal(existsSync(join(f.root, 'src/ui/AGENTS.md')), false)
  assert.equal(contextReport(f.root, manifest).host_behavior_verified, false)
})

test('changed inputs require explicit review and cannot silently refresh provenance', t => {
  const f = setup(t); f.install()
  put(f.root, 'README.md', 'Changed source decision')
  assert.throws(() => bootstrap(f.root, { authorizationRef: 'Routine runtime upgrade' }), /pass --context explicitly/)
  f.install()
  assert.equal(bootstrap(f.root, { authorizationRef: 'Already reviewed' }).plan.operations.length, 0)
})

test('deleted managed blocks and intermediate overrides are not silently repaired or bypassed', t => {
  const f = setup(t); f.install()
  put(f.root, 'src/ui/AGENTS.md', '# Human replacement\n')
  assert.throws(() => bootstrap(f.root, f.options), /manual merge/)
  const g = setup(t, { 'src/AGENTS.override.md': 'Intermediate override' })
  assert.throws(() => bootstrap(g.root, g.options), /shadows/)
})

test('reserved binding collisions and instruction size/exclusion risks are surfaced', t => {
  const f = setup(t)
  assert.throws(() => bootstrap(f.root, { ...f.options, checks: [check('harness-context', claim())] }), /reserved binding/)
  put(f.root, 'AGENTS.md', 'Human instructions '.repeat(2000))
  put(f.root, '.claude/settings.json', '{"claudeMdExcludes":["**/CLAUDE.md"]}')
  const report = contextReport(f.root, f.install())
  assert(report.findings.some(f => f.id.startsWith('context-budget:') && f.status === 'WARN'))
  assert(report.findings.some(f => f.id.startsWith('context-excludes:') && f.status === 'WARN'))
})
