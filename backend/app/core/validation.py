"""Shared input-validation guards.

Centralises the limits applied to untrusted user input (student code,
predicted output, free-text answers) before it reaches execution, analysis, or
the tutor. Raising :class:`InputValidationError` lets routes return a clean 422
instead of letting oversized/odd input flow into the sandbox or the model.
"""

from __future__ import annotations

# Hard caps. Student programs for the MVP are small; these bounds stop abuse
# (giant payloads, zip-bomb-style source) well before the sandbox runs.
MAX_CODE_CHARS = 20_000          # ~500 lines of Python
MAX_TEXT_CHARS = 2_000           # free-text answers / predicted output
MAX_TEST_CASES = 50


class InputValidationError(ValueError):
    """Raised when user input violates a validation guard."""


def validate_code(code: str | None, *, field: str = "code", required: bool = True) -> str:
    """Validate a block of student code."""
    if code is None or code == "":
        if required:
            raise InputValidationError(f"'{field}' must not be empty.")
        return ""
    if not isinstance(code, str):
        raise InputValidationError(f"'{field}' must be a string.")
    if len(code) > MAX_CODE_CHARS:
        raise InputValidationError(
            f"'{field}' exceeds the {MAX_CODE_CHARS}-character limit."
        )
    # Reject NUL bytes (can break subprocess / parsing).
    if "\x00" in code:
        raise InputValidationError(f"'{field}' contains invalid NUL bytes.")
    return code


def validate_text(text: str | None, *, field: str = "text") -> str | None:
    """Validate a short free-text input (answer / predicted output)."""
    if text is None:
        return None
    if not isinstance(text, str):
        raise InputValidationError(f"'{field}' must be a string.")
    if len(text) > MAX_TEXT_CHARS:
        raise InputValidationError(
            f"'{field}' exceeds the {MAX_TEXT_CHARS}-character limit."
        )
    return text


def validate_test_case_count(count: int) -> None:
    """Guard against absurd numbers of test cases."""
    if count > MAX_TEST_CASES:
        raise InputValidationError(
            f"Too many test cases ({count} > {MAX_TEST_CASES})."
        )
