"""Rule interface and evidence helpers.

Each misconception is a :class:`Rule` subclass that inspects a
:class:`Features` object and returns zero or more :class:`Evidence` items. A
rule emits evidence; it does NOT decide confidence — the engine aggregates
evidence across a rule into a capped confidence score. This keeps the
"no single weak signal" policy in one place (the engine) rather than scattered
across rules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.misconception import Evidence, EvidenceSource, EvidenceWeight
from app.services.analysis.feature_extractor import Features


class Rule(ABC):
    """Base class for a misconception detection rule."""

    #: Stable misconception key; must exist in the concept CATALOG.
    key: str = ""

    @abstractmethod
    def evaluate(self, features: Features) -> list[Evidence]:
        """Return evidence supporting this misconception (possibly empty)."""
        raise NotImplementedError


# ---- small evidence constructors for readable rules ----

def code_evidence(
    detail: str, weight: EvidenceWeight, line: int | None = None
) -> Evidence:
    return Evidence(
        source=EvidenceSource.CODE, weight=weight, detail=detail, line=line
    )


def error_evidence(
    detail: str,
    weight: EvidenceWeight,
    error_type: str | None = None,
    line: int | None = None,
) -> Evidence:
    return Evidence(
        source=EvidenceSource.ERROR,
        weight=weight,
        detail=detail,
        line=line,
        error_type=error_type,
    )
