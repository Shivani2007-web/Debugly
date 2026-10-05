"""Assignment vs comparison rule tests."""

from tests.helpers import detect_keys


def test_comparison_as_statement_detected():
    # `total == a + b` on its own line discards the result; likely meant `=`.
    code = (
        "def f(a, b):\n"
        "    total = 0\n"
        "    total == a + b\n"
        "    return total\n"
    )
    keys = detect_keys(code)
    assert "assignment_vs_comparison" in keys


def test_assignment_not_flagged():
    code = (
        "def f(a, b):\n"
        "    total = a + b\n"
        "    return total\n"
    )
    keys = detect_keys(code)
    assert "assignment_vs_comparison" not in keys


def test_comparison_in_condition_not_flagged():
    # `==` inside an if is correct usage, not a discarded statement.
    code = (
        "def f(a):\n"
        "    if a == 5:\n"
        "        return True\n"
        "    return False\n"
    )
    keys = detect_keys(code)
    assert "assignment_vs_comparison" not in keys
