"""Learner profile read service.

Pure read-side projections over the aggregated profile and the raw event log:
summary, per-concept mastery, recent misconceptions, recent events, mastery
trends, and recommended areas for improvement. No mutation here.
"""

from __future__ import annotations

from app.models.behavior import (
    BehaviorEvent,
    ConceptMastery,
    LearnerProfile,
    LearnerSummary,
    MasteryTrendPoint,
    RecentMisconception,
    Recommendation,
)
from app.services.behavior.mastery import hint_dependency_ratio

# Mastery below this is treated as "needs work" for recommendations.
_WEAK_THRESHOLD = 55.0


class ProfileService:
    def __init__(self, events_repo, profile_repo) -> None:
        self._events = events_repo
        self._profiles = profile_repo

    async def _profile(self, user_id: str) -> LearnerProfile | None:
        return await self._profiles.get(user_id)

    async def summary(self, user_id: str) -> LearnerSummary:
        profile = await self._profile(user_id)
        if profile is None or not profile.concepts:
            # Clean new learner: no history.
            return LearnerSummary(
                user_id=user_id,
                overall_mastery=0.0,
                concept_count=0,
                total_events=profile.total_events if profile else 0,
                concepts=[],
                persistent_gaps=[],
                is_new_learner=True,
            )

        concepts = [
            ConceptMastery(
                concept_key=s.concept_key,
                mastery=s.mastery,
                attempts=s.attempts,
                successful_attempts=s.successful_attempts,
                has_persistent_gap=s.has_persistent_gap,
                hint_dependency=hint_dependency_ratio(s),
            )
            for s in profile.concepts.values()
        ]
        concepts.sort(key=lambda c: c.mastery)

        masteries = [c.mastery for c in concepts]
        overall = round(sum(masteries) / len(masteries), 1) if masteries else 0.0
        persistent = [c.concept_key for c in concepts if c.has_persistent_gap]

        return LearnerSummary(
            user_id=user_id,
            overall_mastery=overall,
            concept_count=len(concepts),
            total_events=profile.total_events,
            concepts=concepts,
            persistent_gaps=persistent,
            is_new_learner=False,
        )

    async def concept_mastery(self, user_id: str) -> list[ConceptMastery]:
        summary = await self.summary(user_id)
        return summary.concepts

    async def recent_misconceptions(self, user_id: str) -> list[RecentMisconception]:
        profile = await self._profile(user_id)
        if profile is None:
            return []
        out: list[RecentMisconception] = []
        for stat in profile.concepts.values():
            for mkey, count in stat.misconception_counts.items():
                out.append(
                    RecentMisconception(
                        concept_key=stat.concept_key,
                        misconception_key=mkey,
                        occurrences=count,
                        persistent=count >= 2,
                    )
                )
        out.sort(key=lambda m: m.occurrences, reverse=True)
        return out

    async def recent_events(self, user_id: str, limit: int = 20) -> list[BehaviorEvent]:
        return await self._events.list_for_user(user_id, limit=limit)

    async def mastery_trend(
        self, user_id: str, concept_key: str | None = None
    ) -> list[MasteryTrendPoint]:
        profile = await self._profile(user_id)
        if profile is None:
            return []
        if concept_key is None:
            return profile.trend
        return [p for p in profile.trend if p.concept_key == concept_key]

    async def recommendations(self, user_id: str) -> list[Recommendation]:
        profile = await self._profile(user_id)
        if profile is None or not profile.concepts:
            return []
        recs: list[Recommendation] = []
        for stat in profile.concepts.values():
            if stat.has_persistent_gap:
                recs.append(
                    Recommendation(
                        concept_key=stat.concept_key,
                        reason="A misconception has recurred here — a persistent gap to close.",
                        suggested_difficulty="developing",
                    )
                )
            elif stat.mastery < _WEAK_THRESHOLD and stat.attempts > 0:
                recs.append(
                    Recommendation(
                        concept_key=stat.concept_key,
                        reason="Mastery is still low; more practice recommended.",
                        suggested_difficulty="beginner",
                    )
                )
        # Weakest first.
        recs.sort(key=lambda r: profile.concepts[r.concept_key].mastery)
        return recs
