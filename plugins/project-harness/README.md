# Project Harness

**v0.1.1** · Node.js 22+ · 无安装依赖 · MIT（继承仓库 LICENSE）。

`/bootstrap-project-harness` 调查现有项目、生成可审阅计划、处理冲突并落地最小 Coding Harness，再执行检查并保存绑定候选的收据。保留已有原生规则、文档和工具链，支持 Codex、Claude Code 与 portable 宿主。

## 安装和使用

```text
/plugin install project-harness@claude-code-forge
/project-harness:bootstrap-project-harness 为当前项目建立或完善最小 harness，并实际验证
```

安装或更新后新开 Claude Code 会话。也可以从源码加载：

```bash
claude --plugin-dir /absolute/path/to/claude-code-forge/plugins/project-harness
```

Codex 使用完整 `skills/bootstrap-project-harness/` 目录及其 `agents/openai.yaml`，按宿主支持的技能安装方式调用 `$bootstrap-project-harness`。

| 意图 | 作用 |
|---|---|
| audit | 只读调查规范、命令、资产、冲突与未知，不运行项目命令 |
| bootstrap / upgrade | 生成内容和 hash 可审阅的计划，复用原生配置，安全应用并保留恢复日志 |
| verify / doctor | verify 实际执行检查图；doctor 只检查接线、漂移、环境和收据 |
| evolve | 从已验证根因选取测试、原生规则或文档的最小改进 |

脚本可直接调用：

```bash
node plugins/project-harness/skills/bootstrap-project-harness/scripts/harness.mjs help
node plugins/project-harness/skills/bootstrap-project-harness/scripts/harness.mjs survey \
  --root /path/to/project --out /path/outside/project/inventory.json
```

完整入口见 [SKILL.md](skills/bootstrap-project-harness/SKILL.md)，命令参数与退出码见 [commands.md](skills/bootstrap-project-harness/references/commands.md)。

## 导入来源与验证

从用户提供的 `bootstrap-project-harness-0.1.1.tar.gz` 导入。归档摘要及逐文件原始摘要保存在 [source.json](source.json)。保留全部 22 个 Skill 文件，仅在 SKILL.md frontmatter 加入仓库要求的 `version: 0.1.1`；忽略 macOS AppleDouble 元数据。脚本和参考文件保持原包内容。

随包加入匹配开发项目的回归测试，只有模块导入路径由 `../skill/` 调整为本插件的 `../skills/`。运行：

```bash
node --test plugins/project-harness/tests/*.test.mjs
claude plugin validate plugins/project-harness
claude plugin validate plugins/project-harness/skills
```

测试覆盖只读调查、可恢复写入、过期计划拒绝、重复生成、独立项目运行器、检查依赖图、失败/超时/取消、报告缺失、零测试、候选变化与临时环境影响。使用一次性 fixture，不给本仓库自动生成 Harness，也不递归启动模型会话。

本次导入验证针对插件包装及确定性工具。实际模型使用效果、Windows 进程清理和 Electron 桌面行为需要各自的运行验证。源参考文件中的开发报告/锁文件属于原开发仓库，未包含在此 Skill 归档中。

## 与 Trusted Acceptance 配合

Project Harness 负责项目的开发接入、自测和可复核收据。已生成的项目运行器携带固定 runtime，可以在不安装这个工厂 Skill 的情况下继续使用。

[Trusted Acceptance](../trusted-acceptance/README.md) 负责固定候选的独立验收入口。这里的本地收据属于 `project-self-check`，不能替代受保护 CI、批准合同或可信签发；两者没有自动接通或隐含交付授权。
