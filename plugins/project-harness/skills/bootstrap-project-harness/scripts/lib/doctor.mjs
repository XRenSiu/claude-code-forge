import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { digest, hash, projectRoot, safePath, snapshot } from './core.mjs'
import { validate, validateChecks } from './contracts.mjs'
import { isCurrentReceipt } from './verify.mjs'
import { describeEnvironment } from './environment.mjs'
import { inspectContext } from './context.mjs'

export function doctor(rootPath, manifest, { receipt } = {}) {
  const root = projectRoot(rootPath), findings = []
  const add = (status, id, detail) => findings.push({ status, id, detail })
  validate('manifest', manifest); validateChecks(manifest.checks)
  const environment = describeEnvironment(root)
  if (Number(process.versions.node.split('.')[0]) < 22) add('FAIL', 'runtime-node', `Harness requires Node 22+; got ${process.versions.node}`)
  for (const warning of environment.warnings) add('WARN', 'temporary-environment', warning)
  for (const asset of manifest.assets) {
    try {
      const file = safePath(root, asset.path)
      const current = hash(readFileSync(file))
      add(current === asset.hash ? 'PASS' : 'WARN', `asset:${asset.path}`, current === asset.hash ? 'Matches managed version' : 'Local edit or drift; preserve and review before upgrade')
    } catch (error) { add('FAIL', `asset:${asset.path}`, error.message) }
  }
  const entries = manifest.host === 'dual' ? ['AGENTS.md', 'CLAUDE.md'] : manifest.host === 'codex' ? ['AGENTS.md'] : manifest.host === 'claude-code' ? ['CLAUDE.md'] : []
  for (const entry of entries) {
    try { const text = readFileSync(safePath(root, entry), 'utf8'); add(text.includes('docs/project-harness.md') ? 'PASS' : 'WARN', 'entry-link', `Static ${entry} reference ${text.includes('docs/project-harness.md') ? 'present' : 'missing'}`) } catch (error) { add('FAIL', 'entry-link', error.message) }
    add('UNKNOWN', 'host-live-discovery', 'File presence does not establish host loading; run a new host session and retain its trace')
  }
  findings.push(...inspectContext(root, manifest))
  if (!manifest.checks.length) add('FAIL', 'checks', 'No check bindings; add a native checker with a supported reporter')
  if (manifest.checks.some(c => c.reporter === 'exit-code')) add('WARN', 'exit-only', 'Exit-only bindings cannot produce PASS evidence')
  if (manifest.node_major !== null && Number(process.versions.node.split('.')[0]) !== manifest.node_major) add('FAIL', 'node-version', `Expected ${manifest.node_major}; got ${process.versions.node}`)
  if (receipt) {
    add(isCurrentReceipt(root, manifest, receipt) ? 'PASS' : 'FAIL', 'receipt-current', 'Candidate and manifest digests compared with the supplied receipt')
    add(receipt.checks_passed ? 'PASS' : 'FAIL', 'receipt-verdict', 'Supplied receipt execution verdict')
  } else add('UNKNOWN', 'receipt', 'No execution receipt supplied')
  for (const source of manifest.sources) if (!existsSync(join(root, source))) add('WARN', `source:${source}`, 'Referenced source is missing')
  return { schema_version: 1, manifest_digest: digest(manifest), environment, findings, healthy: !findings.some(f => f.status === 'FAIL'), verified: findings.every(f => f.status === 'PASS') }
}
