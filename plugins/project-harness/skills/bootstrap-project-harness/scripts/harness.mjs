#!/usr/bin/env node
import { resolve } from 'node:path'
import { readJson, writeJson } from './lib/core.mjs'
import { survey } from './lib/survey.mjs'
import { makePlan } from './lib/plan.mjs'
import { apply, recover } from './lib/apply.mjs'
import { verify } from './lib/verify.mjs'
import { bootstrap } from './lib/bootstrap.mjs'
import { doctor } from './lib/doctor.mjs'

const [command, ...argv] = process.argv.slice(2)
const opts = {}
const allowed = new Set(['root', 'out', 'proposal', 'plan', 'state-dir', 'accept-plan', 'manifest', 'artifact-dir', 'receipt', 'host', 'checks', 'context', 'features', 'authorization-ref', 'journal', 'max-files'])
try {
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i].replace(/^--/, '')
    if (!argv[i].startsWith('--') || !allowed.has(key) || argv[i + 1] === undefined || argv[i + 1].startsWith('--') || Object.hasOwn(opts, key)) throw new Error(`Invalid option ${argv[i]}`)
    opts[key] = argv[i + 1]
  }
  if (!command || command === 'help') {
    console.log('harness.mjs survey|bootstrap|plan|apply|recover|verify|doctor --root <repo> [--out <json>]\nSee references/commands.md for contracts and required options.')
  } else {
    const root = resolve(opts.root || process.cwd())
    const requireOpt = name => { if (!opts[name]) throw new Error(`--${name} required`); return opts[name] }
    const manifest = () => readJson(resolve(root, opts.manifest || '.harness/project.json'))
    let result
    if (command === 'survey') {
      const maxFiles = opts['max-files'] === undefined ? 25000 : Number(opts['max-files'])
      if (!Number.isInteger(maxFiles) || maxFiles < 1) throw new Error('--max-files must be a positive integer')
      result = survey(root, { maxFiles })
    } else if (command === 'bootstrap') {
      const created = bootstrap(root, { host: opts.host, authorizationRef: requireOpt('authorization-ref'), checks: opts.checks ? readJson(opts.checks) : undefined, context: opts.context ? readJson(opts.context) : undefined, features: opts.features ? readJson(opts.features) : undefined })
      result = created.plan
    } else if (command === 'plan') result = makePlan(root, readJson(requireOpt('proposal')))
    else if (command === 'apply') result = apply(root, readJson(requireOpt('plan')), { stateDir: requireOpt('state-dir'), acceptedDigest: requireOpt('accept-plan') })
    else if (command === 'recover') result = recover(root, requireOpt('journal'))
    else if (command === 'verify') {
      const controller = new AbortController()
      const abort = () => controller.abort()
      process.on('SIGINT', abort); process.on('SIGTERM', abort)
      try {
        result = await verify(root, manifest(), { outputDir: requireOpt('artifact-dir'), signal: controller.signal })
        process.exitCode = result.receipt.checks_passed ? 0 : result.receipt.execution_complete ? 1 : 2
      } finally { process.off('SIGINT', abort); process.off('SIGTERM', abort) }
    } else if (command === 'doctor') {
      result = doctor(root, manifest(), { receipt: opts.receipt ? readJson(opts.receipt) : undefined })
      process.exitCode = result.healthy ? 0 : 1
    } else throw new Error(`Unknown command: ${command}`)
    if (opts.out) { writeJson(opts.out, result); console.log(JSON.stringify({ output: resolve(opts.out), ...(result.digest ? { plan_digest: result.digest, operations: result.operations.length } : {}) })) }
    else console.log(JSON.stringify(result, null, 2))
  }
} catch (error) { console.error(JSON.stringify({ status: 'ERROR', message: error.message })); process.exitCode = 2 }
