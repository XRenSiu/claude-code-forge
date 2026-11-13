# 判定核心与部署边界

`gate.py` 是可运行的确定性规则核心，不是已部署的可信控制服务。

```bash
python3 plugins/trusted-acceptance/acceptance-control/gate.py \
  --case /tmp/acceptance-demo/case.json \
  --evidence-root /tmp/acceptance-demo/evidence
```

合法输入输出 `authority: local_advisory`、`verification_decision: eligible`；其他情况按原因分流。退出 0 仅表示本地规则满足，不是正式签发。任何用户都能改本地 policy、collector_id 和账本，所以此 CLI 永远不能发布正式通过。

生产部署应将固定控制代码放入实现方不可写的受保护仓库/镜像。由可信运行身份分别加载批准的合同、政策、适配和检查版本；独立 runner/collector 负责实测、来源认证、实际产物绑定、历史/预算和不可变证据。核心不执行候选代码或证据内命令。

部署方还必须实现持久化队列、幂等去重、租约与 fencing、任务状态事务、授权有效性、证据 ACL/保留期，以及唯一来源的 required-check 发布器。参见 [协议与发布器条件](../skills/accept-change/references/protocol.md)。不要部署一个接受任意 CASE 后把 `eligible` 原样转成正式通过的服务。

v1 刻意采用保守规则：正式 required 清单必须精确相等；未支持项不豁免；同 binding 的前序未通过或阻断发现进入复核。没有自动解除 flaky 阻塞或人工例外接口。维护者复核后的新合同/检查包/环境形成新 binding，旧尝试继续留在账本中。

本包的合成 HTTP 示例演示 runner/collector/gate 数据流，但进程属于同一用户且没有部署级权限隔离。它只能证明示例业务检查和程序规则有效，不能证明生产可信性。
