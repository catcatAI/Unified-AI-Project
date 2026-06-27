"""Tests for ImageGenerator."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from ai.multimodal.generator.image_generator import ImageGenerator
from ai.multimodal.generator.sequence_generator import SequenceGenerator
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer


class TestImageGeneratorInit:
    """Test initialization."""

    def test_default_init(self):
        gen = ImageGenerator()
        assert gen._encoder is None
        assert isinstance(gen._generator, SequenceGenerator)
        assert isinstance(gen._prim_encoder, PrimitiveEncoder)
        assert isinstance(gen._renderer, PrimitiveRenderer)


class TestImageGeneratorGenerate:
    """Test image generation."""

    def test_generate_from_text_returns_image(self):
        gen = ImageGenerator()
        img = gen.generate_from_text("a red circle")
        assert img is not None
        assert hasattr(img, "size")

    def test_generate_from_text_correct_size(self):
        gen = ImageGenerator()
        img = gen.generate_from_text("hello", canvas_size=(64, 64))
        assert img.size == (64, 64)

    def test_generate_from_embedding(self):
        gen = ImageGenerator()
        clip_emb = np.random.randn(512).astype(np.float32)
        img = gen.generate_from_embedding(clip_emb)
        assert img is not None
        assert img.size == (128, 128)

    def test_generate_variations(self):
        gen = ImageGenerator()
        imgs = gen.generate_variations("a blue square", n_variations=3)
        assert len(imgs) == 3
        for img in imgs:
            assert img is not None
            assert img.size == (128, 128)

    def test_generate_multi_primitives(self):
        gen = ImageGenerator()
        img = gen.generate_multi_primitives("a green triangle")
        assert img is not None
        assert img.size == (128, 128)


class TestImageGeneratorTrained:
    """Test with trained components."""

    def test_with_trained_generator(self):
        # Pre-train the generator
        gen = ImageGenerator()
        
        # Create training data
        clip_embs = [np.random.randn(512).astype(np.float32) for _ in range(5)]
        sequences = [[np.random.randn(128).astype(np.float32) for _ in range(2)]
                     for _ in range(5)]
        
        gen._generator.train(clip_embs, sequences, epochs=10, lr=0.01)
        
        # Generate
        img = gen.generate_from_text("test")
        assert img is not None
        assert img.size == (128, 128)
