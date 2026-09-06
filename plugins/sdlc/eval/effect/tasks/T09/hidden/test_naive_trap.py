import inspect

from src import contacts


def test_phone_is_normalised_before_comparing():
    src = inspect.getsource(contacts.find_duplicates)
    assert "normalise_phone" in src or "normalize" in src, "比号码之前没有归一化"


def test_identity_is_not_name_plus_phone_equality():
    src = inspect.getsource(contacts.find_duplicates)
    assert 'c.get("name"), c.get("phone")' not in src, "还是「名字 + 号码全等」这个键"
