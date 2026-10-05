"""Misconception engine.

Runs every registered rule against the extracted features, aggregates each
rule's evidence into a bounded confidence score, applies the reporting policy,
and returns ranked verdicts.

Confidence aggregation (deterministic, diminishing returns):

    conf = 1 - prod(1 - w_i)   for each evidence weight w_i

then capped at CONFIDENCE_CAP so the system never claims near-certainty.

Reporting policy ("do not diagnose on a single weak signal"):

* A verdict is reported only if its aggregated confidence >= REPORT_THRESHOLD.
* With exactly one piece of evidence, that evidence must be MEDIUM or stronger
  (a lone WEAK signal is suppressed regardless of arithmetic).
* Multiple independent evidence sources (code + error) get a small
  corroboration bonus before the cap.
"""

from __future__ import annotations

import importlib
import pkgutil

from app.models.misconception import (
    DetectedMisconception,
    DiagnosisResult,
    Evidence,
    EvidenceSource,
    EvidenceWeight,
)
from app.services.analysis.feature_extractor import Features, extract_features
from app.models.execution import ExecutionResult
from app.services.misconception import concepts
from app.services.misconception.registry import all_rules

CONFIDENCE_CAP = 0.95
REPORT_THRESHOLD = 0.4
CORROBORATION_BONUS = 0.08  # applied once when >1 evidence source present


def _load_rules_once() -> None:
    """Import every module in the rules package so decorators run."""
    from app.services.misconception import rules as rules_pkg

    for mod in pkgutil.iter_modules(rules_pkg.__path__):
        importlib.import_module(f"{rules_pkg.__name__}.{mod.name}")


_RULES_LOADED = False


def _ensure_rules() -> None:
    global _RULES_LOADED
    if not _RULES_LOADED:
        _load_rules_once()
        _RULES_LOADED = True


def _aggregate_confidence(evidence: list[Evidence]) -> float:
    """Combine evidence weights with diminishing returns, plus corroboration."""
    product = 1.0
    for ev in evidence:
        product *= 1.0 - float(ev.weight.value)
    conf = 1.0 - product

    sources = {ev.source for ev in evidence}
    if len(sources) > 1:
        conf = min(1.0, conf + CORROBORATION_BONUS)

    return min(conf, CONFIDENCE_CAP)


def _passes_policy(evidence: list[Evidence], confidence: float) -> bool:
    """Apply the 'no single weak signal' reporting policy."""
    if not evidence:
        return False
    if len(evidence) == 1 and evidence[0].weight == EvidenceWeight.WEAK:
        return False
    return confidence >= REPORT_THRESHOLD


def diagnose_features(features: Features) -> DiagnosisResult:
    """Run all rules against pre-extracted features."""
    _ensure_rules()

    verdicts: list[DetectedMisconception] = []
    for rule in all_rules():
        evidence = rule.evaluate(features)
        if not evidence:
            continue

        confidence = _aggregate_confidence(evidence)
        if not _passes_policy(evidence, confidence):
            continue

        definition = concepts.get_def(rule.key)
        lines = sorted({ev.line for ev in evidence if ev.line is not None})
        error_type = next(
            (ev.error_type for ev in evidence if ev.error_type), None
        )

        # Gentle tie-break: if the task targets this concept, nudge confidence.
        if features.target_concepts and _concept_matches(
            definition.concept, features.target_concepts
        ):
            confidence = min(CONFIDENCE_CAP, confidence + 0.03)

        verdicts.append(
            DetectedMisconception(
                concept=definition.concept,
                misconception_key=definition.key,
                misconception=definition.name,
                confidence=round(confidence, 2),
                evidence=evidence,
                lines=lines,
                error_type=error_type,
            )
        )

    verdicts.sort(key=lambda v: v.confidence, reverse=True)

    return DiagnosisResult(
        misconceptions=verdicts,
        analyzed_lines=features.code.total_lines,
        had_execution_evidence=features.error.had_execution,
    )


def _concept_matches(concept: str, target_concepts: list[str]) -> bool:
    """Loose match between a display concept and task concept keys."""
    normalized = concept.lower().replace(" ", "_")
    return any(normalized in t.lower() or t.lower() in normalized for t in target_concepts)


def diagnose(
    code: str,
    execution_result: ExecutionResult | None = None,
    target_concepts: list[str] | None = None,
) -> DiagnosisResult:
    """Convenience entry point: extract features then diagnose."""
    features = extract_features(code, execution_result, target_concepts)
    return diagnose_features(features)
