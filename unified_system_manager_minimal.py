#!/usr/bin/env python3
"""
简化统一系统管理器 - 最小化版本
避免语法错误的依赖，专注于核心功能
"""

import os
import sys
import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemCategory(Enum):
    """系统类别"""
    AI = "ai"                    # AI系统
    MEMORY = "memory"           # 记忆系统
    REPAIR = "repair"           # 修复系统
    CONTEXT = "context"         # 上下文系统
    TRAINING = "training"       # 训练系统
    MONITORING = "monitoring"   # 监控系统
    UTILITY = "utility"         # 工具系统

class SystemStatus(Enum):
    """系统状态"""
    ACTIVE = "active"           # 活跃状态
    INACTIVE = "inactive"       # 非活跃状态
    ERROR = "error"             # 错误状态
    MAINTENANCE = "maintenance" # 维护状态
    ARCHIVED = "archived"       # 已归档

@dataclass
class TransferBlock:
    """传输块 - 用于系统间上下文同步的智能信息载体"""
    block_id: str
    source_system: str
    target_system: str
    content_type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    priority: int = 1
    compression_level: str = "medium"
    encryption_enabled: bool = True
    ham_compatibility: Dict[str, Any] = field(default_factory=dict)
    activation_commands: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'block_id': self.block_id,
            'source_system': self.source_system,
            'target_system': self.target_system,
            'content_type': self.content_type,
            'content': self.content,
            'metadata': self.metadata,
            'priority': self.priority,
            'compression_level': self.compression_level,
            'encryption_enabled': self.encryption_enabled,
            'ham_compatibility': self.ham_compatibility,
            'activation_commands': self.activation_commands,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransferBlock':
        """从字典创建传输块"""
        return cls(
            block_id=data['block_id'],
            source_system=data['source_system'],
            target_system=data['target_system'],
            content_type=data['content_type'],
            content=data['content'],
            metadata=data['metadata'],
            priority=data.get('priority', 1),
            compression_level=data.get('compression_level', 'medium'),
            encryption_enabled=data.get('encryption_enabled', True),
            ham_compatibility=data.get('ham_compatibility', {}),
            activation_commands=data.get('activation_commands', []),
            timestamp=datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp']
        )

@dataclass
class SystemConfig:
    """系统配置"""
    auto_start: bool = True
    enable_monitoring: bool = True
    enable_backup: bool = True
    max_concurrent_operations: int = 8
    health_check_interval: int = 60  # 秒
    context_sync_enabled: bool = True
    repair_fallback_enabled: bool = True
    sync_batch_size: int = 10
    sync_interval: int = 5  # 秒
    
