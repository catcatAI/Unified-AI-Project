"""统一模型加载器"""

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class UnifiedModelLoader:
    """统一模型加载器 - 提供统一的 AI 模型加载接口"""

    _instances: Dict[str, Any] = {}
    _loaders: Dict[str, Callable[..., Any]] = {}

    @classmethod
    def register_loader(cls, model_name: str, loader: Callable[..., Any]) -> None:
        """为指定模型注册自定义加载函数"""
        cls._loaders[model_name] = loader
        logger.info(f"[UnifiedModelLoader] Registered custom loader for: {model_name}")

    @classmethod
    def load_model(
        cls, model_name: str, model_path: Optional[str] = None, **kwargs: Any
    ) -> Any:
        """加载指定名称的模型

        优先使用已注册的自定义加载器；否则返回带元数据的模型句柄。
        """
        if model_name in cls._instances:
            return cls._instances[model_name]

        loader = cls._loaders.get(model_name)
        if loader is not None:
            logger.info(
                f"[UnifiedModelLoader] Loading model via custom loader: {model_name}"
            )
            instance = loader(model_path=model_path, **kwargs)
        else:
            logger.info(
                f"[UnifiedModelLoader] Loading model: {model_name} from "
                f"{model_path or 'default'}"
            )
            instance = cls._create_model_handle(model_name, model_path, kwargs)

        cls._instances[model_name] = instance
        return instance

    @staticmethod
    def _create_model_handle(
        model_name: str, model_path: Optional[str], kwargs: Dict[str, Any]
    ) -> Any:
        """创建带元数据的模型句柄（无自定义加载器时的回退）"""
        handle = type("LoadedModel", (), {})()
        handle.model_name = model_name
        handle.model_path = model_path
        handle.parameters = dict(kwargs)
        handle.loaded = True
        return handle

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
