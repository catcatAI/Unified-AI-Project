"""逻辑解析器和评估器"""

from typing import List, Tuple, Any, Optional
import re


class LogicParserEval:
    """基本逻辑表达式的简单解析器和评估器"""

    def __init__(self):
        """初始化"""
        # 定义标记模式
        self.token_patterns = [
            (r'\s+', None),  # 空白
            (r'\(', 'LPAREN'),
            (r'\)', 'RPAREN'),
            (r'\btrue\b', 'TRUE'),
            (r'\bfalse\b', 'FALSE'),
            (r'\bAND\b', 'AND'),
            (r'\bOR\b', 'OR'),
            (r'\bNOT\b', 'NOT')
        ]
        # 创建正则表达式
        self.token_regex = re.compile('|'.join(
            f'(?P<{name}>{pattern})' if name else pattern
            for pattern, name in self.token_patterns
        ))

    def tokenize(self, expression: str) -> List[Tuple[str, str]]:
        """标记化表达式"""
        tokens = []
        for match in self.token_regex.finditer(expression):
            type_name = match.lastgroup
            if type_name:
                tokens.append((type_name, match.group()))
        return tokens

    def evaluate(self, expression: str) -> Optional[bool]:
        """评估表达式"""
        try:
            # 简化实现：使用Python的eval
            py_expr = expression.lower()
            py_expr = py_expr.replace("true", "True")
            py_expr = py_expr.replace("false", "False")
            py_expr = py_expr.replace("and", " and ")
            py_expr = py_expr.replace("or", " or ")
            py_expr = py_expr.replace("not", " not ")

            return eval(py_expr)
        except Exception as e:
            print(f"评估错误: {e}")
            return None