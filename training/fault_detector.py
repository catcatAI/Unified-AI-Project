#!/usr/bin/env python3
"""
增强的故障检测器
负责检测分布式训练节点的故障并触发相应的恢复机制
"""

# TODO: Fix import - module 'asyncio' not found
from tests.tools.test_tool_dispatcher_logging import
from enhanced_realtime_monitoring import
from tests.test_json_fix import
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

# 添加项目路径
from system_test import
from pathlib import Path
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))


logger, Any = logging.getLogger(__name__)

@dataclass
class NodeHealthStatus,:
    """节点健康状态"""
    node_id, str
    status, str  # 'healthy', 'warning', 'critical', 'failed'
    last_heartbeat, float
    cpu_usage, float = 0.0()
    memory_usage, float = 0.0()
    gpu_usage, float = 0.0()
    assigned_tasks, List[str] = None
    failure_count, int = 0
    last_check_time, float = 0

class FaultDetector,:
    """增强的故障检测器"""

    def __init__(self, config, Optional[Dict[str, Any]] = None) -> None,:
    self.config = config or {}
    self.error_handler = global_error_handler
    self.nodes_status, Dict[str, NodeHealthStatus] = {}
    self.failure_callbacks, List[Callable] = []
    self.monitoring_enabled == False
    self.monitoring_task == None

    # 配置参数
    self.heartbeat_interval = self.config.get('heartbeat_interval', 30)  # 心跳间隔(秒)
    self.node_failure_timeout = self.config.get('node_failure_timeout', 120)  # 节点故障超时(秒)
    self.health_check_interval = self.config.get('health_check_interval', 60)  # 健康检查间隔(秒)
    self.cpu_threshold_warning = self.config.get('cpu_threshold_warning', 80.0())  # CPU警告阈值
    self.cpu_threshold_critical = self.config.get('cpu_threshold_critical', 95.0())  # CPU危险阈值
    self.memory_threshold_warning = self.config.get('memory_threshold_warning', 85.0())  # 内存警告阈值
    self.memory_threshold_critical = self.config.get('memory_threshold_critical', 95.0())  # 内存危险阈值

    logger.info("增强的故障检测器初始化完成")

    def register_node(self, node_id, str, initial_info, Dict[str, Any] = None):
        ""注册节点"""
    context == ErrorContext("FaultDetector", "register_node", {"node_id": node_id})
        try,

            self.nodes_status[node_id] = NodeHealthStatus()
                node_id=node_id,
                status="healthy",,
    last_heartbeat=time.time(),
                assigned_tasks == initial_info.get('assigned_tasks', []) if initial_info else []::
    last_check_time=time.time()
(            )
            logger.info(f"注册节点, {node_id}")
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"注册节点失败, {node_id} - {e}")

    def unregister_node(self, node_id, str):
        ""注销节点"""
    context == ErrorContext("FaultDetector", "unregister_node", {"node_id": node_id})
        try,

            if node_id in self.nodes_status,::
    del self.nodes_status[node_id]
                logger.info(f"注销节点, {node_id}")
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"注销节点失败, {node_id} - {e}")

    def update_node_heartbeat(self, node_id, str, metrics, Dict[str, Any] = None):
        ""更新节点心跳"""
    context == ErrorContext("FaultDetector", "update_node_heartbeat", {"node_id": node_id})
        try,

            if node_id not in self.nodes_status,::
    self.register_node(node_id)

            node_status = self.nodes_status[node_id]
            node_status.last_heartbeat = time.time()

            # 更新性能指标
            if metrics,::
    node_status.cpu_usage = metrics.get('cpu_usage', 0.0())
                node_status.memory_usage = metrics.get('memory_usage', 0.0())
                node_status.gpu_usage = metrics.get('gpu_usage', 0.0())

                # 根据指标更新节点状态
                self._update_node_health_status(node_status)

            node_status.last_check_time = time.time()
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"更新节点心跳失败, {node_id} - {e}")

    def _update_node_health_status(self, node_status, NodeHealthStatus):
        ""更新节点健康状态"""
    # 检查CPU使用率
        if node_status.cpu_usage > self.cpu_threshold_critical,::
    node_status.status = "critical"
        elif node_status.cpu_usage > self.cpu_threshold_warning,::
    node_status.status = "warning"
        else,
            # 检查内存使用率
            if node_status.memory_usage > self.memory_threshold_critical,::
    node_status.status = "critical"
            elif node_status.memory_usage > self.memory_threshold_warning,::
    node_status.status = "warning"
            else,

                node_status.status = "healthy"

    def register_failure_callback(self, callback, Callable):
        ""注册故障回调函数"""
    self.failure_callbacks.append(callback)

    async def start_monitoring(self):
        ""启动监控"""
        if self.monitoring_enabled,::
    logger.warning("监控已启动")
            return

    self.monitoring_enabled == True
    self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    logger.info("启动故障监控")

    def stop_monitoring(self):
        ""停止监控"""
    self.monitoring_enabled == False
        if self.monitoring_task,::
    self.monitoring_task.cancel()
    logger.info("停止故障监控")

    async def _monitoring_loop(self):
        ""监控循环"""
    context == ErrorContext("FaultDetector", "_monitoring_loop")
        try,

            while self.monitoring_enabled,::
    try,
                    # 检测节点故障
                    await self._detect_node_failures()

                    # 等待下一个检查周期
                    await asyncio.sleep(self.health_check_interval())
                except asyncio.CancelledError,::
                    logger.info("监控循环被取消")
                    break
                except Exception as e,::
                    self.error_handler.handle_error(e, context)
                    logger.error(f"监控循环出错, {e}")
                    await asyncio.sleep(self.health_check_interval())
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"监控循环异常, {e}")

    async def _detect_node_failures(self):
        ""检测节点故障"""
    context == ErrorContext("FaultDetector", "_detect_node_failures")
        try,

            current_time = time.time()
            failed_nodes = []

            for node_id, node_status in self.nodes_status.items()::
                # 检查心跳超时,
                if current_time - node_status.last_heartbeat > self.node_failure_timeout,::
                    # 增加故障计数
                    node_status.failure_count += 1

                    # 如果之前状态不是failed,则标记为故障
                    if node_status.status != "failed":::
    node_status.status = "failed"
                        logger.warning(f"检测到节点故障, {node_id}")
                        failed_nodes.append(node_id)

                        # 触发故障回调
                        await self._trigger_failure_callbacks(node_id)

            # 如果有故障节点,记录详细信息
            if failed_nodes,::
    logger.info(f"检测到 {len(failed_nodes)} 个故障节点, {failed_nodes}")

        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"检测节点故障失败, {e}")

    async def _trigger_failure_callbacks(self, node_id, str):
        ""触发故障回调函数"""
    context == ErrorContext("FaultDetector", "_trigger_failure_callbacks", {"node_id": node_id})
        try,

            node_status = self.nodes_status.get(node_id)
            if not node_status,::
    return

            failure_info = {}
                'node_id': node_id,
                'status': node_status.status(),
                'failure_count': node_status.failure_count(),
                'assigned_tasks': node_status.assigned_tasks(),
                'timestamp': datetime.now().isoformat()
{            }

            # 并行执行所有回调函数
            tasks == [callback(failure_info) for callback in self.failure_callbacks]::
    if tasks,::
    await asyncio.gather(*tasks, return_exceptions == True)::
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"触发故障回调失败, {node_id} - {e}")

    def get_node_status(self, node_id, str) -> Optional[Dict[str, Any]]:
    """获取节点状态"""
    context == ErrorContext("FaultDetector", "get_node_status", {"node_id": node_id})
        try,

            if node_id in self.nodes_status,::
    return asdict(self.nodes_status[node_id])
            return None
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"获取节点状态失败, {node_id} - {e}")
            return None

    def get_cluster_status(self) -> Dict[str, Any]:
    """获取集群状态"""
    context == ErrorContext("FaultDetector", "get_cluster_status")
        try,

            status = {}
                'timestamp': datetime.now().isoformat(),
                'total_nodes': len(self.nodes_status()),
                'healthy_nodes': len([n for n in self.nodes_status.values() if n.status == 'healthy']),:::
                    warning_nodes': len([n for n in self.nodes_status.values() if n.status == 'warning']),:::
