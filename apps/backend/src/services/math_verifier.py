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
from typing import Any, Dict, List, Optional, Tuple


class MathExtractor:
    """Extracts and parses mathematical expressions from text."""

    SAFE_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def __init__(self):
        self._ready = True

    def extract(self, text: str) -> Optional[Tuple[str, Optional[float]]]:
        """Extract and evaluate a math expression from text."""
        patterns = [
            r"(?:計算|=?\s*)(-?[\d\s\+\-\*\/\%\(\)\.]+?)\s*(?:\=|[\?。！？]|$)",
            r"(-?\d+\s*[\+\-\*\/\%]\s*-?\d+(?:\s*[\+\-\*\/]\s*-?\d+)*)",
            r"([a-zA-Z_]\w*(?:\s*\([^)]*\))(?:\s*[\+\-\*\/]\s*[a-zA-Z_]\w*(?:\s*\([^)]*\)))*)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                expr = m.group(1).strip()
                if len(expr) >= 2 and (any(op in expr for op in "+-*/%") or re.search(r"[a-zA-Z_]\w*\(", expr)):
                    return expr, self._safe_eval(expr)
        return None

    def _safe_eval(self, expr: str) -> Optional[float]:
        """Safely evaluate a math expression using AST."""
        try:
            tree = ast.parse(expr.strip(), mode="eval")
            if not isinstance(tree.body, (ast.BinOp, ast.UnaryOp, ast.Constant, ast.Call)):
                return None
            result = self._eval_node(tree.body)
            return float(result) if result is not None else None
        except Exception:
            logger.warning("Failed to evaluate expression '%s'", expr, exc_info=True)
            return None

    def _eval_node(self, node) -> Optional[float]:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return float(node.value)
            if isinstance(node.value, int):
                return node.value
            if isinstance(node.value, float):
                return node.value
            return None
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
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                return None
            fn_name = node.func.id
            fn = _SAFE_FUNCTIONS.get(fn_name)
            if fn is None:
                return None
            args = [self._eval_node(a) for a in node.args]
            if any(a is None for a in args):
                return None
            try:
                return float(fn(*args))
            except (ValueError, OverflowError, ZeroDivisionError):
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
            r"\d+\s*[\+\-\*\/\%]\s*\d+",
            r"(?:計算|求解|解方程|sum|calculate|compute)",
            r"[\=\?]\s*\d+",
        ]
        return any(re.search(p, text) for p in math_patterns)

    def verify(self, message: str, user_name: str = "") -> "MathVerifyResult":
        """Verify a math expression by computing ground truth."""
        extracted = self._extractor.extract(message)
        if extracted is None:
            # Check for simple numbers (e.g., "what is 5+3?")
            num_pattern = r"(\d+)\s*([\+\-\*\/])\s*(\d+)"
            m = re.search(num_pattern, message)
            if m:
                a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
                ops_map = {
                    "+": operator.add,
                    "-": operator.sub,
                    "*": operator.mul,
                    "/": operator.truediv,
                }
                if op in ops_map:
                    try:
                        result = ops_map[op](a, b)
                        return MathVerifyResult(
                            response_text=f"{a} {op} {b} = {result}",
                            is_correct=True,
                            explanation=f"計算結果: {result}",
                        )
                    except (ZeroDivisionError, Exception):
                        logger.warning("Math evaluation failed for expression: %s", message, exc_info=True)
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
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "百": 100,
    "千": 1000,
    "万": 10000,
    "两": 2,
    "〇": 0,
    "壹": 1,
    "贰": 2,
    "叁": 3,
    "肆": 4,
    "伍": 5,
    "陆": 6,
    "柒": 7,
    "捌": 8,
    "玖": 9,
}

# Safe functions for AST Call node evaluation
_SAFE_FUNCTIONS: Dict[str, Any] = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "radians": math.radians,
    "degrees": math.degrees,
    "factorial": math.factorial,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
}

# Math constant name → (display_name, numeric_value)
_MATH_CONSTANTS: Dict[str, Tuple[str, float]] = {
    "pi": ("π", math.pi),
    "π": ("π", math.pi),
    "e": ("e", math.e),
    "inf": ("∞", float("inf")),
}

# Number theory helpers
def _is_prime(n: float) -> bool:
    m = int(n)
    if m != n or m < 2:
        return False
    if m < 4:
        return True
    if m % 2 == 0 or m % 3 == 0:
        return False
    i = 5
    while i * i <= m:
        if m % i == 0 or m % (i + 2) == 0:
            return False
        i += 6
    return True


def _gcd(a: float, b: float) -> int:
    x, y = int(a), int(b)
    while y:
        x, y = y, x % y
    return abs(x)


