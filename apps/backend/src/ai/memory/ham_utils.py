# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import numpy as np

# Default English stopwords
stopwords = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "will",
    "with",
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "him",
    "his",
    "she",
    "her",
    "hers",
    "herself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "this",
    "these",
    "those",
}


def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculates the cosine similarity between two vectors."""
    if vec1.ndim != 1 or vec2.ndim != 1:
        raise ValueError("Expected 1D arrays")
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def generate_embedding(text: str) -> np.ndarray:
    """Generates a character bigram embedding for the given text (stdlib-only)."""
    # Same hashing trick as vector_store._NumpyBackend._embed
    text = text.lower().strip()
    vec = np.zeros(384, dtype=np.float32)
    if len(text) < 2:
        return vec
    seen = set()
    for i in range(len(text) - 1):
        bg = text[i : i + 2]
        if bg not in seen:
            seen.add(bg)
            idx = hash(bg) % 384
            vec[idx] += 1.0
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def get_current_utc_timestamp() -> float:
    """Returns the current UTC timestamp as a float."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).timestamp()


def is_valid_uuid(uuid_to_test: str, version: int = 4) -> bool:
    """Checks if a string is a valid UUID."""
    import uuid

    try:
        val = uuid.UUID(uuid_to_test, version=version)
        return str(val) == uuid_to_test
    except (ValueError, AttributeError):
        return False
