"""统一模型加载器"""

import os
from typing import Dict, Any, Optional

_loaded_models: Dict[str, Any] = {}
_model_load_errors: Dict[str, str] = {}


def _get_project_root():
    """获取项目根目录"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_math_model():
    """加载算术模型"""
    model_name = "math_model"
    if model_name in _loaded_models or model_name in _model_load_errors:
        return _loaded_models.get(model_name)

    try:
        # 简化实现：返回占位符
        _loaded_models[model_name] = {"name": "math_model", "loaded": True}
        return _loaded_models[model_name]
    except Exception as e:
        _model_load_errors[model_name] = str(e)
        return None


def load_logic_model():
    """加载逻辑模型"""
    model_name = "logic_model"
    if model_name in _loaded_models or model_name in _model_load_errors:
        return _loaded_models.get(model_name)

    try:
        # 简化实现：返回占位符
        _loaded_models[model_name] = {"name": "logic_model", "loaded": True}
        return _loaded_models[model_name]
    except Exception as e:
        _model_load_errors[model_name] = str(e)
        return None


def get_model_load_errors() -> Dict[str, str]:
    """获取模型加载错误"""
    return _model_load_errors.copy()