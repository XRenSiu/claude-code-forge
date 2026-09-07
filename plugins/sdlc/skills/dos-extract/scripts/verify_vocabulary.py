#!/usr/bin/env python3
"""verify_vocabulary.py — 跨制品术语漂移的传感器（B 档结构信号）。

缺口：这个插件**有**本体（`dos.yaml`），却几乎不拿它当闸。今天词表闭包只跑在一个地方——
GitHub issue 的 `依赖 DOS:` 字段（`verify_issue.py --dos`），外加卡的 `dos_slice` 结构化字段
（`lint_cards.py --dos` 第 3 项）。两者都只看**声明**：作者主动列出来的名词。
下游每一份制品的**散文**——`done_when.yaml` 的 statement / notes、`cards/CARD-*.yaml` 的
title / notes、`spec.md`、PR body、issue body——都可以引入一个 `dos.yaml` 解析不了的领域名词，
而没有任何东西会注意到。这正是 AI-DLC 2.0 在运行时付钱买的那种语义漂移：它没有本体，
只能靠事后学习循环一次记一个词（agent 把 "transaction" 读成数据库事务，人纠正成
"banking transaction"，这一个词被记住）。有本体的插件不该退化到一次一个词。

本脚本把「术语一致性」从不可检变成可检：读 `dos.yaml` 与一组制品，报**制品里出现、本体解析不了
的领域名词**，每条带出处（file:line）与本体里最近的可解析邻居。

用法：
  verify_vocabulary.py --dos dos.yaml <artifact|glob> [<artifact|glob> ...]
      [--artifact-kind auto|contract|card|markdown|yaml]
      [--waive Term,Term] [--waivers decisions.md] [--stopwords FILE]
      [--min-occurrences 3] [--count-unknown] [--threshold 0]
      [--require-ontology] [--no-unused] [--max-notes 10]
      [--out vocabulary-facts.yaml] [--json]

`--out` 缺省**不写文件**。`verify_structure.py` 的 facts 是 A 档闸必须留的产物，所以它有缺省路径；
本脚本是 B 档传感器，会被人从任意目录随手跑一次（"这份契约的词干净吗"），给它一个缺省输出路径
只会在仓库根上留下一个没人要、又很容易被顺手 commit 的 `vocabulary-facts.yaml`。
要 facts 就显式给 `--out`；只要机器读的结果用 `--json`（走 stdout，不落地）。

退出码（与 `verify_structure.py` 同一族）：
  0 = 计入的发现 ≤ --threshold（可能仍有未计入的 unknown / typo 报出来）
  1 = 计入的发现超阈值（B 档：告警，不是一票否决——接线见 SKILL.md）
  2 = 用法 / IO 错误
  3 = **未评估**：没有 `dos.yaml`，或它没有可用的词表（`objects` 为空）。
      这不是 pass。一个没有本体的仓库不是「通过了术语检查」，是「根本没检」。
      `--require-ontology` 把 3 变成 1（当闸用时该这么开）。

设计要点（为什么这样而不是那样）：

  - **模糊只活在报告层，绝不进解析层。** `dos_closure.py` 写死了「synonyms 是声明的，从不推断」，
    这条不能被本脚本稀释：`resolve_object` 依旧是精确匹配，near-miss 邻居只是**失败旁边印的一句提示**，
    永远不构成通过。想让 `work_unit` 闭包，去 `dos.yaml` 里写 `synonyms:`，不是让检查器猜。
  - **不另写一套名词抽取器。** 解析走 `dos_closure.load_closure`（与 `verify_issue.py` /
    `lint_cards.py` 同一个），「本体里这个词有没有被用过」走 `count_terms.variant_pattern`
    （与文档通道计数同一套字面 / 正则 / 词边界规则）。两个消费者对「同一个词」的判断必须一致，
    否则这个传感器和它要保护的闸会各说各话。
  - **假阳性是这个脚本的全部难点。** 一个见到英文名词就报的传感器没人会跑第二次。
    精度靠三重保守，每一层都可配，且每一条收紧都写明是**推理还是实跑换来的**：

      ① **形状过滤**（谁能进候选）。四个通道：PascalCase 复合词（`WorkUnit`）、单个首字母大写词
         （`Ring`）、snake_case（`banking_transaction`），以及**本体 token 通道**——普通小写词，
         但它本身是本体某个复合标识符的一个 token（`transaction` 之于 `BankingTransaction`）。
         第四个通道是必需的：AI-DLC 那个真实例子里出问题的词恰恰是最普通的小写名词，没有形状。
         全大写缩写（`PSL` / `REQ` / `AC`）一律不进候选。

      ② **语境过滤**（哪些位置根本不看）。markdown 的围栏代码块 / 行内代码 / URL / 链接目标先抹掉
         （抹成等长空格，行号列号不变）；路径与带扩展名的文件名抹掉；YAML 只读 **PROSE_KEYS 覆盖的
         散文子树**，不读键名，且整个跳过 `dos_slice` / `allowed_files` 等结构化子树——`dos_slice`
         是 `lint_cards.py --dos` 的活，两个闸报同一件事等于两个都变成噪音。
         另外：**全部出现位置都在句首的大写词直接丢**（英文句首大写是语法，不是术语）。

      ③ **佐证要求**（进了候选还要过这一关）。
           `near_miss`（计入，1 次出现就报）——候选与本体的关系必须是下面之一：
              · 归一化后相同：`work_unit` ≡ `WorkUnit`（写下来的标识符差一个写法，本体没写 synonyms）；
              · 候选是某个**复合标识符**的真子集：`transaction` ⊊ `BankingTransaction`。
           `unknown`（缺省**不**计入，只印给人看；`--count-unknown` 才计入）——找不到邻居，
              但出现 ≥ `--min-occurrences`（缺省 3）次，且不是语料自己用作结构键的词，
              且不是 snake_case。
           `typo`（不计入）——字面相似度 ≥0.87 却没有共同 token（`Contarct` vs `Contract`）。
              错别字是噪音；真正值钱的是「两个词都是真词、指的是同一个东西」那一类。
           `unresolved_rule`（计入）——见下。
         其余一律丢弃，丢弃原因逐类计数进 facts 的 `dropped_candidates`。

    **实跑砍掉的三条**（2026-09-07 首次对 `dogfood/ring-audit` 跑，18 条 near_miss 里 15 条是噪音）：
      · **反方向（候选 ⊋ 本体词）整条不要**。`run_evidence` ⊋ `Run`、`gate_json` ⊋ `Gate`、
        `loop_back` ⊋ `Loop`——单 token 的本体对象几乎被任何含该词的字段名命中。含着本体词的复合
        字段名是普通命名，不是术语漂移。这一向的召回是精度的价钱。
      · **只有复合标识符参与 token 判定**（见 `is_compound_identifier`）。短语型 synonyms
        （`skill node` / `acceptance contract`）与文件名型 synonyms（`done_when.yaml`）被切成 token 后，
        散文里每个 `skill` / `agent` / `yaml` 都成了「真子集」。
      · **unknown 通道再压两条**：语料自己拿它当结构键用的词（`ac_ids` / `allowed_files`）是 schema 词汇；
        散文里的 snake_case（`merge_candidate` / `signer_kind` / `authorization_ref`）绝大多数是被引用的
        字段名 / 枚举值 / 错误码。实测这两条把 37 条 unknown 压到 7 条，留下的是 Ring / Part / Gap /
        Artifact / Assessment——正是那次 dogfood 已登记的 as-is / to-be 本体分裂（I-15 / I-49）。
      改后对真实 dogfood 本体的**计入发现是 0**，note 5 条全真。

    精度/召回的取舍写明白：**这是一个偏精度的传感器。** 它会漏掉只出现一两次、又与本体毫无字面
    关系的新造词，也会漏掉「候选比本体词更具体」那一整向。换来的是「跑出来的每一条都值得看一眼」——
    B 档信号的价值全在这里，一个人不看的告警等于没有告警。要提高召回：调低 `--min-occurrences`
    并加 `--count-unknown`，但那时噪音是你自己选的。
  - **规则引用一起检，形状从本体自己推。** 不硬编码 `R\\d{3}`：从 `rules[].id` 里观察出
    （前缀, 位宽），再拿这个形状去散文里扫。散文里写了 `R018` 而本体只到 `R017` = 引用了一条
    不存在的宪法，这一类几乎没有假阳性，直接计入。
  - **反向信号一起报，但不计入。** 本体里声明了、所有制品一次都没用过的词（`unused_ontology`）。
    证据比正向弱得多——一个词可能只是这一轮没用到——所以只印不判。
  - **豁免是显式的，且和 `verify_dos.py` 同一套约定。** `--waive A,B` 临时；
    `--waivers decisions.md` 读 `## Vocabulary waivers` 段的 bullet（第一个反引号 token 是被豁免的词），
    与 `verify_dos.py --decisions` 的 `## Naming waivers` 是同一个解析器（本脚本 import 它）；
    制品自己也能声明：markdown 写 `<!-- out-of-domain: A, B -->`，YAML 写顶层或卡内
    `out_of_domain: [A, B]`。豁免的词不会消失——它们进 facts 的 `waived`，人能看见谁豁免了什么。

制品形态（`--artifact-kind`，缺省 auto 按文件名猜）：
  contract   `done_when.yaml` 类：只读 acceptance 条目的散文槽（statement / notes / given / expect / …）
  card       `cards/CARD-*.yaml`：只读 title / notes / description，**跳过 `dos_slice`**
  yaml       其它 YAML：同 PROSE_KEYS 的并集
  markdown   `spec.md` / issue body / PR body：整篇都是散文（抹掉代码与路径之后）
"""
from __future__ import annotations

