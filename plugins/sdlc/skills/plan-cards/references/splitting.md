# 拆卡启发式

## 按什么拆（优先级从高到低）

1. **按观察边界**：一个 `observe`（route / cli / ui / db_field / event）一张卡——AC 子集天然成组，验收对象清楚。
2. **按 DOS 对象**：一个聚合根及其关系一张卡；跨对象的行为放在拥有主对象的卡。
3. **先契约后 UI**：接口 / 数据形态的卡先做（其他卡 `depends_on` 它），UI 卡后做。
4. **生成物单独**：schema 生成、lockfile、迁移脚本单独一张卡，或全部禁改。

## 共享文件处置

| 文件 | 默认 |
|---|---|
| package.json / lockfile / go.mod / Cargo.toml | 归"依赖卡"一张；其余卡 forbidden |
| 路由表 / DI 容器 / 配置 | 归拥有最多新路由的卡；其余卡 forbidden，需要加路由的卡在 `notes` 写清让它代加 |
| tests/** | 全部卡 forbidden（非实现者写、写完锁） |
| done_when.yaml / dos.yaml / .done_when.lock | 全部卡 forbidden |

## 上下文估算（粗算即可，但要诚实）

`估算 ≈ 卡本身 1k + AC 子集 × 0.3k + allowed_files 内源码 token + 相关测试 token + DOS 切片 1k`。
用 `wc -c` 除以 3.5 近似 token。> 40k 拆；20–40k 可接受；< 5k 可能拆过细（合并）。

## 反模式

- 一张"其余所有"的卡（`src/**`）。
- 卡 A 的 `notes` 说"参考卡 B 的实现"——卡不能互相引用实现，只能 `depends_on` 顺序。
- 把验收写成"跑全部测试"——卡级只跑 `ac_ids`，整体验收在 fleet。
