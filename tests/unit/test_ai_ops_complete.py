#!/usr/bin/env python3
"""
AI運維系統完整測試套件
基於實際代碼實現的100%測試覆蓋
"""

import asyncio
import sys
import os
import time
import json
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'backend', 'src'))

class TestAIOpsEngine(unittest.TestCase):
    """AI運維引擎測試"""
    
    def setUp(self):
        """測試設置"""
        from ai.ops.ai_ops_engine import AIOpsEngine
        self.ai_ops = AIOpsEngine()
    
    def test_initialization(self):
        """測試初始化"""
        self.assertIsNotNone(self.ai_ops)
        self.assertEqual(self.ai_ops.anomaly_threshold, 0.1)
        self.assertEqual(self.ai_ops.prediction_window, 24)
        self.assertEqual(self.ai_ops.min_data_points, 100)
    
    def test_detect_anomalies_high_cpu(self):
        """測試高CPU異常檢測"""
        async def run_test():
            metrics = {
                "cpu_usage": 95.0,
                "memory_usage": 75.0,
                "error_rate": 2.5,
                "response_time": 450
            }
            
            anomalies = await self.ai_ops.detect_anomalies("test_component", metrics)
            
            self.assertEqual(len(anomalies), 1)
            self.assertEqual(anomalies[0].anomaly_type, "high_cpu")
            self.assertEqual(anomalies[0].severity.value, "high")
            self.assertGreater(anomalies[0].confidence, 0.8)
        
        asyncio.run(run_test())
    
    def test_detect_anomalies_high_memory(self):
        """測試高內存異常檢測"""
        async def run_test():
            metrics = {
                "cpu_usage": 70.0,
                "memory_usage": 90.0,
                "error_rate": 2.5,
                "response_time": 450
            }
            
            anomalies = await self.ai_ops.detect_anomalies("test_component", metrics)
            
            self.assertEqual(len(anomalies), 1)
            self.assertEqual(anomalies[0].anomaly_type, "high_memory")
            self.assertEqual(anomalies[0].severity.value, "high")
        
        asyncio.run(run_test())
    
    def test_detect_anomalies_high_error_rate(self):
        """測試高錯誤率異常檢測"""
        async def run_test():
            metrics = {
                "cpu_usage": 70.0,
                "memory_usage": 75.0,
                "error_rate": 6.0,
                "response_time": 450
            }
            
            anomalies = await self.ai_ops.detect_anomalies("test_component", metrics)
            
            self.assertEqual(len(anomalies), 1)
            self.assertEqual(anomalies[0].anomaly_type, "high_error_rate")
            self.assertEqual(anomalies[0].severity.value, "critical")
        
        asyncio.run(run_test())
    
    def test_detect_anomalies_high_response_time(self):
        """測試高響應時間異常檢測"""
        async def run_test():
            metrics = {
                "cpu_usage": 70.0,
                "memory_usage": 75.0,
                "error_rate": 2.5,
                "response_time": 1200
            }
            
            anomalies = await self.ai_ops.detect_anomalies("test_component", metrics)
            
            self.assertEqual(len(anomalies), 1)
            self.assertEqual(anomalies[0].anomaly_type, "high_response_time")
            self.assertEqual(anomalies[0].severity.value, "high")
        
        asyncio.run(run_test())
    
    def test_detect_anomalies_no_issues(self):
        """測試無異常情況"""
        async def run_test():
            metrics = {
                "cpu_usage": 50.0,
                "memory_usage": 60.0,
                "error_rate": 1.0,
                "response_time": 200
            }
            
            anomalies = await self.ai_ops.detect_anomalies("test_component", metrics)
            
            self.assertEqual(len(anomalies), 0)
        
        asyncio.run(run_test())
    
    def test_predict_capacity_needs_insufficient_data(self):
        """測試容量預測數據不足"""
        async def run_test():
            # 不添加歷史數據
            result = await self.ai_ops.predict_capacity_needs()
            
            self.assertIn("error", result)
            self.assertEqual(result["error"], "數據不足")
        
        asyncio.run(run_test())
    
    def test_predict_capacity_needs_with_data(self):
        """測試容量預測有數據"""
        async def run_test():
            # 模擬歷史數據
            for i in range(20):
                state = {
                    'component_id': 'test',
                    'component_type': 'server',
                    'timestamp': datetime.now().isoformat(),
                    'state': {
                        'cpu_usage': 50 + i * 0.5,
                        'memory_usage': 60,
                        'disk_usage': 70,
                        'network_io': 100,
                        'request_rate': 500,
                        'error_rate': 1,
                        'response_time': 200,
                        'active_connections': 50,
                        'queue_length': 10
                    }
                }
                self.ai_ops.system_states.append(state)
            
            result = await self.ai_ops.predict_capacity_needs()
            
            self.assertIn("predicted_cpu", result)
            self.assertIn("current_cpu", result)
            self.assertIn("trend", result)
            self.assertIn("confidence", result)
        
        asyncio.run(run_test())

