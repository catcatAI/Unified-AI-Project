# =============================================================================
# ANGELA-MATRIX: Hash+Matrix Dual System - Precision Projection Matrix
# =============================================================================
#
# 職責: 提供變精度投射矩陣，實現 CPU 負載自適應精度縮放
# 功能: INT8 ↔ DEC4 ↔ DEC8 轉換，支持稀疏矩陣優化
# 用途: 在低內存環境下自動降精度，高內存環境下恢復精度
# 目標: 4GB RAM 運行 INT8，16GB RAM 運行 DEC4，32GB RAM 運行 DEC8
#
# =============================================================================

from __future__ import annotations

import enum
import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple, Union


class PrecisionMode(enum.Enum):
    INT8 = "INT8"
    DEC4 = "DEC4"
    DEC8 = "DEC8"


_RAM_LIMIT_MAP: Dict[str, PrecisionMode] = {
    "4GB": PrecisionMode.INT8,
    "16GB": PrecisionMode.DEC4,
    "32GB": PrecisionMode.DEC8,
}

_DEFAULT_MODE = PrecisionMode.DEC4

_MEMORY_ESTIMATES: Dict[PrecisionMode, int] = {
    PrecisionMode.INT8: 1000,
    PrecisionMode.DEC4: 8000,
    PrecisionMode.DEC8: 16000,
}


class PrecisionProjectionMatrix:
    """變精度投射矩陣，支持 INT8/DEC4/DEC8 三種精度模式的自適應切換。"""

    def __init__(self, auto_detect: bool = True, force_mode: Optional[PrecisionMode] = None):
        self._auto_detect = auto_detect
        self._force_mode = force_mode
        self._current_mode: PrecisionMode = _DEFAULT_MODE
        self._ram_limit: Optional[str] = None
        self._total_conversions: int = 0
        self._available_ram_mb: float = 0.0

        if force_mode is not None:
            self._current_mode = force_mode
        elif not auto_detect:
            self._current_mode = _DEFAULT_MODE

    @property
    def force_mode(self) -> Optional[PrecisionMode]:
        return self._force_mode

    @force_mode.setter
    def force_mode(self, mode: PrecisionMode) -> None:
        self._force_mode = mode

    def get_precision_mode(self) -> str:
        return self._current_mode.value

    def set_ram_limit(self, limit: str) -> None:
        self._ram_limit = limit
        mode = _RAM_LIMIT_MAP.get(limit)
        if mode is not None:
            self._current_mode = mode

    def project_to_int8(self, value: float, min_val: float, max_val: float) -> int:
        if max_val == min_val:
            return 0
        normalized = (value - min_val) / (max_val - min_val)
        scaled = normalized * 255.0 - 128.0
        return max(-128, min(127, int(round(scaled))))

    def project_from_int8(self, value: int, min_val: float, max_val: float) -> float:
        normalized = (value + 128.0) / 255.0
        return normalized * (max_val - min_val) + min_val

    def project_to_dec4(self, value: float) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    def project_to_dec8(self, value: float) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)

    def convert(self, value: float) -> Union[int, Decimal]:
        self._total_conversions += 1
        mode = self._current_mode
        if mode == PrecisionMode.INT8:
            return self.project_to_int8(value, 0.0, 1.0)
        if mode == PrecisionMode.DEC4:
            return self.project_to_dec4(value)
        return self.project_to_dec8(value)

    def create_sparse_matrix(self, dense_data: Dict[str, float]) -> Dict[str, Any]:
        non_zero = {k: v for k, v in dense_data.items() if abs(v) > 1e-9}
        total = len(dense_data) or 1
        return {
            "non_zero_entries": list(non_zero.items()),
            "compression_ratio": len(non_zero) / total,
        }

    def get_memory_estimate(self, num_entries: int) -> Dict[str, int]:
        return {
            mode.value: _MEMORY_ESTIMATES[mode] * num_entries // 1000
            if mode.value not in ("INT8", "DEC4", "DEC8")
            else _MEMORY_ESTIMATES[mode]
            for mode in PrecisionMode
        }

    def update_precision_mode(self) -> bool:
        if self._force_mode is not None and self._force_mode != self._current_mode:
            self._current_mode = self._force_mode
            return True
        if self._ram_limit is not None:
            new_mode = _RAM_LIMIT_MAP.get(self._ram_limit)
            if new_mode is not None and new_mode != self._current_mode:
                self._current_mode = new_mode
                return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_conversions": self._total_conversions,
            "current_mode": self._current_mode.value,
            "available_ram_mb": self._available_ram_mb,
        }
