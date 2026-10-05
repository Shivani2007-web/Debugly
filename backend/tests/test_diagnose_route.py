"""HTTP tests for POST /api/analysis/diagnose."""

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_diagnose_route_detects_off_by_one():
    payload = {
        "code": "def f(xs):\n    for i in range(len(xs) + 1):\n        print(xs[i])\n",
    }
    resp = client.post("/api/analysis/diagnose", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    keys = [m["misconception_key"] for m in body["misconceptions"]]
    assert "off_by_one" in keys
    # Verdict carries the required fields.
    off = next(m for m in body["misconceptions"] if m["misconception_key"] == "off_by_one")
    assert "concept" in off
    assert "confidence" in off
    assert off["evidence"]
    assert off["lines"]


def test_diagnose_route_with_execution_evidence():
    payload = {
        "code": "def f(xs):\n    for i in range(len(xs) + 1):\n        print(xs[i])\n",
        "execution_result": {
            "status": "test_failed",
            "stdout": "",
            "stderr": "",
            "error": {"error_type": "IndexError", "message": "list index out of range", "line": 3, "traceback": None},
            "test_results": [
                {"name": "c1", "passed": False, "expected": None, "actual": None,
                 "error": {"error_type": "IndexError", "message": "x", "line": 3, "traceback": None}, "hidden": False}
            ],
            "passed_count": 0,
            "total_count": 1,
            "duration_ms": 5,
            "truncated": False,
        },
    }
    resp = client.post("/api/analysis/diagnose", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["had_execution_evidence"] is True
    off = next(m for m in body["misconceptions"] if m["misconception_key"] == "off_by_one")
    assert off["error_type"] == "IndexError"


def test_diagnose_route_clean_code_empty():
    payload = {"code": "def add(a, b):\n    return a + b\n"}
    resp = client.post("/api/analysis/diagnose", json=payload)
    assert resp.status_code == 200
    assert resp.json()["misconceptions"] == []
