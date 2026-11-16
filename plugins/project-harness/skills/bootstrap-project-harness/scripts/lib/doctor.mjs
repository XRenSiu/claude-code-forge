import { existsSync, readFileSync, realpathSync } from 'node:fs'
import { join, dirname, basename, resolve } from 'node:path'
import { digest, hash, projectRoot, safePath } from './core.mjs'
import { validate, validateChecks } from './contracts.mjs'
import { isCurrentReceipt } from './verify.mjs'
import { describeEnvironment } from './environment.mjs'
import { inspectContext } from './context.mjs'
import { validateFeatures } from './features.mjs'
import { productBinding, validateProduct, evidenceFile } from './product.mjs'

export function doctor(rootPath, manifest, { receipt, receiptPath } = {}) {
  const root = projectRoot(rootPath), findings = []
  const productEntries = []
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
  let index
  if (manifest.features) {
    try { index = validateFeatures(root, JSON.parse(readFileSync(safePath(root, manifest.features), 'utf8')), manifest.checks); add('PASS', 'feature-index', 'Feature sources, drivers, fixtures and required checks are linked') }
    catch (error) { add('FAIL', 'feature-index', error.message) }
  }
  if (!manifest.checks.length) add('FAIL', 'checks', 'No check bindings; add a native checker with a supported reporter')
  if (manifest.checks.some(c => c.reporter === 'exit-code')) add('WARN', 'exit-only', 'Exit-only bindings cannot produce PASS evidence')
  if (manifest.node_major !== null && Number(process.versions.node.split('.')[0]) !== manifest.node_major) add('FAIL', 'node-version', `Expected ${manifest.node_major}; got ${process.versions.node}`)
  let current = false, matrix = false, artifactRoot
  if (receipt) {
    try {
      current = isCurrentReceipt(root, manifest, receipt)
      add(current ? 'PASS' : 'FAIL', 'receipt-current', 'Candidate, manifest and Node environment compared with the supplied receipt')
      const expected = manifest.checks.map(c => c.id), actual = receipt.results.map(r => r.id)
      matrix = digest(receipt.expected_checks) === digest(expected) && new Set(actual).size === actual.length && actual.length === expected.length && expected.every(id => actual.includes(id))
      add(matrix ? 'PASS' : 'FAIL', 'receipt-coverage', 'Complete check matrix must match the manifest')
      const required = manifest.checks.filter(c => c.required && (!c.platforms || c.platforms.includes(process.platform)))
      const passed = matrix && receipt.execution_complete && required.length && required.every(c => receipt.results.find(r => r.id === c.id)?.status === 'PASS')
      add(passed && receipt.checks_passed ? 'PASS' : 'FAIL', 'receipt-verdict', 'Required check outcomes and supplied execution verdict compared')
      if (receiptPath) {
        const path = resolve(receiptPath)
        const saved = JSON.parse(readFileSync(evidenceFile(dirname(path), basename(path)), 'utf8'))
        if (digest(saved) !== digest(receipt)) throw new Error('Supplied receipt differs from the saved artifact')
        artifactRoot = realpathSync(dirname(path))
      }
    } catch (error) { matrix = false; add('FAIL', 'receipt-evidence', error.message) }
  } else add('UNKNOWN', 'receipt', 'No execution receipt supplied')
  if (index) for (const feature of index.features) for (const entry of feature.entries) {
    const item = { feature_id: feature.id, entry_id: entry.id, check_id: entry.check_id, status: 'NOT_RUN' }
    if (!receipt) item.reason = 'No execution receipt supplied'
    else if (!current) { item.status = 'STALE'; item.reason = 'Receipt does not describe the current candidate and environment' }
    else if (!matrix) { item.status = 'ERROR'; item.reason = 'Invalid receipt coverage or saved artifact' }
    else if (!artifactRoot) item.reason = 'Supply receiptPath to inspect raw evidence; a summary object is insufficient'
    else {
      const result = receipt.results.find(r => r.id === entry.check_id)
      if (['NOT_RUN', 'NOT_APPLICABLE'].includes(result.status)) { item.status = result.status; item.reason = result.reason || 'Entry was not executed' }
      else try {
        const check = manifest.checks.find(c => c.id === entry.check_id)
        const folder = realpathSync(join(artifactRoot, check.id))
        if (folder !== join(artifactRoot, check.id) || realpathSync(result.artifacts) !== folder) throw new Error('Product artifacts do not belong to this attempt')
        if (typeof result.invocation_id !== 'string') throw new Error('Missing product invocation identity; rerun the entry')
        const raw = JSON.parse(readFileSync(evidenceFile(folder, check.report_file), 'utf8'))
        const binding = productBinding(root, index, feature.id, entry.id, receipt.candidate.content_digest)
        const observed = validateProduct(raw, folder, entry.claims, { invocationId: result.invocation_id, binding, evidenceTypes: entry.evidence_types })
        if (observed.status !== result.status) throw new Error('Product summary contradicts raw observations')
        Object.assign(item, observed)
      } catch (error) { item.status = 'ERROR'; item.reason = error.message }
    }
    productEntries.push(item)
    add(item.status === 'PASS' ? 'PASS' : ['NOT_RUN', 'NOT_APPLICABLE'].includes(item.status) ? 'UNKNOWN' : 'FAIL', `product:${feature.id}/${entry.id}`, item.reason || 'Raw observations, invocation and current bindings verified')
  }
  for (const source of manifest.sources) if (!existsSync(join(root, source))) add('WARN', `source:${source}`, 'Referenced source is missing')
  return { schema_version: 1, manifest_digest: digest(manifest), environment, findings, product_entries: productEntries,
    product_verified: productEntries.length > 0 && productEntries.every(e => e.status === 'PASS'),
    healthy: !findings.some(f => f.status === 'FAIL'), verified: findings.every(f => f.status === 'PASS') }
}
