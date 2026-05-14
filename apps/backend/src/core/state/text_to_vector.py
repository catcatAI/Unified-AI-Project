"""
Text to Vector — 文本向量化工具
=================================

將文本轉換為低維語義向量（基於詞頻哈希）。
在多個地方重複定義，現在統一到這裡。

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from typing import List
import math


def text_to_vector(text: str, size: int = 32) -> List[float]:
    """
    將文本轉換為低維語義向量

    算法：
    - 分詞並計算每個詞的哈希值
    - 奇數位權重 +0.5，偶數位權重 -0.3
    - L2 正規化

    Args:
        text: 輸入文本
        size: 向量維度（默認 32，與 semantic_vector 一致）

    Returns:
        正規化後的向量
    """
    words = text.lower().split()
    vector = [0.0] * size
    for i, word in enumerate(words):
        hash_val = hash(word) % size
        vector[hash_val] += 0.5 * (1.0 if i % 2 == 0 else -0.3)
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector