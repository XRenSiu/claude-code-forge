---
name: humanize
description: "Use when a draft (yours or the model's) reads like AI — every word is clear but the reader loses the thread, hedges everywhere, bullets instead of argument, 首先/其次/最后, 值得注意的是, In today's landscape — and you need it rewritten so a competent human professional could have written it, without changing a single fact. 去AI味 / 人味 / 像人写的 / 改得自然点 / 太AI了 / 翻译腔 / 太别扭. Works on 技术方案、设计文档、ADR、复盘、README 叙述段、邮件、评审意见, Chinese or English. NOT for code, code comments, commit messages, API reference tables, or config docs (those should be tables); NOT for beating AI detectors; NOT for adding slang, jokes, typos, or emoji as 'texture'."
argument-hint: "[文件路径 | 直接粘贴的文本 | 'last'（上一条回复）] [--reader <谁读>] [--genre proposal|design|adr|postmortem|memo|readme|email] [--voice <voice.md>] [--lang zh|en]"
version: 0.1.0
user-invocable: true
---

# humanize

输入一份读起来像 AI 的草稿，输出一份**事实一字不改、表达像一个称职的专业人写的**版本，
外加一份工艺报告（改了哪、为什么、事实比对结果、冷读者判决）。

## 缺口（deletion 测试）

撤掉本 skill，让引擎"把这段改得像人写的"，它会：换掉 delve/赋能 这类词、把 bullet 拆成段、
加几个"我觉得"——然后交回一份**词变了、线没变**的稿子。读者照样在第二段跟丢。原因是引擎缺三样东西：

- **φ（判据）**：什么叫"跟得上"。它知道的是词表（Wikipedia 那 60 条），不知道旧-新契约、
  主题串、重点位泄漏、列表替代论证、立场扁平——这些才是"每个字都认识但读不懂"的机制。
- **Π（原语）**：改写会静默改事实（数字、日期、标识符、确定性）。引擎自己核对不可靠，
  Belem et al. 2026 测得改写在最多 75% 的输出里扭曲了确定性。需要 `factdiff.py` 这种不可绕过的比对。
- **γ（控制）**：自己评自己会放大自偏（arXiv 2402.11436）。评审必须在**隔离上下文**里由一个
  没看过写作意图的读者做，且轮数封顶。

词表层（delve / 赋能 / 排比 / 破折号）现成工具已经解决，本 skill 复用，不重造。增量在语篇层。

## Σ：AI 味的三层，与读者卡住的位置

| 层 | 现成工具覆盖 | 本 skill 的处理 | 读者症状 |
|---|---|---|---|
| **词汇** | 是（Wikipedia 表的各种变体） | `humanlint.py` 报密度；`references/patterns-*.md` 给改法与"何时不改" | "这词太 AI" |
| **句法 / 排版** | 部分 | 名词化、分词尾巴、对照框架、三连、均匀句长、bullet/加粗密度 | "读着累" |
| **语篇** | **无** | 旧-新倒置、主题串断裂、重点位泄漏、列表替代论证、章节互相复述、立场扁平、套路化开头、总结式收尾 | **"每个字都认识，就是跟不上"** |

机制全文见 `references/discourse.md`（每条：机制 / 语料证据 / 症状 / 检查 / 改法）。写第一份改写前先读它，
再读对应语言的 `references/patterns-zh.md` 或 `patterns-en.md`。样本对照见 `fixtures/ai-*.md` → `human-*.md`。

**语域先定，再动手。** 默认语域是专业书面（方案 / 设计 / 复盘 / 邮件）：克制、有判断、有数字。
在这个语域里，口语词、情绪、人设、emoji 是**新的 AI 味**（研究里叫"AI 味 2.0"），不是解药。
学术论文语域允许"进行 + 动词"与被动句。参考类文档（API / 配置表）不进本 skill（列表和表格本来就对）。

**改的是表达，不是内容。** 改写只有一种合法的信息增量：把来源里已有的具体信息（数字、名字、
例子）从被形容词遮住的地方**挖出来**。来源没有的，写 `[需核实：…]` / `[unverified: …]` 占位，
不编。一份带占位的诚实稿好过一份填满编造数字的"像人"稿。

## φ：什么算改对了（exit criteria，按层；机器可判的部分由 humanlint / factdiff 在出口 verify，语篇层由 cold-reader）

**文档层**
- 第一段是触发事件或问题本身（有日期 / 数字 / 专名），不是背景。
- 决定 / 推荐 / 核心主张在前 3 段内以一句话出现（方案、设计、ADR、备忘录体裁）。
- 没有"总之 / 综上 / In conclusion" 段；结尾是最后一条新信息（下一步、未决点、什么证据会推翻结论）。
- 删掉任何一段，结论都少一条支撑；删掉后无损的段是复述，不存在。
- 列表只剩真并列、真无序的项；项间有因果 / 前提 / 取舍关系的已展开成段并写出关系词。
- 标题是主张片段（"为什么不用 Kafka"），不是分类名（"技术选型"）。

