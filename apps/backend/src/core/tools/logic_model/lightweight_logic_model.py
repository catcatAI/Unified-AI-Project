"""
轻量级逻辑模型 - 使用规则基础评估简单逻辑命题
"""

from typing import Dict, Any, Optional
import logging
logger = logging.getLogger(__name__)


class LightweightLogicModel:
    """
    轻量级逻辑模型，无需TensorFlow等重型ML框架
    使用规则基础评估和模式匹配
    """

    def __init__(self) -> None:
        # 逻辑运算符
        self.operators = {
            'AND': 'and',
            'OR': 'or',
            'NOT': 'not',
            '&': 'and',
            '|': 'or',
            '!': 'not'
        }

        # 布尔值
        self.boolean_values = {
            'true': True,
            'false': False,
            'True': True,
            'False': False,
            '1': True,
            '0': False
        }

    def evaluate(self, proposition: str) -> Optional[bool]:
        """
        评估逻辑命题

        Args:
            proposition: 逻辑命题字符串

        Returns:
            评估结果
        """
        if not proposition:
            return None

        try:
            # 转换为Python表达式
            py_expr = self._convert_to_python(proposition)
            result = eval(py_expr, {"__builtins__": {}}, {})
            return bool(result)
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return None


    def _convert_to_python(self, proposition: str) -> str:
        """转换为Python表达式"""
        expr = proposition

        # 替换布尔值
        for key, value in self.boolean_values.items():
            expr = expr.replace(key, str(value))

        # 替换运算符
        for op, py_op in self.operators.items():
            expr = expr.replace(op, py_op)

        return expr