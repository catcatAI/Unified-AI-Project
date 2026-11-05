"""GARDEN TensorSNNCore device contract.

Before this test file, ``TensorSNNCore(device="cuda")`` stored the string and
built every tensor on the CPU: GARDEN declared a GPU and silently used none.
Worse, the forward pass called ``np.argpartition`` on the potential vector,
which cannot consume an accelerator tensor — so "make device real" without
fixing that would crash on the first forward.

These tests pin three things:
  1. ``self.device`` is the device the weights actually live on;
  2. an accelerator (when present) produces numerically identical forward
     outputs and Hebbian updates to CPU;
  3. an unavailable device degrades to CPU instead of raising.
"""

import numpy as np
import pytest
from ai.garden.snn_core import TensorSNNCore, _get_backend
from core.system.config.compute_device import resolve_torch_device

KEY_COUNT = 24


def _build(device: str) -> TensorSNNCore:
    core = TensorSNNCore(timesteps=4, device=device, max_vocab=0)
    for i in range(KEY_COUNT - 1):
        core.add_relation(f"k{i}", f"k{i + 1}", weight=0.6)
    core.add_relation("k0", "k6", weight=0.9)
    return core


def _live(core: TensorSNNCore) -> np.ndarray:
    V = core.vocab_size
    W = core._W[:V, :V]
    if hasattr(W, "detach"):
        W = W.detach().cpu().numpy()
    return np.asarray(W)


def _accelerator() -> str:
    _xp, is_torch = _get_backend()
    if not is_torch:
        return "cpu"
    return resolve_torch_device("auto")


class TestDeviceIsReal:
    def test_cpu_core_reports_cpu(self):
        core = _build("cpu")
        assert core.device == "cpu"
        W = core._W
        if hasattr(W, "device"):
            assert W.device.type == "cpu"

    def test_stats_expose_the_device(self):
        assert _build("cpu").get_stats()["device"] == "cpu"

    def test_unavailable_device_degrades_to_cpu(self):
        # "cuda" does not exist on an XPU-only or CPU-only box; the core must
        # not build tensors on it.
        if resolve_torch_device("cuda") == "cuda":
            pytest.skip("CUDA is available here")
        core = _build("cuda")
        assert core.device == "cpu"

    def test_backend_without_torch_reports_cpu(self):
        core = TensorSNNCore(timesteps=2, device="xpu")
        # Whatever the backend, the attribute matches the tensor placement.
        if core._W is not None and hasattr(core._W, "device"):
            assert core.device == core._W.device.type


class TestAcceleratorParity:
    def test_forward_and_hebbian_match_cpu(self):
        accel = _accelerator()
        if accel == "cpu":
            pytest.skip("no accelerator on this machine")

        cpu = _build("cpu")
        gpu = _build(accel)
        assert gpu.device == accel
        assert gpu._W.device.type == accel

        cpu_out = cpu.forward({"k0": 1.0})
        gpu_out = gpu.forward({"k0": 1.0})
        assert cpu_out.keys() == gpu_out.keys()
        for key in cpu_out:
            assert gpu_out[key] == pytest.approx(cpu_out[key], abs=1e-6)

        cpu_delta = cpu.hebbian_update({"k0": 1.0}, {"k3": 0.9})
        gpu_delta = gpu.hebbian_update({"k0": 1.0}, {"k3": 0.9})
        assert gpu_delta == pytest.approx(cpu_delta, abs=1e-6)
        assert np.allclose(_live(cpu), _live(gpu), atol=1e-6)

    def test_eviction_compaction_matches_cpu(self):
        accel = _accelerator()
        if accel == "cpu":
            pytest.skip("no accelerator on this machine")

        cpu = _build("cpu")
        gpu = _build(accel)
        cpu.max_vocab = 16
        gpu.max_vocab = 16
        for i in range(KEY_COUNT, KEY_COUNT + 20):
            cpu._register_key(f"k{i}")
            gpu._register_key(f"k{i}")
        assert cpu.vocab_size == gpu.vocab_size == 16
        assert np.allclose(_live(cpu), _live(gpu), atol=1e-6)

    def test_save_load_roundtrip_is_device_independent(self, tmp_path):
        accel = _accelerator()
        if accel == "cpu":
            pytest.skip("no accelerator on this machine")

        gpu = _build(accel)
        path = str(tmp_path / "snn.pt")
        gpu.save(path)
        restored = TensorSNNCore(timesteps=4, device="cpu")
        restored.load(path)
        assert restored.vocab_size == gpu.vocab_size
        assert np.allclose(_live(restored), _live(gpu), atol=1e-6)
        assert restored.forward({"k0": 1.0}) == pytest.approx(gpu.forward({"k0": 1.0}))

    def test_reset_for_retrain_stays_on_device(self):
        accel = _accelerator()
        if accel == "cpu":
            pytest.skip("no accelerator on this machine")

        gpu = _build(accel)
        gpu.reset_for_retrain()
        assert gpu._W.device.type == accel
        assert float((gpu.get_stats()["matrix_density"])) >= 0.0


class TestCpuBackendUnchanged:
    def test_zero_allocation_helper_respects_default(self):
        from ai.garden.snn_core import _zeros

        arr = _zeros((2, 2))
        if hasattr(arr, "device"):
            assert arr.device.type == "cpu"

    def test_forward_still_works_without_accelerator(self):
        core = _build("cpu")
        out = core.forward({"k0": 1.0})
        assert isinstance(out, dict) and out
        assert all(isinstance(v, float) for v in out.values())
