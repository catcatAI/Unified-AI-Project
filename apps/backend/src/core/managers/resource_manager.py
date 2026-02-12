# Angela Matrix: Resource Management - α=β=0.6, γ=0.4, δ=0.2 (V×L×P×M)
"""Resource Manager - 资源管理器

This module provides resource management capabilities for services,
including connection pooling, cache management, and file handle management.

此模块为服务提供资源管理功能, 包括连接池、缓存管理和文件句柄管理。
"""

import asyncio
import logging
# from tests.tools.test_tool_dispatcher_logging import
# import weakref
from typing import Dict, List, Optional, Any, Callable
from contextlib import asynccontextmanager

# from .core_service_manager import

logger: Any = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ResourceManager:
    """资源管理器"""

    def __init__(self, service_manager) -> None:
        self.service_manager = service_manager
        self._resources: Dict[str, List[Any]] = {}  # 服务资源列表
        self._resource_cleanup_funcs: Dict[str, List[Callable]] = {}  # 资源清理函数
        self._locks: Dict[str, asyncio.Lock] = {}  # 服务锁

        # 注册到服务管理器的资源清理回调
        self._register_cleanup_callbacks()

    def _register_cleanup_callbacks(self):
        """注册资源清理回调到服务管理器"""
        # 为服务管理器注册通用的资源清理回调
        pass  # 在具体服务中注册

    def register_service_resource(self, service_name: str, resource: Any, cleanup_func: Optional[Callable] = None):
        """注册服务资源"""
        if service_name not in self._resources:
            self._resources[service_name] = []
            self._resource_cleanup_funcs[service_name] = []
            self._locks[service_name] = asyncio.Lock()
        self._resources[service_name].append(resource)

        if cleanup_func:
            self._resource_cleanup_funcs[service_name].append(cleanup_func)

        logger.info(f"Resource registered for service {service_name}")

    async def cleanup_service_resources(self, service_name: str):
        """清理服务资源"""
        async with self._locks.get(service_name, asyncio.Lock()):
            if service_name in self._resources:
                resources = self._resources[service_name]
                cleanup_funcs = self._resource_cleanup_funcs.get(service_name, [])

                # 执行清理函数
                for resource in resources:
                    for cleanup_func in cleanup_funcs:
                        try:
                            if asyncio.iscoroutinefunction(cleanup_func):
                                await cleanup_func(resource)
                            else:
                                cleanup_func(resource)
                        except Exception as e:
                            logger.error(f"Error cleaning up resource for {service_name}: {e}")

                # 清空资源列表
                self._resources[service_name].clear()
                self._resource_cleanup_funcs[service_name].clear()

                logger.info(f"Resources cleaned up for service {service_name}")

    async def cleanup_all_resources(self):
        """清理所有资源"""
        logger.info("Cleaning up all resources")

        for service_name in list(self._resources.keys()):
            await self.cleanup_service_resources(service_name)

        logger.info("All resources cleaned up")


class ConnectionPool:
    """连接池"""

    def __init__(self, max_connections: int = 10) -> None:
        self.max_connections = max_connections
        self._connections: List[Any] = []
        self._in_use: Dict[Any, bool] = {}
        self._lock = asyncio.Lock()

    async def get_connection(self) -> Optional[Any]:
        """获取连接"""
        async with self._lock:
            # 尝试从现有连接中获取空闲连接
            for conn, in_use in self._in_use.items():
                if not in_use:
                    self._in_use[conn] = True
                    return conn

            # 如果没有空闲连接且未达到最大连接数, 创建新连接
            if len(self._connections) < self.max_connections:
                new_conn = await self._create_connection()
                self._connections.append(new_conn)
                self._in_use[new_conn] = True
                return new_conn

            # 如果达到最大连接数, 等待空闲连接
            return None

    async def _create_connection(self) -> Any:
        """创建新连接(需要子类实现)"""
        raise NotImplementedError("Subclasses must implement _create_connection")

    async def release_connection(self, connection: Any):
        """释放连接"""
        async with self._lock:
            if connection in self._in_use:
                self._in_use[connection] = False

    async def close_all_connections(self):
        """关闭所有连接"""
        async with self._lock:
            for conn in self._connections:
                try:
                    if hasattr(conn, 'close'):
                        if asyncio.iscoroutinefunction(conn.close):
                            await conn.close()
                        else:
                            conn.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")

            self._connections.clear()
            self._in_use.clear()


