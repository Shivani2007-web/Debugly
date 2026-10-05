"""Missing or incorrect return value misconception."""

from __future__ import annotations

from app.models.misconception import Evidence, EvidenceWeight
from app.services.analysis.feature_extractor import Features
from app.services.misconception.base import Rule, code_evidence
from app.services.misconception.registry import register


@register
class MissingReturnRule(Rule):
    key = "missing_return"

    def evaluate(self, features: Features) -> list[Evidence]:
        evidence: list[Evidence] = []

        for fn in features.code.functions:
            # Function prints a value but never returns one — a very common
            # "it shows the answer so it must work" misconception.
            if fn.prints and not fn.has_return_value:
                evidence.append(
                    code_evidence(
                        f"Function '{fn.name}' prints but never returns a value; "
                        "callers get None.",
                        EvidenceWeight.STRONG,
                        line=fn.line,
                    )
                )
            # Function computes nothing to return and has no return at all,
            # while clearly doing work (has local assignments). Medium: could
            # legitimately be a procedure, so needs the threshold.
            elif (
                not fn.has_return_value
                and not fn.has_bare_return
                and not fn.prints
                and fn.assigned_names
                and fn.name not in {"main", "setup", "__init__"}
            ):
                evidence.append(
                    code_evidence(
                        f"Function '{fn.name}' computes values but has no return "
                        "statement.",
                        EvidenceWeight.MEDIUM,
                        line=fn.line,
                    )
                )

        return evidence
