# 来源与证据（2026-09-05 调研；四条独立研究线，~60 个一手来源）

按"本 skill 的哪一条设计来自它"组织，不是通用书单。

## 语料证据：LLM 文本到底哪里不一样

- Kobak et al., "Delving into ChatGPT usage in academic writing" (Science Advances 2025) https://arxiv.org/abs/2406.07016 —— 超额词汇是"风格词"不是内容词（crucial / underscores / delves）。→ 词表是地板不是方法。
- Reinhart et al., PNAS 2025 https://arxiv.org/abs/2410.16107 ；作者笔记 https://www.refsmmat.com/notebooks/llm-style.html —— 名词化 1.5-2×，现在分词从句 2-5×，认知立场标记更少，语域偏信息性/学术性。→ `nominalization_per_k`、分词尾巴规则、立场规则。
- Zamaraeva et al., ACL 2025 https://arxiv.org/abs/2506.01407 ；Gude et al. 2026 https://arxiv.org/abs/2605.06030 —— 句子长 15-30%，短句少 9-30×；新模型多样性更低。→ 句长变异系数与短句存在性。
- iScience 2026 https://www.sciencedirect.com/science/article/pii/S2589004226003512 —— 句长离散度 4.8-5.8 vs 人类 16.4。
- 语篇连贯 2026 https://arxiv.org/html/2603.25537 —— 人类指称集中、链少；LLM 指称分散、链多、更可预测更不连贯。→ `discourse.md` §1。
- Chakrabarty, Laban & Wu, CHI 2025 https://arxiv.org/abs/2409.14509 —— 编辑修 1,057 段 LLM 文本的七类问题；LLM 自己修不好"缺具体性"。→ 具体性闸门 + 外部评审。
- Shaib et al., slop 定义 https://arxiv.org/abs/2509.19163 。
- Artificial Hivemind (NeurIPS 2025 best paper) https://arxiv.org/pdf/2510.22954 —— 模式坍缩来自 RLHF 惩罚多样性。
- van Nuenen 2026 https://arxiv.org/abs/2604.22142 —— 改写去掉第一人称与缩写，"从显式因果推理到压缩抽象"。
- Abdulhai et al. 2026 https://arxiv.org/abs/2603.18161 —— 重度使用者中立文章多 70%。→ 立场规则。
- Belem et al. 2026 https://arxiv.org/abs/2606.07951 —— 改写扭曲确定性最多 75%，向上 1.5-2×。→ factdiff 不只查数字，也查确定性词。
- Cinelli et al., PNAS 2025 https://arxiv.org/abs/2502.04426 —— "epistemia"。
- "Base Models Look Human To AI Detectors" https://arxiv.org/abs/2605.19516 —— 检测器盯的是指令微调语域，不是词汇。→ 最高杠杆的修改是去掉"助手语域"（均匀对冲、未被要求的平衡取舍、枚举、收尾）。
- Russell et al. 2025 https://arxiv.org/abs/2501.15654 —— 重度用户五人多数投票 300 篇错 1 篇，依据是词汇、正式度、原创性、清晰度、句法。
- Rodrigues et al. 2026 https://pmc.ncbi.nlm.nih.gov/articles/PMC12969083/ —— 人类长度分布"更宽更平"。
- Terčon & Dobrovoljc 综述 https://arxiv.org/abs/2510.05136 。

## 语篇理论：为什么读不懂

