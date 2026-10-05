"""Smart Reuse contracts.

Debugly does NOT globally disable copy/paste. Instead it classifies a reuse
action against the task's declared reuse zones:

* reusable          — boilerplate that is not the learning objective; reuse freely
* editable          — may be reused but should be adapted
* learning_critical — the code that represents the concept being assessed

A paste that lands in a learning-critical zone is FLAGGED (surfaced to the
student and recorded as behavior), never silently blocked — the goal is to
prevent bypassing the learning objective, not to punish legitimate reuse.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ReuseZoneKind(str, Enum):
    REUSABLE = "reusable"
    EDITABLE = "editable"
    LEARNING_CRITICAL = "learning_critical"


class ReuseVerdict(str, Enum):
    ALLOWED = "allowed"                 # boilerplate / editable reuse
    FLAGGED = "flagged"                 # overlaps a learning-critical zone
    UNRESTRICTED = "unrestricted"       # task has no zones -> nothing to protect


class ReuseCheckRequest(BaseModel):
    """A reuse/paste action to classify.

    ``start_line``/``end_line`` are the 1-based lines in the editor the pasted
    content will occupy. ``source`` describes where the reuse came from (e.g.
    "previous_submission", "clipboard") for behavior analytics only.
    """

    user_id: str
    task_id: str | None = None
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    char_count: int = 0
    source: str = "clipboard"
    session_id: str | None = None


class ReuseCheckResponse(BaseModel):
    verdict: ReuseVerdict
    overlaps: list[ReuseZoneKind] = Field(default_factory=list)
    message: str
    # True when the student is allowed to proceed (always True — we never block,
    # we inform). Kept explicit so the UI reads intent clearly.
    allowed: bool = True
    learning_critical_overlap: bool = False
