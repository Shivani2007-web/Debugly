"""Deterministic challenge fallback templates.

Produces a valid, gradeable :class:`Challenge` without any AI call — used when
Gemini is unavailable or returns malformed content, and by tests so the suite
runs offline. Templates target the same underlying concept as the misconception
but deliberately use a DIFFERENT surface problem than a learner's original code
(transfer, not memorization).

Each template returns a dict matching the challenge JSON schema; the generator
validates it into a Challenge just like the AI path, so both paths converge.
"""

from __future__ import annotations

from app.models.challenge import ChallengeConstraints, ChallengeType

# Concept -> Fix-the-Bug template. These test the SAME concept with a varied
# problem (e.g. off-by-one tested via "last element" rather than summation).
_FIX_THE_BUG: dict[str, dict] = {
    "off_by_one": {
        "title": "Fix the loop boundary",
        "description": (
            "`get_last_three` should return the last three items of a list. "
            "It raises an error on some inputs. Fix the loop boundary so it "
            "works for any list of length >= 3."
        ),
        "starter_code": (
            "def get_last_three(items):\n"
            "    result = []\n"
            "    for i in range(len(items) - 2, len(items) + 1):\n"
            "        result.append(items[i])\n"
            "    return result\n"
        ),
        "expected_behavior": "Returns the final three elements without IndexError.",
        "tests": [
            {"name": "last three of 5", "function_name": "get_last_three", "args": [[1, 2, 3, 4, 5]], "expected": [3, 4, 5]},
            {"name": "exactly three", "function_name": "get_last_three", "args": [[7, 8, 9]], "expected": [7, 8, 9]},
            {"name": "longer list", "function_name": "get_last_three", "args": [[0, 1, 2, 3, 4, 5, 6]], "expected": [4, 5, 6], "hidden": True},
        ],
        "objective": "Reason about valid index ranges: the last index is len-1, not len.",
    },
    "list_indexing": {
        "title": "Fix the index",
        "description": (
            "`middle_element` should return the middle item of an odd-length "
            "list. It uses the wrong index. Fix it."
        ),
        "starter_code": (
            "def middle_element(items):\n"
            "    return items[len(items) // 2 + 1]\n"
        ),
        "expected_behavior": "Returns the center element for odd-length lists.",
        "tests": [
            {"name": "middle of 3", "function_name": "middle_element", "args": [[10, 20, 30]], "expected": 20},
            {"name": "middle of 5", "function_name": "middle_element", "args": [[1, 2, 3, 4, 5]], "expected": 3},
            {"name": "single", "function_name": "middle_element", "args": [[42]], "expected": 42, "hidden": True},
        ],
        "objective": "Zero-based indexing: the middle of an n-length list is at n//2.",
    },
    "infinite_loop": {
        "title": "Make the loop terminate",
        "description": (
            "`countdown` should return a list from n down to 1. The loop never "
            "ends. Fix it so it terminates."
        ),
        "starter_code": (
            "def countdown(n):\n"
            "    result = []\n"
            "    while n > 0:\n"
            "        result.append(n)\n"
            "    return result\n"
        ),
        "expected_behavior": "Returns [n, n-1, ..., 1] and terminates.",
        "tests": [
            {"name": "countdown 3", "function_name": "countdown", "args": [3], "expected": [3, 2, 1]},
            {"name": "countdown 1", "function_name": "countdown", "args": [1], "expected": [1]},
            {"name": "countdown 5", "function_name": "countdown", "args": [5], "expected": [5, 4, 3, 2, 1], "hidden": True},
        ],
        "objective": "A loop needs its condition variable to progress toward termination.",
    },
    "missing_return": {
        "title": "Return the result",
        "description": (
            "`doubled` should return a new list with each number doubled, but "
            "callers get None. Fix it."
        ),
        "starter_code": (
            "def doubled(nums):\n"
            "    result = [n * 2 for n in nums]\n"
            "    print(result)\n"
        ),
        "expected_behavior": "Returns the doubled list to the caller.",
        "tests": [
            {"name": "doubles", "function_name": "doubled", "args": [[1, 2, 3]], "expected": [2, 4, 6]},
            {"name": "empty", "function_name": "doubled", "args": [[]], "expected": []},
        ],
        "objective": "Printing shows a value; returning hands it back to the caller.",
    },
}

_GENERIC_FIX = {
    "title": "Fix the bug",
    "description": "This function has a bug. Find and fix it so all tests pass.",
    "starter_code": "def add_one(n):\n    return n + 2\n",
    "expected_behavior": "Returns n + 1.",
    "tests": [
        {"name": "add_one(1)=2", "function_name": "add_one", "args": [1], "expected": 2},
        {"name": "add_one(5)=6", "function_name": "add_one", "args": [5], "expected": 6},
    ],
    "objective": "Read the failing cases and reason about the intended behavior.",
}

_PREDICT = {
    "off_by_one": {
        "title": "Predict the output",
        "description": "What does this code print? Enter the exact output.",
        "predict_code": "xs = [10, 20, 30]\nfor i in range(len(xs)):\n    print(xs[i])",
        "answer": "10\n20\n30",
        "objective": "range(len(xs)) visits every valid index exactly once.",
    },
}

_SMALL_BUILD = {
    "title": "Small build task",
    "description": (
        "Write a function `count_positive(nums)` that returns how many numbers "
        "in the list are greater than zero."
    ),
    "starter_code": "def count_positive(nums):\n    # your code here\n    pass\n",
    "expected_behavior": "Returns the count of positive numbers.",
    "tests": [
        {"name": "mixed", "function_name": "count_positive", "args": [[-1, 2, -3, 4]], "expected": 2},
        {"name": "all negative", "function_name": "count_positive", "args": [[-1, -2]], "expected": 0},
        {"name": "all positive", "function_name": "count_positive", "args": [[1, 2, 3]], "expected": 3, "hidden": True},
    ],
    "objective": "Translate a plain-language spec into a working loop and condition.",
}


def build_fallback_dict(constraints: ChallengeConstraints) -> dict:
    """Return a challenge dict (schema-shaped) for the given constraints."""
    ttype = constraints.task_type
    mkey = constraints.misconception_key

    if ttype == ChallengeType.PREDICT_THE_OUTPUT:
        tpl = _PREDICT.get(mkey or "", _PREDICT["off_by_one"])
        return {
            "title": tpl["title"],
            "description": tpl["description"],
            "predict_code": tpl["predict_code"],
            "predict_answer": tpl["answer"],
            "learning_objective": tpl["objective"],
            "test_cases": [],
        }

    if ttype == ChallengeType.SMALL_BUILD_TASK:
        tpl = _SMALL_BUILD
        return {
            "title": tpl["title"],
            "description": tpl["description"],
            "starter_code": tpl["starter_code"],
            "expected_behavior": tpl["expected_behavior"],
            "learning_objective": tpl["objective"],
            "test_cases": tpl["tests"],
        }

    # FIX_THE_BUG (default) and COMPLETE_THE_CODE share the bug-template shape.
    tpl = _FIX_THE_BUG.get(mkey or "", _GENERIC_FIX)
    return {
        "title": tpl["title"],
        "description": tpl["description"],
        "starter_code": tpl["starter_code"],
        "expected_behavior": tpl["expected_behavior"],
        "learning_objective": tpl["objective"],
        "test_cases": tpl["tests"],
    }
