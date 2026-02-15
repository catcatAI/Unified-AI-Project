"""
系统管理器模块

Angela Matrix Annotation:
- V (Vitality): L0-L2 - Basic system lifecycle management
- L (Learning): L0 - Static configuration
- P (Processing): L2-L3 - Async initialization/shutdown
- M (Memory): L0 - Minimal state tracking
"""

# from tests.tools.test_tool_dispatcher_logging import  # Commented out - incomplete import
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SystemManager:
    """系统管理器"""

    def __init__(self):
        self.initialized = False
        self.components: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """初始化系统管理器"""
        logger.info("初始化系统管理器...")
        self.initialized = True
        logger.info("系统管理器初始化完成")

    async def shutdown(self) -> None:
        """关闭系统管理器"""
        logger.info("关闭系统管理器...")
        for name, component in self.components.items():
            if hasattr(component, 'shutdown'):
                try:
                    await component.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down {name}: {e}")
        self.initialized = False
        logger.info("系统管理器已关闭")

    def register_component(self, name: str, component: Any):
        """注册组件"""
        self.components[name] = component
        logger.info(f"Component registered: {name}")

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "initialized": self.initialized,
            "status": "running" if self.initialized else "stopped",
            "components": list(self.components.keys()),
            "component_count": len(self.components)
        }