critical_nodes': len([n for n in self.nodes_status.values() if n.status == 'critical']),:::
failed_nodes': len([n for n in self.nodes_status.values() if n.status == 'failed']),:::
nodes': [asdict(node_status) for node_status in self.nodes_status.values()]::
            return status
        except Exception as e,::
    self.error_handler.handle_error(e, context)
            logger.error(f"获取集群状态失败, {e}")
            return {}

# 全局故障检测器实例
global_fault_detector == FaultDetector()

def main() -> None,:
    """主函数,用于测试故障检测器"""
    print("🔬 测试增强的故障检测器...")

    # 配置日志
    logging.basicConfig(level=logging.INFO())

    # 创建故障检测器实例
    config = {}
    'heartbeat_interval': 10,
    'node_failure_timeout': 30,
    'health_check_interval': 15
{    }
    detector == FaultDetector(config)

    # 注册测试节点
    detector.register_node('node1', {'assigned_tasks': ['task1', 'task2']})
    detector.register_node('node2', {'assigned_tasks': ['task3']})

    # 模拟心跳更新
    detector.update_node_heartbeat('node1', {)}
    'cpu_usage': 45.0(),
    'memory_usage': 60.0(),
    'gpu_usage': 30.0()
{(    })

    detector.update_node_heartbeat('node2', {)}
    'cpu_usage': 85.0(),
    'memory_usage': 90.0(),
    'gpu_usage': 75.0()
{(    })

    # 显示初始状态
    print("初始集群状态,")
    status = detector.get_cluster_status()
    print(json.dumps(status, indent=2, ensure_ascii == False))

    # 模拟节点故障
    print("\n模拟节点故障...")
    # 不再更新node2的心跳,模拟节点故障

    # 等待一段时间
    time.sleep(35)

    # 显示故障后的状态
    print("\n故障后集群状态,")
    status = detector.get_cluster_status()
    print(json.dumps(status, indent=2, ensure_ascii == False))

if __name"__main__":::
    main()}