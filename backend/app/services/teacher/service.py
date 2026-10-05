"""Teacher dashboard aggregation (read-only).

Aggregates across all learner profiles to produce class-level analytics:
overall average mastery, the most common misconceptions, weakest concepts, and
students needing attention. Reuses the Phase 5 ProfileService for per-student
drill-down. No mastery is recomputed; values come straight from the profiles.
"""

from __future__ import annotations

from app.models.teacher import (
    CommonMisconception,
    ConceptWeakness,
    StudentDetail,
    StudentListEntry,
    StudentNeedingAttention,
    TeacherOverview,
)
from app.services.behavior.profile_service import ProfileService

# A student is "needing attention" when overall mastery is low or they carry
# multiple persistent gaps.
_ATTENTION_MASTERY = 45.0


class TeacherService:
    def __init__(self, profile_repo, profile_service: ProfileService) -> None:
        self._profiles = profile_repo
        self._profile_service = profile_service

    async def overview(self) -> TeacherOverview:
        profiles = await self._profiles.list_all()
        # Only count learners who have actually practiced something.
        active = [p for p in profiles if p.concepts]

        if not active:
            return TeacherOverview(
                class_size=0,
                average_mastery=0.0,
                common_misconceptions=[],
                concept_weaknesses=[],
                students_needing_attention=[],
                is_empty=True,
            )

        # ---- overall average mastery (mean of per-student overall means) ----
        per_student_overall: dict[str, float] = {}
        for p in active:
            masteries = [s.mastery for s in p.concepts.values()]
            per_student_overall[p.user_id] = (
                round(sum(masteries) / len(masteries), 1) if masteries else 0.0
            )
        avg = round(sum(per_student_overall.values()) / len(per_student_overall), 1)

        # ---- common misconceptions (across students) ----
        mis_students: dict[tuple[str, str], set[str]] = {}
        mis_occurrences: dict[tuple[str, str], int] = {}
        mis_persistent: dict[tuple[str, str], int] = {}
        for p in active:
            for ck, stat in p.concepts.items():
                for mkey, count in stat.misconception_counts.items():
                    key = (mkey, ck)
                    mis_students.setdefault(key, set()).add(p.user_id)
                    mis_occurrences[key] = mis_occurrences.get(key, 0) + count
                    if count >= 2:
                        mis_persistent[key] = mis_persistent.get(key, 0) + 1
        common = [
            CommonMisconception(
                misconception_key=mkey,
                concept_key=ck,
                students_affected=len(students),
                total_occurrences=mis_occurrences[(mkey, ck)],
                persistent_students=mis_persistent.get((mkey, ck), 0),
            )
            for (mkey, ck), students in mis_students.items()
        ]
        common.sort(key=lambda c: (c.students_affected, c.total_occurrences), reverse=True)

        # ---- concept weaknesses ----
        concept_masteries: dict[str, list[float]] = {}
        concept_gaps: dict[str, int] = {}
        for p in active:
            for ck, stat in p.concepts.items():
                concept_masteries.setdefault(ck, []).append(stat.mastery)
                if stat.has_persistent_gap:
                    concept_gaps[ck] = concept_gaps.get(ck, 0) + 1
        weaknesses = [
            ConceptWeakness(
                concept_key=ck,
                average_mastery=round(sum(ms) / len(ms), 1),
                students_practicing=len(ms),
                students_with_gap=concept_gaps.get(ck, 0),
            )
            for ck, ms in concept_masteries.items()
        ]
        weaknesses.sort(key=lambda w: w.average_mastery)

        # ---- students needing attention ----
        attention: list[StudentNeedingAttention] = []
        for p in active:
            gap_count = sum(1 for s in p.concepts.values() if s.has_persistent_gap)
            overall = per_student_overall[p.user_id]
            if overall < _ATTENTION_MASTERY or gap_count >= 2:
                reasons = []
                if overall < _ATTENTION_MASTERY:
                    reasons.append("low overall mastery")
                if gap_count >= 2:
                    reasons.append(f"{gap_count} persistent gaps")
                elif gap_count == 1:
                    reasons.append("a persistent gap")
                attention.append(
                    StudentNeedingAttention(
                        user_id=p.user_id,
                        overall_mastery=overall,
                        persistent_gap_count=gap_count,
                        reason=", ".join(reasons),
                    )
                )
        attention.sort(key=lambda s: s.overall_mastery)

        return TeacherOverview(
            class_size=len(active),
            average_mastery=avg,
            common_misconceptions=common,
            concept_weaknesses=weaknesses,
            students_needing_attention=attention,
            is_empty=False,
        )

    async def students(self) -> list[StudentListEntry]:
        profiles = await self._profiles.list_all()
        out: list[StudentListEntry] = []
        for p in profiles:
            if not p.concepts:
                continue
            masteries = [s.mastery for s in p.concepts.values()]
            overall = round(sum(masteries) / len(masteries), 1) if masteries else 0.0
            gaps = [ck for ck, s in p.concepts.items() if s.has_persistent_gap]
            out.append(
                StudentListEntry(
                    user_id=p.user_id,
                    overall_mastery=overall,
                    concept_count=len(p.concepts),
                    persistent_gaps=gaps,
                )
            )
        out.sort(key=lambda s: s.overall_mastery)
        return out

    async def student_detail(self, user_id: str) -> StudentDetail:
        summary = await self._profile_service.summary(user_id)
        if summary.is_new_learner:
            return StudentDetail(
                user_id=user_id, overall_mastery=0.0, concepts=[],
                misconceptions=[], recent_events=[], found=False,
            )
        misconceptions = await self._profile_service.recent_misconceptions(user_id)
        events = await self._profile_service.recent_events(user_id, limit=25)
        return StudentDetail(
            user_id=user_id,
            overall_mastery=summary.overall_mastery,
            concepts=[c.model_dump() for c in summary.concepts],
            misconceptions=[m.model_dump() for m in misconceptions],
            recent_events=[e.model_dump(mode="json") for e in events],
            found=True,
        )
