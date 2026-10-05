"""HTTP tests for Phase 9 routes: reuse, teacher, demo."""

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def _reset():
    from app.services.behavior import deps as bdeps

    bdeps._mem_events.clear()
    bdeps._mem_profiles.clear()


def test_reuse_route_flags_learning_critical():
    _reset()
    r = client.post("/api/reuse/check", json={
        "user_id": "ru", "task_id": "sum-list", "start_line": 4, "end_line": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "flagged"
    assert body["allowed"] is True


def test_demo_seed_then_teacher_overview():
    _reset()
    seed = client.post("/api/demo/seed").json()
    assert seed["count"] == 5

    ov = client.get("/api/teacher/overview").json()
    assert ov["is_empty"] is False
    assert ov["class_size"] == 5
    assert any(m["misconception_key"] == "off_by_one" for m in ov["common_misconceptions"])

    students = client.get("/api/teacher/students").json()
    assert len(students) == 5

    detail = client.get("/api/teacher/student/demo-ava").json()
    assert detail["found"] is True


def test_teacher_overview_empty_before_seed():
    _reset()
    ov = client.get("/api/teacher/overview").json()
    assert ov["is_empty"] is True
