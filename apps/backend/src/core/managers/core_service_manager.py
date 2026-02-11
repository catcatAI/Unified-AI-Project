"""Core Service Manager - 核心服务管理器

This module provides a centralized system for managing core services with
dynamic loading, dependency management, health monitoring, and hot reload capabilities.
此模块提供了一个集中式的核心服务管理系统, 支持动态加载、依赖管理、健康监控和热重载功能。

Angela Matrix Annotation:
- V (Vitality): L3-L4 - Service lifecycle management and health monitoring
- L (Learning): L2-L3 - Adaptive service loading and dependency resolution
- P (Processing): L3-L4 - Async service operations and monitoring
- M (Memory): L2 - Service state and health history tracking
"""

# from tests.tools.test_tool_dispatcher_logging import  # Commented out - incomplete import
# from enhanced_realtime_monitoring import  # Commented out - incomplete import
import asyncio
import importlib
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Lazy import DependencyManager and ExecutionManager to avoid circular dependencies
# and allow for more flexible testing / mocking.
# These will be imported within CoreServiceManager methods or __init__ if needed.


class ServiceStatus(Enum):
    """服务状态枚举"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    ERROR = "error"
    DEGRADED = "degraded"


class ServiceHealth(Enum):
    """服务健康状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class ServiceConfig:
    """服务配置"""
    name: str
    module_path: str
    class_name: str
    dependencies: List[str] = field(default_factory=list)
    lazy_load: bool = False
    auto_restart: bool = True
    health_check_interval: float = 30.0
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceInfo:
    """服务信息"""
    config: ServiceConfig
    instance: Optional[Any] = None
    status: ServiceStatus = ServiceStatus.UNLOADED
    health: ServiceHealth = ServiceHealth.UNKNOWN
    last_health_check: float = 0.0
    error_message: Optional[str] = None
    load_time: float = 0.0
    dependencies_resolved: bool = False
    health_check_task: Optional[asyncio.Task] = None


class HealthCheckFunction(ABC):
    """健康检查函数抽象基类"""
    @abstractmethod
    async def check_health(self, service_instance: Any) -> ServiceHealth:
        """检查服务健康状态"""
        pass