**段落层**
- 每段第一句是该段的主张；只读每段首句能跟上全文。
- 每句句首的名词在上一句出现过（或是它的指代）；新信息在句尾。
- 每段至少一个具体锚点（数字 / 专名 / 标识符 / 例子），来自来源；没有则 `[需核实]`。
- 句首路标词（首先 / 此外 / Furthermore / Moreover…）占比 ≤ 12%。

**句子层**
- 主语是能做事的实体，动词是它做的事；中文无"进行 / 开展 / 加以 + 名词"壳，英文无 "the implementation of X enables"。
- 无分词尾巴 / "以实现…" 目的尾巴挂在句尾而后文不再提及。
- 对冲只出现在真不确定处，且说明不确定什么、怎么消除；其余判断直说。
- 句长有起伏：变异系数 ≥ 0.45；每 300 字（150 词）至少一句 ≤ 12 字（6 词）。
- 关键术语重复使用，不轮换同义词。

**事实层（硬）**
- `factdiff.py` verdict ≠ fail：数字、日期、标识符、URL、路径、版本号零增删（人工放行的除外）。
- 确定性词总量没有被整体上调或下调（factdiff 的 certainty warn 需逐句解释）。

**语域层**
- 语域移动 ≤ 1 级（书面 → 略口语可以；书面 → 公众号不行）。
- 至少一处"毛边"保留或引入：一个承认的未知、一个标明未测的估计、一个不随大流的观察。**毛边是判断，不是口语。**

机器能判的（词汇密度、节奏、列表 / 标题 / 加粗密度、事实增删）由脚本判；
语篇层的"跟不跟得上"由 `cold-reader` 判；**品味不判**——最终由人。

## Π：原语（存在即可用；不叙述调用顺序）

- `scripts/humanlint.py <file> [--lang zh|en] [--genre narrative|reference] [--json]`：20 项表层指标 + AI 味指数（0-100）+ 先修三项。
  退出码 1 = 有 flag。**改前改后各跑一次**，两份输出都进工艺报告。校准样本在 `fixtures/`。
- `scripts/factdiff.py <source> <rewrite> [--allow-drop …] [--allow-add …]`：事实锚点增删比对 + 确定性漂移。
  退出码 1 = 硬锚点有增删。放行参数只能由人给出，引擎不得自己 `--allow-*`。
- `cold-reader` agent（`agents/cold-reader.md`）：`Agent(subagent_type="general-purpose", prompt=<cold-reader.md 全文 + 改写稿路径 + reader + genre>)`。
  **只给它改写稿、读者、体裁**；不给原稿、不给 brief、不给 humanlint 输出、不给上一轮 cold-read。它输出 `cold-read.yaml`：逐段 expected / got / lost_at / told_not_shown + 文档级四问 + pass | needs_revision。
- 有实验证据的生成技巧（可用，非必须）：
  - 用户给了 3–5 篇自己的样文（`--voice` 或 `.humanize/voice.md`，由 `/voice-profile` 生成）→ 以 completion 方式"续写这个作者的稿"，比"模仿风格"有效 20 倍以上；样本要**不同主题、同体裁**。
  - 对开头段和承重段：生成 5 个候选并各标一个概率，**丢掉概率最高的那个**（典型性偏差），余下用 humanlint 与 φ 挑。
  - 对比对：把引擎自己的默认草稿当负例，和人写样本并排，先写一段"两者差在哪"再改写。

## γ：门（约束，不是流程；exit gate = humanlint + factdiff + cold-reader 三者都有输出才算过）

- **隔离**：cold-reader 在独立 `Agent` 调用里跑；主对话里对自己稿子的"我觉得挺像人的"不算评审。
- **测量在前后**：humanlint 与 factdiff 在改写**前后**各有一份输出；没有"改前"数据的改写不能交付（无法证明改了什么）。
- **事实门不可跳**：factdiff = fail → 定位增删处，回滚那几处改写，重跑；`--allow-*` 只在用户明确指定时使用。
- **轮数封顶**：cold-reader `needs_revision` → 按 `worst_three` 修 → 再跑一次（新的隔离上下文）。最多 2 轮。
  第 2 轮仍 needs_revision → **照常交付**，附 cold-read.yaml 与"仍跟丢的段落"清单，明说"两轮未过"。不第 3 轮，不打扰用户。
- **不问的问题**：读者 / 体裁 / 语言能从文本推出就不问；推不出时用默认（reader = 评审这份文档的资深同事，genre 按标题与结构猜，lang 按字符比例）并在报告里写明"推断值"。
- **一次性询问**：真需要问用户的（例如来源里没有数字、但没有数字这段写不成），攒成一条消息一次问完，附推荐答案；用户不在场 → 全部 `[需核实]` 照常交付。
- **交付硬契约**：无论闸门结果如何，最终必须交付改写稿 + 工艺报告。"这段太 AI 了没法改"是禁止输出。

### 失败分支

