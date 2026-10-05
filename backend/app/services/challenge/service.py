"""Challenge service: personalize, grade, and feed results into Phase 5.

* ``generate_for_learner`` reads the learner profile, deterministically selects
  the target concept/misconception and difficulty, builds constraints, and asks
  the generator for content.
* ``submit`` grades a submission (code via the existing execution runner;
  predict-the-output via exact-match), records a ChallengeResult, and emits
  behavior events into the Phase 5 tracker so mastery updates through the
  existing path (no duplicated mastery logic).

Hidden answers (test cases, expected behavior, predict answer) are never
returned to the caller.
"""

from __future__ import annotations

from app.models.behavior import BehaviorEventType, EventRecordRequest
from app.models.challenge import (
    Challenge,
    ChallengeConstraints,
    ChallengeResult,
    ChallengeType,
    Difficulty,
    SubmitChallengeRequest,
    SubmitChallengeResponse,
)
from app.services.behavior.tracker import BehaviorTracker
from app.services.challenge.difficulty import select_difficulty
from app.services.challenge.generator import generate_challenge
from app.services.challenge.selector import select_target
from app.services.execution.runner import execute

# Default task type when the caller doesn't specify one.
_DEFAULT_TASK_TYPE = ChallengeType.FIX_THE_BUG