import argparse
import difflib
import glob as globmod
import json
import os
import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("verify_vocabulary.py needs PyYAML: pip install pyyaml\n")
    sys.exit(2)

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import dos_closure                      # noqa: E402  the ONE definition of "resolves"
from count_terms import variant_pattern  # noqa: E402  the ONE definition of "this term occurs"
from verify_dos import parse_waivers     # noqa: E402  the ONE waiver-bullet convention

# ---------------------------------------------------------------- 候选形状
# PascalCase 复合词：每段必须「大写 + 至少一个小写/数字」，所以 PSLId / REQId 这类全大写前缀不进。
CAMEL_RE = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b")
# 单个首字母大写词，长度 ≥3（Ring / Gap / Run）。假阳性最大的一类，靠 stopwords + 句首规则 + 佐证压。
CAP_RE = re.compile(r"\b[A-Z][a-z]{2,}\b")
# snake_case：至少一个下划线，全小写。
SNAKE_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
# 第四通道：普通小写词。**只有当它本身就是本体某个多词条目的一个 token 时**才进候选
# （`transaction` 之于 `BankingTransaction`）。这一类没有形状可依——AI-DLC 那个例子里
# 出问题的词恰恰是最普通的名词——所以佐证不靠形状，靠「本体里确实有一个词包含它」。
LOWER_RE = re.compile(r"\b[a-z][a-z0-9]{2,}\b")

