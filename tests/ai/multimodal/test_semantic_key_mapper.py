"""
P44 tests for SemanticKeyMapper — bridges semantic latent vectors to ED3N concept keys.

Tests cover:
1. Basic indexing and querying (4)
2. Router result integration (2)
3. Batch indexing (1)
4. Edge cases (3)
"""

import numpy as np
import pytest

from ai.multimodal.semantic_key_mapper import SemanticKeyMapper


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def mapper():
    return SemanticKeyMapper(max_entries=100)


@pytest.fixture
def seeded_mapper():
    """Mapper with 5 pre-indexed concept keys."""
    m = SemanticKeyMapper(max_entries=100)
    rng = np.random.default_rng(42)
    for i, key in enumerate(["chicken", "bird", "cat", "dog", "fish"]):
        sem = rng.normal(i * 0.5, 0.1, 64).astype(np.float32)
        struct = rng.normal(i * 0.3, 0.2, 64).astype(np.float32)
        m.index_key(key, struct, sem)
    return m


# =========================================================================
# 1. Basic Indexing and Querying (4 tests)
# =========================================================================

class TestBasicIndexQuery:
    """P44a: Basic SemanticKeyMapper operations."""

    def test_empty_mapper_returns_empty(self, mapper):
        """S1: querying empty mapper returns empty list."""
        latent = np.random.randn(64).astype(np.float32)
        results = mapper.map_latent_to_keys(latent)
        assert results == []

    def test_index_and_query(self, seeded_mapper):
        """S2: indexing a key and querying with similar latent finds it."""
        # Query with a latent close to "chicken"'s semantic vector
        chicken_sem = seeded_mapper._semantic_latents[0]
        results = seeded_mapper.map_latent_to_keys(chicken_sem, top_k=1, mode="semantic")
        assert len(results) >= 1
        assert results[0]["key"] == "chicken"
        assert results[0]["score"] > 0.5

    def test_top_k_ordering(self, seeded_mapper):
        """S3: results are ordered by descending similarity."""
        # Query with chicken's semantic vector
        chicken_sem = seeded_mapper._semantic_latents[0]
        results = seeded_mapper.map_latent_to_keys(chicken_sem, top_k=3, mode="semantic")
        assert len(results) <= 3
        # Scores should be descending
        scores = [r["score"] for r in results]
        assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))

    def test_use_structural_fallback(self, seeded_mapper):
        """S4: use_semantic=False falls back to structural latents."""
        chicken_struct = seeded_mapper._structural_latents[0]
        results = seeded_mapper.map_latent_to_keys(chicken_struct, top_k=1, mode="structural")
        assert len(results) >= 1
        assert results[0]["key"] == "chicken"


# =========================================================================
# 2. Router Result Integration (2 tests)
# =========================================================================

class TestRouterIntegration:
    """P44b: index_from_router_result extracts latents from router dict."""

    def test_index_from_router_result(self, mapper):
        """R1: extracts structural_latent, semantic_latent, combined from dict."""
        router_result = {
            "structural_latent": np.ones(64, dtype=np.float32),
            "semantic_latent": np.ones(64, dtype=np.float32) * 2,
            "latent": np.ones(64, dtype=np.float32) * 3,
        }
        mapper.index_from_router_result("test_key", router_result)
        assert mapper.count == 1
        assert mapper._keys[0] == "test_key"
        assert np.allclose(mapper._structural_latents[0], 1.0)
        assert np.allclose(mapper._semantic_latents[0], 2.0)
        assert np.allclose(mapper._combined_latents[0], 3.0)

    def test_query_after_router_index(self, mapper):
        """R2: query works after indexing from router result."""
        router_result = {
            "structural_latent": np.ones(64, dtype=np.float32),
            "semantic_latent": np.ones(64, dtype=np.float32),
            "latent": np.ones(64, dtype=np.float32),
        }
        mapper.index_from_router_result("target", router_result)
        # Query with same latent (use combined mode since router_result has combined)
        results = mapper.map_latent_to_keys(np.ones(64, dtype=np.float32), top_k=1, mode="combined")
        assert len(results) == 1
        assert results[0]["key"] == "target"


# =========================================================================
# 3. Batch Indexing (1 test)
# =========================================================================

class TestBatchIndex:
    """P44c: index_batch indexes multiple entries."""

    def test_batch_index(self, mapper):
        """B1: index_batch returns correct count."""
        entries = [
            ("k1", np.ones(64, dtype=np.float32), np.ones(64, dtype=np.float32) * 2, None),
            ("k2", np.ones(64, dtype=np.float32) * 3, None, None),
        ]
        count = mapper.index_batch(entries)
        assert count == 2
        assert mapper.count == 2
        assert mapper._keys == ["k1", "k2"]


# =========================================================================
# 4. Edge Cases (3 tests)
# =========================================================================

class TestEdgeCases:
    """P44d: Edge cases and error handling."""

    def test_index_without_latents(self, mapper):
        """E1: index_key with no latents does nothing."""
        mapper.index_key("orphan", None, None)
        assert mapper.count == 0

    def test_duplicate_key_updates(self, mapper):
        """E2: re-indexing same key updates its latents."""
        mapper.index_key("dup", np.ones(64, dtype=np.float32), np.ones(64, dtype=np.float32))
        assert mapper.count == 1
        # Update with new latents
        mapper.index_key("dup", np.ones(64, dtype=np.float32) * 5, np.ones(64, dtype=np.float32) * 6)
        assert mapper.count == 1  # Still 1 entry
        assert np.allclose(mapper._structural_latents[0], 5.0)  # Updated
        assert np.allclose(mapper._semantic_latents[0], 6.0)

    def test_max_entries_eviction(self):
        """E3: exceeding max_entries drops oldest."""
        m = SemanticKeyMapper(max_entries=3)
        for i in range(5):
            m.index_key(f"key{i}", np.ones(64, dtype=np.float32) * i,
                        np.ones(64, dtype=np.float32) * i)
        assert m.count == 3
        # Oldest (key0, key1) should be gone
        assert m._keys == ["key2", "key3", "key4"]

    def test_clear_empties_mapper(self, mapper):
        """E4: clear() resets all state."""
        mapper.index_key("k", np.ones(64), np.ones(64))
        assert mapper.count == 1
        mapper.clear()
        assert mapper.count == 0
        assert mapper._keys == []

    def test_keys_property(self, seeded_mapper):
        """E5: .keys returns a copy of key list."""
        k = seeded_mapper.keys
        assert k == ["chicken", "bird", "cat", "dog", "fish"]
        # Modifying the returned list shouldn't affect the mapper
        k.append("new_key")
        assert seeded_mapper.count == 5

    def test_index_from_dictionary_no_data(self, mapper):
        """E6: index_from_dictionary with empty dict does nothing."""
        class MockDict:
            entries = {}
        count = mapper.index_from_dictionary(MockDict(), None)
        assert count == 0
