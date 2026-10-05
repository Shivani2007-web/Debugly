"""Phase 9 hardening tests: input validation + sandbox limits."""

import pytest
from fastapi.testclient import TestClient

from app.core.validation import (
    InputValidationError,
    MAX_CODE_CHARS,
    validate_code,
    validate_test_case_count,
)
from app.main import create_app
from app.models.execution import TestCase
from app.services.execution.runner import execute

client = TestClient(create_app())


# ---- validation unit ----

def test_validate_code_rejects_empty_when_required():
    with pytest.raises(InputValidationError):
        validate_code("", field="code", required=True)


def test_validate_code_allows_empty_when_optional():
    assert validate_code(None, required=False) == ""


def test_validate_code_rejects_oversized():
    with pytest.raises(InputValidationError):
        validate_code("x" * (MAX_CODE_CHARS + 1))


def test_validate_code_rejects_nul():
    with pytest.raises(InputValidationError):
        validate_code("a\x00b")


def test_validate_test_case_count():
    with pytest.raises(InputValidationError):
        validate_test_case_count(51)


# ---- route-level 422 ----

def test_run_route_rejects_oversized_code():
    r = client.post("/api/execution/run", json={"code": "x" * (MAX_CODE_CHARS + 1)})
    assert r.status_code == 422


def test_diagnose_route_rejects_empty_code():
    r = client.post("/api/analysis/diagnose", json={"code": ""})
    assert r.status_code == 422


# ---- sandbox hardening ----

def test_sandbox_rejects_oversized_program():
    big = "x = 1\n" * 60000  # exceeds MAX_SCRIPT_BYTES after harness
    result = execute(big, None)
    assert result.status.value == "internal_error"
    assert result.error and result.error.error_type == "SandboxSetupError"


def test_sandbox_blocks_network():
    result = execute("import socket\nsocket.socket().connect(('1.1.1.1', 80))\n", None)
    assert result.status.value in ("runtime_error",)


def test_sandbox_blocks_file_write():
    code = "def f():\n    open('x.txt', 'w')\n"
    result = execute(code, [TestCase(name="t", function_name="f", args=[], expected=None)])
    # The guard raises PermissionError -> surfaces as a failing test, not a crash.
    assert result.status.value in ("test_failed", "runtime_error")
