# humanize

让 AI 写的技术文字读起来像一个称职的专业人写的。

现有的"去 AI 味"工具（blader/humanizer、shir-danishyar/humanize、qu-ai-wei、the-antislop……）几乎全部源自
Wikipedia《Signs of AI writing》那张表，处理的是词和句。但读者卡住的位置在句与句之间：每个字都认识，
连起来也通顺，就是跟不上。本插件把那一层做成了可检查的判据，词汇层直接复用现成结果。

## 三个 skill

| 命令 | 用途 | 出口闸门 |
|---|---|---|
| `/humanize <文件或文本>` | 改写一份草稿，**事实一字不改**，表达像人 | `humanlint.py` 表层 23 项指标 · `factdiff.py` 数字/日期/标识符零增删 · `cold-reader` 隔离冷读 |
| `/techdoc <brief>` | 从一句话 brief 写出资深工程师形状的方案 / 设计文档 / ADR / 复盘 | `verify_techdoc.py` 产物序 + 上面三道 |
| `/voice-profile <3-5 篇样文>` | 从你自己的文字提炼可执行的声音档案，之后两个 skill 自动加载 | `verify_voice.py` |

另附 `rules/human-voice.md`：常驻写作契约，可整段贴进任何项目的 CLAUDE.md。

## 它修的是什么

| 层 | 现成工具 | 本插件 |
|---|---|---|
| 词汇（delve / 赋能 / 值得注意的是） | 已解决 | 复用；`humanlint` 报密度不报命中 |
| 句法 / 排版（名词化、分词尾巴、三连、均匀句长、bullet 密度） | 部分 | 全部量化 |
| **语篇**（旧-新倒置、主题串断裂、列表替代论证、章节互相复述、立场扁平、套路化开头、总结式收尾） | **无** | `references/discourse.md` 十条机制 + 隔离的 `cold-reader` 逐段轨迹 |
| 事实（改写时静默改数字、改确定性） | 少数 | `factdiff.py` 不可绕过 |
| 中文翻译腔（万能动词 + 名词化、被动、长定语、"和"堆叠、抽象名词主语） | 仅 qu-ai-wei | `patterns-zh.md`，CCL-2023 语料 + 余光中 + yage.ai |
| 2026 密度时代新病（矫饰比喻、自造术语、"不是 X 是 Y"、压缩从句） | 无 | 收录 |

## 为什么这样设计（证据）

- 自己评自己会放大自偏（arXiv 2402.11436）→ 评审必须在隔离上下文，由没看过写作意图的 cold-reader 做。
- 改写在最多 75% 的输出里扭曲确定性（Belem 2026）→ `factdiff` 除了数字还看确定性词漂移。
- 3–5 篇同体裁样文做 completion 式续写，风格匹配比零样本高 20 倍以上；超过 5 篇无增益（arXiv 2509.24930 / 2509.14543）→ `/voice-profile` 的形态。
- 通用"去 AI 味"提示词让所有人收敛到同一个"像人的均值"（宝玉 2026）→ 忌口表按人生成，不用通用表替代。
- 检测器在拿 humanizer 的输出训练（Pangram 4：humanized 文本 97.67% 被抓）→ **不以过检测器为目标，报告里没有检测器分数。**
- 定义式提示几轮后失效、词汇约束更耐久（paddo.dev / issue #77136）→ 出口用脚本重测，不依赖引擎"记得"。

全部来源见 `skills/humanize/references/sources.md`。

## 安装

```
/plugin marketplace add XRenSiu/claude-code-forge
/plugin install humanize@XRenSiu/claude-code-forge
```

需要 `python3`（标准库即可，无第三方依赖）。

## 校准样本

`skills/humanize/fixtures/`：同一个 brief 的 AI 默认稿与人写稿各一份（中英各一对）。

| 样本 | humanlint 指数 | verify_techdoc |
|---|---|---|
| ai-zh.md | 60 FLAG | REJECT ×5 |
| human-zh.md | 2 | PASS |
| ai-en.md | 63 FLAG | REJECT ×4 |
| human-en.md | 0 PASS | PASS |

改任何阈值或词表后必须重跑。

## 诚实声明

三个 skill 都是 `static_only`：结构过审（skillwise L0 lint 0 blocking）、脚本在样本上冒烟；
"带本插件写出来的东西是否比不带的更常通过隔离冷读"未在留出样本上测。校准样本与阈值出自同一作者，
指数的绝对值不要当真，方向（AI ≫ 人）在全部 23 项指标上稳定。各 skill 的 `eval/gate.json` 有 fix_list。

**5 项闸门全过 ≠ 这份文档写得好。** 品味那一关只能由人过。
