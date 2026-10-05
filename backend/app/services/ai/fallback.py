"""Deterministic fallback provider.

Produces structured, level-appropriate Socratic content WITHOUT any AI call.
Used when Gemini is unavailable (no key, SDK missing, API error, rate limit),
and also by tests so the suite runs fully offline.

Crucially, the fallback is still *grounded* in the misconception the engine
detected — it never invents a diagnosis. It emits the same JSON shape the tutor
service expects, so the downstream validation path is identical to the AI path.
"""

from __future__ import annotations

import json

from app.models.tutor import TutorRequest, TutorInteractionType

# Per-misconception Socratic scaffolding, indexed by hint level (1-4). Each
# entry is intentionally conceptual, never the literal corrected code.
_SCAFFOLDS: dict[str, dict[int, dict]] = {
    "off_by_one": {
        1: {"question": "If a list has 3 items, what is the index of the last one? And what does range(len(list)) give you?"},
        2: {"message": "Think about where your loop stops. Compare the largest index you access against the last valid index of the list."},
        3: {"message": "range(n) yields 0..n-1. A list of length n has valid indices 0..n-1 — so range(len(list)) already covers every element. Adding +1 reaches an index that doesn't exist."},
        4: {"message": "Your loop bound is one too high: it visits an index equal to len(list), which is past the end. Adjust the range so the largest index you touch is len(list) - 1."},
    },
    "list_indexing": {
        1: {"question": "For a list of length n, what is the largest index you can safely use?"},
        2: {"message": "Look at the value you're using as an index. Is it ever equal to the list's length?"},
        3: {"message": "Indexing is zero-based: valid indices run from 0 to len(list) - 1. Using len(list) itself always lands one past the end."},
        4: {"message": "You're indexing with the length instead of the last position. The last element is at len(list) - 1, not len(list)."},
    },
    "infinite_loop": {
        1: {"question": "What has to change inside your loop for its condition to eventually become False?"},
        2: {"message": "Check whether the variable in your loop condition is actually updated in the loop body."},
        3: {"message": "A loop terminates only when its condition can become False. If nothing inside the body moves a variable toward that, or there's no break, it runs forever."},
        4: {"message": "Nothing in the loop advances toward the exit condition. Update the loop variable each iteration (or add a break) so the condition can become False."},
    },
    "recursion_base_case": {
        1: {"question": "What input should make your function stop calling itself and just return a value directly?"},
        2: {"message": "Look for a base case — a condition where the function returns without recursing."},
        3: {"message": "Every recursion needs a base case that is eventually reached, and each call must move the input closer to it. Without that, it recurses until the stack overflows."},
        4: {"message": "Your function always calls itself with no stopping condition. Add an if-check that returns directly for the smallest input, and make sure each call shrinks the argument toward it."},
    },
    "missing_return": {
        1: {"question": "After your function computes the answer, how does the caller actually receive it?"},
        2: {"message": "Notice the difference between printing a value and returning it. What does the caller get back?"},
        3: {"message": "print() shows a value on screen but the function still returns None. To hand a result back to the caller you must use return."},
        4: {"message": "Replace (or add) a return statement so the computed value is returned, not just printed. Printing does not give the value back to code that called the function."},
    },
    "function_parameter": {
        1: {"question": "How many values does your function expect, and how many are you giving it at the call site?"},
        2: {"message": "Compare the parameters in the function definition with the arguments in your call."},
        3: {"message": "A function call must supply a value for each required parameter, in order. A mismatch raises a TypeError about missing or extra arguments."},
        4: {"message": "The call doesn't match the definition's parameter count. Pass exactly the arguments the function declares, in the right order."},
    },
    "mutable_default": {
        1: {"question": "What happens to a default list argument the second time you call the function?"},
        2: {"message": "Consider when the default value is created — is it fresh on each call, or shared?"},
        3: {"message": "Default arguments are evaluated once, when the function is defined. A mutable default (like []) is then shared across every call, so changes persist."},
        4: {"message": "Use None as the default and create a fresh list inside the function when the argument is None, instead of a mutable default that is shared between calls."},
    },
    "variable_scope": {
        1: {"question": "Where is this variable defined, and is that the same place you're trying to use it?"},
        2: {"message": "Trace where the name is assigned. Is it visible in the scope where you read it?"},
        3: {"message": "A name defined inside one function isn't visible in another, and a name must be assigned before it's used. Reading an undefined name raises NameError."},
        4: {"message": "The variable isn't defined in the scope where you use it. Define it in that scope, pass it in as a parameter, or assign it before reading."},
    },
    "assignment_vs_comparison": {
        1: {"question": "On that line, are you trying to store a value or to check whether two values are equal?"},
        2: {"message": "Look at = versus ==. One assigns, the other compares and produces a True/False result that you're currently discarding."},
        3: {"message": "A single = assigns a value to a name. A double == compares and yields a boolean. Writing a bare comparison as a statement throws its result away."},
        4: {"message": "That line compares with == but discards the result. If you meant to store a value, use a single =."},
    },
    "boolean_condition": {
        1: {"question": "In your condition, is each side of 'or' actually a complete comparison?"},
        2: {"message": "Check whether a bare value sits on one side of 'or'. Does it compare against anything?"},
        3: {"message": "'A == x or y' is read as '(A == x) or (y)'. A non-empty value y is always truthy, so the whole condition is always True. Each side of 'or' needs its own full comparison."},
        4: {"message": "Rewrite the condition so both sides are real comparisons, e.g. compare the same variable against each value separately on either side of 'or'."},
    },
}