| 触发 | 征兆 | 分支 |
|---|---|---|
| 来源本身没有具体信息（0 个锚点） | humanlint `concrete_anchor_per_k` = 0 且改写后仍 0 | 不编。每段留一个 `[需核实：这里需要一个数字/例子，例如 ___]`；报告首条写明"来源缺事实，人味的上限受此限制" |
| factdiff fail | 数字 / 标识符 DROPPED 或 ADDED | 逐条定位；ADDED 的一律回滚（编造）；DROPPED 的回滚（漏抄），除非用户放行 |
| factdiff certainty warn | up 或 down 翻倍 | 逐句对照原稿：原稿说"会"的改成"可能"是扭曲，反之亦然；只保留原稿的确定性等级 |
| cold-reader needs_revision 两轮 | 同一段反复 lost_at | 交付 + 附判决 + 指出该段可能需要**作者补内容**而不是改表达（表达改不掉内容缺环） |
| 输入是参考类文档（API / 配置 / 命令表） | 列表 / 表格占比 > 60%、无论证段 | 改 `--genre reference`：只处理散文段，列表和表格不动；报告说明 |
| 输入混有代码块 | fenced code | 代码块一字不动（脚本已跳过）；只改散文 |
| 输入是英文但用户要中文（或反之） | `--lang` 与文本不符 | 这是翻译不是 humanize；先翻，再对译文跑本 skill；报告分两段 |
| 用户给的 voice 样文与目标体裁不同（博客样文 → 技术方案） | 样文口语度明显高于目标语域 | 只取样文的句长节奏与忌口，不取口语词；报告写明 |
| humanlint 改后仍 flag | 指标未降到 warn | 按 `fix_first` 再修一轮；仍 flag → 交付并列出残余指标（例如参考类文档的 bullet_ratio 本就高） |
| 改写把段落数 / 长度变了 > 30% | 字数差 | 允许（结构重组是合法的），但报告要写明删了什么、为什么无损 |

## 交付物

1. **改写稿**：默认写到 `<原文件同目录>/<原名>.humanized.md`；输入是粘贴文本或 `last` 时直接回复正文。
2. **工艺报告**（附在改写稿后或单独 `<原名>.humanize-report.md`），固定节：

```markdown
## humanize 报告
- 推断值：reader = …；genre = …；lang = …；voice = 无 / <路径>
- humanlint：改前 <指数>/100 (<verdict>) → 改后 <指数>/100 (<verdict>)；仍 flag 的指标：…
- factdiff：<pass|warn|fail>；放行项：无
- cold-reader：round 1 <verdict>（worst_three: …）→ round 2 <verdict>
- 语篇层改动（每条：位置 → 机制 → 改法）
  - 第 1 段：套路化开头 → 用第 3 段里的"P99 1.4s"事件开头
  - 第 4 段：列表替代论证 → 展开，写出"2 是 1 的前提"
- 未能改的：… （来源缺事实 / 两轮未过 / 需要作者补内容）
- [需核实] 清单：…
```

3. **不交付的东西**：不给"AI 味检测分数会降到多少"（本 skill 不以检测器为目标，检测器也在拿 humanizer 输出训练）。

## 绝不（不可豁免）

- **绝不新增来源里没有的事实**——数字、日期、名字、引用、案例。人味不是编出来的细节，是挖出来的细节。缺就标 `[需核实]`。
- **绝不删掉或改动来源里的数字、标识符、URL、路径、代码、引文**——factdiff fail 即回滚，不存在"为了通顺"的例外。
- **绝不改变主张的确定性等级**——原稿"会"不改成"可能"，"可能"不改成"会"。
- **绝不注入口语词、情绪、人设、emoji、错别字、笑话**来"像人"——技术语域里这是新的 AI 味，还损失读者信任。
- **绝不在主对话里自评"像不像人"当作评审**——评审只承认隔离的 cold-reader 与脚本输出。
- **绝不把"过 AI 检测器"当目标或承诺**——本 skill 优化可读性；检测器分数不在报告里。
- **绝不对代码、代码注释、commit message、API 参考表、配置说明跑本 skill**——那些本该是表和列表。
- **绝不第 3 轮**——两轮 cold-reader 未过就交付并说明，把"该补内容"的判断还给作者。
- **绝不擅自 `--allow-drop` / `--allow-add`**——放行是人的动作。

## 接线（可选邻居，缺席不阻塞）

- `/techdoc`（本插件）：从 brief 直接写方案，写完自动过本 skill 的闸门。已有草稿用本 skill，没草稿用它。
- `/voice-profile`（本插件）：从用户 3–5 篇样文生成 `.humanize/voice.md`；存在时本 skill 自动加载（completion 式续写 + 个人忌口表）。没有也照常跑，用默认专业语域。
- `rules/human-voice.md`（本插件）：常驻契约，可整段贴进项目 CLAUDE.md 让每次输出先天少些 AI 味；本 skill 是它的出口检查。

## 本 skill 自身的出口门

`eval/gate.json`：`static_only`——结构过审、脚本在 `fixtures/` 四份样本上冒烟（AI 样本 65/62 FLAG，人写样本 2/0）；
行为层（带 / 不带本 skill 在留出草稿上的 cold-reader 通过率差）未跑。静态读不是裁决。