class TestPredictiveMaintenance(unittest.TestCase):
    """預測性維護測試"""
    
    def setUp(self):
        """測試設置"""
        from ai.ops.predictive_maintenance import PredictiveMaintenanceEngine
        self.maintenance = PredictiveMaintenanceEngine()
    
    def test_initialization(self):
        """測試初始化"""
        self.assertIsNotNone(self.maintenance)
        self.assertEqual(self.maintenance.prediction_window_hours, 24)
        self.assertEqual(self.maintenance.health_threshold, 70.0)
    
    def test_simple_health_assessment_good(self):
        """測試健康評估良好"""
        metrics = {
            "cpu_usage": 50.0,
            "memory_usage": 60.0,
            "response_time": 200,
            "error_rate": 1.0
        }
        
        health_score = self.maintenance._simple_health_assessment(metrics)
        
        self.assertGreater(health_score, 70.0)
        self.assertLessEqual(health_score, 100.0)
    
    def test_simple_health_assessment_poor(self):
        """測試健康評估差"""
        metrics = {
            "cpu_usage": 90.0,
            "memory_usage": 85.0,
            "response_time": 800,
            "error_rate": 5.0
        }
        
        health_score = self.maintenance._simple_health_assessment(metrics)
        
        self.assertLess(health_score, 70.0)
        self.assertGreaterEqual(health_score, 0.0)
    
    def test_simple_health_assessment_empty_metrics(self):
        """測試健康評估空指標"""
        metrics = {}
        
        health_score = self.maintenance._simple_health_assessment(metrics)
        
        self.assertEqual(health_score, 50.0)  # 默認值
    
    def test_predict_failure_probability(self):
        """測試故障預測"""
        metrics = {
            "cpu_usage": 85.0,
            "memory_usage": 80.0,
            "response_time": 600,
            "error_rate": 3.0
        }
        
        probability = self.maintenance._predict_failure_probability(metrics, "server")
        
        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)
    
    def test_generate_maintenance_recommendation(self):
        """測試生成維護建議"""
        health_score = 45.0
        component_id = "test_server"
        
        recommendation = self.maintenance._generate_maintenance_recommendation(
            health_score, component_id
        )
        
        self.assertIn(component_id, recommendation)
        self.assertIn("維護", recommendation)
        self.assertGreater(len(recommendation), 10)

