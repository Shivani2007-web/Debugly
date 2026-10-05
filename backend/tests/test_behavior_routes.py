"""HTTP tests for behavior + profile routes (Phase 5).

Uses the FastAPI TestClient. Since the test environment has no Mongo lifespan,
the behavior deps fall back to the shared in-memory repositories.
"""

from fastapi.testclient import TestClient

from app.main import create_app
from app.db.repositories import memory as mem

client = TestClient(create_app())


def _reset():
    # The deps module holds process-wide in-memory singletons; clear them so
    # tests don't bleed into each other.
    from app.services.behavior import deps

    deps._mem_events.clear()
    deps._mem_profiles.clear()


def test_record_event_and_fetch_summary():
    _reset()
    u = "http_u1"
    # Record a repeated misconception via the batch endpoint.
    batch = {
        "events": [
            {"user_id": u, "event_type": "submission", "concept_key": "list_indexing"},
            {"user_id": u, "event_type": "runtime_error", "concept_key": "list_indexing", "error_type": "IndexError"},
            {"user_id": u, "event_type": "misconception_detected", "concept_key": "list_indexing", "misconception_key": "off_by_one"},
            {"user_id": u, "event_type": "misconception_detected", "concept_key": "list_indexing", "misconception_key": "off_by_one"},
        ]
    }
    r = client.post("/api/behavior/events", json=batch)
    assert r.status_code == 200
    assert r.json()["recorded"] == 4

    summary = client.get(f"/api/profile/{u}/summary").json()
    assert summary["is_new_learner"] is False
    assert "list_indexing" in summary["persistent_gaps"]


def test_clean_new_student_route():
    _reset()
    summary = client.get("/api/profile/brand_new/summary").json()
    assert summary["is_new_learner"] is True
    assert summary["overall_mastery"] == 0.0


def test_misconceptions_and_recommendations_routes():
    _reset()
    u = "http_u2"
    for _ in range(2):
        client.post("/api/behavior/event", json={
            "user_id": u, "event_type": "misconception_detected",
            "concept_key": "loops", "misconception_key": "infinite_loop",
        })
    rms = client.get(f"/api/profile/{u}/misconceptions").json()
    assert rms and rms[0]["persistent"] is True
    recs = client.get(f"/api/profile/{u}/recommendations").json()
    assert any(r["concept_key"] == "loops" for r in recs)


def test_events_and_trend_routes():
    _reset()
    u = "http_u3"
    client.post("/api/behavior/event", json={
        "user_id": u, "event_type": "submission", "concept_key": "loops",
    })
    client.post("/api/behavior/event", json={
        "user_id": u, "event_type": "successful_execution", "concept_key": "loops",
    })
    events = client.get(f"/api/profile/{u}/events").json()
    assert len(events) == 2
    trend = client.get(f"/api/profile/{u}/trend?concept_key=loops").json()
    assert len(trend) >= 1
