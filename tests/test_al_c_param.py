"""Tests for the C-param gate (``scripts/al_c_param.py``).

The gate's whole value is that it does not trust the wiring: it drives the real
``ChatService.generate_text`` and inspects the parameters that reach the LLM
service. These tests pin the verdict, the untouched control, and that the
explained-variance control separates "the phase decides" from "there is variance".
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_c_param.py"


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("al_c_param_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_c_param_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def result(gate):
    return gate.run()


def test_gate_reaches_its_verdict(result):
    assert result["verdict"] == "generation-params-modulated"
    assert all(result["checks"].values()) is True


def test_the_parameters_actually_moved(result):
    assert max(result["temperature"]) > 0.7 > min(result["temperature"])
    assert result["spread"] > 0.1
    assert max(result["max_tokens"]) > 512 > min(result["max_tokens"])


def test_without_the_rhythm_the_request_is_untouched(result):
    assert result["control"] == {"temperature": 0.7, "max_tokens": 512}


def test_the_phase_explains_the_parameter(result):
    assert result["phase_explained"] > 0.9
    assert result["permutation"]["phase_explained"] < 0.2
    assert result["clock_forgery_reproducible"] is False


class TestBrokenSources:
    """壞掉的狀態源要退成原值，不能拋例外、也不能被當成谷底。"""

    class _Raising:
        @property
        def rhythm(self):
            raise RuntimeError("state store unavailable")

    class _Snap:
        def __init__(self, activation):
            self.rhythm = {"activation": activation}

    @pytest.mark.parametrize(
        "snapshot_factory",
        [
            lambda: None,
            lambda: TestBrokenSources._Snap(float("nan")),
            lambda: TestBrokenSources._Snap(float("inf")),
            lambda: TestBrokenSources._Snap(True),
            lambda: TestBrokenSources._Snap("high"),
            lambda: TestBrokenSources._Raising(),
            lambda: object(),
        ],
    )
    def test_every_broken_source_leaves_the_request_alone(self, snapshot_factory):
        from core.life.al_generation_params import modulate

        params = modulate(0.7, 512, snapshot_factory())
        assert (params.temperature, params.max_tokens) == (0.7, 512)
        assert params.applied == {} and params.source is None

    def test_an_observed_trough_is_not_the_same_as_no_observation(self):
        from core.life.al_generation_params import modulate

        trough = modulate(0.7, 512, self._Snap(0.0))
        missing = modulate(0.7, 512, None)
        assert trough.temperature < missing.temperature
        assert trough.max_tokens < missing.max_tokens


class TestControlsAreReported:
    def test_the_gate_reports_more_than_one_control(self, result):
        controls = [name for name in result["checks"] if name.startswith("control_")]
        assert len(controls) >= 5
        assert all(result["checks"][name] for name in controls)

    def test_broken_source_outcomes_are_visible_in_the_report(self, result):
        assert result["broken_sources"] == {"missing": True, "nan": True, "raising": True}
        assert result["frozen_phase_repeatable"] is True
