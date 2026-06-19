"""
安全表達式求值器 / Secure Expression Evaluator
===============================================

使用 AST 解析實作安全的 eval 替代方案。
僅允許白名單內的操作符和函數。

安全特性:
- 使用 AST 解析表達式，不執行任意代碼
- 僅允許白名單內的操作符和函數
- 自動類型轉換 (int/float/bool/str)
- 防止代碼注入攻擊
"""

from __future__ import annotations

import ast
import operator
from typing import Any, Dict, List, Optional, Set, Tuple, Union


SAFE_OPERATORS: Dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: operator.and_,
    ast.Or: operator.or_,
    ast.Not: operator.not_,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
}

SAFE_NAMES: Dict[str, Any] = {
    "True": True,
    "False": False,
    "None": None,
    "int": int,
    "float": float,
    "bool": bool,
    "str": str,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "abs": abs,
    "max": max,
    "min": min,
    "sum": sum,
    "len": len,
    "round": round,
    "range": range,
    "sorted": sorted,
    "reversed": reversed,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "any": any,
    "all": all,
    "isinstance": isinstance,
    "type": type,
    "pow": pow,
}


class UnsafeExpressionError(ValueError):
    """表達式包含不允許的操作 / Expression contains unsafe operations"""
    pass


def safe_eval(
    expression: str,
    context: Optional[Dict[str, Any]] = None,
    max_nodes: int = 500,
    _safe_operators: Optional[Dict[type, Any]] = None,
    _safe_names: Optional[Dict[str, Any]] = None,
) -> EvalResult:
    """
    安全地求值表達式 / Safely evaluate an expression

    Args:
        expression: 要求值的 Python 表達式字串
        context: 可選的變量上下文 dict
        max_nodes: AST 節點數量限制（防止 DoS）
        _safe_operators: 內部使用，自定義安全操作符
        _safe_names: 內部使用，自定義安全名稱

    Returns:
        EvalResult: 求值結果

    Example:
        >>> r = safe_eval("1 + 2 * 3")
        >>> r.success, r.result
        (True, 7)
    """
    safe_ops = SAFE_OPERATORS if _safe_operators is None else _safe_operators
    safe_nms = SAFE_NAMES if _safe_names is None else _safe_names

    if not isinstance(expression, str):
        return EvalResult(success=False, error=f"表達式必須是字串，得到 {type(expression).__name__}", expression=str(expression))

    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as e:
        return EvalResult(success=False, error=str(e), expression=expression)

    node_count = 0

    def _check(node: ast.AST) -> None:
        nonlocal node_count
        node_count += 1
        if node_count > max_nodes:
            raise UnsafeExpressionError(f"表達式過於複雜 (超過 {max_nodes} 個節點)")

        if isinstance(node, ast.Expression):
            _check(node.body)
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in safe_ops:
                raise UnsafeExpressionError(f"不允許的二進制操作符: {type(node.op).__name__}")
            _check(node.left)
            _check(node.right)
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in safe_ops:
                raise UnsafeExpressionError(f"不允許的一元操作符: {type(node.op).__name__}")
            _check(node.operand)
        elif isinstance(node, ast.BoolOp):
            if type(node.op) not in safe_ops:
                raise UnsafeExpressionError(f"不允許的邏輯操作符: {type(node.op).__name__}")
            for v in node.values:
                _check(v)
        elif isinstance(node, ast.Compare):
            for op in node.ops:
                if type(op) not in safe_ops:
                    raise UnsafeExpressionError(f"不允許的比較操作符: {type(op).__name__}")
            _check(node.left)
            for c in node.comparators:
                _check(c)
        elif isinstance(node, ast.Name):
            if node.id not in safe_nms and (context is None or node.id not in context):
                raise UnsafeExpressionError(f"不允許的名稱訪問: '{node.id}'")
        elif isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float, bool, str, bytes, type(None))):
                raise UnsafeExpressionError(f"不允許的常量類型: {type(node.value).__name__}")
        elif isinstance(node, ast.List):
            for elt in node.elts:
                _check(elt)
        elif isinstance(node, ast.Tuple):
            for elt in node.elts:
                _check(elt)
        elif isinstance(node, ast.Dict):
            for k in node.keys:
                if k is not None:
                    _check(k)
            for v in node.values:
                _check(v)
        elif isinstance(node, ast.Set):
            for elt in node.elts:
                _check(elt)
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise UnsafeExpressionError("僅支援簡單函數調用 (不支援方法調用)")
            if node.func.id not in safe_nms:
                raise UnsafeExpressionError(f"不允許的函數調用: '{node.func.id}'")
            for arg in node.args:
                _check(arg)
            for kw in node.keywords:
                _check(kw.value)
        elif isinstance(node, ast.ListComp):
            _check(node.elt)
            for gen in node.generators:
                _check(gen)
        elif isinstance(node, ast.comprehension):
            _check(node.target)
            _check(node.iter)
            for if_clause in node.ifs:
                _check(if_clause)
        elif isinstance(node, ast.Subscript):
            _check(node.value)
            _check(node.slice)
        elif isinstance(node, ast.Slice):
            if node.lower:
                _check(node.lower)
            if node.upper:
                _check(node.upper)
            if node.step:
                _check(node.step)
        elif isinstance(node, ast.Attribute):
            raise UnsafeExpressionError("不允許的屬性訪問")
        elif isinstance(node, (ast.IfExp, ast.Lambda)):
            raise UnsafeExpressionError("不允許的條件表達式或 lambda")
        else:
            raise UnsafeExpressionError(f"不允許的 AST 節點: {type(node).__name__}")

    try:
        _check(tree)
    except UnsafeExpressionError as e:
        return EvalResult(success=False, error=str(e), expression=expression)

    names = dict(safe_nms)
    if context:
        names.update(context)

    try:
        code = compile(tree, "<safe_eval>", "eval")
        result = eval(code, {"__builtins__": {}}, names)
        return EvalResult(success=True, result=result, expression=expression)
    except (ValueError, TypeError, ZeroDivisionError) as e:
        return EvalResult(success=False, error=str(e), expression=expression)


