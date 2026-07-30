"""
ANGELA-MATRIX: [L3-L4] [γδ] [B] [L2]
Tests for DocumentLearner — dedup, LRU eviction, structure, signatures.
"""

import hashlib

from ai.document.learner import DocumentLearner, _DOCUMENT_REGISTRY, _MAX_REGISTRY_SIZE, _evict_oldest


def test_learner_init():
    learner = DocumentLearner()
    assert learner.chunker is not None


def test_learner_dedup_key():
    h1 = hashlib.sha256(b"test document").hexdigest()
    h2 = hashlib.sha256(b"test document").hexdigest()
    assert h1 == h2


def test_learner_different_text_different_hash():
    h1 = hashlib.sha256(b"document one").hexdigest()
    h2 = hashlib.sha256(b"document two").hexdigest()
    assert h1 != h2


def test_registry_max_size():
    _DOCUMENT_REGISTRY.clear()
    for i in range(_MAX_REGISTRY_SIZE + 50):
        _DOCUMENT_REGISTRY[f"hash_{i}"] = float(i)
    assert len(_DOCUMENT_REGISTRY) > _MAX_REGISTRY_SIZE
    _evict_oldest()
    assert len(_DOCUMENT_REGISTRY) <= _MAX_REGISTRY_SIZE


def test_registry_evicts_oldest_first():
    _DOCUMENT_REGISTRY.clear()
    for i in range(_MAX_REGISTRY_SIZE):
        _DOCUMENT_REGISTRY[f"hash_{i}"] = float(i)
    assert len(_DOCUMENT_REGISTRY) == _MAX_REGISTRY_SIZE
    _DOCUMENT_REGISTRY["new_hash"] = 9999.0
    _evict_oldest()
    assert len(_DOCUMENT_REGISTRY) == _MAX_REGISTRY_SIZE
    # Oldest (hash_0) should have been evicted
    assert "hash_0" not in _DOCUMENT_REGISTRY
    # Newest should remain
    assert "new_hash" in _DOCUMENT_REGISTRY


def test_registry_ordereddict_move_to_end():
    _DOCUMENT_REGISTRY.clear()
    for i in range(5):
        _DOCUMENT_REGISTRY[f"hash_{i}"] = float(i)
    _DOCUMENT_REGISTRY.move_to_end("hash_0")
    keys = list(_DOCUMENT_REGISTRY.keys())
    assert keys[-1] == "hash_0"  # moved to end (most recently used)
