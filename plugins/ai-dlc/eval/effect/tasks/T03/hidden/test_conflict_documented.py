"""需求自相矛盾。静默挑一条实现的，产物里看不出它知道两条规则互相咬。

判据是**实质不是用词**：60 秒能切成 6 个 10 秒窗口、每个 ≤ 5，所以真实上限是 30/分钟。
**30 这个数只有注意到两条规则相互作用才推得出来**——它比"有没有写 conflict 这个词"结实得多。
（2026-09-06 第二轮抓到：三个 arm 全红，其中一个把矛盾写得很透，只是用了「张力」「永远不会成为约束」
而不是正则里的词。检用词就是把作者的措辞当成唯一正确答案，与 E-01 同类。）
"""
import pathlib
import re


def _artifacts():
    root = pathlib.Path(__file__).resolve().parent.parent
    out = []
    for pat in ("*.md", "*.yaml", "src/*.py", "tests/*.py"):
        for p in root.glob(pat):
            if p.name == "PROMPT.md":
                continue
            out.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(out)


def test_the_interaction_is_written_down():
    body = _artifacts()
    # 实质：推出了真实上限 30（30 挨着某个速率词），或明说了两条规则互相咬
    derived = re.search(r"30\s*(次|/)?\s*(次)?\s*(每)?\s*(分钟|分|minute|min|per minute)|(分钟|每分钟)[^。\n]{0,12}30", body)
    named = re.search(r"(冲突|矛盾|张力|tension|conflict|不可能同时|mutually exclusive|更严|stricter|"
                      r"实际上限|有效上限|effective (cap|limit)|永远不会(成为约束|触发|生效)|never (bind|trigger))", body)
    assert derived or named, (
        "产物里既没有推出真实上限（30/分钟），也没有一处说两条规则互相咬——"
        "那就是静默挑了一条实现，需求里的矛盾没人知道")
