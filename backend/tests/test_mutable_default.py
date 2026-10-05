"""Mutable default argument rule tests."""

from tests.helpers import detect_keys


def test_mutable_list_default_detected():
    code = "def add_item(item, bucket=[]):\n    bucket.append(item)\n    return bucket\n"
    keys = detect_keys(code)
    assert "mutable_default" in keys


def test_mutable_dict_default_detected():
    code = "def f(k, v, d={}):\n    d[k] = v\n    return d\n"
    keys = detect_keys(code)
    assert "mutable_default" in keys


def test_immutable_default_not_flagged():
    code = "def f(x, n=0):\n    return x + n\n"
    keys = detect_keys(code)
    assert "mutable_default" not in keys


def test_none_default_not_flagged():
    code = (
        "def f(item, bucket=None):\n"
        "    if bucket is None:\n"
        "        bucket = []\n"
        "    bucket.append(item)\n"
        "    return bucket\n"
    )
    keys = detect_keys(code)
    assert "mutable_default" not in keys
