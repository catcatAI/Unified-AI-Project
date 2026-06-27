"""
共用文字處理工具

提取自 template_matcher.py 和 ham_manager.py。
保留向後兼容：各文件的原方法轉接到這裡的函數。
"""

import re
from typing import List, Optional, Set


def char_bigrams(text: str) -> set:
    """字元級 bigram（含 edge-case guard）"""
    if len(text) < 2:
        return {text} if text else set()
    return {text[i:i+2] for i in range(len(text) - 1)}


def bigram_jaccard(text_a: str, text_b: str) -> float:
    """Bigram Jaccard 相似度（含 1.2x 縮放和 0.95 上限）"""
    a, b = char_bigrams(text_a), char_bigrams(text_b)
    if not a or not b:
        return 0.0
    jaccard = len(a & b) / len(a | b)
    return min(0.95, jaccard * 1.2)


def normalize_text(text: str) -> str:
    """文字標準化：lowercase + 去標點空格"""
    text = text.lower()
    for ch in [" ", "?", "!", "。", "？", "！", "，", ","]:
        text = text.replace(ch, "")
    return text
