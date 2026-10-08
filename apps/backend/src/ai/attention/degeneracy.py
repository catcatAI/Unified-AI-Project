# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""退化檢測器（E2-token）：文本是否進入重複環（純函數，確定性）。

loop 定義：任一 3-gram 出現 >= 3 次（貪婪解碼鎖死的文本簽名，含週期 1
口吃與週期 3 短語環）。只判有無，不判好壞；閾值寫死以保證跨實驗可比。
"""

from __future__ import annotations

from collections import Counter
from typing import List


def trigrams(text: str) -> List[str]:
    """字級 3-gram 序列（空白正規化後切分）。"""
    tokens = text.split()
    return [" ".join(tokens[i : i + 3]) for i in range(len(tokens) - 2)]


def detect_loop(text: str, repeats: int = 3) -> bool:
    """任一 3-gram 出現 repeats 次即記 loop_entry。"""
    grams = trigrams(text)
    if not grams:
        return False
    return max(Counter(grams).values()) >= repeats


def loop_rate(texts: list) -> float:
    """一組完成的 loop 比例（空組回 0.0，不炸門）。"""
    if not texts:
        return 0.0
    return sum(1 for t in texts if detect_loop(t)) / len(texts)
