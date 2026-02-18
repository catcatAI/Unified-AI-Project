# =============================================================================
# ANGELA-MATRIX: Hash+Matrix Dual System - Decimal Hash Table (定量體感)
# =============================================================================
#
# 職責: 管理連續狀態的哈希表，使用 DEC4 定點數哈希
# 用途: 存儲定量狀態 (激素衰減曲線, 微小波動記錄等)
# 精度: DEC4 (4位小數) 支持 0.0001 級別精度
# 性能: 支持微小波動記錄 (如 0.0025 疼痛殘留)
#
# =============================================================================

import logging
import hashlib
import struct
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


@dataclass
class DecimalHashEntry:
    """十進制哈希表條目"""
    key: str
    value: Decimal
    hash_value: int
    timestamp: float
    version: int = 1


class DecimalHashTable:
    """十進制哈希表 - 用於定量體感管理
    
    特性:
    - 使用 DEC4 定點數 (4位小數精度)
    - 支持微小波動記錄 (0.0001 精度)
    - 支持激素衰減曲線追蹤
    - 配合哈希指紋驗證
    """
    
    PRECISION_DEC4 = Decimal('0.0001')
    PRECISION_DEC8 = Decimal('0.00000001')
    
    def __init__(self, capacity: int = 2048, precision: str = "DEC4"):
        """初始化十進制哈希表
        
        Args:
            capacity: 哈希表容量 (預設 2048 個條目)
            precision: 精度模式 ("DEC4" 或 "DEC8")
        """
        self.capacity = capacity
        self.precision = self.PRECISION_DEC4 if precision == "DEC4" else self.PRECISION_DEC8
        self.entries: Dict[str, DecimalHashEntry] = {}
        self.hash_chain: List[int] = []
        self._stats = {
            "total_sets": 0,
            "total_gets": 0,
            "precision_mode": precision
        }
        
    def _normalize_value(self, value: float) -> Decimal:
        """規範化浮點數為定點數
        
        Args:
            value: 浮點數值
            
        Returns:
            規範化的 Decimal 值
        """
        dec_value = Decimal(str(value))
        normalized = dec_value.quantize(self.precision, rounding=ROUND_HALF_UP)
        return normalized
    
    def _compute_hash(self, key: str, value: Decimal) -> int:
        """計算 uint64_t 哈希值
        
        使用規範化的十進制字符串計算哈希
        
        Args:
            key: 狀態鍵名
            value: Decimal 值
            
        Returns:
            uint64_t 哈希值
        """
        value_str = str(value)
        data = f"{key}:{value_str}".encode('utf-8')
        hash_bytes = hashlib.sha256(data).digest()[:8]
        hash_int = struct.unpack('>Q', hash_bytes)[0]
        return hash_int
    
    def set(self, key: str, value: float) -> int:
        """設置十進制狀態值
        
        Args:
            key: 狀態鍵名 (如 "hormone.alpha.level", "pain.residual")
            value: 浮點數值
            
        Returns:
            狀態哈希值 (uint64)
        """
        normalized_value = self._normalize_value(value)
        hash_value = self._compute_hash(key, normalized_value)
        timestamp = datetime.now().timestamp()
        
        entry = DecimalHashEntry(
            key=key,
            value=normalized_value,
            hash_value=hash_value,
            timestamp=timestamp,
            version=1
        )
        
        self.entries[key] = entry
        self.hash_chain.append(hash_value)
        self._stats["total_sets"] += 1
        
        logger.debug(f"Set decimal state: {key}={normalized_value}, hash={hash_value}")
        return hash_value
    
    def get(self, key: str) -> Optional[float]:
        """獲取十進制狀態值
        
        Args:
            key: 狀態鍵名
            
        Returns:
            浮點數值，若不存在則返回 None
        """
        self._stats["total_gets"] += 1
        entry = self.entries.get(key)
        return float(entry.value) if entry else None
    
    def get_decimal(self, key: str) -> Optional[Decimal]:
        """獲取 Decimal 狀態值
        
        Args:
            key: 狀態鍵名
            
        Returns:
            Decimal 值，若不存在則返回 None
        """
        entry = self.entries.get(key)
        return entry.value if entry else None
    
    def get_hash(self, key: str) -> Optional[int]:
        """獲取狀態哈希值
        
        Args:
            key: 狀態鍵名
            
        Returns:
            uint64 哈希值，若不存在則返回 None
        """
        entry = self.entries.get(key)
        return entry.hash_value if entry else None
    
    def get_entry(self, key: str) -> Optional[DecimalHashEntry]:
        """獲取完整條目
        
        Args:
            key: 狀態鍵名
            
        Returns:
            DecimalHashEntry 或 None
        """
        return self.entries.get(key)
    
    def verify_hash(self, key: str) -> bool:
        """驗證狀態哈希一致性
        
        Args:
            key: 狀態鍵名
            
        Returns:
            哈希是否一致
        """
        entry = self.entries.get(key)
        if not entry:
            return False
        
        computed_hash = self._compute_hash(entry.key, entry.value)
        return computed_hash == entry.hash_value
    
    def get_state_fingerprint(self) -> int:
        """獲取整體狀態指紋
        
        將所有哈希值合併為單一指紋
        
        Returns:
            uint64 狀態指紋
        """
        if not self.hash_chain:
            return 0
        
        combined = "".join(str(h) for h in self.hash_chain[-100:])
        fingerprint_bytes = hashlib.sha256(combined.encode()).digest()[:8]
        fingerprint = struct.unpack('>Q', fingerprint_bytes)[0]
        
        return fingerprint
    
    def track_decay(self, key: str, initial_value: float, 
                   decay_rate: float, time_delta: float) -> float:
        """追蹤指數衰減
        
        用於激素衰減曲線等場景
        
        Args:
            key: 狀態鍵名
            initial_value: 初始值
            decay_rate: 衰減率 (0-1)
            time_delta: 時間差 (秒)
            
        Returns:
            衰減後的值
        """
        import math
        decayed_value = initial_value * math.exp(-decay_rate * time_delta)
        self.set(key, decayed_value)
        return decayed_value
    
    def record_fluctuation(self, key: str, base_value: float, 
                          fluctuation: float) -> float:
        """記錄微小波動
        
        支持 0.0001 級別的精度
        
        Args:
            key: 狀態鍵名
            base_value: 基準值
            fluctuation: 波動量
            
        Returns:
            記錄後的值
        """
        final_value = base_value + fluctuation
        self.set(key, final_value)
        return final_value
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息
        
        Returns:
            統計數據字典
        """
        return {
            "capacity": self.capacity,
            "entries_count": len(self.entries),
            "hash_chain_length": len(self.hash_chain),
            "total_sets": self._stats["total_sets"],
            "total_gets": self._stats["total_gets"],
            "precision_mode": self._stats["precision_mode"]
        }
    
    def clear(self):
        """清空哈希表"""
        self.entries.clear()
        self.hash_chain.clear()
        logger.info("Decimal hash table cleared")
    
    def export_state(self) -> Dict[str, Any]:
        """導出狀態快照
        
        Returns:
            包含所有條目的狀態字典
        """
        return {
            "entries": {
                key: {
                    "value": str(entry.value),
                    "hash": entry.hash_value,
                    "timestamp": entry.timestamp,
                    "version": entry.version
                }
                for key, entry in self.entries.items()
            },
            "fingerprint": self.get_state_fingerprint(),
            "stats": self.get_stats()
        }
