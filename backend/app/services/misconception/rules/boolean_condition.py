"""Incorrect boolean condition misconception."""

from __future__ import annotations

from app.models.misconception import Evidence, EvidenceWeight
from app.services.analysis.feature_extractor import Features
from app.services.misconception.base import Rule, code_evidence
from app.services.misconception.registry import register


@register
class BooleanConditionRule(Rule):
    key = "boolean_condition"

    def evaluate(self, features: Features) -> list[Evidence]:
        evidence: list[Evidence] = []

        for line, description in features.code.boolean_antipatterns:
            # Both patterns captured (bare-value `or`, and `is` for value
            # comparison) are concrete mistakes, so MEDIUM — enough to report
            # on its own but not overstated.
            evidence.append(
                code_evidence(description, EvidenceWeight.MEDIUM, line=line)
            )

        return evidence
