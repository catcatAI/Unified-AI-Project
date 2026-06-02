# =============================================================================
# ANGELA-MATRIX: 安全表達式求值器
# =============================================================================
#
# 職責: 提供安全的表達式求值功能，替代不安全的 eval()
# 安全: 使用 AST 解析和沙箱隔離
# 成熟度: L2+ 等級
#
# 安全特性:
# - 使用 AST 解析表達式
# - 僅允許特定的安全操作符和函數
# - 沙箱隔離，防止訪問系統資源
# - 輸入驗證和清理
# - 防止代碼注入攻擊
#
# =============================================================================

import ast
import operator
import logging
import sys
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Compatibility for removed AST node types (Python >= 3.14 removed deprecated aliases)
_HAS_NUM = hasattr(ast, "Num")
_HAS_STR = hasattr(ast, "Str")
_HAS_NAMECONST = hasattr(ast, "NameConstant")
_HAS_INDEX = hasattr(ast, "Index")


@dataclass
class EvalResult:
    """表達式求值結果"""

    success: bool
    result: Any = None
    error: Optional[str] = None
    expression: Optional[str] = None


class SafeEvaluator:
    """
    安全的表達式求值器

    使用 AST 解析來評估表達式，僅允許預定義的安全操作。

    支持的運算符:
    - 算術: +, -, *, /, //, %, **
    - 比較: ==, !=, <, >, <=, >=
    - 邏輯: and, or, not
    - 位運算: &, |, ^, ~, <<, >>

    支持的函數:
    - 數學: abs, min, max, round, pow
    - 類型檢查: int, float, str, bool

    支持的對象:
    - 數字: int, float
    - 字符串: str
    - 布爾值: bool, True, False
    - None: None
    """

    # 允許的操作符
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.BitAnd: operator.and_,
        ast.Invert: operator.invert,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Not: operator.not_,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
        ast.In: lambda a, b: a in b,
        ast.NotIn: lambda a, b: a not in b,
    }

    # 允許的函數
    ALLOWED_FUNCTIONS = {
        "abs": abs,
        "min": min,
        "max": max,
        "round": round,
        "pow": pow,
        "len": len,
        "sum": sum,
        "sorted": sorted,
        "any": any,
        "all": all,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "tuple": tuple,
        "set": set,
        "dict": dict,
    }

    # 允許的常量
    ALLOWED_CONSTANTS = {
        "True": True,
        "False": False,
        "None": None,
    }

    # 允許的節點類型
    ALLOWED_NODE_TYPES: Set[type] = {
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.BoolOp,
        ast.Constant,
        ast.Call,
        ast.List,
        ast.Tuple,
        ast.Set,
        ast.Dict,
        ast.Subscript,
        ast.Slice,
        ast.Name,
    }
    if _HAS_NUM:
        ALLOWED_NODE_TYPES.add(ast.Num)
    if _HAS_STR:
        ALLOWED_NODE_TYPES.add(ast.Str)
    if _HAS_NAMECONST:
        ALLOWED_NODE_TYPES.add(ast.NameConstant)
    if _HAS_INDEX:
        ALLOWED_NODE_TYPES.add(ast.Index)

    def __init__(self, max_length: int = 1000, max_complexity: int = 100):
        """
        初始化安全求值器

        Args:
            max_length: 表達式最大長度
            max_complexity: 最大複雜度（節點數）
        """
        self.max_length = max_length
        self.max_complexity = max_complexity
        self.complexity = 0

    def evaluate(self, expression: str, context: Optional[Dict[str, Any]] = None) -> EvalResult:
        """
        安全地評估表達式

        Args:
            expression: 要評估的表達式字符串
            context: 可選的上下文變量字典

        Returns:
            EvalResult: 評估結果
        """
        self.complexity = 0

        if context is None:
            context = {}

        try:
            # 1. 驗證輸入
            if not expression or not isinstance(expression, str):
                return EvalResult(
                    success=False, error="表達式必須是非空字符串", expression=expression
                )

            # 2. 檢查長度
            if len(expression) > self.max_length:
                return EvalResult(
                    success=False,
                    error=f"表達式過長 (最大: {self.max_length}, 當前: {len(expression)})",
                    expression=expression,
                )

            # 3. 解析 AST
            try:
                tree = ast.parse(expression, mode="eval")
            except SyntaxError as e:
                logger.warning(f"Expression syntax error: {e}", exc_info=True)
                return EvalResult(success=False, error=f"語法錯誤: {e}", expression=expression)

            # 4. 驗證並評估 AST
            result = self._eval_node(tree, context)

            # 5. 檢查複雜度
            if self.complexity > self.max_complexity:
                return EvalResult(
                    success=False,
                    error=f"表達式過於複雜 (最大: {self.max_complexity}, 當前: {self.complexity})",
                    expression=expression,
                )

            return EvalResult(success=True, result=result, expression=expression)

        except RecursionError:
            return EvalResult(success=False, error="表達式過深（遞歸限制）", expression=expression)
        except Exception as e:  # broad exception acceptable: expression evaluation fallback
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            return EvalResult(success=False, error=f"評估錯誤: {str(e)}", expression=expression)

    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """
        評估 AST 節點

        Args:
            node: AST 節點
            context: 上下文變量

        Returns:
            評估結果

        Raises:
            ValueError: 如果遇到不允許的節點類型
        """
        self.complexity += 1

        if isinstance(node, ast.Expression):
            return self._eval_expression_node(node, context)
        elif isinstance(node, ast.Constant):
            return self._eval_constant_node(node, context)
        elif _HAS_NUM and isinstance(node, ast.Num):
            return self._eval_num_node(node, context)
        elif _HAS_STR and isinstance(node, ast.Str):
            return self._eval_str_node(node, context)
        elif _HAS_NAMECONST and isinstance(node, ast.NameConstant):
            return self._eval_nameconstant_node(node, context)
        elif isinstance(node, ast.Name):
            return self._eval_name_node(node, context)
        elif isinstance(node, ast.BinOp):
            return self._eval_binop_node(node, context)
        elif isinstance(node, ast.UnaryOp):
            return self._eval_unaryop_node(node, context)
        elif isinstance(node, ast.Compare):
            return self._eval_compare_node(node, context)
        elif isinstance(node, ast.BoolOp):
            return self._eval_boolop_node(node, context)
        elif isinstance(node, ast.Call):
            return self._eval_call_node(node, context)
        elif isinstance(node, ast.List):
            return self._eval_list_node(node, context)
        elif isinstance(node, ast.Tuple):
            return self._eval_tuple_node(node, context)
        elif isinstance(node, ast.Set):
            return self._eval_set_node(node, context)
        elif isinstance(node, ast.Dict):
            return self._eval_dict_node(node, context)
        elif isinstance(node, ast.Subscript):
            return self._eval_subscript_node(node, context)
        else:
            raise ValueError(f"不允許的節點類型: {type(node).__name__}")

    def _eval_expression_node(self, node: ast.Expression, context: Dict[str, Any]) -> Any:
        return self._eval_node(node.body, context)

    def _eval_constant_node(self, node: ast.Constant, context: Dict[str, Any]) -> Any:
        return node.value

    def _eval_num_node(self, node: ast.Num, context: Dict[str, Any]) -> Any:
        return node.n

    def _eval_str_node(self, node: ast.Str, context: Dict[str, Any]) -> Any:
        return node.s

    def _eval_nameconstant_node(self, node: ast.NameConstant, context: Dict[str, Any]) -> Any:
        return node.value

    def _eval_name_node(self, node: ast.Name, context: Dict[str, Any]) -> Any:
        if node.id in self.ALLOWED_CONSTANTS:
            return self.ALLOWED_CONSTANTS[node.id]
        if node.id in context:
            return context[node.id]
        if node.id in self.ALLOWED_FUNCTIONS:
            return self.ALLOWED_FUNCTIONS[node.id]
        raise ValueError(f"不允許的變量或函數: {node.id}")

    def _eval_binop_node(self, node: ast.BinOp, context: Dict[str, Any]) -> Any:
        left = self._eval_node(node.left, context)
        right = self._eval_node(node.right, context)
        op_type = type(node.op)
        if op_type in self.ALLOWED_OPERATORS:
            return self.ALLOWED_OPERATORS[op_type](left, right)
        raise ValueError(f"不允許的操作符: {op_type}")

    def _eval_unaryop_node(self, node: ast.UnaryOp, context: Dict[str, Any]) -> Any:
        operand = self._eval_node(node.operand, context)
        op_type = type(node.op)
        if op_type in self.ALLOWED_OPERATORS:
            return self.ALLOWED_OPERATORS[op_type](operand)
        raise ValueError(f"不允許的一元操作符: {op_type}")

    def _eval_compare_node(self, node: ast.Compare, context: Dict[str, Any]) -> Any:
        left = self._eval_node(node.left, context)
        result = True
        for op, comparator in zip(node.ops, node.comparators):
            right = self._eval_node(comparator, context)
            op_type = type(op)
            if op_type in self.ALLOWED_OPERATORS:
                result = self.ALLOWED_OPERATORS[op_type](left, right)
            else:
                raise ValueError(f"不允許的比較操作符: {op_type}")
            if not result:
                break
            left = right
        return result

    def _eval_boolop_node(self, node: ast.BoolOp, context: Dict[str, Any]) -> Any:
        op_type = type(node.op)
        values = [self._eval_node(v, context) for v in node.values]
        if op_type == ast.And:
            return all(values)
        elif op_type == ast.Or:
            return any(values)
        raise ValueError(f"不允許的布爾操作符: {op_type}")

    def _eval_call_node(self, node: ast.Call, context: Dict[str, Any]) -> Any:
        func = self._eval_node(node.func, context)
        if not callable(func):
            raise ValueError(f"不可調用的對象: {func}")
        args = [self._eval_node(arg, context) for arg in node.args]
        kwargs = {kw.arg: self._eval_node(kw.value, context) for kw in node.keywords}
        return func(*args, **kwargs)

    def _eval_list_node(self, node: ast.List, context: Dict[str, Any]) -> Any:
        return [self._eval_node(e, context) for e in node.elts]

    def _eval_tuple_node(self, node: ast.Tuple, context: Dict[str, Any]) -> Any:
        return tuple(self._eval_node(e, context) for e in node.elts)

    def _eval_set_node(self, node: ast.Set, context: Dict[str, Any]) -> Any:
        return {self._eval_node(e, context) for e in node.elts}

    def _eval_dict_node(self, node: ast.Dict, context: Dict[str, Any]) -> Any:
        keys = [self._eval_node(k, context) for k in node.keys]
        values = [self._eval_node(v, context) for v in node.values]
        return dict(zip(keys, values))

    def _eval_subscript_node(self, node: ast.Subscript, context: Dict[str, Any]) -> Any:
        value = self._eval_node(node.value, context)
        if isinstance(node.slice, ast.Index):
            index = self._eval_node(node.slice.value, context)
        elif isinstance(node.slice, ast.Slice):
            start = self._eval_node(node.slice.lower, context) if node.slice.lower else None
            stop = self._eval_node(node.slice.upper, context) if node.slice.upper else None
            step = self._eval_node(node.slice.step, context) if node.slice.step else None
            index = slice(start, stop, step)
        else:
            index = self._eval_node(node.slice, context)
        return value[index]

    def evaluate_arithmetic(self, expression: str) -> EvalResult:
        """
        評估算術表達式（僅允許數學運算）

        Args:
            expression: 算術表達式

        Returns:
            EvalResult: 評估結果
        """
        # 創建受限的上下文，只包含數學函數
        math_context = {
            "abs": abs,
            "round": round,
            "pow": pow,
            "min": min,
            "max": max,
        }

        result = self.evaluate(expression, math_context)

        # 驗證結果類型
        if result.success and not isinstance(result.result, (int, float, bool)):
            return EvalResult(
                success=False,
                error=f"算術表達式必須返回數值，得到: {type(result.result).__name__}",
                expression=expression,
            )

        return result


