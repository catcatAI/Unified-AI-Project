#!/usr/bin/env python3
"""
Angela AI - Resource Pool Manager
资源池管理器

管理数据库连接、WebSocket 连接、文件句柄等资源，提高资源利用效率。
"""

import time
import threading
import queue
from typing import Dict, List, Optional, Callable, TypeVar, Generic, Any
from dataclasses import dataclass, field
from contextlib import contextmanager
from enum import Enum
import weakref
import logging
logger = logging.getLogger(__name__)


T = TypeVar('T')


class PoolState(Enum):
    """资源池状态"""
    IDLE = "idle"
    RUNNING = "running"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass
class PoolConfig:
    """资源池配置"""
    min_size: int = 1  # 最小资源数量
    max_size: int = 10  # 最大资源数量
    idle_timeout: float = 300.0  # 空闲超时 (秒)
    max_lifetime: float = 3600.0  # 最大生命周期 (秒)
    acquire_timeout: float = 10.0  # 获取超时 (秒)
    validation_interval: float = 60.0  # 验证间隔 (秒)


@dataclass
class PoolStats:
    """资源池统计"""
    created: int = 0  # 已创建的资源数量
    destroyed: int = 0  # 已销毁的资源数量
    acquired: int = 0  # 已获取的资源数量
    released: int = 0  # 已释放的资源数量
    failed: int = 0  # 失败的获取次数
    current_size: int = 0  # 当前资源数量
    active_size: int = 0  # 活跃资源数量
    idle_size: int = 0  # 空闲资源数量


class PooledResource(Generic[T]):
    """池化资源包装器"""
    
    def __init__(self, resource: T, pool: 'ResourcePool[T]'):
        self.resource = resource
        self.pool = pool
        self.created_at = time.time()
        self.last_used = time.time()
        self.in_use = False
        self._lock = threading.Lock()
    
    def acquire(self) -> bool:
        """获取资源"""
        with self._lock:
            if not self.in_use:
                self.in_use = True
                self.last_used = time.time()
                return True
            return False
    
    def release(self) -> bool:
        """释放资源"""
        with self._lock:
            if self.in_use:
                self.in_use = False
                self.last_used = time.time()
                return True
            return False
    
    def is_expired(self, max_lifetime: float) -> bool:
        """检查是否过期"""
        age = time.time() - self.created_at
        return age > max_lifetime
    
    def is_idle(self, idle_timeout: float) -> bool:
        """检查是否空闲超时"""
        idle_time = time.time() - self.last_used
        return not self.in_use and idle_time > idle_timeout
    
    def __enter__(self):
        """上下文管理器入口"""
        return self.resource
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.pool.release(self)


