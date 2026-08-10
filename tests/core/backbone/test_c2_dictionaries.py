# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""步驟 C2：MultimodalDictionary 協定 + ED3N/GARDEN adapter + backbone 統一查詢。

里程碑（§7 步驟 C）：字典統一協定有 2+ 實作。

驗證：
- `MultimodalDictionary` 為 runtime_checkable protocol，adapter 具備其人。
- `Ed3nDictionaryAdapter` / `GardenDictionaryAdapter` / `InMemoryDictionary`
  都提供 modality/encode/register_entry/query/size 統一介面。
- `backbone.register_dictionary` + `query_dictionary`/`encode_dictionaries`
  可跨字典查詢，並對缺失方法（如沒有 query）優雅降級。
"""

import pytest

from ai.ed3n.dictionary_layer import DictionaryLayer
from core.backbone import get_backbone, reset_backbone
from core.backbone.contracts import MultimodalDictionary
from core.backbone.dicts import (
    Ed3nDictionaryAdapter,
    GardenDictionaryAdapter,
    InMemoryDictionary,
)


@pytest.fixture(autouse=True)
def _fresh():
    reset_backbone()
    yield
    reset_backbone()


@pytest.fixture
def ed3n_adapter():
    layer = DictionaryLayer()
    layer.add_entry("greeting", surface_forms={"zh": "你好"})
    layer.add_entry("farewell", surface_forms={"zh": "再見"})
    return Ed3nDictionaryAdapter(layer)


@pytest.fixture
def garden_adapter():
    try:
        from ai.garden.dictionary import VectorDictionary

        d = VectorDictionary(compatibility_mode=True)
        d.add_entry("g1", surface_forms={"zh": "你好"})
        d.add_entry("g2", surface_forms={"zh": "學習"})
        return GardenDictionaryAdapter(d)
    except Exception as exc:  # pragma: no cover - 環境缺依賴
        pytest.skip(f"VectorDictionary unavailable: {exc}")


class TestProtocol:
    def test_runtime_checkable(self):
        assert isinstance(InMemoryDictionary("space"), MultimodalDictionary)

    def test_ed3n_adapter_is_protocol(self, ed3n_adapter):
        assert isinstance(ed3n_adapter, MultimodalDictionary)

    def test_garden_adapter_is_protocol(self, garden_adapter):
        assert isinstance(garden_adapter, MultimodalDictionary)

    def test_modality(self):
        assert InMemoryDictionary("space").modality() == "space"
        assert InMemoryDictionary("image").modality() == "image"


class TestInMemoryDictionary:
    def test_register_and_size(self):
        d = InMemoryDictionary("space")
        assert d.register_entry("sword", "一把劍")
        assert d.register_entry("potion", "一瓶藥水")
        assert d.size() == 2

    def test_encode_and_query(self):
        d = InMemoryDictionary("space")
        d.register_entry("sword", "一把劍")
        d.register_entry("potion", "一瓶藥水")
        hits = d.query("給我一把劍", top_k=5)
        assert len(hits) == 1
        key, score, payload = hits[0]
        assert key == "sword"
        assert payload == "一把劍"
        assert score > 0

    def test_save_load_roundtrip(self, tmp_path):
        d = InMemoryDictionary("space")
        d.register_entry("sword", "一把劍")
        p = str(tmp_path / "space.json")
        assert d.save(p)
        d2 = InMemoryDictionary("image")
        assert d2.load(p)
        assert d2.modality() == "space"
        assert d2.query("sword")[0][2] == "一把劍"


class TestEd3nAdapter:
    def test_encode_returns_keys(self, ed3n_adapter):
        keys = ed3n_adapter.encode("你好")
        assert len(keys) >= 1
        assert isinstance(keys, list)

    def test_query_payloads(self, ed3n_adapter):
        hits = ed3n_adapter.query("你好", top_k=5)
        assert len(hits) >= 1
        key, score, payload = hits[0]
        assert key
        assert 0.0 <= score <= 1.0

    def test_size_reflects_entries(self, ed3n_adapter):
        assert ed3n_adapter.size() == 2


class TestGardenAdapter:
    def test_encode_and_query(self, garden_adapter):
        keys = garden_adapter.encode("你好")
        assert len(keys) >= 1
        hits = garden_adapter.query("你好", top_k=5)
        assert len(hits) >= 1
        key, score, _payload = hits[0]
        assert key
        assert isinstance(score, float)

    def test_size(self, garden_adapter):
        assert garden_adapter.size() == 2


class TestBackboneDictionaryQuery:
    def test_query_dictionary_aggregates(self, ed3n_adapter, tmp_path):
        bb = get_backbone()
        bb.register_dictionary("ed3n", ed3n_adapter)
        space = InMemoryDictionary("space")
        space.register_entry("sword", "一把劍")
        bb.register_dictionary("space", space)

        results = bb.query_dictionary("你好", top_k=5)
        assert len(results) >= 1
        names = {r["name"] for r in results}
        assert "ed3n" in names
        for r in results:
            assert r["key"]
            assert "score" in r

        # 空間字典對「劍」才有 hit，對「你好」無 hit → 不會炸
        results2 = bb.query_dictionary("請給一把劍")
        assert any(r["name"] == "space" for r in results2)

    def test_encode_dictionaries(self, ed3n_adapter):
        bb = get_backbone()
        bb.register_dictionary("ed3n", ed3n_adapter)
        out = bb.encode_dictionaries("你好")
        assert "ed3n" in out
        assert isinstance(out["ed3n"], list)

    def test_dictionary_without_query_degrades(self):
        bb = get_backbone()
        # 沒有 query 方法的字典：query_dictionary 應跳過不炸
        class NoQuery:
            def encode(self, input_data, **kwargs):
                return ["x"]

        bb.register_dictionary("noquery", NoQuery())
        assert bb.query_dictionary("anything") == []