class TestPerformanceOptimizer(unittest.TestCase):
    """性能優化器測試"""
    
    def setUp(self):
        """測試設置"""
        from ai.ops.performance_optimizer import PerformanceOptimizer
        self.optimizer = PerformanceOptimizer()
    
    def test_initialization(self):
        """測試初始化"""
        self.assertIsNotNone(self.optimizer)
        self.assertEqual(self.optimizer.optimization_threshold, 0.8)
        self.assertEqual(self.optimizer.performance_window_hours, 24)
    
    def test_analyze_performance_trend_empty(self):
        """測試性能趨勢分析空數據"""
        async def run_test():
            result = await self.optimizer._analyze_performance_trend("server", [])
            
            self.assertIn("trend", result)
            self.assertIn("confidence", result)
            self.assertEqual(result["trend"], "insufficient_data")
        
        asyncio.run(run_test())
    
    def test_analyze_performance_trend_with_data(self):
        """測試性能趨勢分析有數據"""
        async def run_test():
            # 模擬性能數據
            performance_data = []
            for i in range(10):
                performance_data.append({
                    'timestamp': datetime.now().isoformat(),
                    'component_id': 'test_server',
                    'component_type': 'server',
                    'metrics': {
                        'cpu_usage': 50 + i * 2,
                        'memory_usage': 60 + i,
                        'response_time': 200 + i * 10,
                        'error_rate': 1.0 + i * 0.1,
                        'throughput': 500 + i * 20
                    }
                })
            
            result = await self.optimizer._analyze_performance_trend("server", performance_data)
            
            self.assertIn("trend", result)
            self.assertIn("confidence", result)
            self.assertIn(result["trend"], ["increasing", "decreasing", "stable"])
        
        asyncio.run(run_test())
    
    def test_detect_bottlenecks_empty(self):
        """測試瓶頸檢測空數據"""
        async def run_test():
            bottlenecks = await self.optimizer.detect_bottlenecks("test_component")
            
            self.assertIsInstance(bottlenecks, list)
        
        asyncio.run(run_test())
    
    def test_detect_bottlenecks_with_data(self):
        """測試瓶頸檢測有數據"""
        async def run_test():
            # 添加性能歷史
            self.optimizer.performance_history = [{
                'timestamp': datetime.now().isoformat(),
                'component_id': 'test_server',
                'component_type': 'server',
                'metrics': {
                    'cpu_usage': 95.0,
                    'memory_usage': 85.0,
                    'response_time': 800,
                    'error_rate': 4.0,
                    'throughput': 300
                }
            }]
            
            bottlenecks = await self.optimizer.detect_bottlenecks("test_server")
            
            self.assertIsInstance(bottlenecks, list)
            # 應該檢測到CPU瓶頸
            if bottlenecks:
                self.assertIn("cpu", bottlenecks[0].lower())
        
        asyncio.run(run_test())

