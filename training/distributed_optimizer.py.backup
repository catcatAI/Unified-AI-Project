#!/usr/bin/env python3
"""
分布式训练优化器
负责优化分布式训练性能，包括节点管理、负载均衡、通信优化等
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class DistributedOptimizer:
    """分布式训练优化器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.nodes = {}  # 节点信息
        self.task_queue = []  # 任务队列
        self.load_balancer = LoadBalancer()
        self.communication_optimizer = CommunicationOptimizer()
        self.monitoring_interval = self.config.get('monitoring_interval', 10)  # 秒
        self.is_monitoring = False
        
        logger.info("分布式训练优化器初始化完成")
    
    async def register_node(self, node_id: str, node_info: Dict[str, Any]):
        """注册训练节点"""
        self.nodes[node_id] = {
            'id': node_id,
            'info': node_info,
            'status': 'active',
            'last_heartbeat': time.time(),
            'performance_metrics': {},
            'assigned_tasks': []
        }
        
        logger.info(f"注册训练节点: {node_id}")
        return True
    
    async def unregister_node(self, node_id: str):
        """注销训练节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            logger.info(f"注销训练节点: {node_id}")
            return True
        return False
    
    async def heartbeat(self, node_id: str, metrics: Dict[str, Any]):
        """节点心跳"""
        if node_id in self.nodes:
            self.nodes[node_id].update({
                'last_heartbeat': time.time(),
                'performance_metrics': metrics
            })
            return True
        return False
    
    async def distribute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """分发训练任务"""
        # 选择最佳节点
        best_node = await self.load_balancer.select_best_node(self.nodes, task)
        
        if not best_node:
            logger.warning("没有可用的训练节点")
            return {'status': 'failed', 'error': 'No available nodes'}
        
        # 优化通信
        optimized_task = await self.communication_optimizer.optimize_task_communication(task)
        
        # 分配任务给节点
        result = await self._assign_task_to_node(best_node, optimized_task)
        
        # 记录任务分配
        if best_node in self.nodes:
            self.nodes[best_node]['assigned_tasks'].append({
                'task_id': task.get('id'),
                'assigned_time': time.time(),
                'status': 'assigned'
            })
        
        return result
    
    async def _assign_task_to_node(self, node_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """将任务分配给节点"""
        # 这里应该是实际的RPC调用或消息队列发送
        # 为了示例，我们模拟任务分配
        
        logger.info(f"将任务 {task.get('id')} 分配给节点 {node_id}")
        
        # 模拟任务执行
        await asyncio.sleep(0.1)
        
        return {
            'status': 'assigned',
            'node_id': node_id,
            'task_id': task.get('id'),
            'assigned_time': time.time()
        }
    
    async def collect_task_result(self, node_id: str, task_id: str, result: Dict[str, Any]):
        """收集任务结果"""
        logger.info(f"从节点 {node_id} 收集任务 {task_id} 的结果")
        
        # 更新节点任务状态
        if node_id in self.nodes:
            for task_info in self.nodes[node_id].get('assigned_tasks', []):
                if task_info.get('task_id') == task_id:
                    task_info['status'] = 'completed'
                    task_info['completed_time'] = time.time()
                    break
        
        return True
    
    async def optimize_resource_allocation(self):
        """优化资源分配"""
        # 收集所有节点的性能指标
        metrics = await self._collect_node_metrics()
        
        # 分析瓶颈
        bottlenecks = await self._identify_bottlenecks(metrics)
        
        # 重新分配资源
        reallocation_plan = await self._generate_reallocation_plan(bottlenecks)
        
        # 执行重新分配
        await self._execute_reallocation(reallocation_plan)
        
        logger.info("资源分配优化完成")
        return reallocation_plan
    
    async def _collect_node_metrics(self) -> Dict[str, Any]:
        """收集节点性能指标"""
        metrics = {}
        for node_id, node_info in self.nodes.items():
            metrics[node_id] = node_info.get('performance_metrics', {})
        return metrics
    
    async def _identify_bottlenecks(self, metrics: Dict[str, Any]) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        for node_id, node_metrics in metrics.items():
            # 检查CPU使用率
            cpu_usage = node_metrics.get('cpu_usage', 0)
            if cpu_usage > 80:
                bottlenecks.append(node_id)
            
            # 检查内存使用率
            memory_usage = node_metrics.get('memory_usage', 0)
            if memory_usage > 85:
                bottlenecks.append(node_id)
            
            # 检查GPU使用率（如果有GPU）
            gpu_usage = node_metrics.get('gpu_usage', 0)
            if gpu_usage > 90:
                bottlenecks.append(node_id)
        
        return bottlenecks
    
    async def _generate_reallocation_plan(self, bottlenecks: List[str]) -> Dict[str, Any]:
        """生成重新分配计划"""
        plan = {
            'timestamp': datetime.now().isoformat(),
            'bottlenecks': bottlenecks,
            'actions': []
        }
        
        # 为每个瓶颈节点生成优化建议
        for node_id in bottlenecks:
            plan['actions'].append({
                'node_id': node_id,
                'action': 'reduce_workload',
                'reason': 'high_resource_usage'
            })
        
        return plan
    
    async def _execute_reallocation(self, plan: Dict[str, Any]):
        """执行重新分配"""
        for action in plan.get('actions', []):
            node_id = action.get('node_id')
            action_type = action.get('action')
            
            if action_type == 'reduce_workload':
                logger.info(f"减少节点 {node_id} 的工作负载")
                # 这里应该实际执行减少工作负载的操作
                await asyncio.sleep(0.1)  # 模拟操作
    
    async def start_monitoring(self):
        """开始监控"""
        self.is_monitoring = True
        logger.info("开始分布式训练监控")
        
        while self.is_monitoring:
            try:
                # 优化资源分配
                await self.optimize_resource_allocation()
                
                # 更新负载均衡
                await self.load_balancer.update_strategy(self.nodes)
                
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"监控过程中发生错误: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        logger.info("停止分布式训练监控")
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """获取集群状态"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'total_nodes': len(self.nodes),
            'active_nodes': len([n for n in self.nodes.values() if n.get('status') == 'active']),
            'nodes': []
        }
        
        for node_id, node_info in self.nodes.items():
            status['nodes'].append({
                'id': node_id,
                'status': node_info.get('status'),
                'last_heartbeat': node_info.get('last_heartbeat'),
                'assigned_tasks_count': len(node_info.get('assigned_tasks', [])),
                'performance_metrics': node_info.get('performance_metrics', {})
            })
        
        return status

