# add-new-design-system — 加入单套 DESIGN.md（用户视角）

> 用户已有一份 DESIGN.md（自有的、或从某处下载的），希望加入素材库。
> 这是用户那边的工作流——加完只在用户本地生效，不影响 skill 默认包。

## 触发

用户说："帮我把这份 DESIGN.md 加进来" / "加入 ./xxx 这套设计系统" / 给一个 URL。

## 操作步骤

### Step 1 — 落地原始 DESIGN.md

确认源文件位置（用户提供的本地路径或 URL）：

```bash
mkdir -p source-design-systems/<system_name>/
# 本地源
cp <user_path>/DESIGN.md source-design-systems/<system_name>/DESIGN.md
# 或 URL 源
curl -sLf <url> -o source-design-systems/<system_name>/DESIGN.md
```

`<system_name>` 用 kebab-case，从 DESIGN.md 标题或用户描述推断（"我的内部设计系统" → `internal-design`）。

### Step 2 — 校验 9-section 标准

```bash
python3 tools/scan_dialect.py source-design-systems/<system_name>/DESIGN.md
```

工具输出 dialect（A/B/C/A-variant/...）和 section_count。

- `section_count == 9` 且 dialect ∈ {A, B}：标准 → 继续
- `section_count == 6` (Dialect C)：可接受，A2/A3 时数据较稀
- `dialect == other`：警告用户，让他参考 `references/design-md-spec.md` 调整为标准方言（不要硬塞，会污染规则库）

### Step 3 — 登记到 source-registry

```bash
python3 tools/register_systems.py --source-collection user_added
```

工具自动：
- 计算 fingerprint hash（去重判断的依据）
- 识别方言
- 加入 `grammar/meta/source-registry.json`，`extraction_state: pending`

### Step 4 — A1 Token 提取（程序化）

```bash
python3 tools/extract_tokens.py source-design-systems/<system_name>/DESIGN.md
```

输出 `grammar/tokens/<system_name>.json`。检查 `_confidence` 字段——如果多数 high/medium，质量好；如果多数 low，原 DESIGN.md 用了非标准格式，A2/A3 时需多看原文。

### Step 5 — A2 Rationale 抽取（LLM）

按 `scripts/extract-grammar.md` 的 A2 步骤，写 `grammar/rationale/<system_name>.md`。

### Step 6 — A3 Rule 抽象（LLM）

按 `scripts/extract-grammar.md` 的 A3 步骤，写 `grammar/rules/<system_name>.yaml`。

### Step 7 — A4 关系图增量更新

```bash
python3 tools/rebuild_graph.py
```

全量重算（也可以每批多套加完后只跑一次）。

### Step 8 — 状态确认

```bash
python3 tools/check_state.py
```

确认 `<system_name>` 出现在 `rules` 阶段，且 graph 节点数已包含。

---

## 报告

```
✅ Added <system_name> to local material library
   dialect: <A|B|...>
   tokens fields: NN (high: NN, medium: NN, low: NN)
   rationale decisions: NN
   rules: NN
   graph nodes: NN total (NN added)

   This system is now available for B2 retrieval in your local skill.
   It will not be in the default plugin package — it lives only in your local grammar/.
```

## 注意

- **用户加的素材只在用户本地**：他的 `grammar/` 修改不会进入 plugin 默认包。要进默认包必须由 skill 维护方（仓库 owner）做。
- **fingerprint 去重**：如果用户加入的 DESIGN.md 与某已有 system 内容完全相同，registry 会标 `also_found_in`，不会重复 A1-A4。
- **dialect == other 时的退化**：可以继续，但 B2 检索时该 system 的规则可能被画像不匹配——告诉用户预期。
