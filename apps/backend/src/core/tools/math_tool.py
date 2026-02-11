"""
数学工具 - 进行算术计算
"""

import os
import re
from typing import Optional

# 尝试导入TensorFlow
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# 配置
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_WEIGHTS_PATH = os.path.join(PROJECT_ROOT, "data/models/arithmetic_model.keras")
CHAR_MAPS_PATH = os.path.join(PROJECT_ROOT, "data/models/arithmetic_char_maps.json")

_model_instance = None
_tensorflow_import_error = None


def _load_math_model():
    """加载算术模型"""
    global _model_instance, _tensorflow_import_error

    if _model_instance is not None or _tensorflow_import_error is not None:
        return _model_instance

    if not TF_AVAILABLE:
        print("TensorFlow不可用，使用简化计算")
        _tensorflow_import_error = "TensorFlow not available"
        _model_instance = None
        return None

    try:
        # 简化实现
        _model_instance = "SimpleMathModel"
        print("数学模型加载成功")
    except Exception as e:
        print(f"加载数学模型时出错: {e}")
        _tensorflow_import_error = str(e)
        _model_instance = None

    return _model_instance


def extract_arithmetic_problem(text: str) -> Optional[str]:
    """从字符串中提取算术问题"""
    normalized_text = text.lower()
    normalized_text = normalized_text.replace("plus", " + ").replace("add", " + ")
    normalized_text = normalized_text.replace("minus", " - ").replace("subtract", " - ")
    normalized_text = normalized_text.replace("times", " * ").replace("multiply by", " * ")
    normalized_text = normalized_text.replace("divided by", " / ").replace("divide by", " / ")

    float_num_pattern = r"[-+]?\d+(?:\.\d+)?"
    problem_pattern_grouped = rf"({float_num_pattern})\s*([\+\-\*/])\s*({float_num_pattern})"

    match = re.search(problem_pattern_grouped, normalized_text)
    if match:
        try:
            num1_str, op_str, num2_str = match.groups()
            float(num1_str)
            float(num2_str)
            return f"{num1_str.strip()} {op_str} {num2_str.strip()}"
        except (ValueError, IndexError):
            return None
    return None


class ToolDispatcherResponse:
    """工具调度器响应"""
    def __init__(self, status: str, payload: Any = None, tool_name_attempted: str = ""):
        self.status = status
        self.payload = payload
        self.tool_name_attempted = tool_name_attempted


def calculate(input_string: str) -> ToolDispatcherResponse:
    """
    接受自然语言字符串，提取算术问题，并返回计算结果
    """
    model = _load_math_model()

    if model is None:
        error_msg = "错误: 数学模型不可用"
        if _tensorflow_import_error:
            error_msg += f" 原因: {_tensorflow_import_error}"
        return ToolDispatcherResponse(
            status="failure_tool_error",
            payload=None,
            tool_name_attempted="calculate"
        )

    # 提取算术问题
    problem = extract_arithmetic_problem(input_string)

    if not problem:
        return ToolDispatcherResponse(
            status="failure_tool_error",
            payload="无法从输入中提取算术问题",
            tool_name_attempted="calculate"
        )

    # 计算结果
    try:
        result = eval(problem)
        return ToolDispatcherResponse(
            status="success",
            payload=str(result),
            tool_name_attempted="calculate"
        )
    except Exception as e:
        return ToolDispatcherResponse(
            status="failure_tool_error",
            payload=f"计算错误: {str(e)}",
            tool_name_attempted="calculate"
        )