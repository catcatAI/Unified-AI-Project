"""
Safe calculator tool for mathematical expressions
"""
import ast
import operator as op
import logging

logger = logging.getLogger(__name__)

# Supported operators
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.BitXor: op.xor,
    ast.USub: op.neg
}


def eval_expr(expr):
    """
    Safely evaluates a mathematical expression.
    
    Args:
        expr: String mathematical expression
        
    Returns:
        Result of the calculation
    """
    try:
        return eval_(ast.parse(expr, mode='eval').body)
    except Exception as e:
        logger.error(f"Failed to evaluate expression '{expr}': {e}")
        raise ValueError(f"Invalid expression: {expr}")


def eval_(node):
    """
    Recursively evaluate AST node
    """
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.Constant):  # Python 3.8+
        return node.value
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(f"Unsupported node type: {type(node)}")


def calculate(expression):
    """
    Calculates the result of a mathematical expression.

    Args:
        expression: The mathematical expression to be calculated.

    Returns:
        The result of the calculation.
    """
    return eval_expr(expression)


class CalculatorTool:
    """Calculator tool for agents"""
    
    def __init__(self):
        self.name = "calculator"
        self.description = "Performs mathematical calculations"
    
    def execute(self, expression: str):
        """Execute calculation"""
        try:
            result = calculate(expression)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
