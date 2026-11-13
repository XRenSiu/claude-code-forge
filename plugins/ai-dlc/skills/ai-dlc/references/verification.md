# Project Harness 与可信验收接入

AI-DLC 编排任务。Project Harness 提供项目自检。Fleet 提供语义评审。
`accept-change` 的受保护控制入口提供指定候选、指定阶段的正式验收结论。
三种结果分别记录在 `verification.self_check / review / trusted`，不能互相升级。

运行前确认实际使用的 Python 3.9+ 和 PyYAML（YAML 契约需要；也支持 JSON 表示的 done_when）。已有项目使用其 Python 环境；缺依赖时可在相应环境执行 `python3 -m pip install PyYAML`。Harness 需要 Node 22+，并继续遵守项目自身的 Node 版本约束。

生命周期写入在 macOS/Linux 使用 POSIX 文件锁串行执行，避免轮询、取消或其他状态更新互相覆盖；只读状态查询不获取写锁。

## 选择接入范围

未配置集成的项目继续沿用原有本地流程，可信验收显示 `not_configured`。旧 state v1 在读取时解释为 v2，首次写入才保存升级；旧验收保留为 `legacy_local`，不会变成正式 accepted。

新项目先使用 `bootstrap-project-harness` 调查、生成并验证项目原生检查，得到
`.harness/project.json`、`.harness/runtime/` 和 `scripts/project-verify.mjs`。
日常任务调用这个项目运行时；bootstrap/evolve 用于接入、升级或经过复现确认的防线改进。

集成配置由维护者提供，放在候选仓库外。参考 [本地配置示例](../assets/verification-config.example.json)，把项目 ID、证据目录和环境变量名单改为真实值：

```bash
python3 "$AI_DLC/scripts/aidlc_state.py" init --slug change-123 --title '具体改动' \
  --verification-config /operator/project/aidlc-verification.json
# 已有任务也可以显式接入：
python3 "$AI_DLC/scripts/aidlc_state.py" verification configure --slug change-123 \
  --config /operator/project/aidlc-verification.json
python3 "$AI_DLC/scripts/aidlc_state.py" verification status --slug change-123
```

`AI_DLC` 是当前实际加载的 ai-dlc Skill 目录，不能假定相邻插件缓存的版本路径。
`harness.node` 可以指定项目所需 Node 的绝对路径；若 shell 与 Python 解析到的 PATH 不同，以诊断中报告的实际可执行文件和版本为准。
也可通过 `AIDLC_VERIFICATION_CONFIG` 为新任务提供默认配置。同一任务的配置、客户端及控制配置摘要固定；升级或改变政策应建立新的运行记录，沿用原任务 ID 并提高修订，不能通过改会话重置服务端累计预算。

配置存放在仓库外只是一项本地接线检查，并不证明权限隔离。正式政策、审批、全部尝试与预算必须由控制端独立取得和验证；本地 JSON 不签发授权。

## 项目自检

```bash
python3 "$AI_DLC/scripts/aidlc_state.py" verification run --slug change-123
```

执行已审阅的项目运行时，保留每次 stdout/stderr、原始 receipt 和 AI-DLC 绑定记录。证据目录必须位于项目外。任务状态应被 gitignore 或使用项目外的 `--root`，不得混入产品候选。

适配器只向项目进程传递 PATH、HOME、系统临时目录、语言/时区等基础变量，以及配置中明确声明的 `environment_keys`；检查本身的显式 `env` 仍由 Harness manifest 管理。项目所需的 CI/服务变量要显式声明。不要把验收 API token 加入项目环境名单。收据只记录环境摘要，不记录变量值。对秘密依赖优先绑定不敏感的版本标识。

缓存适用条件包括：任务修订、Git SHA、受扫描源文件、done_when 内容、manifest、运行时文件、Node 路径/版本和传入环境。变化会使旧收据失效。未被建模的机器状态、外部服务或忽略文件仍需按项目约束重新验证，不能宣称这是整个机器的可重复证明。子模块与未完成扫描拒绝自动判定。

所有 required checks 都必须实际 PASS。缺项、重复、零必跑项、全 skip、平台不适用、检查中修改候选、错误退出、缺少报告均不能通过。平台范围应在批准的检查计划里选定；不能临时用 NOT_APPLICABLE 抹掉必跑项。

QA 优先读取本次收据与原始材料，检查证据覆盖与版本。需要复现、诊断或收据失效时再执行检查。
maintenance 只描述失败原因，required check 未通过仍阻塞。环境故障交环境维护者，检查器故障交检查器维护者；不要因此直接返工产品代码或修改本轮冻结预期。

评审开始前读取 `verification status` 的 `current_source`，固定该候选并派发 Fleet。最终在项目外保存 final-state.json，包含明确的 `unevaluated_reviews` 数组与原样的 `input_binding: <开始评审时的 current_source>`，然后用 `acceptance --result` 登记。候选变化后必须重新评审，登记命令会拒绝旧 binding；不能只给旧报告换一个新 SHA。

