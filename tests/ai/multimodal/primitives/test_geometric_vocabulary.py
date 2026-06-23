"""Tests for GeometricVocabulary."""

import numpy as np
import pytest
import tempfile
import os

from ai.multimodal.primitives.geometric_vocabulary import (
    GeometricVocabulary, VisualWord, ConceptDistribution
)
from ai.multimodal.primitives.primitive_types import TOTAL_DIM


class TestVisualWord:
    def test_create_visual_word(self):
        center = np.random.rand(TOTAL_DIM).astype(np.float32)
        vw = VisualWord(word_id=0, center=center, count=10)
        assert vw.word_id == 0
        assert vw.count == 10
        assert len(vw.center) == TOTAL_DIM

    def test_to_dict_and_from_dict(self):
        center = np.random.rand(TOTAL_DIM).astype(np.float32)
        vw = VisualWord(word_id=1, center=center, count=5,
                        primitive_signature={"n_circles": 2})
        d = vw.to_dict()
        vw2 = VisualWord.from_dict(d)
        assert vw2.word_id == 1
        assert vw2.count == 5
        np.testing.assert_array_almost_equal(vw2.center, center)


class TestConceptDistribution:
    def test_create_concept(self):
        cd = ConceptDistribution(
            concept_name="cat",
            label=3,
            visual_word_ids=[0, 1, 2],
            word_frequencies=np.array([0.3, 0.4, 0.3], dtype=np.float32),
            param_means=np.ones(TOTAL_DIM, dtype=np.float32) * 0.5,
            param_stds=np.ones(TOTAL_DIM, dtype=np.float32) * 0.1,
            n_images=10,
        )
        assert cd.concept_name == "cat"
        assert cd.label == 3
        assert cd.n_images == 10

    def test_to_dict_and_from_dict(self):
        cd = ConceptDistribution(
            concept_name="dog",
            label=5,
            visual_word_ids=[0, 1],
            word_frequencies=np.array([0.6, 0.4], dtype=np.float32),
            param_means=np.ones(TOTAL_DIM, dtype=np.float32) * 0.5,
            param_stds=np.ones(TOTAL_DIM, dtype=np.float32) * 0.1,
            n_images=8,
        )
        d = cd.to_dict()
        cd2 = ConceptDistribution.from_dict(d)
        assert cd2.concept_name == "dog"
        assert cd2.label == 5
        np.testing.assert_array_almost_equal(cd2.word_frequencies, cd.word_frequencies)


class TestGeometricVocabulary:
    def test_create_empty(self):
        vocab = GeometricVocabulary(n_visual_words=10)
        assert len(vocab.get_visual_words()) == 0
        assert len(vocab._concept_distributions) == 0

    def test_build_from_optimized(self):
        # Create synthetic data: 50 vectors, 5 classes
        np.random.seed(42)
        n_images = 50
        n_classes = 5
        params = np.random.rand(n_images, TOTAL_DIM).astype(np.float32)
        labels = np.random.randint(0, n_classes, size=n_images)

        vocab = GeometricVocabulary(n_visual_words=10)
        vocab.build_from_optimized(params, labels,
                                   [f"class_{i}" for i in range(n_classes)])

        # Check visual words were created
        assert len(vocab.get_visual_words()) > 0
        assert len(vocab.get_visual_words()) <= 10

        # Check concept distributions were created
        for i in range(n_classes):
            name = f"class_{i}"
            cd = vocab.get_concept(name)
            assert cd is not None
            assert cd.n_images > 0

    def test_find_nearest_word(self):
        np.random.seed(42)
        params = np.random.rand(20, TOTAL_DIM).astype(np.float32)
        labels = np.random.randint(0, 3, size=20)

        vocab = GeometricVocabulary(n_visual_words=5)
        vocab.build_from_optimized(params, labels, ["a", "b", "c"])

        # Find nearest word to a random vector
        query = np.random.rand(TOTAL_DIM).astype(np.float32)
        word_id, dist = vocab.find_nearest_word(query)
        assert word_id >= 0
        assert dist >= 0

    def test_initialize_from_concept(self):
        np.random.seed(42)
        params = np.random.rand(20, TOTAL_DIM).astype(np.float32)
        labels = np.random.randint(0, 3, size=20)

        vocab = GeometricVocabulary(n_visual_words=5)
        vocab.build_from_optimized(params, labels, ["a", "b", "c"])

        # Initialize from a concept
        vec = vocab.initialize_from_concept("a")
        assert len(vec) == TOTAL_DIM
        assert vec.min() >= 0.0
        assert vec.max() <= 1.0

    def test_save_and_load(self):
        np.random.seed(42)
        params = np.random.rand(20, TOTAL_DIM).astype(np.float32)
        labels = np.random.randint(0, 3, size=20)

        vocab = GeometricVocabulary(n_visual_words=5)
        vocab.build_from_optimized(params, labels, ["a", "b", "c"])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "vocab.json")
            vocab.save(path)

            loaded = GeometricVocabulary.load(path)
            assert len(loaded.get_visual_words()) == len(vocab.get_visual_words())
            assert len(loaded._concept_distributions) == len(vocab._concept_distributions)

    def test_primitive_signature(self):
        np.random.seed(42)
        params = np.random.rand(20, TOTAL_DIM).astype(np.float32)
        labels = np.random.randint(0, 3, size=20)

        vocab = GeometricVocabulary(n_visual_words=5)
        vocab.build_from_optimized(params, labels, ["a", "b", "c"])

        # Check that visual words have signatures
        for vw in vocab.get_visual_words():
            assert "n_points" in vw.primitive_signature
            assert "n_circles" in vw.primitive_signature
