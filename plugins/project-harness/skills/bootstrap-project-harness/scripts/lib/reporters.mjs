const count = value => Number.isInteger(value) && value >= 0
const error = reason => ({ status: 'ERROR', reason })
export function parseReport(check, text, exitCode) {
  if (check.reporter === 'exit-code') return { status: exitCode === 0 ? 'NOT_RUN' : 'ERROR', reason: 'Exit status alone does not demonstrate assertions or scanned files' }
  try {
    let result
    if (check.reporter === 'vitest-json') {
      const data = JSON.parse(text)
      const assertions = (data.testResults || []).flatMap(suite => suite.assertionResults || [])
      const passed = assertions.filter(a => a.status === 'passed').length
      const failed = assertions.filter(a => a.status === 'failed').length
      const skipped = assertions.filter(a => ['pending', 'skipped', 'todo', 'disabled'].includes(a.status)).length
      if (!count(data.numTotalTests) || !Array.isArray(data.testResults) || assertions.length !== data.numTotalTests || passed + failed + skipped !== assertions.length) return error('Invalid/incomplete Vitest assertion matrix')
      if (data.numPassedTests !== passed || data.numFailedTests !== failed) return error('Vitest aggregate/assertion counts disagree')
      result = { status: failed ? 'FAIL' : passed ? 'PASS' : 'NOT_RUN', collected: assertions.length, executed: passed + failed, passed, failed, skipped }
    } else if (check.reporter === 'eslint-json') {
      const data = JSON.parse(text)
      if (!Array.isArray(data) || data.some(row => typeof row.filePath !== 'string' || !Array.isArray(row.messages) || !count(row.errorCount) || !count(row.fatalErrorCount))) return error('Invalid ESLint file results')
      const ignored = row => row.messages.some(m => /File ignored|no matching configuration/i.test(m.message || ''))
      const analyzed = data.filter(row => !ignored(row))
      const fatals = analyzed.reduce((n, row) => n + row.fatalErrorCount, 0)
      const errors = analyzed.reduce((n, row) => n + row.errorCount, 0)
      const warnings = analyzed.reduce((n, row) => n + (row.warningCount || 0), 0)
      result = { status: fatals ? 'ERROR' : errors ? 'FAIL' : analyzed.length ? 'PASS' : 'NOT_RUN', analyzed_files: analyzed.length, ignored_files: data.length - analyzed.length, errors, warnings, messages: analyzed.flatMap(row => row.messages.map(m => ({ path: row.filePath, line: m.line, rule: m.ruleId, message: m.message }))).slice(0, 100) }
    } else if (check.reporter === 'tap') {
      const counters = {}
      for (const match of text.matchAll(/^# (tests|pass|fail|cancelled|skipped|todo) (\d+)\s*$/gm)) counters[match[1]] = Number(match[2])
      const { tests, pass, fail, cancelled, skipped, todo } = counters
      if (![tests, pass, fail, cancelled, skipped, todo].every(count) || pass + fail + cancelled + skipped + todo !== tests) return error('Missing/inconsistent TAP terminal counters')
      // Node counts an empty test file as a passing subtest. Require evidence
      // of named tests rather than treating that file wrapper as an assertion.
      const names = [...text.matchAll(/^\s*# Subtest: (.+)$/gm)].map(match => match[1].trim())
      const named = names.filter(name => !/^(?:\S+\/)*[\w.-]+\.(?:[cm]?js|[cm]?ts|tsx)$/.test(name)).length
      result = { status: cancelled ? 'ERROR' : fail ? 'FAIL' : pass && named ? 'PASS' : 'NOT_RUN', collected: tests, executed: pass + fail, named_subtests: named, passed: pass, failed: fail, skipped: skipped + todo }
    } else if (check.reporter === 'claims-json') {
      const data = JSON.parse(text)
      if (data.schema_version !== 1 || data.complete !== true || !count(data.examined) || !Array.isArray(data.claims)) return error('Incomplete claims evidence')
      const ids = data.claims.map(claim => claim.id)
      if (new Set(ids).size !== ids.length || ids.length !== check.expected_claims.length || check.expected_claims.some(id => !ids.includes(id))) return error('Missing, extra or duplicate claims')
      if (data.claims.some(claim => !['PASS', 'FAIL'].includes(claim.status))) return error('Claims contain unsupported or unverified status')
      result = { status: !data.examined ? 'NOT_RUN' : data.claims.some(c => c.status === 'FAIL') ? 'FAIL' : 'PASS', examined: data.examined, claims: data.claims }
    } else return error('Unknown reporter')
    if (exitCode !== 0 && result.status !== 'FAIL') return { ...result, status: 'ERROR', reason: `Process exit ${exitCode} contradicts or invalidates report` }
    if (result.status === 'NOT_RUN') result.reason = 'No assertions or source files were actually checked'
    return result
  } catch (cause) { return error(`Cannot parse ${check.reporter}: ${cause.message}`) }
}