# 语境抹除（抹成等长空格，行号与列号都不变）
FENCE_RE = re.compile(r"(?ms)^[ \t]*(`{3,}|~{3,})[^\n]*\n.*?^[ \t]*\1[^\n]*$")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
HTML_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
URL_RE = re.compile(r"https?://\S+|\bwww\.\S+")
LINK_TARGET_RE = re.compile(r"\]\([^)\s]+")
# 路径与带扩展名的文件名：`plugins/sdlc/skills`、`done_when.yaml`、`check_audit.py`
PATHY_RE = re.compile(r"[A-Za-z0-9_.\-]*[/\\][A-Za-z0-9_./\\\-]+|\b[A-Za-z0-9_\-]+\.[A-Za-z][A-Za-z0-9]{0,5}\b")

SENTENCE_START_RE = re.compile(r"(?:^|[.!?;:—|\-*>。！？；：、，])\s*$")

# 出现在散文里、形状像领域名词但不是的英文词。宁可漏报也不要让人看到一屏 "The / This / Every"。
STOPWORDS = {
    # 句首 / 连接
    "the", "this", "that", "these", "those", "there", "then", "than", "and", "but", "for", "not",
    "with", "without", "when", "while", "where", "which", "what", "who", "why", "how", "all",
    "any", "each", "every", "some", "none", "only", "also", "such", "same", "other", "another",
    "both", "either", "neither", "here", "from", "into", "onto", "over", "under", "after",
    "before", "since", "until", "unless", "because", "however", "therefore", "otherwise",
    "instead", "already", "still", "yet", "just", "very", "more", "most", "less", "least",
    "many", "much", "few", "several", "first", "second", "third", "last", "next", "previous",
    # 常见动词 / 情态
    "use", "used", "uses", "using", "run", "runs", "make", "makes", "made", "given", "gives",
    "see", "sees", "add", "adds", "set", "sets", "get", "gets", "put", "let", "lets", "can",
    "may", "must", "should", "shall", "will", "would", "could", "does", "did", "done", "has",
    "have", "had", "was", "were", "are", "its", "his", "her", "our", "your", "their", "them",
    "they", "you", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    # 文档骨架词
    "note", "notes", "example", "examples", "usage", "summary", "overview", "section",
    "appendix", "todo", "tbd", "warning", "caution", "important", "default", "optional",
    "required", "yes", "no", "true", "false", "null", "none",
    # 工程通用词（真领域词会通过 near-miss 通道进来，不靠这一层）
    "test", "tests", "code", "file", "files", "line", "lines", "path", "paths", "value",
    "values", "key", "keys", "name", "names", "type", "types", "list", "map", "item", "items",
    "output", "input", "error", "errors", "exit", "check", "checks", "step", "steps", "case",
    "cases", "mode", "flag", "flags", "field", "fields", "data", "info", "text", "string",
    "number", "table", "row", "rows", "column", "columns", "script", "scripts", "tool", "tools",
    # 扩展名：路径抹除会漏掉裸写的扩展名（"这个 yaml 里"）
    "yaml", "yml", "json", "toml", "markdown", "html", "css", "sql", "sha", "url", "uri",
    # **关于建模的词，不是被建模的词**。dogfood 实跑里 "Domain Model" 一句贡献了 2 条假阳性。
    # 一个仓库真把 `Model` 当领域对象时它会写在本体里、因而本来就解析得掉；这一组只影响
    # 「本体可能漏了这个词」那一档的猜测，不影响 near_miss。（`--stopwords` 只增不减。）
    "domain", "model", "models", "ontology", "glossary", "terminology", "vocabulary",
    "taxonomy", "diagram", "entity", "attribute", "relation", "relationship",
}
# token 太泛，不足以支撑一次 near-miss 判定（否则 CheckAudit 与 CheckAnchors 会互相「近似」）
GENERIC_TOKENS = {
    "id", "ids", "data", "info", "item", "items", "list", "map", "type", "kind", "name", "value",
    "obj", "object", "objects", "entry", "entries", "record", "records", "check", "checks",
    "test", "tests", "file", "files", "path", "config", "spec", "meta", "base", "core", "main",
    "new", "old", "tmp", "temp", "util", "utils", "common", "shared", "default", "result",
}
# YAML 里被当作散文读的字段（三种 kind 的并集在 PROSE_KEYS["yaml"]）
PROSE_KEYS = {
    "contract": {"title", "statement", "description", "notes", "note", "rationale", "why",
                 "judge", "evidence", "summary", "given", "expect", "then", "when", "context",
                 "acceptance_notes", "threshold", "disposition"},
    "card": {"title", "notes", "note", "description", "summary", "context", "acceptance_notes",
             "rationale", "why"},
}
PROSE_KEYS["yaml"] = PROSE_KEYS["contract"] | PROSE_KEYS["card"]
# 跳过的子树：`dos_slice` 已经由 lint_cards.py --dos 逐项闭包，重复报同一件事只会让两个闸都变噪音。
SKIP_SUBTREES = {"dos_slice", "allowed_files", "forbidden_files", "mock_allowlist", "reads_from"}


