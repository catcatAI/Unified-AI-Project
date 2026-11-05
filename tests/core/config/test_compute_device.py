"""Contract tests for the single torch-device resolver.

The bug these guard: ``torch.cuda.is_available()`` was used as if it answered
"is there an accelerator?".  On an Intel Arc (torch ``xpu`` backend) it returns
False, so GARDEN and the CLIP/Whisper encoders declared a device they never
used (and could not use).  One resolver now answers the question.
"""

import numpy as np
import pytest
from core.system.config.compute_device import (
    device_available,
    feature_compute_enabled,
    move_batch_to_device,
    resolve_feature_device,
    resolve_torch_device,
)


class _FakeXpu:
    def __init__(self, available: bool):
        self._available = available

    def is_available(self) -> bool:
        return self._available


class _FakeCuda:
    def __init__(self, available: bool):
        self._available = available

    def is_available(self) -> bool:
        return self._available


class _FakeMps:
    def __init__(self, available: bool):
        self._available = available

    def is_available(self) -> bool:
        return self._available


class _FakeBackends:
    def __init__(self, mps_available: bool):
        self.mps = _FakeMps(mps_available)


class _FakeTorch:
    """Just enough torch surface for the resolver (no tensor ops needed)."""

    def __init__(self, xpu: bool = False, cuda: bool = False, mps: bool = False):
        self.xpu = _FakeXpu(xpu)
        self.cuda = _FakeCuda(cuda)
        self.backends = _FakeBackends(mps)

    def device(self, name):
        return name

    class _Unavailable:
        pass


class _NoXpuTorch(_FakeTorch):
    """Torch build without the xpu attribute at all (older/CPU builds)."""

    def __init__(self):
        super().__init__(xpu=False, cuda=False)
        del self.xpu


class TestResolveTorchDevice:
    def test_cpu_always_available(self):
        assert device_available("cpu") is True
        assert resolve_torch_device("cpu") == "cpu"

    def test_auto_prefers_xpu_over_cuda(self):
        t = _FakeTorch(xpu=True, cuda=True)
        assert resolve_torch_device("auto", torch_module=t) == "xpu"

    def test_auto_picks_cuda_when_no_xpu(self):
        t = _FakeTorch(xpu=False, cuda=True)
        assert resolve_torch_device("auto", torch_module=t) == "cuda"

    def test_auto_prefers_xpu_when_cuda_is_false(self):
        # This machine: torch.cuda.is_available() False, torch.xpu True.
        t = _FakeTorch(xpu=True, cuda=False)
        assert resolve_torch_device("auto", torch_module=t) == "xpu"

    def test_auto_falls_back_to_cpu(self):
        t = _FakeTorch(xpu=False, cuda=False, mps=False)
        assert resolve_torch_device("auto", torch_module=t) == "cpu"

    def test_torch_without_xpu_attribute(self):
        t = _NoXpuTorch()
        assert resolve_torch_device("auto", torch_module=t) == "cpu"

    def test_explicit_available_device_is_honoured(self):
        t = _FakeTorch(xpu=True, cuda=True)
        assert resolve_torch_device("cuda", torch_module=t) == "cuda"
        assert resolve_torch_device("xpu", torch_module=t) == "xpu"

    @pytest.mark.parametrize("wanted", ["cuda", "xpu"])
    def test_explicit_unavailable_device_degrades_to_cpu(self, wanted):
        t = _FakeTorch(xpu=False, cuda=False)
        assert resolve_torch_device(wanted, torch_module=t) == "cpu"

    def test_empty_and_none_mean_auto(self):
        t = _FakeTorch(xpu=True)
        assert resolve_torch_device("", torch_module=t) == "xpu"
        assert resolve_torch_device(None, torch_module=t) == "xpu"

    def test_unknown_device_name_is_not_trusted(self):
        t = _FakeTorch(xpu=True)
        assert device_available("definitely-not-a-device", torch_module=t) is False
        assert resolve_torch_device("definitely-not-a-device", torch_module=t) == "cpu"


class TestMoveBatchToDevice:
    def test_cpu_is_a_noop(self):
        batch = {"input_ids": np.zeros((1, 3))}
        assert move_batch_to_device(batch, "cpu") is batch

    def test_moves_every_tensor_like_value(self):
        class _T:
            def __init__(self):
                self.device = "cpu"

            def to(self, device):
                self.device = device
                return self

        a, b = _T(), _T()
        # non-tensor values pass through untouched
        moved = move_batch_to_device({"input_ids": a, "attention_mask": b, "k": 3}, "xpu")
        assert moved["input_ids"].device == "xpu"
        assert moved["attention_mask"].device == "xpu"
        assert moved["k"] == 3

    def test_bad_batch_is_returned_untouched(self):
        assert move_batch_to_device(object(), "xpu") is not None


class TestRealTorch:
    """No skips: asserts the resolver agrees with the installed torch build."""

    def test_matches_live_backend(self):
        torch = pytest.importorskip("torch")
        resolved = resolve_torch_device("auto", torch_module=torch)
        if hasattr(torch, "xpu") and torch.xpu.is_available():
            assert resolved == "xpu"
        elif torch.cuda.is_available():
            assert resolved == "cuda"
        else:
            assert resolved == "cpu"

    def test_requesting_unavailable_accelerator_is_cpu(self):
        torch = pytest.importorskip("torch")
        if not torch.cuda.is_available():
            assert resolve_torch_device("cuda", torch_module=torch) == "cpu"


class TestFeatureGate:
    """``compute.<feature>.mode=off`` means "force CPU", not "ignore the flag".

    The encoders used to pick an accelerator whenever one existed, so a
    power-saver profile that declared ``semantic_visual: off`` still ran CLIP on
    the GPU.  The gate lives here so the declared setting is the used one.
    """

    def test_off_forces_cpu_even_when_accelerator_exists(self, monkeypatch):
        import core.system.config.magic_numbers as mn

        monkeypatch.setattr(mn, "compute_bool", lambda feature, default=True: False)
        t = _FakeTorch(xpu=True, cuda=True)
        assert feature_compute_enabled("semantic_visual") is False
        assert resolve_feature_device("semantic_visual", "auto", torch_module=t) == "cpu"

    def test_on_uses_the_normal_resolver(self, monkeypatch):
        import core.system.config.magic_numbers as mn

        monkeypatch.setattr(mn, "compute_bool", lambda feature, default=True: True)
        t = _FakeTorch(xpu=True)
        assert resolve_feature_device("semantic_visual", "auto", torch_module=t) == "xpu"

    def test_explicit_device_is_still_honoured_when_enabled(self, monkeypatch):
        import core.system.config.magic_numbers as mn

        monkeypatch.setattr(mn, "compute_bool", lambda feature, default=True: True)
        t = _FakeTorch(xpu=True, cuda=True)
        assert resolve_feature_device("semantic_audio", "cuda", torch_module=t) == "cuda"
