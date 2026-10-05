"""Smart Reuse tests (Phase 9)."""

import asyncio

import pytest

from app.db.repositories.memory import (
    InMemoryEventsRepository,
    InMemoryProfileRepository,
)
from app.models.behavior import BehaviorEventType
from app.models.reuse import ReuseCheckRequest, ReuseVerdict
from app.services.behavior.tracker import BehaviorTracker
from app.services.reuse.service import ReuseService


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


@pytest.fixture
def wiring():
    events = InMemoryEventsRepository()
    profiles = InMemoryProfileRepository()
    tracker = BehaviorTracker(events, profiles)
    return ReuseService(tracker), events


def test_boilerplate_reuse_allowed(wiring):
    service, _ = wiring
    # sum-list reusable zone is line 1 (the def signature).
    resp = run(service.check(ReuseCheckRequest(
        user_id="u", task_id="sum-list", start_line=1, end_line=1)))
    assert resp.verdict == ReuseVerdict.ALLOWED
    assert resp.allowed is True
    assert resp.learning_critical_overlap is False


def test_learning_critical_reuse_flagged_not_blocked(wiring):
    service, _ = wiring
    # Lines 3-6 are learning-critical in sum-list.
    resp = run(service.check(ReuseCheckRequest(
        user_id="u", task_id="sum-list", start_line=4, end_line=5)))
    assert resp.verdict == ReuseVerdict.FLAGGED
    assert resp.learning_critical_overlap is True
    # Crucially, reuse is NOT blocked — only flagged.
    assert resp.allowed is True


def test_reuse_without_zones_is_unrestricted(wiring):
    service, _ = wiring
    resp = run(service.check(ReuseCheckRequest(
        user_id="u", task_id="count-evens", start_line=1, end_line=3)))
    assert resp.verdict == ReuseVerdict.UNRESTRICTED
    assert resp.allowed is True


def test_unknown_task_is_unrestricted(wiring):
    service, _ = wiring
    resp = run(service.check(ReuseCheckRequest(
        user_id="u", task_id="nope", start_line=1, end_line=2)))
    assert resp.verdict == ReuseVerdict.UNRESTRICTED


def test_reuse_records_behavior_event(wiring):
    service, events = wiring
    run(service.check(ReuseCheckRequest(
        user_id="u", task_id="sum-list", start_line=4, end_line=5,
        char_count=40, source="previous_submission")))
    recorded = run(events.list_for_user("u"))
    assert len(recorded) == 1
    e = recorded[0]
    assert e.event_type == BehaviorEventType.CODE_REUSE_PASTE
    assert e.payload["learning_critical"] is True
    assert e.payload["source"] == "previous_submission"
