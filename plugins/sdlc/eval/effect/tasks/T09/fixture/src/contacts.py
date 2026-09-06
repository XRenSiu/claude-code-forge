"""通讯录去重。现在：名字 + 手机号完全相同才算重复。"""


def normalise_phone(p):
    return "".join(ch for ch in (p or "") if ch.isdigit())[-11:]


def find_duplicates(contacts):
    """contacts: [{"id","name","phone","email","org"}] → [[id, id, ...]] 每组是同一个人。"""
    seen, groups = {}, []
    for c in contacts:
        key = (c.get("name"), c.get("phone"))
        if key in seen:
            seen[key].append(c["id"])
        else:
            seen[key] = [c["id"]]
    for ids in seen.values():
        if len(ids) > 1:
            groups.append(ids)
    return groups