class ChallengeService:
    def __init__(self, store, tracker: BehaviorTracker, profile_repo) -> None:
        self._store = store
        self._tracker = tracker
        self._profiles = profile_repo

    # ---- generation ----

    async def generate_for_learner(
        self,
        user_id: str,
        *,
        preferred_concept: str | None = None,
        task_type: ChallengeType | None = None,
    ) -> Challenge:
        profile = await self._profiles.get(user_id)
        selection = select_target(profile, preferred_concept=preferred_concept)

        if selection is None:
            # Clean new learner: start with a beginner off-by-one practice.
            constraints = ChallengeConstraints(
                concept_key="loops",
                concept_name="Loops",
                misconception_key=None,
                misconception_name=None,
                difficulty=Difficulty.BEGINNER,
                task_type=task_type or _DEFAULT_TASK_TYPE,
                learning_objective="Practice basic loop reasoning.",
                learner_context={"new_learner": True},
            )
        else:
            difficulty = select_difficulty(selection.stat)
            stat = selection.stat
            learner_context = {
                "mastery": stat.mastery if stat else 0.0,
                "persistent_gap": stat.has_persistent_gap if stat else False,
                "hint_dependency": round(
                    (stat.hints_requested / max(stat.attempts, 1)) if stat and stat.attempts else 0.0,
                    2,
                ),
                "selection_reason": selection.reason,
            }
            avoid = None
            if selection.misconception_key == "off_by_one":
                avoid = "range(len(list) + 1) summation loops"
            constraints = ChallengeConstraints(
                concept_key=selection.concept_key,
                concept_name=selection.concept_name,
                misconception_key=selection.misconception_key,
                misconception_name=selection.misconception_name,
                difficulty=difficulty,
                task_type=task_type or _DEFAULT_TASK_TYPE,
                learning_objective=(
                    f"Demonstrate understanding of {selection.concept_name.lower()} "
                    "by transferring it to a new problem."
                ),
                learner_context=learner_context,
                avoid_pattern=avoid,
            )

        challenge = generate_challenge(constraints, user_id=user_id)
        await self._store.save_challenge(challenge)
        return challenge

    async def preview_target(self, user_id: str) -> dict | None:
        """Read-only preview of the NEXT challenge target for a learner.

        Reuses the exact Phase 6 selector + difficulty logic but does NOT
        generate or persist a challenge and has no side effects. Returns None
        for a clean learner (no profile yet). Used by the dashboard's
        "recommended challenge" section so merely viewing the dashboard never
        spawns a challenge.
        """
        profile = await self._profiles.get(user_id)
        selection = select_target(profile)
        if selection is None:
            return None
        difficulty = select_difficulty(selection.stat)
        return {
            "concept_key": selection.concept_key,
            "concept_name": selection.concept_name,
            "misconception_key": selection.misconception_key,
            "misconception_name": selection.misconception_name,
            "difficulty": difficulty.value,
            "task_type": _DEFAULT_TASK_TYPE.value,
            "learning_objective": (
                f"Demonstrate understanding of {selection.concept_name.lower()} "
                "by transferring it to a new problem."
            ),
            "reason": selection.reason,
        }

    # ---- grading + recording ----

    async def submit(
        self, challenge_id: str, req: SubmitChallengeRequest
    ) -> SubmitChallengeResponse | None:
        challenge = await self._store.get_challenge(challenge_id)
        if challenge is None:
            return None

        if challenge.task_type == ChallengeType.PREDICT_THE_OUTPUT:
            passed, passed_count, total, feedback = self._grade_predict(challenge, req)
        else:
            passed, passed_count, total, feedback = self._grade_code(challenge, req)

        # Record the result (append-only).
        result = ChallengeResult(
            challenge_id=challenge.id,
            user_id=req.user_id,
            concept_key=challenge.concept_key,
            misconception_key=challenge.misconception_key,
            difficulty=challenge.difficulty,
            passed=passed,
            attempts=req.attempts,
            hints_used=req.hints_used,
            duration_ms=req.duration_ms,
        )
        await self._store.save_result(result)

        # Feed Phase 5: a challenge attempt + outcome. Mastery updates through
        # the existing tracker; we do not compute mastery here.
        new_mastery = await self._feed_behavior(challenge, req, passed)

        message = (
            "Solved it! 🎉 This counts toward your mastery."
            if passed
            else "Not passing yet — review the failing cases and try again."
        )
        return SubmitChallengeResponse(
            passed=passed,
            passed_count=passed_count,
            total_count=total,
            test_feedback=feedback,
            message=message,
            new_mastery=new_mastery,
        )

    def _grade_code(self, challenge: Challenge, req: SubmitChallengeRequest):
        code = req.code or ""
        result = execute(code, tests=challenge.test_cases)
        passed = result.status.value == "success" and result.total_count > 0
        # Student-safe feedback: NAMES + pass/fail only, no expected values.
        feedback = [{"name": t.name, "passed": t.passed} for t in result.test_results]
        return passed, result.passed_count, result.total_count, feedback

    def _grade_predict(self, challenge: Challenge, req: SubmitChallengeRequest):
        expected = (challenge.predict_answer or "").strip()
        got = (req.predicted_output or "").strip()
        passed = expected != "" and got == expected
        total = 1
        passed_count = 1 if passed else 0
        # Never echo the expected answer.
        feedback = [{"name": "predicted output", "passed": passed}]
        return passed, passed_count, total, feedback

    async def _feed_behavior(
        self, challenge: Challenge, req: SubmitChallengeRequest, passed: bool
    ) -> float | None:
        ck = challenge.concept_key

        async def rec(event_type, **kw):
            return await self._tracker.record(
                EventRecordRequest(
                    user_id=req.user_id,
                    session_id=req.session_id,
                    concept_key=ck,
                    event_type=event_type,
                    difficulty=challenge.difficulty.value,
                    **kw,
                )
            )

        # The attempt itself (counts toward attempts for mastery).
        await rec(
            BehaviorEventType.CHALLENGE_ATTEMPT,
            misconception_key=challenge.misconception_key,
            payload={"passed": passed, "challenge_id": challenge.id},
        )
        for _ in range(max(0, req.hints_used)):
            await rec(BehaviorEventType.HINT_REQUESTED)

        profile = None
        if passed:
            profile = await rec(
                BehaviorEventType.SUCCESSFUL_EXECUTION,
                payload={"used_hint": req.hints_used > 0, "challenge_id": challenge.id},
            )
        else:
            profile = await rec(
                BehaviorEventType.TEST_FAILURE,
                payload={"challenge_id": challenge.id},
            )

        if profile and ck in profile.concepts:
            return profile.concepts[ck].mastery
        return None
