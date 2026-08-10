# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""後續計畫 §2：多模態字典語義化 — score 標準化 + sources()。

驗證：
- query 後 score 被 clamp/scale 到 0..1（含 None、負值、>1）。
- backbone.dictionary_sources() 列出 {name, modality, mountable}。
- mountable 字典註冊後 sources 標記 mountable=True。
"""

import pytest
from core.backbone import get_backbone, reset_backbone
from core.backbone.dicts import InMemoryDictionary
from core.backbone.registry import _normalize_score


@pytest.fixture(autouse=True)
def _fresh():
    reset_backbone()
    yield
    reset_backbone()


class TestScoreNormalization:
    def test_in_range_preserved(self):
        assert _normalize_score(0.5) == 0.5
        assert _normalize_score(0.0) == 0.0
        assert _normalize_score(1.0) == 1.0

    def test_out_of_range_clamped(self):
        assert _normalize_score(1.5) == 1.0
        assert _normalize_score(-3) == 0.0

    def test_none_and_bad_values(self):
        assert _normalize_score(None) == 0.0
        assert _normalize_score("abc") == 0.0
        assert _normalize_score("0.8") == 0.8

    def test_query_scores_normalized(self):
        from core.backbone.registry import DictionaryRegistry

        reg = DictionaryRegistry()

        class FakeDict:
            modality = "fake"

            def query(self, input_data, top_k=5, **kwargs):
                return [
                    {"key": "a", "score": 1.7},
                    {"key": "b", "score": 0.4},
                    {"key": "c"},  # 無 score → 0.0
                ]

        reg.register("fake", FakeDict())
        out = reg.query("__all__", "x", top_k=5)
        scores = {r["key"]: r["score"] for r in out}
        assert scores["a"] == 1.0
        assert scores["b"] == 0.4
        assert scores["c"] == 0.0
        # 依 score 排序
        assert out[0]["key"] == "a"


class TestDictionarySources:
    def test_sources_lists_names_and_modality(self):
        bb = get_backbone()
        d = InMemoryDictionary(modality="card")
        d.register_entry("k1", "hello")
        bb.register_dictionary("cards", d)
        sources = bb.dictionary_sources()
        entry = next(s for s in sources if s["name"] == "cards")
        assert entry["modality"] == "card"
        assert entry["mountable"] is False

    def test_mountable_dictionary_marked(self):
        bb = get_backbone()
        d = InMemoryDictionary(modality="space")
        bb.register_mountable("space_dict", d)
        sources = bb.dictionary_sources()
        entry = next(s for s in sources if s["name"] == "space_dict")
        assert entry["mountable"] is True
        assert entry["modality"] == "space"

    def test_dictionary_without_modality_unknown(self):
        from core.backbone.registry import DictionaryRegistry

        reg = DictionaryRegistry()

        class NoModality:
            def query(self, input_data, top_k=5, **kwargs):
                return []

        reg.register("plain", NoModality())
        src = reg.sources()
        entry = next(s for s in src if s["name"] == "plain")
        assert entry["modality"] == "Unknown"
