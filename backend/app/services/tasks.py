"""Task catalog service.

For Phase 2 the catalog is seeded in-memory (see ``app.seed.tasks``) and served
read-only. Later phases can back this with MongoDB without changing callers:
the two accessor functions below are the only surface the routes depend on.
"""

from __future__ import annotations

from app.models.task import Task
from app.seed.tasks import SEED_TASKS


def list_tasks() -> list[Task]:
    """Return all available tasks."""
    return list(SEED_TASKS.values())


def get_task(task_id: str) -> Task | None:
    """Return a task by id, or None if it does not exist."""
    return SEED_TASKS.get(task_id)
