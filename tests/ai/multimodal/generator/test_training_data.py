"""Tests for TrainingDataGenerator."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from ai.multimodal.generator.training_data import TrainingDataGenerator
from ai.multimodal.primitives.primitive_library import PrimitiveLibrary
from ai.multimodal.primitives.primitive_types import DrawingInstructions, Point


class TestTrainingDataGeneratorInit:
    """Test initialization."""

    def test_default_init(self):
        gen = TrainingDataGenerator()
        assert gen._encoder is None
        assert gen._prim_encoder is None
        assert gen._library is None


class TestGenerateRandomPrimitives:
    """Test random primitive generation."""

    def test_returns_correct_keys(self):
        gen = TrainingDataGenerator()
        result = gen.generate_random_primitives(n_samples=5)
        assert "clip_embeddings" in result
        assert "primitive_sequences" in result

    def test_correct_count(self):
        gen = TrainingDataGenerator()
        result = gen.generate_random_primitives(n_samples=10)
        assert len(result["clip_embeddings"]) == 10
        assert len(result["primitive_sequences"]) == 10

    def test_clip_embeddings_shape(self):
        gen = TrainingDataGenerator()
        result = gen.generate_random_primitives(n_samples=5)
        for emb in result["clip_embeddings"]:
            assert emb.shape == (512,)

    def test_primitive_sequences_are_lists(self):
        gen = TrainingDataGenerator()
        result = gen.generate_random_primitives(n_samples=5)
        for seq in result["primitive_sequences"]:
            assert isinstance(seq, list)
            assert len(seq) > 0
            for prim in seq:
                assert prim.shape == (128,)


class TestGenerateSyntheticCaptions:
    """Test synthetic caption generation."""

    def test_with_empty_library(self):
        gen = TrainingDataGenerator()
        lib = PrimitiveLibrary()
        gen._library = lib
        result = gen.generate_synthetic_captions()
        assert len(result["clip_embeddings"]) == 0

    def test_with_library_no_encoder(self):
        gen = TrainingDataGenerator()
        lib = PrimitiveLibrary()
        instructions = DrawingInstructions(
            points=[Point(0.5, 0.5, (255, 0, 0), 0.1)]
        )
        emb = np.random.randn(128).astype(np.float32)
        emb = emb / (np.linalg.norm(emb) + 1e-8)
        lib.add_primitive("test", instructions, emb)
        gen._library = lib
        result = gen.generate_synthetic_captions()
        # No encoder → no results
        assert len(result["clip_embeddings"]) == 0


class TestGenerateFromCifar10:
    """Test CIFAR-10 data generation."""

    def test_with_missing_dir(self):
        gen = TrainingDataGenerator()
        result = gen.generate_from_cifar10(cifar10_dir="/nonexistent")
        assert len(result["clip_embeddings"]) == 0
