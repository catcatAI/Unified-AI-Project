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
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


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
        'abs': abs,
        'min': min,
        'max': max,
        'round': round,
        'pow': pow,
        'len': len,
        'sum': sum,
        'sorted': sorted,
        'any': any,
        'all': all,
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
        'list': list,
        'tuple': tuple,
        'set': set,
        'dict': dict,
    }

    # 允許的常量
    ALLOWED_CONSTANTS = {
        'True': True,
        'False': False,
        'None': None,
    }

    # 允許的節點類型
    ALLOWED_NODE_TYPES: Set[type] = {
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.BoolOp,
        ast.Num,
        ast.Constant,
        ast.Str,
        ast.Name,
        ast.NameConstant,
        ast.Call,
        ast.List,
        ast.Tuple,
        ast.Set,
        ast.Dict,
        ast.Subscript,
        ast.Index,
        ast.Slice,
    }

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
                    success=False,
                    error="表達式必須是非空字符串",
                    expression=expression
                )

            # 2. 檢查長度
            if len(expression) > self.max_length:
                return EvalResult(
                    success=False,
                    error=f"表達式過長 (最大: {self.max_length}, 當前: {len(expression)})",
                    expression=expression
                )

            # 3. 解析 AST
            try:
                tree = ast.parse(expression, mode='eval')
            except SyntaxError as e:
                return EvalResult(
                    success=False,
                    error=f"語法錯誤: {e}",
                    expression=expression
                )

            # 4. 驗證並評估 AST
            result = self._eval_node(tree, context)

            # 5. 檢查複雜度
            if self.complexity > self.max_complexity:
                return EvalResult(
                    success=False,
                    error=f"表達式過於複雜 (最大: {self.max_complexity}, 當前: {self.complexity})",
                    expression=expression
                )

            return EvalResult(
                success=True,
                result=result,
                expression=expression
            )

        except RecursionError:
            return EvalResult(
                success=False,
                error="表達式過深（遞歸限制）",
                expression=expression
            )
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return EvalResult(

                success=False,
                error=f"評估錯誤: {str(e)}",
                expression=expression
            )

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
            return self._eval_node(node.body, context)

        elif isinstance(node, ast.Constant):
            return node.value

        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n

        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s

        elif isinstance(node, ast.NameConstant):  # Python < 3.8
            return node.value

        elif isinstance(node, ast.Name):
            # 檢查是否為常量
            if node.id in self.ALLOWED_CONSTANTS:
                return self.ALLOWED_CONSTANTS[node.id]

            # 檢查是否為上下文變量
            if node.id in context:
                return context[node.id]

            # 檢查是否為允許的函數
            if node.id in self.ALLOWED_FUNCTIONS:
                return self.ALLOWED_FUNCTIONS[node.id]

            raise ValueError(f"不允許的變量或函數: {node.id}")

        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            op_type = type(node.op)

            if op_type in self.ALLOWED_OPERATORS:
                return self.ALLOWED_OPERATORS[op_type](left, right)
            else:
                raise ValueError(f"不允許的操作符: {op_type}")

        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            op_type = type(node.op)

            if op_type in self.ALLOWED_OPERATORS:
                return self.ALLOWED_OPERATORS[op_type](operand)
            else:
                raise ValueError(f"不允許的一元操作符: {op_type}")

        elif isinstance(node, ast.Compare):
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

        elif isinstance(node, ast.BoolOp):
            op_type = type(node.op)
            values = [self._eval_node(v, context) for v in node.values]

            if op_type == ast.And:
                return all(values)
            elif op_type == ast.Or:
                return any(values)
            else:
                raise ValueError(f"不允許的布爾操作符: {op_type}")

        elif isinstance(node, ast.Call):
            func = self._eval_node(node.func, context)

            if not callable(func):
                raise ValueError(f"不可調用的對象: {func}")

            args = [self._eval_node(arg, context) for arg in node.args]
            kwargs = {
                kw.arg: self._eval_node(kw.value, context)
                for kw in node.keywords
            }

            return func(*args, **kwargs)

        elif isinstance(node, ast.List):
            return [self._eval_node(e, context) for e in node.elts]

        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(e, context) for e in node.elts)

        elif isinstance(node, ast.Set):
            return {self._eval_node(e, context) for e in node.elts}

        elif isinstance(node, ast.Dict):
            keys = [self._eval_node(k, context) for k in node.keys]
            values = [self._eval_node(v, context) for v in node.values]
            return dict(zip(keys, values))

        elif isinstance(node, ast.Subscript):
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

        else:
            raise ValueError(f"不允許的節點類型: {type(node).__name__}")

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
            'abs': abs,
            'round': round,
            'pow': pow,
            'min': min,
            'max': max,
        }

        result = self.evaluate(expression, math_context)

        # 驗證結果類型
        if result.success and not isinstance(result.result, (int, float, bool)):
            return EvalResult(
                success=False,
                error=f"算術表達式必須返回數值，得到: {type(result.result).__name__}",
                expression=expression
            )

        return result


# 全局實例
_evaluator: Optional[SafeEvaluator] = None


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
            logger.error(f"  錯誤: {result.error}")
        logger.info()

    logger.info("=" * 60)
    logger.info("測試完成")