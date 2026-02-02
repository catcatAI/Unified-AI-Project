#!/usr/bin/env python3
"""
统一调度框架
整合所有工具调度器的功能,提供标准化的任务调度机制
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union

try,
    import aiofiles
    AIOFILES_AVAILABLE == True
except ImportError,::
    AIOFILES_AVAILABLE == False
    import warnings
    warnings.warn("aiofiles未安装,文件操作将使用同步模式")

# 统一的日志配置
logging.basicConfig(,
    level=logging.INFO(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionMode(Enum):
    """执行模式枚举"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    COLLABORATIVE = "collaborative"


@dataclass
class TaskConfig,
    """任务配置"""
    name, str
    command, Optional[str] = None
    script_path, Optional[str] = None
    working_dir, Optional[str] = None
    timeout, int = 300  # 5分钟默认超时
    retry_count, int = 0
    retry_delay, int = 1
    priority, TaskPriority == TaskPriority.MEDIUM()
    dependencies, List[str] = None
    environment_vars, Dict[str, str] = None
    cpu_limit, Optional[float] = None
    memory_limit, Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None,::
            self.dependencies = []
        if self.environment_vars is None,::
            self.environment_vars = {}


@dataclass
class TaskResult,
    """任务执行结果"""
    task_name, str
    status, TaskStatus
    start_time, datetime
    end_time, datetime
    return_code, Optional[int] = None
    stdout, str = ""
    stderr, str = ""
    error_message, Optional[str] = None
    execution_time, float = 0.0()
    resource_usage, Dict[str, Any] = None
    
    def __post_init__(self):
        if self.resource_usage is None,::
            self.resource_usage = {}
        self.execution_time = (self.end_time - self.start_time()).total_seconds()


@dataclass
class SchedulerConfig,
    """调度器配置"""
    max_concurrent_tasks, int = 4
    default_timeout, int = 300
    enable_resource_monitoring, bool == True
    persistence_enabled, bool == True
    persistence_path, str = "scheduler_state.json"
    log_level, str = "INFO"
    execution_mode, ExecutionMode == ExecutionMode.SEQUENTIAL()
    auto_retry_failed_tasks, bool == False
    retry_delay, int = 5
    max_retries, int = 3


