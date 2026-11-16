import { readFileSync, statSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { safePath, digest } from './core.mjs'

const id = /^[a-z0-9][a-z0-9-]*$/
const strings = (value, nonempty = true) => Array.isArray(value) && (!nonempty || value.length > 0) && value.every(x => typeof x === 'string' && x.trim()) && new Set(value).size === value.length
const require = (value, message) => { if (!value) throw new Error(message) }

export function validateFeatures(root, index, checks) {
  require(index?.schema_version === 1 && Array.isArray(index.features) && index.features.length > 0, 'Nonempty feature index v1 required')
  const features = new Set(), entries = new Set(), checkIds = new Set()
  for (const feature of index.features) {
    require(id.test(feature.id) && !features.has(feature.id), 'Invalid or duplicate feature ID'); features.add(feature.id)
    require(typeof feature.title === 'string' && feature.title.trim() && strings(feature.sources), `${feature.id}: title and sources required`)
    require(Array.isArray(feature.entries) && feature.entries.length > 0, `${feature.id}: entries required`)
    if (feature.watch_paths !== undefined) require(strings(feature.watch_paths) && feature.watch_paths.every(p => !p.startsWith('/') && !p.includes('..') && !p.includes('*')), `${feature.id}: watch_paths uses literal repository paths or directory prefixes`)
    for (const path of feature.sources) require(statSync(safePath(root, path)).isFile(), `${path}: source must be a file`)
    for (const entry of feature.entries) {
      const key = `${feature.id}/${entry.id}`
      require(id.test(entry.id) && !entries.has(key), 'Invalid or duplicate entry ID'); entries.add(key)
      require(id.test(entry.check_id) && !checkIds.has(entry.check_id), `${key}: unique check_id required`); checkIds.add(entry.check_id)
      require(['http', 'web', 'desktop', 'cli', 'library'].includes(entry.surface), `${key}: unsupported surface`)
      for (const field of ['location', 'driver']) require(typeof entry[field] === 'string' && entry[field].trim(), `${key}: ${field} required`)
      for (const field of ['claims', 'evidence_types', 'checker_files', 'fixture_files', 'prerequisites']) require(strings(entry[field]), `${key}: nonempty unique ${field} required`)
      require(strings(entry.unsupported, false), `${key}: explicit unsupported scope required`)
      require(Array.isArray(entry.node_args) && entry.node_args.every(x => typeof x === 'string'), `${key}: node_args required`)
      require(Number.isInteger(entry.timeout_ms) && entry.timeout_ms > 0 && entry.timeout_ms <= 3600000, `${key}: bounded timeout required`)
      for (const path of [entry.driver, ...entry.checker_files, ...entry.fixture_files]) require(statSync(safePath(root, path)).isFile(), `${key}: missing runtime file ${path}`)
      if (entry.calibration_plan !== undefined) require(typeof entry.calibration_plan === 'string' && statSync(safePath(root, entry.calibration_plan)).isFile(), `${key}: calibration_plan must name the reviewed plan`)
      if (entry.exploration !== undefined) require(strings(entry.exploration.actions) && entry.exploration.actions.length <= 100, `${key}: exploration requires a bounded action alphabet`)
      if (checks) {
        const bound = checks.find(c => c.id === entry.check_id)
        require(bound?.required && bound.reporter === 'product-json' && digest(bound.expected_claims) === digest(entry.claims), `${key}: required product check and exact claims must be bound`)
      }
    }
  }
  return index
}

export function impact(root, index, base) {
  validateFeatures(root, index)
  const git = args => execFileSync('git', ['-C', root, ...args], { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 }).split('\0').filter(Boolean)
  let unborn = false
  if (base === 'HEAD') {
    try { execFileSync('git', ['-C', root, 'rev-parse', '--verify', 'HEAD'], { stdio: 'ignore' }) } catch { unborn = true }
  }
  const changed = [...new Set(unborn ? git(['ls-files', '--cached', '--others', '--exclude-standard', '-z']) : [...git(['diff', '--name-only', '--no-renames', '-z', base, '--']), ...git(['ls-files', '--others', '--exclude-standard', '-z'])])].sort()
  const covered = new Set(), selected = [], maintenance = []
  for (const feature of index.features) {
    const runtime = feature.entries.flatMap(e => [e.driver, ...e.checker_files, ...e.fixture_files, ...(e.calibration_plan ? [e.calibration_plan] : [])])
    const matched = changed.filter(p => [...feature.sources, ...runtime, ...(feature.watch_paths || [])].some(prefix => p === prefix || prefix.endsWith('/') && p.startsWith(prefix)))
    if (!matched.length) continue
    matched.forEach(p => covered.add(p))
    selected.push(...feature.entries.map(e => ({ feature: feature.id, entry: e.id, check_id: e.check_id, reasons: matched })))
    maintenance.push({ feature: feature.id, review: matched.some(p => runtime.includes(p)) ? 'driver_or_oracle_changed_recalibrate' : 'product_or_requirement_changed_review_index', paths: matched })
  }
  return { schema_version: 1, authority: 'selection_only', base, changed, selected, maintenance, unmapped: changed.filter(p => !covered.has(p)),
    requires_full_verification: true, note: 'Impact selection is fast feedback. Unmapped changes require review; it never replaces the complete native verification graph.' }
}

export function featureEntry(root, index, featureId, entryId) {
  validateFeatures(root, index)
  const feature = index.features.find(f => f.id === featureId)
  const entry = feature?.entries.find(e => e.id === entryId)
  require(entry, `Unknown feature entry ${featureId}/${entryId}`)
  return { feature, entry }
}

export function featureChecks(index) {
  return index.features.flatMap(f => f.entries.map(e => ({
    id: e.check_id, executable: 'node', argv: [...e.node_args, 'scripts/project-product.mjs', f.id, e.id, '{artifact_dir}'],
    cwd: '.', reporter: 'product-json', report_file: 'product.json', expected_claims: e.claims,
    depends_on: [], timeout_ms: e.timeout_ms, required: true, effects: 'temporary-artifacts'
  })))
}

export const filesDigest = (root, paths) => 'sha256:' + digest([...new Set(paths)].sort().map(path => [path, readFileSync(safePath(root, path), 'utf8')]))

export function renderFeatures(index) {
  return '# Product verification features\n\nGenerated from `.harness/features.json`. This is an index, not an execution verdict. Run the listed entry and inspect its current receipt. Product promises remain owned by the referenced requirements.\n\n' + index.features.map(f =>
    `## ${f.title} (${f.id})\n\nSources: ${f.sources.map(s => `[${s}](../${s})`).join(', ')}\n\n` + f.entries.map(e =>
      `### ${e.id}: ${e.surface} ${e.location}\n\nPrerequisites: ${e.prerequisites.join('; ')}\n\n\`node ${e.node_args.join(' ')} scripts/project-product.mjs ${f.id} ${e.id} /path/outside/project/evidence\`\n\nChecks: ${e.claims.join(', ')}. Evidence: ${e.evidence_types.join(', ')}.\n\nCalibration plan: ${e.calibration_plan ? `[${e.calibration_plan}](../${e.calibration_plan})` : 'Not bound; this entry has no current checker qualification.'}\n\nUnverified scope: ${e.unsupported.join('; ') || 'No additional scope declared; the named entry alone is covered.'}\n`
    ).join('\n')).join('\n')
}
