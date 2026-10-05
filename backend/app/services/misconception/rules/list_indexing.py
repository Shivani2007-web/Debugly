"""List indexing confusion (length vs last valid index)."""

from __future__ import annotations

from app.models.misconception import Evidence, EvidenceWeight
from app.services.analysis.feature_extractor import Features
from app.services.misconception.base import Rule, code_evidence, error_evidence
from app.services.misconception.registry import register


@register
class ListIndexingRule(Rule):
    key = "list_indexing"

    def evaluate(self, features: Features) -> list[Evidence]:
        evidence: list[Evidence] = []

        # Code: x[len(x)] — using the length directly as an index is always
        # one past the end. Strong structural signal.
        for ix in features.code.index_exprs:
            if ix.uses_len_as_index:
                evidence.append(
                    code_evidence(
                        f"Indexing with the length itself: {ix.src} is one past "
                        "the last valid index (len - 1).",
                        EvidenceWeight.STRONG,
                        line=ix.line,
                    )
                )

        # Error: IndexError with an index expression present but no obvious
        # loop-range overshoot (that case is off-by-one's territory). Medium so
        # it needs the structural signal or repetition to report.
        if (
            "IndexError" in features.error.error_type_counts
            and features.code.index_exprs
            and not any(r.len_plus_offset for r in features.code.for_ranges)
        ):
            evidence.append(
                error_evidence(
                    "IndexError while subscripting a list.",
                    EvidenceWeight.MEDIUM,
                    error_type="IndexError",
                    line=features.error.primary_error_line,
                )
            )

        return evidence