class ResourcePool(Generic[T]):
    """通用资源池"""
    
    def __init__(
        self,
        factory: Callable[[], T],
        config: Optional[PoolConfig] = None,
        validator: Optional[Callable[[T], bool]] = None,
        closer: Optional[Callable[[T], None]] = None
    ):
        self.factory = factory
        self.config = config or PoolConfig()
        self.validator = validator or (lambda x: True)
        self.closer = closer or (lambda x: None)
        
        self.state = PoolState.IDLE
        self._resources: List[PooledResource[T]] = []
        self._wait_queue: queue.Queue = queue.Queue()
        self._lock = threading.RLock()
        self._stats = PoolStats()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        
        # 启动清理线程
        self._start_cleanup_thread()
    
    def start(self) -> None:
        """启动资源池"""
        with self._lock:
            if self.state == PoolState.RUNNING:
                return
            
            self.state = PoolState.RUNNING
            self._running.set()
            
            # 预创建最小数量的资源
            for _ in range(self.config.min_size):
                self._create_resource()
    
    def stop(self) -> None:
        """停止资源池"""
        with self._lock:
            if self.state == PoolState.CLOSED:
                return
            
            self.state = PoolState.CLOSING
            self._running.clear()
        
        # 等待清理线程结束
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5.0)
        
        # 关闭所有资源
        with self._lock:
            for resource in self._resources:
                self._destroy_resource(resource)
            self._resources.clear()
            self.state = PoolState.CLOSED
    
    def acquire(self, timeout: Optional[float] = None) -> PooledResource[T]:
        """获取资源"""
        timeout = timeout or self.config.acquire_timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self._lock:
                # 检查资源池状态
                if self.state != PoolState.RUNNING:
                    raise RuntimeError(f"资源池未运行: {self.state}")
                
                # 尝试获取空闲资源
                for resource in self._resources:
                    if resource.acquire():
                        self._stats.acquired += 1
                        self._stats.active_size += 1
                        self._stats.idle_size -= 1
                        return resource
                
                # 检查是否可以创建新资源
                if len(self._resources) < self.config.max_size:
                    resource = self._create_resource()
                    resource.acquire()
                    self._stats.acquired += 1
                    self._stats.active_size += 1
                    return resource
            
            # 等待资源释放
            try:
                self._wait_queue.get(timeout=0.1)
            except queue.Empty:
                continue
        
        # 超时
        self._stats.failed += 1
        raise TimeoutError(f"获取资源超时: {timeout} 秒")
    
    def release(self, resource: PooledResource[T]) -> None:
        """释放资源"""
        with self._lock:
            if resource.release():
                self._stats.released += 1
                self._stats.active_size -= 1
                self._stats.idle_size += 1
                
                # 通知等待的获取者
                self._wait_queue.put_nowait(None)
    
    @contextmanager
    def get_resource(self, timeout: Optional[float] = None):
        """获取资源的上下文管理器"""
        resource = self.acquire(timeout)
        try:
            yield resource.resource
        finally:
            self.release(resource)
    
    def _create_resource(self) -> PooledResource[T]:
        """创建新资源"""
        try:
            resource = self.factory()
            pooled = PooledResource(resource, self)
            self._resources.append(pooled)
            self._stats.created += 1
            self._stats.current_size += 1
            self._stats.idle_size += 1
            return pooled
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            self._stats.failed += 1

            raise RuntimeError(f"创建资源失败: {e}")
    
    def _destroy_resource(self, resource: PooledResource[T]) -> None:
        """销毁资源"""
        try:
            self.closer(resource.resource)
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            pass
# 忽略关闭错误
        
        self._resources.remove(resource)
        self._stats.destroyed += 1
        self._stats.current_size -= 1
    
    def _cleanup_expired_resources(self) -> None:
        """清理过期资源"""
        with self._lock:
            if self.state != PoolState.RUNNING:
                return
            
            to_remove = []
            for resource in self._resources:
                if not resource.in_use:
                    # 检查过期和空闲超时
                    if (resource.is_expired(self.config.max_lifetime) or
                        resource.is_idle(self.config.idle_timeout)):
                        # 确保不低于最小数量
                        if len(self._resources) - len(to_remove) > self.config.min_size:
                            to_remove.append(resource)
            
            for resource in to_remove:
                self._destroy_resource(resource)
    
    def _validate_resources(self) -> None:
        """验证资源有效性"""
        with self._lock:
            if self.state != PoolState.RUNNING:
                return
            
            to_remove = []
            for resource in self._resources:
                if not resource.in_use and not self.validator(resource.resource):
                    to_remove.append(resource)
            
            for resource in to_remove:
                self._destroy_resource(resource)
    
    def _start_cleanup_thread(self) -> None:
        """启动清理线程"""
        def cleanup_loop():
            while self._running.is_set():
                try:
                    self._cleanup_expired_resources()
                    self._validate_resources()
                    time.sleep(self.config.validation_interval)
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    pass

        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def get_stats(self) -> PoolStats:
        """获取资源池统计"""
        with self._lock:
            return PoolStats(
                created=self._stats.created,
                destroyed=self._stats.destroyed,
                acquired=self._stats.acquired,
                released=self._stats.released,
                failed=self._stats.failed,
                current_size=len(self._resources),
                active_size=self._stats.active_size,
                idle_size=self._stats.idle_size
            )
    
    def resize(self, new_min: int, new_max: int) -> None:
        """调整资源池大小"""
        with self._lock:
            if new_min < 0 or new_max < new_min:
                raise ValueError("无效的资源池大小配置")
            
            self.config.min_size = new_min
            self.config.max_size = new_max
            
            # 调整当前资源数量
            while len(self._resources) < new_min:
                self._create_resource()
            
            while len(self._resources) > new_max:
                # 移除空闲资源
                for resource in self._resources:
                    if not resource.in_use:
                        self._destroy_resource(resource)
                        break
                else:
                    break  # 没有空闲资源