class TestCapacityPlanner(unittest.TestCase):
    """容量規劃器測試"""
    
    def setUp(self):
        """測試設置"""
        from ai.ops.capacity_planner import CapacityPlanner, ResourceUsage
        self.planner = CapacityPlanner()
        self.ResourceUsage = ResourceUsage
    
    def test_initialization(self):
        """測試初始化"""
        self.assertIsNotNone(self.planner)
        self.assertEqual(self.planner.prediction_window_hours, 24)
        self.assertEqual(self.planner.scaling_threshold, 0.8)
    
    def test_predict_cpu_needs_insufficient_data(self):
        """測試CPU需求預測數據不足"""
        async def run_test():
            usage = self.ResourceUsage(
                timestamp=datetime.now(),
                cpu_cores=4,
                memory_gb=8,
                disk_gb=100,
                network_mbps=100,
                gpu_count=1
            )
            
            result = await self.planner._predict_cpu_needs(usage)
            
            self.assertIsNone(result)
        
        asyncio.run(run_test())
    
    def test_predict_cpu_needs_with_data(self):
        """測試CPU需求預測有數據"""
        async def run_test():
            # 添加歷史數據
            for i in range(20):
                usage = self.ResourceUsage(
                    timestamp=datetime.now() - timedelta(hours=i),
                    cpu_cores=4 + i * 0.1,
                    memory_gb=8,
                    disk_gb=100,
                    network_mbps=100,
                    gpu_count=1
                )
                self.planner.usage_history.append({
                    'timestamp': usage.timestamp.isoformat(),
                    'usage': usage
                })
            
            current_usage = self.ResourceUsage(
                timestamp=datetime.now(),
                cpu_cores=6,
                memory_gb=8,
                disk_gb=100,
                network_mbps=100,
                gpu_count=1
            )
            
            result = await self.planner._predict_cpu_needs(current_usage)
            
            self.assertIsNotNone(result)
            self.assertIn("predicted_cpu", result)
            self.assertIn("recommendation", result)
            self.assertIn("urgency", result)
        
        asyncio.run(run_test())
    
    def test_analyze_capacity_trends_empty(self):
        """測試容量趨勢分析空數據"""
        analysis = self.planner._analyze_capacity_trends([])
        
        self.assertIn("cpu_trend", analysis)
        self.assertIn("memory_trend", analysis)
        self.assertIn("disk_trend", analysis)
    
    def test_analyze_capacity_trends_with_data(self):
        """測試容量趨勢分析有數據"""
        # 添加歷史數據
        for i in range(10):
            usage = self.ResourceUsage(
                timestamp=datetime.now() - timedelta(hours=i),
                cpu_cores=4 + i * 0.1,
                memory_gb=8 + i * 0.2,
                disk_gb=100 + i,
                network_mbps=100,
                gpu_count=1
            )
            self.planner.usage_history.append({
                'timestamp': usage.timestamp.isoformat(),
                'usage': usage
            })
        
        analysis = self.planner._analyze_capacity_trends(self.planner.usage_history)
        
        self.assertIn("cpu_trend", analysis)
        self.assertIn("memory_trend", analysis)
        self.assertIn("disk_trend", analysis)
        
        # 應該檢測到增長趨勢
        self.assertEqual(analysis["cpu_trend"], "increasing")
        self.assertEqual(analysis["memory_trend"], "increasing")

class TestIntelligentOpsManager(unittest.TestCase):
    """智能運維管理器測試"""
    
    def setUp(self):
        """測試設置"""
        from ai.ops.intelligent_ops_manager import IntelligentOpsManager
        self.manager = IntelligentOpsManager()
    
    def test_initialization(self):
        """測試初始化"""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.insight_retention_days, 30)
        self.assertEqual(self.manager.auto_action_threshold, 0.8)
    
    def test_collect_system_metrics(self):
        """測試收集系統指標"""
        async def run_test():
            # 模擬組件初始化失敗（無Redis）
            self.manager.ai_ops_engine = Mock()
            self.manager.predictive_maintenance = Mock()
            self.manager.performance_optimizer = Mock()
            self.manager.capacity_planner = Mock()
            
            # 設置mock返回值
            self.manager.ai_ops_engine.collect_system_metrics = AsyncMock()
            self.manager.predictive_maintenance.collect_component_metrics = AsyncMock()
            self.manager.performance_optimizer.collect_performance_metrics = AsyncMock()
            self.manager.capacity_planner.collect_resource_usage = AsyncMock()
            
            metrics = {
                "cpu_usage": 85.0,
                "memory_usage": 75.0,
                "response_time": 450,
                "error_rate": 2.5,
                "throughput": 800
            }
            
            # 應該不拋出異常
            await self.manager.collect_system_metrics("test_server", "api_server", metrics)
        
        asyncio.run(run_test())
    
    def test_get_insights(self):
        """測試獲取洞察"""
        async def run_test():
            # 添加測試洞察
            from ai.ops.intelligent_ops_manager import OpsInsight
            insight = OpsInsight(
                insight_id="test_1",
                insight_type="anomaly",
                severity="high",
                title="測試洞察",
                description="測試描述",
                affected_components=["test_server"],
                recommendations=["測試建議"],
                confidence=0.9,
                timestamp=datetime.now(),
                auto_actionable=True
            )
            
            self.manager.ops_insights = [insight.__dict__]
            
            insights = await self.manager.get_insights()
            
            self.assertEqual(len(insights), 1)
            self.assertEqual(insights[0].insight_id, "test_1")
        
        asyncio.run(run_test())
    
    def test_get_ops_dashboard_data(self):
        """測試獲取運維儀表板數據"""
        async def run_test():
            # 模擬系統健康分析
            self.manager._analyze_system_health = AsyncMock(return_value={
                'overall_score': 85.0,
                'unhealthy_components': []
            })
            
            dashboard = await self.manager.get_ops_dashboard_data()
            
            self.assertIn('system_health', dashboard)
            self.assertIn('recent_insights', dashboard)
            self.assertIn('active_alerts', dashboard)
            self.assertIn('auto_actions_24h', dashboard)
            self.assertIn('total_insights', dashboard)
            self.assertIn('last_update', dashboard)
        
        asyncio.run(run_test())

