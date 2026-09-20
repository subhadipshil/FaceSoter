"""
Cosine similarity and multi-reference face matching module.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple
import numpy as np


class FaceMatcher:
    """Calculates cosine similarity and matches query embeddings to known person profiles."""

    def __init__(
        self,
        threshold: float = 0.50,
        aggregation: str = "max",  # "max" or "top3_avg"
    ):
        self.threshold = threshold
        self.aggregation = aggregation

    @staticmethod
    def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between two 1D normalized embeddings."""
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 < 1e-6 or norm2 < 1e-6:
            return 0.0
        return float(np.dot(emb1, emb2) / (norm1 * norm2))

    @staticmethod
    def compute_similarity_matrix(query_embs: np.ndarray, ref_embs: np.ndarray) -> np.ndarray:
        """
        Matrix cosine similarity between N query embeddings and M reference embeddings.
        Input shapes: (N, 512), (M, 512)
        Output shape: (N, M)
        """
        q_norm = np.linalg.norm(query_embs, axis=1, keepdims=True)
        r_norm = np.linalg.norm(ref_embs, axis=1, keepdims=True)
        q_norm[q_norm < 1e-6] = 1.0
        r_norm[r_norm < 1e-6] = 1.0
        q_unit = query_embs / q_norm
        r_unit = ref_embs / r_norm
        return np.dot(q_unit, r_unit.T)

    def score_person(
        self,
        query_emb: np.ndarray,
        reference_embs: List[np.ndarray],
    ) -> float:
        """Compute match score against a person's enrolled reference embeddings."""
        if not reference_embs:
            return 0.0

        scores = [self.cosine_similarity(query_emb, ref) for ref in reference_embs]
        if self.aggregation == "top3_avg" and len(scores) > 1:
            scores.sort(reverse=True)
            top_k = scores[:min(3, len(scores))]
            return float(np.mean(top_k))
        return float(max(scores))

    def find_best_match(
        self,
        query_emb: np.ndarray,
        known_people: Dict[int, List[np.ndarray]],
        custom_threshold: Optional[float] = None,
    ) -> Tuple[Optional[int], float]:
        """
        Find the best matching person profile for a query embedding.
        Returns: (matched_person_id, confidence_score). If no match >= threshold, person_id is None.
        """
        thresh = custom_threshold if custom_threshold is not None else self.threshold
        best_person_id: Optional[int] = None
        best_score = -1.0

        for person_id, ref_embs in known_people.items():
            if not ref_embs:
                continue
            score = self.score_person(query_emb, ref_embs)
            if score > best_score:
                best_score = score
                best_person_id = person_id

        if best_score >= thresh:
            return best_person_id, best_score
        return None, best_score

    def matches_target(
        self,
        query_emb: np.ndarray,
        target_reference_embs: List[np.ndarray],
        custom_threshold: Optional[float] = None,
    ) -> Tuple[bool, float]:
        """Check if query embedding matches a specific target person."""
        thresh = custom_threshold if custom_threshold is not None else self.threshold
        score = self.score_person(query_emb, target_reference_embs)
        return (score >= thresh), score
