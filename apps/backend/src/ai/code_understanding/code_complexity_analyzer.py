# ANGELA-MATRIX: L0[基础层] [A] L1

import ast
import logging
import math
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CodeComplexityAnalyzer:
    """代码复杂度分析器 - 计算圈复杂度、认知复杂度等指标"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def analyze(self, source_code: str) -> Dict[str, Any]:
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return {"error": "failed to parse source code"}
        cyclomatic = self._calculate_cyclomatic_complexity(tree)
        return {
            "cyclomatic_complexity": cyclomatic,
            "cognitive_complexity": self._calculate_cognitive_complexity(tree),
            "lines_of_code": len(source_code.splitlines()),
        }

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.Assert)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        return complexity

    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        complexity = 0
        nesting = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1 + nesting
                nesting += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
