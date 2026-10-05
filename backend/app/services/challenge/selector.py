"""Deterministic challenge-target selection.

Chooses WHICH concept (and misconception) the learner should practice, from
their Phase 5 profile, in priority order:

  1. Persistent misconceptions (a recurring conceptual gap)
  2. Concepts with low mastery
  3. Concepts showing recent struggle (recent errors / failed attempts)
  4. Concepts needing repeated hints (high hint dependency)

Mastered concepts (high mastery, no gap) are skipped unless they are the only
option or explicitly requested for reinforcement. Gemini is not involved.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.behavior import ConceptStat, LearnerProfile
from app.services.misconception import concepts as concept_catalog

# A concept at/above this mastery with no persistent gap is "mastered".
MASTERED_THRESHOLD = 80.0


@dataclass
class SelectionResult:
    concept_key: str
    concept_name: str
    misconception_key: str | None
    misconception_name: str | None
    stat: ConceptStat | None
    reason: str


def _hint_dependency(stat: ConceptStat) -> float:
    return stat.hints_requested / max(stat.attempts, 1)


def _dominant_misconception(stat: ConceptStat) -> str | None:
    """The most-seen misconception under a concept, if any."""
    if not stat.misconception_counts:
        return None
    return max(stat.misconception_counts.items(), key=lambda kv: kv[1])[0]


def _concept_name(concept_key: str, stat: ConceptStat | None) -> str:
    # Prefer a catalog display name via the dominant misconception's concept.
    if stat is not None:
        mkey = _dominant_misconception(stat)
        if mkey and mkey in concept_catalog.CATALOG:
            return concept_catalog.CATALOG[mkey].concept
    return concept_key.replace("_", " ").title()


def _misconception_name(mkey: str | None) -> str | None:
    if mkey and mkey in concept_catalog.CATALOG:
        return concept_catalog.CATALOG[mkey].name
    return None


def _score(stat: ConceptStat) -> tuple:
    """Priority sort key (higher = more in need of practice).

    Ordered tuple: (persistent_gap, low_mastery, struggle, hint_dependency).
    """
    persistent = 1 if stat.has_persistent_gap else 0
    low_mastery = max(0.0, (100.0 - stat.mastery)) / 100.0
    struggle = stat.error_count / max(stat.attempts, 1) if stat.attempts else 0.0
    hint_dep = _hint_dependency(stat)
    return (persistent, round(low_mastery, 3), round(struggle, 3), round(hint_dep, 3))


def select_target(
    profile: LearnerProfile | None,
    *,
    preferred_concept: str | None = None,
) -> SelectionResult | None:
    """Pick the concept+misconception to target, or None for a clean learner."""
    if profile is None or not profile.concepts:
        return None

    # Explicit reinforcement request wins if the concept exists.
    if preferred_concept and preferred_concept in profile.concepts:
        stat = profile.concepts[preferred_concept]
        mkey = _dominant_misconception(stat)
        return SelectionResult(
            concept_key=preferred_concept,
            concept_name=_concept_name(preferred_concept, stat),
            misconception_key=mkey,
            misconception_name=_misconception_name(mkey),
            stat=stat,
            reason="reinforcement (explicitly requested)",
        )

    stats = list(profile.concepts.values())

    # Candidates: anything not yet mastered. If everything is mastered, fall
    # back to reinforcing the weakest (so we still produce a challenge).
    not_mastered = [
        s for s in stats
        if s.has_persistent_gap or s.mastery < MASTERED_THRESHOLD or s.attempts == 0
    ]
    candidates = not_mastered or stats

    best = max(candidates, key=_score)
    mkey = _dominant_misconception(best)

    if best.has_persistent_gap:
        reason = "persistent misconception"
    elif best.mastery < 55.0:
        reason = "low mastery"
    elif best.error_count > best.successful_attempts:
        reason = "recent struggle"
    elif _hint_dependency(best) > 0.75:
        reason = "high hint dependency"
    elif not not_mastered:
        reason = "reinforcement (all concepts mastered)"
    else:
        reason = "needs practice"

    return SelectionResult(
        concept_key=best.concept_key,
        concept_name=_concept_name(best.concept_key, best),
        misconception_key=mkey,
        misconception_name=_misconception_name(mkey),
        stat=best,
        reason=reason,
    )
