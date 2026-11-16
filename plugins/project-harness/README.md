# Project Harness

**v0.4.0** · Node.js 22+ · 无安装依赖 · MIT（继承仓库 LICENSE）。

`/bootstrap-project-harness` 调查现有项目、生成可审阅计划、处理冲突并落地完整开发 Harness，再执行检查并保存绑定候选的收据。保留已有原生规则、文档和工具链，支持 Codex、Claude Code 与 portable 宿主。

## 安装和使用

```text
/plugin install project-harness@claude-code-forge
/project-harness:bootstrap-project-harness 为当前项目建立或完善完整开发 harness，并实际验证
```

安装或更新后新开 Claude Code 会话。也可以从源码加载：

```bash
claude --plugin-dir /absolute/path/to/claude-code-forge/plugins/project-harness
```

Codex 使用完整 `skills/bootstrap-project-harness/` 目录及其 `agents/openai.yaml`，按宿主支持的技能安装方式调用 `$bootstrap-project-harness`。

| 意图 | 作用 |
|---|---|
| audit | 只读调查规范、命令、资产、冲突与未知，不运行项目命令 |
| bootstrap / upgrade | 整理有来源的规则与工作流、生成双宿主入口，复用原生配置，安全应用并保留恢复日志 |
| verify / doctor | verify 实际执行检查图；doctor 检查规则、来源、入口、漂移、环境和收据 |
| evolve | 从已验证根因选取测试、原生规则或文档的最小改进 |

脚本可直接调用：

```bash
node plugins/project-harness/skills/bootstrap-project-harness/scripts/harness.mjs help
node plugins/project-harness/skills/bootstrap-project-harness/scripts/harness.mjs survey \
  --root /path/to/project --out /path/outside/project/inventory.json
```

完整入口见 [SKILL.md](skills/bootstrap-project-harness/SKILL.md)，命令参数与退出码见 [commands.md](skills/bootstrap-project-harness/references/commands.md)。

## 开发上下文

默认使用 `--host dual --context <reviewed-profile.json>`。生成 `.claude/rules/`、根与模块 `AGENTS.md`、`docs/development/` 中的规则/工作流/接入评估，以及项目独立的 `project-context.mjs` 和 `project-doctor.mjs`。规则定义统一维护在 `.harness/context.json`；来源变化提示复核，派生文件或入口损坏会使检查失败。

完整合同与十项覆盖要求见 [development-context.md](skills/bootstrap-project-harness/references/development-context.md)。低层不带 context 的命令仍可生成验证运行器，但明确标为 verification-only，不能当成完整开发环境交付。

## 真实产品验证

索引现在还生成双宿主 `verify-project` 技能、`project-impact.mjs` 影响分析和 `project-explore.mjs` 序列探索。探索保留种子、实际轨迹、同一失败的复现与缩减结果，可原样回放；有限模型要求显式假设、实现映射和完整遍历状态，不能代替实际产品轨迹。截图通过二进制捕获保留，语义结果仍由数据/状态观察给出。未映射变更与检查器变更会列入维护项，最终全量原生检查不缩减。

`project-learn.mjs` 将已复现反例经过固定失败候选、正确候选和完整原生检查的资格验证后，在限定授权内加入回归样例。下次探索先执行这些样例再跑原随机预算；缺失或漂移证据拒绝加载，观察和回退保留历史。它只学习动作数据，不自动放宽规则、合同或验收判据。详见 [自我改进闭环](skills/bootstrap-project-harness/references/learning.md)。

功能索引把用户入口连接到实际驱动、检查断言和未覆盖范围。产品运行器执行启动、健康检查、操作、观察与清理，保留原始证据；校准运行器在临时副本中注入故障，检查对应业务断言是否抓住故障，并保留正常 → 故障 → 恢复证据链。doctor 可重读每个入口的原始证据并区分未运行、当前通过、过期和损坏；每次运行绑定独立 invocation，拒绝同一候选的旧报告重放。升级后须重跑生成新格式证据。详见 [驱动与索引合同](skills/bootstrap-project-harness/references/product-verification.md)。本地结果不签发正式验收。

## 导入来源与验证

从用户提供的 `bootstrap-project-harness-0.1.1.tar.gz` 导入。归档摘要及逐文件原始摘要保存在 [source.json](source.json)。v0.1.1 导入时保留全部 22 个 Skill 文件，忽略 macOS AppleDouble 元数据。`source.json` 保留原始导入来源；v0.2.0 在此基础上增加项目上下文编译、双宿主规则、工作流、覆盖评估与独立诊断，并修正 Electron 被直接标成 Vue 的技术栈推断。当前源码已不同于原归档。

随包加入匹配开发项目的回归测试，只有模块导入路径由 `../skill/` 调整为本插件的 `../skills/`。运行：

```bash
node --test plugins/project-harness/tests/*.test.mjs
claude plugin validate plugins/project-harness
claude plugin validate plugins/project-harness/skills
```

测试覆盖双宿主作用域、根入口路由、来源漂移、手改冲突、规则退役、宿主切换、重复生成、独立上下文运行器，以及只读调查、可恢复写入、过期计划拒绝、重复生成、独立项目运行器、检查依赖图、失败/超时/取消、报告缺失、零测试、候选变化与临时环境影响。使用一次性 fixture，不给本仓库自动生成 Harness，也不递归启动模型会话。

本次导入验证针对插件包装及确定性工具。实际模型使用效果、Windows 进程清理和 Electron 桌面行为需要各自的运行验证。源参考文件中的开发报告/锁文件属于原开发仓库，未包含在此 Skill 归档中。

## 与 Trusted Acceptance 配合

Project Harness 负责项目的开发接入、自测和可复核收据。已生成的项目运行器携带固定 runtime，可以在不安装这个工厂 Skill 的情况下继续使用。

[Trusted Acceptance](../trusted-acceptance/README.md) 负责固定候选的独立验收入口。这里的本地收据属于 `project-self-check`，不能替代受保护 CI、批准合同或可信签发；两者没有自动接通或隐含交付授权。
