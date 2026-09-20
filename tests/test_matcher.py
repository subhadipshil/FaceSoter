"""
Unit tests for cosine similarity matcher and multi-reference aggregator.
"""

import numpy as np
import pytest
from facesoter.core.ai.matcher import FaceMatcher


def test_cosine_similarity():
    # Identical vectors
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    assert pytest.approx(FaceMatcher.cosine_similarity(v1, v1), 1e-5) == 1.0

    # Orthogonal vectors
    v2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    assert pytest.approx(FaceMatcher.cosine_similarity(v1, v2), 1e-5) == 0.0

    # Opposite vectors
    v3 = np.array([-1.0, 0.0, 0.0], dtype=np.float32)
    assert pytest.approx(FaceMatcher.cosine_similarity(v1, v3), 1e-5) == -1.0


def test_multi_reference_scoring():
    matcher_max = FaceMatcher(threshold=0.50, aggregation="max")
    matcher_top = FaceMatcher(threshold=0.50, aggregation="top3_avg")

    query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    # References with similarities 0.9, 0.7, 0.2
    refs = [
        np.array([0.9, 0.4358, 0.0], dtype=np.float32),  # dot ~ 0.9
        np.array([0.7, 0.7141, 0.0], dtype=np.float32),  # dot ~ 0.7
        np.array([0.2, 0.9797, 0.0], dtype=np.float32),  # dot ~ 0.2
    ]

    score_max = matcher_max.score_person(query, refs)
    assert pytest.approx(score_max, 1e-3) == 0.9

    score_top = matcher_top.score_person(query, refs)
    assert pytest.approx(score_top, 1e-3) == (0.9 + 0.7 + 0.2) / 3.0


def test_find_best_match():
    matcher = FaceMatcher(threshold=0.60)

    p1_emb = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    p2_emb = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)

    known_people = {
        101: [p1_emb],
        102: [p2_emb],
    }

    # Query close to p1 (similarity ~0.95)
    q1 = np.array([0.95, 0.0, 0.312, 0.0], dtype=np.float32)
    matched_id, score = matcher.find_best_match(q1, known_people)
    assert matched_id == 101
    assert score > 0.60

    # Query not matching anyone (below threshold)
    q_unknown = np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32)
    matched_id, score = matcher.find_best_match(q_unknown, known_people)
    assert matched_id is None
    assert score < 0.60
