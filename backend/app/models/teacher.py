"""Teacher dashboard contracts (read-only, class-level aggregation).

Composed entirely from existing learner profiles — no new storage, no mastery
or diagnosis logic. Surfaces class trends so an instructor can see common
misconceptions, weak concepts, and which students need attention.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CommonMisconception(BaseModel):
    misconception_key: str
    concept_key: str
    students_affected: int
    total_occurrences: int
    persistent_students: int  # students for whom it is a persistent gap


class ConceptWeakness(BaseModel):
    concept_key: str
    average_mastery: float
    students_practicing: int
    students_with_gap: int


class StudentNeedingAttention(BaseModel):
    user_id: str
    overall_mastery: float
    persistent_gap_count: int
    reason: str


class StudentListEntry(BaseModel):
    user_id: str
    overall_mastery: float
    concept_count: int
    persistent_gaps: list[str] = Field(default_factory=list)


class TeacherOverview(BaseModel):
    class_size: int
    average_mastery: float
    common_misconceptions: list[CommonMisconception]
    concept_weaknesses: list[ConceptWeakness]
    students_needing_attention: list[StudentNeedingAttention]
    is_empty: bool


class StudentDetail(BaseModel):
    """A single learner's journey, for the teacher drill-down."""

    user_id: str
    overall_mastery: float
    concepts: list[dict]
    misconceptions: list[dict]
    recent_events: list[dict]
    found: bool = True
