"""
Rule engine for Categorization and Separation/Filter organization modes.
"""

from __future__ import annotations
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from facesoter.core.ai.provider import DetectedFace


@dataclass
class PlannedDestination:
    """Represents a planned destination for an image."""
    category_name: str          # e.g. "Mom", "Person 001", "No Face"
    relative_folder: str        # e.g. "Categorized/Mom", "Uncategorized/No Face", "SeparateFilter/Mom"
    is_filtered_target: bool = False


class OrganizationRuleEngine:
    """Enforces mode-specific rules including multi-face duplication and strict separation exclusion."""

    @staticmethod
    def plan_categorization(
        faces: List[DetectedFace],
        known_people_map: Dict[int, str],  # person_id -> display_name
        auto_create_unknown: bool = True,
    ) -> List[PlannedDestination]:
        """
        Mode A: Categorization planning.
        - If 0 faces: routed to 'Uncategorized/No Face'
        - If >=1 faces: original image copied into EVERY unique identified person's folder.
        """
        if not faces:
            return [
                PlannedDestination(
                    category_name="No Face",
                    relative_folder="Uncategorized/No Face",
                    is_filtered_target=False,
                )
            ]

        destinations: List[PlannedDestination] = []
        seen_categories: Set[str] = set()

        for face in faces:
            category_name: Optional[str] = None

            if face.assigned_person_id is not None and face.assigned_person_id in known_people_map:
                category_name = known_people_map[face.assigned_person_id]
            elif face.assigned_cluster_id:
                if auto_create_unknown:
                    category_name = face.assigned_cluster_id

            if category_name and category_name not in seen_categories:
                seen_categories.add(category_name)
                destinations.append(
                    PlannedDestination(
                        category_name=category_name,
                        relative_folder=f"Categorized/{category_name}",
                        is_filtered_target=False,
                    )
                )

        # Fallback if faces exist but none could be categorized or clustered
        if not destinations:
            destinations.append(
                PlannedDestination(
                    category_name="Unknown",
                    relative_folder="Categorized/Unknown",
                    is_filtered_target=False,
                )
            )

        return destinations

    @staticmethod
    def plan_separation(
        faces: List[DetectedFace],
        target_person_ids: Set[int],
        known_people_map: Dict[int, str],
        exclusive: bool = True,
    ) -> Tuple[List[PlannedDestination], bool]:
        """
        Mode B: Separation / Filter planning.
        - If image contains ANY selected target person:
          - Image is routed to SeparateFilter/<TargetName>
          - Returns (destinations, is_matched)
          - If exclusive is True, the matched photo MUST NOT be processed for normal categorization!
        """
        destinations: List[PlannedDestination] = []
        seen_targets: Set[str] = set()

        for face in faces:
            if face.assigned_person_id is not None and face.assigned_person_id in target_person_ids:
                name = known_people_map.get(face.assigned_person_id, f"Person_{face.assigned_person_id}")
                if name not in seen_targets:
                    seen_targets.add(name)
                    destinations.append(
                        PlannedDestination(
                            category_name=name,
                            relative_folder=f"SeparateFilter/{name}",
                            is_filtered_target=True,
                        )
                    )

        is_matched = len(destinations) > 0
        return destinations, is_matched
