"""Tests for the stability probe (scripts/probe_stability.py).

Claims pinned here:

1. ``spectral_radius`` measures the largest |eigenvalue|, so a scaled identity
   is the exact answer (no tolerance games);
2. the autonomous orbit can tell a structure that holds state from one that has
   been reduced to wire-through: with no recurrence the activity dies as soon as
   the input stops, with a recurrence above the threshold it keeps firing;
3. ``leak_floor`` and ``gain_cap`` are *projections*, and 0 leaves the parameters
   exactly where the optimiser put them (the historical behaviour);
4. the probe's own summary flags erosion, so a report cannot claim the recurrence
   held when the orbit collapsed;
5. the CLI writes a report with the trajectory and that summary.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "probe_stability", REPO / "scripts" / "probe_stability.py"
)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)

sys.path.insert(0, str(REPO / "apps" / "backend" / "src"))
from ai.ed3n.token_snn import TokenConfig, TokenSNN, TokenVocab  # noqa: E402


def _model(**overrides):
    pairs = [
        (
            f"<al_in> v=0.{i:02d} a=-0.{i:02d} d=0.100 fatigue=0.500 stress=0.100 health=0.400 "
            f"mode=neutral intent=math_query dt=0.500 | {100 + i} + {i}",
            f"{100 + 2 * i}\n<al_out> v=0.{i:02d} a=-0.{i:02d} d=0.100 fatigue=0.500 "
            f"stress=0.100 health=0.400 mode=neutral intent=math_query",
        )
        for i in range(12)
    ]
    vocab = TokenVocab.build([p + a for p, a in pairs], min_count=1, max_vocab=200)
    cfg = TokenConfig(d_emb=8, d_hidden=8, layers=2, max_len=96, **overrides)
    return TokenSNN(vocab, cfg, device="cpu"), pairs


def test_spectral_radius_is_exact_on_a_scaled_identity():
    weight = 1.5 * torch.eye(6)
    assert abs(probe.spectral_radius(torch, weight) - 1.5) < 1e-3
    assert probe.spectral_radius(torch, torch.zeros(4, 4)) == 0.0


def test_orbit_dies_without_recurrence_and_survives_with_it():
    model, pairs = _model()
    with torch.no_grad():
        model.net.threshold.fill_(0.2)
        for layer in model.net.w_rec:
            layer.weight.zero_()
        # biases are a constant drive: with them in place the state settles at
        # b/(1-beta) and fires forever, which is exactly why the orbit is only a
        # diagnostic and the drift verdict is read off beta and sr
        for layer in model.net.w_in:
            layer.weight.zero_()
            layer.bias.zero_()
        for layer in model.net.w_skip:
            if hasattr(layer, "weight"):
                layer.weight.zero_()
                layer.bias.zero_()
        model.net.embed.weight.zero_()
    # leak alone does decay the state, just at beta^t: 200 steps is enough to see
    # whether anything else is holding it up
    dead = probe.orbit(torch, model, pairs, steps=200)
    assert dead["dead_at"] is not None, "no recurrence yet activity persists"
    assert dead["end"] == 0.0
    alive_model, _ = _model()
    with torch.no_grad():
        for layer in alive_model.net.w_rec:
            layer.weight.copy_(1.4 * torch.eye(alive_model.config.d_hidden))
    alive = probe.orbit(torch, alive_model, pairs)
    assert alive["dead_at"] is None
    assert alive["end"] > 0.0


def test_projections_are_applied_and_zero_disables_them():
    model, pairs = _model(leak_floor=0.9, gain_cap=0.5)
    with torch.no_grad():
        model.net.beta.fill_(0.0)  # sigmoid -> 0.5, below the floor
        for layer in model.net.w_rec:
            layer.weight.copy_(2.5 * torch.eye(model.config.d_hidden))
        model._project_structure()
        assert float(torch.sigmoid(model.net.beta)) >= 0.9 - 1e-6
        for layer in model.net.w_rec:
            assert probe.spectral_radius(torch, layer.weight) <= 0.5 + 1e-3

    free, _ = _model()
    with torch.no_grad():
        free.net.beta.fill_(0.0)
        for layer in free.net.w_rec:
            layer.weight.copy_(2.5 * torch.eye(free.config.d_hidden))
        free._project_structure()
        assert abs(float(torch.sigmoid(free.net.beta)) - 0.5) < 1e-6
        for layer in free.net.w_rec:
            assert probe.spectral_radius(torch, layer.weight) > 2.0


def _row(epoch, beta, orbit_end, val, sr=(0.6, 0.9)):
    return {
        "epoch": epoch,
        "train": 0.9,
        "val": val,
        "beta": beta,
        "horizon": 1.0 / max(1e-6, 1.0 - beta),
        "theta": 0.5,
        "sr": list(sr),
        "orbit": {"start": 0.5, "end": orbit_end, "dead_at": None, "period": None},
    }


def test_summary_reads_the_drift_off_the_parameters_not_the_orbit():
    drifted = [
        _row(0, 0.90, 0.54, 0.80),
        _row(1, 0.85, 0.30, 0.82, (0.9, 1.45)),
        _row(2, 0.81, 0.12, 0.87, (0.9, 1.60)),
    ]
    summary = probe.summarise(drifted)
    assert summary["verdict"] == "params-drifted"
    assert summary["beta"] == [0.9, 0.81]
    assert summary["val_rose_above_best_at"] == 1
    assert summary["val_regression"] > 0

    # an orbit that fades while beta and sr stay in band is NOT reported as drift:
    # making the code sparse lowers spontaneous activity in everyone
    held = [_row(0, 0.90, 0.54, 0.90), _row(1, 0.90, 0.20, 0.86)]
    assert probe.summarise(held)["verdict"] == "in-band"


def test_cli_writes_the_trajectory_and_summary(tmp_path):
    data = tmp_path / "rows.jsonl"
    rows = [
        {
            "input": f"<al_in> v=0.{i:02d} a=0.100 d=-0.200 fatigue=0.300 stress=0.100 "
            f"health=0.600 mode=neutral intent=math_query dt=0.500 | {200 + i} - {i}",
            "output": f"{200}\n<al_out> v=0.{i:02d} a=0.100 d=-0.200 fatigue=0.300 "
            f"stress=0.100 health=0.600 mode=neutral intent=math_query",
        }
        for i in range(20)
    ]
    data.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    report = tmp_path / "stability.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "probe_stability.py"),
            "--data",
            str(data),
            "--rows",
            "16",
            "--epochs",
            "2",
            "--every",
            "1",
            "--d-emb",
            "8",
            "--d-hidden",
            "8",
            "--device",
            "cpu",
            "--report",
            str(report),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert len(payload["trajectory"]) == 2
    assert set(payload["summary"]) >= {"beta", "orbit_end", "verdict", "val_best_epoch"}
    assert "orbit" in payload["trajectory"][0]
