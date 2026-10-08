# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""ai.attention 匯出（E2 機制原型 + 退化檢測 + 匯度量）。"""

from .degeneracy import detect_loop, loop_rate, trigrams
from .inner_outer import Allocation, InnerOuterAttention, attention_inwardness, attention_sink_mass

__all__ = [
    "Allocation",
    "InnerOuterAttention",
    "attention_inwardness",
    "attention_sink_mass",
    "detect_loop",
    "loop_rate",
    "trigrams",
]
