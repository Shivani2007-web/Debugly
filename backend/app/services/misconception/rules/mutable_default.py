"""Mutable vs immutable misunderstanding (mutable default argument)."""

from __future__ import annotations

from app.models.misconception import Evidence, EvidenceWeight
from app.services.analysis.feature_extractor import Features
from app.services.misconception.base import Rule, code_evidence
from app.services.misconception.registry import register


@register
class MutableDefaultRule(Rule):
    key = "mutable_default"

    def evaluate(self, features: Features) -> list[Evidence]:
        evidence: list[Evidence] = []

        for fn in features.code.functions:
            for arg in fn.mutable_default_args:
                evidence.append(
                    code_evidence(
                        f"Parameter '{arg}' of '{fn.name}' has a mutable default "
                        "(e.g. []/{}); it is shared across calls and persists "
                        "between them.",
                        EvidenceWeight.STRONG,
                        line=fn.line,
                    )
                )

        return evidence
