---
name: voice-profile
description: "Use when the user wants AI drafts to sound like *them* (or their team) rather than like a generic professional, and has 3–5 pieces of their own writing to learn from — 用我的风格 / 像我写的 / 学我的语气 / 建风格档案 / voice profile. Produces .humanize/voice.md (register, rhythm stats, sentence habits, 忌口表 with replacements, positive examples) that /humanize and /techdoc load automatically. NOT for imitating a named third party (author, colleague, public figure) — that needs consent and is out of scope; NOT a substitute for samples: with zero samples it refuses to invent a voice and says so."
argument-hint: "<3-5 个样文路径或目录> [--out .humanize/voice.md] [--update]"
version: 0.1.0
user-invocable: true
---

# voice-profile

从用户自己的 3–5 篇文字里提炼一份**可执行的**声音档案，写到 `.humanize/voice.md`。
`/humanize` 与 `/techdoc` 发现这个文件就自动加载：以 completion 方式续写"这个作者"的稿，并用档案里的忌口表替换通用禁词表。

## 缺口

宝玉（2026-02）的诊断：所有"去 AI 味"提示词都错在**没说像谁**——于是模型收敛到"像人的均值"，这本身又是一个模式，
叫 AI 味 2.0。实验证据（arXiv 2509.24930 / 2509.14543）：3–5 篇同体裁样文做 completion 式 few-shot，风格匹配比零样本高 20 倍以上；
超过 5 篇无增益；**内容相似的样本反而伤**（收窄了风格范围）。引擎缺的是：从样文里抽出**可核对的**风格事实（Σ），
而不是"温暖而专业"这种描述。

deletion 测试：没有本 skill，用户把样文丢给引擎说"学我的风格"，得到的是形容词（"简洁、直接、有条理"）和几个 bullet，
下一次写作时什么都用不上。

## Σ：一份声音档案长什么样（`assets/voice.template.md`）

| 节 | 内容 | 来源 | 为什么是这个形态 |
|---|---|---|---|
| 读者与场合 | 这个人通常写给谁、什么体裁 | 样文推断 + 用户确认 | 语域门 |
| 节奏数据 | 句长均值 / 变异系数 / 最短句 / 段长 / 路标词比例 / 具体锚点密度 | `humanlint.py --json` 跑每篇样文取中位数 | 数字能当门；形容词不能 |
| 句子习惯 | 开头怎么起、怎么举例、怎么表达不确定、怎么收尾（各引一句原文） | 样文引用 | completion 需要原句不需要描述 |
| 忌口表 | 这个人**从不**用的词/句式（对照通用禁词表，样文里 0 次的） + 替换 | 样文与 `patterns-*.md` 对照 | 个人忌口表比通用表耐久且不同质化 |
| 正例 | 3–5 段原文（不同主题、同体裁、长度相近），标出为什么像他 | 样文 | few-shot 的载体 |
| 反例 | 引擎为同一主题写的默认草稿一段 + "差在哪"一段 | 引擎自生成 | 对比式 in-context（arXiv 2401.17390） |
| 更新记录 | 日期 / 从哪次修改学到了什么 | 每次 `--update` | 档案是长出来的，不是一次写成的 |

## φ：什么算提炼对了

- 节奏数据来自脚本，不是估的；每项附样文中位数。
- 每条句子习惯都有一句**原文引用**；没有引用的习惯不写。
- 忌口表每条给替换（"深耕多年的老兵" → "做了十几年的人"），不只是禁。
- 正例覆盖 ≥3 个不同主题；同一主题的多篇只取一篇。
- 反例真的是引擎的默认写法（不是故意写烂的稻草人）。
- 档案 ≤ 150 行。超过说明写成了风格论文，不是工具。
- 不含人格描述（"他是一个严谨而温暖的人"）——只含可核对的写法。

## Π：原语

- `../humanize/scripts/humanlint.py <sample> --json`：每篇样文的节奏与密度数据。
- `assets/voice.template.md`：档案骨架，按节填。`fixtures/voice.example.md` 是一份填好的、能过门的样例——先看它再填。
- `scripts/verify_voice.py <voice.md>`：机械出口（exit check）。reject：缺必需节、节奏数据仍是占位或无数字、句子习惯无原文引用、
  忌口无替换、正例 < 3、出现人格形容词、> 150 行。交付前必须跑；reject 的档案不写入 `.humanize/voice.md`。
- `--update`：读现有 `voice.md`，把用户对上一次输出的修改（diff）里重复出现的纠正蒸馏成新的忌口/习惯条目，追加到更新记录；不重写整份。

## γ：约束

- **样本数门**：< 3 篇 → 明说"样本不够，档案会过拟合到这几篇的话题"，仍可生成但在档案顶部标 `confidence: low`；0 篇 → 拒绝生成，说明需要什么。
- **体裁一致**：样文体裁与目标体裁不同（博客样文、要写技术方案）→ 只提取节奏数据与忌口表，句子习惯与正例节标 `[体裁不匹配，仅供参考]`。
- **同意门**：样文必须是用户自己的（或用户明确有权代表的团队的）。用户要求学某个第三方作者 → 拒绝并说明原因，不提供替代路径。
- **一次性询问**：需要确认的（读者、场合、哪几篇最代表你）攒成一条消息问完，每问附推荐答案；用户不答 → 用推断值并标注。
- 档案写到 `.humanize/voice.md`（项目级）或用户指定路径；已存在且未加 `--update` → 先问是否覆盖。

### 失败分支

| 触发 | 分支 |
|---|---|
| 样文之间风格差异很大（cv 差 > 0.3 或忌口表冲突） | 按体裁分成两份档案，问用户目标是哪种；不做平均 |
| 样文本身 humanlint 指数 > 40（用户的样文也很 AI） | 如实报告；档案只取节奏与忌口，正例节标"样文本身带 AI 味，正例效力有限" |
| 样文含敏感信息（密钥、个人数据） | 正例节引用时打码；档案不复制整段含敏感信息的文字 |
| `--update` 但没有可比对的上一次输出 | 说明无法蒸馏，退化为重新提炼 |

## 绝不

- **绝不模仿具名第三方**（作者、同事、公众人物）——本 skill 只学用户自己的声音。
- **绝不编造样文里没有的习惯**——每条习惯必须能指向一句原文。
- **绝不写人格形容词**——"温暖 / 严谨 / 犀利"不可核对，也不可执行。
- **绝不把个人忌口表推广为通用规则**——它只对这个作者有效。
- **绝不在样本为 0 时生成档案**。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`。模板与结构过审，`verify_voice.py` 在 `fixtures/voice.example.md`（PASS）与空模板（REJECT）上冒烟；"档案是否真的让 /humanize 输出更像该作者"未测（需要用户样文与盲评）。
