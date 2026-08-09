# =============================================================================
# ANGELA-MATRIX: L1-L6[全层] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: 轉譯器註冊與執行（§5.3）
#       （§6 translate.py）
# 維度: ζ 連通維度（跨層格式轉換）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸轉譯概念
#
# =============================================================================

"""轉譯器註冊與執行（§5.3）。

不同層之間資料格式不同（LLM provider 格式 ↔ 主幹線信封格式 ↔ 矩陣/字典
格式）。`BackboneTranslator` 統一執行 `TranslationRule`：

- 註冊：`register(name, rule)` 或 `register_func(...)`。
- 執行：`translate(source, target, data, direction)` 找尋第一個可處理路徑的
  轉譯器並執行；找不到則回傳原始資料（identity）。
"""

from __future__ import annotations

import logging
from typing import Any

from core.backbone.contracts import TranslationDirection

logger = logging.getLogger("angela_backbone_translate")


class BackboneTranslator:
    """轉譯器註冊與執行門面（§5.3）。"""

    def __init__(self, registry: Any = None) -> None:
        self._registry = registry

    # ------------------------------------------------------------------
    # 註冊
    # ------------------------------------------------------------------
    def register(self, name: str, rule: Any) -> None:
        if self._registry is None:
            raise RuntimeError("translator registry not bound")
        self._registry.register_rule(name, rule)

    def register_func(self, name: str, can_translate, translate) -> None:
        if self._registry is None:
            raise RuntimeError("translator registry not bound")
        self._registry.register_func(name, can_translate, translate)

    def names(self) -> list:
        if self._registry is None:
            return []
        return list(self._registry.keys())

    # ------------------------------------------------------------------
    # 執行
    # ------------------------------------------------------------------
    def translate(
        self,
        source: str,
        target: str,
        data: Any,
        direction: str = TranslationDirection.DOWN,
        **kwargs: Any,
    ) -> Any:
        """執行 source→target 的轉譯；找不到規則時 identity 回傳。"""
        if self._registry is None:
            return data
        rule = self._registry.find(source, target, direction)
        if rule is None:
            return data
        try:
            return rule.translate(data, direction=direction, **kwargs)
        except Exception as exc:
            logger.warning("translate %s->%s (%s) failed: %s", source, target, direction, exc)
            return data

    def can_translate(self, source: str, target: str, direction: str) -> bool:
        if self._registry is None:
            return False
        return self._registry.find(source, target, direction) is not None
