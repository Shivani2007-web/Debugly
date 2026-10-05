"""Infinite loop rule tests."""

from app.models.execution import ExecutionStatus
from tests.helpers import detect_keys, make_execution


def test_while_true_no_break_detected():
    code = "def f():\n    while True:\n        x = 1\n"
    keys = detect_keys(code)
    assert "infinite_loop" in keys


def test_while_true_with_break_not_flagged():
    code = (
        "def f():\n"
        "    while True:\n"
        "        x = compute()\n"
        "        if x:\n"
        "            break\n"
    )
    keys = detect_keys(code)
    assert "infinite_loop" not in keys


def test_no_progress_variable_detected():
    code = (
        "def f(n):\n"
        "    i = 0\n"
        "    while i < n:\n"
        "        print(i)\n"  # i never advances
    )
    keys = detect_keys(code)
    assert "infinite_loop" in keys


def test_advancing_variable_not_flagged():
    code = (
        "def f(n):\n"
        "    i = 0\n"
        "    while i < n:\n"
        "        i += 1\n"
    )
    keys = detect_keys(code)
    assert "infinite_loop" not in keys


def test_timeout_corroborates():
    code = "def f():\n    while True:\n        pass\n"
    execution = make_execution(status=ExecutionStatus.TIMEOUT)
    keys = detect_keys(code, execution=execution)
    assert "infinite_loop" in keys
    assert keys["infinite_loop"] >= 0.8
