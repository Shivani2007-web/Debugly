"""Execution orchestration.

Turns a student submission into a structured :class:`ExecutionResult` by:

1. Generating a harness program (student code + guards + test loop).
2. Running it through the isolated :mod:`sandbox`.
3. Parsing the harness's JSON report (or a syntax/runtime error) into the
   unified result contract.

The harness writes its structured report to a sentinel-delimited block on
stdout so the student's own ``print`` output stays separate and readable.
"""

from __future__ import annotations

import json
import re

from app.models.execution import (
    ErrorInfo,
    ExecutionResult,
    ExecutionStatus,
    TestCase,
    TestResult,
)
from app.services.execution.sandbox import SandboxSetupError, run_in_sandbox

# Sentinels the harness prints around its JSON report. Chosen to be extremely
# unlikely to collide with student output.
REPORT_START = "<<<DEBUGLY_REPORT_START>>>"
REPORT_END = "<<<DEBUGLY_REPORT_END>>>"

# In-process guards injected ahead of student code. These harden the single
# process (defence in depth on top of the subprocess isolation): deny network
# via socket, and deny opening files for writing.
_GUARD_PREAMBLE = f'''
import sys, io, json, traceback

# ---- Network guard: block socket connections ----
try:
    import socket as _socket
    def _blocked_socket(*a, **k):
        raise OSError("Network access is disabled in the sandbox.")
    _socket.socket = _blocked_socket            # type: ignore
    _socket.create_connection = _blocked_socket  # type: ignore
except Exception:
    pass

# ---- Filesystem write guard: allow reads, deny writes ----
_real_open = open
def _guarded_open(file, mode="r", *args, **kwargs):
    if any(flag in mode for flag in ("w", "a", "x", "+")):
        raise PermissionError("Filesystem writes are disabled in the sandbox.")
    return _real_open(file, mode, *args, **kwargs)
import builtins as _builtins
_builtins.open = _guarded_open

_DEBUGLY_REPORT_START = {REPORT_START!r}
_DEBUGLY_REPORT_END = {REPORT_END!r}

def _debugly_emit(report):
    sys.stdout.flush()
    sys.stderr.flush()
    print(_DEBUGLY_REPORT_START)
    print(json.dumps(report))
    print(_DEBUGLY_REPORT_END)
'''


def _student_module_wrapper(code: str) -> str:
    """Indent student code so it can be exec'd into a namespace with error capture."""
    # We exec the student source so a SyntaxError is catchable and reportable
    # with a line number, rather than killing the harness at import time.
    escaped = repr(code)
    return f"""
_STUDENT_SRC = {escaped}
_student_ns = {{}}
_compile_error = None
try:
    _compiled = compile(_STUDENT_SRC, "<student>", "exec")
    exec(_compiled, _student_ns)
except SyntaxError as e:
    _compile_error = {{
        "kind": "syntax_error",
        "error_type": type(e).__name__,
        "message": str(e.msg),
        "line": e.lineno,
    }}
except Exception as e:
    _compile_error = {{
        "kind": "runtime_error",
        "error_type": type(e).__name__,
        "message": str(e),
        "line": _first_student_line(traceback.extract_tb(sys.exc_info()[2])),
        "traceback": traceback.format_exc(),
    }}
"""


_HELPERS = '''
def _first_student_line(frames):
    for fr in reversed(frames):
        if fr.filename == "<student>":
            return fr.lineno
    return None
'''


def _test_loop(serialized_tests: str) -> str:
    """Harness tail that runs assertion test cases against the student namespace."""
    return f"""
_tests = json.loads({serialized_tests!r})
_results = []
_report = {{"kind": "ok", "tests": _results}}

if _compile_error is not None:
    _debugly_emit({{"kind": _compile_error["kind"], "error": _compile_error}})
else:
    for _t in _tests:
        _entry = {{"name": _t["name"], "hidden": _t.get("hidden", False)}}
        try:
            _fn = _student_ns.get(_t["function_name"])
            if _fn is None or not callable(_fn):
                _entry.update({{
                    "passed": False,
                    "expected": _t.get("expected"),
                    "actual": None,
                    "error": {{
                        "error_type": "NameError",
                        "message": "Function '" + str(_t["function_name"]) + "' is not defined.",
                        "line": None,
                    }},
                }})
            else:
                _actual = _fn(*_t.get("args", []), **_t.get("kwargs", {{}}))
                _passed = _actual == _t.get("expected")
                try:
                    json.dumps(_actual)
                    _actual_safe = _actual
                except Exception:
                    _actual_safe = repr(_actual)
                _entry.update({{
                    "passed": bool(_passed),
                    "expected": _t.get("expected"),
                    "actual": _actual_safe,
                    "error": None,
                }})
        except Exception as e:
            _entry.update({{
                "passed": False,
                "expected": _t.get("expected"),
                "actual": None,
                "error": {{
                    "error_type": type(e).__name__,
                    "message": str(e),
                    "line": _first_student_line(traceback.extract_tb(sys.exc_info()[2])),
                    "traceback": traceback.format_exc(),
                }},
            }})
        _results.append(_entry)
    _debugly_emit(_report)
"""


