"""Concept + misconception catalog.

A small, extensible registry mapping stable misconception keys to their concept
area and display name. Rules reference these keys; the engine uses the catalog
to populate ``concept`` and ``misconception`` on each verdict. Adding a new
misconception is a single entry here plus a rule module.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MisconceptionDef:
    """Static definition of a misconception for display + grouping."""

    key: str
    concept: str
    name: str
    description: str


# Keyed by misconception key. Concept names are human-facing.
CATALOG: dict[str, MisconceptionDef] = {
    "off_by_one": MisconceptionDef(
        key="off_by_one",
        concept="Loop Boundaries",
        name="Off-by-one / loop boundary error",
        description="Loop range or index bound is one too many or one too few.",
    ),
    "boolean_condition": MisconceptionDef(
        key="boolean_condition",
        concept="Boolean Logic",
        name="Incorrect boolean condition",
        description="Condition uses the wrong operator or logic for the intended check.",
    ),
    "assignment_vs_comparison": MisconceptionDef(
        key="assignment_vs_comparison",
        concept="Operators",
        name="Assignment vs comparison confusion",
        description="Using = where == is meant, or confusing the two in reasoning.",
    ),
    "infinite_loop": MisconceptionDef(
        key="infinite_loop",
        concept="Loop Termination",
        name="Infinite loop / missing progress",
        description="Loop condition never becomes false; the loop variable is not advanced.",
    ),
    "variable_scope": MisconceptionDef(
        key="variable_scope",
        concept="Variable Scope",
        name="Variable scope confusion",
        description="Expecting a name defined in one scope to be visible in another.",
    ),
    "function_parameter": MisconceptionDef(
        key="function_parameter",
        concept="Functions",
        name="Function parameter / argument confusion",
        description="Calling a function with the wrong number or shape of arguments.",
    ),
    "missing_return": MisconceptionDef(
        key="missing_return",
        concept="Functions",
        name="Missing or incorrect return value",
        description="Function computes a value but returns None, or prints instead of returning.",
    ),
    "list_indexing": MisconceptionDef(
        key="list_indexing",
        concept="List Indexing",
        name="List indexing confusion",
        description="Indexing past the end, or confusing length with last valid index.",
    ),
    "mutable_default": MisconceptionDef(
        key="mutable_default",
        concept="Mutability",
        name="Mutable vs immutable misunderstanding",
        description="Using a mutable default argument, or assuming copies where there are references.",
    ),
    "recursion_base_case": MisconceptionDef(
        key="recursion_base_case",
        concept="Recursion",
        name="Recursion / base-case misunderstanding",
        description="Recursive function lacks a reachable base case or never reduces its input.",
    ),
}


def get_def(key: str) -> MisconceptionDef:
    """Return a misconception definition, raising if the key is unknown."""
    return CATALOG[key]
