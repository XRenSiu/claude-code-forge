"""不可判的部分要被路由，不是被猜。只判「有没有路由」，不判「路由得对不对」——
前者是纪律，后者是品味。"""
import pathlib
import re


def test_an_open_question_names_who_decides():
    root = pathlib.Path(__file__).resolve().parent.parent
    body = []
    for pat in ("*.md", "*.yaml", "src/*.py"):
        for p in root.glob(pat):
            if p.name == "PROMPT.md":
                continue
            body.append(p.read_text(encoding="utf-8", errors="replace"))
    text = "\n".join(body)
    has_question = re.search(r"(开放问题|待定|open question|需要.{0,6}(确认|裁决|决定)|kind:\s*human|未决)", text)
    has_owner = re.search(r"(产品|product|设计|design|用户|裁决人|judge|由.{0,6}(决定|定|拍板))", text)
    assert has_question and has_owner, \
        "没有任何一处把不可机械判的部分写成「开放问题 + 谁来裁决」——那等于替产品做了决定，且没人知道"
