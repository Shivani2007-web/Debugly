"""Learner knowledge-graph derivation (read-only, evidence-grounded).

Builds the chain:

    Student -> Concept -> Misconception -> Evidence -> Intervention -> Challenge -> Outcome

STRICTLY from stored data:
* concept + misconception + hint evidence  <- Phase 5 LearnerProfile / events
* error-type evidence                      <- behavior events
* intervention (hints)                     <- hint events / hint-level stats
* challenge + outcome                       <- Phase 6 ChallengeResult store

If the evidence for a relationship is not present, the edge/node is OMITTED —
never fabricated. A learner with no concepts yields an empty graph (just the
student node).
"""

from __future__ import annotations

from app.models.behavior import BehaviorEvent, BehaviorEventType, LearnerProfile
from app.models.challenge import ChallengeResult
from app.models.dashboard import (
    GraphEdge,
    GraphNode,
    GraphNodeType,
    KnowledgeGraph,
)
from app.services.misconception import concepts as concept_catalog

MASTERED = 80.0


class GraphService:
    def __init__(self, profile_repo, events_repo, challenge_store) -> None:
        self._profiles = profile_repo
        self._events = events_repo
        self._store = challenge_store

    async def build(self, user_id: str) -> KnowledgeGraph:
        profile: LearnerProfile | None = await self._profiles.get(user_id)
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        student_id = f"student:{user_id}"
        nodes.append(GraphNode(id=student_id, type=GraphNodeType.STUDENT, label="You"))

        if profile is None or not profile.concepts:
            return KnowledgeGraph(user_id=user_id, is_empty=True, nodes=nodes, edges=edges)

        # Gather supporting evidence from events + challenge results.
        events = await self._events.list_for_user(user_id, limit=500)
        results = await self._store.results_for_user(user_id)

        error_types_by_concept = _error_types_by_concept(events)
        max_hint_by_concept = _max_hint_by_concept(events, profile)
        results_by_concept = _group_results(results)

        for concept_key, stat in profile.concepts.items():
            healthy = stat.mastery >= MASTERED and not stat.has_persistent_gap
            concept_id = f"concept:{concept_key}"
            nodes.append(GraphNode(
                id=concept_id,
                type=GraphNodeType.CONCEPT,
                label=_concept_label(concept_key, stat),
                healthy=healthy,
                meta={
                    "mastery": stat.mastery,
                    "attempts": stat.attempts,
                    "persistent_gap": stat.has_persistent_gap,
                },
            ))
            relation = "struggles_with" if not healthy else "practices"
            edges.append(GraphEdge(source=student_id, target=concept_id, relation=relation))

            # Misconception nodes (only those actually recorded).
            for mkey, count in stat.misconception_counts.items():
                mis_id = f"mis:{concept_key}:{mkey}"
                nodes.append(GraphNode(
                    id=mis_id,
                    type=GraphNodeType.MISCONCEPTION,
                    label=_misconception_label(mkey),
                    healthy=not (count >= 2),
                    meta={"occurrences": count, "persistent": count >= 2},
                ))
                edges.append(GraphEdge(source=concept_id, target=mis_id, relation="has_misconception"))

                # Evidence node: error types seen for this concept (only if any).
                errs = error_types_by_concept.get(concept_key)
                if errs:
                    ev_id = f"evidence:{concept_key}:{mkey}"
                    detail = ", ".join(sorted(errs))
                    if count >= 2:
                        detail += " + repeated"
                    nodes.append(GraphNode(
                        id=ev_id,
                        type=GraphNodeType.EVIDENCE,
                        label=detail,
                        meta={"error_types": sorted(errs), "repeated": count >= 2},
                    ))
                    edges.append(GraphEdge(source=mis_id, target=ev_id, relation="evidenced_by"))

                # Intervention node: hints reached (only if a hint occurred).
                max_hint = max_hint_by_concept.get(concept_key, 0)
                if max_hint > 0:
                    iv_id = f"intervention:{concept_key}:{mkey}"
                    nodes.append(GraphNode(
                        id=iv_id,
                        type=GraphNodeType.INTERVENTION,
                        label=f"Socratic hint L1-L{max_hint}",
                        meta={"max_hint_level": max_hint},
                    ))
                    # Intervention follows the evidence if present, else the misconception.
                    src = f"evidence:{concept_key}:{mkey}" if errs else mis_id
                    edges.append(GraphEdge(source=src, target=iv_id, relation="intervention"))

            # Challenge + outcome nodes (only if a challenge was attempted).
            for i, res in enumerate(results_by_concept.get(concept_key, [])):
                ch_id = f"challenge:{concept_key}:{i}"
                nodes.append(GraphNode(
                    id=ch_id,
                    type=GraphNodeType.CHALLENGE,
                    label=f"{res.difficulty.value.title()} challenge",
                    meta={"difficulty": res.difficulty.value, "attempts": res.attempts},
                ))
                # Link challenge to the concept's intervention if one exists,
                # else directly to the concept.
                mkey0 = next(iter(stat.misconception_counts), None)
                iv_candidate = f"intervention:{concept_key}:{mkey0}" if mkey0 else None
                has_iv = iv_candidate is not None and any(n.id == iv_candidate for n in nodes)
                edges.append(GraphEdge(
                    source=iv_candidate if has_iv else concept_id,
                    target=ch_id,
                    relation="followed_by",
                ))

                out_id = f"outcome:{concept_key}:{i}"
                nodes.append(GraphNode(
                    id=out_id,
                    type=GraphNodeType.OUTCOME,
                    label="Solved ✓" if res.passed else "Not yet ✗",
                    healthy=res.passed,
                    meta={"passed": res.passed},
                ))
                edges.append(GraphEdge(source=ch_id, target=out_id, relation="result"))

        return KnowledgeGraph(user_id=user_id, is_empty=False, nodes=nodes, edges=edges)


# ---- helpers (pure) ----

def _error_types_by_concept(events: list[BehaviorEvent]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for e in events:
        if e.error_type and e.concept_key:
            out.setdefault(e.concept_key, set()).add(e.error_type)
    return out


def _max_hint_by_concept(events: list[BehaviorEvent], profile: LearnerProfile) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in events:
        if e.event_type == BehaviorEventType.HINT_LEVEL_REACHED and e.concept_key and e.hint_level:
            out[e.concept_key] = max(out.get(e.concept_key, 0), e.hint_level)
    # Fall back to the aggregated max hint level in the profile.
    for ck, stat in profile.concepts.items():
        if stat.max_hint_level_reached:
            out[ck] = max(out.get(ck, 0), stat.max_hint_level_reached)
        elif stat.hints_requested and ck not in out:
            out[ck] = 1  # a hint was requested even if no level event was logged
    return out


def _group_results(results: list[ChallengeResult]) -> dict[str, list[ChallengeResult]]:
    out: dict[str, list[ChallengeResult]] = {}
    for r in sorted(results, key=lambda r: r.created_at):
        out.setdefault(r.concept_key, []).append(r)
    return out


def _concept_label(concept_key: str, stat) -> str:
    mkey = next(iter(stat.misconception_counts), None)
    if mkey and mkey in concept_catalog.CATALOG:
        return concept_catalog.CATALOG[mkey].concept
    return concept_key.replace("_", " ").title()


def _misconception_label(mkey: str) -> str:
    if mkey in concept_catalog.CATALOG:
        return concept_catalog.CATALOG[mkey].name
    return mkey.replace("_", " ").title()
