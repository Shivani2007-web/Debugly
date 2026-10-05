"""Engine aggregation and reporting-policy tests."""

from app.services.misconception.engine import (
    CONFIDENCE_CAP,
    _aggregate_confidence,
)
from app.models.misconception import Evidence, EvidenceSource, EvidenceWeight
from tests.helpers import diagnose_code


def _ev(source, weight):
    return Evidence(source=source, weight=weight, detail="x")


def test_confidence_is_capped():
    many_strong = [_ev(EvidenceSource.CODE, EvidenceWeight.STRONG) for _ in range(10)]
    assert _aggregate_confidence(many_strong) <= CONFIDENCE_CAP


def test_corroboration_bonus_applies_across_sources():
    code_only = [_ev(EvidenceSource.CODE, EvidenceWeight.MEDIUM)]
    mixed = [
        _ev(EvidenceSource.CODE, EvidenceWeight.MEDIUM),
        _ev(EvidenceSource.ERROR, EvidenceWeight.MEDIUM),
    ]
    assert _aggregate_confidence(mixed) > _aggregate_confidence(code_only)


def test_clean_correct_code_yields_no_misconceptions():
    code = (
        "def sum_list(numbers):\n"
        "    total = 0\n"
        "    for n in numbers:\n"
        "        total += n\n"
        "    return total\n"
    )
    result = diagnose_code(code)
    assert result.misconceptions == []


def test_syntax_error_code_does_not_crash_engine():
    code = "def f(:\n    return 1\n"
    result = diagnose_code(code)
    # Should return cleanly (no structural rules can run), not raise.
    assert isinstance(result.misconceptions, list)


def test_verdicts_are_ranked_by_confidence():
    # Code with two issues; ensure sorted descending by confidence.
    code = (
        "def f(xs):\n"
        "    for i in range(len(xs) + 1):\n"  # off-by-one (STRONG)
        "        print(xs[i])\n"              # prints, no return (missing_return)
    )
    result = diagnose_code(code)
    confidences = [m.confidence for m in result.misconceptions]
    assert confidences == sorted(confidences, reverse=True)