_GENERIC = {
    1: {"question": "What part of your code do you think produced this result? Walk through what you expected versus what happened."},
    2: {"message": "Focus on the line involved in the error and reason about what it does step by step."},
    3: {"message": "Re-read the failing line carefully and compare its behavior to what the task asks for."},
    4: {"message": "Narrow it down to the single line causing the problem and consider what a correct version would need to do differently."},
}

_ACK = {
    "off_by_one": "I see a loop boundary that might be reaching one step too far.",
    "list_indexing": "There's an indexing step worth a closer look.",
    "infinite_loop": "This loop looks like it may never stop on its own.",
    "recursion_base_case": "Your recursive function may be missing a place to stop.",
    "missing_return": "Your function does the work, but the result may not be getting back to the caller.",
    "function_parameter": "The way this function is called doesn't quite match how it's defined.",
    "mutable_default": "That default argument could behave in a surprising way across calls.",
    "variable_scope": "A variable here might not be visible where you're using it.",
    "assignment_vs_comparison": "There's a spot where assigning and comparing may have been mixed up.",
    "boolean_condition": "This condition may not be checking what you intend.",
}


def _hint_payload(req: TutorRequest, level: int) -> dict:
    key = req.misconception.misconception_key if req.misconception else None
    scaffold = _SCAFFOLDS.get(key, _GENERIC).get(level, _GENERIC[level]) if key else _GENERIC.get(level, _GENERIC[1])

    ack = _ACK.get(key, "Let's take a closer look at what happened.") if key else "Let's take a closer look."
    question = scaffold.get("question")
    message = scaffold.get("message") or (
        f"{ack} Here's something to think about." if level == 1 else ack
    )

    robot_state = "concerned" if level <= 2 else "encouraging"
    next_action = "answer_question" if question else "request_next_hint"
    if level >= 4:
        next_action = "try_again"

    return {
        "message": message if not question else ack,
        "hint_level": level,
        "question": question,
        "options": [],
        "explanation": None,
        "robot_state": robot_state,
        "next_action": next_action,
    }


def _feedback_payload(req: TutorRequest) -> dict:
    key = req.misconception.misconception_key if req.misconception else None
    learned = None
    if key and key in _SCAFFOLDS:
        learned = _SCAFFOLDS[key][3].get("message")
    return {
        "message": "Nice work — you corrected it! 🎉",
        "hint_level": None,
        "question": None,
        "options": [],
        "explanation": learned or "You worked through the problem and fixed it.",
        "robot_state": "celebrating",
        "next_action": "continue",
    }


def _explain_payload(req: TutorRequest) -> dict:
    key = req.misconception.misconception_key if req.misconception else None
    explanation = _SCAFFOLDS.get(key, {}).get(3, {}).get("message") if key else None
    return {
        "message": "Here's the idea behind it.",
        "hint_level": None,
        "question": None,
        "options": [],
        "explanation": explanation or "Review the concept involved and how it applies to your code.",
        "robot_state": "thinking",
        "next_action": "continue",
    }


def _wrong_answer_payload(req: TutorRequest, level: int) -> dict:
    base = _hint_payload(req, level)
    base["message"] = "Not quite — let's look at it from another angle."
    base["robot_state"] = "encouraging"
    return base


def build_fallback_json(req: TutorRequest, level: int) -> str:
    """Return a JSON string matching the tutor response schema.

    Mirrors the AI path so validation downstream is identical.
    """
    if req.interaction == TutorInteractionType.FEEDBACK:
        payload = _feedback_payload(req)
    elif req.interaction == TutorInteractionType.EXPLAIN:
        payload = _explain_payload(req)
    elif req.answer_was_correct is False:
        payload = _wrong_answer_payload(req, level)
    else:
        payload = _hint_payload(req, level)

    return json.dumps(payload)
