"""Function parameter / argument rule tests."""

from app.models.execution import ExecutionStatus
from tests.helpers import detect_keys, make_execution


def test_arg_count_mismatch_detected():
    code = (
        "def greet(name, greeting):\n"
        "    return greeting + name\n"
        "greet('alice')\n"
    )
    keys = detect_keys(code)
    assert "function_parameter" in keys


def test_correct_arg_count_not_flagged():
    code = (
        "def greet(name, greeting):\n"
        "    return greeting + name\n"
        "greet('alice', 'hi ')\n"
    )
    keys = detect_keys(code)
    assert "function_parameter" not in keys


def test_type_error_about_arguments_corroborates():
    code = (
        "def greet(name, greeting):\n"
        "    return greeting + name\n"
        "greet('alice')\n"
    )
    execution = make_execution(
        status=ExecutionStatus.RUNTIME_ERROR,
        error_type="TypeError",
        error_message="greet() missing 1 required positional argument: 'greeting'",
        error_line=3,
    )
    keys = detect_keys(code, execution=execution)
    assert "function_parameter" in keys
    assert keys["function_parameter"] >= 0.6


def test_unrelated_type_error_not_flagged():
    # TypeError not about arguments, and no call mismatch, should not trip it.
    code = "def f(a):\n    return a + 1\n"
    execution = make_execution(
        status=ExecutionStatus.RUNTIME_ERROR,
        error_type="TypeError",
        error_message="unsupported operand type(s) for +: 'int' and 'str'",
    )
    keys = detect_keys(code, execution=execution)
    assert "function_parameter" not in keys
