"""Recursion / base-case rule tests."""

from app.models.execution import ExecutionStatus
from tests.helpers import detect_keys, make_execution


def test_recursion_without_base_case_detected():
    code = "def f(n):\n    return f(n - 1)\n"
    keys = detect_keys(code)
    assert "recursion_base_case" in keys


def test_recursion_with_base_case_not_flagged():
    code = (
        "def f(n):\n"
        "    if n <= 0:\n"
        "        return 0\n"
        "    return n + f(n - 1)\n"
    )
    keys = detect_keys(code)
    assert "recursion_base_case" not in keys


def test_recursion_error_corroborates():
    code = "def f(n):\n    return f(n - 1)\n"
    execution = make_execution(
        status=ExecutionStatus.RUNTIME_ERROR,
        error_type="RecursionError",
        error_message="maximum recursion depth exceeded",
    )
    keys = detect_keys(code, execution=execution)
    assert "recursion_base_case" in keys


def test_non_recursive_not_flagged():
    code = "def f(n):\n    return n + 1\n"
    keys = detect_keys(code)
    assert "recursion_base_case" not in keys
