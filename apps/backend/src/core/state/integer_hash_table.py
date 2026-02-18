# =============================================================================
# ANGELA-MATRIX: Hash+Matrix Dual System - Integer Hash Table (定性狀態)
# =============================================================================
#
# 職責: 管理離散狀態的哈希表，使用 uint64_t 本地哈希
# 用途: 存儲定性狀態 (L3 情緒等級, L1 激素開關等)
# 性能: 快速索引、邏輯跳轉
# 安全: 配合 A/B/C 密鑰進行狀態指紋驗證
#
# =============================================================================

import logging
import hashlib
import struct
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class IntegerHashEntry:
    """整數哈希表條目"""
    key: str
    value: int
    hash_value: int
    timestamp: float
    version: int = 1


class IntegerHashTable:
    """整數哈希表 - 用於定性狀態管理
    
    特性:
    - 使用 uint64_t 本地哈希
    - 快速索引和邏輯跳轉
    - 支持狀態指紋生成
    - 支持哈希鏈驗證
    """
    
    def __init__(self, capacity: int = 1024):
        """初始化整數哈希表
        
        Args:
            capacity: 哈希表容量 (預設 1024 個條目)
        """
        self.capacity = capacity
        self.entries: Dict[str, IntegerHashEntry] = {}
        self.hash_chain: List[int] = []
        self._stats = {
            "total_sets": 0,
            "total_gets": 0,
            "hash_collisions": 0
        }
        
    def _compute_hash(self, key: str, value: int) -> int:
        """計算 uint64_t 哈希值
        
        使用 SHA256 的前 8 字節轉換為 uint64
        
        Args:
            key: 狀態鍵名
            value: 整數值
            
        Returns:
            uint64_t 哈希值
        """
        data = f"{key}:{value}".encode('utf-8')
        hash_bytes = hashlib.sha256(data).digest()[:8]
        hash_int = struct.unpack('>Q', hash_bytes)[0]
        return hash_int
    
    def set(self, key: str, value: int) -> int:
        """設置整數狀態值
        
        Args:
            key: 狀態鍵名 (如 "emotion.level", "hormone.alpha.active")
            value: 整數值
            
        Returns:
            狀態哈希值 (uint64)
        """
        if not isinstance(value, int):
            raise TypeError(f"Value must be integer, got {type(value)}")
        
        hash_value = self._compute_hash(key, value)
        timestamp = datetime.now().timestamp()
        
        entry = IntegerHashEntry(
            key=key,
            value=value,
            hash_value=hash_value,
            timestamp=timestamp,
            version=1
        )
        
        self.entries[key] = entry
        self.hash_chain.append(hash_value)
        self._stats["total_sets"] += 1
        
        logger.debug(f"Set integer state: {key}={value}, hash={hash_value}")
        return hash_value
    
    def get(self, key: str) -> Optional[int]:
        """獲取整數狀態值
        
        Args:
            key: 狀態鍵名
            
        Returns:
            整數值，若不存在則返回 None
        """
        self._stats["total_gets"] += 1
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
    
    def get_entry(self, key: str) -> Optional[IntegerHashEntry]:
        """獲取完整條目
        
        Args:
            key: 狀態鍵名
            
        Returns:
            IntegerHashEntry 或 None
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
    
    def verify_causality(self, start_fingerprint: int, end_fingerprint: int,
                        change_log: List[Dict[str, Any]]) -> bool:
        """驗證因果鏈完整性
        
        驗證從起始指紋到終止指紋的變更是否合法
        
        Args:
            start_fingerprint: 起始狀態指紋
            end_fingerprint: 終止狀態指紋
            change_log: 變更記錄列表
            
        Returns:
            因果鏈是否有效
        """
        if not change_log:
            return start_fingerprint == end_fingerprint
        
        current_fingerprint = start_fingerprint
        
        for change in change_log:
            key = change.get("key")
            value = change.get("value")
            
            if key and value is not None:
                change_hash = self._compute_hash(key, value)
                combined = f"{current_fingerprint}:{change_hash}".encode()
                current_fingerprint = struct.unpack('>Q', 
                    hashlib.sha256(combined).digest()[:8])[0]
        
        return current_fingerprint == end_fingerprint
    
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
            "hash_collisions": self._stats["hash_collisions"]
        }
    
    def clear(self):
        """清空哈希表"""
        self.entries.clear()
        self.hash_chain.clear()
        logger.info("Integer hash table cleared")
    
    def export_state(self) -> Dict[str, Any]:
        """導出狀態快照
        
        Returns:
            包含所有條目的狀態字典
        """
        return {
            "entries": {
                key: {
                    "value": entry.value,
                    "hash": entry.hash_value,
                    "timestamp": entry.timestamp,
                    "version": entry.version
                }
                for key, entry in self.entries.items()
            },
            "fingerprint": self.get_state_fingerprint(),
            "stats": self.get_stats()
        }
