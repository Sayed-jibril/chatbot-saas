"""
Similarity calculation functions for vector embeddings.
"""

import numpy as np
from typing import List, Union, Optional
import json


def cosine_similarity(vec1: Union[List[float], np.ndarray],
                      vec2: Union[List[float], np.ndarray]) -> float:
    """
    Calculate cosine similarity between two vectors.
    """
    if isinstance(vec1, list):
        vec1 = np.array(vec1)
    if isinstance(vec2, list):
        vec2 = np.array(vec2)

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = dot_product / (norm1 * norm2)
    return max(-1.0, min(1.0, float(similarity)))


def batch_cosine_similarity(query_vector: Union[List[float], np.ndarray],
                            candidate_vectors: List[Union[List[float], np.ndarray]]) -> List[float]:
    """Calculate cosine similarity between query and multiple candidates"""
    if isinstance(query_vector, list):
        query_vector = np.array(query_vector)

    query_norm = np.linalg.norm(query_vector)
    if query_norm > 0:
        query_vector = query_vector / query_norm

    similarities = []
    for cand in candidate_vectors:
        if isinstance(cand, list):
            cand = np.array(cand)

        cand_norm = np.linalg.norm(cand)
        if cand_norm > 0:
            cand = cand / cand_norm

        similarity = np.dot(query_vector, cand)
        similarities.append(float(similarity))

    return similarities


def find_most_similar(query_vector: Union[List[float], np.ndarray],
                      candidate_vectors: List[Union[List[float], np.ndarray]],
                      top_k: int = 5) -> List[tuple]:
    """Find most similar vectors"""
    similarities = batch_cosine_similarity(query_vector, candidate_vectors)
    indexed_similarities = list(enumerate(similarities))
    indexed_similarities.sort(key=lambda x: x[1], reverse=True)
    return indexed_similarities[:top_k]
