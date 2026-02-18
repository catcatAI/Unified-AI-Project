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

import logging
import psutil
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from decimal import Decimal

logger = logging.getLogger(__name__)


class PrecisionMode(Enum):
    """精度模式枚舉"""
    INT8 = "INT8"
    DEC4 = "DEC4"
    DEC8 = "DEC8"


class PrecisionProjectionMatrix:
    """精度投射矩陣
    
    特性:
    - 自動檢測可用 RAM
    - 動態選擇精度模式
    - 支持精度轉換
    - 稀疏矩陣優化
    """
    
    RAM_THRESHOLDS = {
        PrecisionMode.INT8: 4 * 1024 * 1024 * 1024,
        PrecisionMode.DEC4: 16 * 1024 * 1024 * 1024,
        PrecisionMode.DEC8: 32 * 1024 * 1024 * 1024
    }
    
    INT8_RANGE = (-128, 127)
    DEC4_PRECISION = Decimal('0.0001')
    DEC8_PRECISION = Decimal('0.00000001')
    
    def __init__(self, auto_detect: bool = True, force_mode: Optional[PrecisionMode] = None):
        """初始化精度投射矩陣
        
        Args:
            auto_detect: 自動檢測 RAM 並選擇精度模式
            force_mode: 強制指定精度模式 (忽略自動檢測)
        """
        self.auto_detect = auto_detect
        self.force_mode = force_mode
        self.current_mode = self._determine_precision_mode()
        
        self._stats = {
            "total_conversions": 0,
            "mode_switches": 0,
            "last_mode": None
        }
        
        logger.info(f"Precision mode initialized: {self.current_mode.value}")
    
    def _get_available_ram(self) -> int:
        """獲取可用 RAM (字節)
        
        Returns:
            可用 RAM 字節數
        """
        try:
            mem = psutil.virtual_memory()
            return mem.available
        except Exception as e:
            logger.warning(f"Failed to detect RAM: {e}, using default 8GB")
            return 8 * 1024 * 1024 * 1024
    
    def _determine_precision_mode(self) -> PrecisionMode:
        """確定精度模式
        
        Returns:
            選擇的精度模式
        """
        if self.force_mode:
            return self.force_mode
        
        if not self.auto_detect:
            return PrecisionMode.DEC4
        
        available_ram = self._get_available_ram()
        
        if available_ram >= self.RAM_THRESHOLDS[PrecisionMode.DEC8]:
            return PrecisionMode.DEC8
        elif available_ram >= self.RAM_THRESHOLDS[PrecisionMode.DEC4]:
            return PrecisionMode.DEC4
        else:
            return PrecisionMode.INT8
    
    def get_precision_mode(self) -> str:
        """獲取當前精度模式
        
        Returns:
            精度模式名稱
        """
        return self.current_mode.value
    
    def update_precision_mode(self) -> bool:
        """更新精度模式 (重新檢測 RAM)
        
        Returns:
            精度模式是否發生變化
        """
        old_mode = self.current_mode
        new_mode = self._determine_precision_mode()
        
        if old_mode != new_mode:
            self._stats["last_mode"] = old_mode.value
            self._stats["mode_switches"] += 1
            self.current_mode = new_mode
            logger.info(f"Precision mode switched: {old_mode.value} → {new_mode.value}")
            return True
        
        return False
    
    def set_ram_limit(self, ram_str: str):
        """設置 RAM 限制 (用於測試)
        
        Args:
            ram_str: RAM 字符串 (如 "4GB", "16GB", "32GB")
        """
        ram_bytes = self._parse_ram_string(ram_str)
        
        if ram_bytes >= self.RAM_THRESHOLDS[PrecisionMode.DEC8]:
            self.force_mode = PrecisionMode.DEC8
        elif ram_bytes >= self.RAM_THRESHOLDS[PrecisionMode.DEC4]:
            self.force_mode = PrecisionMode.DEC4
        else:
            self.force_mode = PrecisionMode.INT8
        
        self.current_mode = self.force_mode
        logger.info(f"RAM limit set to {ram_str}, mode: {self.current_mode.value}")
    
    def _parse_ram_string(self, ram_str: str) -> int:
        """解析 RAM 字符串為字節數
        
        Args:
            ram_str: RAM 字符串 (如 "4GB", "16GB")
            
        Returns:
            字節數
        """
        ram_str = ram_str.upper().strip()
        
        if ram_str.endswith("GB"):
            return int(ram_str[:-2]) * 1024 * 1024 * 1024
        elif ram_str.endswith("MB"):
            return int(ram_str[:-2]) * 1024 * 1024
        else:
            raise ValueError(f"Invalid RAM string: {ram_str}")
    
    def project_to_int8(self, value: float, min_val: float = 0.0, 
                       max_val: float = 1.0) -> int:
        """投射浮點數到 INT8
        
        Args:
            value: 浮點數值
            min_val: 映射範圍最小值
            max_val: 映射範圍最大值
            
        Returns:
            INT8 整數 (-128 to 127)
        """
        normalized = (value - min_val) / (max_val - min_val)
        int8_value = int(normalized * 255) - 128
        int8_value = max(self.INT8_RANGE[0], min(self.INT8_RANGE[1], int8_value))
        
        self._stats["total_conversions"] += 1
        return int8_value
    
    def project_from_int8(self, int8_value: int, min_val: float = 0.0,
                         max_val: float = 1.0) -> float:
        """從 INT8 恢復為浮點數
        
        Args:
            int8_value: INT8 整數
            min_val: 映射範圍最小值
            max_val: 映射範圍最大值
            
        Returns:
            浮點數值
        """
        normalized = (int8_value + 128) / 255.0
        float_value = normalized * (max_val - min_val) + min_val
        
        self._stats["total_conversions"] += 1
        return float_value
    
    def project_to_dec4(self, value: float) -> Decimal:
        """投射浮點數到 DEC4
        
        Args:
            value: 浮點數值
            
        Returns:
            DEC4 Decimal 值
        """
        from decimal import ROUND_HALF_UP
        dec_value = Decimal(str(value))
        dec4_value = dec_value.quantize(self.DEC4_PRECISION, rounding=ROUND_HALF_UP)
        
        self._stats["total_conversions"] += 1
        return dec4_value
    
    def project_to_dec8(self, value: float) -> Decimal:
        """投射浮點數到 DEC8
        
        Args:
            value: 浮點數值
            
        Returns:
            DEC8 Decimal 值
        """
        from decimal import ROUND_HALF_UP
        dec_value = Decimal(str(value))
        dec8_value = dec_value.quantize(self.DEC8_PRECISION, rounding=ROUND_HALF_UP)
        
        self._stats["total_conversions"] += 1
        return dec8_value
    
    def convert(self, value: float, target_mode: Optional[PrecisionMode] = None) -> Any:
        """轉換值到目標精度模式
        
        Args:
            value: 浮點數值
            target_mode: 目標精度模式 (None 則使用當前模式)
            
        Returns:
            轉換後的值 (int 或 Decimal)
        """
        mode = target_mode or self.current_mode
        
        if mode == PrecisionMode.INT8:
            return self.project_to_int8(value)
        elif mode == PrecisionMode.DEC4:
            return self.project_to_dec4(value)
        elif mode == PrecisionMode.DEC8:
            return self.project_to_dec8(value)
        else:
            return value
    
    def create_sparse_matrix(self, dense_data: Dict[str, float]) -> Dict[str, Any]:
        """創建稀疏矩陣表示
        
        只存儲非零值，節省內存
        
        Args:
            dense_data: 密集數據字典
            
        Returns:
            稀疏矩陣字典
        """
        sparse_matrix = {
            "mode": self.current_mode.value,
            "non_zero_entries": {},
            "total_entries": len(dense_data)
        }
        
        for key, value in dense_data.items():
            if abs(value) > 1e-9:
                converted_value = self.convert(value)
                sparse_matrix["non_zero_entries"][key] = converted_value
        
        compression_ratio = 1 - (len(sparse_matrix["non_zero_entries"]) / max(len(dense_data), 1))
        sparse_matrix["compression_ratio"] = compression_ratio
        
        logger.debug(f"Sparse matrix created: {len(sparse_matrix['non_zero_entries'])}/{len(dense_data)} entries, "
                    f"compression: {compression_ratio:.2%}")
        
        return sparse_matrix
    
    def get_memory_estimate(self, entry_count: int) -> Dict[str, int]:
        """估算不同精度模式的內存使用
        
        Args:
            entry_count: 條目數量
            
        Returns:
            各精度模式的內存估算 (字節)
        """
        return {
            "INT8": entry_count * 1,
            "DEC4": entry_count * 8,
            "DEC8": entry_count * 16
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息
        
        Returns:
            統計數據字典
        """
        return {
            "current_mode": self.current_mode.value,
            "available_ram_mb": self._get_available_ram() / (1024 * 1024),
            "total_conversions": self._stats["total_conversions"],
            "mode_switches": self._stats["mode_switches"],
            "last_mode": self._stats["last_mode"]
        }
