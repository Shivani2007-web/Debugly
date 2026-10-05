"""Teacher-service dependency wiring (reuses Phase 5 repos/service)."""

from __future__ import annotations

from app.services.behavior.deps import _repos
from app.services.behavior.profile_service import ProfileService
from app.services.teacher.service import TeacherService


def get_teacher_service() -> TeacherService:
    events_repo, profile_repo = _repos()
    return TeacherService(profile_repo, ProfileService(events_repo, profile_repo))