def _run_only_tail() -> str:
    """Harness tail for a plain run: just surface a compile/runtime error, if any."""
    return """
if _compile_error is not None:
    _debugly_emit({"kind": _compile_error["kind"], "error": _compile_error})
else:
    _debugly_emit({"kind": "ok", "tests": []})
"""


def _build_script(code: str, tests: list[TestCase] | None) -> str:
    """Assemble the full harness program text."""
    serialized = json.dumps([t.model_dump() for t in (tests or [])])
    tail = _test_loop(serialized) if tests is not None else _run_only_tail()
    return (
        _GUARD_PREAMBLE
        + _HELPERS
        + _student_module_wrapper(code)
        + tail
    )


def _extract_report(stdout: str) -> tuple[str, dict | None]:
    """Split student stdout from the harness JSON report.

    Returns (clean_stdout, report_dict_or_None).
    """
    pattern = re.compile(
        re.escape(REPORT_START) + r"\s*(.*?)\s*" + re.escape(REPORT_END),
        re.DOTALL,
    )
    match = pattern.search(stdout)
    if not match:
        return stdout, None
    clean = (stdout[: match.start()] + stdout[match.end():]).strip("\n")
    try:
        report = json.loads(match.group(1))
    except json.JSONDecodeError:
        report = None
    return clean, report


def _result_from_report(
    report: dict | None,
    outcome_stdout: str,
    outcome_stderr: str,
    duration_ms: int,
    truncated: bool,
    *,
    with_tests: bool,
) -> ExecutionResult:
    """Convert a parsed harness report into an ExecutionResult."""
    if report is None:
        # Harness never emitted a report → something crashed before guards,
        # or output got truncated. Treat as runtime error with stderr as detail.
        return ExecutionResult(
            status=ExecutionStatus.RUNTIME_ERROR,
            stdout=outcome_stdout,
            stderr=outcome_stderr,
            error=ErrorInfo(message=outcome_stderr.strip() or "Execution produced no report."),
            duration_ms=duration_ms,
            truncated=truncated,
        )

    kind = report.get("kind")

    if kind in ("syntax_error", "runtime_error"):
        err = report.get("error", {}) or {}
        status = (
            ExecutionStatus.SYNTAX_ERROR
            if kind == "syntax_error"
            else ExecutionStatus.RUNTIME_ERROR
        )
        return ExecutionResult(
            status=status,
            stdout=outcome_stdout,
            stderr=outcome_stderr,
            error=ErrorInfo(
                error_type=err.get("error_type"),
                message=err.get("message"),
                line=err.get("line"),
                traceback=err.get("traceback"),
            ),
            duration_ms=duration_ms,
            truncated=truncated,
        )

    # kind == "ok"
    raw_tests = report.get("tests", [])
    test_results = [
        TestResult(
            name=t["name"],
            passed=bool(t.get("passed")),
            expected=t.get("expected"),
            actual=t.get("actual"),
            error=ErrorInfo(**t["error"]) if t.get("error") else None,
            hidden=bool(t.get("hidden", False)),
        )
        for t in raw_tests
    ]
    passed = sum(1 for t in test_results if t.passed)
    total = len(test_results)

    if with_tests and total > 0:
        status = ExecutionStatus.SUCCESS if passed == total else ExecutionStatus.TEST_FAILED
    else:
        status = ExecutionStatus.SUCCESS

    return ExecutionResult(
        status=status,
        stdout=outcome_stdout,
        stderr=outcome_stderr,
        test_results=test_results,
        passed_count=passed,
        total_count=total,
        duration_ms=duration_ms,
        truncated=truncated,
    )


def execute(code: str, tests: list[TestCase] | None) -> ExecutionResult:
    """Run a submission. ``tests=None`` is a plain run; a list grades it."""
    script = _build_script(code, tests)
    try:
        outcome = run_in_sandbox(script)
    except SandboxSetupError as exc:
        # Rejected before execution (e.g. oversized program). Degrade cleanly.
        return ExecutionResult(
            status=ExecutionStatus.INTERNAL_ERROR,
            stdout="",
            stderr=str(exc),
            error=ErrorInfo(error_type="SandboxSetupError", message=str(exc)),
            duration_ms=0,
        )

    if outcome.timed_out:
        return ExecutionResult(
            status=ExecutionStatus.TIMEOUT,
            stdout=outcome.stdout,
            stderr=outcome.stderr,
            error=ErrorInfo(
                error_type="TimeoutError",
                message="Execution exceeded the time limit and was stopped. "
                "Check for an infinite loop.",
            ),
            duration_ms=outcome.duration_ms,
            truncated=outcome.stdout_truncated or outcome.stderr_truncated,
        )

    clean_stdout, report = _extract_report(outcome.stdout)
    return _result_from_report(
        report,
        clean_stdout,
        outcome.stderr,
        outcome.duration_ms,
        outcome.stdout_truncated or outcome.stderr_truncated,
        with_tests=tests is not None,
    )
