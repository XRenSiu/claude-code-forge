const s = { type: 'string', minLength: 1 }
const text = { type: 'string' }
const num = { type: 'integer', minimum: 0 }
const bool = { type: 'boolean' }
const nullableHash = { type: ['string', 'null'], pattern: '^[a-f0-9]{64}$' }
const arr = items => ({ type: 'array', items })
const obj = (properties, required = Object.keys(properties), extra = false) => ({ type: 'object', properties, required, additionalProperties: extra })
const version = { const: 1 }
export const checkSchema = obj({
  id: { ...s, pattern: '^[a-z0-9][a-z0-9-]*$' }, executable: s, argv: arr(text), cwd: text,
  reporter: { enum: ['vitest-json', 'eslint-json', 'tap', 'claims-json', 'product-json', 'exit-code'] },
  depends_on: arr(s), timeout_ms: { type: 'integer', minimum: 1, maximum: 3600000 }, required: bool,
  report_file: s, stdin: text, expected_claims: arr(s), platforms: arr(s),
  env: { type: 'object', additionalProperties: text }, reason: s,
  effects: { enum: ['read-only', 'temporary-artifacts', 'writes-project', 'external'] }
}, ['id', 'executable', 'argv', 'cwd', 'reporter', 'depends_on', 'timeout_ms', 'required', 'effects'])
const operation = obj({ path: s, content: { type: ['string', 'null'] }, before_hash: nullableHash, after_hash: nullableHash, reason: s, source: s })
const identifier = { ...s, pattern: '^[a-z0-9][a-z0-9-]*$' }
const manifestProperties = { schema_version: version, factory_version: s, host: { enum: ['codex', 'claude-code', 'dual', 'portable'] }, stack: s, node_major: { type: ['integer', 'null'] }, assets: arr(obj({ path: s, hash: s, owner: s })), checks: arr(checkSchema), sources: arr(s), limitations: arr(s) }
export const schemas = {
  context: obj({ schema_version: version, project: s, summary: s,
    rules: arr(obj({ id: identifier, title: s, scopes: arr(s), sources: arr(s), body: s })),
    workflows: arr(obj({ id: identifier, title: s, when: s, steps: arr(s), sources: arr(s) })),
    assessment: arr(obj({ area: { enum: ['toolchain', 'architecture', 'testing', 'security', 'delivery', 'ci', 'hosts', 'skills', 'hooks', 'maintenance'] }, status: { enum: ['configured', 'manual', 'not-applicable', 'gap'] }, detail: s, sources: arr(s) }))
  }),
  inventory: obj({ schema_version: version, factory_version: s, root: s, created_at: s, candidate: { type: 'object' }, scan: { type: 'object' }, packages: arr({ type: 'object' }), assets: arr({ type: 'object' }), facts: arr({ type: 'object' }), conflicts: arr({ type: 'object' }), unknowns: arr({ type: 'object' }) }),
  plan: obj({ schema_version: version, factory_version: s, root: s, created_at: s, purpose: s, authorization_ref: s, operations: arr(operation), checks: arr(checkSchema), digest: s }),
  manifest: obj({ ...manifestProperties, features: { const: '.harness/features.json' }, context: obj({ profile: { const: '.harness/context.json' }, lock: { const: '.harness/context-lock.json' } }) }, Object.keys(manifestProperties)),
  receipt: obj({ schema_version: version, evidence_kind: { const: 'project-self-check' }, factory_version: s, created_at: s, candidate: { type: 'object' }, candidate_after: { type: 'object' }, manifest_digest: s, environment: { type: 'object' }, expected_checks: arr(s), results: arr({ type: 'object' }), execution_complete: bool, checks_passed: bool, limitations: arr(s), external_acceptance: { type: 'object' } })
}

// This validator implements only the keywords used by the exported schemas.
export function validateValue(value, schema, path = '$') {
  if (schema.const !== undefined && value !== schema.const) throw new Error(`${path}: expected ${schema.const}`)
  if (schema.enum && !schema.enum.includes(value)) throw new Error(`${path}: unsupported value ${value}`)
  if (schema.type) {
    const types = [].concat(schema.type)
    const matches = types.some(type => type === 'null' ? value === null : type === 'array' ? Array.isArray(value) : type === 'object' ? value !== null && typeof value === 'object' && !Array.isArray(value) : type === 'integer' ? Number.isInteger(value) : typeof value === type)
    if (!matches) throw new Error(`${path}: expected ${types.join('|')}`)
  }
  if (typeof value === 'string') {
    if (schema.minLength && value.length < schema.minLength) throw new Error(`${path}: must not be empty`)
    if (schema.pattern && !new RegExp(schema.pattern).test(value)) throw new Error(`${path}: invalid format`)
  }
  if (typeof value === 'number' && ((schema.minimum !== undefined && value < schema.minimum) || (schema.maximum !== undefined && value > schema.maximum))) throw new Error(`${path}: out of range`)
  if (Array.isArray(value) && schema.items) value.forEach((item, i) => validateValue(item, schema.items, `${path}[${i}]`))
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    for (const key of schema.required || []) if (!Object.hasOwn(value, key)) throw new Error(`${path}.${key}: required`)
    for (const [key, item] of Object.entries(value)) {
      const child = schema.properties?.[key]
      if (child) validateValue(item, child, `${path}.${key}`)
      else if (schema.additionalProperties === false) throw new Error(`${path}.${key}: unknown field`)
      else if (typeof schema.additionalProperties === 'object') validateValue(item, schema.additionalProperties, `${path}.${key}`)
    }
  }
  return value
}
export function validate(kind, value) { if (!schemas[kind]) throw new Error(`Unknown contract: ${kind}`); return validateValue(value, schemas[kind]) }
export function validateChecks(checks) {
  const ids = new Set()
  for (const check of checks) {
    validateValue(check, checkSchema)
    if (ids.has(check.id)) throw new Error(`Duplicate check: ${check.id}`)
    ids.add(check.id)
    if (['claims-json', 'product-json'].includes(check.reporter) && !check.expected_claims?.length) throw new Error(`${check.id}: ${check.reporter} requires expected_claims`)
    if (check.expected_claims && new Set(check.expected_claims).size !== check.expected_claims.length) throw new Error(`${check.id}: duplicate expected claims`)
  }
  const done = new Set(), visiting = new Set()
  function visit(id) {
    if (!ids.has(id)) throw new Error(`Missing dependency: ${id}`)
    if (visiting.has(id)) throw new Error(`Dependency cycle: ${id}`)
    if (done.has(id)) return
    visiting.add(id)
    for (const dep of checks.find(c => c.id === id).depends_on) visit(dep)
    visiting.delete(id); done.add(id)
  }
  for (const id of ids) visit(id)
  return checks
}
