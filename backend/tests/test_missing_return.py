"""Missing / incorrect return rule tests."""

from tests.helpers import detect_keys


def test_prints_instead_of_returns_detected():
    code = (
        "def add(a, b):\n"
        "    result = a + b\n"
        "    print(result)\n"
    )
    keys = detect_keys(code)
    assert "missing_return" in keys


def test_returns_value_not_flagged():
    code = "def add(a, b):\n    return a + b\n"
    keys = detect_keys(code)
    assert "missing_return" not in keys


def test_computes_without_return_detected():
    code = (
        "def total(xs):\n"
        "    s = 0\n"
        "    for x in xs:\n"
        "        s += x\n"
    )
    keys = detect_keys(code)
    assert "missing_return" in keys


def test_prints_and_returns_not_flagged():
    code = (
        "def add(a, b):\n"
        "    result = a + b\n"
        "    print(result)\n"
        "    return result\n"
    )
    keys = detect_keys(code)
    assert "missing_return" not in keys
