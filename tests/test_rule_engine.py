"""
Unit tests for Acceptance Test A, Acceptance Test B, and OrganizationRuleEngine.
"""

import pytest
from facesoter.core.ai.provider import DetectedFace
from facesoter.core.organizer.rule_engine import OrganizationRuleEngine, PlannedDestination


def test_acceptance_test_a_multi_person_and_no_face():
    """
    Acceptance Test A:
    Input:
    - one no-face image
    - several single-person images
    - one three-person image (Mom + Dad + Dhruv)
    Expected:
    - three-person image copied into all three relevant person folders
    - no-face image placed into Uncategorized/No Face
    """
    known_people_map = {1: "Mom", 2: "Dad", 3: "Dhruv"}

    # 1. No face image
    no_face_dest = OrganizationRuleEngine.plan_categorization(
        faces=[],
        known_people_map=known_people_map,
    )
    assert len(no_face_dest) == 1
    assert no_face_dest[0].relative_folder == "Uncategorized/No Face"

    # 2. Single person image (Mom)
    mom_face = DetectedFace(bbox=(10, 10, 50, 50), score=0.95, assigned_person_id=1)
    mom_dest = OrganizationRuleEngine.plan_categorization(
        faces=[mom_face],
        known_people_map=known_people_map,
    )
    assert len(mom_dest) == 1
    assert mom_dest[0].relative_folder == "Categorized/Mom"

    # 3. Three-person image (Mom + Dad + Dhruv)
    dad_face = DetectedFace(bbox=(60, 10, 100, 50), score=0.92, assigned_person_id=2)
    dhruv_face = DetectedFace(bbox=(110, 10, 150, 50), score=0.94, assigned_person_id=3)

    three_person_dest = OrganizationRuleEngine.plan_categorization(
        faces=[mom_face, dad_face, dhruv_face],
        known_people_map=known_people_map,
    )
    # Must copy into all 3 person folders!
    assert len(three_person_dest) == 3
    folders = {d.relative_folder for d in three_person_dest}
    assert folders == {"Categorized/Mom", "Categorized/Dad", "Categorized/Dhruv"}


def test_acceptance_test_b_separation_filter_and_strict_exclusion():
    """
    Acceptance Test B:
    Target: Mom
    Collection:
    - Mom alone
    - Mom + Dad
    - Dad alone
    - Mom + several people
    Expected:
    - every image containing Mom is copied to SeparateFilter/Mom/
    - those matched images must not leak into normal categorized folders under default separation rule.
    """
    known_people_map = {1: "Mom", 2: "Dad", 3: "Friend"}
    target_ids = {1}  # Target: Mom

    mom_face = DetectedFace(bbox=(10, 10, 50, 50), score=0.95, assigned_person_id=1)
    dad_face = DetectedFace(bbox=(60, 10, 100, 50), score=0.92, assigned_person_id=2)
    friend_face = DetectedFace(bbox=(110, 10, 150, 50), score=0.90, assigned_person_id=3)

    # 1. Mom alone
    dest1, matched1 = OrganizationRuleEngine.plan_separation(
        faces=[mom_face],
        target_person_ids=target_ids,
        known_people_map=known_people_map,
        exclusive=True,
    )
    assert matched1 is True
    assert len(dest1) == 1
    assert dest1[0].relative_folder == "SeparateFilter/Mom"

    # 2. Mom + Dad
    dest2, matched2 = OrganizationRuleEngine.plan_separation(
        faces=[mom_face, dad_face],
        target_person_ids=target_ids,
        known_people_map=known_people_map,
        exclusive=True,
    )
    assert matched2 is True
    assert len(dest2) == 1
    assert dest2[0].relative_folder == "SeparateFilter/Mom"

    # 3. Dad alone (Mom NOT present)
    dest3, matched3 = OrganizationRuleEngine.plan_separation(
        faces=[dad_face],
        target_person_ids=target_ids,
        known_people_map=known_people_map,
        exclusive=True,
    )
    assert matched3 is False
    assert len(dest3) == 0

    # 4. Mom + several people
    dest4, matched4 = OrganizationRuleEngine.plan_separation(
        faces=[mom_face, dad_face, friend_face],
        target_person_ids=target_ids,
        known_people_map=known_people_map,
        exclusive=True,
    )
    assert matched4 is True
    assert len(dest4) == 1
    assert dest4[0].relative_folder == "SeparateFilter/Mom"
