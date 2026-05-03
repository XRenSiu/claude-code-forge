# import-from-collection — 从外部集合批量导入

> 从 OD ~140 套 / awesome-design-md / 用户指定的 git 仓库批量拉素材。

## 支持的源

| 集合 | URL | 路径模式 |
|---|---|---|
| OD (open-design) ~140 套（持续增长） | `https://github.com/nexu-io/open-design` | `design-systems/<system>/DESIGN.md` |
| awesome-design-md | `https://github.com/VoltAgent/awesome-design-md` | `<category>/<system>/DESIGN.md` 或 `systems/<system>.md` |
| 自定义 git 仓库 | 用户提供 URL + glob pattern | 用户指定 |

## 输入

来自用户：

- 集合标识（`open-design` / `awesome-design-md` / `custom`）
- 如果是 custom：git URL + DESIGN.md 文件的 glob pattern
- 可选：要导入的 system 名单（默认全部）

---

## Step 1 — Fetch

### 选项 A：git clone（推荐）

```bash
git clone --depth 1 <repo_url> .tmp/import-<collection>/
```

clone 到临时目录，避免污染当前项目。

### 选项 B：raw fetch（避免依赖 git）

如果用户没装 git 或不想 clone，按 GitHub raw URL 拉单个文件：

```bash
curl -sL https://raw.githubusercontent.com/<owner>/<repo>/main/<path>/DESIGN.md
```

逐个拉。

### 网络/许可声明

**导入前告诉用户**：

```
即将从 <source> 导入 N 套 DESIGN.md。这些素材的许可信息：
- <列出已知的 license>
- <如不确定的标注 "license unknown, please verify before commercial use">

导入会：
1. 复制 DESIGN.md 到 source-design-systems/<system>/
2. 生成 tokens / rationale / rules / 关系图
3. 登记到 source-registry.json

继续吗？(y/n)
```

## Step 2 — 枚举可导入的 systems

按集合的目录约定枚举：

- **OD**：列出 `design-systems/` 下所有子目录
- **awesome-design-md**：按 README 索引或目录结构扫描
- **custom**：按用户给的 glob pattern 扫描

输出列表给用户确认：

```
找到 N 套：
  1. linear
  2. stripe
  3. vercel
  ...

要全部导入吗？或者用编号选择？
```

## Step 3 — 去重

对每个待导入 system：

1. 检查 `grammar/meta/source-registry.json` 中是否已存在
2. 如果存在但 fingerprint_hash 不同（同名不同版本）→ 询问用户：保留旧的、覆盖、并存（重命名为 `<system>-<source>`）
3. 如果存在且 fingerprint 相同 → 跳过，但在 source-registry 中**追加**该集合到 `also_found_in[]`，便于多源追溯

## Step 4 — 批量拆解

对每套 system，调用 `scripts/extract-grammar.md` 的 A1-A4。

**并行策略**：

- 单纯 token 提取 (A1) 可以并行（无相互依赖）
- A2/A3 也可并行（每套独立）
- A4（关系图增量）必须串行，避免并发写文件冲突

如果 A1-A3 阶段任一套失败：

- 记录到 `import_errors.log`
- 继续处理其它套
- 最后报告失败列表

## Step 5 — 全量重建关系图

批量导入完成后**必须**跑 `scripts/rebuild-graph.md`。增量更新在 N>3 时不再可靠，全量重建确保 co_occurs 频率正确。

## Step 6 — 更新 source-registry

每套都在 `grammar/meta/source-registry.json` 登记，并在 `meta/imports.log` 记录本次批量导入：

```json
{
  "imported_at": "<ISO 8601>",
  "collection": "open-design",
  "url": "https://github.com/nexu-io/open-design",
  "commit_sha": "<from clone>",
  "systems_imported": [...],
  "systems_skipped": [...],
  "systems_failed": [...]
}
```

## Step 7 — 清理

- 删除临时 clone 目录 `.tmp/import-<collection>/`
- 给用户最终报告：

```
✅ Imported from <collection>
   Total: NN systems
   New: NN
   Skipped (duplicates): NN
   Failed: NN  ← list if any

   Total rules library now: NN rules from NN systems
   Graph rebuilt: NN nodes, NN edges
```

## 许可与归属注意事项

- DESIGN.md 通常作为公开文档可被引用作设计参考。**仍**建议在 `source-registry.json` 完整记录每个来源的许可信息。
- 用户用 skill 生成的 DESIGN.md 是**衍生作品**，但因为是基于"规则反推 + 重新做判断"——并非素材的简单复用——通常可视为新作。如有商业用途疑虑，建议用户咨询法务。
- 如果某素材的来源明确禁止商业用途（少见），在 `source-registry.json` 标 `commercial_use: prohibited`，B6 输出时如果用了这套素材的规则会在 negotiation-summary 里加注。
