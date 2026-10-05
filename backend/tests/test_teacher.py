"""Teacher dashboard aggregation + demo seed tests (Phase 9)."""

import asyncio

import pytest

from app.db.repositories.memory import (
    InMemoryEventsRepository,
    InMemoryProfileRepository,
)
from app.services.behavior.profile_service import ProfileService
from app.services.behavior.tracker import BehaviorTracker
from app.services.demo.seed import seed_demo_class
from app.services.teacher.service import TeacherService


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


@pytest.fixture
def wiring():
    events = InMemoryEventsRepository()
    profiles = InMemoryProfileRepository()
    tracker = BehaviorTracker(events, profiles)
    profile_service = ProfileService(events, profiles)
    teacher = TeacherService(profiles, profile_service)
    return teacher, tracker, profiles, events


def test_empty_class_overview(wiring):
    teacher, *_ = wiring
    ov = run(teacher.overview())
    assert ov.is_empty is True
    assert ov.class_size == 0
    assert ov.common_misconceptions == []


def test_demo_seed_populates_class(wiring):
    teacher, tracker, profiles, events = wiring
    result = run(seed_demo_class(tracker, profiles, events))
    assert result["count"] == 5
    all_profiles = run(profiles.list_all())
    assert len([p for p in all_profiles if p.concepts]) == 5


def test_overview_reports_class_metrics(wiring):
    teacher, tracker, profiles, events = wiring
    run(seed_demo_class(tracker, profiles, events))
    ov = run(teacher.overview())
    assert ov.is_empty is False
    assert ov.class_size == 5
    assert 0 <= ov.average_mastery <= 100
    # off_by_one appears for multiple students -> a common misconception.
    keys = {m.misconception_key for m in ov.common_misconceptions}
    assert "off_by_one" in keys
    off = next(m for m in ov.common_misconceptions if m.misconception_key == "off_by_one")
    assert off.students_affected >= 2


def test_overview_surfaces_students_needing_attention(wiring):
    teacher, tracker, profiles, events = wiring
    run(seed_demo_class(tracker, profiles, events))
    ov = run(teacher.overview())
    # demo-dia has heavy struggle and should need attention.
    uids = {s.user_id for s in ov.students_needing_attention}
    assert "demo-dia" in uids


def test_concept_weaknesses_sorted_weakest_first(wiring):
    teacher, tracker, profiles, events = wiring
    run(seed_demo_class(tracker, profiles, events))
    ov = run(teacher.overview())
    masteries = [w.average_mastery for w in ov.concept_weaknesses]
    assert masteries == sorted(masteries)


def test_student_list_and_detail(wiring):
    teacher, tracker, profiles, events = wiring
    run(seed_demo_class(tracker, profiles, events))
    students = run(teacher.students())
    assert len(students) == 5
    detail = run(teacher.student_detail("demo-ava"))
    assert detail.found is True
    assert detail.user_id == "demo-ava"
    assert detail.concepts


def test_student_detail_unknown(wiring):
    teacher, *_ = wiring
    detail = run(teacher.student_detail("ghost"))
    assert detail.found is False


def test_seed_is_idempotent(wiring):
    teacher, tracker, profiles, events = wiring
    run(seed_demo_class(tracker, profiles, events))
    run(seed_demo_class(tracker, profiles, events))  # re-seed
    # Still exactly 5 demo students, not 10.
    all_profiles = run(profiles.list_all())
    demo = [p for p in all_profiles if p.user_id.startswith("demo-")]
    assert len(demo) == 5
