# Claude Code Forge - 项目规范

这是 Claude Code 插件市场项目。结构：`.claude-plugin/marketplace.json` → `plugins/<name>/` → skills / agents / rules。

## 版本管理

使用语义化版本 (SemVer)。三处版本必须同步：

| 文件 | 作用 |
|------|------|
| `plugins/<name>/skills/<skill>/SKILL.md` frontmatter `version` | Skill 自身版本 |
| `plugins/<name>/.claude-plugin/plugin.json` `version` | 插件版本（源头） |
| `.claude-plugin/marketplace.json` 对应插件的 `version` | 市场注册表（与 plugin.json 同步） |

### 什么时候 bump

| 变更类型 | Skill 版本 | Plugin 版本 | 示例 |
|---------|-----------|------------|------|
| 修复 typo / 格式调整 | patch (+0.0.1) | patch (+0.0.1) | 1.0.0 → 1.0.1 |
| 功能增强 / 流程变更 | minor (+0.1.0) | minor (+0.1.0) | 1.0.0 → 1.1.0 |
| 不兼容变更 / 重大重构 | major (+1.0.0) | major (+1.0.0) | 1.0.0 → 2.0.0 |
| 新增 skill / agent | — | minor (+0.1.0) | 1.1.0 → 1.2.0 |

### 修改文件后的同步清单

修改 skill 内容时，必须同时更新：
1. 该 skill 的 `SKILL.md` frontmatter `version`
2. `plugins/<name>/.claude-plugin/plugin.json` 的 `version`
3. `.claude-plugin/marketplace.json` 中对应插件的 `version`

新增 skill / agent 时，更新第 2、3 项。

### 新建插件（plugin）的额外步骤

新增**整个 plugin**（不是给已存在 plugin 加 skill/agent）时，除上面三处外还要做：

4. **本机启用**：在 `~/.claude/settings.json` 的 `enabledPlugins` 字典加一条：
   ```json
   "enabledPlugins": {
     "<plugin-name>@claude-code-forge": true
   }
   ```
5. **重启 Claude Code 会话**——`Skill` 工具的可用列表在 session 启动时定型，运行中改 `settings.json` 不会热加载。

第 4-5 步是**用户级、不入 git** 的本机配置，但它决定了你能不能调用新 plugin 的 skill。漏了它就会得到 `Unknown skill` 报错，且本会话无法补救（必须新开 session）。

> 历史 bug：`bespoke-design-system` v1.8.0 完整注册到 `marketplace.json` 但漏了 `enabledPlugins`，导致用户调 `/bespoke-design-system` 时 Skill 工具找不到。详见 `~/.claude/projects/.../memory/feedback_plugin_enable_required.md`。

## Commit 规范

遵循 Conventional Commits：

- `feat:` 新功能（新 skill / agent）
- `fix:` 修复
- `refactor:` 重构
- `docs:` 文档
- `chore:` 维护（版本 bump、配置变更）

版本 bump 单独提交：`chore: bump <plugin> to v<version> with <description>`

## 项目结构

```
claude-code-forge/
├── .claude-plugin/marketplace.json   # 市场注册表
├── plugins/
│   └── <plugin-name>/
│       ├── .claude-plugin/plugin.json  # 插件清单
│       ├── agents/                     # Agent 定义 (*.md)
│       ├── skills/                     # Skill 定义 (<name>/SKILL.md)，也作为斜杠命令入口
│       ├── rules/                      # 约束规则 (*.md)
│       ├── hooks/hooks.json            # 事件钩子
│       └── docs/                       # 阶段文档
├── CONTRIBUTING.md
└── README.md
```

Agents、skills、rules、hooks 从目录自动发现，不需要在 plugin.json 中列举。
Skill 的 `name` 字段决定斜杠命令名（如 `name: forge-teams` → `/forge-teams`）。
