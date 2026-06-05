"""统一模型加载器"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class UnifiedModelLoader:
    """统一模型加载器 - 提供统一的 AI 模型加载接口"""

    _instances: Dict[str, Any] = {}

    @classmethod
    def load_model(cls, model_name: str, model_path: Optional[str] = None, **kwargs: Any) -> Any:
        """加载指定名称的模型"""
        if model_name in cls._instances:
            return cls._instances[model_name]
        logger.info(f"[UnifiedModelLoader] Loading model: {model_name} from {model_path or 'default'}")
        instance = object()
        cls._instances[model_name] = instance
        return instance

    @classmethod
    def unload_model(cls, model_name: str) -> bool:
        """卸载指定模型"""
        if model_name in cls._instances:
            del cls._instances[model_name]
            logger.info(f"[UnifiedModelLoader] Unloaded model: {model_name}")
            return True
        return False

    @classmethod
    def get_loaded_models(cls) -> Dict[str, Any]:
        """获取所有已加载的模型"""
        return dict(cls._instances)