class CoreServiceManager:
    """核心服务管理器 - 统一管理核心服务的生命周期"""

    def __init__(self, dependency_manager: Optional[Any] = None,
                 execution_manager: Optional[Any] = None) -> None:
        # Lazy import DependencyManager and ExecutionManager
        # from .dependency_manager import DependencyManager
        # from .execution_manager import ExecutionManager

        self._services: Dict[str, ServiceInfo] = {}
        self._service_configs: Dict[str, ServiceConfig] = {}
        self._dependency_manager = dependency_manager  # or DependencyManager()
        self._execution_manager = execution_manager  # or ExecutionManager()
        self._health_check_functions: Dict[str, HealthCheckFunction] = {}
        self._event_handlers: Dict[str, List[Callable]] = {
            'service_loaded': [],
            'service_unloaded': [],
            'service_health_changed': [],
            'service_error': []
        }
        self._lock = asyncio.Lock()
        self._is_running = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._resource_cleanup_callbacks: Dict[str, List[Callable]] = {}  # 资源清理回调

        self._register_default_health_checks()

        logger.info("CoreServiceManager initialized")

    def _register_default_health_checks(self):
        """注册默认的健康检查函数"""
        pass

    def register_service(self, config: ServiceConfig):
        """注册服务配置"""
        self._service_configs[config.name] = config
        self._services[config.name] = ServiceInfo(config=config)
        logger.info(f"Service registered: {config.name}")

    def register_health_check(self, service_name: str, health_check: HealthCheckFunction):
        """注册服务的健康检查函数"""
        self._health_check_functions[service_name] = health_check
        logger.info(f"Health check registered for service: {service_name}")

    def register_event_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type in self._event_handlers:
            self._event_handlers[event_type].append(handler)
            logger.info(f"Event handler registered for {event_type}")
        else:
            logger.warning(f"Unknown event type: {event_type}")

    async def _emit_event(self, event_type: str, service_name: str,
                          data: Optional[Dict[str, Any]] = None):
        """触发事件"""
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(service_name, data)
                    else:
                        handler(service_name, data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")

    async def _resolve_dependencies(self, service_name: str) -> bool:
        """解析服务依赖"""
        service_info = self._services.get(service_name)
        if not service_info:
            return False

        config = service_info.config
        for dep_name in config.dependencies:
            dep_info = self._services.get(dep_name)
            if not dep_info or dep_info.status != ServiceStatus.LOADED:
                logger.warning(f"Dependency {dep_name} not loaded for service {service_name}")
                return False

        service_info.dependencies_resolved = True
        return True

    async def _load_service_instance(self, service_name: str) -> bool:
        """加载服务实例"""
        service_info = self._services.get(service_name)
        if not service_info:
            logger.error(f"Service {service_name} not registered")
            return False

        config = service_info.config
        try:
            service_info.status = ServiceStatus.LOADING
            await self._emit_event('service_loading', service_name)

            if not await self._resolve_dependencies(service_name):
                if config.dependencies:
                    service_info.status = ServiceStatus.ERROR
                    service_info.error_message = "Dependencies not resolved"
                    await self._emit_event('service_error', service_name,
                                          {'error': service_info.error_message})
                    return False

            start_time = time.time()
            module = importlib.import_module(config.module_path)
            service_class = getattr(module, config.class_name)

            kwargs = config.config.copy()
            for dep_name in config.dependencies:
                dep_info = self._services.get(dep_name)
                if dep_info and dep_info.instance:
                    kwargs[dep_name] = dep_info.instance
            service_info.instance = service_class(**kwargs)
            service_info.load_time = time.time() - start_time

            service_info.status = ServiceStatus.LOADED
            service_info.health = ServiceHealth.UNKNOWN
            await self._emit_event('service_loaded', service_name)

            logger.info(f"Service {service_name} loaded successfully in {service_info.load_time:.2f}s")
            return True

        except Exception as e:
            logger.error(f"Failed to load service {service_name}: {e}")
            service_info.status = ServiceStatus.ERROR
            service_info.error_message = str(e)
            await self._emit_event('service_error', service_name, {'error': str(e)})
            return False

    async def load_service(self, service_name: str, force: bool = False) -> bool:
        """加载服务"""
        async with self._lock:
            service_info = self._services.get(service_name)
            if not service_info:
                logger.error(f"Service {service_name} not registered")
                return False

            if service_info.status == ServiceStatus.LOADED and not force:
                logger.info(f"Service {service_name} already loaded")
                return True

            if service_info.status in [ServiceStatus.LOADING, ServiceStatus.UNLOADING]:
                logger.warning(f"Service {service_name} is busy ({service_info.status}), cannot load now")
                return False

            return await self._load_service_instance(service_name)

    async def load_services(self, service_names: List[str], force: bool = False) -> Dict[str, bool]:
        """批量加载服务"""
        results: Dict[str, bool] = {}
        all_services = set(service_names)
        for name in service_names:
            service_info = self._services.get(name)
            if service_info:
                all_services.update(service_info.config.dependencies)

        sorted_services = self._sort_services_by_dependencies(list(all_services))

        for service_name in sorted_services:
            results[service_name] = await self.load_service(service_name, force)

        return results

    def _sort_services_by_dependencies(self, service_names: List[str]) -> List[str]:
        """按依赖关系排序服务"""
        sorted_services: List[str] = []
        visited = set()
        temp_visited = set()

        def visit(name: str):
            if name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {name}")
            if name not in visited:
                temp_visited.add(name)
                service_info = self._services.get(name)
                if service_info:
                    for dep in service_info.config.dependencies:
                        if dep in self._services:
                            visit(dep)
                temp_visited.remove(name)
                visited.add(name)
                sorted_services.append(name)

        for name in service_names:
            if name not in visited:
                try:
                    visit(name)
                except ValueError as e:
                    logger.error(f"Error sorting services: {e}")
                    return service_names

        return sorted_services

    async def unload_service(self, service_name: str, force: bool = False) -> bool:
        """卸载服务"""
        async with self._lock:
            service_info = self._services.get(service_name)
            if not service_info:
                logger.error(f"Service {service_name} not registered")
                return False

            if service_info.status == ServiceStatus.UNLOADED and not force:
                logger.info(f"Service {service_name} already unloaded")
                return True

            dependent_services = self._get_dependent_services(service_name)
            if dependent_services and not force:
                logger.warning(f"Service {service_name} is depended by {dependent_services}, cannot unload")
                return False

            try:
                service_info.status = ServiceStatus.UNLOADING
                await self._emit_event('service_unloading', service_name)

                if service_info.health_check_task:
                    service_info.health_check_task.cancel()
                    try:
                        await service_info.health_check_task
                    except asyncio.CancelledError:
                        pass
                    service_info.health_check_task = None

                if service_name in self._resource_cleanup_callbacks:
                    for callback in self._resource_cleanup_callbacks[service_name]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(service_info.instance)
                            else:
                                callback(service_info.instance)
                        except Exception as e:
                            logger.error(f"Error in resource cleanup callback for {service_name}: {e}")

                if service_info.instance and hasattr(service_info.instance, 'shutdown'):
                    if asyncio.iscoroutinefunction(service_info.instance.shutdown):
                        await service_info.instance.shutdown()
                    else:
                        service_info.instance.shutdown()
                elif service_info.instance and hasattr(service_info.instance, 'close'):
                    if asyncio.iscoroutinefunction(service_info.instance.close):
                        await service_info.instance.close()
                    else:
                        service_info.instance.close()

                service_info.instance = None
                service_info.status = ServiceStatus.UNLOADED
                service_info.health = ServiceHealth.UNKNOWN
                service_info.error_message = None
                service_info.dependencies_resolved = False

                await self._emit_event('service_unloaded', service_name)
                logger.info(f"Service {service_name} unloaded successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to unload service {service_name}: {e}")
                service_info.status = ServiceStatus.ERROR
                service_info.error_message = str(e)
                await self._emit_event('service_error', service_name, {'error': str(e)})
                return False

    def _get_dependent_services(self, service_name: str) -> List[str]:
        """获取依赖指定服务的其他服务"""
        dependent_services: List[str] = []
        for name, service_info in self._services.items():
            if service_name in service_info.config.dependencies:
                dependent_services.append(name)
        return dependent_services

    async def _check_service_health(self, service_name: str):
        """检查服务健康状态"""
        service_info = self._services.get(service_name)
        if not service_info or service_info.status != ServiceStatus.LOADED:
            return

        try:
            health = ServiceHealth.UNHEALTHY
            if service_name in self._health_check_functions:
                health_check = self._health_check_functions[service_name]
                health = await health_check.check_health(service_info.instance)
            else:
                if service_info.instance is not None:
                    health = ServiceHealth.HEALTHY
                else:
                    health = ServiceHealth.UNHEALTHY

            old_health = service_info.health
            service_info.health = health
            service_info.last_health_check = time.time()

            if old_health != health:
                await self._emit_event('service_health_changed', service_name, {
                    'old_health': old_health.value,
                    'new_health': health.value
                })

            if (health != ServiceHealth.HEALTHY and
                service_info.config.auto_restart and
                service_info.status == ServiceStatus.LOADED):
                logger.warning(f"Service {service_name} is unhealthy, attempting restart")
                await self.restart_service(service_name)

        except Exception as e:
            logger.error(f"Error checking health for service {service_name}: {e}")
            service_info.health = ServiceHealth.UNHEALTHY
            service_info.error_message = str(e)

    async def _health_monitoring_loop(self):
        """健康监控循环"""
        while self._is_running:
            try:
                for service_name, service_info in self._services.items():
                    if service_info.status == ServiceStatus.LOADED:
                        if (time.time() - service_info.last_health_check >
                            service_info.config.health_check_interval):
                            await self._check_service_health(service_name)

                await asyncio.sleep(5.0)

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(5.0)

    async def start_health_monitoring(self):
        """启动健康监控"""
        if not self._is_running:
            self._is_running = True
            self._monitoring_task = asyncio.create_task(self._health_monitoring_loop())
            logger.info("Health monitoring started")

    async def stop_health_monitoring(self):
        """停止健康监控"""
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        logger.info("Health monitoring stopped")

    async def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        logger.info(f"Restarting service {service_name}")
        if not await self.unload_service(service_name, force=True):
            return False
        return await self.load_service(service_name, force=True)

    async def reload_service(self, service_name: str) -> bool:
        """重新加载服务(卸载后重新加载)"""
        logger.info(f"Reloading service {service_name}")
        if not await self.unload_service(service_name, force=True):
            return False
        return await self.load_service(service_name, force=True)

    def get_service(self, service_name: str) -> Optional[Any]:
        """获取服务实例"""
        service_info = self._services.get(service_name)
        if service_info and service_info.status == ServiceStatus.LOADED:
            return service_info.instance
        return None

    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """获取服务状态"""
        service_info = self._services.get(service_name)
        return service_info.status if service_info else None

    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """获取服务健康状态"""
        service_info = self._services.get(service_name)
        return service_info.health if service_info else None

    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务的状态信息"""
        status_info: Dict[str, Dict[str, Any]] = {}
        for name, service_info in self._services.items():
            status_info[name] = {
                'status': service_info.status.value,
                'health': service_info.health.value,
                'error_message': service_info.error_message,
                'load_time': service_info.load_time,
                'last_health_check': service_info.last_health_check
            }
        return status_info

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_health_monitoring()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop_health_monitoring()
        for service_name in list(self._services.keys()):
            await self.unload_service(service_name, force=True)


# 全局核心服务管理器实例
_global_core_service_manager: Optional[CoreServiceManager] = None


def get_core_service_manager() -> CoreServiceManager:
    """获取全局核心服务管理器实例"""
    global _global_core_service_manager
    if _global_core_service_manager is None:
        _global_core_service_manager = CoreServiceManager()
    return _global_core_service_manager


# 示例健康检查函数
class DefaultHealthCheck(HealthCheckFunction):
    """示例健康检查函数"""
    async def check_health(self, service_instance: Any) -> ServiceHealth:
        """检查服务健康状态"""
        try:
            if hasattr(service_instance, 'is_healthy'):
                if asyncio.iscoroutinefunction(service_instance.is_healthy):
                    is_healthy = await service_instance.is_healthy()
                else:
                    is_healthy = service_instance.is_healthy()

                return ServiceHealth.HEALTHY if is_healthy else ServiceHealth.UNHEALTHY
            else:
                return ServiceHealth.HEALTHY
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return ServiceHealth.UNHEALTHY


if __name__ == "__main__":
    async def main() -> None:
        manager = CoreServiceManager()

        config = ServiceConfig(
            name="example_service",
            module_path="core_services",
            class_name="MultiLLMService",
            dependencies=[],
            lazy_load=False,
            auto_restart=True
        )

        manager.register_service(config)
        logger.info("Service registered")

        status = manager.get_all_services_status()
        logger.info(f"Service status: {status}")

        logger.info("CoreServiceManager basic test completed")

    asyncio.run(main())