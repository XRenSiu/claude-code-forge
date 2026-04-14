---
name: distill-collector
description: >
  多模态语料采集脚手架。把微信/QQ/iMessage/播客/视频/PDF 等多种输入统一成
  Markdown 放进 persona skill 的 knowledge/ 目录。本 skill 是**规范 + 编排层**，
  不打包可运行的平台解析器（见下方"scaffolding-only"说明）。
  Use when: (1) 需要为 distill-meta 准备多模态语料,
  (2) 想把跨平台聊天记录归档成统一 Markdown,
  (3) 需要把音频/视频访谈转写成文本,
  (4) 手动整理语料前想先看 CLI 契约和目录规范。
  Triggers: "collect corpus", "采集语料", "ingest chat history",
  "transcribe interview", "import wechat"
when_to_use: |
  - distill-meta Phase 1 需要把多模态输入归档到 knowledge/ 之前
  - 你有跨平台的原始导出（WeChat/QQ/Slack/Notion 等），想统一成 Markdown
  - 你有访谈录音/播客/视频，想拿到可供蒸馏的文字稿
  - 你想知道 persona skill 的 knowledge/ 目录该怎么组织
  - 你要手动准备语料，想先看官方 CLI 契约和目录约定
version: 0.1.0
---

# Distill Collector (Scaffolding-Only)

**把多模态语料统一成 Markdown，放进 `knowledge/` 目录。**

Announce at start: "I'm using the distill-collector skill to document the unified corpus-collection contract and point to the right third-party tools; I won't run platform-specific parsers inside this skill."

> **Scaffolding-only disclaimer (必读 / REQUIRED READING)**
>
> **This skill is a specification + orchestration layer. It documents the unified CLI contract and points users to appropriate third-party tools for each platform. It does NOT ship runnable parsers for WeChat/QQ/iMessage/Whisper/yt-dlp due to platform-specific OS dependencies.**
>
> 本 skill 只提供**规范 + 编排**：定义统一 CLI 契约、输出目录约定、脱敏管线接口，并指向各平台合适的第三方工具。它**不打包**可运行的 WeChat / QQ / iMessage / Whisper / yt-dlp 解析器，因为这些工具依赖宿主 OS / 账号 / 二进制（ffmpeg 等）。
>
> 这是本方案在风险评估 TEC-01 / TEC-02 / EST-02 下的显式取舍：与其发布一个 90% 情况下跑不起来的解析器套件，不如发布一份稳定的契约 + 指向真正能用的外部工具的索引。

## Why This Shape

原始方案设想的是"15+ 平台解析器一键安装"。实际情况：
- 微信/QQ/iMessage 的本地数据库路径、加密方案、账号授权，**每个 OS 每个大版本都在变**。
- Whisper、yt-dlp 依赖用户侧的 Python/ffmpeg 环境，容器化会让体积膨胀 GB 级。
- 打包易过期的代码 = 给用户一堆跑不起来的脚本。

所以本 skill 定位收敛为：
1. **契约层**：`references/cli-spec.md` 定义的统一 CLI 是 distill-meta、用户脚本、第三方工具共同遵守的接口。
2. **目录约定**：`knowledge/{chats,articles,transcripts,media}/` 的组织方式（对齐 master PRD §1.2）。
3. **脱敏策略**：`references/redaction-policy.md` 的 PII 正则与写入时过滤接口。
4. **工具索引**：对每种格式指向已验证的外部工具，而不是自己重造。

## Supported Formats Matrix

| 类别 | 覆盖的平台/格式 | 本 skill 提供的规范深度 | 推荐的外部工具 |
|------|----------------|---------------------|-------------|
| 文本 | WeChat, QQ, Feishu, Slack, Dingtalk, iMessage, Telegram, 邮件 (mbox/eml), Twitter/X 导出 | reference-docs-only | wechatDataBackup, QQExport, slack-export-viewer, imessage-exporter, telegram-export |
| 图像 | 截图 OCR + EXIF 元数据 | reference-docs-only | tesseract-ocr, exiftool |
| 音频 | 访谈/播客/语音备忘录 → 文字稿 | reference-docs-only（给出 Whisper 调用样例，不随 skill 分发） | openai/whisper (本地), whisper.cpp, faster-whisper |
| 视频 | 播客/YouTube/B 站 → 音轨 + 字幕 | reference-docs-only | yt-dlp, ffmpeg, 再接音频管线 |
| 文档 | PDF, docx, epub, Notion 导出 | reference-docs-only + minimal reference impl (纯文本 PDF / docx 的最小样例) | pypdf / pdfplumber, python-docx, pandoc, notion-exporter |

"reference-docs-only" 意味着：你在 `references/` 下能看到字段映射、目录约定、命令样例；但你**不会**在本 skill 里看到可直接 `python parse_wechat.py` 的运行时。

## Unified CLI Contract

借鉴 `agenmod/immortal-skill` 的 `immortal_cli.py` 思路，本 skill 定义**一套 CLI 命令名称与参数语义**，无论底层是第三方工具还是用户自己的脚本，只要遵守这个契约，distill-meta 都能消费其输出。

```bash
# 列出本 skill 契约里定义的平台 / 格式
distill-collector platforms

# 打印某平台的凭据/导出准备步骤（指向第三方工具文档）
distill-collector setup <platform>

# 从某平台采集语料到 knowledge/
# X ∈ {wechat, qq, feishu, slack, imessage, telegram, twitter, notion, ...}
distill-collector collect --platform X --target Y

# 音/视频 → 文字稿（要求本机装好 Whisper / ffmpeg）
distill-collector transcribe <file>

# 已有文本文件的通用导入（最稳定的入口）
distill-collector import <file> --format generic
```

