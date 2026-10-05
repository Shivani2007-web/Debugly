"""List indexing rule tests."""

from app.models.execution import ExecutionStatus
from tests.helpers import detect_keys, make_execution


def test_len_as_index_detected():
    code = "def last(xs):\n    return xs[len(xs)]\n"
    keys = detect_keys(code)
    assert "list_indexing" in keys


def test_correct_last_index_not_flagged():
    code = "def last(xs):\n    return xs[len(xs) - 1]\n"
    keys = detect_keys(code)
    assert "list_indexing" not in keys


def test_index_error_with_subscript_detected():
    code = "def get(xs, i):\n    return xs[i]\n"
    execution = make_execution(
        status=ExecutionStatus.TEST_FAILED,
        failed_tests_with_error=["IndexError"],
        error_message="list index out of range",
        error_line=2,
    )
    keys = detect_keys(code, execution=execution)
    assert "list_indexing" in keys


def test_no_subscript_no_detection():
    code = "def f(a, b):\n    return a + b\n"
    keys = detect_keys(code)
    assert "list_indexing" not in keys
