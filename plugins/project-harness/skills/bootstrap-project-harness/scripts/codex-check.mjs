#!/usr/bin/env node
import { existsSync, realpathSync } from 'node:fs'
import { delimiter, isAbsolute, join, resolve } from 'node:path'
import { runProcess } from './lib/verify.mjs'
import { now, writeJson } from './lib/core.mjs'

const opts = {}
try {
  const args = process.argv.slice(2)
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, '')
    if (!args[i].startsWith('--') || !['binary', 'model', 'out'].includes(key) || !args[i + 1] || Object.hasOwn(opts, key)) throw new Error(`Invalid option: ${args[i]}`)
    opts[key] = args[i + 1]
  }
  if (!opts.model) throw new Error('--model required; use the requested or configured model, not an invented fallback')
  const name = opts.binary || 'codex'
  const binary = isAbsolute(name) || name.includes('/') ? resolve(name) : (process.env.PATH || '').split(delimiter).map(dir => join(dir, name)).find(path => existsSync(path))
  if (!binary || !existsSync(binary)) throw new Error(`Executable not found: ${name}`)
  const version = await runProcess(binary, ['--version'], { cwd: process.cwd(), timeoutMs: 10000 })
  const catalog = await runProcess(binary, ['debug', 'models'], { cwd: process.cwd(), timeoutMs: 30000 })
  let models = [], parseError = null
  try { models = JSON.parse(catalog.stdout).models || [] } catch (error) { parseError = error.message }
  const selected = models.find(model => model.slug === opts.model)
  const report = {
    schema_version: 1, created_at: now(), binary, resolved_binary: realpathSync(binary), version: version.stdout.trim(), requested_model: opts.model,
    compatible_metadata: version.code === 0 && catalog.code === 0 && !catalog.failure && Boolean(selected),
    model_metadata: selected ? { slug: selected.slug, context_window: selected.context_window, default_reasoning_level: selected.default_reasoning_level } : null,
    available_models: models.map(model => model.slug), catalog_error: catalog.failure || parseError || (catalog.code !== 0 ? catalog.stderr.slice(-2000) : null),
    live_request_verified: false,
    next_action: selected ? 'Run the authorized real task and retain its trace and fresh verification receipt' : 'Inspect PATH and upgrade the owning CLI installation; do not replace the requested model or edit shared model cache to disguise a mismatch'
  }
  if (opts.out) writeJson(opts.out, report)
  console.log(JSON.stringify(report, null, 2))
  if (!report.compatible_metadata) process.exitCode = 2
} catch (error) { console.error(JSON.stringify({ status: 'ERROR', message: error.message })); process.exitCode = 2 }
