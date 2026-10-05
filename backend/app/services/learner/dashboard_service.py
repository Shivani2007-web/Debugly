"""Student dashboard composition (read-only).

Composes the dashboard from EXISTING services:
* mastery, concepts, misconceptions, trend, recent events -> Phase 5 ProfileService
* recommended challenge target -> Phase 6 ChallengeService.preview_target (no gen)

No mastery, misconception, or selection logic is computed here. If the learner
has no history, a clean "new learner" dashboard is returned.
"""

from __future__ import annotations

from app.models.dashboard import (
    Bottleneck,
    ConceptProgress,
    DashboardResponse,
    OverallMastery,
    RecommendedChallenge,
    band_for,
)
from app.services.behavior.profile_service import ProfileService
from app.services.challenge.service import ChallengeService
from app.services.learner.timeline import to_timeline


class DashboardService:
    def __init__(self, profile_service: ProfileService, challenge_service: ChallengeService) -> None:
        self._profiles = profile_service
        self._challenges = challenge_service

    async def build(self, user_id: str, *, timeline_limit: int = 25) -> DashboardResponse:
        summary = await self._profiles.summary(user_id)
        trend = await self._profiles.mastery_trend(user_id)
        misconceptions = await self._profiles.recent_misconceptions(user_id)
        events = await self._profiles.recent_events(user_id, limit=timeline_limit)
        profile = await self._profiles._profile(user_id)  # for recovery evidence

        # Section A — overall indicator (value straight from Phase 5).
        overall = OverallMastery(
            indicator=summary.overall_mastery,
            band=band_for(summary.overall_mastery, 1 if not summary.is_new_learner else 0),
            trend=trend,
        )

        # Section B — per-concept progress with presentational band + mini-trend.
        concepts: list[ConceptProgress] = []
        for c in summary.concepts:
            concept_trend = [p.mastery for p in trend if p.concept_key == c.concept_key]
            concepts.append(
                ConceptProgress(
                    concept_key=c.concept_key,
                    mastery=c.mastery,
                    band=band_for(c.mastery, c.attempts),
                    attempts=c.attempts,
                    successful_attempts=c.successful_attempts,
                    has_persistent_gap=c.has_persistent_gap,
                    hint_dependency=c.hint_dependency,
                    trend=concept_trend,
                )
            )

        # Section C — bottlenecks (persistent gaps + weakest first).
        bottlenecks = self._bottlenecks(summary, misconceptions, profile)

        # Section D — meaningful event timeline (no keystrokes).
        timeline = [to_timeline(e) for e in events]

        # Section E — recommended next challenge (Phase 6 selector, read-only).
        preview = await self._challenges.preview_target(user_id)
        if preview is None:
            recommended = RecommendedChallenge(available=False)
        else:
            recommended = RecommendedChallenge(available=True, **preview)

        return DashboardResponse(
            user_id=user_id,
            is_new_learner=summary.is_new_learner,
            overall=overall,
            concepts=concepts,
            bottlenecks=bottlenecks,
            timeline=timeline,
            recommended_challenge=recommended,
        )

    def _bottlenecks(self, summary, misconceptions, profile) -> list[Bottleneck]:
        """Build bottleneck rows from existing misconception + profile data."""
        mastery_by_concept = {c.concept_key: c.mastery for c in summary.concepts}
        hint_dep_by_concept = {c.concept_key: c.hint_dependency for c in summary.concepts}

        rows: list[Bottleneck] = []
        for m in misconceptions:
            stat = profile.concepts.get(m.concept_key) if profile else None
            recovery = stat.unaided_successes_after_correction if stat else 0
            rows.append(
                Bottleneck(
                    concept_key=m.concept_key,
                    misconception_key=m.misconception_key,
                    occurrences=m.occurrences,
                    persistent=m.persistent,
                    hint_dependency=hint_dep_by_concept.get(m.concept_key, 0.0),
                    recovery_successes=recovery,
                    concept_mastery=mastery_by_concept.get(m.concept_key, 0.0),
                )
            )

        # Persistent gaps first, then by lowest concept mastery, then by
        # most occurrences — visually surfacing the biggest blockers.
        rows.sort(key=lambda b: (not b.persistent, b.concept_mastery, -b.occurrences))
        return rows
