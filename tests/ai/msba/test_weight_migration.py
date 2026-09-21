# -*- coding: utf-8 -*-
"""
Tests for MSBA WeightMigration.
"""

import os
import tempfile

import numpy as np
import pytest
from ai.msba.weight_migration import WeightMigration


class MockEngine:
    """Mock engine with weights for testing."""

    def __init__(self, shape=(100, 100)):
        self.W = np.random.randn(*shape).astype(np.float32)


class TestWeightMigration:
    def test_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            migrator = WeightMigration(tmpdir)
            assert os.path.exists(tmpdir)

    def test_migrate_generic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            migrator = WeightMigration(tmpdir)
            engine = MockEngine()

            path = migrator.migrate_generic(engine, "test_block")
            assert path is not None
            assert os.path.exists(path)

    def test_migrate_core_network(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            migrator = WeightMigration(tmpdir)
            engine = MockEngine()

            path = migrator.migrate_core_network(engine, "test_block")
            assert path is not None
            assert os.path.exists(path)

    def test_migrate_tensor_snn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            migrator = WeightMigration(tmpdir)
            engine = MockEngine()

            path = migrator.migrate_tensor_snn(engine, "test_block")
            assert path is not None
            assert os.path.exists(path)

    def test_list_migrated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            migrator = WeightMigration(tmpdir)
            engine = MockEngine()

            migrator.migrate_generic(engine, "block1")
            migrator.migrate_generic(engine, "block2")

            files = migrator.list_migrated()
            assert len(files) == 2

    def test_get_migration_info(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            migrator = WeightMigration(tmpdir)
            engine = MockEngine()

            migrator.migrate_generic(engine, "test_block")

            info = migrator.get_migration_info()
            assert info["total_blocks"] == 1
            assert "test_block" in info["blocks"]

    def test_no_weights_engine(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            migrator = WeightMigration(tmpdir)

            class NoWeightsEngine:
                pass

            path = migrator.migrate_generic(NoWeightsEngine(), "test_block")
            assert path is None
