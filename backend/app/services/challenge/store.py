"""Challenge + result storage.

In-memory and MongoDB-backed stores for generated challenges and their results.
Challenges are stored with full answers server-side; only the student-safe view
is ever returned by the API. Results are an append-only record (like events).
"""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.challenge import Challenge, ChallengeResult

CHALLENGES_COLLECTION = "challenges"
CHALLENGE_RESULTS_COLLECTION = "challenge_results"


class InMemoryChallengeStore:
    def __init__(self) -> None:
        self._challenges: dict[str, Challenge] = {}
        self._results: list[ChallengeResult] = []

    async def save_challenge(self, challenge: Challenge) -> None:
        self._challenges[challenge.id] = challenge.model_copy(deep=True)

    async def get_challenge(self, challenge_id: str) -> Challenge | None:
        c = self._challenges.get(challenge_id)
        return c.model_copy(deep=True) if c else None

    async def save_result(self, result: ChallengeResult) -> None:
        self._results.append(result)

    async def results_for_user(self, user_id: str) -> list[ChallengeResult]:
        return [r for r in self._results if r.user_id == user_id]

    def clear(self) -> None:
        self._challenges.clear()
        self._results.clear()


class MongoChallengeStore:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._challenges = db[CHALLENGES_COLLECTION]
        self._results = db[CHALLENGE_RESULTS_COLLECTION]

    async def save_challenge(self, challenge: Challenge) -> None:
        await self._challenges.replace_one(
            {"id": challenge.id}, challenge.model_dump(mode="json"), upsert=True
        )

    async def get_challenge(self, challenge_id: str) -> Challenge | None:
        doc = await self._challenges.find_one({"id": challenge_id})
        if doc is None:
            return None
        doc.pop("_id", None)
        return Challenge.model_validate(doc)

    async def save_result(self, result: ChallengeResult) -> None:
        await self._results.insert_one(result.model_dump(mode="json"))

    async def results_for_user(self, user_id: str) -> list[ChallengeResult]:
        docs = await self._results.find({"user_id": user_id}).to_list(length=200)
        out = []
        for d in docs:
            d.pop("_id", None)
            out.append(ChallengeResult.model_validate(d))
        return out
