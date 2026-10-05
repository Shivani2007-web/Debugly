"""Deterministic Debugly Mastery Indicator.

A transparent, reproducible 0-100 score derived purely from measurable learning
signals. It is explicitly an *indicator*, not a scientifically validated
probability of mastery. Gemini is never involved in computing it.

Signals (all from aggregated :class:`ConceptStat`):
  + success rate            successful_attempts / attempts
  + corrections             the learner fixed their own mistakes
  + improvement             unaided successes after a prior correction
  + difficulty progression  passing harder challenges
  - repeated misconceptions a persistent gap drags the score down more than a
                            one-off error
  - hint dependency         needing many hints per attempt lowers the score

The formula is intentionally simple and bounded. Each component is clamped so
no single signal dominates, and the result is rounded to one decimal.
"""

from __future__ import annotations

from app.models.behavior import ConceptStat

_DIFFICULTY_WEIGHT = {
    "beginner": 0.4,
    "developing": 0.6,
    "intermediate": 0.8,
    "advanced": 1.0,
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def compute_mastery(stat: ConceptStat) -> float:
    """Return the Debugly Mastery Indicator (0-100) for one concept.

    A learner with no attempts has mastery 0 (unknown / not yet demonstrated).
    """
    if stat.attempts == 0:
        return 0.0

    # Base competence: how often attempts succeed (0..1).
    success_rate = _clamp(stat.successful_attempts / stat.attempts)

    # Reward self-correction: fixing your own mistakes shows learning. Scaled
    # by attempts so a single lucky correction doesn't spike the score.
    correction_credit = _clamp(stat.corrections / max(stat.attempts, 1)) * 0.5

    # Reward durable improvement: succeeding WITHOUT hints after an earlier
    # correction is the strongest positive signal.
    improvement_credit = _clamp(stat.unaided_successes_after_correction / 3.0) * 1.0

    # Penalise repeated misconceptions (persistent gap). The 2nd+ occurrence of
    # the same misconception is what counts here. The penalty DECAYS as the
    # learner demonstrates recovery (unaided successes after a correction), so a
    # student who genuinely improves is not punished forever by old mistakes.
    recovery = _clamp(stat.unaided_successes_after_correction / 4.0)  # 0..1
    effective_repeats = stat.repeated_misconception_events * (1.0 - 0.75 * recovery)
    repeat_penalty = _clamp(effective_repeats / 4.0) * 0.6

    # Penalise hint dependency: many hints per attempt means shallow grasp.
    hint_dependency = stat.hints_requested / max(stat.attempts, 1)
    hint_penalty = _clamp(hint_dependency / 3.0) * 0.4

    # Difficulty bonus: passing harder material lifts the ceiling.
    difficulty_bonus = _DIFFICULTY_WEIGHT.get(stat.last_difficulty_passed or "", 0.0) * 0.15

    raw = (
        success_rate * 0.6
        + correction_credit
        + improvement_credit * 0.25
        + difficulty_bonus
        - repeat_penalty
        - hint_penalty
    )

    return round(_clamp(raw) * 100.0, 1)


def hint_dependency_ratio(stat: ConceptStat) -> float:
    """hints_requested / attempts (0 when no attempts)."""
    if stat.attempts == 0:
        return 0.0
    return round(stat.hints_requested / stat.attempts, 3)
