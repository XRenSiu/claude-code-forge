# 协议 v1 与服务端义务

客户端协议实现位于 `scripts/protocol.py`：所有对象字段必填、拒绝未知字段，整数不接受布尔值，ID 不含路径分隔符，digest 必须为 `sha256:` 加 64 位小写十六进制。JSON 限 2 MiB，数组限 2000 项，文本限 8192 字符，拒绝重复键和非有限数值。只支持 Python 3.9+ 标准库。

这些数据格式不包含“已验证身份”开关。校验通过不产生权限，字段中的审批和身份必须在服务器的受保护记录里查证。

## 请求与合同

`REQUEST`：`schema_version: 1`、`idempotency_key`、`binding`。

`binding` 字段：`project_id`、`task_id`、正整数 `task_revision`、40/64 位 `candidate_sha`、`artifact_digest`、`contract_digest`、`check_bundle_digest`、`adapter_digest`、`environment_digest`，以及 `stage: acceptance | merge | release`。摘要覆盖完整配置与测量条件，不能用手写名字代替。

合同结构见 `assets/contract.example.json`。`CONTRACT` 校验器只做客户端快检。正式来源、批准引用、冻结版本和必验项展开由服务器复核；不能直接信任上传者提交的 required 清单。客户端没有批准/改标准 API。

`digest(value)` 使用 Python `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` 的 UTF-8 字节计算 SHA-256；协议不使用浮点数字。`request_digest` 包含幂等键与全部请求字段。跨语言实现需通过相同 fixture 校验编码一致性；不声称遵循通用 JCS 标准。

## 最小控制 API

这是**需要部署方实现的接口契约**，本包提供客户端和判定核心，不自带公网服务、调度器、GitHub App 或默认 endpoint。

| 操作 | 输入 | 输出 |
|---|---|---|
| `POST {endpoint}/runs` | Bearer token、`Idempotency-Key`、完整 REQUEST JSON | HTTP 200/201/202，RESULT JSON |
| `GET {endpoint}/runs/{run_id}` | Bearer token | HTTP 200，RESULT JSON |

同键同内容返回同一 run_id；同键不同内容 HTTP 409，禁止偷偷新建运行。幂等键与授权调用者/项目关联，不暴露其他项目记录。鉴权失败 401/403，不存在 404；服务端不得通过重定向转发凭据。服务器按 token 权限限制项目、任务和操作。不能信任客户端验证结果。

`RESULT` 所有字段：

| 字段 | 约束 |
|---|---|
| schema_version / run_id / request_digest / binding | 版本 1；身份必须与原请求和查询编号相同 |
| state | queued / running / complete |
| verification_decision | 未完成只能 pending；完成只能 accepted_for_stage / needs_repair / needs_review / blocked / infrastructure_blocked / checker_blocked / obsolete |
| delivery_authorization | 本验收接口固定 not_granted；交付另有授权渠道 |
| checks | CHECK 数组，ID 唯一，正式成功时为完整必验清单 |
| evidence | EVIDENCE 数组，ID 唯一，访问路径由受保护证据库解释 |
| findings | FINDING 数组，未解决阻断发现不可接受 |
| unverified / reasons | 字符串数组；必须披露缺口及分流原因 |

`CHECK`：id、status（pass/fail/skip/not_run/unknown/timeout/error）、requirement_ids、failure_type（none/implementation/environment/checker/unknown）、expected、observed、reproduction_ref（无复现可用空串）、evidence_refs。可复现实现失败必须有复现引用。

`EVIDENCE`：id、check_id、type、path、digest、size_bytes。参考核心仅接受安全相对路径与非空普通文件；单个文件上限 64 MiB、当前 binding 全历史总计 256 MiB。大型 trace 需由部署方受控对象存储分块/流式读取适配，不要直接调大上限绕过资源审查。

`FINDING`：id、blocking（布尔）、resolved（布尔）、summary、evidence_refs。只有受保护复核流程能设置 resolved；候选自填不产生效力。

客户端只做响应一致性校验，完整清单、证据和身份鉴权由服务端判断。TLS 证明连接到配置 endpoint，不能证明错误配置的 endpoint 也值得信任。不要从候选目录自动发现配置。

## 固定判定核心的输入

插件的 `acceptance-control/gate.py` 接受一个 `CASE`：`contract`、`policy`、`current`、`run`。它是本地回归/部署集成用的核心，不是接收候选任意 CASE 的公共 API。

- `policy`：批准的合同摘要/approval_ref、项目、stage、检查包/适配器摘要、baseline_check_ids 与 catalog（id、规则来源、必要证据种类）。必验集合 = 合同必验项 ∪ 政策底线；每项必须存在于批准 catalog。
- `current`：当前 binding、run_id、request_digest、已认证 collector_id、active/cancelled/superseded、授权失效时间、累计 budget、完整 attempt_manifest。时间使用 Unix UTC 秒；v1 的金额使用整数微单位，不能浮点累计。
- `run`：分配身份和全部 attempts。每个 attempt 含 attempt_id、连续 sequence、binding、checks/evidence/findings/unverified。current 的 manifest 为每次尝试的 ID + canonical digest，检测删改、重排和漏交。
- `budget`：max_code_repairs/code_repairs、max_environment_retries/environment_retries、max_cost_microunits/cost_microunits、deadline_at。等于已分配次数上限的最后一轮结果仍可判定；调度下一轮必须先检查是否有余量。结果时消耗超过上限或过截止时间即阻塞。

- `policy` schema 2 = v1 字段 + `formal` 数组（check_id、min_level、model/contract/properties 摘要、pass_verdicts、rerun）。gate 对这些检查重新校验 `fv-receipt` 证据，`rerun` 时用 `fv-model` / `fv-contract` / `fv-trace` 原件重算。v1 政策行为不变。见 [formal-evidence.md](formal-evidence.md)。

即使所有输入都自洽，本地只能得出 `authority: local_advisory` 与 `eligible`，永远不签发 accepted。完整例子由 `evaluations/demo.py` 用真实本地 HTTP 观察生成，包含精确摘要和实际证据字节。

## 正式发布器不可省略的步骤

1. 从受保护存储取得 policy、授权、合同、运行分配和完整账本，不接受候选提供这些“可信输入”。collector 身份来自作业身份/认证通道，不来自 JSON 自称。
2. 冻结控制包与适配版本；在无验收签发、生产或观察器写权限的环境运行候选安装/构建/测试。独立观察器采证，禁止共享可写缓存、宿主 Docker socket 或高权限目录造成跨区写入。
3. 确认实际运行的产物/环境和目标绑定，持久记录全部尝试与预算，使用租约及 fencing token 排除过期 worker。证据存储访问受控且不可由候选覆写。
4. 用受保护版本的 gate 校验，再在发布事务中原子重新核对任务、候选、合同、取消状态和授权。只有该事务可把 eligible 映射为正式 accepted_for_stage。
5. 通过独立最小权限身份发布固定 required check；候选不能获得该身份的凭据。需验证分支规则、来源绑定与绕过权限，而不只是看 job 颜色。缺项/skip/neutral 不得被汇总为 success。
6. 合并/发布前再次核对当前状态与独立交付授权；验收成功不自动授权不可逆外部动作。

这些是部署验收条件，不是本仓库当前已经具备的运行保证。
