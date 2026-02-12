"""
轻量级数学模型
"""

from typing import Optional
import logging
logger = logging.getLogger(__name__)


class LightweightMathModel:
    """
    轻量级数学模型，执行基本算术运算
    使用简单模式匹配和规则基础评估
    """

    def __init__(self) -> None:
        """初始化"""
        self.operations = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y if y != 0 else float('inf'),
            '**': lambda x, y: x ** y,
            '%': lambda x, y: x % y if y != 0 else 0,
        }

    def evaluate_expression(self, expression: str) -> Optional[float]:
        """
        评估简单算术表达式

        Args:
            expression: 包含算术表达式的字符串

        Returns:
            计算结果
        """
        if not expression:
            return None

        try:
            result = eval(expression, {"__builtins__": {}})
            return float(result)
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return None


    def add(self, x: float, y: float) -> float:
        """加法"""
        return x + y

    def subtract(self, x: float, y: float) -> float:
        """减法"""
        return x - y

    def multiply(self, x: float, y: float) -> float:
        """乘法"""
        return x * y

    def divide(self, x: float, y: float) -> Optional[float]:
        """除法"""
        if y == 0:
            return None
        return x / y