# ---------------------------------------------------------------- 工具
def blank(text: str, pattern: re.Pattern) -> str:
    """把匹配段抹成等长空格（换行保留），这样行号与列号都不动。"""
    return pattern.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def tokens_of(term: str) -> list[str]:
    """把一个 ASCII 词切成小写 token：WorkUnit / work_unit / work-unit → ['work','unit']。"""
    s = re.sub(r"[_\-.]+", " ", term)
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    return [t.lower() for t in s.split() if t]


def normal(term: str) -> str:
    return "".join(tokens_of(term))


def is_ascii_wordish(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_\-. ]*", s or ""))


def is_compound_identifier(label: str) -> bool:
    """这个本体条目是不是一个**复合标识符**（`BankingTransaction` / `banking_transaction`）。

    只有复合标识符参与 token 子集判定。理由是 2026-09-07 在 `dogfood/ring-audit` 上的第一次
    实跑：`dos.yaml` 的 synonyms 里混着三类东西——短语（`skill node` / `acceptance contract` /
    `human seam`）、文件名（`done_when.yaml`）、带占位符的模式（`CARD-xx` / `ev-nnnn`）。
    把它们也切成 token，散文里每一个 `skill` / `agent` / `human` / `yaml` 都变成「真子集」，
    一次报出 18 条 near_miss，其中 15 条是噪音。短语的中心词单独出现是正常英语，不是漂移。

    判据：无空白、无路径分隔符、无 `.ext` 结尾、≥2 个 token、每个 token 是 ≥3 个字母的词。
    """
    if not label or re.search(r"[\s/\\]", label):
        return False
    if re.search(r"\.[A-Za-z][A-Za-z0-9]{0,5}$", label):
        return False
    toks = tokens_of(label)
    return len(toks) >= 2 and all(re.fullmatch(r"[a-z][a-z0-9]{2,}", t) for t in toks)


def rule_shapes(rule_ids) -> list[re.Pattern]:
    """从声明的 rule id 里观察出形状，不硬编码 R\\d{3}。"""
    shapes = set()
    for rid in rule_ids:
        m = re.fullmatch(r"([A-Za-z]{1,6})(\d{2,4})", str(rid))
        if m:
            shapes.add((m.group(1), len(m.group(2))))
    return [re.compile(rf"\b{re.escape(p)}\d{{{n}}}\b") for p, n in sorted(shapes)]


# ---------------------------------------------------------------- 制品读取
def detect_kind(path: str) -> str:
    base = os.path.basename(path).lower()
    ext = os.path.splitext(base)[1]
    if ext in (".md", ".markdown", ".txt", ""):
        return "markdown"
    if ext in (".yaml", ".yml"):
        if base.startswith("card-") or "/cards/" in path.replace("\\", "/").lower():
            return "card"
        if "done_when" in base or "acceptance" in base or "contract" in base:
            return "contract"
        return "yaml"
    return "markdown"


def md_segments(text: str):
    """markdown → [(lineno, 该行的散文文本)]，代码 / URL / 路径已抹除。"""
    t = blank(text, FENCE_RE)
    t = blank(t, HTML_COMMENT_RE)
    t = blank(t, INLINE_CODE_RE)
    t = blank(t, URL_RE)
    t = blank(t, LINK_TARGET_RE)
    t = blank(t, PATHY_RE)
    return [(i, line) for i, line in enumerate(t.splitlines(), 1)]


