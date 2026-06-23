"""Tests for ConceptMapper."""

import numpy as np
import pytest
import tempfile
import os

from ai.multimodal.primitives.concept_mapper import ConceptMapper
from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
from ai.multimodal.primitives.primitive_types import TOTAL_DIM


def make_test_vocabulary():
    """Create a test vocabulary with synthetic data."""
    np.random.seed(42)
    n_images = 30
    n_classes = 3
    params = np.random.rand(n_images, TOTAL_DIM).astype(np.float32)
    labels = np.random.randint(0, n_classes, size=n_images)

    vocab = GeometricVocabulary(n_visual_words=5)
    vocab.build_from_optimized(params, labels, ["cat", "dog", "bird"])
    return vocab


class TestConceptMapper:
    def test_create_mapper(self):
        vocab = make_test_vocabulary()
        mapper = ConceptMapper(vocab)
        assert len(mapper._concept_clip_embeddings) == 0

    def test_register_concept_embedding(self):
        vocab = make_test_vocabulary()
        mapper = ConceptMapper(vocab)

        emb = np.random.rand(512).astype(np.float32)
        mapper.register_concept_embedding("cat", emb)

        assert "cat" in mapper._concept_clip_embeddings
        np.testing.assert_array_equal(mapper._concept_clip_embeddings["cat"], emb)

    def test_map_text_to_concept(self):
        vocab = make_test_vocabulary()
        mapper = ConceptMapper(vocab)

        # Register embeddings
        rng = np.random.default_rng(42)
        for cls in ["cat", "dog", "bird"]:
            mapper.register_concept_embedding(cls, rng.random(512).astype(np.float32))

        # Map a query
        query = rng.random(512).astype(np.float32)
        results = mapper.map_text_to_concept(query, top_k=2)

        assert len(results) == 2
        assert all(isinstance(name, str) for name, _ in results)
        assert all(0 <= sim <= 1 for _, sim in results)

    def test_map_text_to_primitives(self):
        vocab = make_test_vocabulary()
        mapper = ConceptMapper(vocab)

        rng = np.random.default_rng(42)
        for cls in ["cat", "dog", "bird"]:
            mapper.register_concept_embedding(cls, rng.random(512).astype(np.float32))

        query = rng.random(512).astype(np.float32)
        result = mapper.map_text_to_primitives(query)

        assert "concept" in result
        assert "initialization" in result
        assert len(result["initialization"]) == TOTAL_DIM
        assert result["initialization"].min() >= 0.0
        assert result["initialization"].max() <= 1.0

    def test_save_and_load(self):
        vocab = make_test_vocabulary()
        mapper = ConceptMapper(vocab)

        rng = np.random.default_rng(42)
        for cls in ["cat", "dog", "bird"]:
            mapper.register_concept_embedding(cls, rng.random(512).astype(np.float32))

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "mapper.json")
            mapper.save(path)

            loaded = ConceptMapper.load(vocab, path)
            assert len(loaded._concept_clip_embeddings) == 3
            assert "cat" in loaded._concept_clip_embeddings
