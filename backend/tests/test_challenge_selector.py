"""Challenge target-selection tests (Phase 6)."""

from app.models.behavior import ConceptStat, LearnerProfile
from app.services.challenge.selector import select_target


def _profile(**concepts) -> LearnerProfile:
    p = LearnerProfile(user_id="u")
    p.concepts = concepts
    return p


def test_none_for_clean_learner():
    assert select_target(None) is None
    assert select_target(LearnerProfile(user_id="u")) is None


def test_persistent_misconception_is_prioritised():
    profile = _profile(
        loops=ConceptStat(concept_key="loops", attempts=5, successful_attempts=4, mastery=70.0),
        list_indexing=ConceptStat(
            concept_key="list_indexing", attempts=4, successful_attempts=1, mastery=30.0,
            misconception_counts={"off_by_one": 3}, repeated_misconception_events=2,
        ),
    )
    sel = select_target(profile)
    assert sel.concept_key == "list_indexing"
    assert sel.reason == "persistent misconception"
    assert sel.misconception_key == "off_by_one"


def test_low_mastery_selected_when_no_persistent_gap():
    profile = _profile(
        loops=ConceptStat(concept_key="loops", attempts=5, successful_attempts=5, mastery=75.0),
        funcs=ConceptStat(concept_key="funcs", attempts=4, successful_attempts=1, mastery=30.0),
    )
    sel = select_target(profile)
    assert sel.concept_key == "funcs"


def test_mastered_concepts_skipped_unless_only_option():
    # Both mastered -> still returns one (reinforcement) rather than None.
    profile = _profile(
        a=ConceptStat(concept_key="a", attempts=5, successful_attempts=5, mastery=90.0),
        b=ConceptStat(concept_key="b", attempts=5, successful_attempts=5, mastery=88.0),
    )
    sel = select_target(profile)
    assert sel is not None
    assert "reinforcement" in sel.reason


def test_preferred_concept_override():
    profile = _profile(
        loops=ConceptStat(concept_key="loops", attempts=5, successful_attempts=1, mastery=20.0),
        funcs=ConceptStat(concept_key="funcs", attempts=5, successful_attempts=5, mastery=90.0),
    )
    sel = select_target(profile, preferred_concept="funcs")
    assert sel.concept_key == "funcs"
    assert "reinforcement" in sel.reason
