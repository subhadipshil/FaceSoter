"""
Clustering module for unknown recurring face grouping.
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class FaceCluster:
    cluster_id: str          # e.g. "Person 001", "Person 002"
    face_ids: List[int]      # all face IDs assigned to this cluster
    representative_face_id: int  # medoid face ID for UI thumbnail preview
    sample_count: int
    mean_embedding: np.ndarray


class FaceClusterer:
    """Clusters unassigned face embeddings using cosine distance agglomerative grouping."""

    def __init__(self, similarity_threshold: float = 0.55):
        self.similarity_threshold = similarity_threshold

    def cluster_faces(
        self,
        face_items: List[Tuple[int, np.ndarray]],
        name_prefix: str = "Person ",
    ) -> List[FaceCluster]:
        """
        Cluster a collection of (face_id, embedding) tuples into FaceCluster objects.
        Returns a list of FaceCluster sorted by sample count (most frequent first).
        """
        if not face_items:
            return []

        face_ids = [item[0] for item in face_items]
        embeddings = np.array([item[1] for item in face_items], dtype=np.float32)

        # Normalize embeddings to unit norm
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms < 1e-6] = 1.0
        norm_embeddings = embeddings / norms

        n_samples = len(face_ids)
        if n_samples == 1:
            return [
                FaceCluster(
                    cluster_id=f"{name_prefix}001",
                    face_ids=[face_ids[0]],
                    representative_face_id=face_ids[0],
                    sample_count=1,
                    mean_embedding=norm_embeddings[0],
                )
            ]

        # Use AgglomerativeClustering with cosine distance
        try:
            from sklearn.cluster import AgglomerativeClustering
            distance_threshold = max(0.01, 1.0 - self.similarity_threshold)
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=distance_threshold,
                metric="cosine",
                linkage="average",
            )
            labels = clustering.fit_predict(norm_embeddings)
            
            label_dict: Dict[int, List[int]] = {}
            for idx, label in enumerate(labels):
                label_dict.setdefault(label, []).append(idx)
            raw_clusters = list(label_dict.values())
        except Exception:
            # Fallback graph connected components
            sim_matrix = np.dot(norm_embeddings, norm_embeddings.T)
            adj = sim_matrix >= self.similarity_threshold
            visited = np.zeros(n_samples, dtype=bool)
            raw_clusters = []
            for idx in range(n_samples):
                if visited[idx]:
                    continue
                component = []
                queue = [idx]
                visited[idx] = True
                while queue:
                    curr = queue.pop(0)
                    component.append(curr)
                    for neighbor in np.where(adj[curr])[0]:
                        if not visited[neighbor]:
                            visited[neighbor] = True
                            queue.append(neighbor)
                raw_clusters.append(component)

        # Build FaceCluster objects, sorted by size descending
        raw_clusters.sort(key=lambda c: len(c), reverse=True)
        clusters: List[FaceCluster] = []

        for i, member_indices in enumerate(raw_clusters):
            c_face_ids = [face_ids[idx] for idx in member_indices]
            c_embs = norm_embeddings[member_indices]
            
            # Find medoid (closest to cluster mean) as representative face
            mean_emb = np.mean(c_embs, axis=0)
            mean_emb_norm = mean_emb / max(np.linalg.norm(mean_emb), 1e-6)
            
            sims_to_mean = np.dot(c_embs, mean_emb_norm)
            best_idx_in_cluster = int(np.argmax(sims_to_mean))
            rep_face_id = c_face_ids[best_idx_in_cluster]

            cid = f"{name_prefix}{i + 1:03d}"
            clusters.append(
                FaceCluster(
                    cluster_id=cid,
                    face_ids=c_face_ids,
                    representative_face_id=rep_face_id,
                    sample_count=len(c_face_ids),
                    mean_embedding=mean_emb_norm,
                )
            )

        return clusters
