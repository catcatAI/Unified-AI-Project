# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""步驟 C4：物件/空間/語義字典以 MultimodalDictionary 協定加入。

里程碑（§7 步驟 C）：字典統一協定有 2+ 實作（累計 ED3N/GARDEN/semantic/
object/space 共 5 種）。

驗證：
- `KeyValueDictionary`（modality="object" / "space"）可註冊/查詢/存取 payload。
- `SemanticKeyMapperAdapter` 包真實 SemanticKeyMapper，query(latent) 回傳
  [{key, score}]，size 反映索引條數。
- backbone 統一 query 涵蓋多模態混合字典。
"""

import numpy as np
import pytest

from ai.multimodal.semantic_key_mapper import SemanticKeyMapper
from core.backbone import get_backbone, reset_backbone
from core.backbone.contracts import MultimodalDictionary
from core.backbone.dicts import (
    KeyValueDictionary,
    SemanticKeyMapperAdapter,
)


@pytest.fixture(autouse=True)
def _fresh():
    reset_backbone()
    yield
    reset_backbone()


class TestObjectDictionary:
    def test_protocol(self):
        assert isinstance(KeyValueDictionary("object"), MultimodalDictionary)

    def test_register_and_query(self):
        d = KeyValueDictionary("object")
        assert d.modality() == "object"
        assert d.register_entry("sword", {"name": "鐵劍", "material": "iron"})
        assert d.register_entry("pickaxe", {"name": "十字鎬", "material": "wood+iron"})
        assert d.size() == 2
        hits = d.query("一把鐵劍", top_k=5)
        assert len(hits) == 1
        key, score, payload = hits[0]
        assert key == "sword"
        assert payload["material"] == "iron"

    def test_query_no_match(self):
        d = KeyValueDictionary("object")
        d.register_entry("sword", "劍")
        assert d.query("藥水") == []


class TestSpaceDictionary:
    def test_use_as_space_dict(self):
        d = KeyValueDictionary("space")
        d.register_entry("lemonade", {"liquid": "檸檬水", "容器": "杯子"})
        assert d.modality() == "space"
        hits = d.query("玻璃杯裡有檸檬水")
        assert len(hits) == 1
        assert hits[0][0] == "lemonade"


class TestSemanticKeyMapperAdapter:
    def _mk(self):
        mapper = SemanticKeyMapper()
        rng = np.random.default_rng(0)
        for i, key in enumerate([f"c{i}" for i in range(3)]):
            mapper.index_key(key, combined_latent=rng.normal(size=64).astype(np.float32))
        return SemanticKeyMapperAdapter(mapper), mapper

    def test_protocol_and_modality(self):
        adapter, _ = self._mk()
        assert isinstance(adapter, MultimodalDictionary)
        assert adapter.modality() == "semantic"

    def test_size_reflects_index(self):
        adapter, _ = self._mk()
        assert adapter.size() == 3

    def test_query_latent_returns_keys(self):
        adapter, _ = self._mk()
        query = np.ones(64, dtype=np.float32)
        hits = adapter.query(query, top_k=3)
        assert len(hits) >= 1
        key, score = hits[0][0], hits[0][1]
        assert key in {"c0", "c1", "c2"}
        assert 0.0 <= score <= 1.0

    def test_empty_mapper_returns_empty(self):
        adapter = SemanticKeyMapperAdapter(SemanticKeyMapper())
        assert adapter.query(np.ones(64, dtype=np.float32)) == []
        assert adapter.size() == 0

    def test_encode_derives_keys(self):
        adapter, _ = self._mk()
        keys = adapter.encode(np.ones(64, dtype=np.float32), top_k=3)
        assert len(keys) >= 1


class TestBackboneMultiModal:
    def test_mixed_dictionaries_query(self):
        bb = get_backbone()
        obj = KeyValueDictionary("object")
        obj.register_entry("sword", {"name": "鐵劍"})
        bb.register_dictionary("object", obj)

        space = KeyValueDictionary("space")
        space.register_entry("potion", {"藥水": "紅色治療藥水"})
        bb.register_dictionary("space", space)

        results = bb.query_dictionary("鐵劍", top_k=5)
        assert any(r["name"] == "object" and r["key"] == "sword" for r in results)
        results2 = bb.query_dictionary("紅色治療藥水", top_k=5)
        assert any(r["name"] == "space" and r["key"] == "potion" for r in results2)
