"""Challenge-generation prompts for Gemini.

Gemini receives the deterministic constraints and must return a single JSON
object matching the challenge schema. The prompt enforces the anti-memorization
rule (vary the surface problem, test the same concept) and forbids leaking that
it is reusing any specific pattern.
"""

from __future__ import annotations

import json

from app.models.challenge import ChallengeConstraints, ChallengeType

SYSTEM_INSTRUCTION = (
    "You are Debugly's challenge author for Python learners. You generate ONE "
    "short, focused coding micro-challenge that targets a specific concept and "
    "difficulty chosen by the system. You do NOT choose the concept, "
    "misconception, or difficulty — those are fixed in the constraints.\n\n"
    "RULES:\n"
    "1. Test TRANSFER of understanding: use a different surface problem than "
    "the learner's original mistake. Do not reproduce the exact pattern named "
    "in 'avoid_pattern'.\n"
    "2. Keep it small and solvable in a few minutes at the given difficulty.\n"
    "3. For fix_the_bug/complete_the_code/small_build_task: provide "
    "starter_code and 2-4 assertion test cases calling a single function.\n"
    "4. For predict_the_output: provide predict_code and the exact "
    "predict_answer.\n"
    "5. Respond with ONLY a JSON object (no markdown fences) of this shape:\n"
    "{\n"
    '  "title": string,\n'
    '  "description": string,\n'
    '  "starter_code": string,\n'
    '  "expected_behavior": string,\n'
    '  "learning_objective": string,\n'
    '  "predict_code": string or null,\n'
    '  "predict_answer": string or null,\n'
    '  "test_cases": [\n'
    '     {"name": string, "function_name": string, "args": array,\n'
    '      "kwargs": object, "expected": any, "hidden": boolean}\n'
    "  ]\n"
    "}\n"
)

_TASK_HINT = {
    ChallengeType.FIX_THE_BUG: "Provide starter_code that contains a bug the learner must fix.",
    ChallengeType.COMPLETE_THE_CODE: "Provide starter_code with a clearly marked gap to complete.",
    ChallengeType.PREDICT_THE_OUTPUT: "Provide predict_code; test_cases must be empty.",
    ChallengeType.SMALL_BUILD_TASK: "Provide a spec and an empty-bodied starter function.",
}


def build_prompts(constraints: ChallengeConstraints) -> tuple[str, str]:
    """Return (system_instruction, user_prompt)."""
    ctx = {
        "concept": constraints.concept_name,
        "concept_key": constraints.concept_key,
        "misconception": constraints.misconception_name,
        "difficulty": constraints.difficulty.value,
        "task_type": constraints.task_type.value,
        "learning_objective": constraints.learning_objective,
        "task_type_hint": _TASK_HINT[constraints.task_type],
        "avoid_pattern": constraints.avoid_pattern,
        "learner_context": constraints.learner_context,
    }
    user_prompt = (
        "Generate one challenge satisfying these constraints. Vary the surface "
        "problem so it tests the concept, not recall.\n\n"
        f"CONSTRAINTS (JSON):\n{json.dumps(ctx, indent=2)}\n\n"
        "Respond with the JSON object only."
    )
    return SYSTEM_INSTRUCTION, user_prompt
