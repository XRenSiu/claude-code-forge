import { existsSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { digest, hash, safePath } from './core.mjs'
import { validate } from './contracts.mjs'

export const contextPath = '.harness/context.json'
export const contextLockPath = '.harness/context-lock.json'
export const assessmentAreas = ['toolchain', 'architecture', 'testing', 'security', 'delivery', 'ci', 'hosts', 'skills', 'hooks', 'maintenance']
export const contextCheck = {
  id: 'harness-context', executable: 'node', argv: ['scripts/project-context.mjs', '{artifact_dir}'], cwd: '.',
  reporter: 'claims-json', report_file: 'claims.json', expected_claims: ['context-wiring'],
  depends_on: [], timeout_ms: 30000, required: true, effects: 'temporary-artifacts'
}
export function managedBlock(id, body) { return `<!-- project-harness:${id}:start -->\n${body.trim()}\n<!-- project-harness:${id}:end -->` }
export function extractBlock(text, id) {
  const start = `<!-- project-harness:${id}:start -->`, end = `<!-- project-harness:${id}:end -->`
  const a = text.indexOf(start), b = text.indexOf(end)
  if (a < 0 && b < 0) return null
  if (a < 0 || b < a || text.indexOf(start, a + 1) >= 0 || text.indexOf(end, b + 1) >= 0) throw new Error(`Malformed managed instruction block: ${id}`)
  return text.slice(a, b + end.length)
}
export function replaceBlock(text, id, block) {
  const old = extractBlock(text, id)
  return old === null ? (block ? text.trimEnd() + '\n\n' + block + '\n' : text) : text.replace(old, block || '')
}
const link = (from, target) => relative(dirname(from), target).split('\\').join('/')
const rulePath = rule => `docs/development/rules/${rule.id}.md`
export function instructionDirectories(scopes) {
  const dirs = new Set(['.'])
  for (const scope of scopes) {
    const parts = scope.split('/')
    for (let i = 1; i <= parts.length; i++) dirs.add(parts.slice(0, i).join('/'))
  }
  return [...dirs].sort()
}
export function sourceFingerprint(root, path) {
  let content = readFileSync(safePath(root, path), 'utf8')
  // Human instructions may be a source, but generated blocks must not hash themselves.
  for (const id of ['verification', 'context-codex', 'context-claude']) content = replaceBlock(content, id, '')
  return hash(content.trim())
}

export function validateContext(root, input) {
  const profile = validate('context', input)
  const unique = (values, label) => { if (new Set(values).size !== values.length) throw new Error(`Duplicate ${label}`) }
  unique(profile.rules.map(r => r.id), 'rule id'); unique(profile.workflows.map(w => w.id), 'workflow id')
  unique(profile.assessment.map(a => a.area), 'assessment area')
  for (const area of assessmentAreas) if (!profile.assessment.some(a => a.area === area)) throw new Error(`Missing assessment: ${area}`)
  if (!profile.rules.length || !profile.workflows.length) throw new Error('Development context needs project rules and workflows')
  if (!profile.rules.some(r => r.scopes.includes('.'))) throw new Error('Development context needs global guidance')
  for (const flow of profile.workflows) if (!flow.steps.length) throw new Error(`${flow.id}: workflow steps required`)
  for (const rule of profile.rules) {
    if (rule.body.includes('<!-- project-harness:')) throw new Error(`${rule.id}: reserved managed marker in rule body`)
    if (!rule.scopes.length || !rule.sources.length) throw new Error(`${rule.id}: scope and sources required`)
    unique(rule.scopes, `${rule.id} scope`)
    for (const scope of rule.scopes) {
      // Directory scopes have the same meaning in both hosts. No invented glob-to-directory equivalence.
      if (scope !== '.' && (!/^[\p{L}\p{N}_./-]+$/u.test(scope) || scope.split('/').some(p => !p || p === '.'))) throw new Error(`Invalid directory scope: ${scope}`)
      if (!statSync(safePath(root, scope, { allowRoot: true })).isDirectory()) throw new Error(`Scope is not a directory: ${scope}`)
    }
    if (rule.scopes.includes('.') && rule.scopes.length !== 1) throw new Error(`${rule.id}: global scope cannot be mixed with directories`)
  }
  for (const item of [...profile.rules, ...profile.workflows, ...profile.assessment]) {
    if (!item.sources.length) throw new Error(`${item.id || item.area}: sources required`)
    for (const source of item.sources) {
      if (source.startsWith('docs/development/') || source.startsWith('.harness/context')) throw new Error(`Circular generated source: ${source}`)
      if (!statSync(safePath(root, source)).isFile()) throw new Error(`Source is not a file: ${source}`)
    }
  }
  return profile
}

export function renderContext(root, profile, host) {
  validateContext(root, profile)
  const files = new Map(), blocks = [], scopes = [...new Set(profile.rules.flatMap(r => r.scopes).filter(s => s !== '.'))].sort()
  const sourceList = (item, file) => '\n\n依据 / Sources: ' + item.sources.map(s => `[${s}](${link(file, s)})`).join(' · ')
  const renderedRule = (r, file) => `# ${r.title}\n\n${r.body.trim()}${sourceList(r, file)}\n`
  const generated = '<!-- Generated from .harness/context.json; edit the profile and regenerate. -->\n'
  for (const rule of profile.rules) {
    files.set(rulePath(rule), generated + renderedRule(rule, rulePath(rule)))
    if (['dual', 'claude-code'].includes(host)) {
      const path = `.claude/rules/project-harness-${rule.id}.md`
      const frontmatter = rule.scopes.includes('.') ? '' : `---\npaths:\n${rule.scopes.map(s => `  - ${JSON.stringify(s + '/**/*')}`).join('\n')}\n---\n\n`
      files.set(path, frontmatter + generated + renderedRule(rule, path))
    }
  }
  for (const flow of profile.workflows) {
    const file = `docs/development/workflows/${flow.id}.md`
    files.set(file, `${generated}# ${flow.title}\n\n触发 / When: ${flow.when}\n\n${flow.steps.map((s, i) => `${i + 1}. ${s}`).join('\n')}${sourceList(flow, file)}\n`)
  }
  const indexPath = 'docs/development/README.md'
  files.set(indexPath, `${generated}# ${profile.project} 开发指南\n\n${profile.summary}\n\n## 规则\n\n${profile.rules.map(r => `- [${r.title}](rules/${r.id}.md) — ${r.scopes.join(', ')}`).join('\n')}\n\n## 工作流\n\n${profile.workflows.map(w => `- [${w.title}](workflows/${w.id}.md) — ${w.when}`).join('\n')}\n\n## 接入评估\n\n这些状态记录项目接入决策，不是运行通过证据。\n\n${profile.assessment.map(a => `### ${a.area}: ${a.status}\n\n${a.detail}${sourceList(a, indexPath)}`).join('\n\n')}\n\n## 维护\n\n编辑项目自有的 [.harness/context.json](../../.harness/context.json)，审阅来源与作用目录，再用 bootstrap 生成并应用计划。禁止只改某个宿主的派生副本。\n\n运行 \`node scripts/project-context.mjs\` 检查规则、来源、宿主入口与派生产物。来源变化提示重新阅读，不自动重写约定；生成内容损坏或入口缺失会失败。完整检查见 [project-harness.md](../project-harness.md)。\n\nClaude Code 使用 .claude/rules 的 paths；Codex 使用根入口路由与目录 AGENTS.md。Codex 从根目录启动后跨模块工作时，应先读取对应目录规则，不能假定启动时已加载所有嵌套指令。宿主新会话加载和实际行为需另行验证。\n`)
  if (['dual', 'codex'].includes(host)) {
    const rootBody = `## 项目开发规则\n\n开始任务时读 [开发指南](docs/development/README.md)，选择对应工作流。以下为全局约定：\n\n${profile.rules.filter(r => r.scopes.includes('.')).map(r => renderedRule(r, 'AGENTS.md').replace(/^# /, '### ')).join('\n')}\n### 模块规则路由\n\n从仓库根目录启动不会保证自动加载所有嵌套 AGENTS.md。读取或修改下列目录前，先读对应规则及目录 AGENTS.md；目录内启动时同样遵守根规则。\n\n${profile.rules.filter(r => !r.scopes.includes('.')).map(r => `- ${r.scopes.map(s => '`' + s + '/`').join(', ')} → [${r.title}](${rulePath(r)})`).join('\n')}`
    blocks.push({ path: 'AGENTS.md', id: 'context-codex', content: managedBlock('context-codex', rootBody) })
    for (const scope of scopes) {
      const path = `${scope}/AGENTS.md`
      const body = `## 本目录开发规则\n\n项目根规则继续适用；工作流见 [开发指南](${link(path, indexPath)})。\n\n${profile.rules.filter(r => !r.scopes.includes('.') && r.scopes.includes(scope)).map(r => renderedRule(r, path).replace(/^# /, '### ')).join('\n')}`
      blocks.push({ path, id: 'context-codex', content: managedBlock('context-codex', body) })
    }
  }
  if (['dual', 'claude-code'].includes(host)) blocks.push({ path: 'CLAUDE.md', id: 'context-claude', content: managedBlock('context-claude', '## 项目开发上下文\n\n开始任务时读 [开发指南](docs/development/README.md)，选择对应工作流。全局与目录规则位于 `.claude/rules/project-harness-*.md`；目录规则使用 paths 限定范围。规则定义统一维护在 `.harness/context.json`。') })
  return { files, blocks, scopes }
}

export function inspectContext(root, manifest) {
  const findings = [], add = (status, id, detail) => findings.push({ status, id, detail })
  try {
    if (Number(process.versions.node.split('.')[0]) < 22) add('FAIL', 'context-node', `Harness requires Node 22+; got ${process.versions.node}`)
    if (!manifest.context) { add('WARN', 'context-missing', 'Verification-only harness; development context has not been adopted'); return findings }
    const profile = JSON.parse(readFileSync(safePath(root, contextPath), 'utf8'))
    const lock = JSON.parse(readFileSync(safePath(root, contextLockPath), 'utf8'))
    const { files, blocks, scopes } = renderContext(root, profile, manifest.host)
    add(lock.profile_digest === digest(profile) ? 'PASS' : 'FAIL', 'context-profile', 'Profile matches reviewed generation')
    for (const [path, expected] of files) add(readFileSync(safePath(root, path), 'utf8') === expected ? 'PASS' : 'FAIL', `context-output:${path}`, 'Generated document matches profile')
    for (const block of blocks) {
      const actual = extractBlock(readFileSync(safePath(root, block.path), 'utf8'), block.id)
      add(actual === block.content ? 'PASS' : 'FAIL', `context-entry:${block.path}`, 'Managed instruction block matches profile')
    }
    if (['dual', 'codex'].includes(manifest.host)) for (const scope of instructionDirectories(scopes)) {
      const override = join(scope, 'AGENTS.override.md')
      if (existsSync(safePath(root, override))) add('FAIL', `context-override:${override}`, 'AGENTS.override.md shadows the generated AGENTS.md; reconcile explicitly')
      const chain = instructionDirectories([scope]).map(s => s === '.' ? 'AGENTS.md' : `${s}/AGENTS.md`).filter(p => existsSync(safePath(root, p)))
      const bytes = chain.reduce((sum, path) => sum + Buffer.byteLength(readFileSync(safePath(root, path))), 0)
      if (bytes > 24576) add('WARN', `context-budget:${scope}`, `Project instruction chain uses ${bytes} bytes; leave room for global instructions (default Codex limit 32768)`)
    }
    if (['dual', 'claude-code'].includes(manifest.host)) {
      for (const path of ['.claude/settings.json', '.claude/settings.local.json']) if (existsSync(safePath(root, path))) {
        const settings = JSON.parse(readFileSync(safePath(root, path), 'utf8'))
        if (settings.claudeMdExcludes?.length) add('WARN', `context-excludes:${path}`, 'Claude exclusion settings exist; inspect actual loading in a new session')
      }
      if (/@(?:\.\/)?AGENTS\.md\b/.test(readFileSync(safePath(root, 'CLAUDE.md'), 'utf8'))) add('WARN', 'context-shared-import', 'CLAUDE.md imports AGENTS.md; shared instructions may duplicate Claude rules. Preserve human decisions while consolidating the entry.')
    }
    const sources = [...new Set([...profile.rules, ...profile.workflows, ...profile.assessment].flatMap(x => x.sources))].sort()
    for (const path of sources) add(lock.sources?.[path] === sourceFingerprint(root, path) ? 'PASS' : 'WARN', `context-source:${path}`, 'Source fingerprint; changes require semantic review before regenerating')
    const businessChecks = manifest.checks.filter(c => c.id !== contextCheck.id && c.required && c.reporter !== 'exit-code')
    add(businessChecks.length ? 'PASS' : 'FAIL', 'context-native-checks', 'Context consistency alone cannot replace native project verification')
    add(manifest.checks.some(c => digest(c) === digest(contextCheck)) ? 'PASS' : 'FAIL', 'context-check-binding', 'Required context check uses the reviewed binding')
    for (const area of profile.assessment) if (area.status === 'gap') add('WARN', `context-gap:${area.area}`, area.detail)
    add('UNKNOWN', 'context-host-live', 'Static wiring is checked; host loading and behavior need separate real-session evidence')
  } catch (error) { add('FAIL', 'context-invalid', error.message) }
  return findings
}

export function contextReport(root, manifest) {
  const findings = inspectContext(root, manifest)
  const good = !!manifest.context && !findings.some(f => f.status === 'FAIL')
  return { schema_version: 1, complete: true, examined: findings.length, claims: [{ id: 'context-wiring', status: good ? 'PASS' : 'FAIL' }], findings, authority: 'project-self-check', host_behavior_verified: false }
}