class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self):
        self.strategy = 'round_robin'
        self.last_selected_node_index = 0
    
    async def select_best_node(self, nodes: Dict[str, Any], task: Dict[str, Any]) -> Optional[str]:
        """选择最佳节点"""
        active_nodes = [node_id for node_id, node_info in nodes.items() 
                       if node_info.get('status') == 'active']
        
        if not active_nodes:
            return None
        
        if self.strategy == 'round_robin':
            return self._round_robin_selection(active_nodes)
        elif self.strategy == 'least_loaded':
            return await self._least_loaded_selection(nodes, active_nodes)
        else:
            return active_nodes[0]  # 默认选择第一个
    
    def _round_robin_selection(self, active_nodes: List[str]) -> str:
        """轮询选择"""
        selected_node = active_nodes[self.last_selected_node_index % len(active_nodes)]
        self.last_selected_node_index += 1
        return selected_node
    
    async def _least_loaded_selection(self, nodes: Dict[str, Any], active_nodes: List[str]) -> str:
        """最少负载选择"""
        # 选择负载最少的节点
        min_load = float('inf')
        best_node = None
        
        for node_id in active_nodes:
            node_info = nodes[node_id]
            # 计算节点负载（简化计算）
            metrics = node_info.get('performance_metrics', {})
            cpu_load = metrics.get('cpu_usage', 0)
            memory_load = metrics.get('memory_usage', 0)
            task_count = len(node_info.get('assigned_tasks', []))
            
            # 综合负载计算
            load = cpu_load * 0.5 + memory_load * 0.3 + task_count * 10
            
            if load < min_load:
                min_load = load
                best_node = node_id
        
        return best_node
    
    async def update_strategy(self, nodes: Dict[str, Any]):
        """更新负载均衡策略"""
        # 根据集群状态动态调整策略
        active_nodes = [node_info for node_info in nodes.values() 
                       if node_info.get('status') == 'active']
        
        if len(active_nodes) > 10:
            self.strategy = 'least_loaded'  # 节点多时使用最少负载策略
        else:
            self.strategy = 'round_robin'   # 节点少时使用轮询策略
        
        logger.debug(f"负载均衡策略更新为: {self.strategy}")

class CommunicationOptimizer:
    """通信优化器"""
    
    def __init__(self):
        self.compression_enabled = True
        self.batching_enabled = True
        self.batch_size = 10
    
    async def optimize_task_communication(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """优化任务通信"""
        optimized_task = task.copy()
        
        # 启用数据压缩
        if self.compression_enabled:
            optimized_task = await self._compress_task_data(optimized_task)
        
        # 启用批处理
        if self.batching_enabled:
            optimized_task = await self._batch_task_data(optimized_task)
        
        return optimized_task
    
    async def _compress_task_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """压缩任务数据"""
        # 这里应该实现实际的数据压缩逻辑
        # 为了示例，我们只是标记任务已被压缩
        task['_compressed'] = True
        logger.debug("任务数据已压缩")
        return task
    
    async def _batch_task_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """批处理任务数据"""
        # 这里应该实现实际的数据批处理逻辑
        # 为了示例，我们只是标记任务已批处理
        task['_batched'] = True
        logger.debug("任务数据已批处理")
        return task

if __name__ == "__main__":
    # 测试分布式优化器
    logging.basicConfig(level=logging.INFO)
    
    async def test_distributed_optimizer():
        optimizer = DistributedOptimizer()
        
        # 注册节点
        await optimizer.register_node('node1', {'cpu_cores': 8, 'memory_gb': 16})
        await optimizer.register_node('node2', {'cpu_cores': 16, 'memory_gb': 32})
        
        # 发送心跳
        await optimizer.heartbeat('node1', {'cpu_usage': 45, 'memory_usage': 60})
        await optimizer.heartbeat('node2', {'cpu_usage': 30, 'memory_usage': 40})
        
        # 分发任务
        task = {'id': 'task1', 'type': 'model_training', 'data_size': 1000}
        result = await optimizer.distribute_task(task)
        print(f"任务分发结果: {result}")
        
        # 获取集群状态
        cluster_status = optimizer.get_cluster_status()
        print(f"集群状态: {json.dumps(cluster_status, indent=2, ensure_ascii=False)}")
    
    # 运行测试
    asyncio.run(test_distributed_optimizer())