## 契约提案与批准

继续保留 done_when v2、G2 判据锁、L5 测试锁、红基线与红转绿机制。使用显式映射把每条 AC 关联到本地/可信检查；编译器不从实现代码猜测预期。

```bash
python3 "$AI_DLC/scripts/compile_acceptance.py" \
  --done-when done_when.yaml --mapping /work/check-mapping.json --out /work/proposal.json
```

mapping v1 顶层字段：`schema_version: 1`、`project_id`、`task_id`、正整数 `task_revision`、`contract_id`、`request_ref`、`product_rules_ref`、`criteria`。每项 criterion 必须提供：

- `id / source_ref / given / when / expected / check_id / scope / method`：明确字符串。
- `evidence_types`：非空证据类型列表。
- `ac_ids / local_check_ids / obligations`：显式列表；每项须对应至少一个 AC 或义务。

一条 AC 可由多个 criterion/check 覆盖，源 AC 映射单独保留。义务标识为
`threshold:<指标>`、`structure:<约束>`、`constraint:<其他 constraints 键>`、`rule:<从零起的下标>`。
编译器列出漏项，不删除阈值、结构/路径约束或规则。项目 baseline 来自维护者配置与控制政策，不由任务映射减少。

输出是 `proposal_only`，没有 `approval_ref`。控制区的批准流程应独立核验原始需求、映射语义和标准，并产生带真实 `approval_ref` 的合同。送验时适配器重建提案、核对源摘要与批准合同内容；控制服务仍须认证批准记录。

含 human AC 的提案保持未决。Trusted Acceptance v1 尚没有完整的认证人工签署协议，不能把 G3 的本地姓名、委托文本或 meta-judge 评分代入。正式接入此类任务前先建设人工证据协议；既有本地 G3 流程继续可用。

## 配置可信入口

把集成配置的 `trusted: null` 换成以下字段（摘要与路径必须来自维护者，示意值不能直接送验）：

```text
client                已安装 accept-change/scripts/acceptance.py 的绝对路径
control_config        accept-change HTTPS endpoint/token_env 配置的绝对路径
required_stages       [merge, release]，也支持 acceptance（在推进 PR 时检查）
baseline_check_ids    项目必须保留的回归/架构/权限检查 ID
check_bundle_digest   批准检查包的 sha256 摘要
adapter_digest        批准适配器的 sha256 摘要
environment_digest    控制端定义的目标环境摘要
```

客户端、同目录 protocol.py 和控制配置必须在候选仓库外，并按内容固定。
配置不包含 token 值，客户端从指定环境变量取得 API token。项目自检进程不会默认继承它。
验收服务必须验证不可变候选、实际产物、合同、当前任务状态、预算和全部尝试；候选运行区不能接触签发身份。

## 固定请求、重试与阶段核对

请求沿用 accept-change 的 schema v1，绑定 project/task/revision、候选 SHA、产物/合同/检查包/适配器/环境摘要和阶段。候选必须已经提交且工作区干净。产物摘要从实际文件计算，不能拿源文件摘要或占位值代替。

```bash
python3 "$AI_DLC/scripts/aidlc_state.py" verification prepare --slug change-123 \
  --request /work/request.json --contract /work/approved-contract.json \
  --proposal /work/proposal.json --artifact /work/build.tar.gz
python3 "$AI_DLC/scripts/aidlc_state.py" verification submit --slug change-123 --stage merge
python3 "$AI_DLC/scripts/aidlc_state.py" verification poll --slug change-123 --stage merge
python3 "$AI_DLC/scripts/aidlc_state.py" verification check --slug change-123 --stage merge
```

prepare 在调用网络前保存请求。同一绑定重试必须复用请求与幂等键；POST 超时可以再次 submit，已经取得 run_id 后 poll 同一运行。响应逐次保存，失败历史不覆盖。只有直接调用固定 HTTPS 客户端得到的结果可填充正式结果缓存，不提供“导入任意 JSON 作为 trusted success”的命令。

`run`：0 自检通过、1 检查失败、2 执行/配置错误。
`submit/poll`：0 阶段接受、2 未接受或错误、3 仍在排队/执行。
`check`：0 当前配置要求满足、1 未满足；未接入项目返回的 0 仅表示本地配置未要求该门禁，不能显示为正式验收通过。读取输出中的 configured/status/authority。

启用可信要求后，`advance pr`（对应 acceptance）、`advance merge`、`advance release` 会重新取回对应阶段结果；没有运行、网络异常、身份变化或缺必验项都会阻塞，`--force` 和 S 档豁免不能绕过。merge 的结果不能替代 release。

