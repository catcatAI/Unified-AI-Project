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