def yaml_segments(text: str, kind: str, path: str):
    """YAML → [(lineno, 散文标量的一行)]，只走 PROSE_KEYS 覆盖的子树，跳过 SKIP_SUBTREES。

    第二个返回值是走过的**结构键名**集合：语料自己当键用的词是 schema 词汇不是领域词汇
    （`ac_ids` / `allowed_files` / `psl_ids`），拿它去压 unknown 通道的噪音，见主流程。

    行号取自 `yaml.compose` 的 start_mark：对流式标量精确；对块标量（`|` / `>`）是**该值起始行**，
    多行值内的偏移按值内换行数累加。折叠标量的换行会被 YAML 折掉，所以那一类的行号是近似的——
    facts 里同时给出该行原文，人按文本定位比按行号快。
    """
    prose_keys = PROSE_KEYS.get(kind, PROSE_KEYS["yaml"])
    segs, keys = [], set()

    def walk(node, in_prose: bool):
        if isinstance(node, yaml.MappingNode):
            for k, v in node.value:
                kname = k.value if isinstance(k, yaml.ScalarNode) else None
                if isinstance(kname, str):
                    keys.add(kname.lower())
                if kname in SKIP_SUBTREES:
                    continue
                walk(v, in_prose or (kname in prose_keys))
        elif isinstance(node, yaml.SequenceNode):
            for item in node.value:
                walk(item, in_prose)
        elif isinstance(node, yaml.ScalarNode):
            if in_prose and isinstance(node.value, str) and node.value.strip():
                base = node.start_mark.line + 1
                for off, line in enumerate(node.value.splitlines()):
                    segs.append((base + off, line))

    try:
        for doc in yaml.compose_all(text):
            if doc is not None:
                walk(doc, False)
    except yaml.YAMLError as e:
        raise ValueError(f"{path}: YAML 解析失败：{e}") from e
    # 抹掉散文里嵌的路径与 URL（卡的 notes 里全是路径）
    return [(ln, blank(blank(txt, URL_RE), PATHY_RE)) for ln, txt in segs], keys


def artifact_waivers(text: str, kind: str) -> set:
    """制品自己声明「这个词故意不在领域里」。"""
    out = set()
    for m in re.finditer(r"<!--\s*out-of-domain\s*:\s*([^>]+?)-->", text, re.IGNORECASE):
        out |= {x.strip() for x in re.split(r"[,，;；]", m.group(1)) if x.strip()}
    if kind in ("card", "contract", "yaml"):
        for m in re.finditer(r"(?m)^\s*out_of_domain\s*:\s*\[([^\]]*)\]", text):
            out |= {x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()}
    return out


# ---------------------------------------------------------------- 候选抽取
def candidates(segments, ontology_tokens):
    """[(lineno, line)] → {term: (channel, [(lineno, line, sentence_initial)])}

    channel = "shaped"（形状像声明出来的标识符）或 "ontology_token"（普通小写词，
    但它是本体某个多词条目的组成 token）。两个通道的佐证规则不同，见 neighbour_of。
    """
    found = {}
    for lineno, line in segments:
        for rx in (CAMEL_RE, CAP_RE, SNAKE_RE, LOWER_RE):
            for m in rx.finditer(line):
                term = m.group(0)
                if term.lower() in STOPWORDS:
                    continue
                channel = "ontology_token" if rx is LOWER_RE else "shaped"
                if channel == "ontology_token" and term.lower() not in ontology_tokens:
                    continue
                nxt = line[m.end():m.end() + 1]
                if nxt in (":", "=", "("):        # YAML 键 / 赋值 / 函数调用
                    continue
                prev = line[:m.start()]
                initial = rx is CAP_RE and bool(SENTENCE_START_RE.search(prev))
                found.setdefault(term, (channel, []))[1].append((lineno, line.strip(), initial))
    return found


def neighbour_of(term: str, vocab: dict, channel: str = "shaped"):
    """本体里离 term 最近的可解析词 → (label, canonical, kind, severity, why)。

    两个通道的判定不同，这是精度的关键：

      shaped         —— 归一化相同（`work_unit` ≡ `WorkUnit`：写下来的标识符差一个写法，
                        本体却没写这条 synonyms），或候选是某个复合标识符的**真子集**；
                        都不成立时用字面相似度兜一个 `typo`（报出来但不计入）。
      ontology_token —— 只认真子集：`transaction` ⊊ {banking, transaction}。
                        散文里的 `account` 与本体的 `Account` token 集相等，那只是英文小写，
                        不是漂移；把它算成发现，这个传感器一天就会被关掉。

    **反方向（候选 ⊋ 本体词）整条砍掉**，这是实跑换来的：`run_evidence` ⊋ `Run`、
    `gate_json` ⊋ `Gate`、`loop_back` ⊋ `Loop` —— 单 token 的本体对象（Run / Gate / Loop /
    Node / Card）几乎被任何含该词的字段名命中，dogfood 上 11/18 条 near_miss 是这一类。
    含着本体词的复合字段名是**普通命名**，不是术语漂移。这一向的召回是精度的价钱。
    """
    tset = set(tokens_of(term))
    best_near, best_typo, best_typo_ratio = None, None, 0.0
    nterm = normal(term)
    for label, (canon, kind) in vocab.items():
        if not is_ascii_wordish(label):
            continue                      # CJK 没有分词器，不参与 token 判定
        lset = set(tokens_of(label))
        if not lset:
            continue
        compound = is_compound_identifier(label)
        shared = (tset & lset) - GENERIC_TOKENS
        if compound and shared and tset < lset:
            if best_near is None or len(lset) < len(set(tokens_of(best_near[0]))):
                best_near = (label, canon, kind, "near_miss",
                             f"`{term}` 是复合标识符 `{label}` 的真子集（共享 {sorted(shared)}）"
                             f"——省掉了限定词，读的人（和 agent）得自己猜是不是同一个东西")
        if channel == "ontology_token":
            continue                      # 这一通道只有真子集一条判据
        if normal(label) == nterm and label != term:
            return (label, canon, kind, "near_miss",
                    f"归一化后与 `{label}` 相同（只差大小写 / 分隔符）——本体里没写这条 synonyms")
        r = difflib.SequenceMatcher(None, nterm, normal(label)).ratio()
        if r > best_typo_ratio:
            best_typo_ratio, best_typo = r, (label, canon, kind, "typo",
                                             f"与 `{label}` 字面相似度 {r:.2f}，但没有共同 token")
    if best_near:
        return best_near
    if channel == "shaped" and best_typo and best_typo_ratio >= 0.87 and len(nterm) >= 5:
        return best_typo
    return None