# 专用资源池实现

class ConnectionPool(ResourcePool[Any]):
    """连接池（数据库、WebSocket 等）"""
    
    def __init__(
        self,
        factory: Callable[[], Any],
        config: Optional[PoolConfig] = None,
        test_query: Optional[Callable[[Any], bool]] = None
    ):
        self.test_query = test_query
        validator = test_query if test_query else (lambda x: True)
        closer = lambda x: x.close() if hasattr(x, 'close') else None
        super().__init__(factory, config, validator, closer)


class ThreadPool:
    """线程池"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._workers: List[threading.Thread] = []
        self._task_queue: queue.Queue = queue.Queue()
        self._running = threading.Event()
        self._stats = PoolStats()
    
    def start(self) -> None:
        """启动线程池"""
        if self._running.is_set():
            return
        
        self._running.set()
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._workers.append(worker)
    
    def stop(self) -> None:
        """停止线程池"""
        self._running.clear()
        for worker in self._workers:
            worker.join(timeout=1.0)
        self._workers.clear()
    
    def submit(self, func: Callable, *args, **kwargs) -> Any:
        """提交任务"""
        future = Future()
        self._task_queue.put((func, args, kwargs, future))
        return future
    
    def _worker_loop(self) -> None:
        """工作线程循环"""
        while self._running.is_set():
            try:
                func, args, kwargs, future = self._task_queue.get(timeout=0.1)
                try:
                    result = func(*args, **kwargs)
                    future.set_result(result)
                    self._stats.completed += 1
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    future.set_exception(e)

                    self._stats.failed += 1
            except queue.Empty:
                continue
    
    def get_stats(self) -> PoolStats:
        """获取统计信息"""
        return PoolStats(
            active_size=self._task_queue.qsize(),
            current_size=len(self._workers)
        )


class Future:
    """简单 Future 实现"""
    
    def __init__(self):
        self._result = None
        self._exception = None
        self._ready = threading.Event()
    
    def set_result(self, result: Any) -> None:
        """设置结果"""
        self._result = result
        self._ready.set()
    
    def set_exception(self, exception: Exception) -> None:
        """设置异常"""
        self._exception = exception
        self._ready.set()
    
    def get(self, timeout: Optional[float] = None) -> Any:
        """获取结果"""
        if not self._ready.wait(timeout=timeout):
            raise TimeoutError("获取结果超时")
        
        if self._exception:
            raise self._exception
        
        return self._result
    
    def ready(self) -> bool:
        """检查是否就绪"""
        return self._ready.is_set()


# 全局资源池管理器
class ResourceManager:
    """全局资源管理器"""
    
    def __init__(self):
        self._pools: Dict[str, ResourcePool] = {}
        self._lock = threading.Lock()
    
    def register_pool(self, name: str, pool: ResourcePool) -> None:
        """注册资源池"""
        with self._lock:
            self._pools[name] = pool
            pool.start()
    
    def unregister_pool(self, name: str) -> None:
        """注销资源池"""
        with self._lock:
            if name in self._pools:
                self._pools[name].stop()
                del self._pools[name]
    
    def get_pool(self, name: str) -> Optional[ResourcePool]:
        """获取资源池"""
        with self._lock:
            return self._pools.get(name)
    
    def get_all_stats(self) -> Dict[str, PoolStats]:
        """获取所有资源池的统计"""
        with self._lock:
            return {name: pool.get_stats() for name, pool in self._pools.items()}
    
    def stop_all(self) -> None:
        """停止所有资源池"""
        with self._lock:
            for pool in self._pools.values():
                pool.stop()
            self._pools.clear()


# 全局资源管理器实例
_resource_manager = ResourceManager()


def get_resource_manager() -> ResourceManager:
    """获取全局资源管理器"""
    return _resource_manager


if __name__ == "__main__":
    # 测试资源池
    pool = ResourcePool(
        factory=lambda: {"id": id, "data": "test"},
        config=PoolConfig(min_size=2, max_size=5)
    )
    
    pool.start()
    
    # 获取资源
    with pool.get_resource() as resource:
        logger.info(f"获取资源: {resource}")
        time.sleep(1)
    
    # 获取统计
    stats = pool.get_stats()
    logger.info(f"资源池统计: {stats}")
    
    pool.stop()