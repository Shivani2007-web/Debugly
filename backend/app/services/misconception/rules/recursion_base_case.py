"""Recursion / base-case misunderstanding."""

from __future__ import annotations

from app.models.misconception import Evidence, EvidenceWeight
from app.services.analysis.feature_extractor import Features
from app.services.misconception.base import Rule, code_evidence, error_evidence
from app.services.misconception.registry import register


@register
class RecursionBaseCaseRule(Rule):
    key = "recursion_base_case"

    def evaluate(self, features: Features) -> list[Evidence]:
        evidence: list[Evidence] = []

        for fn in features.code.functions:
            if not fn.is_recursive:
                continue
            # Recursive function with no conditional return => no base case to
            # stop the recursion. Strong structural signal.
            if not fn.has_conditional_return:
                evidence.append(
                    code_evidence(
                        f"Recursive function '{fn.name}' has no conditional "
                        "return (base case); it will recurse without stopping.",
                        EvidenceWeight.STRONG,
                        line=fn.line,
                    )
                )

        # Error corroboration: RecursionError.
        if "RecursionError" in features.error.error_type_counts and any(
            fn.is_recursive for fn in features.code.functions
        ):
            evidence.append(
                error_evidence(
                    "RecursionError raised — recursion did not terminate.",
                    EvidenceWeight.STRONG,
                    error_type="RecursionError",
                    line=features.error.primary_error_line,
                )
            )

        return evidence