from dataclasses import dataclass, field


@dataclass
class EvalResult:
    """求值結果 / Evaluation result"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    expression: Optional[str] = None


class SafeEvaluator:
    """
    安全表達式求值器類 / Safe expression evaluator class

    提供 evaluate() 方法，返回 EvalResult 物件。
    """

    def __init__(self, max_length: int = 0, max_complexity: int = 0, max_nodes: int = 500):
        self.max_length = max_length
        self.max_complexity = max_complexity
        self.max_nodes = max_nodes

    def _check_length(self, expression: str) -> None:
        if self.max_length > 0 and len(expression) > self.max_length:
            raise UnsafeExpressionError(f"表達式長度 {len(expression)} 超過限制 {self.max_length}")

    def evaluate(self, expression: str, context: Optional[Dict[str, Any]] = None) -> EvalResult:
        """
        安全地求值表達式 / Safely evaluate an expression

        Args:
            expression: 要求值的 Python 表達式字串
            context: 可選的變量上下文 dict

        Returns:
            EvalResult: 求值結果
        """
        try:
            if not isinstance(expression, str):
                return EvalResult(success=False, error=f"表達式必須是字串，得到 {type(expression).__name__}", expression=str(expression))
            self._check_length(expression)
            return safe_eval(expression, context, max_nodes=self.max_nodes if self.max_complexity <= 0 else self.max_complexity)
        except (SyntaxError, UnsafeExpressionError) as e:
            return EvalResult(success=False, error=str(e), expression=expression)

    def evaluate_arithmetic(self, expression: str, context: Optional[Dict[str, Any]] = None) -> EvalResult:
        """
        安全地求值算術表達式 / Safely evaluate an arithmetic expression

        Args:
            expression: 要求值的算術表達式字串
            context: 可選的變量上下文 dict

        Returns:
            EvalResult: 求值結果
        """
        try:
            if not isinstance(expression, str):
                return EvalResult(success=False, error=f"表達式必須是字串，得到 {type(expression).__name__}", expression=str(expression))
            self._check_length(expression)
            return safe_eval_arithmetic(
                expression, context,
                max_nodes=self.max_nodes if self.max_complexity <= 0 else self.max_complexity,
            )
        except (SyntaxError, UnsafeExpressionError) as e:
            return EvalResult(success=False, error=str(e), expression=expression)


# 僅允許算術操作的 SAFE_OPERATORS 子集
ARITHMETIC_OPERATORS = {k: v for k, v in SAFE_OPERATORS.items() if k in {
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.USub, ast.UAdd,
}}

# 僅允許數字和基本算術的 SAFE_NAMES 子集
ARITHMETIC_NAMES: Dict[str, Any] = {
    "True": True, "False": False, "None": None,
    "int": int, "float": float, "bool": bool, "abs": abs, "round": round, "pow": pow,
}


def safe_eval_arithmetic(
    expression: str,
    context: Optional[Dict[str, Any]] = None,
    max_nodes: int = 200,
) -> EvalResult:
    """
    安全地求值算術表達式 / Safely evaluate an arithmetic expression

    比 safe_eval 更嚴格，僅允許算術操作符和基本類型。

    Args:
        expression: 要求值的算術表達式字串
        context: 可選的變量上下文 dict
        max_nodes: AST 節點數量限制

    Returns:
        EvalResult: 求值結果
    """
    result = safe_eval(
        expression, context, max_nodes,
        _safe_operators=ARITHMETIC_OPERATORS,
        _safe_names=ARITHMETIC_NAMES,
    )
    if result.success and not isinstance(result.result, (int, float)):
        return EvalResult(success=False, error=f"算術表達式返回非數值類型: {type(result.result).__name__}", expression=expression)
    return result


_default_evaluator: Optional[SafeEvaluator] = None


def get_safe_evaluator() -> SafeEvaluator:
    """
    獲取默認的 SafeEvaluator 實例 / Get default SafeEvaluator instance
    """
    global _default_evaluator
    if _default_evaluator is None:
        _default_evaluator = SafeEvaluator()
    return _default_evaluator
