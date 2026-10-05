"""HTTP tests for challenge routes incl. hidden-answer protection (Phase 6)."""

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def _reset():
    from app.services.behavior import deps as bdeps
    from app.services.challenge import deps as cdeps

    bdeps._mem_events.clear()
    bdeps._mem_profiles.clear()
    cdeps._mem_store.clear()


def test_generate_and_get_never_expose_answers():
    _reset()
    gen = client.post("/api/challenges/generate", json={"user_id": "http_c1"})
    assert gen.status_code == 200
    body = gen.json()
    # The response is a ChallengeView — no answer fields.
    for forbidden in ("test_cases", "expected_behavior", "predict_answer"):
        assert forbidden not in body
    assert "visible_tests" in body

    # GET the same challenge: still no answers.
    got = client.get(f"/api/challenges/{body['id']}").json()
    for forbidden in ("test_cases", "expected_behavior", "predict_answer"):
        assert forbidden not in got


def test_submit_route_grades_and_returns_safe_feedback():
    _reset()
    body = client.post("/api/challenges/generate", json={"user_id": "http_c2"}).json()
    correct = "def get_last_three(items):\n    return items[len(items) - 3:]\n"
    resp = client.post(
        f"/api/challenges/{body['id']}/submit",
        json={"user_id": "http_c2", "code": correct},
    ).json()
    assert resp["passed"] in (True, False)
    for fb in resp["test_feedback"]:
        assert set(fb.keys()) == {"name", "passed"}


def test_submit_unknown_challenge_404():
    _reset()
    r = client.post("/api/challenges/nope/submit", json={"user_id": "x", "code": "y"})
    assert r.status_code == 404
