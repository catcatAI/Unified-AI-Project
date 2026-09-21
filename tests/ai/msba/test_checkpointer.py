# -*- coding: utf-8 -*-
"""
Tests for MSBA MSBACheckpointer.
"""

import os
import tempfile

import numpy as np
import pytest

from ai.msba.checkpointer import MSBACheckpointer
from ai.msba.semantic_block import SemanticBlock
from ai.msba.types import BlockHistory


class TestMSBACheckpointer:
    def test_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cp = MSBACheckpointer(tmpdir)
            assert os.path.exists(tmpdir)

    def test_save_and_load_cross_attention(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cp = MSBACheckpointer(tmpdir)
            ca = np.random.randn(9, 9)
            cp.save({}, ca, {})
            loaded = cp.load({})
            assert loaded is not None
            np.testing.assert_array_almost_equal(loaded, ca)

    def test_save_and_load_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cp = MSBACheckpointer(tmpdir)
            hist = {"temporal": {"total": 5, "confirm": 3}}
            cp.save({}, np.ones((9, 9)), hist)
            loaded = cp.load({})
            hist_path = os.path.join(tmpdir, "history.json")
            assert os.path.exists(hist_path)

    def test_load_no_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cp = MSBACheckpointer(tmpdir)
            loaded = cp.load({})
            assert loaded is None

    def test_save_with_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cp = MSBACheckpointer(tmpdir)

            class MockEngine:
                W = np.ones((3, 3))

                def save_checkpoint(self, path):
                    np.savez(path, W=self.W)

            block = SemanticBlock(block_id="test", block_name="Test")
            block.coordinator = type("Coord", (), {"engine": MockEngine()})()
            cp.save({"test": block}, np.ones((9, 9)), {})

            # Verify file was created
            assert os.path.exists(os.path.join(tmpdir, "test_snn.npz"))

    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cp = MSBACheckpointer(tmpdir)
            ca = np.eye(9) * 0.5
            hist = {"a": {"x": 1}}
            cp.save({}, ca, hist)
            loaded = cp.load({})
            assert loaded is not None
