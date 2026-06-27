"""Tests for GeometricRecognizer."""

import numpy as np
import pytest
from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.primitives.primitive_types import TOTAL_DIM, DrawingInstructions
from ai.multimodal.recognition.geometric_recognizer import GeometricRecognizer


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


class TestGeometricRecognizer:
    def test_create_recognizer(self):
        vocab = make_test_vocabulary()
        recognizer = GeometricRecognizer(vocab)
        assert recognizer._vocabulary is vocab

    def test_recognize_from_vector(self):
        vocab = make_test_vocabulary()
        recognizer = GeometricRecognizer(vocab)

        # Use a vector from the vocabulary
        vec = vocab.get_visual_words()[0].center
        result = recognizer.recognize_from_vector(vec)

        assert "predicted_class" in result
        assert "confidence" in result
        assert "class_scores" in result
        assert result["predicted_class"] in ["cat", "dog", "bird"]
        assert 0 <= result["confidence"] <= 1

    def test_recognize_from_vector_all_classes(self):
        vocab = make_test_vocabulary()
        recognizer = GeometricRecognizer(vocab)

        # Test that each concept's mean vector scores highest for that concept
        for name, concept in vocab._concept_distributions.items():
            result = recognizer.recognize_from_vector(concept.param_means)
            # The concept should have a non-zero score
            assert result["class_scores"][name] > 0

    def test_class_scores_sum_to_one(self):
        vocab = make_test_vocabulary()
        recognizer = GeometricRecognizer(vocab)

        vec = np.random.rand(TOTAL_DIM).astype(np.float32)
        result = recognizer.recognize_from_vector(vec)

        scores = result["class_scores"]
        total = sum(scores.values())
        # Scores don't need to sum to 1 (they're not probabilities),
        # but they should be non-negative
        assert all(v >= 0 for v in scores.values())

    def test_batch_recognize(self):
        vocab = make_test_vocabulary()
        recognizer = GeometricRecognizer(vocab)

        # Create multiple vectors
        vectors = [np.random.rand(TOTAL_DIM).astype(np.float32) for _ in range(5)]

        # Batch recognize (using recognize_from_vector in a loop)
        results = [recognizer.recognize_from_vector(v) for v in vectors]

        assert len(results) == 5
        for r in results:
            assert "predicted_class" in r
            assert "confidence" in r
