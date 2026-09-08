"""同一个人 = 同一个身份，不是同一串字段。三条用例上，全等模型给相反答案。"""
from src.contacts import find_duplicates


def _same_group(groups, a, b):
    return any(a in g and b in g for g in groups)


def test_same_person_new_phone_number():
    cs = [{"id": 1, "name": "张三", "phone": "13800000000", "email": "z@acme.com", "org": "Acme"},
          {"id": 2, "name": "张三", "phone": "13911111111", "email": "z@acme.com", "org": "Acme"}]
    assert _same_group(find_duplicates(cs), 1, 2), "换了号码就认不出是同一个人（邮箱相同）"


def test_same_person_two_emails_same_phone():
    cs = [{"id": 3, "name": "李四", "phone": "+86 137-0000-0000", "email": "li@work.com", "org": "Beta"},
          {"id": 4, "name": "李四", "phone": "13700000000", "email": "li@personal.com", "org": ""}]
    assert _same_group(find_duplicates(cs), 3, 4), "同一个号码（格式不同）没被归一化"


def test_two_different_people_sharing_a_name_are_not_merged():
    cs = [{"id": 5, "name": "王伟", "phone": "13500000001", "email": "w1@a.com", "org": "A"},
          {"id": 6, "name": "王伟", "phone": "13500000002", "email": "w2@b.com", "org": "B"}]
    assert not _same_group(find_duplicates(cs), 5, 6), "同名不同人被合并了 —— 重名不是身份"
