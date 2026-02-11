"""
逻辑解析器评估器
"""

from typing import List, Tuple, Any, Optional


class LogicParserEval:
    """
    简单的逻辑表达式解析器和评估器
    支持 AND, OR, NOT, true, false 和括号
    """

    def __init__(self) -> None:
        """初始化"""
        pass

    def tokenize(self, expression: str) -> List[str]:
        """将表达式标记化"""
        tokens = []
        i = 0

        while i < len(expression):
            if expression[i] in ' \t\n':
                i += 1
                continue

            if expression[i] in '()':
                tokens.append(expression[i])
                i += 1
                continue

            # 读取关键字或值
            j = i
            while j < len(expression) and expression[j] not in '() \t\n':
                j += 1

            token = expression[i:j].strip()
            if token:
                tokens.append(token)
            i = j

        return tokens

    def evaluate(self, expression: str) -> Optional[bool]:
        """评估逻辑表达式"""
        try:
            # 转换为Python表达式
            py_expr = self._convert_to_python(expression)
            result = eval(py_expr, {"__builtins__": {}})
            return bool(result)
        except Exception:
            return None

    def _convert_to_python(self, expression: str) -> str:
        """转换为Python表达式"""
        py_expr = expression.lower()

        # 替换布尔值
        py_expr = py_expr.replace("true", "True")
        py_expr = py_expr.replace("false", "False")

        # 替换运算符
        py_expr = py_expr.replace(" and ", " and ")
        py_expr = py_expr.replace(" or ", " or ")
        py_expr = py_expr.replace(" not ", " not ")

        return py_expr