每个命令的详细参数、退出码、输出格式、错误约定，见 `references/cli-spec.md`。

**重要**：以上 CLI 当前是**规范**。本 skill 不提供统一可执行体。你可以：
- 用 distill-meta 的交互提示走人工流程；
- 或自行实现一个脚本/alias，把它映射到你选的第三方工具，只要输出目录结构遵守本契约即可。

## Output Layout

所有采集结果最终落到目标 persona skill 的 `knowledge/` 下，对齐 master PRD §1.2：

```
{persona-slug}/
└── knowledge/
    ├── chats/         # 聊天记录（每平台一个子目录 + 一个索引 md）
    ├── articles/      # 长文/邮件/公开文章（按来源分组）
    ├── transcripts/   # 音频/视频转写稿（保留时间戳段落）
    └── media/         # 原始媒体指针或低码率副本（非语料本体）
```

约定：
- 所有文件 UTF-8 Markdown；音视频只在 `media/` 保留指针或低码率副本，**文字稿放 `transcripts/`**。
- 每个子目录顶层有一个 `INDEX.md`，列出来源、时间范围、条数、脱敏状态。
- 原始二进制不进仓库，除非用户显式要求（`media/` 可以软链接到外部目录）。

## Privacy Redaction

采集到 Markdown 写盘时，统一过一道脱敏管线（见 `references/redaction-policy.md`）：

- 电话 / 邮箱 / 身份证 / 银行卡号 / URL token 的正则替换为占位符。
- 第三方姓名（除目标 persona 本人）默认 hash 化为 `PersonA / PersonB`。
- 位置字段（EXIF GPS 等）默认丢弃，除非用户明确保留。
- 最终产物 Markdown 头部写入 `redaction: applied-vYYYYMMDD` 标记，供 persona-judge 核对。

脱敏规则是**写入时**应用，不是事后扫描——这样即使源文件被删除，仓库里也不会留 PII。具体正则与豁免名单见 references。

## How distill-meta Invokes This

distill-meta 的 Phase 1（语料采集）有两条路径：

1. **Collector-assisted**：distill-meta 识别到用户有多模态源（"我有 1GB 微信记录 + 3 场访谈录音"），**建议**调用本 skill 的 CLI 契约或人工对照 `references/` 走一遍，再回到 distill-meta Phase 1.5 的 Research Review Checkpoint。
2. **Manual bring-your-own**：用户自己已经把 `knowledge/{chats,articles,transcripts,media}/` 准备好了，distill-meta 跳过 collector，直接进入 Phase 1.5。

两条路径互斥但都合法。distill-meta 不强制调用本 skill——它的存在是为了**在用户没有现成 knowledge/ 时给出结构化的准备路径**。

## Known Limitations (surfacing TEC-01 / TEC-02)

直面不做什么：

- **不打包平台数据库解析器**。WeChat、QQ、iMessage 的本地数据库提取强依赖 OS 与账号授权。请使用 `wechatDataBackup`、`QQExport`、`imessage-exporter` 等外部工具拿到原始导出，再走 `distill-collector import --format generic`。
- **不打包 Whisper / yt-dlp**。音视频转写要求用户侧自行安装 Whisper（或 whisper.cpp / faster-whisper）与 ffmpeg；视频下载要求安装 yt-dlp。`references/cli-spec.md` 给出参考调用方式，但 skill 本身不分发这些二进制。
- **OCR 不打包**。`tesseract-ocr` + 对应语言包需用户侧安装；EXIF 提取推荐 `exiftool`。
- **不做跨平台对齐**。同一个联系人在 WeChat / iMessage 的 ID 合并由 distill-meta Phase 2 处理，不在 collector 范围内。
- **不做实时增量同步**。每次采集都是一次性快照；增量对齐是 v2 话题。
- **脱敏是尽力而为**。正则会漏，最终是用户责任；本 skill 明确不做 PII 审计合规承诺。

当以上能力真正落到位时，它们会以独立的 skill / tool 发布，而不是偷偷塞进本 skill 把体积撑大。

## References (progressive disclosure)

当你需要展开细节时再去读：

- `references/cli-spec.md` — 每个 CLI 命令的参数、退出码、输出格式、错误约定。
- `references/text-parsers.md` — 8+ 文本平台的导出方式、第三方工具指针、输出模式。
- `references/av-pipeline.md` — 音视频转写 / yt-dlp / ffmpeg 的管线规范（scaffolding-only）。
- `references/image-doc-parsers.md` — OCR / EXIF / PDF / docx / epub / Notion 的处理规范。
- `references/redaction-policy.md` — PII 正则、占位符、豁免名单、写入时接口。

> `text-parsers.md` 同时包含平台索引（工具指针 + 已知坑），`redaction-policy.md` 包含写入时的 frontmatter 约定。无独立 `platform-index.md` / `output-schema.md`。

## Core Principle

> **"Ship the contract, not the brittle binary glue."**
>
> 发布稳定的契约，不发布脆弱的粘合代码。
> 一个能持续工作 3 年的 CLI 约定，比一个今天能跑、明年因为微信更新就死掉的解析器更有价值。
