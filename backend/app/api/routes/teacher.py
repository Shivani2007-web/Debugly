"""Teacher dashboard endpoints (read-only, class-level)."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.teacher import StudentDetail, StudentListEntry, TeacherOverview
from app.services.teacher.deps import get_teacher_service

router = APIRouter(prefix="/teacher", tags=["teacher"])


@router.get("/overview", response_model=TeacherOverview)
async def teacher_overview() -> TeacherOverview:
    return await get_teacher_service().overview()


@router.get("/students", response_model=list[StudentListEntry])
async def teacher_students() -> list[StudentListEntry]:
    return await get_teacher_service().students()


@router.get("/student/{user_id}", response_model=StudentDetail)
async def teacher_student_detail(user_id: str) -> StudentDetail:
    return await get_teacher_service().student_detail(user_id)
