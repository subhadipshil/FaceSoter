"""
Unit tests for Single & Group Photo Separator rule engine planning.
"""

import pytest
from facesoter.core.ai.provider import DetectedFace
from facesoter.core.organizer.rule_engine import OrganizationRuleEngine, PlannedDestination


def test_single_group_no_face():
    """Verify that images with 0 detected faces route to No_Face when enabled, or are skipped when disabled."""
    # 1. include_no_face=True (default)
    dest1 = OrganizationRuleEngine.plan_single_group(
        faces=[],
        single_folder="Single_Photos",
        group_folder="Group_Photos",
        no_face_folder="No_Face",
        include_no_face=True,
    )
    assert len(dest1) == 1
    assert dest1[0].relative_folder == "No_Face"
    assert dest1[0].category_name == "No Face"

    # 2. include_no_face=False
    dest2 = OrganizationRuleEngine.plan_single_group(
        faces=[],
        single_folder="Single_Photos",
        group_folder="Group_Photos",
        no_face_folder="No_Face",
        include_no_face=False,
    )
    assert len(dest2) == 0


def test_single_group_single_photo():
    """Verify that an image with 1 detected face routes to Single_Photos."""
    face = DetectedFace(bbox=(10, 10, 50, 50), score=0.95)
    dest = OrganizationRuleEngine.plan_single_group(
        faces=[face],
        single_folder="Single_Photos",
        group_folder="Group_Photos",
        min_group_count=2,
    )
    assert len(dest) == 1
    assert dest[0].relative_folder == "Single_Photos"
    assert dest[0].category_name == "Single"


def test_single_group_group_photo():
    """Verify that an image with >=2 detected faces routes to Group_Photos."""
    face1 = DetectedFace(bbox=(10, 10, 50, 50), score=0.95)
    face2 = DetectedFace(bbox=(60, 10, 100, 50), score=0.92)
    face3 = DetectedFace(bbox=(110, 10, 150, 50), score=0.90)

    # 2 faces
    dest2 = OrganizationRuleEngine.plan_single_group(
        faces=[face1, face2],
        single_folder="Single_Photos",
        group_folder="Group_Photos",
        min_group_count=2,
    )
    assert len(dest2) == 1
    assert dest2[0].relative_folder == "Group_Photos"
    assert dest2[0].category_name == "Group"

    # 3 faces
    dest3 = OrganizationRuleEngine.plan_single_group(
        faces=[face1, face2, face3],
        single_folder="Single_Photos",
        group_folder="Group_Photos",
        min_group_count=2,
    )
    assert len(dest3) == 1
    assert dest3[0].relative_folder == "Group_Photos"
    assert dest3[0].category_name == "Group"


def test_single_group_custom_parameters():
    """Verify custom folder names and threshold."""
    face1 = DetectedFace(bbox=(10, 10, 50, 50), score=0.95)
    face2 = DetectedFace(bbox=(60, 10, 100, 50), score=0.92)

    # With min_group_count=3, 2 faces should be considered Single (or sub-group)
    dest = OrganizationRuleEngine.plan_single_group(
        faces=[face1, face2],
        single_folder="Solo_Portraits",
        group_folder="Family_Gatherings",
        no_face_folder="Landscape_Art",
        min_group_count=3,
    )
    assert len(dest) == 1
    assert dest[0].relative_folder == "Solo_Portraits"
    assert dest[0].category_name == "Single"