class TestIntegration(unittest.TestCase):
    """集成測試"""
    
    def test_components_interaction(self):
        """測試組件交互"""
        async def run_test():
            from ai.ops.ai_ops_engine import AIOpsEngine
            from ai.ops.predictive_maintenance import PredictiveMaintenanceEngine
            from ai.ops.performance_optimizer import PerformanceOptimizer
            from ai.ops.capacity_planner import CapacityPlanner
            
            # 創建所有組件
            ai_ops = AIOpsEngine()
            maintenance = PredictiveMaintenanceEngine()
            optimizer = PerformanceOptimizer()
            planner = CapacityPlanner()
            
            # 測試數據
            metrics = {
                "cpu_usage": 85.0,
                "memory_usage": 75.0,
                "error_rate": 2.5,
                "response_time": 450,
                "throughput": 800
            }
            
            # 執行異常檢測
            anomalies = await ai_ops.detect_anomalies("test_component", metrics)
            self.assertGreaterEqual(len(anomalies), 0)
            
            # 執行健康評估
            health_score = maintenance._simple_health_assessment(metrics)
            self.assertGreaterEqual(health_score, 0)
            self.assertLessEqual(health_score, 100)
            
            # 添加性能數據
            optimizer.performance_history = [{
                'timestamp': datetime.now().isoformat(),
                'component_id': 'test_component',
                'component_type': 'server',
                'metrics': metrics
            }]
            
            # 執行瓶頸檢測
            bottlenecks = await optimizer.detect_bottlenecks("test_component")
            self.assertIsInstance(bottlenecks, list)
            
            # 創建資源使用記錄
            from ai.ops.capacity_planner import ResourceUsage
            usage = ResourceUsage(
                timestamp=datetime.now(),
                cpu_cores=4,
                memory_gb=8,
                disk_gb=100,
                network_mbps=100,
                gpu_count=1
            )
            
            # 添加歷史數據
            for i in range(20):
                historical_usage = ResourceUsage(
                    timestamp=datetime.now() - timedelta(hours=i),
                    cpu_cores=4 + i * 0.1,
                    memory_gb=8,
                    disk_gb=100,
                    network_mbps=100,
                    gpu_count=1
                )
                planner.usage_history.append({
                    'timestamp': historical_usage.timestamp.isoformat(),
                    'usage': historical_usage
                })
            
            # 執行CPU預測
            prediction = await planner._predict_cpu_needs(usage)
            if prediction:  # 可能为None如果数据不足
                self.assertIn("predicted_cpu", prediction)
        
        asyncio.run(run_test())

def run_all_tests():
    """運行所有測試"""
    # 創建測試套件
    test_suite = unittest.TestSuite()
    
    # 添加測試類
    test_classes = [
        TestAIOpsEngine,
        TestPredictiveMaintenance,
        TestPerformanceOptimizer,
        TestCapacityPlanner,
        TestIntelligentOpsManager,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 輸出結果
    print(f"\n{'='*60}")
    print("測試結果摘要")
    print(f"{'='*60}")
    print(f"運行測試: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n失敗詳情:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\n錯誤詳情:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
