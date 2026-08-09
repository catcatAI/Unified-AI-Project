# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
#
# 職責: 內建轉譯器註冊（§5.3）— StateMatrix↔neural + latent↔keys
#       （步驟 B2: neural_bridge / semantic_key_mapper 改經主幹線註冊）
# 維度: ζ 連通維度（跨層格式轉換）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸轉譯器概念
#
# =============================================================================

"""內建轉譯器（§5.3 / 步驟 B2）。

將既有兩組「最少轉譯」橋樑包裝為 `TranslationRule` 並註冊到主幹線：

- **neural**：`state_matrix` ↔ `neural`（`ai/bridge/neural_bridge.py`）。
  StateMatrix axis 值 ↔ GARDEN/ED3N SNN concept-key 活化值。
- **keys**：`latent` ↔ `keys`（`ai/multimodal/semantic_key_mapper.py`）。
  SharedLatentSpace 向量 ↔ ED3N 概念鍵（cosine similarity top-k）。

這些規則為惰性載入：僅在 `backbone.register_default_translators()` 被呼叫時
才 import 實際模組，避免拖慢主幹線啟動。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from core.backbone.contracts import TranslationDirection

logger = logging.getLogger("angela_backbone_translators")


class NeuralBridgeTranslator:
    """StateMatrix ↔ neural concept-key 轉譯（包裝 ai/bridge/neural_bridge.py）。

    - `state_matrix` → `neural`：`state_to_neural_inputs(state_matrix)`。
    - `neural` → `state_matrix`：`neural_outputs_to_state_updates(neural_output)`
      產生可經 `write_axis` 套用的軸更新（不直接改 `.values[]`，§8）。
    """

    name = "neural_bridge"

    def can_translate(self, source: str, target: str, direction: str) -> bool:
        pair = (source, target)
        return pair in (("state_matrix", "neural"), ("neural", "state_matrix"))

    def translate(
        self, data: Any, direction: str = TranslationDirection.DOWN, **kwargs: Any
    ) -> Any:
        try:
            from ai.bridge.neural_bridge import (
                neural_outputs_to_state_updates,
                state_to_neural_inputs,
            )

            if direction == TranslationDirection.UP:
                return neural_outputs_to_state_updates(data)
            return state_to_neural_inputs(data)
        except ImportError as exc:  # pragma: no cover - neural_bridge 不可用
            logger.warning("neural_bridge unavailable: %s", exc)
            return data


class SemanticKeyMapperTranslator:
    """latent ↔ keys 轉譯（包裝 ai/multimodal/semantic_key_mapper.py）。

    - `latent` → `keys`：`map_latent_to_keys(query_latent, top_k, mode)` 回傳
      `[{key, score}, ...]`。
    - 反向（keys → latent）暫無既有實作，回傳原始資料（identity）。
    """

    name = "semantic_key_mapper"

    def __init__(self, max_entries: int = 10000) -> None:
        self._mapper: Any = None
        self._max_entries = max_entries

    def _ensure_mapper(self) -> Any:
        if self._mapper is None:
            from ai.multimodal.semantic_key_mapper import SemanticKeyMapper

            self._mapper = SemanticKeyMapper(max_entries=self._max_entries)
        return self._mapper

    def can_translate(self, source: str, target: str, direction: str) -> bool:
        return source == "latent" and target == "keys"

    def translate(
        self, data: Any, direction: str = TranslationDirection.DOWN, **kwargs: Any
    ) -> Any:
        if direction != TranslationDirection.DOWN:
            return data
        try:
            mapper = self._ensure_mapper()
            top_k = kwargs.get("top_k", 5)
            mode = kwargs.get("mode", "auto")
            return mapper.map_latent_to_keys(data, top_k=top_k, mode=mode)
        except ImportError as exc:  # pragma: no cover
            logger.warning("semantic_key_mapper unavailable: %s", exc)
            return data

    def index_key(self, key: str, latent: Any, mode: str = "auto") -> None:
        """註冊一個 latent→key 對映（供查詢使用）。

        `mode` 決定存放為 semantic/structural/raw 潛向量（對應
        `SemanticKeyMapper.index_key` 的參數）。
        """
        mapper = self._ensure_mapper()
        kwargs: Dict[str, Any] = {"semantic_latent": latent}
        if mode == "structural":
            kwargs = {"structural_latent": latent}
        elif mode == "raw":
            kwargs = {"raw_semantic": latent}
        mapper.index_key(key, **kwargs)


def register_default_translators(backbone: Any) -> None:
    """註冊內建轉譯器到主幹線（步驟 B2）。

    惰性：僅註冊規則，不實例化底層重元件。
    """
    if not backbone.registries.translators.has("neural_bridge"):
        backbone.registries.translators.register_rule("neural_bridge", NeuralBridgeTranslator())
    if not backbone.registries.translators.has("semantic_key_mapper"):
        backbone.registries.translators.register_rule(
            "semantic_key_mapper", SemanticKeyMapperTranslator()
        )
