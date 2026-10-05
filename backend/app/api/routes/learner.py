"""Student analytics endpoints (read-only).

* GET /api/learner/dashboard?user_id=...        — full mastery dashboard.
* GET /api/learner/knowledge-graph?user_id=...  — derived knowledge graph.

Both compose existing Phase 5/6 data; neither computes mastery, selects
challenges, or calls Gemini.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.models.dashboard import DashboardResponse, KnowledgeGraph
from app.services.learner.deps import get_dashboard_service, get_graph_service

router = APIRouter(prefix="/learner", tags=["learner"])


@router.get("/dashboard", response_model=DashboardResponse)
async def learner_dashboard(user_id: str) -> DashboardResponse:
    return await get_dashboard_service().build(user_id)


@router.get("/knowledge-graph", response_model=KnowledgeGraph)
async def learner_knowledge_graph(user_id: str) -> KnowledgeGraph:
    return await get_graph_service().build(user_id)
