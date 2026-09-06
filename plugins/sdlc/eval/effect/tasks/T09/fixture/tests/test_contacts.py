from src.contacts import find_duplicates, normalise_phone


def test_exact_duplicates():
    cs = [{"id": 1, "name": "张三", "phone": "13800000000"},
          {"id": 2, "name": "张三", "phone": "13800000000"}]
    assert find_duplicates(cs) == [[1, 2]]


def test_normalise_phone():
    assert normalise_phone("+86 138-0000-0000") == "13800000000"
