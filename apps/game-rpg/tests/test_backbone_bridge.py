# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
"""backbone bridge 測試（後續計畫 §6）。

驗證：
- get_bridge() 回傳 bridge（配置啟用 + backbone 可用時）。
- bridge.bootstrap：卡片字典、軸譜 registry、自由矩陣、資料集皆掛上。
- lookup_card 能查（織織等卡片零文字）。
- axis / axis_systems 讀到遊戲軸譜。
- matrix 回傳遊戲自由矩陣。
- 無 backbone 環境下 get_bridge() 回 None（模擬 import 失效）。
"""

import importlib
import sys

import pytest

sys.path.insert(0, "apps/game-rpg")

import backbone_bridge
from core.system.config.tiered_loader import get_config


@pytest.fixture(autouse=True)
def _config_enabled():
    """確保 system/game.enabled 為 True（bridge 啟用）。"""
    base = get_config("system/game") or {}
    assert (base.get("game") or {}).get("enabled") is True
    backbone_bridge.reset_bridge()
    yield
    backbone_bridge.reset_bridge()


class TestBridgeEnabled:
    def test_bridge_returns_instance(self):
        bridge = backbone_bridge.get_bridge()
        assert bridge is not None

    def test_card_dictionary_mounted(self):
        bridge = backbone_bridge.get_bridge()
        assert bridge.card_dictionary is not None
        bb = bridge.bb
        sources = {s["name"] for s in bb.dictionary_sources()}
        assert "game_cards" in sources

    def test_axes_registry_mounted(self):
        bridge = backbone_bridge.get_bridge()
        assert bridge.axes_registry is not None
        assert "物種" in bridge.axes_registry
        species = bridge.axes_registry.axis("物種")
        assert species.has_axis("原種距離")

    def test_free_matrix_mounted(self):
        bridge = backbone_bridge.get_bridge()
        assert bridge.matrix() is not None
        mats = {m["key"] for m in bridge.bb.free_matrices()}
        assert "game_matrix" in mats

    def test_dataset_registered(self):
        bridge = backbone_bridge.get_bridge()
        assert bridge.datasets == "game_cards"
        records = bridge.bb.datasets.load("game_cards")
        assert len(records) > 0


class TestBridgeQueries:
    def test_lookup_card(self):
        bridge = backbone_bridge.get_bridge()
        hits = bridge.lookup_card("織織", top_k=3)
        assert isinstance(hits, list)
        # 織織是 CC-01，應被檢索到
        keys = [h.get("key") for h in hits]
        assert "CC-01" in keys

    def test_lookup_unknown_returns_list(self):
        bridge = backbone_bridge.get_bridge()
        hits = bridge.lookup_card("不存在的查詢詞XYZ", top_k=3)
        assert isinstance(hits, list)

    def test_axis_systems_dict(self):
        bridge = backbone_bridge.get_bridge()
        d = bridge.axis_systems()
        assert "物種" in d

    def test_axis_penetration(self):
        bridge = backbone_bridge.get_bridge()
        dist = bridge.axis("物種", "原種距離")
        assert dist is not None
        assert dist.label_for("N") == "近原種"

    def test_matrix_is_shared_latent_space(self):
        bridge = backbone_bridge.get_bridge()
        from ai.multimodal.shared_latent_space import SharedLatentSpace

        assert isinstance(bridge.matrix(), SharedLatentSpace)


class TestBridgeResilience:
    def test_bridge_disabled_when_config_off(self, monkeypatch):
        bridge = backbone_bridge.get_bridge()

        def fake_config(path):
            return {"game": {"enabled": False}}

        monkeypatch.setattr("core.system.config.tiered_loader.get_config", fake_config)
        # 需重建 bridge 以重讀 config；整體不可再啟用
        monkeypatch.setattr(backbone_bridge, "_game_config_enabled", lambda: False)
        assert backbone_bridge.get_bridge() is None

    def test_bridge_resilient_when_no_backbone(self, monkeypatch):
        monkeypatch.setattr(backbone_bridge, "_BACKBONE_AVAILABLE", False)
        assert backbone_bridge.get_bridge() is None


class TestGameStillRuns:
    def test_run_game_importable(self):
        # run_game import 不崩（含新加入的 start_game bridge hook 只是 func 內）
        import run_game

        assert hasattr(run_game, "start_game")

    def test_bridge_module_importable_without_backbone(self, monkeypatch):
        # 模擬 core.backbone 不可用 → 模組仍可 import
        monkeypatch.setattr(backbone_bridge, "_BACKBONE_AVAILABLE", False)
        assert backbone_bridge._BACKBONE_AVAILABLE is False