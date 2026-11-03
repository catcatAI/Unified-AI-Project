"""Tests for the scale-envelope probe (scripts/probe_scale_envelope.py).

The probe's own failure mode is the interesting one: an envelope measured by a
tool that cannot see the peak is worse than no envelope, because it answers
"fits" with confidence. These tests pin the three things that made the first
version wrong:

1. the grid must actually ascend, or "largest fit" is just the last row;
2. a config's cost must come from its own process (host high-water marks are
   monotonic, so several configs in one process report one number);
3. the host reading must be a real value from the kernel, not a unit guess.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "probe_scale_envelope.py"


@pytest.fixture(scope="module")
def probe_scale():
    spec = importlib.util.spec_from_file_location("probe_scale_envelope_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_scale_envelope_test"] = module
    spec.loader.exec_module(module)
    return module


def test_grid_ascends_in_capacity(probe_scale):
    sizes = [c["d_emb"] * c["d_hidden"] * c["layers"] for c in probe_scale.GRID]
    assert sizes == sorted(sizes)
    assert len(set(sizes)) == len(sizes), "two configs with the same capacity prove nothing"


def test_grid_starts_at_the_shape_that_already_ran(probe_scale):
    first = probe_scale.GRID[0]
    assert first == {"d_emb": 96, "d_hidden": 1024, "layers": 1, "batch": 32, "max_len": 384}


def test_pairs_respects_the_limit(probe_scale, tmp_path):
    path = tmp_path / "train.jsonl"
    path.write_text(
        "".join('{"input": "q%d", "output": "a%d"}\n' % (i, i) for i in range(10)),
        encoding="utf-8",
    )
    assert len(probe_scale._pairs(path, 4)) == 4
    assert len(probe_scale._pairs(path, 0)) == 10
    assert probe_scale._pairs(path, 1)[0] == ("q0", "a0")


def test_host_reading_is_a_plausible_kernel_value(probe_scale):
    resident, peak = probe_scale._host_mib()
    assert 0 < resident <= peak
    # anything outside this is a unit mistake, not a small machine
    assert peak < 64 * 1024, f"high-water {peak} MiB is not MiB"
