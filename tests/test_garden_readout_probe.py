"""Tests for the readout-resolution probe (``scripts/garden_readout_probe.py``).

The probe exists to explain a failed experiment, so what matters is that its
verdict distinguishes "the task has headroom and we still could not measure it"
from "the readout cannot express a margin at all".
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "garden_readout_probe.py"


@pytest.fixture(scope="module")
def probe():
    spec = importlib.util.spec_from_file_location("garden_readout_probe_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["garden_readout_probe_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report(probe):
    return probe.run()


def _panels(*hits):
    return [{"threshold": 0.1 + i, "hit_rate": h, "tie_rate": 1.0 - h} for i, h in enumerate(hits)]


class TestVerdict:
    def test_only_endpoints_means_the_readout_is_the_limit(self, probe):
        sweep = _panels(0.0, 1.0, 0.0, 1.0)
        assert probe._verdict(sweep, dropped=True, empty=False) == "readout-quantised-no-headroom"

    def test_an_intermediate_value_proves_headroom(self, probe):
        sweep = _panels(0.0, 0.5, 1.0)
        assert probe._verdict(sweep, dropped=True, empty=False) == "readout-has-headroom"

    def test_dropped_magnitude_alone_is_not_enough(self, probe):
        sweep = _panels(0.0, 0.5, 1.0)
        assert probe._verdict(sweep, dropped=False, empty=False) == "readout-has-headroom"

    def test_nothing_spiking_is_its_own_answer(self, probe):
        sweep = _panels(0.0, 0.0, 0.0)
        assert probe._verdict(sweep, dropped=True, empty=True) == "no-output-above-threshold"


class TestMeasuredSweep:
    def test_the_sweep_has_no_intermediate_threshold(self, report):
        assert report["verdict"] == "readout-quantised-no-headroom"
        assert report["intermediate_thresholds"] == []

    def test_magnitude_really_is_dropped(self, report):
        assert report["magnitude_dropped"] is True

    def test_the_readout_is_finite(self, report):
        assert report["distinct_output_values"] == report["timesteps"] + 1

    def test_every_threshold_lands_on_an_endpoint(self, report):
        assert all(p["hit_rate"] in (0.0, 1.0) for p in report["sweep"])
