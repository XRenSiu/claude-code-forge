# Trusted Acceptance

一个 `/accept-change` 入口，把原始需求、冻结标准、固定候选、逐项证据与失败分流连起来。**v0.4.1**，Python 3.9+ 标准库，MIT（继承仓库 LICENSE）。

依据用户提供的《独立可信自动验收系统 Skill 化建设方案》（2026-11-12）实现。没有复制其引用的第三方项目代码，也不依赖另一个审查插件。

## 已提供什么

- `skills/accept-change/`：流程、合同/证据/分流/宿主/适配参考、JSON 提案模板，以及校验、送验、取结果客户端。
- `acceptance-control/gate.py`：固定判定核心，核对必验集合、需求覆盖、证据文件、全部尝试、版本、环境、取消状态、授权到期及累计预算。
- `acceptance-control/service.py` / `docker_worker.py`：持久控制队列与两个容器的隔离试点。候选无宿主挂载，冻结观察器单独运行；正常、故障、取消、过期工作者与预算均留证。见 [部署合同](acceptance-control/deployment.md)。本机试点仍无正式签发权。
- `skills/accept-change/scripts/fv.py` + `fvkit/`：自闭环的形式化验证工具（仅标准库，YAML 输入需要 PyYAML）。安全表达式语言写的规则合同（fv-contract）与状态机模型（fv-model）；显式状态模型检查，覆盖不变量、迁移性质、可达见证、死锁，以及弱/强公平下的活性，给出最短反例或套索反例，支持对称约简；变异资格判定（证明规则抓得到故意注入的设计缺陷）；真实代码轨迹一致性与运行时监控；模型驱动测试向量；源码映射漂移检测；契约弱化检测；风险分级的 CI；TLC / Apalache / Quint / FizzBee 适配。证据按 E0–E4 分级，回执可重放、可重算。见 [formal-evidence.md](skills/accept-change/references/formal-evidence.md)。
- 规则与模型由 AI 按原样收录的开源流程生成（Spec Kit、Quint LLM Kit、TLA+ AgentSkills、Specula、Formal Verification Skills；全集在 AI-DLC 的 `formal-verify/upstream/`），生成过程可检：逐字引文的需求清单、Spec Kit / Quint intake、≥2 份隔离生成候选的语义比较（有限域上给出见证值）与人的裁决、FVS 审阅契约下的审阅、Quint / Specula 模型审阅，收口为 `fv gen-evidence` 回执。`fv upstream verify` 确认收录原文未被改动，产物按 sha256 引用原文。
- `skills/accept-change/upstream/`：原样收录的 Specula spec-fidelity checklist 与 bug-classification（Apache-2.0，带许可证），用于判断反例是模型失真还是实现缺陷；`fv triage-check` 核对分诊文件。
- `acceptance-control/gate.py` 支持 policy schema 2：维护者固定模型/规则摘要、批准的实现契约（`impl_contract_digests`）和最低证据等级，gate 重新校验每份 `fv-receipt`，`rerun` 时用原件重算资格判定与轨迹一致性；`conform` / `implement` 回执必须属于被验收的候选。
- `fv impl-contract` / `fv impl-verify`：模型检查通过后把设计转成实现契约（模型推导的原子、并发、验收义务 + 代码映射、幂等、故障处理），实现后验证代码落实了契约（E3 `implement` 回执）。
- `evaluations/`：协议与门禁回归、真实本地 HTTP 示例、fvkit 与形式化门禁回归，以及待独立执行的 Skill 行为评测用例。

Skill 负责提案、送验和解释；AI-DLC/Forge/项目 Harness 继续负责实现与自测。`acceptance-fleet` 的审查报告可作为输入，不自动成为正式通过。

## 安装与调用

在已添加本仓库 marketplace 的 Claude Code 中安装：

```text
/plugin install trusted-acceptance@claude-code-forge
/trusted-acceptance:accept-change 验收 SHARE-123 修订 3 的固定候选，按已批准合同送验
```

本地源码可在启动 Claude Code 时通过插件目录加载：

```bash
claude --plugin-dir /absolute/path/to/claude-code-forge/plugins/trusted-acceptance
```

只写入仓库不会让已启动会话自动更新技能列表。本地未发布版本需同步启用、安装缓存和 marketplace 缓存条目，再新开 Claude Code 会话；可用 `claude plugin details trusted-acceptance@claude-code-forge` 检查。Codex 可单独安装完整 `skills/accept-change/`，见 [hosts.md](skills/accept-change/references/hosts.md)。

常用请求：

```text
用 accept-change 给这项需求起草验收合同，列出缺少的产品决定。
用 accept-change 把 request.json 送到维护者配置的控制入口，保存运行编号。
用 accept-change 分析这个运行为什么被阻塞，给出反例和下一步。
```

