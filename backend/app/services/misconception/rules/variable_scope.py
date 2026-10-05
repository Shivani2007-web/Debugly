"""Variable scope confusion."""

from __future__ import annotations

from app.models.misconception import Evidence, EvidenceWeight
from app.services.analysis.feature_extractor import Features
from app.services.misconception.base import Rule, code_evidence, error_evidence
from app.services.misconception.registry import register


@register
class VariableScopeRule(Rule):
    key = "variable_scope"

    def evaluate(self, features: Features) -> list[Evidence]:
        evidence: list[Evidence] = []

        # Error channel first: a NameError is the clearest runtime confirmation
        # of using a name outside its scope / before definition.
        if "NameError" in features.error.error_type_counts:
            evidence.append(
                error_evidence(
                    "NameError — a variable is used where it is not defined "
                    "(wrong scope or used before assignment).",
                    EvidenceWeight.MEDIUM,
                    error_type="NameError",
                    line=features.error.primary_error_line,
                )
            )

        # Code channel: a name read inside a function that is never defined
        # there, isn't a parameter, builtin, or known function. Weak on its own
        # (could be an intended global), so it only reports when corroborated.
        for name, line in features.code.undefined_name_reads.items():
            evidence.append(
                code_evidence(
                    f"Name '{name}' is read inside a function but never defined "
                    "in that scope.",
                    EvidenceWeight.WEAK,
                    line=line,
                )
            )

        return evidence
