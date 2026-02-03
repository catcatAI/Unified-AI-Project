import ast
from typing import List, Dict, Any

def calculate_complexity(node: ast.AST) -> float:
    """
    Calculate code complexity score based on AST node.
    """
    complexity = 0

    # Count control flow statements
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 0.5
        elif isinstance(child, (ast.And, ast.Or)):
            complexity += 0.2
        elif isinstance(child, ast.FunctionDef):
            complexity += 2  # Functions add complexity
        elif isinstance(child, ast.ClassDef):
            complexity += 3  # Classes add more complexity
    return complexity
