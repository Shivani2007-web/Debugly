"""Function parameter / argument confusion."""

from __future__ import annotations

from app.models.misconception import Evidence, EvidenceWeight
from app.services.analysis.feature_extractor import Features
from app.services.misconception.base import Rule, code_evidence, error_evidence
from app.services.misconception.registry import register


@register
class FunctionParameterRule(Rule):
    key = "function_parameter"

    def evaluate(self, features: Features) -> list[Evidence]:
        evidence: list[Evidence] = []

        # Build a map of locally-defined function arities.
        local_defs = {fn.name: fn for fn in features.code.functions}

        for call in features.code.calls:
            fn = local_defs.get(call.func_name)
            if fn is None or call.has_starargs:
                continue
            # Compare positional count against the definition's arity. We only
            # flag a clear mismatch (ignoring default-arg nuance would create
            # false positives, so require the call to pass MORE than defined or
            # fewer than the count of non-defaulted params is hard to know here;
            # we conservatively flag a strict count mismatch).
            if call.positional_count != len(fn.args):
                evidence.append(
                    code_evidence(
                        f"Call to '{call.func_name}' passes "
                        f"{call.positional_count} argument(s) but it is defined "
                        f"with {len(fn.args)} parameter(s).",
                        EvidenceWeight.MEDIUM,
                        line=call.line,
                    )
                )

        # Error corroboration: a TypeError mentioning arguments is a strong
        # runtime confirmation.
        if "TypeError" in features.error.error_type_counts:
            msg = (features.error.primary_error_message or "").lower()
            if "argument" in msg or "positional" in msg:
                evidence.append(
                    error_evidence(
                        "TypeError about arguments — the call does not match the "
                        "function's parameters.",
                        EvidenceWeight.STRONG,
                        error_type="TypeError",
                        line=features.error.primary_error_line,
                    )
                )

        return evidence
