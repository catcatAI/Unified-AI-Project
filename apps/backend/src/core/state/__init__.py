# =============================================================================
# ANGELA-MATRIX: Hash+Matrix Dual System - State Module
# =============================================================================
#
# 職責: Angela 的"數位脊柱" - 狀態主權與真實性保障
# 組成: 哈希表 (骨) + 精度矩陣 (肉) + 密鑰驗證 (靈魂)
#
# "矩陣負責'肉'(語言與感知), 哈希負責'骨'(主權與真實)"
#
# =============================================================================

from .integer_hash_table import IntegerHashTable, IntegerHashEntry
from .decimal_hash_table import DecimalHashTable, DecimalHashEntry
from .precision_projection_matrix import PrecisionProjectionMatrix, PrecisionMode
from .state_hash_manager import StateHashManager

__all__ = [
    "IntegerHashTable",
    "IntegerHashEntry",
    "DecimalHashTable",
    "DecimalHashEntry",
    "PrecisionProjectionMatrix",
    "PrecisionMode",
    "StateHashManager"
]
