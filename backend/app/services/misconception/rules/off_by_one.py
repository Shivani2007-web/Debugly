"""Off-by-one / loop boundary misconception."""

from __future__ import annotations

from app.models.misconception import Evidence, EvidenceWeight
from app.services.analysis.feature_extractor import Features
from app.services.misconception.base import Rule, code_evidence, error_evidence
from app.services.misconception.registry import register


@register
class OffByOneRule(Rule):
    key = "off_by_one"

    def evaluate(self, features: Features) -> list[Evidence]:
        evidence: list[Evidence] = []

        # Code: range(len(x) + 1) or range(len(x) - 1) in a for header — the
        # classic boundary error. +1 overshoots (IndexError), -1 undershoots.
        for rc in features.code.for_ranges:
            if rc.len_plus_offset and rc.offset == 1:
                evidence.append(
                    code_evidence(
                        f"Loop uses range(len(...) + 1), which iterates one index "
                        f"past the end: {', '.join(rc.args_src)}",
                        EvidenceWeight.STRONG,
                        line=rc.line,
                    )
                )
            elif rc.len_plus_offset and rc.offset == -1:
                evidence.append(
                    code_evidence(
                        "Loop uses range(len(...) - 1), which stops one short of "
                        "the last element.",
                        EvidenceWeight.MEDIUM,
                        line=rc.line,
                    )
                )

        # Error: an IndexError strongly corroborates an overshoot.
        if "IndexError" in features.error.error_type_counts:
            # Only treat as off-by-one evidence when there is also a loop/index
            # structure to attach it to (avoid grabbing every IndexError).
            if features.code.for_ranges or features.code.index_exprs:
                count = features.error.error_type_counts["IndexError"]
                weight = EvidenceWeight.MEDIUM if count == 1 else EvidenceWeight.STRONG
                evidence.append(
                    error_evidence(
                        f"IndexError raised ({count}x) while indexing inside a loop.",
                        weight,
                        error_type="IndexError",
                        line=features.error.primary_error_line,
                    )
                )

        return evidence
