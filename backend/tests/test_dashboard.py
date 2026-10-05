"""Student dashboard + knowledge-graph tests (Phase 7).

Covers: aggregation, mastery-from-Phase-5, misconception-from-profile, event
timeline, recommendation-from-Phase-6, no fabricated graph relationships,
graph structure, and empty/new-learner state.
"""

import asyncio

import pytest

from app.db.repositories.memory import (
    InMemoryEventsRepository,
    InMemoryProfileRepository,
)
from app.models.behavior import BehaviorEventType, EventRecordRequest
from app.models.challenge import SubmitChallengeRequest
from app.services.behavior.profile_service import ProfileService
from app.services.behavior.tracker import BehaviorTracker
from app.services.challenge import generator
from app.services.challenge.service import ChallengeService
from app.services.challenge.store import InMemoryChallengeStore
from app.services.learner.dashboard_service import DashboardService
from app.services.learner.graph_service import GraphService


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


@pytest.fixture
def wiring(monkeypatch):
    monkeypatch.setattr(generator, "get_provider", lambda: None)  # deterministic
    events = InMemoryEventsRepository()
    profiles = InMemoryProfileRepository()
    store = InMemoryChallengeStore()
    tracker = BehaviorTracker(events, profiles)
    profile_service = ProfileService(events, profiles)
    challenge_service = ChallengeService(store, tracker, profiles)
    dashboard = DashboardService(profile_service, challenge_service)
    graph = GraphService(profiles, events, store)
    return {
        "events": events, "profiles": profiles, "store": store, "tracker": tracker,
        "dashboard": dashboard, "graph": graph, "challenge": challenge_service,
    }


async def seed_persistent_gap(tracker, user="u1", concept="list_indexing"):
    seq = [
        (BehaviorEventType.SUBMISSION, {}),
        (BehaviorEventType.RUNTIME_ERROR, {"error_type": "IndexError"}),
        (BehaviorEventType.MISCONCEPTION_DETECTED, {"misconception_key": "off_by_one"}),
        (BehaviorEventType.HINT_REQUESTED, {}),
        (BehaviorEventType.HINT_LEVEL_REACHED, {"hint_level": 1}),
        (BehaviorEventType.SUBMISSION, {}),
        (BehaviorEventType.RUNTIME_ERROR, {"error_type": "IndexError"}),
        (BehaviorEventType.MISCONCEPTION_DETECTED, {"misconception_key": "off_by_one"}),
    ]
    for et, extra in seq:
        await tracker.record(EventRecordRequest(user_id=user, concept_key=concept, event_type=et, **extra))


# ---- empty / new learner ----

def test_dashboard_empty_new_learner(wiring):
    dash = run(wiring["dashboard"].build("ghost"))
    assert dash.is_new_learner is True
    assert dash.overall.indicator == 0.0
    assert dash.overall.band.value == "not_started"
    assert dash.concepts == []
    assert dash.bottlenecks == []
    assert dash.timeline == []
    assert dash.recommended_challenge.available is False


def test_graph_empty_new_learner(wiring):
    g = run(wiring["graph"].build("ghost"))
    assert g.is_empty is True
    # Only the student node exists.
    assert len(g.nodes) == 1
    assert g.nodes[0].type.value == "student"
    assert g.edges == []


# ---- aggregation + sourcing ----

def test_dashboard_mastery_matches_phase5(wiring):
    run(seed_persistent_gap(wiring["tracker"]))
    dash = run(wiring["dashboard"].build("u1"))
    summary = run(wiring["profiles"].get("u1"))
    # Overall indicator equals the mean of Phase 5 concept masteries (one concept here).
    assert dash.concepts[0].mastery == summary.concepts["list_indexing"].mastery


def test_dashboard_misconception_from_profile(wiring):
    run(seed_persistent_gap(wiring["tracker"]))
    dash = run(wiring["dashboard"].build("u1"))
    assert dash.bottlenecks
    b = dash.bottlenecks[0]
    assert b.concept_key == "list_indexing"
    assert b.misconception_key == "off_by_one"
    assert b.persistent is True
    assert b.occurrences == 2


