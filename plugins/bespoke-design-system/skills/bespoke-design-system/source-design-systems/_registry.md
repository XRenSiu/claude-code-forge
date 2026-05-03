# Source Design Systems — 素材库登记

> 本目录存放原始 DESIGN.md 副本。skill 主流程通过 `grammar/` 中的拆解产物工作；本目录主要用于：
>
> 1. 素材的可追溯性（每条规则可以回到原始 DESIGN.md 验证）
> 2. 拆解失败时重新提取的依据
> 3. 用户审阅"我的规则库覆盖了哪些设计系统"时的目录索引

## 目录约定

```
source-design-systems/
├── _registry.md                  ← 本文件
├── <system_1>/
│   └── DESIGN.md
├── <system_2>/
│   └── DESIGN.md
└── ...
```

每套素材一个子目录，目录名 = system_name（kebab-case）。

每套素材的元数据登记在 `grammar/meta/source-registry.json`，本文件**不**作为权威登记——只是 README 形式的人类可读概览。

## 推荐起步源

首次安装 skill 后，可执行下列维护命令拉取起步素材：

### 选项 1：OD ~140 套（最方便）

```
导入 OD 的 ~140 套设计系统
```

skill 调用 `scripts/import-from-collection.md`，从 `nexu-io/open-design` 的 `design-systems/` 目录拉取所有 DESIGN.md。

### 选项 2：awesome-design-md

```
从 awesome-design-md 导入素材
```

从 `VoltAgent/awesome-design-md` 拉取社区贡献。

### 选项 3：用户自有的 DESIGN.md

```
帮我把 ./my-design.md 加入素材库
```

skill 调用 `scripts/add-new-design-system.md`，把单套素材加入并跑 A1-A4 拆解。

### 选项 4：空启动

也可以从 0 开始，逐步加入自己的 DESIGN.md。

## 素材的去重

如果同一套 DESIGN.md 来自多个集合（OD 和 awesome-design-md 都收录了 Linear），只保留一份，但在 `grammar/meta/source-registry.json` 中通过 `also_found_in` 字段记录所有出处。

## 许可与归属

DESIGN.md 通常作为公开文档可被引用作设计参考。但每套素材的来源、许可、商用许可情况都登记在 `grammar/meta/source-registry.json`：

- `source_type`: `user_original | open_source | public_company_doc | fair_use_reference`
- `license`: 具体许可名（MIT / CC-BY / proprietary / unknown）
- `commercial_use`: `permitted | restricted | prohibited | unknown`

skill 生成的 DESIGN.md 是**衍生作品**——基于规则反推 + 重新做判断，不是素材简单复用。但如果某素材标记了 `commercial_use: prohibited`（罕见），且 B6 阶段产物的 inheritance 中含该素材的规则，会在 negotiation-summary.md 中加注，便于用户决定是否调整。

## 不要做的事

- 不要把素材库本身作为产物使用（这是输入，不是输出）
- 不要直接修改某套素材的 DESIGN.md（如果素材有问题，更新 source-registry 记录并重新导入）
- 不要把 `grammar/` 与 `source-design-systems/` 混淆——前者是规则库（运行时使用），后者是原始素材（拆解依据）
