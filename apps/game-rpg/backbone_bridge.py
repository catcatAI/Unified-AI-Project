# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
"""backbone bridge — 遊戲與主幹線的可選接入層（後續計畫 §6）。

設計原則：
  - **惰性**：只有「backbone 可 import」且「遊戲配置啟用」時才接入；
    否則 `get_bridge()` 回傳 None，遊戲 CLI 照常執行，零破壞。
  - **唯讀**：本橋接只做「讀取層」——把遊戲卡片掛成字典、軸譜註冊進
    AxesRegistry、建遊戲專屬自由矩陣；不改遊戲自身邏輯或資料。
  - **權威來源**：軸譜以 ``axis_system.AXIS_SYSTEMS``、卡片以
    ``game_data`` 為權威；backbone 只是查詢/讀取介面。

用法：
  >>> bridge = get_bridge()          # 可能 None
  >>> if bridge:
  ...     hits = bridge.lookup_card("織織")
  ...     axes = bridge.axis_systems()
"""

import logging
import os
import sys
from typing import Any

_GAME_DIR = os.path.dirname(os.path.abspath(__file__))
if _GAME_DIR not in sys.path:
    sys.path.insert(0, _GAME_DIR)

logger = logging.getLogger("game.backbone_bridge")

try:
    from core.backbone import get_backbone
    from core.backbone.axes import AxesRegistry
    from core.backbone.datasets import register_game_cards as _register_game_cards
    from core.backbone.dicts import InMemoryDictionary
    from ai.multimodal.shared_latent_space import SharedLatentSpace

    _BACKBONE_AVAILABLE = True
except Exception as exc:  # pragma: no cover - 環境無 backbone 時遊戲照跑
    _BACKBONE_AVAILABLE = False
    logger.debug("backbone unavailable: %s", exc)


def _game_config_enabled() -> bool:
    """依 system/game 配置決定是否接入。缺配置時預設 False（保守，不偷跑）。"""
    if not _BACKBONE_AVAILABLE:
        return False
    try:
        from core.system.config.tiered_loader import get_config

        cfg = (get_config("system/game") or {}).get("game") or {}
        return bool(cfg.get("enabled", False))
    except Exception:
        return False


class GameBackboneBridge:
    """遊戲 ↔ backbone 橋接實例。

    Attributes:
        bb: backbone 實例。
        card_dictionary: 遊戲卡片掛成的字典（InMemoryDictionary, modality="card"）。
        axes_registry: 遊戲軸譜 AxesRegistry。
        free_matrix: 遊戲專屬 SharedLatentSpace。
        datasets: 遊戲卡片資料集名（"game_cards"）。
    """

    def __init__(self) -> None:
        self.bb = get_backbone()
        self.card_dictionary = None
        self.axes_registry = None
        self.free_matrix = None
        self.datasets = "game_cards"
        self._bootstrap()

    def _bootstrap(self) -> None:
        try:
            import game_data
            import axis_system

            # 1) 卡片字典：以 card_id → name+description 掛載
            cards = game_data._ALL_CARDS
            if cards:
                self.card_dictionary = InMemoryDictionary(modality="card")
                for card in cards:
                    cid = card.get("card_id") or card.get("name") or ""
                    if not cid:
                        continue
                    text = " ".join(
                        str(card.get(k, ""))
                        for k in ("name", "description")
                        if card.get(k)
                    ).strip()
                    if text:
                        self.card_dictionary.register_entry(cid, text)
                self.bb.register_dictionary("game_cards", self.card_dictionary)

            # 2) 軸譜 registry
            self.axes_registry = AxesRegistry("game")
            self.axes_registry.register_axes(axis_system.AXIS_SYSTEMS)
            self.bb.register_axes_registry("game", self.axes_registry)

            # 3) 自由矩陣（遊戲專屬）
            self.free_matrix = SharedLatentSpace()
            self.bb.register_free_matrix("game_matrix", self.free_matrix)

            # 4) 資料集
            _register_game_cards(self.bb.datasets)

            logger.info(
                "game backbone bridge ready: %d cards, %d axes, datasets=%s",
                len(cards) if cards else 0,
                len(self.axes_registry),
                self.datasets,
            )
        except Exception as exc:
            logger.debug("game backbone bootstrap failed: %s", exc, exc_info=True)

    # ------------------------------------------------------------------
    def lookup_card(self, query: str, top_k: int = 3) -> list:
        """經 backbone 查詢卡片；未接入回傳 []。"""
        if self.card_dictionary is None:
            return []
        try:
            return self.bb.query_dictionary(query, top_k=top_k)
        except Exception as exc:
            logger.debug("lookup_card failed: %s", exc)
            return []

    def axis_systems(self) -> dict:
        """回傳遊戲軸譜結構（dict，registry 視角）。"""
        if self.axes_registry is None:
            return {}
        try:
            return self.axes_registry.to_dict()
        except Exception as exc:
            logger.debug("axis_systems failed: %s", exc)
            return {}

    def axis(self, registry: str, axis_name: str) -> Any:
        """讀取指定軸位定義（穿透子 registry）。"""
        if self.axes_registry is None:
            return None
        try:
            top = self.axes_registry.axis(registry, default=None)
            if top is None or not hasattr(top, "axis"):
                return None
            return top.axis(axis_name, default=None)
        except Exception as exc:
            logger.debug("axis failed: %s", exc)
            return None

    def matrix(self) -> Any:
        """回傳遊戲自由矩陣（未接入回傳 None）。"""
        return self.free_matrix


_bridge = None


def get_bridge() -> Any:
    """取得（或建立）遊戲 backbone bridge 單例；未啟用回傳 None。"""
    global _bridge
    if not _BACKBONE_AVAILABLE or not _game_config_enabled():
        return None
    if _bridge is None:
        _bridge = GameBackboneBridge()
    return _bridge


def reset_bridge() -> None:
    """重置 bridge 單例（測試用）。"""
    global _bridge
    _bridge = None


__all__ = ["GameBackboneBridge", "get_bridge", "reset_bridge"]