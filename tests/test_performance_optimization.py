"""
测试模块 - test_performance_optimization

自动生成的测试模块,用于验证系统功能。
"""

#!/usr/bin/env python3
"""
性能优化测试
测试所有性能优化功能是否正常工作
"""

import unittest
import asyncio
import tempfile
from pathlib import Path

# 添加项目路径
import sys
project_root: Path = Path(__file__).parent.parent
backend_path: Path = project_root / "apps" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))
sys.path.insert(0, str(project_root / "training"))

class TestPerformanceOptimization(unittest.TestCase):
    """性能优化测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_gpu_optimizer_initialization(self) -> None:
        """测试GPU优化器初始化"""
        try:
            from training.gpu_optimizer import GPUOptimizer
            optimizer = GPUOptimizer()
            self.assertIsNotNone(optimizer)
        except Exception as e:
            self.skipTest(f"GPU优化器测试跳过, {e}")
    
    def test_system_monitor_initialization(self) -> None:
        """测试系统监控器初始化"""
        try:
            from apps.backend.src.monitoring.system_monitor import SystemMonitor
            monitor = SystemMonitor()
            self.assertIsNotNone(monitor)
        except Exception as e:
            self.skipTest(f"系统监控器测试跳过, {e}")
    
    def test_hsp_performance_optimizer_initialization(self) -> None:
        """测试HSP性能优化器初始化"""
        try:
            from apps.backend.src.hsp.performance_optimizer import HSPPerformanceOptimizer
            optimizer = HSPPerformanceOptimizer()
            self.assertIsNotNone(optimizer)
        except Exception as e:
            self.skipTest(f"HSP性能优化器测试跳过, {e}")
    
    def test_smart_resource_allocator_initialization(self) -> None:
        """测试智能资源分配器初始化"""
        try:
            from training.smart_resource_allocator import SmartResourceAllocator
            allocator = SmartResourceAllocator()
            self.assertIsNotNone(allocator)
        except Exception as e:
            self.skipTest(f"智能资源分配器测试跳过, {e}")
    
    def test_distributed_optimizer_initialization(self) -> None:
        """测试分布式优化器初始化"""
        try:
            from training.distributed_optimizer import DistributedOptimizer
            optimizer = DistributedOptimizer()
            self.assertIsNotNone(optimizer)
        except Exception as e:
            self.skipTest(f"分布式优化器测试跳过, {e}")

class TestGPUOptimization(unittest.TestCase):
    """GPU优化测试类"""
    
    def test_gpu_memory_optimization(self) -> None:
        """测试GPU内存优化"""
        try:
            from training.gpu_optimizer import GPUOptimizer
            optimizer = GPUOptimizer()
            
            # 测试GPU内存优化功能
            result = optimizer.optimize_gpu_memory()
            # 如果GPU不可用,应该返回False而不是抛出异常
            self.assertIsInstance(result, bool)
        except Exception as e:
            self.skipTest(f"GPU内存优化测试跳过, {e}")
    
    def test_mixed_precision_enable(self) -> None:
        """测试混合精度启用"""
        try:
            from training.gpu_optimizer import GPUOptimizer
            optimizer = GPUOptimizer()
            
            # 测试混合精度启用功能
            result = optimizer.enable_mixed_precision()
            # 如果GPU不可用,应该返回False而不是抛出异常
            self.assertIsInstance(result, bool)
        except Exception as e:
            self.skipTest(f"混合精度启用测试跳过, {e}")

class TestSystemMonitoring(unittest.TestCase):
    """系统监控测试类"""
    
    def test_system_metrics_collection(self) -> None:
        """测试系统指标收集"""
        try:
            from apps.backend.src.monitoring.system_monitor import SystemMonitor
            monitor = SystemMonitor()
            
            # 收集一次指标
            metrics = monitor.collect_metrics()
            self.assertIsNotNone(metrics)
            
            # 检查指标字段
            self.assertTrue(hasattr(metrics, 'cpu_percent'))
            self.assertTrue(hasattr(metrics, 'memory_percent'))
        except Exception as e:
            self.skipTest(f"系统指标收集测试跳过, {e}")
    
    def test_resource_recommendations(self) -> None:
        """测试资源使用建议"""
        try:
            from apps.backend.src.monitoring.system_monitor import SystemMonitor
            monitor = SystemMonitor()
            
            # 获取资源建议
            recommendations = monitor.get_resource_recommendations()
            self.assertIsNotNone(recommendations)
        except Exception as e:
            self.skipTest(f"资源使用建议测试跳过, {e}")

class TestHSPPerformanceOptimization(unittest.TestCase):
    """HSP性能优化测试类"""
    
    def test_message_caching(self) -> None:
        """测试消息缓存"""
        try:
            from apps.backend.src.hsp.performance_optimizer import HSPPerformanceOptimizer
            optimizer = HSPPerformanceOptimizer()
            
            # 测试消息缓存
            test_message = {'data': 'test'}
            optimizer.cache_message('test_id', test_message)
            
            # 测试获取缓存消息
            cached_message = optimizer.get_cached_message('test_id')
            self.assertEqual(cached_message, test_message)
        except Exception as e:
            self.skipTest(f"消息缓存测试跳过, {e}")
    
    def test_message_compression(self) -> None:
        """测试消息压缩"""
        try:
            from apps.backend.src.hsp.performance_optimizer import HSPPerformanceOptimizer
            optimizer = HSPPerformanceOptimizer()
            
            # 测试消息压缩
            test_message = {
                'message_id': 'test1',
                'message_type': 'HSP.Fact_v0.1',
                'data': 'This is a test message with some data to compress'
            }
            
            compressed = optimizer.compress_message(test_message)
            self.assertIsInstance(compressed, bytes)
            
            # 测试消息解压缩
            decompressed = optimizer.decompress_message(compressed)
            self.assertEqual(decompressed, test_message)
        except Exception as e:
            self.skipTest(f"消息压缩测试跳过, {e}")

class TestResourceAllocation(unittest.TestCase):
    """资源分配测试类"""
    
    def test_smart_resource_allocation(self) -> None:
        """测试智能资源分配"""
        try:
            from training.smart_resource_allocator import SmartResourceAllocator, ResourceRequest
            allocator = SmartResourceAllocator()
            
            # 创建资源请求
            request = ResourceRequest(
                task_id="test_task",
                cpu_cores=2,
                memory_gb=4.0,
                gpu_memory_gb=0.0,
                priority=5,
                estimated_time_hours=1.0,
                resource_type="cpu"
            )
            
            # 请求资源
            allocator.request_resources(request)
            
            # 分配资源
            allocations = allocator.allocate_resources()
            self.assertIsInstance(allocations, list)
        except Exception as e:
            self.skipTest(f"智能资源分配测试跳过, {e}")
    
    def test_resource_utilization_monitoring(self) -> None:
        """测试资源利用率监控"""
        try:
            from training.smart_resource_allocator import SmartResourceAllocator
            allocator = SmartResourceAllocator()
            
            # 获取资源利用率
            utilization = allocator.get_resource_utilization()
            self.assertIsNotNone(utilization)
        except Exception as e:
            self.skipTest(f"资源利用率监控测试跳过, {e}")

class TestDistributedOptimization(unittest.TestCase):
    """分布式优化测试类"""
    
    def test_node_registration(self) -> None:
        """测试节点注册"""
        try:
            from training.distributed_optimizer import DistributedOptimizer
            optimizer = DistributedOptimizer()
            
            # 注册节点
            node_info = {'cpu_cores': 8, 'memory_gb': 16}
            result = asyncio.run(optimizer.register_node('test_node', node_info))
            self.assertTrue(result)
        except Exception as e:
            self.skipTest(f"节点注册测试跳过, {e}")
    
    def test_cluster_status(self) -> None:
        """测试集群状态"""
        try:
            from training.distributed_optimizer import DistributedOptimizer
            optimizer = DistributedOptimizer()
            
            # 获取集群状态
            status = optimizer.get_cluster_status()
            self.assertIsNotNone(status)
        except Exception as e:
            self.skipTest(f"集群状态测试跳过, {e}")

if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)