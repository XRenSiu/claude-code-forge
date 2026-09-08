<!-- out-of-domain: Kubernetes, Prometheus -->
# 部署说明

服务跑在 Kubernetes 上，指标进 Prometheus。Kubernetes 的滚动更新不影响
BankingTransaction 的语义。Prometheus 抓取周期 15s。Kubernetes 的 HPA 也一样。
