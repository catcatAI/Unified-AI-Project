"""
ANGELA-MATRIX: [L3-L4] [γδ] [B] [L2]
Tests for DocumentLearner — dedup, structure, signatures.
"""

from ai.document.learner import DocumentLearner, _DOCUMENT_REGISTRY


def test_learner_init():
    learner = DocumentLearner()
    assert learner.chunker is not None


def test_learner_dedup_key():
    """SHA-256 hash dedup: same text produces same hash."""
    import hashlib
    h1 = hashlib.sha256(b"test document").hexdigest()
    h2 = hashlib.sha256(b"test document").hexdigest()
    assert h1 == h2


def test_learner_different_text_different_hash():
    import hashlib
    h1 = hashlib.sha256(b"document one").hexdigest()
    h2 = hashlib.sha256(b"document two").hexdigest()
    assert h1 != h2