## 客户端

```bash
python3 plugins/trusted-acceptance/skills/accept-change/scripts/acceptance.py \
  validate-request plugins/trusted-acceptance/skills/accept-change/assets/request.example.json
```

`assets/` 都是**合成提案示例**。候选/产物摘要示例不能用于真实送验，endpoint 使用保留的 `.invalid` 域名。不要把样例的 approval_ref 或 recipe ID 当作已经批准/可运行。

真实接入后，由维护者提供候选不可写的配置文件和仅有提交/读取权限的 token 环境变量：

```bash
python3 plugins/trusted-acceptance/skills/accept-change/scripts/acceptance.py submit \
  --request request.json --config /operator-owned/control.json --output receipt-001.json
python3 plugins/trusted-acceptance/skills/accept-change/scripts/acceptance.py get-result \
  --request request.json --config /operator-owned/control.json --run-id RUN_ID --output result-001.json
```

语法有效/远端 accepted 返回 0，远端未接受返回 2，排队/运行返回 3，协议/配置/通信错误返回 4。既有结果文件不覆盖；网络重试沿用同一个请求与幂等键。完整 [接口和服务端义务](skills/accept-change/references/protocol.md)。

## 可重复验证

在仓库根目录运行：

```bash
python3 -m unittest discover -s plugins/trusted-acceptance/evaluations -p 'test_*.py' -v
python3 plugins/trusted-acceptance/evaluations/validate_package.py
```

保留一次可查看证据的 HTTP 演示（输出目录必须尚不存在）：

```bash
python3 plugins/trusted-acceptance/evaluations/demo.py --variant good --out /tmp/acceptance-good
python3 plugins/trusted-acceptance/evaluations/demo.py --variant good-alternative --out /tmp/acceptance-alternative
python3 plugins/trusted-acceptance/evaluations/demo.py --variant ui-only --out /tmp/acceptance-ui-bug
```

前两例预期 `eligible` / 退出 0；最后一例预期 `needs_repair` / 退出 2。演示启动真实本地 HTTP 服务，以独立请求观察“能读 → 所有者撤销 → 匿名再次读”，输出 request、case、decision 与请求/响应证据并清理子进程。候选身份、政策、审批和账号均为合成样本，所有结论标为 `local_advisory`。

## 可信性的实际边界

本版本已经提供规则实现和可运行示例，**没有部署受保护控制服务、真实项目适配器、独立发布身份或生产门禁**。本地同一用户可以修改代码和输入，所以本地核心永不签发 `accepted_for_stage`。正式结果只能来自部署方认证并保护的控制入口。

正式接入需独立保护合同/政策/检查包、候选运行区、观察器/证据库和签发凭据，持久化任务/预算/全部尝试，实现幂等、租约和原子状态复核，再接 required check 与交付授权。具体条件见 [控制区说明](acceptance-control/README.md)。哈希、额外进程、另一个模型或额外 CI job 本身不证明这些边界成立。

本地测试证明协议和列出的程序规则可运行，并在合成 HTTP 任务上识别对应缺陷。尚未做真实项目接入、Skill 有/无对照、独立保留集评测或生产误放行/误拦截测量；行为评测方案见 [evaluations/behavioral.md](evaluations/behavioral.md)。

## 形式化验证

需求定义“应该怎样”，代码描述“实际上怎样”。fvkit 用同一份规则合同检查两边：模型检查回答“这个设计有没有违反规则的交错”，轨迹一致性回答“真实代码跑出来的行为是不是这个设计允许的”。两者都通过，也只能声称到 E3。

```bash
FV=plugins/trusted-acceptance/skills/accept-change/scripts/fv.py
python3 $FV check   --model model.yaml --out check.json            # E2：完整探索，FAIL 时给最短反例
python3 $FV qualify --model model.yaml --out qualify.json          # 设计门槛：完整 + 见证 + 无死动作 + 变异被杀
python3 $FV conform --model model.yaml --map source-map.yaml --traces traces/*.jsonl --out conform.json   # E3
python3 plugins/trusted-acceptance/skills/accept-change/scripts/acceptance.py validate-formal conform.json \
  --model model.yaml --rerun --min-level E3 --expect CONFORMS
```

完整示例（只剩一张票：反例、修复、真实 SQLite 实现、轨迹、CI）在 AI-DLC 的 `formal-verify/assets/example-ticket/`。外部引擎适配只用固定格式的样例输出测过，本仓库没有实际运行 TLC、Apalache、Quint 或 FizzBee。

Product operation and checker calibration chains can now be independently checked with `validate-calibration`; see [the evidence contract](skills/accept-change/references/calibration-evidence.md). This checks local artifact integrity and does not deploy protected acceptance.
