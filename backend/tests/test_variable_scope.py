"""Variable scope rule tests."""

from app.models.execution import ExecutionStatus
from tests.helpers import detect_keys, make_execution


def test_name_error_detected():
    code = "def f():\n    return undefined_var + 1\n"
    execution = make_execution(
        status=ExecutionStatus.RUNTIME_ERROR,
        error_type="NameError",
        error_message="name 'undefined_var' is not defined",
        error_line=2,
    )
    keys = detect_keys(code, execution=execution)
    assert "variable_scope" in keys


def test_undefined_read_plus_name_error_corroborates():
    code = "def f():\n    return undefined_var + 1\n"
    execution = make_execution(
        status=ExecutionStatus.RUNTIME_ERROR,
        error_type="NameError",
        error_message="name 'undefined_var' is not defined",
        error_line=2,
    )
    result = detect_keys(code, execution=execution)
    # Code WEAK + error MEDIUM across two sources → comfortably above threshold.
    assert result["variable_scope"] >= 0.5


def test_lone_weak_undefined_read_not_reported():
    # Without an error, a single undefined-name read (WEAK) must NOT report,
    # per the "no single weak signal" policy. (Could be an intended global.)
    code = "def f():\n    return GLOBAL_CONFIG\n"
    keys = detect_keys(code)
    assert "variable_scope" not in keys


def test_well_scoped_code_not_flagged():
    code = "def f(x):\n    y = x + 1\n    return y\n"
    keys = detect_keys(code)
    assert "variable_scope" not in keys
