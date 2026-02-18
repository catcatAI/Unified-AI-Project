# =============================================================================
# ANGELA-MATRIX: Hash+Matrix Dual System - State Hash Manager
# =============================================================================
#
# 職責: 統一管理整數/十進制哈希表，提供狀態指紋和因果驗證
# 功能: 協調 Integer Hash Table + Decimal Hash Table + Precision Matrix
# API: get_state_hash(), verify_causality(), set/get 統一接口
# 安全: 配合 A/B/C 密鑰進行狀態簽名和驗證
#
# =============================================================================

import logging
import hashlib
import struct
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from decimal import Decimal

from .integer_hash_table import IntegerHashTable
from .decimal_hash_table import DecimalHashTable
from .precision_projection_matrix import PrecisionProjectionMatrix, PrecisionMode

logger = logging.getLogger(__name__)


class StateHashManager:
    """狀態哈希管理器 - 協調整數/十進制哈希表
    
    特性:
    - 統一的 set/get 接口
    - 自動路由到正確的哈希表
    - 提供全局狀態指紋
    - 支持因果鏈驗證
    - 配合 A/B/C 密鑰簽名
    """
    
    def __init__(self, precision_mode: str = "DEC4", auto_adapt: bool = True):
        """初始化狀態哈希管理器
        
        Args:
            precision_mode: 精度模式 ("INT8", "DEC4", "DEC8")
            auto_adapt: 是否自動適應 RAM
        """
        self.integer_table = IntegerHashTable(capacity=1024)
        self.decimal_table = DecimalHashTable(capacity=2048, precision=precision_mode)
        self.precision_matrix = PrecisionProjectionMatrix(auto_detect=auto_adapt)
        
        self.change_log: List[Dict[str, Any]] = []
        self._key_manager = None
        
        self._stats = {
            "total_operations": 0,
            "integer_operations": 0,
            "decimal_operations": 0
        }
        
        logger.info(f"StateHashManager initialized with precision={precision_mode}, "
                   f"auto_adapt={auto_adapt}")
    
    def set_key_manager(self, key_manager):
        """設置密鑰管理器
        
        Args:
            key_manager: UnifiedKeyManager 實例
        """
        self._key_manager = key_manager
        logger.info("Key manager attached to StateHashManager")
    
    def set(self, key: str, value: Union[int, float]) -> int:
        """設置狀態值 (自動路由)
        
        Args:
            key: 狀態鍵名
            value: 整數或浮點數值
            
        Returns:
            狀態哈希值
        """
        timestamp = datetime.now().timestamp()
        
        if isinstance(value, int):
            hash_value = self.integer_table.set(key, value)
            self._stats["integer_operations"] += 1
            table_type = "integer"
        else:
            hash_value = self.decimal_table.set(key, float(value))
            self._stats["decimal_operations"] += 1
            table_type = "decimal"
        
        self.change_log.append({
            "key": key,
            "value": value,
            "hash": hash_value,
            "table": table_type,
            "timestamp": timestamp
        })
        
        self._stats["total_operations"] += 1
        
        return hash_value
    
    def get(self, key: str) -> Optional[Union[int, float]]:
        """獲取狀態值 (自動路由)
        
        Args:
            key: 狀態鍵名
            
        Returns:
            狀態值，優先查找整數表，再查找十進制表
        """
        int_value = self.integer_table.get(key)
        if int_value is not None:
            return int_value
        
        dec_value = self.decimal_table.get(key)
        return dec_value
    
    def get_hash(self, key: str) -> Optional[int]:
        """獲取狀態哈希值
        
        Args:
            key: 狀態鍵名
            
        Returns:
            uint64 哈希值
        """
        int_hash = self.integer_table.get_hash(key)
        if int_hash is not None:
            return int_hash
        
        dec_hash = self.decimal_table.get_hash(key)
        return dec_hash
    
    def get_state_hash(self) -> int:
        """獲取全局狀態指紋
        
        合併整數表和十進制表的指紋
        
        Returns:
            uint64 全局狀態指紋
        """
        int_fingerprint = self.integer_table.get_state_fingerprint()
        dec_fingerprint = self.decimal_table.get_state_fingerprint()
        
        combined = f"{int_fingerprint}:{dec_fingerprint}".encode()
        fingerprint_bytes = hashlib.sha256(combined).digest()[:8]
        global_fingerprint = struct.unpack('>Q', fingerprint_bytes)[0]
        
        return global_fingerprint
    
    def verify_causality(self, start_hash: int, end_hash: int,
                        change_log: Optional[List[Dict[str, Any]]] = None) -> bool:
        """驗證因果鏈完整性
        
        驗證從起始狀態到終止狀態的變更是否合理
        
        Args:
            start_hash: 起始狀態哈希
            end_hash: 終止狀態哈希
            change_log: 變更記錄 (None 則使用內部記錄)
            
        Returns:
            因果鏈是否有效
        """
        log = change_log or self.change_log
        
        if not log:
            return start_hash == end_hash
        
        if start_hash == end_hash and len(log) > 0:
            logger.warning("State hash unchanged despite changes in log")
            return False
        
        for i, change in enumerate(log):
            required_fields = ["key", "value", "hash", "timestamp"]
            if not all(field in change for field in required_fields):
                logger.warning(f"Change log entry {i} missing required fields")
                return False
        
        is_valid = True
        logger.debug(f"Causality verification: {len(log)} changes from {start_hash} to {end_hash}")
        
        return is_valid
    
    def sign_state_with_key_a(self, state_hash: int) -> Optional[str]:
        """使用 Key A 簽名狀態哈希
        
        Args:
            state_hash: 狀態哈希值
            
        Returns:
            簽名字符串，若無密鑰管理器則返回 None
        """
        if not self._key_manager:
            logger.warning("No key manager attached, cannot sign state")
            return None
        
        key_a = self._key_manager.get_security_key("KeyA")
        if not key_a:
            logger.warning("Key A not available")
            return None
        
        data = f"{state_hash}:{key_a}".encode()
        signature = hashlib.sha256(data).hexdigest()
        
        logger.debug(f"State {state_hash} signed with Key A")
        return signature
    
    def verify_signature(self, state_hash: int, signature: str) -> bool:
        """驗證狀態簽名
        
        Args:
            state_hash: 狀態哈希值
            signature: 簽名字符串
            
        Returns:
            簽名是否有效
        """
        if not self._key_manager:
            logger.warning("No key manager attached, cannot verify signature")
            return False
        
        key_a = self._key_manager.get_security_key("KeyA")
        if not key_a:
            logger.warning("Key A not available")
            return False
        
        data = f"{state_hash}:{key_a}".encode()
        expected_signature = hashlib.sha256(data).hexdigest()
        
        is_valid = signature == expected_signature
        
        if not is_valid:
            logger.warning(f"Signature verification failed for state {state_hash}")
        
        return is_valid
    
    def prevent_state_forgery(self, key: str, value: Union[int, float],
                             signature: str) -> bool:
        """防止狀態偽造
        
        驗證狀態變更的合法性
        
        Args:
            key: 狀態鍵名
            value: 新值
            signature: 變更簽名
            
        Returns:
            變更是否合法
        """
        temp_hash = self._compute_change_hash(key, value)
        return self.verify_signature(temp_hash, signature)
    
    def _compute_change_hash(self, key: str, value: Union[int, float]) -> int:
        """計算變更哈希
        
        Args:
            key: 狀態鍵名
            value: 值
            
        Returns:
            變更哈希值
        """
        data = f"{key}:{value}".encode()
        hash_bytes = hashlib.sha256(data).digest()[:8]
        return struct.unpack('>Q', hash_bytes)[0]
    
    def get_precision_mode(self) -> str:
        """獲取當前精度模式
        
        Returns:
            精度模式名稱
        """
        return self.precision_matrix.get_precision_mode()
    
    def set_ram_limit(self, ram_str: str):
        """設置 RAM 限制 (觸發精度調整)
        
        Args:
            ram_str: RAM 字符串 (如 "4GB", "16GB")
        """
        self.precision_matrix.set_ram_limit(ram_str)
        
        new_mode = self.precision_matrix.get_precision_mode()
        logger.info(f"RAM limit set to {ram_str}, precision mode: {new_mode}")
    
    def export_full_state(self) -> Dict[str, Any]:
        """導出完整狀態快照
        
        Returns:
            包含所有哈希表和元數據的狀態字典
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "global_hash": self.get_state_hash(),
            "precision_mode": self.get_precision_mode(),
            "integer_table": self.integer_table.export_state(),
            "decimal_table": self.decimal_table.export_state(),
            "change_log_size": len(self.change_log),
            "stats": self.get_stats()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息
        
        Returns:
            統計數據字典
        """
        return {
            "total_operations": self._stats["total_operations"],
            "integer_operations": self._stats["integer_operations"],
            "decimal_operations": self._stats["decimal_operations"],
            "change_log_size": len(self.change_log),
            "integer_table": self.integer_table.get_stats(),
            "decimal_table": self.decimal_table.get_stats(),
            "precision_matrix": self.precision_matrix.get_stats()
        }
    
    def clear_change_log(self):
        """清空變更日誌"""
        self.change_log.clear()
        logger.info("Change log cleared")
    
    def clear_all(self):
        """清空所有狀態"""
        self.integer_table.clear()
        self.decimal_table.clear()
        self.change_log.clear()
        logger.info("All state cleared")
