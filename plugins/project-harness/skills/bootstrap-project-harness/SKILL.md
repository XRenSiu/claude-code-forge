---
name: bootstrap-project-harness
version: 0.2.0
description: 调查、搭建、验证和改进项目的 Coding Harness。适用于建立 AI 开发环境、诊断项目规则或验证流程不生效、将已验证的重复错误转为可执行防线；普通业务功能沿用项目现有流程。
---

# Project Harness

用项目已有的规范、开发入口和工具链建立完整、可维护的开发 harness：项目规则、双宿主上下文、开发工作流、原生检查、诊断与演进。模型负责理解、选型与解释；附带脚本负责调查、变更协议和可复核执行。需要 Node 22+，无安装依赖。所有路径相对本 skill 所在目录解析，不依赖当前工作目录。

先按用户意图选择 **audit / bootstrap / verify / evolve**。当前会话已授权的本地工作继续推进；计划摘要与 `authorization_ref` 仅记录审阅范围，不提供授权。对范围外动作或真实架构冲突才请求决策。

## Audit

读取目标仓库适用指令，然后读 [discovery.md](references/discovery.md)。执行 `node <skill>/scripts/harness.mjs survey --root <repo> --out <任务目录>/inventory.json`。

将事实、推断、冲突和未知分开。检查已有资产与项目 CI；扫描不到或无运行记录不等于缺能力。audit 到调查报告结束，不改目标仓库，也不运行项目命令。

## Bootstrap / upgrade

读取 [commands.md](references/commands.md)、[safe-apply.md](references/safe-apply.md) 和 [development-context.md](references/development-context.md)，根据 [adapters.md](references/adapters.md) 选择技术栈与宿主。

1. 先 survey，确定已有规范的唯一来源、实际命令、约束依据和副作用。用户请求生成或改进 harness 时可在授权范围落地。
2. 默认建立完整开发 harness：读取实际文档与模块源码，整理有依据的 rules、目录作用范围、开发工作流和十项接入评估，准备 context JSON。双宿主用 `bootstrap --host dual --context <file>`，保留已有原生检查，必要时显式传 checks。缺少受支持的原生检查时保留未完成状态；只检查规则一致性不能算项目验证通过。仅在用户明确要求验证运行器时使用不带 context 的低层入口。
3. 对 CI、hooks、skills、宿主加载和维护流程逐项评估，授权范围内补齐有实际用途的缺口。不要为了结构齐全生成无用目录，也不要把所有缺口记成 manual 就结束。既有架构和工具规则按来源保留，不能由依赖名称发明新规范。
4. 审阅 plan 中的完整文件内容、hash、理由、命令和授权范围。原生配置/指令冲突由模型读取后做最小合并，重建 proposal；不要绕过冲突。
5. 通过 `apply --accept-plan <digest>` 落地。这个参数绑定已审阅内容，不替代用户授权。任务状态目录置于项目外。
6. 按下一节实际验证。向用户交付路径、改动、规则依据、可复核收据、限制和下次使用命令。安装、生成、宿主发现和业务收益分别报告。

## Verify / doctor

读取 [verification.md](references/verification.md)。默认 manifest 是 `.harness/project.json`，先读其中的命令、范围和 effects，再检查对应原生配置。`doctor` 检查静态接线、资产漂移、临时环境和收据新鲜度，不执行项目检查。资产 hash 匹配且命令与任务范围相符时继续验证；出现漂移、错误或不明副作用时再深入 runtime/测试源码，避免每次重做完整实现审计。

`verify` 执行已审阅的检查图。测试创建并清理临时 fixture 属于正常验证行为；若用户连临时写入也明确禁止，使用隔离副本。证据目录与测试临时目录是两件事：保留系统 TMPDIR，不默认把它改到 artifacts 下；另一仓库的 Git 根和 package.json 也会污染临时 fixture。桌面 E2E 等副作用遵守项目约束。

所有必跑检查都要有真实结果。零测试、全 skip、缺报告、解析错误、超时、候选被修改都不能宣称通过。新增约束在一次性副本验证合法样例与违规样例，并检查实际错误来自预期规则。宿主发现要用新会话实测；仅有文件不能证明已生效。保留成本缺失、平台限制及未运行项。

诊断时临时修改检查参数得到的成功收据，不能替代项目原始绑定。可在授权范围修复的本地环境问题应继续处理，再按原绑定复跑；确有无法消除的限制时，明确报告哪些必跑项仍未完成。

## Product verification

用户要求真实产品操作、功能验证入口或检查器校准时，按 [product-verification.md](references/product-verification.md) 落地 feature index、五阶段驱动和原始证据。沿已有检查图绑定 `product-json`；校准必须实际执行正常候选、故障副本和恢复候选。不要把启动成功、报告字段或变异数量当作产品效果。

## Evolve

读取 [evolution.md](references/evolution.md)。从验证过的根因选择测试、原生规则或已有文档的最小改进，复用 survey → plan → apply → verify。不要为每次失败新增一份经验文件。

运行 `node <skill>/scripts/harness.mjs help` 查看入口。脚本契约示例与退出码见 commands；来源与方法取舍见 [upstreams.md](references/upstreams.md)。用户要求真实 Codex 会话验证或遇到模型兼容问题时，按 [codex-host.md](references/codex-host.md) 检查实际二进制和模型目录。
