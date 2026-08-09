# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""Backbone 主幹線整合測試（§6 backbone.py + 步驟 A 單例註冊）。"""

import pytest
from core.backbone import get_backbone, reset_backbone
from core.backbone.contracts import Envelope, PairStatus


@pytest.fixture(autouse=True)
def _fresh():
    reset_backbone()
    yield
    reset_backbone()


@pytest.fixture
def bb():
    return get_backbone()


class TestBackboneSingleton:
    def test_get_backbone_singleton(self):
        assert get_backbone() is get_backbone()

    def test_reset_backbone(self):
        a = get_backbone()
        reset_backbone()
        b = get_backbone()
        assert a is not b

    def test_summary_structure(self, bb):
        s = bb.summary()
        assert set(s.keys()) == {
            "matrices",
            "axes",
            "modules",
            "dictionaries",
            "translators",
            "mountables",
            "pairs",
            "io_pairs_domain_bound",
        }


class TestBackboneRegistration:
    def test_register_matrix_primary(self, bb):
        matrix = object()
        bb.register_matrix("state_matrix4d", matrix)
        assert bb.primary_matrix() is matrix
        assert bb.registries.matrices.count() == 1

    def test_register_axis(self, bb):
        axis = object()
        bb.register_axis("alpha", axis)
        assert bb.registries.axes.has("alpha")

    def test_register_module_get(self, bb):
        module = object()
        bb.register_module("router", module)
        assert bb.get_module("router") is module

    def test_register_dictionary(self, bb):
        dic = object()
        bb.register_dictionary("cc_cedict", dic)
        assert bb.get_dictionary("cc_cedict") is dic

    def test_register_learning_training(self, bb):
        bb.register_learning("continuous", lambda: None)
        bb.register_training("joint", lambda: None)
        assert bb.get_module("learning:continuous") is not None
        assert bb.get_module("training:joint") is not None

    def test_register_module_with_hooks(self, bb):
        calls = []
        bb.register_module(
            "ed3n",
            object(),
            on_mount=lambda: calls.append("m"),
            on_unmount=lambda: calls.append("u"),
        )
        assert bb.registries.modules.mount("ed3n") is True
        assert bb.registries.modules.unmount("ed3n") is True
        assert calls == ["m", "u"]


class TestBackboneConfig:
    def test_config_bool_default(self, bb):
        assert bb.config_bool("neural_bridge", default=False) is False

    def test_config_override(self, bb):
        bb.config.set_override("neural_bridge", True)
        assert bb.config_bool("neural_bridge", default=False) is True

    def test_config_mode(self, bb):
        mode = bb.config_mode("garden_snn", default="auto")
        assert mode in ("auto", "on", "off")


class TestBackboneState:
    def test_write_axis_via_registry(self, bb):
        class _FakeAxis:
            def __init__(self):
                self._store = {}

            def get(self, key, default=None):
                return self._store.get(key, default)

            def set(self, key, value):
                self._store[key] = value

        axis = _FakeAxis()
        bb.register_axis("alpha", axis)
        assert bb.state.write_axis("alpha", "focus", 0.8) is True
        assert axis.get("focus") == 0.8

    def test_read_axis_default(self, bb):
        assert bb.state.read_axis("gamma", "speed", default=0.5) == 0.5


class TestBackboneIOIntegration:
    def test_send_down_chat_with_pairs(self, bb):
        bb.io.register_down("chat", lambda e, **kw: {"reply": "hello"})
        result = bb.send_down(Envelope(payload="hi", kind="chat"))
        assert result == {"reply": "hello"}
        # 成對追蹤：send_down 建立並配對，無殘留 pending
        assert bb.io.pending() == []

    def test_send_down_orphan_detected(self, bb):
        bb.io.register_down("slow", lambda e, **kw: {"ok": True})
        pid = bb.pairs.submit(Envelope(payload="x", kind="slow"), timeout=0.05)
        import time

        time.sleep(0.1)
        assert len(bb.io.orphans()) >= 1


class TestBackboneMountableRegistry:
    def test_register_mountable_dictionary(self, bb):
        resource = object()
        bb.register_mountable("ed3n_dict", resource, idle_timeout=100)
        # 同時登記進 dictionary registry 的 mountable 表
        assert bb.registries.dictionaries.is_mountable("ed3n_dict")


class TestClear:
    def test_clear_resets_everything(self, bb):
        bb.register_matrix("m", object())
        bb.register_module("r", object())
        bb.register_translator("t", object())
        bb.clear()
        s = bb.summary()
        assert s["matrices"] == 0
        assert s["modules"] == 0
        assert s["translators"] == 0