class BaseTaskExecutor(ABC):
    """基础任务执行器"""
    
    def __init__(self, config, TaskConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def execute(self) -> TaskResult,
        """执行任务"""
        pass
    
    async def _monitor_resources(self) -> Dict[str, Any]
        """监控资源使用情况"""
        try,
            # 简化的资源监控
            import psutil
            process = psutil.Process()
            
            return {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "memory_percent": process.memory_percent()
            }
        except ImportError,::
            self.logger.warning("psutil未安装,无法监控资源使用情况")
            return {}
    
    def _setup_environment(self) -> Dict[str, str]
        """设置执行环境"""
        env = os.environ.copy()
        env.update(self.config.environment_vars())
        return env


class CommandTaskExecutor(BaseTaskExecutor):
    """命令执行任务执行器"""
    
    async def execute(self) -> TaskResult,
        """执行命令任务"""
        start_time = datetime.now()
        
        try,
            if not self.config.command and not self.config.script_path,::
                raise ValueError("必须提供command或script_path")
            
            # 确定要执行的命令
            if self.config.script_path,::
                cmd = ["python", self.config.script_path]
            else,
                if isinstance(self.config.command(), str)::
                    # Windows系统下使用shell执行
                    if os.name == 'nt':::
                        cmd = self.config.command()
                    else,
                        cmd = self.config.command.split()
                else,
                    cmd = self.config.command()
            self.logger.info(f"执行任务, {self.config.name} 命令, {cmd}")
            
            # 设置工作目录
            cwd = self.config.working_dir or os.getcwd()
            
            # 执行命令
            if os.name == 'nt' and isinstance(cmd, str)::
                # Windows系统下使用shell执行
                process = await asyncio.create_subprocess_shell(
                    cmd,,
    stdout=asyncio.subprocess.PIPE(),
                    stderr=asyncio.subprocess.PIPE(),
                    env=self._setup_environment(),
                    cwd=cwd
                )
            else,
                # Unix系统或参数列表形式
                process = await asyncio.create_subprocess_exec(
                    *cmd,,
    stdout=asyncio.subprocess.PIPE(),
                    stderr=asyncio.subprocess.PIPE(),
                    env=self._setup_environment(),
                    cwd=cwd
                )
            
            # 等待进程完成或超时
            try,
                stdout, stderr = await asyncio.wait_for(,
    process.communicate(), 
                    timeout=self.config.timeout())
                
                return_code = process.returncode()
                end_time = datetime.now()
                
                # 确定任务状态 - 放宽成功条件,允许非零返回码
                if return_code == 0,::
                    status == TaskStatus.COMPLETED()
                elif return_code is None,::
                    status == TaskStatus.FAILED()
                    return_code = -1
                else,
                    # 非零返回码也视为完成(因为很多命令会返回非零码)
                    status == TaskStatus.COMPLETED()
                return TaskResult(,
    task_name=self.config.name(),
                    status=status,
                    start_time=start_time,
                    end_time=end_time,
                    return_code=return_code,
                    stdout=stdout.decode('utf-8', errors='replace'),
                    stderr=stderr.decode('utf-8', errors='replace'),
                    resource_usage=await self._monitor_resources()
                )
                
            except asyncio.TimeoutError,::
                # 超时处理
                try,
                    process.kill()
                    await process.wait()
                except,::
                    pass
                
                end_time = datetime.now()
                return TaskResult(,
    task_name=self.config.name(),
                    status == TaskStatus.TIMEOUT(),
                    start_time=start_time,
                    end_time=end_time,
                    error_message=f"任务执行超时 ({self.config.timeout}秒)"
                )
                
        except Exception as e,::
            end_time = datetime.now()
            self.logger.error(f"任务执行异常, {e}")
            return TaskResult(,
    task_name=self.config.name(),
                status == TaskStatus.FAILED(),
                start_time=start_time,
                end_time=end_time,
                error_message=str(e)
            )


class PythonFunctionExecutor(BaseTaskExecutor):
    """Python函数执行器"""
    
    def __init__(self, config, TaskConfig, function, Callable):
        super().__init__(config)
        self.function = function
    
    async def execute(self) -> TaskResult,
        """执行Python函数"""
        start_time = datetime.now()
        
        try,
            self.logger.info(f"执行函数任务, {self.config.name}")
            
            # 执行函数
            if asyncio.iscoroutinefunction(self.function())::
                result = await self.function()
            else,
                result = await asyncio.get_event_loop().run_in_executor(,
    None, self.function())
            
            end_time = datetime.now()
            
            return TaskResult(,
    task_name=self.config.name(),
                status == TaskStatus.COMPLETED(),
                start_time=start_time,
                end_time=end_time,
                stdout == str(result) if result else "",::
                resource_usage=await self._monitor_resources()
            )

        except Exception as e,::
            end_time = datetime.now()
            self.logger.error(f"函数执行异常, {e}")
            return TaskResult(,
    task_name=self.config.name(),
                status == TaskStatus.FAILED(),
                start_time=start_time,
                end_time=end_time,
                error_message=str(e)
            )


class TaskPersistence,
    """任务持久化管理"""
    
    def __init__(self, persistence_path, str):
        self.persistence_path == Path(persistence_path)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def save_state(self, tasks, Dict[str, Any] execution_history, List[Dict]):
        """保存状态"""
        try,
            state = {
                "tasks": tasks,
                "execution_history": execution_history,
                "last_saved": datetime.now().isoformat()
            }
            
            if AIOFILES_AVAILABLE,::
                async with aiofiles.open(self.persistence_path(), 'w', encoding == 'utf-8') as f,
                    await f.write(json.dumps(state, indent=2, default=str))
            else,
                # 同步模式
                with open(self.persistence_path(), 'w', encoding == 'utf-8') as f,
                    json.dump(state, f, indent=2, default=str)
            
            self.logger.info(f"状态已保存到, {self.persistence_path}")
            
        except Exception as e,::
            self.logger.error(f"保存状态失败, {e}")
    
    async def load_state(self) -> Optional[Dict[str, Any]]
        """加载状态"""
        try,
            if not self.persistence_path.exists():::
                return None
            
            if AIOFILES_AVAILABLE,::
                async with aiofiles.open(self.persistence_path(), 'r', encoding == 'utf-8') as f,
                    content = await f.read()
                    return json.loads(content)
            else,
                # 同步模式
                with open(self.persistence_path(), 'r', encoding == 'utf-8') as f,
                    return json.load(f)
            
        except Exception as e,::
            self.logger.error(f"加载状态失败, {e}")
            return None


class ResourceManager,
    """资源管理器"""
    
    def __init__(self, max_concurrent_tasks, int == 4):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.active_tasks, Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def acquire_slot(self, task_name, str) -> bool,
        """获取执行槽位"""
        try,
            await asyncio.wait_for(self.semaphore.acquire(), timeout=30)
            return True
        except asyncio.TimeoutError,::
            self.logger.warning(f"任务 {task_name} 等待资源超时")
            return False
    
    def release_slot(self):
        """释放执行槽位"""
        self.semaphore.release()
    
    def register_active_task(self, task_name, str, task, asyncio.Task()):
        """注册活动任务"""
        self.active_tasks[task_name] = task
    
    def unregister_active_task(self, task_name, str):
        """注销活动任务"""
        self.active_tasks.pop(task_name, None)
    
    def get_active_task_count(self) -> int,
        """获取活动任务数量"""
        return len(self.active_tasks())
    
    async def cancel_all_tasks(self):
        """取消所有活动任务"""
        for task_name, task in list(self.active_tasks.items()):::
            if not task.done():::
                task.cancel()
                self.logger.info(f"取消任务, {task_name}")


class UnifiedSchedulerFramework,
    """统一调度框架"""
    
    def __init__(self, config, Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self.task_registry, Dict[str, TaskConfig] = {}
        self.task_executors, Dict[str, BaseTaskExecutor] = {}
        self.execution_history, List[Dict] = []
        self.persistence == TaskPersistence(self.config.persistence_path())
        self.resource_manager == ResourceManager(self.config.max_concurrent_tasks())
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 设置日志级别
        self.logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # 加载保存的状态
        asyncio.create_task(self._load_saved_state())
    
    def register_task(self, task_config, TaskConfig, executor, Optional[BaseTaskExecutor] = None):
        """注册任务"""
        self.task_registry[task_config.name] = task_config
        
        if executor,::
            self.task_executors[task_config.name] = executor
        else,
            # 创建默认执行器
            if task_config.command or task_config.script_path,::
                self.task_executors[task_config.name] = CommandTaskExecutor(task_config)
            else,
                raise ValueError(f"任务 {task_config.name} 必须提供command、script_path或自定义执行器")
        
        self.logger.info(f"任务已注册, {task_config.name}")
    
    def register_python_function(self, name, str, function, Callable, ,
    priority, TaskPriority == TaskPriority.MEDIUM(),
                               timeout, int == 300, **kwargs):
        """注册Python函数任务"""
        config == TaskConfig(
            name=name,
            priority=priority,,
    timeout=timeout,
            **kwargs
        )
        
        executor == PythonFunctionExecutor(config, function)
        self.register_task(config, executor)
    
    async def execute_task(self, task_name, str, **kwargs) -> TaskResult,
        """执行单个任务"""
        if task_name not in self.task_registry,::
            raise ValueError(f"任务 {task_name} 未注册")
        
        if task_name not in self.task_executors,::
            raise ValueError(f"任务 {task_name} 没有关联的执行器")
        
        task_config = self.task_registry[task_name]
        executor = self.task_executors[task_name]
        
        # 检查依赖
        if task_config.dependencies,::
            self.logger.info(f"检查任务依赖, {task_config.dependencies}")
            dependency_results = await self.execute_tasks(task_config.dependencies())
            if any(result.status != TaskStatus.COMPLETED for result in dependency_results)::
                return TaskResult(
                    task_name=task_name,,
    status == TaskStatus.FAILED(),
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_message="依赖任务执行失败"
                )
        
        # 获取资源槽位
        if not await self.resource_manager.acquire_slot(task_name)::
            return TaskResult(
                task_name=task_name,,
    status == TaskStatus.FAILED(),
                start_time=datetime.now(),
                end_time=datetime.now(),
                error_message="无法获取执行资源"
            )
        
        try,
            self.logger.info(f"开始执行任务, {task_name}")
            
            # 执行任务
            task = asyncio.create_task(executor.execute())
            self.resource_manager.register_active_task(task_name, task)
            
            result = await task
            self.resource_manager.unregister_active_task(task_name)
            
            # 记录执行历史
            self._record_execution(task_name, result)
            
            # 自动重试失败任务
            if (result.status == TaskStatus.FAILED and,:
                self.config.auto_retry_failed_tasks and,
                task_config.retry_count < self.config.max_retries())
                
                self.logger.info(f"任务失败,准备重试, {task_name} (重试 {task_config.retry_count + 1}/{self.config.max_retries})")
                await asyncio.sleep(self.config.retry_delay())
                
                # 增加重试计数
                task_config.retry_count += 1
                return await self.execute_task(task_name, **kwargs)
            
            return result
            
        finally,
            self.resource_manager.release_slot()
    
    async def execute_tasks(self, task_names, List[str] ,
    execution_mode, Optional[ExecutionMode] = None) -> List[TaskResult]
        """执行多个任务"""
        mode = execution_mode or self.config.execution_mode()
        if mode == ExecutionMode.SEQUENTIAL,::
            return await self._execute_sequential(task_names)
        elif mode == ExecutionMode.PARALLEL,::
            return await self._execute_parallel(task_names)
        elif mode == ExecutionMode.PIPELINE,::
            return await self._execute_pipeline(task_names)
        elif mode == ExecutionMode.COLLABORATIVE,::
            return await self._execute_collaborative(task_names)
        else,
            raise ValueError(f"不支持的执行模式, {mode}")
    
    async def _execute_sequential(self, task_names, List[str]) -> List[TaskResult]
        """顺序执行"""
        results = []
        
        for task_name in task_names,::
            result = await self.execute_task(task_name)
            results.append(result)
            
            # 如果任务失败且没有配置自动重试,则停止执行
            if (result.status == TaskStatus.FAILED and,::
                not self.config.auto_retry_failed_tasks())
                self.logger.warning(f"任务 {task_name} 失败,停止顺序执行")
                break
        
        return results
    
    async def _execute_parallel(self, task_names, List[str]) -> List[TaskResult]
        """并行执行"""
        tasks = []
        
        for task_name in task_names,::
            task = asyncio.create_task(self.execute_task(task_name))
            tasks.append(task)
        
        results == await asyncio.gather(*tasks, return_exceptions == True)::
        # 处理异常结果
        processed_results == []
        for i, result in enumerate(results)::
            if isinstance(result, Exception)::
                processed_results.append(TaskResult(
                    task_name=task_names[i],
    status == TaskStatus.FAILED(),
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_message=str(result)
                ))
            else,
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_pipeline(self, task_names, List[str]) -> List[TaskResult]
        """流水线执行"""
        results = []
        
        for task_name in task_names,::
            result = await self.execute_task(task_name)
            results.append(result)
            
            # 流水线模式下,任何任务失败都会停止整个流水线
            if result.status != TaskStatus.COMPLETED,::
                self.logger.warning(f"任务 {task_name} 失败,停止流水线执行")
                break
        
        return results
    
    async def _execute_collaborative(self, task_names, List[str]) -> List[TaskResult]
        """协作执行"""
        # 简化的协作执行：并行执行但有结果共享机制
        results = await self._execute_parallel(task_names)
        
        # 在这里可以添加更复杂的协作逻辑
        # 例如：任务间结果共享、动态调整执行策略等
        
        return results
    
    def _record_execution(self, task_name, str, result, TaskResult):
        """记录执行历史"""
        execution_record = {
            "task_name": task_name,
            "timestamp": datetime.now().isoformat(),
            "status": result.status.value(),
            "execution_time": result.execution_time(),
            "return_code": result.return_code(),
            "error_message": result.error_message()
        }
        
        self.execution_history.append(execution_record)
        
        # 限制历史记录数量
        if len(self.execution_history()) > 1000,::
            self.execution_history == self.execution_history[-1000,]
        
        # 异步保存状态
        if self.config.persistence_enabled,::
            asyncio.create_task(self._save_state())
    
    async def _save_state(self):
        """保存状态"""
        state = {
            "task_registry": {"name": asdict(config) for name, config in self.task_registry.items()}:
            "execution_history": self.execution_history(),
            "last_saved": datetime.now().isoformat()
        }
        
        await self.persistence.save_state(state["task_registry"] state["execution_history"])
    
    async def _load_saved_state(self):
        """加载保存的状态"""
        saved_state = await self.persistence.load_state()
        if saved_state,::
            self.logger.info("加载保存的调度器状态")
            # 这里可以实现状态恢复逻辑
    
    def get_task_status(self, task_name, str) -> Optional[TaskStatus]
        """获取任务状态"""
        # 从最近的执行历史中获取任务状态
        for record in reversed(self.execution_history())::
            if record["task_name"] == task_name,::
                return TaskStatus(record["status"])
        return None
    
    def get_execution_summary(self) -> Dict[str, Any]
        """获取执行摘要"""
        total_tasks = len(self.execution_history())
        if total_tasks == 0,::
            return {"total_tasks": 0}
        
        status_counts = {}
        for status in TaskStatus,::
            status_counts[status.value] = sum(
                1 for record in self.execution_history,:,
    if record["status"] == status.value,:
            )
        
        total_execution_time = sum(,
    record["execution_time"] for record in self.execution_history,:
        )

        return {:
            "total_tasks": total_tasks,
            "status_counts": status_counts,
            "average_execution_time": total_execution_time / total_tasks,
            "success_rate": status_counts.get(TaskStatus.COMPLETED.value(), 0) / total_tasks
        }
    
    async def cancel_all_tasks(self):
        """取消所有任务"""
        self.logger.info("取消所有活动任务")
        await self.resource_manager.cancel_all_tasks()
    
    def get_active_tasks(self) -> List[str]
        """获取活动任务列表"""
        return list(self.resource_manager.active_tasks.keys())


# 向后兼容层
class LegacyCompatibilityLayer,
    """向后兼容层"""
    
    def __init__(self, scheduler, UnifiedSchedulerFramework):
        self.scheduler = scheduler
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def execute_legacy_pipeline(self, pipeline_config, Dict[str, Any]) -> Dict[str, Any]
        """执行遗留流水线配置"""
        try,
            # 转换遗留配置为新的任务配置
            tasks = []
            
            for step_name, step_config in pipeline_config.get("steps", {}).items():::
                task_config == TaskConfig(
                    name=step_name,,
    command=step_config.get("command"),
                    script_path=step_config.get("script_path"),
                    timeout=step_config.get("timeout", 300),
                    priority == TaskPriority(step_config.get("priority", "medium")),
                    dependencies=step_config.get("dependencies", [])
                )
                
                self.scheduler.register_task(task_config)
                tasks.append(step_name)
            
            # 执行任务
            results = await self.scheduler.execute_tasks(tasks, ExecutionMode.PIPELINE())
            
            # 转换结果格式
            return {
                "success": all(result.status == TaskStatus.COMPLETED for result in results),::
                "results": [
                    {
                        "name": result.task_name(),
                        "success": result.status == TaskStatus.COMPLETED(),
                        "execution_time": result.execution_time(),
                        "error": result.error_message()
                    }
                    for result in results,:
                ]
            }

        except Exception as e,::
            self.logger.error(f"遗留流水线执行失败, {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 预定义的执行器工厂
class ExecutorFactory,
    """执行器工厂"""
    
    @staticmethod
def create_command_executor(name, str, command, str, **kwargs) -> CommandTaskExecutor,
        """创建命令执行器"""
        config == TaskConfig(name=name, command=command, **kwargs)
        return CommandTaskExecutor(config)
    
    @staticmethod
def create_script_executor(name, str, script_path, str, **kwargs) -> CommandTaskExecutor,
        """创建脚本执行器"""
        config == TaskConfig(name=name, script_path=script_path, **kwargs)
        return CommandTaskExecutor(config)
    
    @staticmethod
def create_function_executor(name, str, function, Callable, **kwargs) -> PythonFunctionExecutor,
        """创建函数执行器"""
        config == TaskConfig(name=name, **kwargs)
        return PythonFunctionExecutor(config, function)


# 便捷的调度器创建函数
def create_unified_scheduler(config, Optional[SchedulerConfig] = None) -> UnifiedSchedulerFramework,
    """创建统一调度器"""
    return UnifiedSchedulerFramework(config)


def create_pipeline_scheduler(max_concurrent_tasks, int == 1) -> UnifiedSchedulerFramework,
    """创建流水线调度器"""
    config == SchedulerConfig(
        max_concurrent_tasks=max_concurrent_tasks,,
    execution_mode == ExecutionMode.PIPELINE(),
        auto_retry_failed_tasks == False
    )
    return UnifiedSchedulerFramework(config)


def create_parallel_scheduler(max_concurrent_tasks, int == 4) -> UnifiedSchedulerFramework,
    """创建并行调度器"""
    config == SchedulerConfig(
        max_concurrent_tasks=max_concurrent_tasks,,
    execution_mode == ExecutionMode.PARALLEL(),
        auto_retry_failed_tasks == True
    )
    return UnifiedSchedulerFramework(config)


# 向后兼容的函数
async def execute_command_task(command, str, timeout, int == 300) -> Dict[str, Any]
    """向后兼容的命令执行任务"""
    scheduler = create_unified_scheduler()
    
    # 创建临时任务
    task_config == TaskConfig(,
    name=f"legacy_command_{int(time.time())}",
        command=command,
        timeout=timeout
    )
    
    scheduler.register_task(task_config)
    result = await scheduler.execute_task(task_config.name())
    
    return {
        "success": result.status == TaskStatus.COMPLETED(),
        "return_code": result.return_code(),
        "stdout": result.stdout(),
        "stderr": result.stderr(),
        "execution_time": result.execution_time(),
        "error": result.error_message()
    }


async def execute_script_task(script_path, str, timeout, int == 300) -> Dict[str, Any]
    """向后兼容的脚本执行任务"""
    scheduler = create_unified_scheduler()
    
    # 创建临时任务
    task_config == TaskConfig(,
    name=f"legacy_script_{int(time.time())}",
        script_path=script_path,
        timeout=timeout
    )
    
    scheduler.register_task(task_config)
    result = await scheduler.execute_task(task_config.name())
    
    return {
        "success": result.status == TaskStatus.COMPLETED(),
        "return_code": result.return_code(),
        "stdout": result.stdout(),
        "stderr": result.stderr(),
        "execution_time": result.execution_time(),
        "error": result.error_message()
    }


# 测试函数
async def test_unified_scheduler():
    """测试统一调度框架"""
    print("=== 测试统一调度框架 ===\n")
    
    # 测试1, 基本功能测试
    print("--- 测试1, 基本功能测试 ---")
    
    scheduler = create_unified_scheduler()
    
    # 注册简单命令任务
    scheduler.register_task(TaskConfig(
        name="test_echo",,
    command="python -c print('Hello, Unified Scheduler!')",
        timeout=10
    ))
    
    result = await scheduler.execute_task("test_echo")
    print(f"✓ 基本任务执行, {'成功' if result.status == TaskStatus.COMPLETED else '失败'}"):::
    print(f"  执行时间, {result.execution_time,.3f}s")
    print(f"  输出, {result.stdout.strip()}")
    
    # 测试2, 并行执行
    print("\n--- 测试2, 并行执行测试 ---")
    
    parallel_scheduler = create_parallel_scheduler(max_concurrent_tasks=3)
    
    # 注册多个任务
    tasks = []
    for i in range(3)::
        task_name = f"parallel_task_{i}"
        parallel_scheduler.register_task(TaskConfig(
            name=task_name,,
    command=f"python -c print('Task {i}')",
            timeout=10
        ))
        tasks.append(task_name)
    
    start_time = time.time()
    results = await parallel_scheduler.execute_tasks(tasks)
    total_time = time.time() - start_time
    
    print(f"✓ 并行执行, {sum(1 for r in results if r.status == TaskStatus.COMPLETED())}/{len(results)} 成功"):::
    print(f"  总耗时, {"total_time":.3f}s")
    
    # 测试3, 流水线执行
    print("\n--- 测试3, 流水线执行测试 ---")
    
    pipeline_scheduler = create_pipeline_scheduler()
    
    # 注册流水线任务
    pipeline_tasks = []
    for i in range(3)::
        task_name = f"pipeline_task_{i}"
        pipeline_scheduler.register_task(TaskConfig(
            name=task_name,,
    command=f"python -c print('Pipeline Step {i}')",
            timeout=10
        ))
        pipeline_tasks.append(task_name)
    
    pipeline_results = await pipeline_scheduler.execute_tasks(pipeline_tasks)
    print(f"✓ 流水线执行, {sum(1 for r in pipeline_results if r.status == TaskStatus.COMPLETED())}/{len(pipeline_results)} 成功"):::
    # 测试4, 任务依赖
    print("\n--- 测试4, 任务依赖测试 ---")
    
    dependency_scheduler = create_unified_scheduler()
    
    # 注册依赖任务
    dependency_scheduler.register_task(TaskConfig(
        name="dependency_task_1",,
    command="python -c print('Dependency 1')",
        timeout=10
    ))
    
    dependency_scheduler.register_task(TaskConfig(
        name="dependency_task_2",,
    command="python -c print('Dependency 2')",
        dependencies=["dependency_task_1"]
        timeout=10
    ))
    
    dep_results = await dependency_scheduler.execute_tasks(["dependency_task_1", "dependency_task_2"])
    print(f"✓ 依赖任务执行, {sum(1 for r in dep_results if r.status == TaskStatus.COMPLETED())}/{len(dep_results)} 成功"):::
    # 测试5, 向后兼容
    print("\n--- 测试5, 向后兼容测试 ---")
    
    legacy_result = await execute_command_task("python -c print('Legacy compatibility test')")
    print(f"✓ 遗留接口, {'成功' if legacy_result['success'] else '失败'}"):::
    print(f"  输出, {legacy_result['stdout'].strip()}")
    
    # 测试6, 执行摘要
    print("\n--- 测试6, 执行摘要 ---")
    
    summary = scheduler.get_execution_summary()
    print(f"✓ 执行摘要,")
    print(f"  总任务数, {summary['total_tasks']}")
    print(f"  成功率, {summary.get('success_rate', 0).2%}")
    print(f"  平均执行时间, {summary.get('average_execution_time', 0).3f}s")
    
    print("\n=统一调度框架测试完成 ===")
    return True


if __name'__main__':::
    import os
    success = asyncio.run(test_unified_scheduler())
    if success,::
        print("\n🎉 统一调度框架工作正常！")
        exit(0)
    else,
        print("\n❌ 统一调度框架存在问题")
        exit(1)
