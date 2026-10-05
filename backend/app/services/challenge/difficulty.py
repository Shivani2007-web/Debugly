"""Deterministic difficulty selection.

Difficulty is derived from the Debugly Mastery Indicator plus behavioral
signals — NEVER by Gemini. Mastery sets the base band; hint dependency and a
persistent gap pull it down; a clean record pulls it up.

    mastery band:   <35 beginner | 35-59 developing | 60-84 intermediate | 85+ advanced

Adjustments (bounded to +/-1 step):
  - high hint dependency (>1 hint/attempt)     -> step down
  - persistent gap on the concept              -> step down (cap at developing)
  - strong success + low hint dependency       -> step up

Also exposes next-difficulty helpers for the adaptive loop:
  * harder() when the student consistently succeeds with little help
  * easier() when the student repeatedly fails or needs heavy intervention
"""

from __future__ import annotations

from app.models.behavior import ConceptStat
from app.models.challenge import DIFFICULTY_ORDER, Difficulty


def _band_from_mastery(mastery: float) -> Difficulty:
    if mastery >= 85:
        return Difficulty.ADVANCED
    if mastery >= 60:
        return Difficulty.INTERMEDIATE
    if mastery >= 35:
        return Difficulty.DEVELOPING
    return Difficulty.BEGINNER


def _step(difficulty: Difficulty, delta: int) -> Difficulty:
    idx = DIFFICULTY_ORDER.index(difficulty)
    idx = max(0, min(len(DIFFICULTY_ORDER) - 1, idx + delta))
    return DIFFICULTY_ORDER[idx]


def select_difficulty(stat: ConceptStat | None) -> Difficulty:
    """Choose a difficulty for the learner's current state on a concept."""
    if stat is None or stat.attempts == 0:
        # Unknown learner / concept: start gently.
        return Difficulty.BEGINNER

    band = _band_from_mastery(stat.mastery)
    hint_dependency = stat.hints_requested / max(stat.attempts, 1)
    success_rate = stat.successful_attempts / max(stat.attempts, 1)

    # Pull down for heavy reliance on hints or a persistent gap.
    if hint_dependency > 1.0 or stat.has_persistent_gap:
        band = _step(band, -1)
        if stat.has_persistent_gap:
            # Never push a persistent-gap concept above developing.
            idx = DIFFICULTY_ORDER.index(band)
            cap = DIFFICULTY_ORDER.index(Difficulty.DEVELOPING)
            band = DIFFICULTY_ORDER[min(idx, cap)]

    # Push up for strong, independent performance.
    elif success_rate >= 0.8 and hint_dependency <= 0.3 and stat.attempts >= 2:
        band = _step(band, 1)

    return band


def harder(current: Difficulty) -> Difficulty:
    """Next step up (for consistent success)."""
    return _step(current, 1)


def easier(current: Difficulty) -> Difficulty:
    """Next step down (for repeated failure / heavy intervention)."""
    return _step(current, -1)


def adjust_after_result(current: Difficulty, *, passed: bool, hints_used: int) -> Difficulty:
    """Deterministically adjust difficulty after a single challenge result.

    * Pass with no/low hints   -> harder.
    * Fail, or pass needing many hints -> easier.
    * Otherwise unchanged.
    """
    if passed and hints_used <= 1:
        return harder(current)
    if not passed or hints_used >= 3:
        return easier(current)
    return current
