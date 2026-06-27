"""Tests for InstanceOptimizer."""

import numpy as np
import pytest
from ai.multimodal.primitives.concept_mapper import ConceptMapper
from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
from ai.multimodal.primitives.instance_optimizer import InstanceOptimizer
from ai.multimodal.primitives.primitive_types import TOTAL_DIM


def make_test_vocabulary_and_mapper():
    """Create test vocabulary and mapper."""
    np.random.seed(42)
    n_images = 30
    n_classes = 3
    params = np.random.rand(n_images, TOTAL_DIM).astype(np.float32)
    labels = np.random.randint(0, n_classes, size=n_images)

    vocab = GeometricVocabulary(n_visual_words=5)
    vocab.build_from_optimized(params, labels, ["cat", "dog", "bird"])

    mapper = ConceptMapper(vocab)
    rng = np.random.default_rng(42)
    for cls in ["cat", "dog", "bird"]:
        mapper.register_concept_embedding(cls, rng.random(512).astype(np.float32))

    return vocab, mapper


class TestInstanceOptimizer:
    def test_create_optimizer(self):
        vocab, mapper = make_test_vocabulary_and_mapper()
        optimizer = InstanceOptimizer(vocab, mapper)
        assert optimizer._vocabulary is vocab
        assert optimizer._concept_mapper is mapper

    def test_optimize_for_image(self):
        vocab, mapper = make_test_vocabulary_and_mapper()
        optimizer = InstanceOptimizer(vocab, mapper)

        # Create a simple test image
        target = np.random.rand(128, 128, 3).astype(np.float32)

        result = optimizer.optimize_for_image(
            target, concept_name="cat",
            n_iterations=3, n_probes=3
        )

        assert "vector" in result
        assert "rendered" in result
        assert "loss" in result
        assert len(result["vector"]) == TOTAL_DIM
        assert result["loss"] >= 0

    def test_optimize_for_image_auto_concept(self):
        vocab, mapper = make_test_vocabulary_and_mapper()
        optimizer = InstanceOptimizer(vocab, mapper)

        target = np.random.rand(128, 128, 3).astype(np.float32)

        result = optimizer.optimize_for_image(
            target, concept_name=None,
            n_iterations=3, n_probes=3
        )

        assert "vector" in result
        assert result["loss"] >= 0

    def test_rendered_image_size(self):
        vocab, mapper = make_test_vocabulary_and_mapper()
        optimizer = InstanceOptimizer(vocab, mapper, canvas_size=(64, 64))

        target = np.random.rand(64, 64, 3).astype(np.float32)

        result = optimizer.optimize_for_image(
            target, n_iterations=2, n_probes=2
        )

        rendered = result["rendered"]
        assert rendered.size == (64, 64)
