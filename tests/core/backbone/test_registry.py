# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""主幹線註冊表測試（§6 registry.py + 步驟 A #2 單例註冊）。"""

import pytest
from core.backbone.registry import (
    AxisRegistry,
    BackboneRegistries,
    DictionaryRegistry,
    MatrixRegistry,
    ModuleRegistry,
    RegistryError,
    TranslatorRegistry,
)


class _FakeMatrix:
    def get(self, key, default=None):
        return {"focus": 0.8}.get(key, default)

    def update_alpha(self, data):
        self.last_update = ("alpha", data)


class _FakeAxis:
    def __init__(self):
        self._store = {}

    def get(self, key, default=None):
        return self._store.get(key, default)

    def set(self, key, value):
        self._store[key] = value

    def update(self, data):
        self._store.update(data)


class TestMatrixRegistry:
    def test_register_and_primary(self):
        reg = MatrixRegistry()
        m = _FakeMatrix()
        reg.register("state_matrix4d", m)
        assert reg.primary() is m
        assert reg.count() == 1

    def test_duplicate_allowed_for_matrix(self):
        reg = MatrixRegistry()
        reg.register("m", _FakeMatrix())
        reg.register("m", _FakeMatrix())  # allow_replace=True
        assert reg.count() == 1

    def test_unregister(self):
        reg = MatrixRegistry()
        reg.register("m", _FakeMatrix())
        assert reg.unregister("m") is True
        assert reg.unregister("m") is False


class TestAxisRegistry:
    def test_register_write_read(self):
        reg = AxisRegistry()
        axis = _FakeAxis()
        reg.register("alpha", axis)
        assert reg.write("alpha", "focus", 0.8) is True
        assert reg.read("alpha", "focus") == 0.8

    def test_update_multiple(self):
        reg = AxisRegistry()
        axis = _FakeAxis()
        reg.register("beta", axis)
        assert reg.update("beta", {"curiosity": 0.9, "focus": 0.7}) is True
        assert axis.get("curiosity") == 0.9

    def test_write_missing_axis_false(self):
        reg = AxisRegistry()
        assert reg.write("gamma", "x", 1) is False

    def test_read_missing_axis_default(self):
        reg = AxisRegistry()
        assert reg.read("gamma", "x", default=42) == 42


class TestModuleRegistry:
    def test_register_mount_unmount_hooks(self):
        reg = ModuleRegistry()
        calls = []
        reg.register(
            "router",
            object(),
            on_mount=lambda: calls.append("m"),
            on_unmount=lambda: calls.append("u"),
        )
        assert reg.mount("router") is True
        assert reg.unmount("router") is True
        assert calls == ["m", "u"]

    def test_mount_unknown_false(self):
        reg = ModuleRegistry()
        assert reg.mount("nope") is False

    def test_register_without_hooks(self):
        reg = ModuleRegistry()
        reg.register("chat", object())
        assert reg.mount("chat") is True
        assert reg.unmount("chat") is True


class TestDictionaryRegistry:
    def test_register_get(self):
        reg = DictionaryRegistry()
        reg.register("cc_cedict", object())
        assert reg.has("cc_cedict")
        assert reg.get("cc_cedict") is not None

    def test_register_mountable(self):
        reg = DictionaryRegistry()
        reg.register("ed3n_dict", object())
        reg.register_mountable("ed3n_dict", object())
        assert reg.is_mountable("ed3n_dict")
        assert reg.get_mountable("ed3n_dict") is not None


class TestTranslatorRegistry:
    def test_register_rule_object(self):
        reg = TranslatorRegistry()

        class Rule:
            name = "test"

            def can_translate(self, source, target, direction):
                return source == "llm" and target == "matrix"

            def translate(self, data, direction="down", **kwargs):
                return f"translated:{data}"

        reg.register_rule("r", Rule())
        assert reg.find("llm", "matrix", "down") is not None
        assert reg.find("matrix", "llm", "down") is None

    def test_register_func(self):
        reg = TranslatorRegistry()
        reg.register_func(
            "f",
            lambda s, t, d: s == "a" and t == "b",
            lambda data, direction="down", **kwargs: f"f:{data}",
        )
        rule = reg.find("a", "b", "up")
        assert rule is not None
        assert rule.translate("x", direction="up") == "f:x"

    def test_duplicate_raises(self):
        reg = TranslatorRegistry()
        reg.register_rule("dup", object())
        with pytest.raises(RegistryError):
            reg.register_rule("dup", object())


class TestBackboneRegistries:
    def test_all_five_present(self):
        regs = BackboneRegistries()
        assert regs.matrices is not None
        assert regs.axes is not None
        assert regs.modules is not None
        assert regs.dictionaries is not None
        assert regs.translators is not None

    def test_clear_all(self):
        regs = BackboneRegistries()
        regs.matrices.register("m", _FakeMatrix())
        regs.modules.register("r", object())
        regs.clear_all()
        assert regs.matrices.count() == 0
        assert regs.modules.count() == 0
