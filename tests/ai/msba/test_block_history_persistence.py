# -*- coding: utf-8 -*-
"""
Tests for MSBA BlockHistoryPersistence.
"""

import os
import tempfile

import pytest

from ai.msba.block_history_persistence import BlockHistoryPersistence
from ai.msba.types import BlockHistory


class TestBlockHistoryPersistence:
    def test_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            persist = BlockHistoryPersistence(tmpdir)
            assert os.path.exists(tmpdir)

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            persist = BlockHistoryPersistence(tmpdir)

            history = {
                "temporal": BlockHistory(),
                "emotional": BlockHistory(),
            }
            history["temporal"].record("confirm")
            history["temporal"].record("confirm")
            history["emotional"].record("question")

            path = persist.save(history)
            assert os.path.exists(path)

            loaded = persist.load()
            assert "temporal" in loaded
            assert "emotional" in loaded
            assert loaded["temporal"].confirm_count == 2
            assert loaded["emotional"].question_count == 1

    def test_load_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            persist = BlockHistoryPersistence(tmpdir)
            loaded = persist.load()
            assert loaded == {}

    def test_append_selection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            persist = BlockHistoryPersistence(tmpdir)

            persist.append_selection(
                "hello",
                ["temporal", "emotional"],
                {"temporal": "confirm", "emotional": "neutral"},
            )

            log = persist.load_selection_log()
            assert len(log) == 1
            assert log[0]["input"] == "hello"
            assert log[0]["blocks"] == ["temporal", "emotional"]

    def test_selection_log_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            persist = BlockHistoryPersistence(tmpdir)

            # Add 1100 records
            for i in range(1100):
                persist.append_selection(
                    f"input_{i}",
                    ["temporal"],
                    {"temporal": "confirm"},
                )

            log = persist.load_selection_log()
            assert len(log) <= 1000  # Kept only last 1000

    def test_save_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            persist = BlockHistoryPersistence(tmpdir)
            path = persist.save({})
            assert os.path.exists(path)

            loaded = persist.load()
            assert loaded == {}
