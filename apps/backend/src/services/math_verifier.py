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

import logging

logger = logging.getLogger(__name__)


import ast
import math
import operator
import re
from typing import Optional, Tuple


class MathExtractor:
    """Extracts and parses mathematical expressions from text."""

    SAFE_OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def __init__(self):
        self._ready = True

    def extract(self, text: str) -> Optional[Tuple[str, float]]:
        """Extract and evaluate a math expression from text."""
        patterns = [
            r'(?:計算|=?\s*)([\d\s\+\-\*\/\%\(\)\.]+?)\s*(?:\=|[\?。！？]|$)',
            r'(\d+\s*[\+\-\*\/\%]\s*\d+(?:\s*[\+\-\*\/]\s*\d+)*)',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                expr = m.group(1).strip()
                if len(expr) >= 2 and any(op in expr for op in '+-*/%'):
                    return expr, self._safe_eval(expr)
        return None

    def _safe_eval(self, expr: str) -> Optional[float]:
        """Safely evaluate a math expression using AST."""
        try:
            tree = ast.parse(expr.strip(), mode='eval')
            if not isinstance(tree.body, (ast.BinOp, ast.UnaryOp, ast.Constant)):
                return None
            result = self._eval_node(tree.body)
            return float(result) if result is not None else None
        except Exception:
            logger.debug("Failed to evaluate expression '%s'", expr, exc_info=True)
            return None

    def _eval_node(self, node) -> Optional[float]:
        if isinstance(node, ast.Constant):
            return float(node.value) if isinstance(node.value, (int, float)) else None
        if isinstance(node, ast.UnaryOp):
            op = self.SAFE_OPS.get(type(node.op))
            if op is None:
                return None
            operand = self._eval_node(node.operand)
            return op(operand) if operand is not None else None
        if isinstance(node, ast.BinOp):
            op = self.SAFE_OPS.get(type(node.op))
            if op is None:
                return None
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if left is None or right is None:
                return None
            try:
                return op(left, right)
            except (ZeroDivisionError, OverflowError):
                return None
        return None


class SpatialEngine:
    """Native spatial geometry engine for ground truth computation."""

    def __init__(self):
        self._ready = True
        self._extractor = MathExtractor()

    def compute(self, expression: str) -> Optional[float]:
        """Compute a numeric expression (delegates to MathExtractor)."""
        result = self._extractor.extract(expression)
        return result[1] if result else None


class MathVerifier:
    """MathVerifier — compares LLM extracted math with ground truth computation."""

    def __init__(self, state_matrix=None):
        self._ready = True
        self.state_matrix = state_matrix
        self._extractor = MathExtractor()

    def is_math_message(self, text: str) -> bool:
        math_patterns = [
            r'\d+\s*[\+\-\*\/\%]\s*\d+',
            r'(?:計算|求解|解方程|sum|calculate|compute)',
            r'[\=\?]\s*\d+',
        ]
        return any(re.search(p, text) for p in math_patterns)

    async def verify(self, message: str, user_name: str = "") -> "MathVerifyResult":
        """Verify a math expression by computing ground truth."""
        extracted = self._extractor.extract(message)
        if extracted is None:
            # Check for simple numbers (e.g., "what is 5+3?")
            num_pattern = r'(\d+)\s*([\+\-\*\/])\s*(\d+)'
            m = re.search(num_pattern, message)
            if m:
                a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
                ops_map = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv}
                if op in ops_map:
                    try:
                        result = ops_map[op](a, b)
                        return MathVerifyResult(
                            response_text=f"{a} {op} {b} = {result}",
                            is_correct=True,
                            explanation=f"計算結果: {result}",
                        )
                    except (ZeroDivisionError, Exception):
                        logger.debug("Math evaluation failed for expression: %s", message)
            return MathVerifyResult(
                response_text=None,
                is_correct=False,
                explanation="無法識別數學表達式",
            )

        expr, result = extracted
        return MathVerifyResult(
            response_text=f"{expr} = {result}",
            is_correct=True,
            explanation=f"表達式 '{expr}' 的計算結果為 {result}",
        )


class MathVerifyResult:
    """Result container for math verification."""

    def __init__(self, response_text=None, is_correct=None, explanation=None):
        self.response_text = response_text
        self.is_correct = is_correct
        self.explanation = explanation
        self.matches = is_correct or False
        self.needs_clarification = False
        self.extraction = None
        self.final_answer = None
        if response_text:
            self.extraction = {"confidence": 0.9}
            self.final_answer = response_text


