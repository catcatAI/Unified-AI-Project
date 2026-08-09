# =============================================================================
# ANGELA-MATRIX: L1-L6[全层] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: 配置注入（包裝 magic_numbers + tiered_loader）（§6 config.py）
# 維度: η 執行維度（資源效率）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸統一配置存取概念
#
# =============================================================================

"""配置注入（§6 config.py）。

包裝 `core.system.config.magic_numbers` 的 `compute_mode/compute_bool/
compute_int/compute_float`，提供主幹線統一的配置存取入口。所有主幹線相關
功能開關與參數均經此查詢，避免散落的硬編碼。

若 `magic_numbers` 不可用（最小安裝），以傳入的 dict 或預設值降級。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

try:  # 延遲導入
    from core.system.config.magic_numbers import compute_bool as _mb_compute_bool
    from core.system.config.magic_numbers import compute_float as _mb_compute_float
    from core.system.config.magic_numbers import compute_int as _mb_compute_int
    from core.system.config.magic_numbers import compute_mode as _mb_compute_mode
except Exception:  # pragma: no cover - 最小安裝降級
    _mb_compute_mode = None
    _mb_compute_bool = None
    _mb_compute_int = None
    _mb_compute_float = None


class BackboneConfig:
    """主幹線配置門面（§6 config.py）。"""

    def __init__(self, overrides: Optional[Dict[str, Any]] = None) -> None:
        self._overrides: Dict[str, Any] = dict(overrides or {})

    def set_override(self, key: str, value: Any) -> None:
        self._overrides[key] = value

    def compute_mode(self, feature: str, default: str = "auto") -> str:
        if feature in self._overrides:
            return str(self._overrides[feature])
        if _mb_compute_mode is not None:
            try:
                return _mb_compute_mode(feature, default)
            except Exception:
                pass
        return default

    def compute_bool(self, feature: str, default: bool = True) -> bool:
        if feature in self._overrides:
            return bool(self._overrides[feature])
        if _mb_compute_bool is not None:
            try:
                return _mb_compute_bool(feature, default)
            except Exception:
                pass
        return default

    def compute_int(self, feature: str, key: str, default: int = 0) -> int:
        if feature in self._overrides:
            try:
                return int(self._overrides[feature])
            except (TypeError, ValueError):
                return default
        if _mb_compute_int is not None:
            try:
                return _mb_compute_int(feature, key, default)
            except Exception:
                pass
        return default

    def compute_float(self, feature: str, key: str, default: float = 0.0) -> float:
        if feature in self._overrides:
            try:
                return float(self._overrides[feature])
            except (TypeError, ValueError):
                return default
        if _mb_compute_float is not None:
            try:
                result = _mb_compute_float(feature, key, default)
                return float(result)
            except Exception:
                pass
        return default

    def get(self, key: str, default: Any = None) -> Any:
        """直接讀取 override 或 magic_numbers 的 cache_value。"""
        if key in self._overrides:
            return self._overrides[key]
        try:
            from core.system.config.magic_numbers import cache_value

            return cache_value(key, default=default)
        except Exception:
            return default