@dataclass
class SystemMetrics:
    """系统指标"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_response_time: float = 0.0
    last_health_check: Optional[datetime] = None
    system_health_score: float = 1.0
    active_components: List[str] = field(default_factory=list)
    sync_operations: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0

class MinimalContextManager:
    """最小化上下文管理器"""
    
    def __init__(self):
        self.contexts: Dict[str, Dict[str, Any]] = {}
        logger.info("最小化上下文管理器初始化完成")
    
    def create_context(self, context_type: str, initial_content: Optional[Dict[str, Any]] = None) -> str:
        """创建上下文"""
        context_id = f"ctx_{int(time.time() * 1000)}"
        self.contexts[context_id] = {
            'context_id': context_id,
            'context_type': context_type,
            'content': initial_content or {},
            'metadata': {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        logger.info(f"创建上下文: {context_id}")
        return context_id
    
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """获取上下文"""
        return self.contexts.get(context_id)
    
    def update_context(self, context_id: str, updates: Dict[str, Any]) -> bool:
        """更新上下文"""
        if context_id in self.contexts:
            self.contexts[context_id]['content'].update(updates)
            self.contexts[context_id]['updated_at'] = datetime.now().isoformat()
            logger.info(f"更新上下文: {context_id}")
            return True
        return False
    
    def delete_context(self, context_id: str) -> bool:
        """删除上下文"""
        if context_id in self.contexts:
            del self.contexts[context_id]
            logger.info(f"删除上下文: {context_id}")
            return True
        return False

class UnifiedSystemManagerMinimal:
    """简化统一系统管理器 - 最小化版本"""
    
    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or SystemConfig()
        self.start_time = datetime.now()
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_operations)
        
        # 系统注册表
        self.systems: Dict[str, Any] = {}
        self.system_configs: Dict[str, Dict[str, Any]] = {}
        self.system_metrics: Dict[str, SystemMetrics] = {}
        self.system_status: Dict[str, SystemStatus] = {}
        
        # 上下文同步相关
        self.transfer_blocks: List[TransferBlock] = []
        self.sync_queue: asyncio.Queue = asyncio.Queue()
        self.sync_tasks: List[asyncio.Task] = []
        self.sync_history: List[Dict[str, Any]] = []
        
        # 监控和健康检查
        self.health_check_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        # 初始化系统
        self._initialize_core_systems()
        
        logger.info("🚀 简化统一系统管理器初始化完成")
    
    def _initialize_core_systems(self):
        """初始化核心系统"""
        logger.info("初始化核心系统...")
        
        # 1. 自动修复系统
        self._register_system(
            "auto_repair",
            SystemCategory.REPAIR,
            self._init_auto_repair_system()
        )
        
        # 2. 简化上下文管理系统
        self._register_system(
            "context_manager",
            SystemCategory.CONTEXT,
            MinimalContextManager()
        )
        
        # 3. 模拟其他系统
        self._register_system(
            "memory_manager",
            SystemCategory.MEMORY,
            self._create_mock_system("memory_manager")
        )
        
        self._register_system(
            "ai_agents",
            SystemCategory.AI,
            self._create_mock_system("ai_agents")
        )
        
        self._register_system(
            "training",
            SystemCategory.TRAINING,
            self._create_mock_system("training")
        )
        
        logger.info("✅ 核心系统初始化完成")
    
    def _register_system(self, name: str, category: SystemCategory, system_instance: Any):
        """注册系统"""
        self.systems[name] = system_instance
        self.system_configs[name] = {
            "category": category.value,
            "registered_at": datetime.now().isoformat(),
            "enabled": True
        }
        self.system_metrics[name] = SystemMetrics()
        self.system_status[name] = SystemStatus.ACTIVE
        logger.info(f"系统注册完成: {name} ({category.value})")
    
    def _init_auto_repair_system(self) -> Any:
        """初始化自动修复系统"""
        try:
            from unified_auto_repair_system import UnifiedAutoRepairSystem
            return UnifiedAutoRepairSystem()
        except ImportError as e:
            logger.error(f"自动修复系统初始化失败: {e}")
            return None
    
    def _create_mock_system(self, name: str) -> Any:
        """创建模拟系统"""
        class MockSystem:
            def __init__(self, name):
                self.name = name
                self.status = "active"
            
            def get_status(self):
                return {"status": self.status, "health_score": 1.0}
        
        return MockSystem(name)
    
    async def start_system(self) -> bool:
        """启动统一系统管理器"""
        if self.is_running:
            logger.warning("系统已在运行中")
            return False
        
        logger.info("🚀 启动简化统一系统管理器...")
        self.is_running = True
        
        # 启动监控线程
        if self.config.enable_monitoring:
            self._start_health_monitoring()
        
        # 启动上下文同步
        if self.config.context_sync_enabled:
            await self._start_context_sync()
        
        logger.info("✅ 简化统一系统管理器启动完成")
        return True
    
    def _start_health_monitoring(self):
        """启动健康监控"""
        self.monitoring_active = True
        self.health_check_thread = threading.Thread(target=self._health_monitoring_loop, daemon=True)
        self.health_check_thread.start()
        logger.info("健康监控已启动")
    
    async def _start_context_sync(self):
        """启动上下文同步"""
        logger.info("启动上下文同步...")
        sync_task = asyncio.create_task(self._context_sync_loop())
        self.sync_tasks.append(sync_task)
        logger.info("✅ 上下文同步已启动")
    
    def _health_monitoring_loop(self):
        """健康监控循环"""
        while self.monitoring_active and self.is_running:
            try:
                self._perform_health_check()
                time.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"健康监控循环错误: {e}")
                time.sleep(60)  # 错误后等待1分钟
    
    def _perform_health_check(self):
        """执行健康检查"""
        for name, system in self.systems.items():
            if system and self.system_status[name] == SystemStatus.ACTIVE:
                try:
                    health_score = self._check_system_health(name, system)
                    self.system_metrics[name].system_health_score = health_score
                    self.system_metrics[name].last_health_check = datetime.now()
                except Exception as e:
                    logger.error(f"健康检查失败: {name} - {e}")
                    self.system_status[name] = SystemStatus.ERROR
    
    def _check_system_health(self, name: str, system: Any) -> float:
        """检查单个系统健康状态"""
        if hasattr(system, 'get_status'):
            try:
                status = system.get_status()
                if isinstance(status, dict):
                    return status.get('health_score', 1.0)
            except:
                pass
        return 1.0  # 默认健康分数
    
    async def _context_sync_loop(self):
        """上下文同步循环"""
        logger.info("上下文同步循环已启动")
        while self.is_running:
            try:
                # 批量处理同步请求
                batch = []
                for _ in range(self.config.sync_batch_size):
                    if self.sync_queue.empty():
                        break
                    sync_request = await self.sync_queue.get()
                    batch.append(sync_request)
                
                if batch:
                    await self._process_sync_batch(batch)
                
                await asyncio.sleep(self.config.sync_interval)
            except Exception as e:
                logger.error(f"上下文同步循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _process_sync_batch(self, batch: List[Dict[str, Any]]):
        """批量处理同步请求"""
        logger.info(f"处理同步批次: {len(batch)} 个请求")
        
        tasks = []
        for request in batch:
            task = asyncio.create_task(self._process_sync_request_safe(request))
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            successful = sum(1 for r in results if r is True)
            failed = sum(1 for r in results if isinstance(r, Exception))
            
            # 更新指标
            for metrics in self.system_metrics.values():
                metrics.sync_operations += len(batch)
                metrics.successful_syncs += successful
                metrics.failed_syncs += failed
            
            logger.info(f"同步批次完成: 成功 {successful}, 失败 {failed}")
    
    async def _process_sync_request_safe(self, request: Dict[str, Any]) -> bool:
        """安全处理同步请求"""
        try:
            source_system = request.get('source_system')
            target_system = request.get('target_system')
            transfer_block = request.get('transfer_block')
            
            if source_system and target_system and transfer_block:
                await self._synchronize_context(source_system, target_system, transfer_block)
                return True
            else:
                logger.warning(f"同步请求参数不完整: {request}")
                return False
        except Exception as e:
            logger.error(f"同步请求处理失败: {e}")
            return False
    
    async def _synchronize_context(self, source: str, target: str, transfer_block: Union[Dict[str, Any], TransferBlock]):
        """同步上下文"""
        # 转换传输块格式
        if isinstance(transfer_block, dict):
            tb = TransferBlock.from_dict(transfer_block)
        else:
            tb = transfer_block
        
        logger.info(f"同步上下文: {source} -> {target} (块: {tb.block_id})")
        
        # 记录同步历史
        sync_record = {
            'timestamp': datetime.now().isoformat(),
            'source_system': source,
            'target_system': target,
            'transfer_block_id': tb.block_id,
            'content_type': tb.content_type,
            'priority': tb.priority,
            'status': 'started'
        }
        self.sync_history.append(sync_record)
        
        try:
            # 根据目标系统类型执行不同的同步逻辑
            if target == 'memory_manager' and 'memory_manager' in self.systems:
                await self._sync_to_memory_manager(tb)
            elif target == 'context_manager' and 'context_manager' in self.systems:
                await self._sync_to_context_manager(tb)
            elif target == 'ai_agents' and 'ai_agents' in self.systems:
                await self._sync_to_ai_agents(tb)
            elif target == 'auto_repair' and 'auto_repair' in self.systems:
                await self._sync_to_auto_repair(tb)
            else:
                logger.warning(f"目标系统不支持同步: {target}")
                sync_record['status'] = 'unsupported_target'
                return
            
            sync_record['status'] = 'completed'
            logger.info(f"✅ 上下文同步完成: {tb.block_id}")
            
        except Exception as e:
            logger.error(f"❌ 上下文同步失败: {tb.block_id} - {e}")
            sync_record['status'] = 'failed'
            sync_record['error'] = str(e)
    
    async def _sync_to_memory_manager(self, tb: TransferBlock):
        """同步到记忆管理器"""
        memory_manager = self.systems['memory_manager']
        if memory_manager:
            logger.info(f"记忆管理器同步: {tb.block_id}")
            # 模拟同步操作
            pass
    
    async def _sync_to_context_manager(self, tb: TransferBlock):
        """同步到上下文管理器"""
        context_manager = self.systems['context_manager']
        if context_manager and isinstance(context_manager, MinimalContextManager):
            # 创建新的上下文
            context_type = tb.content_type
            context_id = context_manager.create_context(context_type, tb.content)
            logger.info(f"上下文创建成功: {context_id}")
    
    async def _sync_to_ai_agents(self, tb: TransferBlock):
        """同步到AI代理系统"""
        ai_agents = self.systems['ai_agents']
        if ai_agents:
            logger.info(f"AI代理同步: {tb.block_id}")
            # 模拟同步操作
            pass
    
    async def _sync_to_auto_repair(self, tb: TransferBlock):
        """同步到自动修复系统"""
        auto_repair = self.systems['auto_repair']
        if auto_repair:
            logger.info(f"自动修复同步: {tb.block_id}")
            # 模拟同步操作
            pass
    
    def create_transfer_block(self, source_system: str, target_system: str, 
                            content_type: str, content: Dict[str, Any], 
                            priority: int = 1, **kwargs) -> TransferBlock:
        """创建传输块"""
        block_id = f"tb_{int(time.time() * 1000)}_{hash(f'{source_system}_{target_system}_{content_type}') % 10000}"
        
        tb = TransferBlock(
            block_id=block_id,
            source_system=source_system,
            target_system=target_system,
            content_type=content_type,
            content=content,
            metadata=kwargs.get('metadata', {}),
            priority=priority,
            compression_level=kwargs.get('compression_level', 'medium'),
            encryption_enabled=kwargs.get('encryption_enabled', True),
            ham_compatibility=kwargs.get('ham_compatibility', {}),
            activation_commands=kwargs.get('activation_commands', [])
        )
        
        self.transfer_blocks.append(tb)
        logger.info(f"创建传输块: {block_id}")
        return tb
    
    async def queue_sync_request(self, source_system: str, target_system: str, 
                               transfer_block: Union[TransferBlock, Dict[str, Any]]):
        """队列同步请求"""
        if isinstance(transfer_block, TransferBlock):
            tb_dict = transfer_block.to_dict()
        else:
            tb_dict = transfer_block
        
        sync_request = {
            'source_system': source_system,
            'target_system': target_system,
            'transfer_block': tb_dict,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.sync_queue.put(sync_request)
        logger.info(f"同步请求已队列: {source_system} -> {target_system}")
    
    def get_system_status(self, system_name: Optional[str] = None) -> Dict[str, Any]:
        """获取系统状态"""
        if system_name:
            if system_name in self.systems:
                return {
                    'name': system_name,
                    'status': self.system_status[system_name].value,
                    'metrics': self._metrics_to_dict(self.system_metrics[system_name]),
                    'config': self.system_configs[system_name]
                }
            return {}
        
        # 返回所有系统状态
        all_status = {}
        for name in self.systems.keys():
            all_status[name] = {
                'status': self.system_status[name].value,
                'metrics': self._metrics_to_dict(self.system_metrics[name]),
                'config': self.system_configs[name]
            }
        return all_status
    
    def _metrics_to_dict(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """转换指标为字典"""
        return {
            'total_operations': metrics.total_operations,
            'successful_operations': metrics.successful_operations,
            'failed_operations': metrics.failed_operations,
            'average_response_time': metrics.average_response_time,
            'last_health_check': metrics.last_health_check.isoformat() if metrics.last_health_check else None,
            'system_health_score': metrics.system_health_score,
            'active_components': metrics.active_components,
            'sync_operations': metrics.sync_operations,
            'successful_syncs': metrics.successful_syncs,
            'failed_syncs': metrics.failed_syncs
        }
    
    def execute_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """执行操作"""
        try:
            # 记录操作开始
            start_time = time.time()
            
            # 根据操作类型分发到相应的系统
            result = self._dispatch_operation(operation, **kwargs)
            
            # 记录操作完成
            execution_time = time.time() - start_time
            self._record_operation_metrics(operation, True, execution_time)
            
            return {
                'success': True,
                'result': result,
                'execution_time': execution_time
            }
        except Exception as e:
            logger.error(f"操作执行失败: {operation} - {e}")
            self._record_operation_metrics(operation, False, 0)
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }
    
    def _dispatch_operation(self, operation: str, **kwargs) -> Any:
        """分发操作到相应的系统"""
        # 根据操作类型路由到不同的系统
        if operation.startswith('repair.'):
            return self._handle_repair_operation(operation, **kwargs)
        elif operation.startswith('context.'):
            return self._handle_context_operation(operation, **kwargs)
        elif operation.startswith('memory.'):
            return self._handle_memory_operation(operation, **kwargs)
        elif operation.startswith('ai.'):
            return self._handle_ai_operation(operation, **kwargs)
        elif operation.startswith('training.'):
            return self._handle_training_operation(operation, **kwargs)
        elif operation.startswith('sync.'):
            return self._handle_sync_operation(operation, **kwargs)
        else:
            raise ValueError(f"不支持的操作类型: {operation}")
    
    def _handle_repair_operation(self, operation: str, **kwargs) -> Any:
        """处理修复操作"""
        if 'auto_repair' in self.systems and self.systems['auto_repair']:
            repair_system = self.systems['auto_repair']
            if operation == 'repair.run_unified':
                target_path = kwargs.get('target_path', '.')
                return repair_system.run_unified_auto_repair(target_path)
        raise RuntimeError("修复系统不可用")
    
    def _handle_context_operation(self, operation: str, **kwargs) -> Any:
        """处理上下文操作"""
        if 'context_manager' in self.systems and self.systems['context_manager']:
            context_manager = self.systems['context_manager']
            if operation == 'context.create':
                context_type = kwargs.get('context_type', 'general')
                initial_content = kwargs.get('initial_content')
                return context_manager.create_context(context_type, initial_content)
            elif operation == 'context.get':
                context_id = kwargs.get('context_id')
                return context_manager.get_context(context_id)
            elif operation == 'context.update':
                context_id = kwargs.get('context_id')
                updates = kwargs.get('updates')
                return context_manager.update_context(context_id, updates)
        raise RuntimeError("上下文管理器不可用")
    
    def _handle_memory_operation(self, operation: str, **kwargs) -> Any:
        """处理记忆操作"""
        if 'memory_manager' in self.systems and self.systems['memory_manager']:
            memory_manager = self.systems['memory_manager']
            # 模拟记忆操作
            if operation == 'memory.store':
                return {"status": "stored", "memory_id": f"mem_{int(time.time())}"}
            elif operation == 'memory.retrieve':
                return [{"memory_id": "mem_1", "content": "sample memory"}]
        raise RuntimeError("记忆管理器不可用")
    
    def _handle_ai_operation(self, operation: str, **kwargs) -> Any:
        """处理AI操作"""
        if 'ai_agents' in self.systems and self.systems['ai_agents']:
            ai_system = self.systems['ai_agents']
            # 模拟AI操作
            return {"status": "ai_operation_completed"}
        raise RuntimeError("AI系统不可用")
    
    def _handle_training_operation(self, operation: str, **kwargs) -> Any:
        """处理训练操作"""
        if 'training' in self.systems and self.systems['training']:
            training_system = self.systems['training']
            # 模拟训练操作
            return {"status": "training_completed"}
        raise RuntimeError("训练系统不可用")
    
    def _handle_sync_operation(self, operation: str, **kwargs) -> Any:
        """处理同步操作"""
        if operation == 'sync.create_block':
            return self.create_transfer_block(
                kwargs.get('source_system'),
                kwargs.get('target_system'),
                kwargs.get('content_type'),
                kwargs.get('content'),
                kwargs.get('priority', 1),
                **{k: v for k, v in kwargs.items() if k not in ['source_system', 'target_system', 'content_type', 'content', 'priority']}
            )
        elif operation == 'sync.queue':
            # 这里需要异步执行，但execute_operation是同步的
            # 返回一个可以await的协程
            return self.queue_sync_request(
                kwargs.get('source_system'),
                kwargs.get('target_system'),
                kwargs.get('transfer_block')
            )
        raise RuntimeError(f"不支持的同步操作: {operation}")
    
    def _record_operation_metrics(self, operation: str, success: bool, execution_time: float):
        """记录操作指标"""
        # 这里可以根据操作类型记录到相应的系统指标中
        for metrics in self.system_metrics.values():
            metrics.total_operations += 1
            if success:
                metrics.successful_operations += 1
            else:
                metrics.failed_operations += 1
            # 更新平均响应时间
            if metrics.average_response_time == 0:
                metrics.average_response_time = execution_time
            else:
                metrics.average_response_time = (metrics.average_response_time + execution_time) / 2
    
    async def stop_system(self) -> bool:
        """停止统一系统管理器"""
        if not self.is_running:
            return True
        
        logger.info("🛑 停止简化统一系统管理器...")
        self.is_running = False
        
        # 停止监控
        self.monitoring_active = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=30)
        
        # 停止同步任务
        for task in self.sync_tasks:
            task.cancel()
        
        # 等待所有同步任务完成
        if self.sync_tasks:
            await asyncio.gather(*self.sync_tasks, return_exceptions=True)
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info("✅ 简化统一系统管理器已停止")
        return True
    
    def get_system_summary(self) -> Dict[str, Any]:
        """获取系统摘要"""
        total_systems = len(self.systems)
        active_systems = sum(1 for status in self.system_status.values() if status == SystemStatus.ACTIVE)
        error_systems = sum(1 for status in self.system_status.values() if status == SystemStatus.ERROR)
        
        total_operations = sum(m.total_operations for m in self.system_metrics.values())
        successful_operations = sum(m.successful_operations for m in self.system_metrics.values())
        
        total_syncs = sum(m.sync_operations for m in self.system_metrics.values())
        successful_syncs = sum(m.successful_syncs for m in self.system_metrics.values())
        
        uptime = datetime.now() - self.start_time
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'total_systems': total_systems,
            'active_systems': active_systems,
            'error_systems': error_systems,
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'success_rate': (successful_operations / total_operations * 100) if total_operations > 0 else 0,
            'total_syncs': total_syncs,
            'successful_syncs': successful_syncs,
            'sync_success_rate': (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0,
            'transfer_blocks_count': len(self.transfer_blocks),
            'sync_history_count': len(self.sync_history),
            'system_categories': self._get_system_categories_summary()
        }
    
    def _get_system_categories_summary(self) -> Dict[str, int]:
        """获取系统类别摘要"""
        categories = {}
        for config in self.system_configs.values():
            category = config.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def get_sync_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取同步历史"""
        return self.sync_history[-limit:] if self.sync_history else []
    
    def cleanup_old_transfer_blocks(self, max_age_hours: int = 24):
        """清理旧的传输块"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        old_count = len(self.transfer_blocks)
        self.transfer_blocks = [
            tb for tb in self.transfer_blocks 
            if tb.timestamp > cutoff_time
        ]
        
        new_count = len(self.transfer_blocks)
        cleaned_count = old_count - new_count
        
        if cleaned_count > 0:
            logger.info(f"清理了 {cleaned_count} 个旧的传输块")
        
        return cleaned_count

# 全局实例
_system_manager: Optional[UnifiedSystemManagerMinimal] = None

def get_unified_system_manager_minimal(config: Optional[SystemConfig] = None) -> UnifiedSystemManagerMinimal:
    """获取简化统一系统管理器实例"""
    global _system_manager
    if _system_manager is None:
        _system_manager = UnifiedSystemManagerMinimal(config)
    return _system_manager

async def start_unified_system_minimal(config: Optional[SystemConfig] = None) -> bool:
    """启动简化统一系统"""
    manager = get_unified_system_manager_minimal(config)
    return await manager.start_system()

async def stop_unified_system_minimal() -> bool:
    """停止简化统一系统"""
    global _system_manager
    if _system_manager:
        result = await _system_manager.stop_system()
        _system_manager = None
        return result
    return True

def get_system_status_minimal() -> Dict[str, Any]:
    """获取简化系统状态"""
    global _system_manager
    if _system_manager:
        return _system_manager.get_system_summary()
    return {}

def create_transfer_block_minimal(source_system: str, target_system: str, 
                                content_type: str, content: Dict[str, Any], 
                                priority: int = 1, **kwargs) -> TransferBlock:
    """创建传输块（简化版本）"""
    global _system_manager
    if _system_manager:
        return _system_manager.create_transfer_block(source_system, target_system, 
                                                   content_type, content, priority, **kwargs)
    else:
        # 如果没有系统管理器，直接创建传输块
        block_id = f"tb_{int(time.time() * 1000)}_{hash(f'{source_system}_{target_system}_{content_type}') % 10000}"
        return TransferBlock(
            block_id=block_id,
            source_system=source_system,
            target_system=target_system,
            content_type=content_type,
            content=content,
            metadata=kwargs.get('metadata', {}),
            priority=priority,
            compression_level=kwargs.get('compression_level', 'medium'),
            encryption_enabled=kwargs.get('encryption_enabled', True),
            ham_compatibility=kwargs.get('ham_compatibility', {}),
            activation_commands=kwargs.get('activation_commands', [])
        )

if __name__ == "__main__":
    # 测试简化统一系统管理器
    async def test_minimal_system():
        print("🚀 测试简化统一系统管理器...")
        
        # 创建系统管理器实例
        config = SystemConfig()
        manager = UnifiedSystemManagerMinimal(config)
        
        print("✅ 简化统一系统管理器创建成功")
        
        # 启动系统
        success = await manager.start_system()
        
        if success:
            print("✅ 简化统一系统启动成功")
            
            # 获取系统状态
            status = manager.get_system_summary()
            print(f"系统摘要:")
            print(f"  - 总系统数: {status['total_systems']}")
            print(f"  - 活跃系统数: {status['active_systems']}")
            print(f"  - 错误系统数: {status['error_systems']}")
            
            # 测试传输块创建
            test_block = create_transfer_block_minimal(
                source_system="test_system",
                target_system="context_manager",
                content_type="test_data",
                content={"test_key": "test_value", "timestamp": "2025-10-08T21:00:00"},
                priority=2
            )
            print(f"✅ 传输块创建成功: {test_block.block_id}")
            
            # 测试队列同步请求
            await manager.queue_sync_request("test_system", "context_manager", test_block)
            print("✅ 同步请求已队列")
            
            # 运行一段时间后获取同步历史
            await asyncio.sleep(3)
            
            sync_history = manager.get_sync_history(10)
            print(f"✅ 同步历史: {len(sync_history)} 条记录")
            
            # 测试上下文操作
            context_result = manager.execute_operation('context.create', 
                                                     context_type='test', 
                                                     initial_content={'test': 'data'})
            print(f"✅ 上下文创建结果: {context_result}")
            
            # 停止系统
            await stop_unified_system_minimal()
            print("✅ 简化统一系统已停止")
        else:
            print("❌ 简化统一系统启动失败")
    
    # 运行测试
    asyncio.run(test_minimal_system())