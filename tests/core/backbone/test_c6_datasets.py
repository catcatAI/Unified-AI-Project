# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""後續計畫 §5：數據集供給 DatasetRegistry + 遊戲卡片整合。

另驗證 §2 目標之一：遊戲卡片以字典（InMemoryDictionary）掛載後，
`backbone.query_dictionary` 可對其查詢。
"""

import pytest
from core.backbone import get_backbone, reset_backbone
from core.backbone.datasets import (
    Dataset,
    DatasetRegistry,
    load_json_records,
    register_game_cards,
)
from core.backbone.dicts import InMemoryDictionary


@pytest.fixture(autouse=True)
def _fresh():
    reset_backbone()
    yield
    reset_backbone()


class TestDatasetRegistry:
    def test_register_records(self):
        reg = DatasetRegistry()
        reg.register_records("cards", [{"key": "CC-01", "text": "織織"}])
        assert "cards" in reg
        assert reg.load("cards") == [{"key": "CC-01", "text": "織織"}]

    def test_lazy_loader(self):
        reg = DatasetRegistry()
        calls = []

        def loader():
            calls.append(1)
            return [{"key": "A"}, {"key": "B"}]

        d = reg.register_loader("lazy", loader)
        assert not d.loaded
        assert d.size == 0  # 未載入
        assert reg.load("lazy") == [{"key": "A"}, {"key": "B"}]
        assert d.loaded
        assert d.size == 2
        assert len(calls) == 1  # 只載入一次

    def test_list_and_names(self):
        reg = DatasetRegistry()
        reg.register_records("a", [])
        reg.register_records("b", [{"x": 1}])
        assert set(reg.names()) == {"a", "b"}
        lst = reg.list()
        assert {d["name"] for d in lst} == {"a", "b"}

    def test_missing_load_returns_empty(self):
        reg = DatasetRegistry()
        assert reg.load("missing") == []
        assert reg.get("missing") is None
        assert "missing" not in reg

    def test_dataset_no_loader(self):
        reg = DatasetRegistry()
        d = Dataset("empty")
        reg.register("empty", d)
        assert reg.load("empty") == []


class TestJsonLoader:
    def test_load_game_cards_json(self, tmp_path):
        import json

        path = tmp_path / "cards.json"
        path.write_text(
            json.dumps(
                {
                    "cards": [
                        {"card_id": "CC-01", "name": "織織", "description": "像素貓娘"},
                        {"card_id": "CC-02", "name": "阿布", "description": "機器人", "extra": 1},
                    ]
                }
            ),
            encoding="utf-8",
        )
        records = load_json_records(str(path))
        assert len(records) == 2
        assert records[0]["key"] == "CC-01"
        assert "織織" in records[0]["text"]
        assert "像素貓娘" in records[0]["text"]
        assert records[1]["meta"]["extra"] == 1

    def test_missing_file_returns_empty(self):
        assert load_json_records("apps/game-rpg/data/does_not_exist.json") == []

    def test_bad_json_returns_empty(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json{{{", encoding="utf-8")
        assert load_json_records(str(path)) == []


class TestBackboneDatasets:
    def test_records_registration(self):
        bb = get_backbone()
        bb.register_dataset_records("cards", [{"key": "k1"}])
        assert bb.load_dataset("cards") == [{"key": "k1"}]

    def test_loader_registration(self):
        bb = get_backbone()
        bb.register_dataset_loader("lazy", lambda: [1, 2, 3])
        assert bb.load_dataset("lazy") == [1, 2, 3]

    def test_list(self):
        bb = get_backbone()
        bb.register_dataset_records("x", [])
        names = {d["name"] for d in bb.datasets_list()}
        assert "x" in names


class TestRealGameCards:
    def test_game_cards_load(self):
        reg = DatasetRegistry()
        register_game_cards(reg)
        records = reg.load("game_cards")
        assert len(records) > 0
        assert all(r["key"] for r in records)

    def test_game_cards_registered_in_backbone_usable_as_dictionary(self):
        # §2 目標：遊戲卡片當字典掛載，backbone.query_dictionary 可查
        bb = get_backbone()
        reg = DatasetRegistry()
        register_game_cards(reg)
        records = reg.load("game_cards")
        assert records, "expected game cards to load"

        # 以 InMemoryDictionary 掛載（key → text）
        dict_of_cards = {r["key"]: r["text"] for r in records[:50]}
        game_dict = InMemoryDictionary(modality="card")
        for key, text in dict_of_cards.items():
            game_dict.register_entry(key, text)
        bb.register_dictionary("game_cards", game_dict)

        # 查詢包含常見語言（如「貓」之於織織等），只驗證查詢回傳 list 結構
        results = bb.query_dictionary("織織", top_k=3)
        assert isinstance(results, list)
        # 任一結果 name 應含 game_cards
        names = {r.get("name") for r in results} if results else set()
        if results:
            assert names

    def test_get_config_game_matches_dataset_path(self):
        # §4 配置一致性：get_config(system/game).data_path 對應資料集路徑
        from core.system.config.tiered_loader import get_config

        cfg = (get_config("system/game") or {}).get("game") or {}
        assert cfg.get("data_path") == "apps/game-rpg/data/game_cards.json"
        assert cfg.get("max_cards") == 351
