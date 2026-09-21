# -*- coding: utf-8 -*-
"""
Tests for MSBA Checkpointer.
"""

import json
import os
import tempfile

import numpy as np
import pytest

from ai.msba.checkpointer import MSBACheckpointer


class TestMSBACheckpointer:
    def test_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = MSBACheckpointer(base_dir=tmpdir)
            assert ckpt.base_dir == tmpdir
            assert ckpt.auto_save_interval == 300.0

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = MSBACheckpointer(base_dir=tmpdir)
            ca = np.ones((9, 9)) * 0.5
            history = {"emotional": {"count": 10}}

            ckpt.save({}, ca, history)

            # Load
            result = ckpt.load({})
            assert "cross_attention" in result
            assert np.allclose(result["cross_attention"], ca)
            assert result["history"] == history

    def test_save_with_training_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = MSBACheckpointer(base_dir=tmpdir)
            ca = np.ones((9, 9))
            training = {"step_count": 100, "learning_rate": 0.005}

            ckpt.save({}, ca, {}, training_state=training)

            result = ckpt.load({})
            assert result["training_state"] == training

    def test_save_with_ab_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = MSBACheckpointer(base_dir=tmpdir)
            ca = np.ones((9, 9))
            ab = {"variant_a": 50, "variant_b": 50}

            ckpt.save({}, ca, {}, ab_state=ab)

            result = ckpt.load({})
            assert result["ab_state"] == ab

    def test_version_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = MSBACheckpointer(base_dir=tmpdir)
            ca = np.ones((9, 9))

            ckpt.save({}, ca, {})
            ckpt.save({}, ca, {})

            versions = ckpt.get_version_list()
            assert len(versions) == 2
            assert versions[0]["version"] == 1
            assert versions[1]["version"] == 2

    def test_auto_save_check(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = MSBACheckpointer(base_dir=tmpdir, auto_save_interval=0.001)
            # First check should trigger
            assert ckpt.check_auto_save() is True
            ckpt.mark_saved()
            # Second check immediately should not
            assert ckpt.check_auto_save() is False

    def test_max_versions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = MSBACheckpointer(base_dir=tmpdir, max_versions=3)
            ca = np.ones((9, 9))

            for _ in range(5):
                ckpt.save({}, ca, {})

            versions = ckpt.get_version_list()
            assert len(versions) == 3

    def test_load_specific_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = MSBACheckpointer(base_dir=tmpdir)
            ca1 = np.ones((9, 9)) * 0.5
            ca2 = np.ones((9, 9)) * 0.8

            ckpt.save({}, ca1, {})
            ckpt.save({}, ca2, {})

            result = ckpt.load({}, version=1)
            assert np.allclose(result["cross_attention"], ca1)

    def test_latest_symlink(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = MSBACheckpointer(base_dir=tmpdir)
            ca = np.ones((9, 9))

            ckpt.save({}, ca, {})

            latest = os.path.join(tmpdir, "latest")
            assert os.path.islink(latest)
