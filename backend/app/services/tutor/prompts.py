"""Prompt construction for the Socratic tutor.

Builds the system instruction (role + hard guardrails) and a compact, STRUCTURED
user prompt containing only the relevant context: the engine's misconception,
confidence, evidence, lines, error info, hint level, task description, and a
minimal summary of prior attempts. Full learner history is deliberately NOT
sent.

The guardrails here are the policy surface that keeps Gemini from overriding the
deterministic diagnosis or dumping the full solution.
"""

from __future__ import annotations

import json

from app.models.tutor import HintLevel, TutorInteractionType, TutorRequest

_LEVEL_GUIDANCE = {
    HintLevel.QUESTION: (
        "LEVEL 1 (QUESTION): Ask ONE short Socratic question that makes the "
        "student reason about the problem. Do not reveal the cause. Set "
        "'question' and next_action='answer_question'."
    ),
    HintLevel.DIRECTION: (
        "LEVEL 2 (DIRECTION): Point toward the relevant concept or the region "
        "of code to inspect, without naming the exact fix."
    ),
    HintLevel.CONCEPTUAL: (
        "LEVEL 3 (CONCEPTUAL): Explain the underlying principle in general "
        "terms. Still do not write their corrected code."
    ),
    HintLevel.STRONG_GUIDANCE: (
        "LEVEL 4 (STRONG GUIDANCE): Be explicit about what must change and why, "
        "enough to unblock the student — but DO NOT provide the complete "
        "corrected code or a copy-paste solution."
    ),
}

SYSTEM_INSTRUCTION = (
    "You are Debugly, a Socratic programming tutor for Python learners. Your "
    "job is to help a student UNDERSTAND why their code is wrong and learn to "
    "reason it out — not to hand them the answer.\n\n"
    "HARD RULES (never violate):\n"
    "1. You may ONLY discuss the misconception provided in the context. Never "
    "diagnose a different or additional misconception. If no misconception is "
    "provided, give only generic debugging encouragement.\n"
    "2. Never output the student's complete corrected code or a full solution.\n"
    "3. Never claim to have run or modified their code.\n"
    "4. Keep 'message' to 1-3 short sentences, warm and plain.\n"
    "5. Respond ONLY with a single JSON object matching this schema:\n"
    "{\n"
    '  "message": string,\n'
    '  "hint_level": integer 1-4 or null,\n'
    '  "question": string or null,\n'
    '  "options": array of strings (may be empty),\n'
    '  "explanation": string or null,\n'
    '  "robot_state": one of '
    '["idle","thinking","concerned","encouraging","happy","celebrating","sad"],\n'
    '  "next_action": one of '
    '["answer_question","request_next_hint","try_again","continue"]\n'
    "}\n"
    "Do not wrap the JSON in markdown fences."
)


def _context_block(req: TutorRequest, level: int) -> dict:
    """Assemble the minimal structured context for the model."""
    ctx: dict = {"interaction": req.interaction.value}

    if req.task_prompt:
        # Trim to keep the prompt tight.
        ctx["task"] = req.task_prompt[:600]

    if req.misconception is not None:
        m = req.misconception
        ctx["misconception"] = {
            "key": m.misconception_key,
            "concept": m.concept,
            "name": m.misconception,
            "confidence": m.confidence,
            "lines": m.lines,
            "error_type": m.error_type,
            # Compact evidence: detail strings only (no internal weights).
            "evidence": [e.detail for e in m.evidence][:4],
        }
    else:
        ctx["misconception"] = None

    if req.error_type:
        ctx["error"] = {"type": req.error_type, "message": (req.error_message or "")[:200]}

    if req.interaction == TutorInteractionType.HINT:
        ctx["hint_level"] = level
        ctx["level_instruction"] = _LEVEL_GUIDANCE[HintLevel(level)]

    if req.student_answer is not None:
        ctx["student_answer"] = req.student_answer[:300]
        ctx["answer_was_correct"] = req.answer_was_correct

    if req.prior_attempts:
        # Minimal, relevant only — last 3 attempts' error type + pass flag.
        ctx["prior_attempts"] = [
            {"n": a.attempt_number, "error_type": a.error_type, "passed": a.passed}
            for a in req.prior_attempts[-3:]
        ]

    if req.learner_context is not None:
        lc = req.learner_context
        # Longitudinal context ONLY tunes tone/level. It must not change which
        # misconception is discussed (that is fixed by the engine's verdict).
        ctx["learner_context"] = {
            "concept_mastery": lc.concept_mastery,
            "times_this_misconception_seen": lc.times_misconception_seen,
            "persistent_gap": lc.persistent_gap,
            "hint_dependency": lc.hint_dependency,
            "note": (
                "Use this only to adjust encouragement and pacing. Do NOT change "
                "the diagnosed misconception based on it."
            ),
        }

    return ctx


def build_prompts(req: TutorRequest, level: int) -> tuple[str, str]:
    """Return (system_instruction, user_prompt) for the given request."""
    if req.interaction == TutorInteractionType.FEEDBACK:
        task = (
            "The student just CORRECTED their mistake and their code now passes. "
            "Give warm, specific encouragement and a one-sentence 'what you "
            "learned' in 'explanation'. Set robot_state='celebrating', "
            "next_action='continue', hint_level=null."
        )
    elif req.interaction == TutorInteractionType.EXPLAIN:
        task = (
            "Explain the underlying concept of the provided misconception in "
            "general terms (not their exact code) in 'explanation'. "
            "robot_state='thinking', next_action='continue', hint_level=null."
        )
    elif req.answer_was_correct is False:
        task = (
            "The student answered the previous Socratic question incorrectly. "
            "Gently redirect with another angle at the SAME hint level. "
            "robot_state='encouraging'."
        )
    else:
        task = "Produce the hint for the specified hint_level."

    context = _context_block(req, level)
    user_prompt = (
        f"TASK: {task}\n\n"
        f"CONTEXT (JSON):\n{json.dumps(context, indent=2)}\n\n"
        "Respond with the JSON object only."
    )
    return SYSTEM_INSTRUCTION, user_prompt
