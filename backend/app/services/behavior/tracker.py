"""Behavior tracker.

Records a learning event (append-only) and folds it into the learner's
aggregated profile. This is where the two key insights from the brief live:

* **Repeated misconception detection** — the 2nd+ time the same misconception
  key appears under a concept, we increment ``repeated_misconception_events``,
  turning isolated mistakes into evidence of a persistent gap.

* **Intervention outcome** — we track hint -> correction, and a later *unaided*
  success after a correction, as improvement evidence that raises mastery.

The tracker never diagnoses misconceptions (Phase 3 owns that) and never calls
Gemini. It only aggregates behavior and recomputes the deterministic mastery
indicator.
"""

from __future__ import annotations

from app.models.behavior import (
    BehaviorEvent,
    BehaviorEventType,
    ConceptStat,
    EventRecordRequest,
    LearnerProfile,
    MasteryTrendPoint,
    _utcnow,
)
from app.services.behavior.mastery import compute_mastery

# Event types that count as an "attempt" at a concept.
_ATTEMPT_EVENTS = {
    BehaviorEventType.SUBMISSION,
    BehaviorEventType.CHALLENGE_ATTEMPT,
}
_ERROR_EVENTS = {
    BehaviorEventType.SYNTAX_ERROR,
    BehaviorEventType.RUNTIME_ERROR,
    BehaviorEventType.TEST_FAILURE,
}


class BehaviorTracker:
    """Applies events to a learner profile. Storage is injected."""

    def __init__(self, events_repo, profile_repo) -> None:
        self._events = events_repo
        self._profiles = profile_repo

    async def record(self, req: EventRecordRequest) -> LearnerProfile:
        """Append the raw event and update the aggregated profile."""
        event = BehaviorEvent(**req.model_dump())
        await self._events.append(event)

        profile = await self._profiles.get(req.user_id) or LearnerProfile(user_id=req.user_id)
        profile.total_events += 1

        if event.concept_key:
            stat = profile.concepts.get(event.concept_key) or ConceptStat(
                concept_key=event.concept_key
            )
            self._apply_event(stat, event)
            # Recompute the deterministic mastery indicator and snapshot a trend
            # point if it changed.
            new_mastery = compute_mastery(stat)
            if new_mastery != stat.mastery:
                stat.mastery = new_mastery
                stat.mastery_updated_at = _utcnow()
                profile.trend.append(
                    MasteryTrendPoint(concept_key=stat.concept_key, mastery=new_mastery)
                )
            profile.concepts[event.concept_key] = stat

        profile.updated_at = _utcnow()
        await self._profiles.save(profile)
        return profile

    def _apply_event(self, stat: ConceptStat, event: BehaviorEvent) -> None:
        et = event.event_type

        if et in _ATTEMPT_EVENTS:
            stat.attempts += 1
            if event.difficulty and event.payload.get("passed"):
                stat.last_difficulty_passed = event.difficulty

        if et == BehaviorEventType.SUCCESSFUL_EXECUTION:
            stat.successful_attempts += 1
            # Improvement evidence: an unaided success that follows a prior
            # correction and was NOT immediately preceded by a hint request.
            if stat.corrections > 0 and not event.payload.get("used_hint", False):
                stat.unaided_successes_after_correction += 1

        if et in _ERROR_EVENTS:
            stat.error_count += 1
            if event.error_type:
                stat.error_type_counts[event.error_type] = (
                    stat.error_type_counts.get(event.error_type, 0) + 1
                )

        if et == BehaviorEventType.MISCONCEPTION_DETECTED and event.misconception_key:
            prior = stat.misconception_counts.get(event.misconception_key, 0)
            stat.misconception_counts[event.misconception_key] = prior + 1
            # 2nd and later occurrences => persistent gap evidence.
            if prior >= 1:
                stat.repeated_misconception_events += 1

        if et == BehaviorEventType.HINT_REQUESTED:
            stat.hints_requested += 1

        if et == BehaviorEventType.HINT_LEVEL_REACHED and event.hint_level:
            stat.max_hint_level_reached = max(stat.max_hint_level_reached, event.hint_level)

        if et == BehaviorEventType.SUCCESSFUL_CORRECTION:
            stat.corrections += 1
            # If a hint was reached before correcting, it was a hint-assisted fix.
            if stat.max_hint_level_reached > 0 or event.payload.get("after_hint"):
                stat.corrections_after_hint += 1
