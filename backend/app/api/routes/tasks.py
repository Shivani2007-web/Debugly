"""Task catalog endpoints (read-only for Phase 2)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.task import Task, TaskSummary
from app.services.tasks import get_task, list_tasks

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskSummary])
async def get_tasks() -> list[TaskSummary]:
    """List available tasks (summary view, no test cases)."""
    return [TaskSummary(id=t.id, title=t.title, prompt=t.prompt) for t in list_tasks()]


@router.get("/{task_id}", response_model=Task)
async def get_task_detail(task_id: str) -> Task:
    """Return a full task.

    Hidden test cases are intentionally included so the IDE could show their
    names (but not inputs). Phase 3+ may strip inputs further; for now the
    frontend simply does not render hidden-case details.
    """
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