正式结果仍带 `delivery_authorization: not_granted`。以上是本地编排检查，不执行交付。
真实合并/发布系统必须在执行时独立、原子地核验当前任务、最终候选、阶段授权和正式门禁，使用受保护发布身份与分支规则。仓库内的脚本不能抵挡能修改这些脚本的实现方。

## 流程顺序与失效

默认在 merge/release 要求正式门禁，允许本地验证和 Fleet 完成后建立草稿 PR，再由 PR 事件触发控制服务；避免“必须先验收才能创建触发验收的 PR”。现有十五阶段保持兼容，正式验证状态与阶段正交。

Fleet DONE 表示本地评审收敛。它不授予合入或发布权限。S 档只减少 Fleet/卡成本；独立项目政策照常检查。PR 修复、rebase、合并基线、合同、环境或产物变化后必须更新绑定。G3 人判与交付例外要在相应正式终判前完成，不能构成互相等待。

```bash
python3 "$AI_DLC/scripts/aidlc_state.py" verification task --slug change-123 \
  --task-status cancelled --reason '需求撤销'
python3 "$AI_DLC/scripts/aidlc_state.py" verification task --slug change-123 \
  --task-status active --revision 2 --reason '批准了新的需求修订'
```

取消或被替代的任务只归档；恢复必须提高修订。同一任务的服务预算不因新 session/run 清零。本地取消记录也需要同步到控制端的任务来源；本客户端 v1 没有远端取消 API，不能仅靠本地记录阻止远端交付。

失败响应带 `route.domain / action / consumes_code_budget`：仅 `needs_repair` 交现有实现返工路由；environment、checker、review、unknown、obsolete 分别处理，不调用 card_test_fail 消耗代码预算。AI-DLC 统一调度下一步，Fleet、Harness evolve 不另起无限修复循环。

## 实际能力边界

本仓库提供本地执行适配、契约提案编译、严格客户端调用、版本失效与交付前置检查。
没有随本次改造部署控制服务、发布 GitHub required check 或启用远端分支保护；没有这些设施的项目保持 `not_configured`。
评估使用临时项目与本地 HTTPS 服务验证协议与路由，并不证明生产权限隔离成立。

## 最小接入示例

假设项目已经有 `test/quantity.test.mjs`，验证十进制字符串 1..99 的业务规则。Harness 接入时显式提供 checks 文件：

```json
[{"id":"quantity-rules","executable":"node","argv":["--test","--test-reporter=tap","test/quantity.test.mjs"],"cwd":".","reporter":"tap","depends_on":[],"timeout_ms":30000,"required":true,"effects":"temporary-artifacts"}]
```

使用 bootstrap-project-harness 的 `bootstrap --checks <文件> --authorization-ref <当前授权引用>` 生成计划，按该 Skill 审阅并 apply，再用上述集成配置登记。项目的完整 done_when 仍须满足原有 G2 校验；假设其中已批准的机械 AC 为 `AC-quantity-range`，映射文件可写为：

```json
{
  "schema_version": 1,
  "project_id": "quantity-project",
  "task_id": "quantity-change",
  "task_revision": 1,
  "contract_id": "quantity-contract-v1",
  "request_ref": "issue:quantity-change",
  "product_rules_ref": "rules:quantity-v1",
  "criteria": [{
    "id": "quantity-range-observed",
    "source_ref": "issue:quantity-change#AC-quantity-range",
    "given": "输入为字符串或其他类型",
    "when": "调用数量解析入口",
    "expected": "规范十进制字符串 1..99 返回整数，越界或非规范文本被拒绝，非字符串被拒绝",
    "check_id": "quantity-rules",
    "evidence_types": ["json"],
    "scope": "数量解析公开入口与边界值",
    "method": "受保护观察器调用产物公开入口并保留逐项输入输出",
    "ac_ids": ["AC-quantity-range"],
    "local_check_ids": ["quantity-rules"],
    "obligations": []
  }]
}
```

这里的来源引用需要换成实际批准来源；其他 AC、阈值和约束仍须逐项映射，不能为了示例删除它们。

```bash
python3 "$AI_DLC/scripts/aidlc_state.py" set --slug quantity-change contract.done_when=done_when.yaml
python3 "$AI_DLC/scripts/aidlc_state.py" verification run --slug quantity-change
python3 "$AI_DLC/scripts/aidlc_state.py" verification status --slug quantity-change > /work/review-input.json
# 对 review-input.json 的 current_source 所指候选执行实际评审，保存报告到项目外。
python3 "$AI_DLC/scripts/aidlc_state.py" acceptance --slug quantity-change --result /work/final-state.json
```

final-state.json 中 `input_binding` 是开始评审时保存的完整 `current_source`，`unevaluated_reviews` 必须如实列出未完成的审查。只有实际评审收敛才能写 DONE；没有执行 Fleet 的接入演示不得伪造其结论。正式送验还需上文的真实审批、固定产物与控制入口。
