"""
Calculator Tool - Safe mathematical expression evaluator
安全数学表达式计算器
"""

import ast
import operator
from typing import Any
import logging

logger = logging.getLogger(__name__)

operators = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitXor: operator.xor,
    ast.USub: operator.neg,
}


def eval_expr(expr: str) -> Any:
    """
    Safely evaluates a mathematical expression.
    安全地计算数学表达式。
    """
    try:
        node = ast.parse(expr, mode="eval")
        return _eval(node.body)
    except Exception as e:
        logger.error(f"Error in {__name__}: {e}", exc_info=True)
        return None


def _eval(node: ast.AST) -> Any:
    """Evaluate AST node / 评估AST节点"""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.BinOp):
        op_func = operators.get(type(node.op))
        if op_func:
            return op_func(_eval(node.left), _eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub):
            return -_eval(node.operand)
    elif isinstance(node, ast.Name):
        return globals().get(node.id, 0)
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            args = [_eval(a) for a in node.args]
            if func_name == "abs":
                return abs(args[0] if args else 0)
            elif func_name == "round":
                return round(args[0] if args else 0)
            elif func_name == "max":
                return max(args) if args else 0
            elif func_name == "min":
                return min(args) if args else 0
    return None


def calculate(expression: str) -> str:
    """Calculate expression / 计算表达式"""
    result = eval_expr(expression)
    if result is not None:
        return str(result)
    return "Error: Invalid expression"


def demo():
    """Demo / 演示"""
    expressions = [
        "2 + 2",
        "10 - 5 * 2",
        "(10 - 5) * 2",
        "2 ** 10",
        "abs(-5)",
        "round(3.14159, 2)",
    ]

    logger.info("🧮 Calculator Tool Demo")
    logger.info("=" * 40)

    for expr in expressions:
        result = calculate(expr)
        logger.info(f"  {expr} = {result}")


if __name__ == "__main__":
    demo()
