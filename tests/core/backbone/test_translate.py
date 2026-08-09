# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""轉譯器測試（§5.3 translate.py — 註冊與執行）。"""

import pytest
from core.backbone.translate import BackboneTranslator


class _UpperRule:
    name = "upper"

    def can_translate(self, source, target, direction):
        return source == "llm" and target == "matrix"

    def translate(self, data, direction="down", **kwargs):
        return str(data).upper()


class TestBackboneTranslator:
    @pytest.fixture
    def translator(self):
        from core.backbone import get_backbone

        return get_backbone().translator

    def test_register_rule_and_translate(self, translator):
        translator.register("upper", _UpperRule())
        result = translator.translate("llm", "matrix", "hello")
        assert result == "HELLO"

    def test_no_matching_rule_identity(self, translator):
        result = translator.translate("llm", "garden", {"x": 1})
        assert result == {"x": 1}

    def test_register_func(self, translator):
        translator.register_func(
            "lower",
            lambda s, t, d: s == "matrix" and t == "llm",
            lambda data, direction="down", **kwargs: str(data).lower(),
        )
        assert translator.translate("matrix", "llm", "ABC") == "abc"

    def test_can_translate(self, translator):
        translator.register("upper", _UpperRule())
        assert translator.can_translate("llm", "matrix", "down")
        assert not translator.can_translate("matrix", "llm", "down")

    def test_names(self, translator):
        translator.register("upper", _UpperRule())
        translator.register_func("lower", lambda *a: False, lambda *a, **k: None)
        assert set(translator.names()) == {"upper", "lower"}


class TestBackboneTranslateIntegration:
    def test_backbone_translate_method(self):
        from core.backbone import get_backbone

        bb = get_backbone()
        bb.register_translator("upper", _UpperRule())
        assert bb.translate("llm", "matrix", "abc") == "ABC"

    def test_translator_registered_in_summary(self):
        from core.backbone import get_backbone

        bb = get_backbone()
        bb.register_translator("upper", _UpperRule())
        assert bb.summary()["translators"] >= 1
