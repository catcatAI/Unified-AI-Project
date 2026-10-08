# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""ai.attention 匯出（E2 機制原型 + 退化檢測）。"""

from .degeneracy import detect_loop, loop_rate, trigrams
from .inner_outer import Allocation, InnerOuterAttention

__all__ = ["Allocation", "InnerOuterAttention", "detect_loop", "loop_rate", "trigrams"]
