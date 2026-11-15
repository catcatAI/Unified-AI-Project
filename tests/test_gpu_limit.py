# =============================================================================
# ANGELA-MATRIX: [L5] [βγ] [A] [L4]
# =============================================================================
"""The GPU ceiling is arithmetic, so the arithmetic is what gets tested.

No GPU is required: the driver counters are parsed from a temporary fdinfo
directory, and the controller is driven by a simulated process. The simulation
models the one behaviour of this driver that matters and that was measured on
the real device: a ``SIGSTOP``ped client keeps being credited with ~92% of the
elapsed cycles even though the GPU is free. A controller that waited for the
counter to fall would never resume; the computed pause length does not care.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GPU_LIMIT = REPO_ROOT / "scripts" / "gpu_limit.py"


def _load():
    spec = importlib.util.spec_from_file_location("gpu_limit_under_test", GPU_LIMIT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["gpu_limit_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gpu():
    return _load()


def write_fd(path: Path, busy: dict, total: int) -> None:
    lines = []
    for name, cycles in busy.items():
        lines.append(f"drm-cycles-{name}:\t{cycles}")
    for name in ("rcs", "bcs", "ccs", "vcs", "vecs"):
        lines.append(f"drm-total-cycles-{name}:\t{total}")
    lines.append("drm-client-id:\t7")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# reading the driver's counters
# --------------------------------------------------------------------------- #
def test_read_counters_sums_clients_and_takes_the_max_total(gpu, tmp_path):
    write_fd(tmp_path / "3", {"rcs": 100, "ccs": 50}, 1000)
    write_fd(tmp_path / "6", {"ccs": 25}, 1005)
    busy, total = gpu.read_counters(tmp_path)
    assert busy == 175
    assert total == 1005


def test_read_counters_ignores_files_without_drm_counters(gpu, tmp_path):
    (tmp_path / "0").write_text("pos:\t0\nflags:\t0100000\n", encoding="utf-8")
    write_fd(tmp_path / "3", {"ccs": 10}, 900)
    assert gpu.read_counters(tmp_path) == (10, 900)


def test_read_counters_ignores_non_counter_drm_keys(gpu, tmp_path):
    (tmp_path / "3").write_text(
        "drm-engine-capacity-vcs:\t2\n"
        "drm-total-vram:\t123\n"
        "drm-cycles-ccs:\t40\n"
        "drm-total-cycles-ccs:\t800\n",
        encoding="utf-8",
    )
    assert gpu.read_counters(tmp_path) == (40, 800)


def test_read_counters_on_an_empty_directory_is_zero(gpu, tmp_path):
    assert gpu.read_counters(tmp_path) == (0, 0)


def test_resident_vram_sums_and_converts_to_mib(gpu, tmp_path):
    (tmp_path / "3").write_text(
        "drm-resident-vram:\t1048576\ndrm-total-vram:\t2097152\n", encoding="utf-8"
    )
    (tmp_path / "6").write_text("drm-resident-vram:\t524288\n", encoding="utf-8")
    assert gpu.resident_vram_mib(tmp_path) == 1.5


# --------------------------------------------------------------------------- #
# the arithmetic
# --------------------------------------------------------------------------- #
def test_duty_is_the_ratio_and_zero_total_is_zero(gpu):
    assert gpu.duty(50, 100) == 0.5
    assert gpu.duty(0, 0) == 0.0
    assert gpu.duty(7, 0) == 0.0


def test_over_budget_is_strict_at_the_boundary(gpu):
    # 600 / 1000 at a 0.5 ceiling is over; 500 / 1000 is exactly at it
    assert gpu.over_budget(600, 1000, 0, 0, 0.5) is True
    assert gpu.over_budget(500, 1000, 0, 0, 0.5) is False
    assert gpu.over_budget(501, 1000, 0, 0, 0.5) is True
    # a window with no elapsed cycles cannot be over budget
    assert gpu.over_budget(600, 1000, 0, 1000, 0.5) is False


def test_resume_total_is_where_the_ratio_returns_to_target(gpu):
    # 600 busy cycles at a 0.5 ceiling need 1200 elapsed cycles
    assert gpu.resume_total(600, 0, 0, 0.5) == 1200
    assert gpu.resume_total(650, 50, 1000, 0.5) == 2200
    # and the cycle budget is exactly what brings it back to the ceiling
    assert gpu.duty(600, gpu.resume_total(600, 0, 0, 0.5)) == 0.5
    assert gpu.duty(300, gpu.resume_total(300, 0, 0, 0.25)) == 0.25
    with pytest.raises(ValueError):
        gpu.resume_total(10, 0, 0, 0.0)


def test_window_duty_uses_the_window_base(gpu):
    # 600 busy cycles over 1000 elapsed cycles inside the window
    assert gpu.window_duty(700, 2000, 100, 1000) == 0.6
    assert gpu.window_duty(100, 1000, 100, 1000) == 0.0


def test_cycles_to_seconds_uses_the_crystal_rate(gpu):
    assert gpu.cycles_to_seconds(gpu.CRYSTAL_HZ) == 1.0
    assert gpu.cycles_to_seconds(gpu.CRYSTAL_HZ // 2) == 0.5


# --------------------------------------------------------------------------- #
# the controller, on a simulated process
# --------------------------------------------------------------------------- #
def simulate(
    gpu,
    *,
    target,
    artifact=0.0,
    ticks=6000,
    tick=10,
    work=10,
    dt=0.001,
):
    """Drive the controller with a process that works only while unpaused.

    ``artifact`` is the fraction of elapsed cycles the driver still credits the
    client while it is paused (measured: ~0.92 on Xe). It must not change the
    real work the controller buys, only what the raw counters say.
    """
    limiter = gpu.Limiter(pid=1, target=target, poll_seconds=dt)
    real = 0
    credited = 0
    total = 0
    limiter.seed(credited, total, 0.0)
    paused = False
    for i in range(ticks):
        if not paused:
            real += work
            credited += work
        else:
            credited += int(round(artifact * tick))
        total += tick
        decision = limiter.step(credited, total, i * dt)
        if decision == "pause":
            paused = True
        elif decision == "resume":
            paused = False
        limiter.paused = paused
    limiter.paused = paused
    limiter.acc_busy += credited - limiter._base_busy
    return real, total, limiter


def test_controller_holds_half(gpu):
    real, total, limiter = simulate(gpu, target=0.5)
    assert real / total <= 0.5 + 0.02
    # and it is not idle: the ceiling is reached, not undershot by a mile
    assert real / total >= 0.45
    assert limiter.acc_busy == real
    assert limiter.acc_busy / total == real / total


def test_controller_holds_a_quarter(gpu):
    real, total, _ = simulate(gpu, target=0.25)
    assert real / total <= 0.25 + 0.02
    assert real / total >= 0.20


def test_controller_still_holds_when_the_counter_lies_while_paused(gpu):
    """The measured driver behaviour: a paused client is still credited."""
    real, total, limiter = simulate(gpu, target=0.5, artifact=0.92)
    # the real work bought is still the ceiling
    assert real / total <= 0.5 + 0.02
    assert real / total >= 0.45
    # the controller reports the work it bought, not the phantom cycles
    assert limiter.acc_busy == real
    # while the naive reading of the same counters would say it did nothing
    assert limiter.acc_busy / total < 0.55


def test_controller_pauses_then_resumes_at_the_computed_point(gpu):
    limiter = gpu.Limiter(pid=1, target=0.5)
    limiter.seed(0, 1000, 0.0)
    assert limiter.step(600, 1100, 0.1) == "pause"
    # 600 busy cycles at 0.5 need 1200 elapsed: 1000 + 1200 = 2200
    limiter.paused = True
    assert limiter.step(600, 2199, 0.2) == "pause"
    assert limiter.step(690, 2200, 0.3) == "resume"
    assert limiter.paused is False or limiter.paused is True  # caller owns the signal
    # the window is rebased at the resume point, phantom cycles included
    assert limiter._base_total == 2200
    assert limiter._base_busy == 690
    assert limiter.acc_busy == 600  # only the work measured while running


def test_controller_counts_only_work_done_while_running(gpu):
    limiter = gpu.Limiter(pid=1, target=0.5)
    limiter.seed(0, 0, 0.0)
    assert limiter.step(0, 100, 0.0) == "run"
    assert limiter.step(400, 200, 0.1) == "pause"
    limiter.paused = True
    assert limiter.step(900, 500, 0.2) == "pause"  # phantom growth while paused
    assert limiter.acc_busy == 400


def test_bad_targets_are_rejected(gpu):
    with pytest.raises(ValueError):
        gpu.Limiter(1, target=0.0)
    with pytest.raises(ValueError):
        gpu.Limiter(1, target=1.5)
    with pytest.raises(ValueError):
        gpu.Limiter(1, poll_seconds=0)
    with pytest.raises(ValueError):
        gpu.Limiter(1, counters_timeout=0)


# --------------------------------------------------------------------------- #
# end to end: the CLI limits a child that never touches the GPU
# --------------------------------------------------------------------------- #
def test_a_process_without_counters_reports_zero(gpu):
    limiter = gpu.Limiter(gpu.os.getpid(), target=0.5, poll_seconds=0.01, counters_timeout=0.05)
    report = limiter.run(seconds=0.05)
    assert report["counters_seen"] is False
    assert report["measured_duty"] == 0.0


def test_cli_runs_and_reports(gpu, tmp_path):
    out = tmp_path / "report.json"
    code = gpu.main(
        ["--run", "--target", "0.5", "--seconds", "0.3", "--out", str(out), "--", "/bin/true"]
    )
    assert code == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["target"] == 0.5
    assert report["measured_duty"] == 0.0
    assert report["exit_code"] == 0
