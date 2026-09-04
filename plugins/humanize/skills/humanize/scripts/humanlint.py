#!/usr/bin/env python3
"""humanlint.py — AI 味的机械度量（中英双语）。

这不是 AI 检测器，是给编辑用的仪表盘。它只量"能量的东西"：句长节奏、
句首路标词、列表/标题/加粗密度、套话命中、虚化名词化、对冲词、具体性锚点、
套路化开头与总结式收尾……每一项都是文献里与"AI 腔"稳定相关的表层特征。
真正让文字难读的原因（主题串断裂、旧-新信息倒置、没有立场、论证被并列列表替代）
机器量不出来，那一半判给 cold-reader agent 与人。

用法：
  python3 humanlint.py <file.md> [--lang auto|zh|en] [--genre narrative|reference] [--json]
  cat draft.md | python3 humanlint.py - --lang zh

退出码：0 = pass / warn，1 = flag（有 ≥1 项进入 flag 带），2 = 用法错误。
--genre reference（API 文档、配置表、速查表）放宽 bullet / heading 密度阈值。

校准依据：fixtures/ 下四份样本（ai-zh / human-zh / ai-en / human-en）。改阈值或词表后必须重跑
`python3 humanlint.py fixtures/<x>.md`：两份 ai-* 必须 FLAG 且指数 ≥50，两份 human-* 必须 ≤15。
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# 词表：只收"高特异性"条目——人几乎不这么写、模型高频这么写。
# 人也常用的普通词（稳定 / 高效 / various / significant）不收：它们命中率高但没有区分度。
# 官话（赋能 / 抓手 / 闭环）单列 JARGON_ZH，只报 info 不计分——那是企业黑话，不是 AI 味。
# 词表与 references/patterns-zh.md / patterns-en.md 同源，改这里先改那里。
# ---------------------------------------------------------------------------

STOCK_ZH = [
    "值得注意的是", "值得一提的是", "需要注意的是", "不难发现", "不难看出", "综上所述",
    "总而言之", "总的来说", "一言以蔽之", "在这个过程中", "在此基础上", "与此同时", "除此之外",
    "换言之", "换句话说", "深入探讨", "深度剖析", "全面提升", "显著提升", "有效提升", "大幅提升",
    "极大地", "在当今", "日新月异", "不可或缺", "举足轻重", "至关重要", "重中之重",
    "起着关键作用", "发挥着重要作用", "具有重要意义", "意义重大", "影响深远", "保驾护航",
    "多维度", "全方位", "多层次", "有机结合", "相辅相成", "相得益彰", "不仅仅是", "让我们",
    "本文将", "本文旨在", "毫无疑问", "众所周知", "从某种意义上说", "在很大程度上", "持续优化",
    "无缝", "丝滑", "优雅", "健壮", "核心要点", "关键在于", "本质上", "归根结底", "简而言之",
    "通俗地讲", "不容忽视", "不可忽视", "尤为重要", "行之有效", "层出不穷", "应运而生",
    "迎刃而解", "事半功倍", "息息相关", "一目了然", "立竿见影", "有力支撑", "强有力",
    "系统性", "前瞻性", "一站式", "全链路", "精细化", "数字化转型", "重要课题", "重要议题",
    "越来越", "日益", "愈发", "逐渐成为", "已经成为", "一系列", "各种各样", "方方面面",
    "进一步提升", "更好地", "为后续", "打下基础", "奠定基础", "坚实的基础", "提供了保障",
    "共同努力", "携手", "共创", "赋予", "助力", "开启", "新篇章", "新征程", "里程碑",
]

# 句法框架（正则）：模型的"背景段"与"重要性段"生成器
FRAME_ZH = [
    re.compile(r"随着.{0,14}的(不断|持续|快速|迅速|飞速)?(发展|增长|提升|普及|演进|扩张|深入)"),
    re.compile(r"扮演着?.{0,8}角色"),
    re.compile(r"面临着?.{0,14}(挑战|压力|问题|困难)"),
    re.compile(r"为.{0,14}(奠定|打下).{0,4}基础"),
    re.compile(r"提供(了)?.{0,8}(支撑|支持|保障)"),
    re.compile(r"成为.{0,12}(课题|议题|焦点|关键|重点|趋势)"),
    re.compile(r"不断(发展|提升|增长|完善|优化|演进|涌现|推进)"),
    re.compile(r"(有效|显著|极大|大幅|全面|切实)(地)?(提升|提高|降低|减少|增强|改善)"),
    re.compile(r"(具有|有着)(重要|深远|积极|重大)(的)?(意义|影响|作用|价值)"),
]

JARGON_ZH = ["赋能", "抓手", "闭环", "打通", "拉通", "对齐", "沉淀", "落地", "颗粒度", "组合拳", "底层逻辑", "顶层设计", "方法论", "心智", "生态", "壁垒", "护城河", "抓大放小", "价值", "赛道"]

STOCK_EN = [
    "delve", "delves", "delving", "tapestry", "testament to", "landscape", "realm", "paradigm",
    "leverage", "leverages", "leveraging", "robust", "seamless", "seamlessly", "streamline", "streamlines",
    "cutting-edge", "state-of-the-art", "game-changer", "game changer", "unlock", "unlocks", "unlocking",
    "harness", "harnessing", "empower", "empowers", "empowering", "elevate", "elevates", "foster", "fosters",
    "pivotal", "crucial", "invaluable", "multifaceted", "holistic", "comprehensive", "nuanced",
    "underscore", "underscores", "highlight the importance", "it's important to note", "it is important to note",
    "it's worth noting", "it is worth noting", "it's essential to", "it is essential to", "it's crucial to", "it is crucial to",
    "in today's", "in the ever-evolving", "ever-evolving", "rapidly evolving", "fast-paced", "in the realm of", "in the world of",
    "in conclusion", "in summary", "to summarize", "to sum up", "at the end of the day", "all in all",
    "plays a crucial role", "plays a vital role", "plays a key role", "plays a pivotal role", "a wide range of",
    "myriad", "plethora", "enhance", "enhances", "enhancing", "utilize", "utilizes", "utilizing", "facilitate", "facilitates",
    "dive into", "deep dive", "unpack", "let's explore", "let's dive", "in this article", "this article will", "this document aims",
    "we will explore", "moreover", "furthermore", "additionally", "consequently", "key takeaways", "actionable insights",
    "synergy", "whether you're", "when it comes to", "vibrant", "innovative", "transformative", "revolutionize", "revolutionizing",
    "embark", "embarking", "stands as", "serves as a", "meticulous", "meticulously", "intricate", "delicate balance",
    "showcase", "showcases", "boasts", "profound", "groundbreaking", "one of the key", "a key aspect", "various aspects",
    "ensuring that", "aims to", "is designed to", "lays the foundation", "lay a foundation", "foundation for",
    "exceptional", "empowering teams", "strategic investment", "significant opportunities", "numerous advantages",
    "across multiple dimensions", "in terms of", "the ability to", "a variety of", "a range of",
]

# 句首路标词 / 元话语（句首命中即算）
SIGNPOST_ZH = re.compile(
    r"^(首先|其次|再次|再者|然后|接着|最后|此外|另外|除此之外|同时|与此同时|然而|但是|不过|"
    r"因此|所以|总之|综上|总而言之|总的来说|值得注意的是|值得一提的是|需要注意的是|"
    r"换言之|换句话说|具体来说|具体而言|举例来说|一方面|另一方面|事实上|实际上|"
    r"简而言之|更重要的是|更进一步|进一步地|在此基础上|在这个过程中|接下来|最终|随着|在当今|众所周知|毫无疑问)"
)
SIGNPOST_EN = re.compile(
    r"^(first(ly)?|second(ly)?|third(ly)?|finally|lastly|additionally|furthermore|moreover|"
    r"however|therefore|thus|hence|consequently|overall|ultimately|in conclusion|in summary|"
    r"to summarize|notably|importantly|interestingly|crucially|specifically|in addition|on the other hand|"
    r"on one hand|in other words|that said|that being said|as a result|for example|for instance|"
    r"it's important|it is important|it's worth|it is worth|it's essential|it is essential|in today's|"
    r"in the world of|in the realm of|when it comes to|as (our|the|we|technology|businesses))\b",
    re.IGNORECASE,
)

# 套路化开头：第一个正文段落命中即算
OPENING_ZH = re.compile(r"^(随着|在当今|当前|近年来|众所周知|在.{0,10}(时代|背景|环境)下|.{0,20}是.{0,10}(不可或缺|至关重要|重要组成))")
OPENING_EN = re.compile(r"^(in today's|in the (ever|rapidly)|as (our|the) .{0,40}(grow|evolve|continue|scale)|in an era|in the age of|in recent years|with the (rise|advent|growth) of|as technology)", re.IGNORECASE)

# 对冲 / 稀释词
HEDGE_ZH = re.compile(r"可能会|或许|也许|大概|一定程度上|某种程度上|某种意义上|在很大程度上|一般来说|一般而言|往往|相对来说|较为|有一定|基本上|大致|或多或少|不失为|不妨|在一定程度上")
HEDGE_EN = re.compile(r"\b(may|might|could|potentially|possibly|perhaps|arguably|somewhat|relatively|generally|typically|often|usually|tend to|tends to|in some cases|to some extent|it seems|seemingly|fairly)\b", re.IGNORECASE)

# 虚化名词化
NOMINAL_ZH = re.compile(r"(进行|开展|实施|加以|予以|做出|作出|推进|落实|加强|强化|保障|确保)(了|的)?[一-龥]{2,4}(化|性|度|率)?")
NOMINAL_EN = re.compile(r"\b[A-Za-z]{4,}(tion|sion|ment|ance|ence|ity|ness|ization|isation)s?\b")

# 对照框架 "不是 X 而是 Y" / "not just X but Y"
CONTRAST_ZH = re.compile(r"不是[^。！？]{1,30}?而是|不仅[^。！？]{1,30}?(而且|更是|更|还|也)|并非[^。！？]{1,30}?而是|与其说[^。！？]{1,30}?不如说")
CONTRAST_EN = re.compile(r"\bnot (just|only|merely|simply)\b[^.!?]{1,80}?\b(but|rather)\b|\b(it|this|that)'?s not (about|a|just)\b[^.!?]{1,60}?\b(it'?s|but)\b|\bnot because\b[^.!?]{1,60}?\bbut because\b", re.IGNORECASE)

# 三连并列（rule of three）近似
TRIAD_ZH = re.compile(r"[一-龥]{1,6}、[一-龥]{1,6}(和|与|以及|及)[一-龥]{1,6}")
TRIAD_EN = re.compile(r"\b\w+(?:\s\w+)?,\s\w+(?:\s\w+)?,?\s(?:and|or)\s\w+", re.IGNORECASE)

# 具体性锚点：数字、日期、代码标识、路径、专名、带单位的量、百分比、版本号
CONCRETE = re.compile(
    r"`[^`]+`|\b\d{4}-\d{2}-\d{2}\b|\b\d+(\.\d+)?\s?(ms|s|min|h|d|%|GB|MB|KB|TB|QPS|RPS|TPS|rps|qps|x|X|倍|万|亿|个|次|条|台|人|天|周|月|年|行|毫秒|秒|分钟|小时)\b|"
    r"\b\d+(\.\d+)?%|[A-Za-z_][\w\-]*/[\w\-./]+|\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b|\b\d{2,}\b|\b(P50|P95|P99|p50|p95|p99)\b|\bv\d+\.\d+|\b[A-Z]{2,}[A-Za-z0-9]*\b"
)

# 作者立场标记
STANCE_ZH = re.compile(r"我认为|我建议|我们建议|我倾向|我不同意|我反对|我担心|我最担心|我的判断|我们决定|我们选择|我们不做|我不确定|我没有把握|我猜|我赌|我们赌|我没有选|我没选|我不打算|我打算|我想")
STANCE_EN = re.compile(r"\b(I think|I believe|I recommend|we recommend|I'd|I would|I'm not sure|I don't know|we decided|we chose|we won't|we will not|I disagree|I'm worried|my guess|we're betting|I bet|I want|I'm not proposing|I'll take|I'm unsure)\b", re.IGNORECASE)

# 总结式收尾
CLOSER_ZH = re.compile(r"^(总之|综上|综上所述|总而言之|总的来说|归根结底|一言以蔽之|简而言之|让我们)")
CLOSER_EN = re.compile(r"^(in conclusion|in summary|to summarize|to sum up|overall|ultimately|all in all|at the end of the day)\b", re.IGNORECASE)

# "**加粗标签**：空话" 式列表项
BOLD_LABEL_BULLET = re.compile(r"^\s*(?:[-*+•]|\d+[.)、])\s+\*\*[^*]{1,30}\*\*\s*[:：]")

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅❌]")
BOLD = re.compile(r"\*\*[^*]+\*\*")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+")
BULLET = re.compile(r"^\s*(?:[-*+•]|\d+[.)、])\s+")
TABLE = re.compile(r"^\s*\|")
FENCE = re.compile(r"^\s*(```|~~~)")
EMDASH_EN = re.compile(r"—|(?<=\w)--(?=\w)|(?<=\s)--(?=\s)")
EMDASH_ZH = re.compile(r"——")


@dataclass
class Metric:
    key: str
    label: str
    value: float
    unit: str
    band: str            # ok | warn | flag | info
    note: str = ""
    examples: list = field(default_factory=list)


def detect_lang(text: str) -> str:
    cjk = len(re.findall(r"[一-龥]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return "zh" if cjk * 2 >= latin else "en"


def split_lines(text: str):
    """把文档拆成 (kind, line)：heading / bullet / table / prose / blank；跳过代码块与 frontmatter。"""
    out = []
    in_fence = False
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        try:
            end = lines.index("---", 1)
            lines = lines[end + 1:]
        except ValueError:
            pass
    for raw in lines:
        if FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not raw.strip():
            out.append(("blank", raw))
        elif HEADING.match(raw):
            out.append(("heading", raw))
        elif TABLE.match(raw):
            out.append(("table", raw))
        elif BULLET.match(raw):
            out.append(("bullet", raw))
        else:
            out.append(("prose", raw))
    return out


def paragraphs(kinds):
    """连续 prose 行合成段落。bullet 行各自算短段（不参与段落节奏统计）。"""
    paras, buf = [], []
    for kind, line in kinds:
        if kind == "prose":
            buf.append(line.strip())
        else:
            if buf:
                paras.append(" ".join(buf))
                buf = []
    if buf:
        paras.append(" ".join(buf))
    return paras


def sentences(text: str, lang: str):
    text = BOLD.sub(lambda m: m.group(0)[2:-2], text)
    if lang == "zh":
        parts = re.split(r"(?<=[。！？；])\s*", text)
    else:
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(\[`])", text)
    return [p.strip() for p in parts if p and len(p.strip()) > 1]


def sent_len(s: str, lang: str) -> int:
    if lang == "zh":
        return len(re.findall(r"[一-龥A-Za-z0-9]", s))
    return len(re.findall(r"\b\w+\b", s))


def cv(values) -> float:
    if len(values) < 2:
        return 0.0
    m = statistics.mean(values)
    return 0.0 if m == 0 else statistics.pstdev(values) / m


def per_k(count: int, size: int) -> float:
    return 0.0 if size == 0 else count * 1000.0 / size


def band(value, ok, warn, higher_is_worse=True):
    if higher_is_worse:
        return "ok" if value <= ok else ("warn" if value <= warn else "flag")
    return "ok" if value >= ok else ("warn" if value >= warn else "flag")


def count_phrases(low: str, phrases, lang: str):
    hits = {}
    for ph in phrases:
        if lang == "zh":
            n = low.count(ph)
        else:
            n = len(re.findall(r"(?<![A-Za-z])" + re.escape(ph) + r"(?![A-Za-z])", low))
        if n:
            hits[ph] = n
    return hits


def analyze(text: str, lang: str, genre: str):
    kinds = split_lines(text)
    paras = paragraphs(kinds)
    prose_text = "\n".join(l for k, l in kinds if k in ("prose", "bullet"))
    all_sents = []
    for p in paras:
        all_sents.extend(sentences(p, lang))
    bullet_lines = [l for k, l in kinds if k == "bullet"]
    heading_lines = [l for k, l in kinds if k == "heading" and not l.lstrip().startswith("# ")]  # 不计 H1 标题
    prose_lines = [l for k, l in kinds if k == "prose"]
    size = sent_len(prose_text, lang) if prose_text else 0
    # 中文按字、英文按词计密度；同一"每千"阈值下英文文档更短，所以英文阈值统一乘 1.6
    k = 1.0 if lang == "zh" else 1.6
    metrics: list[Metric] = []

    # 1. 句长节奏（burstiness）
    lens = [sent_len(s, lang) for s in all_sents]
    rhythm = cv(lens)
    metrics.append(Metric(
        "sentence_len_cv", "句长变异系数（节奏）", round(rhythm, 2), "cv",
        band(rhythm, 0.45, 0.32, higher_is_worse=False) if len(lens) >= 6 else "info",
        f"{len(lens)} 句，均长 {round(statistics.mean(lens), 1) if lens else 0}；人写的说明文通常 ≥0.45，AI 常在 0.2–0.35",
    ))

    # 1b. 短句存在性：中文每 300 字至少一句 ≤12 字；英文每 150 词至少一句 ≤6 词
    short_cap, per = (12, 300) if lang == "zh" else (6, 150)
    short_n = sum(1 for n in lens if n <= short_cap)
    required = max(1, size // per)
    short_ratio = short_n / required
    metrics.append(Metric(
        "short_sentence_presence", "短句存在性", round(short_ratio, 2), "ratio",
        band(short_ratio, 1.0, 0.5, higher_is_worse=False) if size >= per and len(lens) >= 6 else "info",
        f"{short_n} 句 ≤{short_cap}{'字' if lang == 'zh' else '词'}，需要 ≥{required}；LLM 把短句压掉了 9–30 倍（ACL 2025）",
    ))

    # 1c. 连续平句 run：相邻句长差都在容差内的最长连续段
    tol = 8 if lang == "zh" else 5
    run, best = 1, 1
    for a, b in zip(lens, lens[1:]):
        run = run + 1 if abs(a - b) <= tol else 1
        best = max(best, run)
    metrics.append(Metric(
        "flat_run_max", "最长连续平句数", best, "count",
        ("ok" if best <= 3 else ("warn" if best <= 4 else "flag")) if len(lens) >= 6 else "info",
        f"连续 {best} 句长度差 ≤{tol}；三句以上等长像念经",
    ))

    # 1d. 同开头句比例（排除代词/冠词）
    def opener(s):
        s = s.lstrip("*「\"'(（")
        if lang == "zh":
            w = s[:2]
            return None if not w or w[0] in "我这它该在这那此" else w
        m = re.match(r"[A-Za-z']+", s)
        if not m:
            return None
        w = m.group(0).lower()
        return None if w in ("the", "a", "an", "i", "we", "it", "this", "that", "these", "those", "you") else w
    ops = [o for o in (opener(s) for s in all_sents) if o]
    top_op = max((ops.count(o) for o in set(ops)), default=0)
    same_ratio = 0.0 if not all_sents else top_op / len(all_sents)
    metrics.append(Metric(
        "same_opener_ratio", "同开头句比例", round(same_ratio, 2), "ratio",
        band(same_ratio, 0.15, 0.25) if len(all_sents) >= 8 else "info",
        "同一个词开头的句子占比；模板化段落每句都以同一个主语或路标词起",
    ))

    # 2. 段落长度均匀度（弱信号：≥8 段才计分）
    plens = [sent_len(p, lang) for p in paras]
    pcv = cv(plens)
    metrics.append(Metric(
        "paragraph_len_cv", "段落长度变异系数", round(pcv, 2), "cv",
        band(pcv, 0.35, 0.20, higher_is_worse=False) if len(plens) >= 8 else "info",
        f"{len(plens)} 段；每段都差不多长是模板化的征兆（短文档只报 info）",
    ))

    # 3. 列表密度
    total_body = len(bullet_lines) + len(prose_lines)
    bullet_ratio = 0.0 if total_body == 0 else len(bullet_lines) / total_body
    ok_b, warn_b = (0.40, 0.55) if genre == "narrative" else (0.65, 0.85)
    metrics.append(Metric(
        "bullet_ratio", "列表行占比", round(bullet_ratio, 2), "ratio",
        band(bullet_ratio, ok_b, warn_b) if total_body >= 8 else "info",
        "方案/设计类文档里列表替代论证是最常见的 AI 结构；参考类文档阈值放宽",
    ))

    # 4. "**标签**：空话" 列表项
    blb = [l for l in bullet_lines if BOLD_LABEL_BULLET.match(l)]
    blb_generic = [l for l in blb if not CONCRETE.search(l)]
    metrics.append(Metric(
        "bold_label_bullets", "加粗标签式列表项", len(blb), "count",
        "flag" if len(blb_generic) >= 4 else ("warn" if len(blb_generic) >= 2 else "ok"),
        f"其中 {len(blb_generic)} 条不含任何数字/标识符/专名。'**提升性能**：显著降低延迟' 这种项等于没写",
        [re.sub(r"^\s*(?:[-*+•]|\d+[.)、])\s+", "", l)[:40] for l in blb_generic[:3]],
    ))

    # 5. 标题密度（不含 H1；只拦极端情况）
    hpk = per_k(len(heading_lines), size)
    ok_h, warn_h = (8 * k, 13 * k) if genre == "narrative" else (14 * k, 22 * k)
    metrics.append(Metric(
        "headings_per_k", "标题密度", round(hpk, 1), "/1k",
        band(hpk, ok_h, warn_h) if size >= 400 else "info",
        "每 100 字一个标题基本等于没有段落，只有目录（短文档只报 info）",
    ))

    # 6. 加粗密度
    bpk = per_k(len(BOLD.findall(prose_text)), size)
    metrics.append(Metric(
        "bold_per_k", "加粗密度", round(bpk, 1), "/1k",
        band(bpk, 3 * k, 6 * k) if size >= 300 else "info",
        "满篇加粗 = 没有重点",
    ))

    # 7. 句首路标词比例
    sp = SIGNPOST_ZH if lang == "zh" else SIGNPOST_EN
    sp_hits = [s for s in all_sents if sp.match(s.lstrip("*「\"'(（"))]
    sp_ratio = 0.0 if not all_sents else len(sp_hits) / len(all_sents)
    metrics.append(Metric(
        "signpost_start_ratio", "句首路标词比例", round(sp_ratio, 2), "ratio",
        band(sp_ratio, 0.12, 0.20) if len(all_sents) >= 6 else "info",
        "首先/其次/此外/Furthermore/Moreover 开头——人靠内容衔接，模型靠路标",
        [s[:36] for s in sp_hits[:5]],
    ))

    # 8. 套路化开头
    first = paras[0].strip().lstrip("*") if paras else ""
    op = OPENING_ZH if lang == "zh" else OPENING_EN
    generic_open = bool(op.match(first))
    metrics.append(Metric(
        "generic_opening", "套路化开头", 1 if generic_open else 0, "bool",
        "flag" if generic_open else "ok",
        "'随着…的发展 / In today's…' 开头 = 还没开始说事。人从触发这份文档的那个具体事件/数字开头",
        [first[:50]] if generic_open else [],
    ))

    # 9. 套话密度（词表 + 句法框架）
    low = prose_text.lower()
    hits = count_phrases(low, STOCK_ZH if lang == "zh" else STOCK_EN, lang)
    if lang == "zh":
        for rx in FRAME_ZH:
            found = rx.findall(prose_text)
            n = len(re.findall(rx, prose_text))
            if n:
                hits[f"[框架]{rx.pattern[:18]}…"] = n
    stock_total = sum(hits.values())
    spk = per_k(stock_total, size)
    top = sorted(hits.items(), key=lambda kv: -kv[1])[:8]
    metrics.append(Metric(
        "stock_phrase_per_k", "套话密度", round(spk, 1), "/1k",
        band(spk, 4 * k, 8 * k) if size >= 200 else "info",
        "词表见 references/patterns-*.md；命中 ≠ 必错，但密度高一定错",
        [f"{kk}×{v}" for kk, v in top],
    ))

    # 10. 官话（info）
    if lang == "zh":
        jh = count_phrases(prose_text, JARGON_ZH, "zh")
        metrics.append(Metric(
            "jargon_zh", "官话/黑话命中", sum(jh.values()), "count", "info",
            "赋能/抓手/闭环——这是企业黑话不是 AI 味，不计分；但读者会一起讨厌",
            [f"{kk}×{v}" for kk, v in sorted(jh.items(), key=lambda kv: -kv[1])[:5]],
        ))

    # 11. 对冲词密度
    hg = HEDGE_ZH if lang == "zh" else HEDGE_EN
    hpk_ = per_k(len(hg.findall(prose_text)), size)
    metrics.append(Metric(
        "hedge_per_k", "对冲词密度", round(hpk_, 1), "/1k",
        band(hpk_, 6 * k, 12 * k) if size >= 200 else "info",
        "每句都留退路 = 没有判断。该说'会'的地方别说'可能会'；真不确定就说清不确定什么",
    ))

    # 12. 虚化名词化密度
    nm = NOMINAL_ZH if lang == "zh" else NOMINAL_EN
    npk = per_k(len(nm.findall(prose_text)), size)
    ok_n, warn_n = (5, 10) if lang == "zh" else (40, 65)
    metrics.append(Metric(
        "nominalization_per_k", "虚化名词化密度", round(npk, 1), "/1k",
        band(npk, ok_n, warn_n) if size >= 200 else "info",
        "'进行优化'→'优化'；'the implementation of X'→'implement X'。动作藏进名词，读者得自己还原谁在做什么",
    ))

    # 13. 对照框架
    ct = CONTRAST_ZH if lang == "zh" else CONTRAST_EN
    cpk = per_k(len(ct.findall(prose_text)), size)
    metrics.append(Metric(
        "contrast_frame_per_k", "'不是X而是Y'密度", round(cpk, 1), "/1k",
        band(cpk, 1.5 * k, 3 * k) if size >= 300 else "info",
        "偶尔用是修辞，反复用是模板。通常删掉否定半句直接说 Y",
    ))

    # 14. 三连并列
    tr = TRIAD_ZH if lang == "zh" else TRIAD_EN
    tpk = per_k(len(tr.findall(prose_text)), size)
    metrics.append(Metric(
        "triad_per_k", "三连并列密度", round(tpk, 1), "/1k",
        band(tpk, 3 * k, 6 * k) if size >= 300 else "info",
        "什么都凑三个（灵活、高效、可靠）——人只会列真有的那几个",
    ))

    # 15. 破折号
    dm = EMDASH_ZH if lang == "zh" else EMDASH_EN
    dpk = per_k(len(dm.findall(prose_text)), size)
    metrics.append(Metric(
        "emdash_per_k", "破折号密度", round(dpk, 1), "/1k",
        band(dpk, 2 * k, 4 * k) if size >= 300 else "info",
        "破折号把两个本该分开的句子黏在一起，是模型最爱的黏合剂",
    ))

    # 16. 具体性锚点（越高越好）
    ckp = per_k(len(CONCRETE.findall(prose_text)), size)
    metrics.append(Metric(
        "concrete_anchor_per_k", "具体性锚点密度", round(ckp, 1), "/1k",
        band(ckp, 8 * k, 4 * k, higher_is_worse=False) if size >= 300 else "info",
        "数字/日期/标识符/路径/专名。技术方案没有数字，说明没做过调查",
    ))

    # 17. 立场标记（info）
    stc = STANCE_ZH if lang == "zh" else STANCE_EN
    metrics.append(Metric(
        "stance_markers", "作者立场标记数", len(stc.findall(prose_text)), "count", "info",
        "0 个不算错，但方案/评审类文档里 0 个通常意味着没有人在为这个判断负责",
    ))

    # 18. 总结式收尾
    closer = CLOSER_ZH if lang == "zh" else CLOSER_EN
    last_para = paras[-1].strip().lstrip("*") if paras else ""
    has_closer = bool(closer.match(last_para))
    metrics.append(Metric(
        "summary_closer", "总结式收尾", 1 if has_closer else 0, "bool",
        "flag" if has_closer else "ok",
        "'总之/In conclusion' 段几乎总是复述上文；删掉，或换成下一步动作 / 还没想清楚的点",
    ))

    # 19. emoji
    em = len(EMOJI.findall(text))
    metrics.append(Metric("emoji_count", "emoji 数", em, "count", "flag" if em >= 3 else ("warn" if em else "ok"),
                          "技术文档里 emoji 只出现在 AI 和年会 PPT 里"))

    # 20. Title Case 标题（英文）
    if lang == "en" and heading_lines:
        tc = 0
        for h in heading_lines:
            words = re.sub(r"^\s*#+\s*", "", h).split()
            caps = [w for w in words[1:] if w[:1].isupper() and not w.isupper()]
            if len(words) >= 3 and len(caps) >= len(words) - 2:
                tc += 1
        metrics.append(Metric("title_case_headings", "Title Case 标题数", tc, "count",
                              "warn" if tc >= 3 else "ok", "工程文档通常 sentence case"))

    scored = [m for m in metrics if m.band != "info"]
    raw = sum(3 if m.band == "flag" else (1 if m.band == "warn" else 0) for m in scored)
    maxraw = 3 * len(scored) if scored else 1
    score = round(100 * raw / maxraw)
    flags = [m for m in metrics if m.band == "flag"]
    warns = [m for m in metrics if m.band == "warn"]
    return {
        "lang": lang, "genre": genre, "size": size, "sentences": len(all_sents), "paragraphs": len(paras),
        "ai_flavor_score": score, "verdict": "flag" if flags else ("warn" if warns else "pass"),
        "metrics": [m.__dict__ for m in metrics],
        "fix_first": [m.key for m in (flags + warns)[:3]],
    }


def render(result) -> str:
    out = [
        f"humanlint · lang={result['lang']} genre={result['genre']} · {result['size']} "
        f"{'字' if result['lang'] == 'zh' else 'words'} / {result['sentences']} 句 / {result['paragraphs']} 段",
        f"AI 味指数 {result['ai_flavor_score']}/100 · verdict = {result['verdict'].upper()}",
        "",
        f"{'状态':<6}{'指标':<22}{'值':>8}  说明",
    ]
    mark = {"ok": "  ok", "warn": "WARN", "flag": "FLAG", "info": "info"}
    for m in result["metrics"]:
        val = f"{m['value']}{'' if m['unit'] in ('count', 'bool') else ' ' + m['unit']}"
        out.append(f"{mark[m['band']]:<6}{m['label']:<22}{val:>8}  {m['note']}")
        if m["examples"] and m["band"] in ("warn", "flag", "info"):
            out.append(f"{'':6}  ↳ " + " | ".join(m["examples"]))
    if result["fix_first"]:
        out.append("")
        out.append("先修：" + " → ".join(result["fix_first"]))
    out.append("")
    out.append("注意：这是表层仪表盘。指数低 ≠ 像人写的；主题串断裂、旧-新倒置、没有立场，机器量不出来。")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="文件路径，或 - 读 stdin")
    ap.add_argument("--lang", default="auto", choices=["auto", "zh", "en"])
    ap.add_argument("--genre", default="narrative", choices=["narrative", "reference"],
                    help="narrative=方案/设计/说明/邮件；reference=API/配置/速查表（放宽列表与标题阈值）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    try:
        text = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if not text.strip():
        print("ERROR: empty input", file=sys.stderr)
        return 2
    lang = detect_lang(text) if args.lang == "auto" else args.lang
    result = analyze(text, lang, args.genre)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render(result))
    return 1 if result["verdict"] == "flag" else 0


if __name__ == "__main__":
    sys.exit(main())