# ---------------------------------------------------------------- 主流程
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("artifacts", nargs="*", help="制品路径或 glob")
    ap.add_argument("--dos", help="dos.yaml；缺席 = 未评估（exit 3），不是通过")
    ap.add_argument("--artifact-kind", default="auto",
                    choices=["auto", "contract", "card", "markdown", "yaml"])
    ap.add_argument("--waive", default="", help="逗号分隔：故意不在领域里的词")
    ap.add_argument("--waivers", help="decisions.md：读 `## Vocabulary waivers` 段")
    ap.add_argument("--stopwords", help="每行一个词，追加到内建 stopword 表")
    ap.add_argument("--min-occurrences", type=int, default=3,
                    help="unknown 通道的佐证门槛（缺省 3）")
    ap.add_argument("--count-unknown", action="store_true",
                    help="让 unknown 也计入退出码（提高召回，自担噪音）")
    ap.add_argument("--threshold", type=int, default=0, help="容忍的计入发现数（缺省 0）")
    ap.add_argument("--require-ontology", action="store_true", help="把 exit 3 变成 exit 1")
    ap.add_argument("--no-unused", action="store_true", help="不报反向信号")
    ap.add_argument("--max-notes", type=int, default=10,
                    help="stdout 上最多印几条不计入的 note（计入的发现永远全印）")
    ap.add_argument("--out", help="把 facts 写到这里（缺省不写文件，见 docstring）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    # -- 制品 --------------------------------------------------------------
    paths = []
    for spec in a.artifacts:
        hits = sorted(globmod.glob(spec, recursive=True)) if any(c in spec for c in "*?[") else [spec]
        for h in hits:
            if os.path.isfile(h) and h not in paths:
                paths.append(h)
    if not paths:
        sys.stderr.write("verify_vocabulary: 没有可读的制品（给路径或 glob）\n")
        return 2

    facts = {"tool": "verify_vocabulary", "tier": "B", "dos": a.dos,
             "thresholds": {"min_occurrences": a.min_occurrences, "threshold": a.threshold,
                            "count_unknown": bool(a.count_unknown)},
             "artifacts": [], "ontology": {}, "findings": [], "unused_ontology": [],
             "waived": [], "unevaluated": [], "verdict": "unevaluated"}

    # -- 本体：没有 = 未评估 ------------------------------------------------
    if not a.dos or not os.path.isfile(a.dos):
        facts["unevaluated"].append({"what": "ontology", "why": f"没有 dos.yaml（--dos {a.dos!r}）",
                                     "fix": "跑 /dos-extract 产出 dos.yaml，或说明这个仓库没有本体"})
        return finish(a, facts, 3)
    try:
        closure = dos_closure.load_closure(a.dos)
    except Exception as e:
        sys.stderr.write(f"verify_vocabulary: 读不了 {a.dos}: {e}\n")
        return 2
    if not closure.objects:
        facts["unevaluated"].append({"what": "ontology", "why": f"{a.dos} 的 objects 为空——没有词表可比",
                                     "fix": "补 objects:，或换一份真的 dos.yaml"})
        facts["ontology"] = {"objects": 0, "object_synonyms": 0, "rules": len(closure.rules)}
        return finish(a, facts, 3)

    vocab = closure.vocabulary()                       # label -> (canonical, kind)
    # 第四通道的字典只从**复合标识符**来（见 is_compound_identifier 的实跑理由）。
    ontology_tokens = set()
    for label in vocab:
        if is_ascii_wordish(label) and is_compound_identifier(label):
            ontology_tokens |= {t for t in tokens_of(label) if t not in GENERIC_TOKENS}
    facts["ontology"] = {"objects": len(closure.objects),
                         "object_synonyms": len(closure.object_aliases),
                         "rules": len(closure.rules),
                         "rule_aliases": len(closure.rule_aliases),
                         "compound_identifiers": sorted(
                             l for l in vocab
                             if is_ascii_wordish(l) and is_compound_identifier(l))}

    # -- 豁免 --------------------------------------------------------------
    waived = {w.strip() for w in a.waive.split(",") if w.strip()}
    waiver_why = {w: "--waive" for w in waived}
    if a.waivers:
        for name, why in parse_waivers(a.waivers, "vocabulary waivers").items():
            waived.add(name)
            waiver_why[name] = why or f"{a.waivers} `## Vocabulary waivers`"
    if a.stopwords:
        try:
            for line in open(a.stopwords, encoding="utf-8"):
                w = line.strip()
                if w and not w.startswith("#"):
                    STOPWORDS.add(w.lower())
        except OSError as e:
            sys.stderr.write(f"verify_vocabulary: 读不了 --stopwords: {e}\n")
            return 2

    # -- 扫描 --------------------------------------------------------------
    shapes = rule_shapes(closure.rules)
    all_cands, rule_refs, corpus_lines, schema_keys = {}, {}, [], set()
    for p in paths:
        kind = detect_kind(p) if a.artifact_kind == "auto" else a.artifact_kind
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError as e:
            sys.stderr.write(f"verify_vocabulary: 读不了 {p}: {e}\n")
            return 2
        for w in artifact_waivers(text, kind):
            waived.add(w)
            waiver_why.setdefault(w, f"{p} 自己声明 out-of-domain")
        try:
            if kind == "markdown":
                segs = md_segments(text)
            else:
                segs, keys = yaml_segments(text, kind, p)
                schema_keys |= keys
        except ValueError as e:
            sys.stderr.write(f"verify_vocabulary: {e}\n")
            return 2
        facts["artifacts"].append({"path": p, "kind": kind, "prose_lines": len(segs)})
        corpus_lines.extend(txt for _, txt in segs)
        for term, (channel, hits) in candidates(segs, ontology_tokens).items():
            entry = all_cands.setdefault(term, {"channel": channel, "where": []})
            for ln, line, initial in hits:
                entry["where"].append({"file": p, "line": ln, "quote": line[:160],
                                       "sentence_initial": initial})
        for ln, line in segs:
            for rx in shapes:
                for m in rx.finditer(line):
                    rule_refs.setdefault(m.group(0), []).append(
                        {"file": p, "line": ln, "quote": line[:160]})

    # -- 判定：对象名词 ----------------------------------------------------
    findings, dropped = [], {"resolved": 0, "waived": 0, "sentence_initial": 0,
                             "uncorroborated": 0, "schema_key": 0, "code_shaped": 0}
    for term, entry in sorted(all_cands.items()):
        channel, where = entry["channel"], entry["where"]
        if closure.resolve_object(term) is not None:
            dropped["resolved"] += 1
            continue
        if term in waived:
            dropped["waived"] += 1
            facts["waived"].append({"term": term, "why": waiver_why.get(term, ""),
                                    "occurrences": len(where)})
            continue
        if where and all(w["sentence_initial"] for w in where):
            dropped["sentence_initial"] += 1      # 全部出现都在句首 = 英文语法，不是术语
            continue
        nb = neighbour_of(term, vocab, channel)
        if nb:
            label, canon, nkind, relation, why = nb
            severity = relation
        else:
            label = canon = nkind = None
            why = "本体里没有字面相近的词"
            severity = "unknown"
        if severity == "unknown":
            # ontology_token 通道没有形状佐证，找不到真子集邻居就不是发现，直接丢。
            if channel == "ontology_token" or len(where) < a.min_occurrences:
                dropped["uncorroborated"] += 1
                continue
            # 语料自己拿它当结构键用 = schema 词汇，不是领域名词。只压 unknown 这一档：
            # near_miss / typo / unresolved_rule 是有邻居佐证的，不受这条影响。
            if term.lower() in schema_keys:
                dropped["schema_key"] += 1
                continue
            # snake_case 出现在散文里，绝大多数是被引用的字段名 / 枚举值 / 错误码，不是团队说的词。
            # dogfood 实跑：37 条 unknown 里 30 条是这一类（`merge_candidate` / `signer_kind` /
            # `authorization_ref`），而真正值得看的 5 条全是大写开头的名词（Ring / Part / Gap /
            # Artifact / Assessment）。unknown 是「本体可能漏了一个词」的猜测，猜测就该走
            # 团队真会说出口的那种词形。snake_case 仍然完整参与 near_miss——
            # `banking_transaction` ≡ `BankingTransaction` 正是那一档的招牌案例。
            if "_" in term:
                dropped["code_shaped"] += 1
                continue
        counted = severity == "near_miss" or (severity == "unknown" and a.count_unknown)
        findings.append({"term": term, "severity": severity, "counted": counted,
                         "channel": channel,
                         "occurrences": len(where), "neighbour": label,
                         "neighbour_canonical": canon, "neighbour_kind": nkind,
                         "why": why, "where": where[:5]})

    # -- 判定：规则引用（几乎无假阳性，直接计入）---------------------------
    for rid, where in sorted(rule_refs.items()):
        if closure.resolve_rule(rid) is not None or rid in waived:
            continue
        near = difflib.get_close_matches(rid, sorted(closure.rules), n=1, cutoff=0.6)
        findings.append({"term": rid, "severity": "unresolved_rule", "counted": True,
                         "occurrences": len(where), "neighbour": near[0] if near else None,
                         "neighbour_canonical": near[0] if near else None,
                         "neighbour_kind": "rule" if near else None,
                         "why": f"形状像本体的 rule id，但 {a.dos} 里没有这条",
                         "where": where[:5]})

    order = {"unresolved_rule": 0, "near_miss": 1, "unknown": 2, "typo": 3}
    findings.sort(key=lambda f: (order.get(f["severity"], 9), -f["occurrences"], f["term"]))
    facts["findings"] = findings
    facts["dropped_candidates"] = dropped

    # -- 反向信号：本体声明了、没人用 --------------------------------------
    if not a.no_unused:
        blob = "\n".join(corpus_lines)
        for canon, body in sorted(closure.objects.items()):
            variants = [canon] + [str(s).strip() for s in (body.get("synonyms") or []) if s]
            if not any(re.search(variant_pattern(v), blob, re.IGNORECASE) for v in variants):
                facts["unused_ontology"].append({"label": canon, "kind": "object",
                                                 "variants": variants})
        for rid in sorted(closure.rules):
            variants = [rid] + [al for al, c in closure.rule_aliases.items() if c == rid]
            if not any(re.search(variant_pattern(v), blob, re.IGNORECASE) for v in variants):
                facts["unused_ontology"].append({"label": rid, "kind": "rule", "variants": variants})

    counted = [f for f in findings if f["counted"]]
    facts["counted_findings"] = len(counted)
    facts["verdict"] = "drift" if len(counted) > a.threshold else "pass"
    return finish(a, facts, 1 if len(counted) > a.threshold else 0)


def finish(a, facts, rc: int) -> int:
    if rc == 3 and a.require_ontology:
        facts["verdict"] = "unevaluated_treated_as_drift"
        rc = 1
    try:
        if a.out:
            d = os.path.dirname(a.out)
            if d:
                os.makedirs(d, exist_ok=True)
            with open(a.out, "w", encoding="utf-8") as f:
                yaml.safe_dump(facts, f, allow_unicode=True, sort_keys=False, width=120)
    except OSError as e:
        sys.stderr.write(f"verify_vocabulary: 写不了 facts: {e}\n")
        return 2
    if a.json:
        print(json.dumps(facts, ensure_ascii=False, indent=2))
        return rc
    o = facts["ontology"]
    print(f"verify_vocabulary · verdict = {facts['verdict'].upper()} · "
          f"本体 {o.get('objects', 0)} 对象 / {o.get('object_synonyms', 0)} 同义词 / "
          f"{o.get('rules', 0)} 规则 · 制品 {len(facts['artifacts'])}")
    for u in facts["unevaluated"]:
        print(f"  UNEVAL  {u['what']}: {u['why']} → {u['fix']}")
    shown, notes_shown, notes_total = 0, 0, 0
    for f in facts["findings"]:
        if not f["counted"]:
            notes_total += 1
            if notes_shown >= a.max_notes:
                continue
            notes_shown += 1
        w = f["where"][0] if f["where"] else {}
        nb = f" ≈ `{f['neighbour']}`" if f["neighbour"] else ""
        print(f"  {'DRIFT ' if f['counted'] else 'note  '} [{f['severity']}] `{f['term']}`{nb} "
              f"×{f['occurrences']} — {w.get('file', '?')}:{w.get('line', '?')}")
        print(f"          {f['why']}")
        shown += 1
    if notes_total > notes_shown:
        print(f"  …… 另有 {notes_total - notes_shown} 条不计入的 note（弱证据），见 {a.out}")
    if facts["unused_ontology"]:
        print(f"  反向信号（弱证据，不计入）：本体里 {len(facts['unused_ontology'])} 条无人使用 — "
              + ", ".join(u["label"] for u in facts["unused_ontology"][:10]))
    d = facts.get("dropped_candidates")
    if d:
        print(f"  丢弃候选：已解析 {d['resolved']} · 已豁免 {d['waived']} · "
              f"句首大写 {d['sentence_initial']} · 佐证不足 {d['uncorroborated']} · "
              f"schema 键名 {d.get('schema_key', 0)} · 代码词形 {d.get('code_shaped', 0)}")
    if a.out:
        print(f"  facts → {a.out}")
    elif facts["findings"] or facts["unevaluated"]:
        print("  （没写 facts 文件：--out 缺省不落地。要留证据加 --out <path>，要机器读加 --json）")
    return rc


if __name__ == "__main__":
    sys.exit(main())