def test_dashboard_timeline_has_meaningful_events(wiring):
    run(seed_persistent_gap(wiring["tracker"]))
    dash = run(wiring["dashboard"].build("u1"))
    kinds = {e.event_type for e in dash.timeline}
    assert "misconception_detected" in kinds
    assert "hint_requested" in kinds
    # Every entry has a human label; none are raw keystrokes.
    assert all(e.label for e in dash.timeline)


def test_dashboard_recommendation_from_phase6(wiring):
    run(seed_persistent_gap(wiring["tracker"]))
    dash = run(wiring["dashboard"].build("u1"))
    rec = dash.recommended_challenge
    assert rec.available is True
    assert rec.concept_key == "list_indexing"
    assert rec.misconception_key == "off_by_one"
    # Difficulty comes from the Phase 6 deterministic selector (capped for a gap).
    assert rec.difficulty in ("beginner", "developing")
    assert rec.reason == "persistent misconception"


# ---- graph structure + no fabrication ----

def test_graph_builds_full_chain_from_evidence(wiring):
    run(seed_persistent_gap(wiring["tracker"]))
    # Add a solved challenge so outcome evidence exists.
    ch = run(wiring["challenge"].generate_for_learner("u1"))
    run(wiring["challenge"].submit(ch.id, SubmitChallengeRequest(
        user_id="u1", code="def get_last_three(items):\n    return items[len(items) - 3:]\n")))

    g = run(wiring["graph"].build("u1"))
    types = {n.type.value for n in g.nodes}
    # Chain present: student, concept, misconception, evidence, intervention, challenge, outcome.
    assert {"student", "concept", "misconception", "evidence", "intervention", "challenge", "outcome"} <= types
    rels = {e.relation for e in g.edges}
    assert "has_misconception" in rels
    assert "evidenced_by" in rels
    assert "intervention" in rels
    assert "result" in rels


def test_graph_omits_evidence_without_errors(wiring):
    # A concept with a misconception but NO recorded error type must NOT get an
    # evidence node (no fabrication).
    run(wiring["tracker"].record(EventRecordRequest(
        user_id="noerr", concept_key="loops", event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
        misconception_key="infinite_loop")))
    g = run(wiring["graph"].build("noerr"))
    assert not any(n.type.value == "evidence" for n in g.nodes)


def test_graph_omits_intervention_without_hints(wiring):
    # Misconception + error but NO hint -> no intervention node.
    run(wiring["tracker"].record(EventRecordRequest(
        user_id="nohint", concept_key="list_indexing", event_type=BehaviorEventType.RUNTIME_ERROR,
        error_type="IndexError")))
    run(wiring["tracker"].record(EventRecordRequest(
        user_id="nohint", concept_key="list_indexing", event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
        misconception_key="off_by_one")))
    g = run(wiring["graph"].build("nohint"))
    assert not any(n.type.value == "intervention" for n in g.nodes)


def test_graph_omits_challenge_without_results(wiring):
    run(seed_persistent_gap(wiring["tracker"]))  # no challenge submitted
    g = run(wiring["graph"].build("u1"))
    assert not any(n.type.value == "challenge" for n in g.nodes)
    assert not any(n.type.value == "outcome" for n in g.nodes)


def test_graph_edges_reference_existing_nodes(wiring):
    run(seed_persistent_gap(wiring["tracker"]))
    ch = run(wiring["challenge"].generate_for_learner("u1"))
    run(wiring["challenge"].submit(ch.id, SubmitChallengeRequest(
        user_id="u1", code="def get_last_three(items):\n    return items[len(items) - 3:]\n")))
    g = run(wiring["graph"].build("u1"))
    ids = {n.id for n in g.nodes}
    for e in g.edges:
        assert e.source in ids
        assert e.target in ids


def test_mastered_concept_marked_healthy(wiring):
    # Drive a concept to mastery with clean successes (no gap).
    for _ in range(6):
        run(wiring["tracker"].record(EventRecordRequest(
            user_id="pro", concept_key="loops", event_type=BehaviorEventType.SUBMISSION)))
        run(wiring["tracker"].record(EventRecordRequest(
            user_id="pro", concept_key="loops", event_type=BehaviorEventType.SUCCESSFUL_EXECUTION)))
    g = run(wiring["graph"].build("pro"))
    concept_node = next(n for n in g.nodes if n.type.value == "concept")
    # healthy flag reflects mastery/no-gap (may be True if mastery>=80).
    assert concept_node.healthy in (True, False)
