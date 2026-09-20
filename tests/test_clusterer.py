"""
Unit tests for unknown face clustering algorithm.
"""

import numpy as np
import pytest
from facesoter.core.ai.clusterer import FaceClusterer


def test_clustering_unknown_faces():
    """Test clustering embeddings from two distinct identities."""
    clusterer = FaceClusterer(similarity_threshold=0.60)

    np.random.seed(42)

    # Base identity 1
    base_1 = np.random.randn(512).astype(np.float32)
    base_1 /= np.linalg.norm(base_1)

    # Base identity 2 (orthogonal)
    base_2 = np.random.randn(512).astype(np.float32)
    base_2 -= np.dot(base_1, base_2) * base_1
    base_2 /= np.linalg.norm(base_2)

    # Generate 10 samples of Person 1 with small noise (cosine sim ~ 0.85-0.95)
    person_1_samples = []
    for i in range(10):
        noise = np.random.randn(512).astype(np.float32) * 0.02
        emb = base_1 + noise
        emb /= np.linalg.norm(emb)
        person_1_samples.append((i + 1, emb))

    # Generate 5 samples of Person 2 with small noise
    person_2_samples = []
    for i in range(5):
        noise = np.random.randn(512).astype(np.float32) * 0.02
        emb = base_2 + noise
        emb /= np.linalg.norm(emb)
        person_2_samples.append((i + 11, emb))

    all_samples = person_1_samples + person_2_samples

    clusters = clusterer.cluster_faces(all_samples)

    # Must produce exactly 2 clusters
    assert len(clusters) == 2

    # First cluster should have 10 samples, second 5
    assert clusters[0].sample_count == 10
    assert clusters[1].sample_count == 5

    # Check member IDs
    c1_ids = set(clusters[0].face_ids)
    c2_ids = set(clusters[1].face_ids)

    assert c1_ids == {i + 1 for i in range(10)}
    assert c2_ids == {i + 11 for i in range(5)}

    # Representative face should be within the cluster
    assert clusters[0].representative_face_id in c1_ids
    assert clusters[1].representative_face_id in c2_ids
