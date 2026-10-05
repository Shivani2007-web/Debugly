"""Coding task contract.

A task is a prompt + starter code + the test cases that grade a submission.
``concept_keys`` and ``reuse_zones`` are declared now (empty-capable) so the
misconception engine (Phase 3) and Smart Reuse (Phase 8) have a stable field
to populate later without reshaping the task.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.execution import TestCase


class ReuseZone(BaseModel):
    """A labeled line range for Smart Reuse (populated in Phase 8)."""

    kind: str  # "reusable" | "editable" | "learning_critical"
    start_line: int
    end_line: int


class Task(BaseModel):
    """A coding exercise served to the IDE."""

    id: str
    title: str
    prompt: str
    starter_code: str
    test_cases: list[TestCase] = Field(default_factory=list)
    concept_keys: list[str] = Field(default_factory=list)
    reuse_zones: list[ReuseZone] = Field(default_factory=list)


class TaskSummary(BaseModel):
    """Lightweight task listing (no test cases / starter code)."""

    id: str
    title: str
    prompt: str