- Clark & Haviland 1977, given-new contract http://www.web.stanford.edu/~clark/1970s/Clark,%20H.H.%20_%20Haviland,%20S.E.%20_Comprehension%20and%20the%20given-new%20contract_%201977.pdf
- Gopen & Swan 1990, "The Science of Scientific Writing" https://georgegopen.com/scientific-writing-articles/ ；摘要 https://www.crowl.org/Lawrence/writing/GopenSwan90.html
- Daneš 主位推进（综述） https://arxiv.org/pdf/2010.07440
- Williams, *Style: Lessons in Clarity and Grace* https://en.wikipedia.org/wiki/Style:_Lessons_in_Clarity_and_Grace
- Pinker, 知识的诅咒 https://www.psychologicalscience.org/observer/the-curse-of-knowledge-pinker-describes-a-key-cause-of-bad-writing ；Thomas & Turner, *Clear and Simple as the Truth* https://press.princeton.edu/books/paperback/9780691147437/clear-and-simple-as-the-truth
- Minto 金字塔 / SCQA https://strategycase.com/the-pyramid-principle-case-interview/ ；https://modelthinkers.com/mental-model/minto-pyramid-scqa
- Bezos 2004 备忘录（为什么禁 PPT） https://slab.com/blog/jeff-bezos-writing-management-strategy/
- 认知负荷：McNamara & Kintsch 1996 反向连贯效应 https://eric.ed.gov/?id=EJ538963 ；Martins et al. 2006 空信号 https://journals.openedition.org/cpl/1146 ；Sadoski 具体性 https://www.researchgate.net/publication/232552637 ；specificity 2025 https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1718655/full

## 中文

- 北语 CCL 2023（159 特征，6,586 篇） https://aclanthology.org/2023.ccl-1.46.pdf —— 和 11.76 vs 4.13；并列短语 4.60 vs 0.81；句长 SD 6.73 vs 9.25；TTR 0.543 vs 0.725。
- yage.ai 2026-04-18 "AI 味就是翻译腔" https://yage.ai/share/ai-chinese-translationese-20260418.html
- 余光中 1987《中文的常态与变态》 https://www.zgshige.cn/c/2017-12-15/4950348.shtml ；欧化中文 https://zh.wikipedia.org/zh-hans/%E6%AD%90%E5%8C%96%E4%B8%AD%E6%96%87
- 腾讯新闻"文字的预制菜" https://news.qq.com/rain/a/20250321A08CTI00 ；湖南日报 https://m.voc.com.cn/xhn/news/202510/30687762.html ；虎嗅 https://www.huxiu.com/article/4809838.html
- 翔宇 8 特征 https://xiangyugongzuoliu.com/ai-style-writing-8-common-giveaways/ ；CSDN https://blog.csdn.net/Androiddddd/article/details/144033289
- 宝玉《别再用提示词去 AI 味了》 https://baoyu.io/blog/2026-02-14/remove-ai-writing-flavor —— 通用提示词造成"AI 味 2.0"；要一份从自己的修改里长出来的风格文件。→ `/voice-profile`。
- 牛合天 qu-ai-wei（51 模式、9 语域门、"单独出现不算 AI 腔"） https://wiki.liuhetian.work/skills/writing/qu-ai-wei/
- stop-slop-zh https://github.com/VincentOld/stop-slop-zh （口语配额那部分本 skill 不采用）
- 阿里云社区技术方案模板 https://developer.aliyun.com/article/941947 ；https://developer.aliyun.com/article/1588284 —— 安全生产块（监控/对账/灰度/回滚）必含。

## 工程写作范式（`/techdoc` 骨架来源）

