# Claude Code Forge - 项目规范

这是 Claude Code 插件市场项目。结构：`.claude-plugin/marketplace.json` → `plugins/<name>/` → skills / commands / agents / rules。

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
| 新增 skill / command / agent | — | minor (+0.1.0) | 1.1.0 → 1.2.0 |

### 修改文件后的同步清单

修改 skill 内容时，必须同时更新：
1. 该 skill 的 `SKILL.md` frontmatter `version`
2. `plugins/<name>/.claude-plugin/plugin.json` 的 `version`
3. `.claude-plugin/marketplace.json` 中对应插件的 `version`

新增 skill / command / agent 时，更新第 2、3 项。

## Commit 规范

遵循 Conventional Commits：

- `feat:` 新功能（新 skill / command / agent）
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
│       ├── commands/                   # 命令定义 (*.md)
│       ├── skills/                     # 技能定义 (SKILL.md)
│       ├── rules/                      # 约束规则 (*.md)
│       ├── hooks/hooks.json            # 事件钩子
│       └── docs/                       # 阶段文档
├── CONTRIBUTING.md
└── README.md
```

Commands、agents、skills、hooks 从目录自动发现，不需要在 plugin.json 中列举。
