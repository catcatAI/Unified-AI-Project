# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""座標軸統一 registry（主幹線後續計畫 §3）。

將「後端核心軸」（core/state/axis.py 等 4 檔）與「遊戲軸譜」
（apps/game-rpg/axis_system.py）以同一介面註冊/讀取，但不重寫
各自的軸語意——本 registry 只作**讀取層**。
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

MISSING = object()


class AxisDefinition:
    """單一座標軸的結構化定義。

    Attributes:
        name: 軸名（如「原種距離」）。
        dimensions: 維度名列表（如 ["近原種", "標準種", "遠原種"]）。
        positions: 軸位 → 維度標籤的對映（可省略；與 dimensions 擇一）。
    """

    def __init__(
        self,
        name: str,
        dimensions: Optional[Iterable[str]] = None,
        positions: Optional[Dict[str, str]] = None,
    ) -> None:
        self.name = name
        if positions is not None:
            self.positions: Dict[str, str] = dict(positions)
            self.dimensions: List[str] = list(self.positions.values()) if self.positions else []
        else:
            self.positions = {}
            self.dimensions = list(dimensions or [])

    def label_for(self, code: str) -> Optional[str]:
        """軸位代碼（如 "N"）→ 維度標籤（如 "近原種"）。"""
        return self.positions.get(code)

    def has_position(self, code: str) -> bool:
        return code in self.positions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dimensions": self.dimensions,
            "positions": self.positions,
        }


class AxesRegistry:
    """座標軸註冊表（可含多個子系統的軸譜）。

    Example:
        >>> reg = AxesRegistry("game")
        >>> reg.register_axis("物種", dimensions=["近原種", "標準種", "遠原種"])
        >>> reg.axis("物種").dimensions
        ['近原種', '標準種', '遠原種']
    """

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._axes: Dict[str, AxisDefinition] = {}
        self._source: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # 註冊
    # ------------------------------------------------------------------
    def register_axis(
        self,
        name: str,
        dimensions: Optional[Iterable[str]] = None,
        positions: Optional[Dict[str, str]] = None,
    ) -> AxisDefinition:
        """註冊單一座標軸。回傳該軸定義。"""
        axis = AxisDefinition(name=name, dimensions=dimensions, positions=positions)
        self._axes[name] = axis
        return axis

    def register_axes(self, axes: Dict[str, Any]) -> int:
        """從巢狀 dict 大量註冊軸譜。

        支援三種結構：
          {axis_name: {"pos": "label", ...}}      → positions 形式的單軸
          {axis_name: ["dim1", "dim2", ...]}      → dimensions 形式的單軸
          {registry_name: {"軸": {"pos": "label"}}, ...} → 子 AxesRegistry（三層巢狀）
        回傳註冊軸數（含子 registry 內軸）。
        """
        count = 0
        for name, spec in axes.items():
            if isinstance(spec, dict) and spec and all(isinstance(v, dict) for v in spec.values()):
                # 三層巢狀：此 dict 的 value 全是 dict → 視為「子 AxesRegistry」
                child = AxesRegistry(name)
                child.register_axes(spec)
                self._axes[name] = child  # type: ignore[assignment]
                count += len(child)
            elif isinstance(spec, dict):
                self.register_axis(name, positions=spec)
                count += 1
            elif isinstance(spec, (list, tuple)):
                self.register_axis(name, dimensions=list(spec))
                count += 1
            else:
                continue
        return count

    def set_source(self, source: Any) -> None:
        """記錄權威來源（如遊戲 axis_system 模組），供 close-loop 對齊。"""
        self._source[self.name] = source

    # ------------------------------------------------------------------
    # 讀取
    # ------------------------------------------------------------------
    def axis(self, name: str, default: Any = MISSING) -> Any:
        if name in self._axes:
            return self._axes[name]
        if default is not MISSING:
            return default
        raise KeyError(f"axis '{name}' not registered in '{self.name}'")

    def axes(self) -> Dict[str, AxisDefinition]:
        return dict(self._axes)

    def names(self) -> List[str]:
        return list(self._axes.keys())

    def dimensions(self, name: str) -> List[str]:
        """回傳軸的所有維度標籤。"""
        return list(self._axes[name].dimensions)

    def has_axis(self, name: str) -> bool:
        return name in self._axes

    def __contains__(self, name: object) -> bool:
        return name in self._axes

    def __len__(self) -> int:
        return len(self._axes)

    def to_dict(self) -> Dict[str, Any]:
        return {name: axis.to_dict() for name, axis in self._axes.items()}


# 全專案 registry 快取：依名稱建造例，避免重複建。
_REGISTRIES: Dict[str, AxesRegistry] = {}


def get_axes_registry(name: str = "default") -> AxesRegistry:
    """取得（或建立）指定名稱的 AxesRegistry 單例。"""
    if name not in _REGISTRIES:
        _REGISTRIES[name] = AxesRegistry(name)
    return _REGISTRIES[name]


__all__ = ["AxesRegistry", "AxisDefinition", "get_axes_registry"]
