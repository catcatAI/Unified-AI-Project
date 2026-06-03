"""
Angela Math Verifier - 雙軌數學驗證系統
========================================

架構：LLM 提取計算式 → 引擎驗證結果 → 比對並校正

| 組件 | 職責 |
|------|------|
| MathExtractor | LLM 提取數學表達式 + 理解 |
| SpatialEngine | 原生空間幾何運算（ground truth）|
| MathVerifier | 比對器 + 觸發狀態更新 |

Author: Angela AI Development Team
Version: 6.2.1
"""

from __future__ import annotations
import re
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict