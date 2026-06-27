"""Tests for GenerationEvaluator."""

import os
import sys

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator


def _make_image(color=(128, 128, 128), size=(64, 64)):
    """Helper to create a solid color image."""
    return Image.new("RGB", size, color)


def _make_gradient_image(size=(64, 64)):
    """Helper to create a gradient image."""
    arr = np.zeros((*size, 3), dtype=np.uint8)
    for i in range(size[0]):
        for j in range(size[1]):
            arr[i, j] = [int(i * 255 / size[0]), int(j * 255 / size[1]), 128]
    return Image.fromarray(arr)


class TestGenerationEvaluatorInit:
    """Test initialization."""

    def test_default_init(self):
        eval_ = GenerationEvaluator()
        assert eval_._encoder is None

    def test_init_with_encoder(self):
        eval_ = GenerationEvaluator(semantic_encoder="fake")
        assert eval_._encoder == "fake"


class TestEvaluate:
    """Test full evaluate method."""

    def test_evaluate_minimal(self):
        eval_ = GenerationEvaluator()
        img = _make_image()
        result = eval_.evaluate(img)
        assert "mean_brightness" in result
        assert "color_coverage" in result
        assert "edge_density" in result

    def test_evaluate_with_text(self):
        eval_ = GenerationEvaluator()
        img = _make_image()
        result = eval_.evaluate(img, text="a gray square")
        assert "clip_text_similarity" in result
        assert 0.0 <= result["clip_text_similarity"] <= 1.0

    def test_evaluate_with_reference(self):
        eval_ = GenerationEvaluator()
        img1 = _make_image((255, 0, 0))
        img2 = _make_image((255, 0, 0))
        result = eval_.evaluate(img1, reference=img2)
        assert "clip_image_similarity" in result
        assert result["clip_image_similarity"] > 0.9  # Same color

    def test_evaluate_with_primitives(self):
        eval_ = GenerationEvaluator()
        img = _make_image()
        prims = [np.random.randn(64).astype(np.float32) for _ in range(3)]
        result = eval_.evaluate(img, primitives=prims)
        assert "primitive_diversity" in result
        assert "n_primitives" in result
        assert result["n_primitives"] == 3


class TestColorMetrics:
    """Test color-related metrics."""

    def test_solid_image_low_color_coverage(self):
        eval_ = GenerationEvaluator()
        img = _make_image((128, 128, 128))
        result = eval_.evaluate(img)
        assert result["color_coverage"] < 0.1  # Single color

    def test_gradient_image_high_color_coverage(self):
        eval_ = GenerationEvaluator()
        img = _make_gradient_image()
        result = eval_.evaluate(img)
        assert result["color_coverage"] > 0.1  # Many colors

    def test_white_image_high_brightness(self):
        eval_ = GenerationEvaluator()
        img = _make_image((255, 255, 255))
        result = eval_.evaluate(img)
        assert result["mean_brightness"] > 0.9

    def test_black_image_low_brightness(self):
        eval_ = GenerationEvaluator()
        img = _make_image((0, 0, 0))
        result = eval_.evaluate(img)
        assert result["mean_brightness"] < 0.1


class TestPrimitiveDiversity:
    """Test primitive diversity metric."""

    def test_identical_primitives_zero_diversity(self):
        eval_ = GenerationEvaluator()
        emb = np.ones(64, dtype=np.float32)
        prims = [emb.copy(), emb.copy(), emb.copy()]
        result = eval_.evaluate(_make_image(), primitives=prims)
        assert result["primitive_diversity"] < 0.01

    def test_different_primitives_high_diversity(self):
        eval_ = GenerationEvaluator()
        prims = [
            np.array([1] + [0]*63, dtype=np.float32),
            np.array([0]*63 + [1], dtype=np.float32),
            np.array([0, 1] + [0]*62, dtype=np.float32),
        ]
        result = eval_.evaluate(_make_image(), primitives=prims)
        assert result["primitive_diversity"] > 0.5

    def test_single_primitive_zero_diversity(self):
        eval_ = GenerationEvaluator()
        prims = [np.random.randn(64).astype(np.float32)]
        result = eval_.evaluate(_make_image(), primitives=prims)
        assert result["primitive_diversity"] == 0.0


class TestTextSimilarity:
    """Test text similarity with fallback."""

    def test_color_match_red(self):
        eval_ = GenerationEvaluator()
        img = _make_image((255, 0, 0))
        score = eval_.clip_text_similarity(img, "a red object")
        assert score > 0.5

    def test_color_match_blue(self):
        eval_ = GenerationEvaluator()
        img = _make_image((0, 0, 255))
        score = eval_.clip_text_similarity(img, "a blue object")
        assert score > 0.5

    def test_no_match(self):
        eval_ = GenerationEvaluator()
        img = _make_image((0, 0, 0))
        score = eval_.clip_text_similarity(img, "a bright yellow sun")
        assert score < 0.7


class TestEdgeDensity:
    """Test edge density metric."""

    def test_solid_image_low_edges(self):
        eval_ = GenerationEvaluator()
        img = _make_image((128, 128, 128))
        result = eval_.evaluate(img)
        assert result["edge_density"] < 0.05

    def test_gradient_image_has_edges(self):
        eval_ = GenerationEvaluator()
        # Sharp gradient: left half black, right half white
        arr = np.zeros((64, 64, 3), dtype=np.uint8)
        arr[:, 32:, :] = 255
        img = Image.fromarray(arr)
        result = eval_.evaluate(img)
        assert result["edge_density"] > 0.0
