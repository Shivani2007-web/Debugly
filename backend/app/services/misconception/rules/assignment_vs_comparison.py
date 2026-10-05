"""Assignment vs comparison confusion."""

from __future__ import annotations

from app.models.misconception import Evidence, EvidenceWeight
from app.services.analysis.feature_extractor import Features
from app.services.misconception.base import Rule, code_evidence
from app.services.misconception.registry import register


@register
class AssignmentVsComparisonRule(Rule):
    key = "assignment_vs_comparison"

    def evaluate(self, features: Features) -> list[Evidence]:
        evidence: list[Evidence] = []

        # A comparison used as a bare statement, e.g. a line that is just
        # `x == 5`, usually means the student meant to assign (`x = 5`) or the
        # comparison result is being discarded. Medium structural signal.
        for line in features.code.comparison_as_statement:
            evidence.append(
                code_evidence(
                    "A comparison (`==`) is used as a standalone statement; its "
                    "result is discarded — did you mean to assign (`=`)?",
                    EvidenceWeight.MEDIUM,
                    line=line,
                )
            )

        return evidence
