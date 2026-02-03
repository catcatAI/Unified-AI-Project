import operator
import ast
import re
from typing import Union, Dict, Callable, Type, List

def extract_arithmetic_problem(text: str) -> str:
    """
    Extracts a simple arithmetic problem from a given text.
    For example, "What is 5 + 3?" -> "5 + 3"
    This is a placeholder for a more sophisticated NLP-based extraction.
    """
    # Very basic extraction: looks for numbers and basic operators
    match = re.search(r'(\d+\s*[\+\-\*\/]\s*\d+)', text)
    if match:
        return match.group(1)
    return ""

def calculate(expression: str) -> Union[int, float]:
    """
    Calculates the result of a simple arithmetic expression.
    Supports basic operations: +, -, *, /, ** (power), % (modulo).
    """
    # Define supported operators
    bin_operators: Dict[Type[ast.operator], Callable[[Union[int, float], Union[int, float]], Union[int, float]]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }

    unary_operators: Dict[Type[ast.unaryop], Callable[[Union[int, float]], Union[int, float]]] = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def eval_node(node) -> Union[int, float]:
        if isinstance(node, ast.Constant):  # Python 3.8+
            value = node.value
            if isinstance(value, (int, float)):
                return value
            else:
                raise ValueError(f"Unsupported constant value type: {type(value)}")
        elif isinstance(node, ast.Num):  # Python < 3.8
            # Ensure return value is int or float type
            n_value = node.n
            if isinstance(n_value, complex):
                # If complex, return real part
                return float(n_value.real)
            elif isinstance(n_value, (int, float)):
                return n_value
            else:
                raise ValueError(f"Unsupported number type: {type(n_value)}")
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            op_func = bin_operators.get(type(node.op))
            if op_func:
                return op_func(left, right)
            else:
                raise ValueError(f"Unsupported binary operation: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):
            operand = eval_node(node.operand)
            op_func = unary_operators.get(type(node.op))
            if op_func:
                return op_func(operand)
            else:
                raise ValueError(f"Unsupported unary operation: {type(node.op)}")
        else:
            raise ValueError(f"Unsupported operation: {type(node)}")

    try:
        tree = ast.parse(expression, mode='eval')
        return eval_node(tree.body)
    except Exception as e:
        raise ValueError(f"Cannot evaluate expression: {expression} error: {str(e)}")

if __name__ == "__main__":
    print("--- Math Tool Example Usage ---")

    # Test cases
    expressions = [
        "5 + 3",
        "10 - 4",
        "6 * 7",
        "100 / 5",
        "2 ** 3",
        "10 % 3",
        "(5 + 3) * 2",
        "10 / (2 + 3)",
        "-5 + 2",
        "2 + -5",
        "10 / 0" # Should raise ZeroDivisionError
    ]

    for expr in expressions:
        try:
            result = calculate(expr)
            print(f"Expression: '{expr}' = {result}")
        except ValueError as e:
            print(f"Expression: '{expr}' - Error: {e}")
        except ZeroDivisionError:
            print(f"Expression: '{expr}' - Error: Division by zero")

    print("\n--- Extraction Example ---")
    text_query = "Please calculate 15 * 4 for me."
    extracted_problem = extract_arithmetic_problem(text_query)
    if extracted_problem:
        try:
            result = calculate(extracted_problem)
            print(f"From text: '{text_query}', extracted: '{extracted_problem}', result: {result}")
        except ValueError as e:
            print(f"From text: '{text_query}', extracted: '{extracted_problem}', error: {e}")
    else:
        print(f"No arithmetic problem extracted from: '{text_query}'")

    print("\nMath Tool script execution finished.")