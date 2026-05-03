# import-from-collection — 从外部集合批量导入

> 从 OD（~140 套，持续增长）/ awesome-design-md / 用户指定的 git 仓库批量拉素材。
> 用户那边的工作流——加完只在用户本地生效。

## 支持的源

| 集合 | 命令 | 说明 |
|---|---|---|
| OD (open-design) ~140 套 | `tools/import_collection.sh --source open-design` | 首选起步源 |
| awesome-design-md | （暂未实现 preset，需 custom 模式） | 社区维护，flat 结构 |
| 自定义 git 仓库 | `tools/import_collection.sh --custom-repo <url> --pattern '<glob>'` | 用户自有的设计系统集合 |

## 用法示例

```bash
# 全量导入 OD（首次安装最常见）
./tools/import_collection.sh --source open-design

# 增量（只拉本地没有的）
./tools/import_collection.sh --source open-design --only-new

# 子集（只拉指定的）
./tools/import_collection.sh --source open-design --systems linear-app,vercel,stripe,notion

# 自定义并行度（默认 8）
./tools/import_collection.sh --source open-design --parallel 16
```

## 工具自动做的步骤

1. **gh api 枚举**远程集合下所有可用 system 名单
2. **过滤**（按 `--systems` / `--only-new`）
3. **并行 curl** 把 DESIGN.md 拉到 `source-design-systems/<name>/`
4. **register_systems.py**：登记每套到 source-registry（含 dialect / fingerprint）
5. **extract_tokens.py --batch --only-pending**：跑 A1（程序化，约 137 套耗时 < 5 秒）
6. **check_state.py**：报告状态
7. **提示下一步**：A2/A3 由 LLM 跑（按 `scripts/extract-grammar.md` 指引）

## 网络与许可声明

import 前工具会输出：

```
Importing from: nexu-io/open-design (design-systems)
Found 137 systems in remote.
```

OD 仓库的许可见仓库本身（参考 LICENSE 文件）。本 skill 把 OD 的 DESIGN.md 作为**设计参考**使用，与 fair-use 范畴一致。如果用户在商业产品中使用本 skill 生成的 DESIGN.md，建议查询源仓库的具体许可。

## 去重

- `register_systems.py` 通过 fingerprint hash 判同名同内容 → 标 `unchanged`
- 同名不同内容 → 标 `needs_reextraction = true`，让用户决定是否重跑 A1-A4
- 不同名同内容（罕见）→ 都登记，但 `also_found_in` 字段标多源

## 全量重建关系图

批量导入完成后，**强烈建议**跑一次：

```bash
python3 tools/rebuild_graph.py
```

增量更新在 N > 3 时不再可靠（co_occurs 频率波动大），全量重建确保统计稳定。

## 完成报告

```
✅ Imported from <collection>
   Total: NN systems
   New: NN
   Skipped (duplicates): NN
   Failed: NN

   A1 token extraction: NN/NN OK (programmatic)
   A2/A3 still pending: NN systems (run LLM workflow)

   Total rules library now: NN rules from NN systems
   Graph: NN nodes, NN edges (run rebuild_graph after A2/A3 complete)
```

## 失败处理

- **网络失败**：xargs parallel 模式中，单个 fetch 失败的 system 会被打印 `✗ <name> (fetch failed)`，跳过。可重跑命令补齐（`--only-new` 模式）。
- **A1 失败**：通常是 DESIGN.md 格式严重异常（< 6 sections / 完全不符合任何方言）。`extract_tokens.py` 仍会写一个最小 token JSON 并标 `_confidence: low`。LLM 在 A2 时人工评估是否纳入。
- **gh CLI 缺失**：脚本会报错并退出。安装 `https://cli.github.com`。
