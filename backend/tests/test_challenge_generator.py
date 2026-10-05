"""Challenge generation + parsing + fallback + view-safety tests (Phase 6)."""

import json

from app.models.challenge import (
    ChallengeConstraints,
    ChallengeType,
    Difficulty,
    to_view,
)
from app.services.ai.provider import AIProvider, AIProviderError
from app.services.challenge import generator


def constraints(task_type=ChallengeType.FIX_THE_BUG, mkey="off_by_one"):
    return ChallengeConstraints(
        concept_key="list_indexing",
        concept_name="List Indexing",
        misconception_key=mkey,
        misconception_name="Off-by-one",
        difficulty=Difficulty.BEGINNER,
        task_type=task_type,
        learning_objective="Transfer the concept.",
    )


class _GoodProvider(AIProvider):
    name = "good"

    @property
    def available(self):
        return True

    def generate_json(self, system, user):
        return json.dumps({
            "title": "Fix the slice",
            "description": "Return the first two elements.",
            "starter_code": "def first_two(xs):\n    return xs[0:3]\n",
            "expected_behavior": "Returns first two.",
            "learning_objective": "Index ranges.",
            "predict_code": None,
            "predict_answer": None,
            "test_cases": [
                {"name": "two of three", "function_name": "first_two", "args": [[1, 2, 3]], "expected": [1, 2], "kwargs": {}, "hidden": False},
                {"name": "two of five", "function_name": "first_two", "args": [[1, 2, 3, 4, 5]], "expected": [1, 2], "kwargs": {}, "hidden": True},
            ],
        })


class _MalformedProvider(AIProvider):
    name = "bad"

    @property
    def available(self):
        return True

    def generate_json(self, system, user):
        return "this is not JSON at all {{{"


class _EmptyTestsProvider(AIProvider):
    name = "empty"

    @property
    def available(self):
        return True

    def generate_json(self, system, user):
        # Valid JSON but a code challenge with NO tests -> must fall back.
        return json.dumps({
            "title": "x", "description": "y", "starter_code": "def f():\n    pass\n",
            "expected_behavior": "", "learning_objective": "", "test_cases": [],
        })


class _FailingProvider(AIProvider):
    name = "fail"

    @property
    def available(self):
        return True

    def generate_json(self, system, user):
        raise AIProviderError("rate limited")


def test_ai_generation_parses_into_challenge(monkeypatch):
    monkeypatch.setattr(generator, "get_provider", lambda: _GoodProvider())
    ch = generator.generate_challenge(constraints(), user_id="u1")
    assert ch.generated_by == "gemini"
    assert ch.title == "Fix the slice"
    assert len(ch.test_cases) == 2
    # Backend-fixed fields are preserved regardless of model output.
    assert ch.concept_key == "list_indexing"
    assert ch.difficulty == Difficulty.BEGINNER


def test_malformed_response_falls_back(monkeypatch):
    monkeypatch.setattr(generator, "get_provider", lambda: _MalformedProvider())
    ch = generator.generate_challenge(constraints(), user_id="u1")
    assert ch.generated_by == "fallback"
    assert ch.test_cases  # fallback provides gradeable tests


def test_empty_tests_response_falls_back(monkeypatch):
    monkeypatch.setattr(generator, "get_provider", lambda: _EmptyTestsProvider())
    ch = generator.generate_challenge(constraints(), user_id="u1")
    assert ch.generated_by == "fallback"


def test_api_error_falls_back(monkeypatch):
    monkeypatch.setattr(generator, "get_provider", lambda: _FailingProvider())
    ch = generator.generate_challenge(constraints(), user_id="u1")
    assert ch.generated_by == "fallback"


def test_no_provider_uses_fallback(monkeypatch):
    monkeypatch.setattr(generator, "get_provider", lambda: None)
    ch = generator.generate_challenge(constraints(), user_id="u1")
    assert ch.generated_by == "fallback"


def test_predict_fallback_has_answer(monkeypatch):
    monkeypatch.setattr(generator, "get_provider", lambda: None)
    ch = generator.generate_challenge(
        constraints(task_type=ChallengeType.PREDICT_THE_OUTPUT), user_id="u1"
    )
    assert ch.predict_code is not None
    assert ch.predict_answer is not None


# ---- hidden-answer protection ----

def test_view_strips_hidden_answers(monkeypatch):
    monkeypatch.setattr(generator, "get_provider", lambda: _GoodProvider())
    ch = generator.generate_challenge(constraints(), user_id="u1")
    view = to_view(ch)
    dumped = view.model_dump()
    # No expected values, no hidden test, no expected_behavior in the view.
    assert "expected_behavior" not in dumped
    assert "test_cases" not in dumped
    assert "predict_answer" not in dumped
    # Only non-hidden test NAMES are exposed.
    assert dumped["visible_tests"] == [{"name": "two of three"}]
    assert dumped["total_tests"] == 2  # count known, details hidden


def test_predict_view_hides_answer(monkeypatch):
    monkeypatch.setattr(generator, "get_provider", lambda: None)
    ch = generator.generate_challenge(
        constraints(task_type=ChallengeType.PREDICT_THE_OUTPUT), user_id="u1"
    )
    view = to_view(ch)
    dumped = view.model_dump()
    assert dumped.get("predict_code") is not None
    assert "predict_answer" not in dumped