- Malte Ubl, Design Docs at Google https://www.industrialempathy.com/posts/design-docs-at-google/
- Oxide RFD 1 https://rfd.shared.oxide.computer/rfd/0001
- Orosz, RFC & design doc examples https://blog.pragmaticengineer.com/rfcs-and-design-docs/
- Amazon 6-pager / PR-FAQ https://workingbackwards.com/resources/working-backwards-pr-faq/ ；Vogels https://www.allthingsdistributed.com/2006/11/working_backwards.html
- Nygard ADR https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- Shape Up pitch https://basecamp.com/shapeup/1.5-chapter-06
- HashiCorp RFC https://www.hashicorp.com/en/how-hashicorp-works/articles/rfc-template
- Rust RFC 模板 https://github.com/rust-lang/rfcs/blob/master/0000-template.md ；PEP 1 https://peps.python.org/pep-0001/
- Paul Graham: Write Like You Talk https://paulgraham.com/talk.html ；Putting Ideas into Words https://paulgraham.com/words.html
- Spolsky, Painless Functional Specifications https://www.joelonsoftware.com/2000/10/03/painless-functional-specifications-part-2-whats-a-spec/
- Will Larson https://staffeng.com/guides/engineering-strategy/ ；https://lethain.com/eng-strategies/
- Grant Slatton, How to design document https://grantslatton.com/how-to-design-document
- Julia Evans, confusing explanations https://jvns.ca/blog/confusing-explanations/
- Eugene Yan, ML design docs https://eugeneyan.com/writing/ml-design-docs/
- Michael Lynch https://refactoringenglish.com/blog/useful-feedback-on-design-docs/
- Google developer style: tone https://developers.google.com/style/tone ；Microsoft top 10 https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice ；GOV.UK https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/ ；Diátaxis https://diataxis.fr/
- Bouchard, AI editing fixes https://www.louisbouchard.ai/ai-editing/

## 提示技术证据（`γ` 设计来源）

- few-shot 风格模仿 https://arxiv.org/abs/2509.24930 （completion 框架 99.9% 风格一致）；https://arxiv.org/html/2509.14543v1 （5-shot 之后无增益；内容相似样本反而伤）
- 对比式 in-context https://arxiv.org/abs/2401.17390
- Verbalized Sampling https://arxiv.org/html/2510.01171v3 ；Prompt-and-Rerank https://arxiv.org/abs/2205.11503
- Self-Refine https://github.com/madaan/self-refine ；自偏放大 https://arxiv.org/abs/2402.11436 → 评审必须隔离
- persona 无效 https://arxiv.org/abs/2311.10054
- 模型数不准 https://arxiv.org/abs/2505.16234 ；https://arxiv.org/abs/2410.07035 → 数字阈值当门不当指令
- Anthropic 提示最佳实践 https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices ；Fable 5.1 "Writing density" https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#writing-density
- claude-code issue #77136（密度时代的 tics） https://github.com/anthropics/claude-code/issues/77136 ；paddo.dev https://paddo.dev/blog/a-dial-worth-turning/
- OpenAI GPT-5 prompting guide https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide

## 现成工具（本 skill 复用了什么、没复用什么）

- Wikipedia:Signs of AI writing https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing —— 词汇/句法/排版层的源头。
- blader/humanizer https://github.com/blader/humanizer —— 复用：两个验收问题（"还有什么听着像 AI""改写有没有增删任何事实/名字/数字/日期/引用"）、"改周围整段而不是补丁式换词"。
- shir-danishyar/humanize https://github.com/shir-danishyar/humanize —— 复用：确定性 linter + 阈值 + 退出码的形态；voice-profile 的形态。
- the-antislop https://github.com/aplaceforallmystuff/the-antislop —— 复用：Horoscope test（"这段话是不是给谁都能用"）。
- Aparnabuilds/humanizer https://github.com/Aparnabuilds/humanizer —— 复用：样文覆盖目录、"按簇处理不按单点"。
- anthropics/skills doc-coauthoring —— 复用：无上下文读者测试（→ cold-reader）。
- SNL-UCSB paper-writing-skill https://github.com/SNL-UCSB/paper-writing-skill —— 复用：先写主题句骨架。
- 检测器：Pangram 4 技术报告 https://arxiv.org/html/2607.27183 ；GPTZero https://gptzero.me/news/how-ai-detectors-work/ —— **结论：过检测器 ≠ 像人，本 skill 不以检测器分数为目标。**
- Vale https://docs.vale.sh/checks/existence ；write-good；EQ-Bench slop score https://eqbench.com/slop-score.html ；auto-antislop https://github.com/sam-paech/auto-antislop （按语料挖过表达 n-gram，是构建个人忌口表的正确方法）。
