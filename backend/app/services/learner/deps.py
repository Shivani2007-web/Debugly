"""Learner-analytics dependency wiring.

Builds the dashboard + graph services on top of the EXISTING Phase 5 and
Phase 6 wiring, so analytics read the same data stores (Mongo when available,
in-memory otherwise). No new storage is introduced.
"""

from __future__ import annotations

from app.db.mongo import mongo
from app.services.behavior.deps import _repos
from app.services.behavior.profile_service import ProfileService
from app.services.behavior.tracker import BehaviorTracker
from app.services.challenge.deps import _store as _challenge_store
from app.services.challenge.service import ChallengeService
from app.services.learner.dashboard_service import DashboardService
from app.services.learner.graph_service import GraphService


def get_dashboard_service() -> DashboardService:
    events_repo, profile_repo = _repos()
    profile_service = ProfileService(events_repo, profile_repo)
    tracker = BehaviorTracker(events_repo, profile_repo)
    challenge_service = ChallengeService(_challenge_store(), tracker, profile_repo)
    return DashboardService(profile_service, challenge_service)


def get_graph_service() -> GraphService:
    events_repo, profile_repo = _repos()
    return GraphService(profile_repo, events_repo, _challenge_store())
