"""Seed coding tasks for the MVP.

Phase 2 ships a small catalog so the IDE has concrete exercises to load and
grade. The concepts chosen (loop boundaries, list indexing) map directly onto
the Phase 3 misconception library, so no rework is needed when the engine
arrives. ``concept_keys`` are already attached for that reason.
"""

from __future__ import annotations

from app.models.execution import TestCase
from app.models.task import ReuseZone, Task

SEED_TASKS: dict[str, Task] = {
    "sum-list": Task(
        id="sum-list",
        title="Sum a list of numbers",
        prompt=(
            "Write a function `sum_list(numbers)` that returns the sum of all "
            "numbers in the list.\n\n"
            "Example: sum_list([1, 2, 3]) should return 6.\n"
            "An empty list should return 0."
        ),
        starter_code=(
            "def sum_list(numbers):\n"
            "    # TODO: return the sum of all numbers\n"
            "    total = 0\n"
            "    for i in range(len(numbers)):\n"
            "        total += numbers[i]\n"
            "    return total\n"
        ),
        concept_keys=["loops", "list_indexing"],
        # Smart Reuse zones: the signature is reusable boilerplate; the loop
        # that performs the summation is the learning-critical part.
        reuse_zones=[
            ReuseZone(kind="reusable", start_line=1, end_line=1),
            ReuseZone(kind="learning_critical", start_line=3, end_line=6),
        ],
        test_cases=[
            TestCase(name="sum of [1,2,3]", function_name="sum_list", args=[[1, 2, 3]], expected=6),
            TestCase(name="sum of [10,20]", function_name="sum_list", args=[[10, 20]], expected=30),
            TestCase(name="empty list", function_name="sum_list", args=[[]], expected=0),
            TestCase(
                name="negatives",
                function_name="sum_list",
                args=[[-5, 5, -2]],
                expected=-2,
                hidden=True,
            ),
        ],
    ),
    "count-evens": Task(
        id="count-evens",
        title="Count even numbers",
        prompt=(
            "Write a function `count_evens(numbers)` that returns how many "
            "numbers in the list are even.\n\n"
            "Example: count_evens([1, 2, 3, 4]) should return 2."
        ),
        starter_code=(
            "def count_evens(numbers):\n"
            "    # TODO: count how many numbers are even\n"
            "    count = 0\n"
            "    for n in numbers:\n"
            "        if n % 2 == 0:\n"
            "            count += 1\n"
            "    return count\n"
        ),
        concept_keys=["loops", "boolean_conditions"],
        test_cases=[
            TestCase(name="[1,2,3,4] -> 2", function_name="count_evens", args=[[1, 2, 3, 4]], expected=2),
            TestCase(name="all odd", function_name="count_evens", args=[[1, 3, 5]], expected=0),
            TestCase(name="all even", function_name="count_evens", args=[[2, 4, 6, 8]], expected=4),
            TestCase(name="empty", function_name="count_evens", args=[[]], expected=0, hidden=True),
        ],
    ),
}
