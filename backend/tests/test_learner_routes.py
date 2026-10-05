"""HTTP tests for /api/learner/dashboard and /knowledge-graph (Phase 7)."""

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def _reset():
    from app.services.behavior import deps as bdeps
    from app.services.challenge import deps as cdeps

    bdeps._mem_events.clear()
    bdeps._mem_profiles.clear()
    cdeps._mem_store.clear()


def test_dashboard_route_empty_learner():
    _reset()
    r = client.get("/api/learner/dashboard", params={"user_id": "new_user"})
    assert r.status_code == 200
    body = r.json()
    assert body["is_new_learner"] is True
    assert body["overall"]["label"] == "Debugly Mastery Indicator"
    assert body["recommended_challenge"]["available"] is False


def test_dashboard_route_with_history():
    _reset()
    u = "dash_http"
    for _ in range(2):
        client.post("/api/behavior/event", json={
            "user_id": u, "event_type": "misconception_detected",
            "concept_key": "list_indexing", "misconception_key": "off_by_one"})
    client.post("/api/behavior/event", json={
        "user_id": u, "event_type": "runtime_error",
        "concept_key": "list_indexing", "error_type": "IndexError"})
    r = client.get("/api/learner/dashboard", params={"user_id": u}).json()
    assert r["is_new_learner"] is False
    assert any(b["concept_key"] == "list_indexing" for b in r["bottlenecks"])
    assert r["recommended_challenge"]["available"] is True


def test_knowledge_graph_route():
    _reset()
    u = "graph_http"
    client.post("/api/behavior/event", json={
        "user_id": u, "event_type": "runtime_error",
        "concept_key": "list_indexing", "error_type": "IndexError"})
    for _ in range(2):
        client.post("/api/behavior/event", json={
            "user_id": u, "event_type": "misconception_detected",
            "concept_key": "list_indexing", "misconception_key": "off_by_one"})
    g = client.get("/api/learner/knowledge-graph", params={"user_id": u}).json()
    assert g["is_empty"] is False
    types = {n["type"] for n in g["nodes"]}
    assert "student" in types and "concept" in types and "misconception" in types
    # Edges reference existing node ids.
    ids = {n["id"] for n in g["nodes"]}
    for e in g["edges"]:
        assert e["source"] in ids and e["target"] in ids
