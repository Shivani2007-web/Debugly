"""Infinite loop / missing progress misconception."""

from __future__ import annotations

from app.models.misconception import Evidence, EvidenceWeight
from app.services.analysis.feature_extractor import Features
from app.services.misconception.base import Rule, code_evidence, error_evidence
from app.services.misconception.registry import register


@register
class InfiniteLoopRule(Rule):
    key = "infinite_loop"

    def evaluate(self, features: Features) -> list[Evidence]:
        evidence: list[Evidence] = []

        for wl in features.code.while_loops:
            # `while True` with no break is a strong structural signal.
            if wl.is_literal_true and not wl.has_break:
                evidence.append(
                    code_evidence(
                        "`while True` loop with no break — the loop can never "
                        "exit on its own.",
                        EvidenceWeight.STRONG,
                        line=wl.line,
                    )
                )
            # A condition on names that are never reassigned in the body means
            # the loop variable never advances toward the exit condition.
            elif wl.test_names and not (wl.test_names & wl.body_assigned_names) and not wl.has_break:
                evidence.append(
                    code_evidence(
                        f"while loop tests {sorted(wl.test_names)} but none of "
                        "those variables are updated in the body — no progress "
                        "toward termination.",
                        EvidenceWeight.MEDIUM,
                        line=wl.line,
                    )
                )

        # Error: an actual timeout corroborates non-termination, but only when
        # the code even has a loop (avoid blaming slow non-loop code).
        if features.error.timed_out and features.code.while_loops:
            evidence.append(
                error_evidence(
                    "Execution timed out, consistent with a loop that never ends.",
                    EvidenceWeight.MEDIUM,
                    error_type="TimeoutError",
                    line=None,
                )
            )

        return evidence