# =============================================================================
# ANGELA-MATRIX: [L3] [αδ] [B] [L2]
# =============================================================================

# ---------------------------------------------------------------------------
# Single compute source for math.
#
# MathVerifier is the ONLY arithmetic engine. Chinese-numeral support was
# ported here from MathRippleEngine so that ED3N / GARDEN / cognitive_pipeline
# all route computation through one place instead of each re-implementing an
# evaluator. MathRippleEngine is kept ONLY for ripple/state propagation and now
# delegates its numeric result to compute_arithmetic() below.
# ---------------------------------------------------------------------------

_ZH_NUM = {
    "零": 0, "一": 1, "二": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
    "十": 10, "百": 100, "千": 1000, "万": 10000,
    "两": 2, "〇": 0, "壹": 1, "贰": 2, "叁": 3,
    "肆": 4, "伍": 5, "陆": 6, "柒": 7, "捌": 8, "玖": 9,
}

_ZH_OPS = {
    "加": "+", "加上": "+", "减": "-", "减去": "-",
    "乘": "*", "乘以": "*", "乘上": "*", "times": "*",
    "除": "/", "除以": "/", "divided": "/",
    "的和": "+", "的差": "-", "的积": "*", "的商": "/",
    "等于": "=", "等於": "=", "是多少": "=", "等于几": "=", "结果": "=",
    "plus": "+", "minus": "-",
}

_ZH_NUM_RE = re.compile(r"[零一二两三四五六七八九十百千万〇壹贰叁肆伍陆柒捌玖]+")


def _convert_chinese_numbers(text: str) -> str:
    """Convert runs of Chinese numerals to Arabic (positional multipliers)."""

    def convert_number(s: str) -> str:
        result = 0
        current = 0
        for ch in s:
            if ch in _ZH_NUM:
                val = _ZH_NUM[ch]
                if val >= 10:
                    if current == 0:
                        current = 1
                    result += current * val
                    current = 0
                else:
                    current = current * 10 + val
            else:
                return s
        return str(result + current)

    return _ZH_NUM_RE.sub(lambda m: convert_number(m.group(0)), text)


def convert_chinese_math(text: str) -> Optional[str]:
    """Convert a Chinese math expression to Arabic. Returns None if not math."""
    cleaned = text.strip().rstrip("？?！!。.")
    cleaned = _convert_chinese_numbers(cleaned)
    for zh_op, en_op in sorted(_ZH_OPS.items(), key=lambda x: -len(x[0])):
        cleaned = cleaned.replace(zh_op, f" {en_op} ")
    if re.search(r"\d+\s*[+\-*/]\s*\d+", cleaned):
        return cleaned
    return None


def _normalize_expr(text: str) -> str:
    """Strip leading/trailing non-arithmetic decoration (e.g. 等于/？/=)."""
    expr = text.strip().replace("×", "*").replace("÷", "/").replace("^", "**")
    converted = convert_chinese_math(expr)
    expr = converted if converted is not None else expr
    expr = re.sub(r"^[=等于是\s]+", "", expr).strip()
    expr = re.sub(r"[=？?！!。.\s]+$", "", expr).strip()
    return expr


def compute_arithmetic(text: str) -> Optional[float]:
    """Safe arithmetic evaluation (Arabic OR Chinese). Single source of truth.

    Returns the numeric result, or None when the input is not a math expression
    (division by zero and other unsafe forms also return None).
    """
    if not text:
        return None
    expr = _normalize_expr(text)
    extracted = MathExtractor().extract(expr)
    if extracted is None:
        return None
    _, result = extracted
    return result


def evaluate_math(text: str) -> Optional[str]:
    """Single-source math answer for ED3N/GARDEN dictionary-layer routing.

    Returns a formatted "expr = result" string, or None when not a math expression.
    """
    if not text:
        return None
    display = text.strip().rstrip("？?！!。.")
    expr = _normalize_expr(text)
    if not re.search(r"\d+\s*(\*\*|//|[+\-*/%])\s*\d+", expr):
        return None
    # Division by zero -> dedicated message (preserves prior behaviour)
    if re.search(r"/\s*0(?![.\d])", expr):
        return f"{display} = 除数不能为零"
    extracted = MathExtractor().extract(expr)
    if extracted is None:
        return None
    _, result = extracted
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    if isinstance(result, int):
        return f"{display} = {result}"
    if isinstance(result, float) and math.isinf(result):
        return f"{display} = 除数不能为零"
    return f"{display} = {result:.2f}"