# 全局實例
_evaluator: Optional[SafeEvaluator] = None


# DORMANT FACTORY (not called externally)
def get_safe_evaluator() -> SafeEvaluator:
    """獲取全局安全求值器實例"""
    global _evaluator
    if _evaluator is None:
        _evaluator = SafeEvaluator()
    return _evaluator


def safe_eval(expression: str, context: Optional[Dict[str, Any]] = None) -> EvalResult:
    """
    安全地評估表達式（便捷函數）

    Args:
        expression: 要評估的表達式
        context: 可選的上下文變量

    Returns:
        EvalResult: 評估結果
    """
    evaluator = get_safe_evaluator()
    return evaluator.evaluate(expression, context)


def safe_eval_arithmetic(expression: str) -> EvalResult:
    """
    安全地評估算術表達式（便捷函數）

    Args:
        expression: 算術表達式

    Returns:
        EvalResult: 評估結果
    """
    evaluator = get_safe_evaluator()
    return evaluator.evaluate_arithmetic(expression)


if __name__ == "__main__":
    # 測試安全求值器
    logging.basicConfig(level=logging.INFO)

    logger.info("測試安全表達式求值器")
    logger.info("=" * 60)

    test_cases = [
        # 算術運算
        ("1 + 1", True),
        ("2 * 3 + 4", True),
        ("10 / 2", True),
        ("2 ** 8", True),
        ("abs(-5)", True),
        ("round(3.14159, 2)", True),
        # 邏輯運算
        ("True and False", True),
        ("True or False", True),
        ("not True", True),
        ("1 < 2 and 3 > 4", True),
        # 危險操作（應該失敗）
        ("__import__('os')", False),
        ("open('test.txt')", False),
        ("exec('print(1)')", False),
        ("eval('1+1')", False),
        ("().__class__", False),
    ]

    for expr, should_succeed in test_cases:
        result = safe_eval(expr)
        status = "✓" if (result.success == should_succeed) else "✗"
        logger.info(f"{status} {expr}")
        if result.success:
            logger.info(f"  結果: {result.result}")
        else:
            logger.error(f"  錯誤: {result.error}", exc_info=True)
        logger.info()

    logger.info("=" * 60)
    logger.info("測試完成")
