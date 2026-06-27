"""Tests for SequenceGenerator."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from ai.multimodal.generator.sequence_generator import SequenceGenerator


class TestSequenceGeneratorInit:
    """Test initialization."""

    def test_default_init(self):
        gen = SequenceGenerator()
        assert gen.input_dim == 512
        assert gen.hidden_dim == 128
        assert gen.primitive_dim == 128
        assert gen.max_steps == 20

    def test_custom_init(self):
        gen = SequenceGenerator(input_dim=256, hidden_dim=64, primitive_dim=32, max_steps=10)
        assert gen.input_dim == 256
        assert gen.hidden_dim == 64
        assert gen.primitive_dim == 32
        assert gen.max_steps == 10

    def test_not_trained_initially(self):
        gen = SequenceGenerator()
        assert gen.is_trained is False


class TestSequenceGeneratorGenerate:
    """Test generation."""

    def test_generate_returns_list(self):
        gen = SequenceGenerator()
        clip_emb = np.random.randn(512).astype(np.float32)
        result = gen.generate(clip_emb)
        assert isinstance(result, list)

    def test_generate_returns_primitives(self):
        gen = SequenceGenerator()
        clip_emb = np.random.randn(512).astype(np.float32)
        result = gen.generate(clip_emb)
        assert len(result) > 0
        assert result[0].shape == (128,)

    def test_generate_normalized(self):
        gen = SequenceGenerator()
        clip_emb = np.random.randn(512).astype(np.float32)
        result = gen.generate(clip_emb)
        for prim in result:
            norm = np.linalg.norm(prim)
            assert abs(norm - 1.0) < 0.01  # L2 normalized

    def test_generate_variable_length(self):
        gen = SequenceGenerator(max_steps=10)
        clip_emb = np.random.randn(512).astype(np.float32)
        lengths = set()
        for _ in range(20):
            result = gen.generate(clip_emb, temperature=1.0)
            lengths.add(len(result))
        # Should produce different lengths due to stochastic stop
        assert len(lengths) > 1

    def test_generate_deterministic(self):
        gen = SequenceGenerator()
        clip_emb = np.random.randn(512).astype(np.float32)
        r1 = gen.generate_deterministic(clip_emb)
        r2 = gen.generate_deterministic(clip_emb)
        assert len(r1) == len(r2)
        for a, b in zip(r1, r2):
            np.testing.assert_array_almost_equal(a, b)

    def test_generate_wrong_shape_raises(self):
        gen = SequenceGenerator()
        with pytest.raises(ValueError):
            gen.generate(np.random.randn(256).astype(np.float32))


class TestSequenceGeneratorTrain:
    """Test training."""

    def test_train_step_returns_loss(self):
        gen = SequenceGenerator()
        clip_emb = np.random.randn(512).astype(np.float32)
        targets = [np.random.randn(128).astype(np.float32) for _ in range(3)]
        loss = gen.train_step(clip_emb, targets)
        assert isinstance(loss, float)
        assert loss >= 0

    def test_train_step_reduces_loss(self):
        gen = SequenceGenerator()
        clip_emb = np.random.randn(512).astype(np.float32)
        targets = [np.random.randn(128).astype(np.float32) for _ in range(3)]
        
        losses = []
        for _ in range(50):
            loss = gen.train_step(clip_emb, targets, lr=0.01)
            losses.append(loss)
        
        # Loss should decrease
        assert losses[-1] < losses[0]

    def test_train_step_empty_targets(self):
        gen = SequenceGenerator()
        clip_emb = np.random.randn(512).astype(np.float32)
        loss = gen.train_step(clip_emb, [])
        assert loss == 0.0

    def test_train_reduces_loss(self):
        gen = SequenceGenerator(hidden_dim=32)
        n_samples = 10
        clip_embs = [np.random.randn(512).astype(np.float32) for _ in range(n_samples)]
        sequences = [[np.random.randn(128).astype(np.float32) for _ in range(3)]
                     for _ in range(n_samples)]
        
        result = gen.train(clip_embs, sequences, epochs=30, lr=0.005)
        assert result["final_loss"] < result["history"][0]

    def test_train_marks_trained(self):
        gen = SequenceGenerator(hidden_dim=32)
        clip_embs = [np.random.randn(512).astype(np.float32)]
        sequences = [[np.random.randn(128).astype(np.float32)]]
        gen.train(clip_embs, sequences, epochs=5)
        assert gen.is_trained is True

    def test_train_mismatched_lengths_raises(self):
        gen = SequenceGenerator()
        with pytest.raises(ValueError):
            gen.train(
                [np.random.randn(512).astype(np.float32)],
                [np.random.randn(128).astype(np.float32) for _ in range(3)],
            )


class TestSequenceGeneratorSaveLoad:
    """Test save/load."""

    def test_save_and_load(self, tmp_path):
        gen = SequenceGenerator(hidden_dim=32)
        clip_emb = np.random.randn(512).astype(np.float32)
        gen.generate_deterministic(clip_emb)  # Touch weights
        
        path = str(tmp_path / "gen.json")
        gen.save(path)
        
        loaded = SequenceGenerator.load(path)
        assert loaded.input_dim == gen.input_dim
        assert loaded.hidden_dim == gen.hidden_dim
        assert loaded.primitive_dim == gen.primitive_dim
        assert loaded.is_trained is True
        
        # Should produce same output
        r1 = gen.generate_deterministic(clip_emb)
        r2 = loaded.generate_deterministic(clip_emb)
        assert len(r1) == len(r2)
        for a, b in zip(r1, r2):
            np.testing.assert_array_almost_equal(a, b)
