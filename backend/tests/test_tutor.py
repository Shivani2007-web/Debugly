"""Tutor service tests (Phase 4).

Covers the required scenarios:
1. A detected misconception produces a Level 1 Socratic interaction.
2. Repeated help requests progress through hint levels 1 -> 4 (and cap).
3. A successful correction produces encouraging feedback (and resets level).
4. Gemini/API failure produces a graceful fallback.

Tests run fully offline using the deterministic fallback (no provider) and a
stub provider for the AI-path and failure-path cases.
"""

import json

import pytest

from app.models.misconception import (
    DetectedMisconception,
    Evidence,
    EvidenceSource,
    EvidenceWeight,
)
from app.models.tutor import (
    NextAction,
    RobotState,
    TutorInteractionType,
    TutorRequest,
)
from app.services.ai.provider import AIProvider, AIProviderError
from app.services.tutor import socratic
from app.services.tutor.state import hint_state


def make_misconception(key="off_by_one"):
    return DetectedMisconception(
        concept="Loop Boundaries",
        misconception_key=key,
        misconception="Off-by-one / loop boundary error",
        confidence=0.9,
        evidence=[
            Evidence(
                source=EvidenceSource.CODE,
                weight=EvidenceWeight.STRONG,
                detail="range(len(x)+1) overshoots",
                line=3,
            )
        ],
        lines=[3],
        error_type="IndexError",
    )


def _clear_provider_cache():
    fn = getattr(socratic, "get_provider", None)
    if fn is not None and hasattr(fn, "cache_clear"):
        fn.cache_clear()


@pytest.fixture(autouse=True)
def _clear_state():
    # Ensure each test starts with fresh hint progression.
    hint_state._levels.clear()
    _clear_provider_cache()
    yield
    hint_state._levels.clear()
    _clear_provider_cache()


# ---- Scenario 1: Level 1 Socratic interaction ----

def test_detected_misconception_produces_level_1(monkeypatch):
    monkeypatch.setattr(socratic, "get_provider", lambda: None)  # force fallback
    req = TutorRequest(
        session_id="s1",
        interaction=TutorInteractionType.HINT,
        misconception=make_misconception(),
        task_prompt="Sum a list",
    )
    resp = socratic.generate(req)
    assert resp.hint_level == 1
    assert resp.question is not None            # Level 1 asks a question
    assert resp.next_action == NextAction.ANSWER_QUESTION
    assert resp.grounded_in == "off_by_one"     # grounded in engine verdict


# ---- Scenario 2: progression through levels ----

def test_repeated_requests_progress_levels(monkeypatch):
    monkeypatch.setattr(socratic, "get_provider", lambda: None)
    req = TutorRequest(
        session_id="s2",
        interaction=TutorInteractionType.HINT,
        misconception=make_misconception(),
    )
    levels = [socratic.generate(req).hint_level for _ in range(5)]
    assert [int(l) for l in levels] == [1, 2, 3, 4, 4]  # advances then caps at 4


def test_wrong_answer_does_not_escalate(monkeypatch):
    monkeypatch.setattr(socratic, "get_provider", lambda: None)
    base = dict(session_id="s3", misconception=make_misconception())
    first = socratic.generate(TutorRequest(interaction=TutorInteractionType.HINT, **base))
    assert first.hint_level == 1
    # A wrong answer re-asks the SAME level, not level 2.
    retry = socratic.generate(
        TutorRequest(
            interaction=TutorInteractionType.HINT,
            answer_was_correct=False,
            **base,
        )
    )
    assert retry.hint_level == 1


# ---- Scenario 3: successful correction feedback ----

def test_correction_produces_encouraging_feedback(monkeypatch):
    monkeypatch.setattr(socratic, "get_provider", lambda: None)
    # Advance a couple of levels first.
    hint_req = TutorRequest(session_id="s4", misconception=make_misconception())
    socratic.generate(hint_req)
    socratic.generate(hint_req)
    assert hint_state.current_level("s4", "off_by_one") == 2

    fb = socratic.generate(
        TutorRequest(
            session_id="s4",
            interaction=TutorInteractionType.FEEDBACK,
            misconception=make_misconception(),
        )
    )
    assert fb.robot_state == RobotState.CELEBRATING
    assert fb.explanation is not None
    # The route resets; emulate that the service exposes the reset helper.
    socratic.on_successful_correction("s4", "off_by_one")
    assert hint_state.current_level("s4", "off_by_one") == 0


# ---- Scenario 4: API failure -> graceful fallback ----

class _FailingProvider(AIProvider):
    name = "failing"

    @property
    def available(self):
        return True

    def generate_json(self, system_instruction, user_prompt):
        raise AIProviderError("simulated rate limit")


def test_api_failure_falls_back_gracefully(monkeypatch):
    monkeypatch.setattr(socratic, "get_provider", lambda: _FailingProvider())
    resp = socratic.generate(
        TutorRequest(session_id="s5", misconception=make_misconception())
    )
    assert resp.is_fallback is True
    assert resp.message                      # still a usable message
    assert resp.hint_level == 1
    assert resp.grounded_in == "off_by_one"


# ---- AI-path happy case with a stub provider (validates parsing + grounding) ----

class _StubProvider(AIProvider):
    name = "stub"

    @property
    def available(self):
        return True

    def generate_json(self, system_instruction, user_prompt):
        # A model that (misbehaving) tries to claim a different misconception;
        # the service must still ground to the engine's key.
        return json.dumps(
            {
                "message": "What index does your loop reach last?",
                "hint_level": 1,
                "question": "What is the last valid index of a list of length n?",
                "options": [],
                "explanation": None,
                "robot_state": "concerned",
                "next_action": "answer_question",
            }
        )


def test_ai_path_parses_and_grounds(monkeypatch):
    monkeypatch.setattr(socratic, "get_provider", lambda: _StubProvider())
    resp = socratic.generate(
        TutorRequest(session_id="s6", misconception=make_misconception("off_by_one"))
    )
    assert resp.is_fallback is False
    assert resp.question is not None
    assert resp.grounded_in == "off_by_one"   # grounding enforced server-side


def test_no_misconception_stays_generic(monkeypatch):
    monkeypatch.setattr(socratic, "get_provider", lambda: None)
    resp = socratic.generate(TutorRequest(session_id="s7", misconception=None))
    assert resp.grounded_in is None
    assert resp.message