def _lcm(a: float, b: float) -> int:
    d = _gcd(a, b)
    return (int(a) // d) * int(b) if d else 0


_ZH_OPS = {
    "加": "+",
    "加上": "+",
    "减": "-",
    "减去": "-",
    "乘": "*",
    "乘以": "*",
    "乘上": "*",
    "times": "*",
    "除": "/",
    "除以": "/",
    "divided": "/",
    "的和": "+",
    "的差": "-",
    "的积": "*",
    "的商": "/",
    "等于": "=",
    "等於": "=",
    "是多少": "=",
    "等于几": "=",
    "结果": "=",
    "plus": "+",
    "minus": "-",
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


def evaluate_logic(text: str) -> Optional[str]:
    """Evaluate boolean logic expressions.

    Supports:
    - English: true/false/and/or/not/nor/nand/xor (case-insensitive)
    - Chinese: 真/假/或/且/既不是/並非/不成立/矛盾/衝突

    Returns "true" or "false" string, or None when not a logic expression.
    """
    if not text:
        return None

    t = text.strip().lower().rstrip("？?！!。.")

    # ---- Chinese path ----
    if any(kw in t for kw in ("或", "且", "既不是", "並非", "不成立", "矛盾", "衝突", "真", "假")):
        expr = t
        expr = expr.replace("真的", "True").replace("假的", "False")
        expr = expr.replace("真", "True").replace("假", "False")
        expr = expr.replace("或", " or ")
        expr = expr.replace("且", " and ")
        expr = expr.replace("既不是", " not ")
        expr = expr.replace("並非", " not ")
        expr = expr.replace("不成立", " not True ")
        expr = expr.replace("矛盾", " False ").replace("衝突", " False ")
        tokens = re.findall(r"\b\w+\b", expr)
        if all(t in ("True", "False", "and", "or", "not") for t in tokens):
            try:
                result = eval(expr, {"__builtins__": {}}, {})  # noqa: S307
                return "true" if result else "false"
            except Exception:
                return None
        return None

    # ---- English path ----
    if not re.search(r"\b(true|false|and|or|not|nor|nand|xor)\b", t):
        return None

    expr = t
    expr = re.sub(r"\btrue\b", "True", expr)
    expr = re.sub(r"\bfalse\b", "False", expr)

    # Expand compound operators: nor/nand/xor have fixed arity of 2
    def _expand_nor(m):
        parts = re.findall(r"(True|False)", m.group(0))
        if len(parts) == 2:
            return f"not ({parts[0]} or {parts[1]})"
        return m.group(0)

    def _expand_nand(m):
        parts = re.findall(r"(True|False)", m.group(0))
        if len(parts) == 2:
            return f"not ({parts[0]} and {parts[1]})"
        return m.group(0)

    def _expand_xor(m):
        parts = re.findall(r"(True|False)", m.group(0))
        if len(parts) == 2:
            return f"({parts[0]} and not {parts[1]}) or (not {parts[0]} and {parts[1]})"
        return m.group(0)

    expr = re.sub(r"\bnor\s+(True|False)\s+(True|False)\b", _expand_nor, expr)
    expr = re.sub(r"\bnand\s+(True|False)\s+(True|False)\b", _expand_nand, expr)
    expr = re.sub(r"\bxor\s+(True|False)\s+(True|False)\b", _expand_xor, expr)

    expr = re.sub(r"\band\b", "and", expr)
    expr = re.sub(r"\bor\b", "or", expr)
    expr = re.sub(r"\bnot\b", "not", expr)

    tokens = re.findall(r"\b\w+\b", expr)
    if all(t in ("True", "False", "and", "or", "not") for t in tokens):
        try:
            result = eval(expr, {"__builtins__": {}}, {})  # noqa: S307
            return "true" if result else "false"
        except Exception:
            return None
    return None


def evaluate_math(text: str) -> Optional[str]:
    """Single-source math answer for ED3N/GARDEN dictionary-layer routing.

    Returns a formatted "expr = result" string using only the extracted
    expression (not the original text with natural language), or None
    when not a math expression.  Float results use full precision to
    allow value-based comparison downstream.

    Supports arithmetic (``+ - * / % **``), trig (``sin, cos, tan``),
    sqrt, log, constants (``pi, e``), and number theory (``factorial``).
    """
    if not text:
        return None

    # Step 1: constant queries ("what is pi", "value of e")
    const_match = re.search(
        r"\b(pi|π|euler(?:'s)?\s*(?:number|constant)?|e\b|inf(?:inity)?)\b",
        text.strip().lower(),
    )
    if const_match:
        key = const_match.group(1)
        # Map variants to canonical constant keys
        if key in ("pi", "π"):
            display, val = _MATH_CONSTANTS["pi"]
            return f"{display} = {val}"
        if key == "e" or "euler" in key:
            display, val = _MATH_CONSTANTS["e"]
            return f"{display} = {val}"
        if key in ("inf", "infinity"):
            return "∞ = 無限大"

    # Step 2: number theory queries ("is 17 prime", "gcd 12 18")
    prime_m = re.search(r"(?:is|是)\s*(-?\d+)\s*(?:prime|質數|素数)", text.strip().lower())
    if prime_m:
        n = int(prime_m.group(1))
        result = _is_prime(n)
        return f"{n} is prime = {'true' if result else 'false'}"

    gcd_m = re.search(r"(?:gcd|最大公因數|最大公约数)\s*[：(]?\s*(-?\d+)\s*,?\s*(-?\d+)", text.strip().lower())
    if gcd_m:
        a, b = int(gcd_m.group(1)), int(gcd_m.group(2))
        return f"gcd({a}, {b}) = {_gcd(a, b)}"

    lcm_m = re.search(r"(?:lcm|最小公倍數|最小公倍数)\s*[：(]?\s*(-?\d+)\s*,?\s*(-?\d+)", text.strip().lower())
    if lcm_m:
        a, b = int(lcm_m.group(1)), int(lcm_m.group(2))
        return f"lcm({a}, {b}) = {_lcm(a, b)}"

    # Step 3: normal expression evaluation
    expr = _normalize_expr(text)
    if not re.search(r"-?\d+\s*(\*\*|//|[+\-*/%])\s*-?\d+", expr) and not re.search(r"[a-zA-Z_]\w*\s*\(", expr):
        return None
    if re.search(r"/\s*0(?![.\d])", expr):
        return f"{_normalize_expr(text)} = 除数不能为零"
    extracted = MathExtractor().extract(expr)
    if extracted is None:
        return None
    math_expr, result = extracted
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    if isinstance(result, int):
        return f"{math_expr} = {result}"
    if isinstance(result, float) and math.isinf(result):
        return f"{math_expr} = 除数不能为零"
    float_str = f"{result:.10f}".rstrip("0").rstrip(".")
    return f"{math_expr} = {float_str}"
