"""Tests for the fixed scoring protocol (``scripts/al_downstream_protocol.py``).

The protocol exists so the mechanism question cannot be answered by picking a
regime after the fact. Only two things need pinning: the overall verdict must
refuse to conclude from a single informative regime, and the cell evaluation must
keep the arms gain-matched.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_downstream_protocol.py"


@pytest.fixture(scope="module")
def protocol():
    spec = importlib.util.spec_from_file_location("al_downstream_protocol_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_downstream_protocol_test"] = module
    spec.loader.exec_module(module)
    return module


def _cell(verdict, informative=True):
    return {"informative": informative, "cell": {"verdict": verdict}}


class TestOverallVerdict:
    def test_one_informative_regime_is_not_enough(self, protocol):
        cells = [_cell("phase-beats-matched-mean"), _cell("whatever", informative=False)]
        assert protocol.overall_verdict(cells) == "insufficient-informative-regimes"

    def test_same_direction_everywhere_is_a_claim(self, protocol):
        cells = [_cell("phase-beats-matched-mean"), _cell("phase-beats-matched-mean")]
        assert protocol.overall_verdict(cells) == "mechanism-benefit-consistent"

    def test_consistent_absence_of_benefit_is_also_a_claim(self, protocol):
        cells = [_cell("no-downstream-difference"), _cell("timing-does-not-matter-only-gain")]
        assert protocol.overall_verdict(cells) == "no-mechanism-benefit-consistent"

    def test_opposite_directions_make_no_claim(self, protocol):
        cells = [_cell("phase-beats-matched-mean"), _cell("no-downstream-difference")]
        assert protocol.overall_verdict(cells) == "regime-dependent-no-claim"


class TestProtocolConstants:
    def test_readout_is_the_one_that_can_rank(self, protocol):
        assert protocol.READOUT == "potential"

    def test_regime_matrix_is_not_a_single_regime(self, protocol):
        assert len(protocol.EPOCHS_MATRIX) >= 2

    def test_ladder_gets_harder_not_easier(self, protocol):
        sizes = [pairs for pairs, _ in protocol.LADDER]
        assert sizes == sorted(sizes)


class TestCell:
    def test_cell_keeps_the_arms_gain_matched(self, protocol):
        cell = protocol.evaluate_cell({"pairs": 48, "noise_bits": 3, "lr": 0.03}, epochs=1)
        assert cell["gain_matched"] is True
        means = {name: cell["arms"][name]["gain_mean"] for name in cell["arms"]}
        assert abs(means["phase"] - means["neutral"]) <= 0.05
        assert abs(means["shuffled"] - means["neutral"]) <= 0.05

    def test_cell_reports_every_arm(self, protocol):
        cell = protocol.evaluate_cell({"pairs": 48, "noise_bits": 3, "lr": 0.03}, epochs=1)
        assert set(cell["arms"]) == {"neutral", "phase", "shuffled"}
