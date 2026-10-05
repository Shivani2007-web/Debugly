"""Off-by-one / loop boundary rule tests."""

from app.models.execution import ExecutionStatus
from tests.helpers import detect_keys, make_execution


def test_range_len_plus_one_is_detected():
    code = (
        "def f(xs):\n"
        "    total = 0\n"
        "    for i in range(len(xs) + 1):\n"
        "        total += xs[i]\n"
        "    return total\n"
    )
    keys = detect_keys(code)
    assert "off_by_one" in keys


def test_index_error_corroborates_off_by_one():
    code = (
        "def f(xs):\n"
        "    for i in range(len(xs) + 1):\n"
        "        print(xs[i])\n"
    )
    execution = make_execution(
        status=ExecutionStatus.TEST_FAILED,
        failed_tests_with_error=["IndexError", "IndexError"],
        error_message="list index out of range",
        error_line=3,
    )
    keys = detect_keys(code, execution=execution)
    assert "off_by_one" in keys
    # Code (STRONG) + repeated error (STRONG) + corroboration → high confidence.
    assert keys["off_by_one"] >= 0.8


def test_correct_loop_not_flagged():
    code = (
        "def f(xs):\n"
        "    total = 0\n"
        "    for i in range(len(xs)):\n"
        "        total += xs[i]\n"
        "    return total\n"
    )
    keys = detect_keys(code)
    assert "off_by_one" not in keys


def test_index_error_without_loop_structure_not_off_by_one():
    # A bare IndexError with no loop/index structure should not become
    # off-by-one evidence out of thin air.
    code = "def f():\n    return 1\n"
    execution = make_execution(
        status=ExecutionStatus.RUNTIME_ERROR,
        error_type="IndexError",
        error_message="list index out of range",
    )
    keys = detect_keys(code, execution=execution)
    assert "off_by_one" not in keys
