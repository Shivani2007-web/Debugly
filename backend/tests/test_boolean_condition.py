"""Boolean condition rule tests."""

from tests.helpers import detect_keys


def test_bare_value_in_or_detected():
    code = (
        "def is_weekend(day):\n"
        "    if day == 'sat' or 'sun':\n"
        "        return True\n"
        "    return False\n"
    )
    keys = detect_keys(code)
    assert "boolean_condition" in keys


def test_is_for_value_comparison_detected():
    code = (
        "def check(x):\n"
        "    if x is 100:\n"
        "        return True\n"
        "    return False\n"
    )
    keys = detect_keys(code)
    assert "boolean_condition" in keys


def test_correct_or_not_flagged():
    code = (
        "def is_weekend(day):\n"
        "    if day == 'sat' or day == 'sun':\n"
        "        return True\n"
        "    return False\n"
    )
    keys = detect_keys(code)
    assert "boolean_condition" not in keys


def test_is_none_not_flagged():
    # `is None` is correct and idiomatic — must not be flagged.
    code = "def f(x):\n    if x is None:\n        return 0\n    return x\n"
    keys = detect_keys(code)
    assert "boolean_condition" not in keys
