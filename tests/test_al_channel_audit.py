"""Tests for the AL->generation channel audit (scripts/al_channel_audit.py).

The audit's job is to keep "the state changed the reply" from being read as
"the state is inside the model". What is pinned:

1. the prompt route and the sampling route are both present, so a claim that
   AL is coupled to generation is not empty;
2. the sampling route's resolution is a real number derived from the voter's
   rounding, not a hand-written constant — and it is coarser than the prompt's;
3. no route carries the state inside a recurrent model state, so the literal
   "one model" claim is reported as not implemented;
4. every implemented route is reproducible by an injector, which is why route
   choice cannot settle real-vs-fake on its own.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_channel_audit.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def audit():
    return _load("al_channel_audit_test", SCRIPT)


def test_both_prompt_and_sampling_routes_exist(audit):
    result = audit.audit()
    implemented = result["summary"]["implemented"]
    assert "prompt_text" in implemented
    assert "sampling_param" in implemented


def test_resolutions_are_measured_and_the_prompt_route_is_finer(audit):
    result = audit.audit()
    prompt = result["summary"]["prompt_route_resolution"]
    sampling = result["summary"]["sampling_route_resolution"]
    assert prompt == 10**audit.PROMPT_DECIMALS + 1
    assert sampling > 1  # a channel with resolution 1 is a constant
    assert sampling < prompt


def test_the_literal_one_model_route_is_not_implemented(audit):
    result = audit.audit()
    assert result["summary"]["one_model_implemented"] is False
    state = next(c for c in result["channels"] if c["route"] == "C-state")
    assert state["implemented"] is False


def test_every_channel_is_reproducible_by_an_injector(audit):
    """Route choice cannot settle real-vs-fake: text and temperature are both
    settable by a third party."""
    assert all(c["reproducible_by_an_injector"] for c in audit.audit()["channels"])


def test_the_sampling_route_cannot_be_read_or_ignored_by_the_model(audit):
    param = next(c for c in audit.audit()["channels"] if c["route"] == "C-param")
    assert param["model_can_read_it"] is False
    assert param["model_can_ignore_it"] is False