class DatabaseConnectionPool(ConnectionPool):
    """数据库连接池"""

    def __init__(self, max_connections: int = 10, db_url: str = "") -> None:
        super().__init__(max_connections)
        self.db_url = db_url

    async def _create_connection(self) -> Any:
        """创建数据库连接"""
        # 这里应该实现实际的数据库连接创建逻辑
        # 例如使用asyncpg, aiomysql等
        logger.info(f"Creating database connection to {self.db_url}")
        return f"db_connection_{len(self._connections)}"


class CacheManager:
    """缓存管理器"""

    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key in self._cache:
                self._access_times[key] = asyncio.get_event_loop().time()
                return self._cache[key]
            return None

    async def set(self, key: str, value: Any):
        """设置缓存值"""
        async with self._lock:
            self._cache[key] = value
            self._access_times[key] = asyncio.get_event_loop().time()

            # 如果缓存大小超过限制, 清理最旧的条目
            if len(self._cache) > self.max_size:
                await self._cleanup_old_entries()

    async def _cleanup_old_entries(self):
        """清理旧的缓存条目"""
        # 按访问时间排序, 删除最旧的条目
        sorted_items = sorted(self._access_times.items(), key=lambda x: x[1])
        items_to_remove = len(self._cache) - self.max_size + 10  # 多清理一些

        for i in range(min(items_to_remove, len(sorted_items))):
            key, _ = sorted_items[i]
            del self._cache[key]
            del self._access_times[key]

    async def delete(self, key: str):
        """删除缓存条目"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]

    async def clear(self):
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        async with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "access_times": dict(self._access_times)
            }


class FileManager:
    """文件管理器"""

    def __init__(self) -> None:
        self._open_files: Dict[str, Any] = {}
        self._file_locks: Dict[str, asyncio.Lock] = {}

    @asynccontextmanager
    async def open_file(self, filepath: str, mode: str = 'r'):
        """打开文件的上下文管理器"""
        if filepath not in self._file_locks:
            self._file_locks[filepath] = asyncio.Lock()

        async with self._file_locks[filepath]:
            try:
                # 打开文件
                file_handle = open(filepath, mode)
                self._open_files[filepath] = file_handle

                yield file_handle

            finally:
                # 关闭文件
                if filepath in self._open_files:
                    file_handle = self._open_files[filepath]
                    file_handle.close()
                    del self._open_files[filepath]


# 示例：为LLM服务注册资源清理回调
async def cleanup_llm_service_resources(service_instance: Any):
    """清理LLM服务资源"""
    logger.info("Cleaning up LLM service resources")

    # 清理连接池
    if hasattr(service_instance, '_connection_pool'):
        await service_instance._connection_pool.close_all_connections()
    # 清理缓存
    if hasattr(service_instance, '_cache'):
        await service_instance._cache.clear()
    # 其他资源清理...


# 示例：为HSP连接器注册资源清理回调
async def cleanup_hsp_connector_resources(service_instance: Any):
    """清理HSP连接器资源"""
    logger.info("Cleaning up HSP connector resources")

    # 断开连接
    if hasattr(service_instance, 'disconnect'):
        if asyncio.iscoroutinefunction(service_instance.disconnect):
            await service_instance.disconnect()
        else:
            service_instance.disconnect()
    # 清理订阅
    if hasattr(service_instance, '_subscriptions'):
        service_instance._subscriptions.clear()


if __name__ == "__main__":
    # 简单测试
    async def main() -> None:
        logger.info("Resource manager test started")

        # 创建连接池
        db_pool = DatabaseConnectionPool(max_connections=5, db_url="postgresql://localhost/test")

        # 获取连接
        conn1 = await db_pool.get_connection()
        conn2 = await db_pool.get_connection()
        logger.info(f"Got connections: {conn1} {conn2}")

        # 释放连接
        await db_pool.release_connection(conn1)
        await db_pool.release_connection(conn2)

        # 关闭所有连接
        await db_pool.close_all_connections()

        # 创建缓存管理器
        cache = CacheManager(max_size=100)

        # 设置缓存
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        # 获取缓存
        value1 = await cache.get("key1")
        logger.info(f"Cache value for key1: {value1}")

        # 获取统计信息
        stats = await cache.get_stats()
        logger.info(f"Cache stats: {stats}")

        logger.info("Resource manager test completed")

    asyncio.run(main())