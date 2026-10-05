"""Learner profile read endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.behavior import (
    BehaviorEvent,
    ConceptMastery,
    LearnerSummary,
    MasteryTrendPoint,
    RecentMisconception,
    Recommendation,
)
from app.services.behavior.deps import get_profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/{user_id}/summary", response_model=LearnerSummary)
async def learner_summary(user_id: str) -> LearnerSummary:
    return await get_profile_service().summary(user_id)


@router.get("/{user_id}/mastery", response_model=list[ConceptMastery])
async def concept_mastery(user_id: str) -> list[ConceptMastery]:
    return await get_profile_service().concept_mastery(user_id)


@router.get("/{user_id}/misconceptions", response_model=list[RecentMisconception])
async def recent_misconceptions(user_id: str) -> list[RecentMisconception]:
    return await get_profile_service().recent_misconceptions(user_id)


@router.get("/{user_id}/events", response_model=list[BehaviorEvent])
async def recent_events(user_id: str, limit: int = 20) -> list[BehaviorEvent]:
    return await get_profile_service().recent_events(user_id, limit=limit)


@router.get("/{user_id}/trend", response_model=list[MasteryTrendPoint])
async def mastery_trend(user_id: str, concept_key: str | None = None) -> list[MasteryTrendPoint]:
    return await get_profile_service().mastery_trend(user_id, concept_key=concept_key)


@router.get("/{user_id}/recommendations", response_model=list[Recommendation])
async def recommendations(user_id: str) -> list[Recommendation]:
    return await get_profile_service().recommendations(user_id)
