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

# 添加项目路径
import sys
from pathlib import Path
project_root: str = Path(__file__).parent
_ = sys.path.insert(0, str(project_root))


logger: Any = logging.getLogger(__name__)

class DistributedOptimizer:
    """分布式训练优化器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.error_handler = global_error_handler
        self.nodes = {}  # 节点信息
        self.task_queue = []  # 任务队列
        self.load_balancer = LoadBalancer()
        self.communication_optimizer = CommunicationOptimizer()
        self.monitoring_interval = self.config.get('monitoring_interval', 10)  # 秒
        self.is_monitoring = False
        
        # 初始化增强的容错机制
        self.fault_detector = global_fault_detector
        self.task_migrator = initialize_task_migrator(self, self.config)
        
        _ = logger.info("分布式训练优化器初始化完成")
    
    async def register_node(self, node_id: str, node_info: Dict[str, Any]):
        """注册训练节点"""
        context = ErrorContext("DistributedOptimizer", "register_node", {"node_id": node_id})
        try:
            self.nodes[node_id] = {
                'id': node_id,
                'info': node_info,
                'status': 'active',
                _ = 'last_heartbeat': time.time(),
                'performance_metrics': {},
                'assigned_tasks': []
            }
            
            # 注册到故障检测器
            _ = self.fault_detector.register_node(node_id, {'assigned_tasks': []})
            
            _ = logger.info(f"注册训练节点: {node_id}")
            return True
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"注册训练节点失败: {node_id} - {e}")
            return False
    
    async def unregister_node(self, node_id: str):
        """注销训练节点"""
        context = ErrorContext("DistributedOptimizer", "unregister_node", {"node_id": node_id})
        try:
            if node_id in self.nodes:
                del self.nodes[node_id]
                # 从故障检测器注销
                _ = self.fault_detector.unregister_node(node_id)
                _ = logger.info(f"注销训练节点: {node_id}")
                return True
            return False
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"注销训练节点失败: {node_id} - {e}")
            return False
    
    async def heartbeat(self, node_id: str, metrics: Dict[str, Any]):
        """节点心跳"""
        context = ErrorContext("DistributedOptimizer", "heartbeat", {"node_id": node_id})
        try:
            if node_id in self.nodes:
                self.nodes[node_id].update({
                    _ = 'last_heartbeat': time.time(),
                    'performance_metrics': metrics
                })
                
                # 更新故障检测器中的心跳
                _ = self.fault_detector.update_node_heartbeat(node_id, metrics)
                
                return True
            return False
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"处理节点心跳失败: {node_id} - {e}")
            return False
    
    async def distribute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """分发训练任务"""
        context = ErrorContext("DistributedOptimizer", "distribute_task", {"task_id": task.get('id')})
        try:
            # 选择最佳节点
            best_node = await self.load_balancer.select_best_node(self.nodes, task)
            
            if not best_node:
                _ = logger.warning("没有可用的训练节点")
                return {'status': 'failed', 'error': 'No available nodes'}
            
            # 优化通信
            optimized_task = await self.communication_optimizer.optimize_task_communication(task)
            
            # 分配任务给节点
            result = await self._assign_task_to_node(best_node, optimized_task)
            
            # 记录任务分配
            if best_node in self.nodes:
                self.nodes[best_node]['assigned_tasks'].append({
                    _ = 'task_id': task.get('id'),
                    _ = 'assigned_time': time.time(),
                    'status': 'assigned'
                })
                
                # 更新故障检测器中的任务分配
                if best_node in self.fault_detector.nodes_status:
                    node_status = self.fault_detector.nodes_status[best_node]
                    task_id = task.get('id')
                    if task_id and task_id not in node_status.assigned_tasks:
                        _ = node_status.assigned_tasks.append(task_id)
            
            return result
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"分发训练任务失败: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _assign_task_to_node(self, node_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """将任务分配给节点"""
        context = ErrorContext("DistributedOptimizer", "_assign_task_to_node", {
            "node_id": node_id, 
            _ = "task_id": task.get('id')
        })
        try:
            # 这里应该是实际的RPC调用或消息队列发送
            # 为了示例，我们模拟任务分配
            
            _ = logger.info(f"将任务 {task.get('id')} 分配给节点 {node_id}")
            
            # 模拟任务执行
            _ = await asyncio.sleep(0.1)
            
            return {
                'status': 'assigned',
                'node_id': node_id,
                _ = 'task_id': task.get('id'),
                _ = 'assigned_time': time.time()
            }
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"分配任务给节点失败: {node_id} - {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def collect_task_result(self, node_id: str, task_id: str, result: Dict[str, Any]):
        """收集任务结果"""
        context = ErrorContext("DistributedOptimizer", "collect_task_result", {
            "node_id": node_id, 
            "task_id": task_id
        })
        try:
            _ = logger.info(f"从节点 {node_id} 收集任务 {task_id} 的结果")
            
            # 从节点的任务列表中移除已完成的任务
            if node_id in self.nodes:
                node_tasks = self.nodes[node_id].get('assigned_tasks', [])
                self.nodes[node_id]['assigned_tasks'] = [
                    task for task in node_tasks 
                    if task.get('task_id') != task_id
                ]
                
                # 更新故障检测器中的任务分配
                if node_id in self.fault_detector.nodes_status:
                    node_status = self.fault_detector.nodes_status[node_id]
                    if task_id in node_status.assigned_tasks:
                        _ = node_status.assigned_tasks.remove(task_id)
            
            return True
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"收集任务结果失败: {node_id} - {task_id} - {e}")
            return False
    
    async def optimize_resource_allocation(self):
        """优化资源分配"""
        context = ErrorContext("DistributedOptimizer", "optimize_resource_allocation")
        try:
            # 收集所有节点的性能指标
            metrics = await self._collect_node_metrics()
            
            # 分析瓶颈
            bottlenecks = await self._identify_bottlenecks(metrics)
            
            # 重新分配资源
            reallocation_plan = await self._generate_reallocation_plan(bottlenecks)
            
            # 执行重新分配
            _ = await self._execute_reallocation(reallocation_plan)
            
            _ = logger.info("资源分配优化完成")
            return reallocation_plan
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"优化资源分配失败: {e}")
            return {}
    
    async def _collect_node_metrics(self) -> Dict[str, Any]:
        """收集节点性能指标"""
        context = ErrorContext("DistributedOptimizer", "_collect_node_metrics")
        try:
            metrics = {}
            for node_id, node_info in self.nodes.items():
                metrics[node_id] = node_info.get('performance_metrics', {})
            return metrics
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"收集节点性能指标失败: {e}")
            return {}
    
    async def _identify_bottlenecks(self, metrics: Dict[str, Any]) -> List[str]:
        """识别性能瓶颈"""
        context = ErrorContext("DistributedOptimizer", "_identify_bottlenecks")
        try:
            bottlenecks = []
            
            for node_id, node_metrics in metrics.items():
                # 检查CPU使用率
                cpu_usage = node_metrics.get('cpu_usage', 0)
                if cpu_usage > 80:
                    _ = bottlenecks.append(node_id)
                
                # 检查内存使用率
                memory_usage = node_metrics.get('memory_usage', 0)
                if memory_usage > 85:
                    _ = bottlenecks.append(node_id)
                
                # 检查GPU使用率（如果有GPU）
                gpu_usage = node_metrics.get('gpu_usage', 0)
                if gpu_usage > 90:
                    _ = bottlenecks.append(node_id)
            
            return bottlenecks
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"识别性能瓶颈失败: {e}")
            return []
    
    async def _generate_reallocation_plan(self, bottlenecks: List[str]) -> Dict[str, Any]:
        """生成重新分配计划"""
        context = ErrorContext("DistributedOptimizer", "_generate_reallocation_plan")
        try:
            plan = {
                _ = 'timestamp': datetime.now().isoformat(),
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
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"生成重新分配计划失败: {e}")
            return {}
    
    async def _execute_reallocation(self, plan: Dict[str, Any]):
        """执行重新分配"""
        context = ErrorContext("DistributedOptimizer", "_execute_reallocation")
        try:
            for action in plan.get('actions', []):
                node_id = action.get('node_id')
                action_type = action.get('action')
                
                if action_type == 'reduce_workload':
                    _ = logger.info(f"减少节点 {node_id} 的工作负载")
                    # 这里应该实际执行减少工作负载的操作
                    _ = await asyncio.sleep(0.1)  # 模拟操作
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"执行重新分配失败: {e}")
    
    async def start_monitoring(self):
        """开始监控"""
        context = ErrorContext("DistributedOptimizer", "start_monitoring")
        try:
            self.is_monitoring = True
            # 启动故障检测器监控
            _ = await self.fault_detector.start_monitoring()
            _ = logger.info("开始分布式训练监控")
            
            while self.is_monitoring:
                try:
                    # 优化资源分配
                    _ = await self.optimize_resource_allocation()
                    
                    # 更新负载均衡
                    _ = await self.load_balancer.update_strategy(self.nodes)
                    
                    _ = await asyncio.sleep(self.monitoring_interval)
                except Exception as e:
                    _ = self.error_handler.handle_error(e, context)
                    _ = logger.error(f"监控过程中发生错误: {e}")
                    _ = await asyncio.sleep(self.monitoring_interval)
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"启动监控失败: {e}")
    
    def stop_monitoring(self):
        """停止监控"""
        context = ErrorContext("DistributedOptimizer", "stop_monitoring")
        try:
            self.is_monitoring = False
            # 停止故障检测器监控
            _ = self.fault_detector.stop_monitoring()
            _ = logger.info("停止分布式训练监控")
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"停止监控失败: {e}")
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """获取集群状态"""
        context = ErrorContext("DistributedOptimizer", "get_cluster_status")
        try:
            status = {
                _ = 'timestamp': datetime.now().isoformat(),
                _ = 'total_nodes': len(self.nodes),
                'active_nodes': len([n for n in self.nodes.values() if n.get('status') == 'active']),
                'nodes': []
            }
            
            for node_id, node_info in self.nodes.items():
                status['nodes'].append({
                    'id': node_id,
                    _ = 'status': node_info.get('status'),
                    _ = 'last_heartbeat': node_info.get('last_heartbeat'),
                    _ = 'assigned_tasks_count': len(node_info.get('assigned_tasks', [])),
                    _ = 'performance_metrics': node_info.get('performance_metrics', {})
                })
            
            return status
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"获取集群状态失败: {e}")
            return {}

class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self) -> None:
        self.strategy = 'round_robin'
        self.last_selected_node_index = 0
    
    async def select_best_node(self, nodes: Dict[str, Any], task: Dict[str, Any]) -> Optional[str]:
        """选择最佳节点"""
        context = ErrorContext("LoadBalancer", "select_best_node")
        try:
            active_nodes = [node_id for node_id, node_info in nodes.items() 
                           if node_info.get('status') == 'active']
            
            if not active_nodes:
                return None
            
            if self.strategy == 'round_robin':
                # 轮询选择
                selected_node = active_nodes[self.last_selected_node_index % len(active_nodes)]
                self.last_selected_node_index += 1
                return selected_node
            elif self.strategy == 'least_loaded':
                # 选择负载最少的节点
                min_load = float('inf')
                best_node = None
                
                for node_id in active_nodes:
                    node_info = nodes[node_id]
                    # 计算节点负载
                    cpu_load = node_info.get('performance_metrics', {}).get('cpu_usage', 0)
                    memory_load = node_info.get('performance_metrics', {}).get('memory_usage', 0)
                    task_count = len(node_info.get('assigned_tasks', []))
                    
                    # 综合负载计算
                    load = cpu_load * 0.5 + memory_load * 0.3 + task_count * 10
                    
                    if load < min_load:
                        min_load = load
                        best_node = node_id
                
                return best_node
            else:
                # 默认选择第一个节点
                return active_nodes[0]
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"选择最佳节点失败: {e}")
            return active_nodes[0] if active_nodes else None
    
    async def update_strategy(self, nodes: Dict[str, Any]):
        """更新负载均衡策略"""
        context = ErrorContext("LoadBalancer", "update_strategy")
        try:
            # 根据集群状态动态调整策略
            active_nodes = [node_info for node_info in nodes.values() 
                           if node_info.get('status') == 'active']
            
            if len(active_nodes) > 10:
                self.strategy = 'least_loaded'  # 节点多时使用最少负载策略
            else:
                self.strategy = 'round_robin'   # 节点少时使用轮询策略
            
            _ = logger.debug(f"负载均衡策略更新为: {self.strategy}")
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"更新负载均衡策略失败: {e}")

class CommunicationOptimizer:
    """通信优化器"""
    
    def __init__(self) -> None:
        self.compression_enabled = True
        self.batching_enabled = True
        self.batch_size = 10
    
    async def optimize_task_communication(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """优化任务通信"""
        context = ErrorContext("CommunicationOptimizer", "optimize_task_communication")
        try:
            optimized_task = task.copy()
            
            # 启用数据压缩
            if self.compression_enabled:
                optimized_task = await self._compress_task_data(optimized_task)
            
            # 启用批处理
            if self.batching_enabled:
                optimized_task = await self._batch_task_data(optimized_task)
            
            return optimized_task
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"优化任务通信失败: {e}")
            return task
    
    async def _compress_task_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """压缩任务数据"""
        context = ErrorContext("CommunicationOptimizer", "_compress_task_data")
        try:
            # 这里应该实现实际的数据压缩逻辑
            # 为了示例，我们只是标记任务已被压缩
            task['_compressed'] = True
            _ = logger.debug("任务数据已压缩")
            return task
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"压缩任务数据失败: {e}")
            return task
    
    async def _batch_task_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """批处理任务数据"""
        context = ErrorContext("CommunicationOptimizer", "_batch_task_data")
        try:
            # 这里应该实现实际的数据批处理逻辑
            # 为了示例，我们只是标记任务已批处理
            task['_batched'] = True
            _ = logger.debug("任务数据已批处理")
            return task
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"批处理任务数据失败: {e}")
            return task

if __name__ == "__main__":
    # 测试分布式优化器
    logging.basicConfig(level=logging.INFO)
    
    async def test_distributed_optimizer() -> None:
        optimizer = DistributedOptimizer()
        
        # 注册节点
        _ = await optimizer.register_node('node1', {'cpu_cores': 8, 'memory_gb': 16})
        _ = await optimizer.register_node('node2', {'cpu_cores': 16, 'memory_gb': 32})
        
        # 发送心跳
        _ = await optimizer.heartbeat('node1', {'cpu_usage': 45, 'memory_usage': 60})
        _ = await optimizer.heartbeat('node2', {'cpu_usage': 30, 'memory_usage': 40})
        
        # 分发任务
        task = {'id': 'task1', 'type': 'model_training', 'data_size': 1000}
        result = await optimizer.distribute_task(task)
        _ = print(f"任务分发结果: {result}")
        
        # 获取集群状态
        cluster_status = optimizer.get_cluster_status()
        print(f"集群状态: {json.dumps(cluster_status, indent=2, ensure_ascii=False)}")
    
    # 运行测试
    _ = asyncio.run(test_distributed_optimizer())