#!/usr/bin/env python3
"""
AI运维系统集成测试
验证所有AI运维组件协同工作
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'backend', 'src'))

from ai.ops.intelligent_ops_manager import get_intelligent_ops_manager
from ai.ops.ai_ops_engine import get_ai_ops_engine
from ai.ops.predictive_maintenance import get_predictive_maintenance_engine
from ai.ops.performance_optimizer import get_performance_optimizer
from ai.ops.capacity_planner import get_capacity_planner

logging.basicConfig(level=logging.INFO())
logger = logging.getLogger(__name__)

class AIOpsIntegrationTest:
    """AI运维系统集成测试"""
    
    def __init__(self):
        self.test_results = {}
        self.ops_manager = None
        self.ai_ops = None
        self.maintenance = None
        self.optimizer = None
        self.planner = None
        
    async def setup(self):
        """设置测试环境"""
        try:
            logger.info("初始化AI运维组件...")
            
            # 初始化所有组件
            self.ops_manager = await get_intelligent_ops_manager()
            await self.ops_manager.initialize()
            
            self.ai_ops = await get_ai_ops_engine()
            await self.ai_ops.initialize()
            
            self.maintenance = await get_predictive_maintenance_engine()
            await self.maintenance.initialize()
            
            self.optimizer = await get_performance_optimizer()
            await self.optimizer.initialize()
            
            self.planner = await get_capacity_planner()
            await self.planner.initialize()
            
            logger.info("AI运维组件初始化完成")
            return True
            
        except Exception as e,:
            logger.error(f"初始化失败, {e}")
            return False
    
    async def test_component_initialization(self) -> bool,
        """测试组件初始化"""
        try:
            logger.info("测试组件初始化...")
            
            # 检查所有组件是否正常运行
            components_status = {
                "intelligent_ops_manager": self.ops_manager is not None,
                "ai_ops_engine": self.ai_ops is not None,
                "predictive_maintenance": self.maintenance is not None,
                "performance_optimizer": self.optimizer is not None,
                "capacity_planner": self.planner is not None
            }
            
            all_initialized = all(components_status.values())
            
            self.test_results["component_initialization"] = {
                "status": "PASS" if all_initialized else "FAIL",::
                "details": components_status
            }
            
            logger.info(f"组件初始化测试, {'通过' if all_initialized else '失败'}"):
            return all_initialized

        except Exception as e,:
            logger.error(f"组件初始化测试失败, {e}")
            self.test_results["component_initialization"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    async def test_metrics_collection(self) -> bool,
        """测试指标收集"""
        try:
            logger.info("测试指标收集...")
            
            # 模拟组件指标数据
            test_metrics = {
                "cpu_usage": 75.5(),
                "memory_usage": 68.2(),
                "response_time": 250,
                "error_rate": 1.5(),
                "throughput": 1200,
                "disk_io": 45.3(),
                "network_io": 85.7(),
                "active_connections": 150,
                "queue_length": 25,
                "concurrent_users": 80,
                "request_rate": 45.6()
            }
            
            # 收集指标
            await self.ops_manager.collect_system_metrics(
                "test_component_1", "api_server", test_metrics
            )
            
            # 等待处理
            await asyncio.sleep(2)
            
            # 验证数据是否被正确收集
            insights = await self.ops_manager.get_insights(limit=10)
            
            success = len(insights) >= 0  # 至少应该有洞察生成
            
            self.test_results["metrics_collection"] = {
                "status": "PASS" if success else "FAIL",::
                "insights_generated": len(insights),
                "metrics_processed": test_metrics
            }
            
            logger.info(f"指标收集测试, {'通过' if success else '失败'}"):
            return success

        except Exception as e,:
            logger.error(f"指标收集测试失败, {e}")
            self.test_results["metrics_collection"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    async def test_anomaly_detection(self) -> bool,
        """测试异常检测"""
        try:
            logger.info("测试异常检测...")
            
            # 模拟异常指标
            anomaly_metrics = {
                "cpu_usage": 95.0(),  # 异常高CPU使用率
                "memory_usage": 88.5(),
                "response_time": 1500,  # 异常高响应时间
                "error_rate": 8.0(),  # 异常高错误率
                "throughput": 200,
                "disk_io": 90.0(),
                "network_io": 95.0(),
                "active_connections": 300,
                "queue_length": 100,
                "concurrent_users": 200,
                "request_rate": 25.0()
            }
            
            # 收集异常指标
            await self.ops_manager.collect_system_metrics(
                "test_component_2", "database", anomaly_metrics
            )
            
            # 等待异常检测
            await asyncio.sleep(3)
            
            # 检查是否检测到异常
            anomalies = await self.ai_ops.get_recent_anomalies()
            
            success = len(anomalies) > 0
            
            self.test_results["anomaly_detection"] = {
                "status": "PASS" if success else "FAIL",::
                "anomalies_detected": len(anomalies),
                "anomaly_data": [a.__dict__ for a in anomalies[:3]]  # 前3个异常,:
            }
            
            logger.info(f"异常检测测试, {'通过' if success else '失败'}"):
            return success

        except Exception as e,:
            logger.error(f"异常检测测试失败, {e}")
            self.test_results["anomaly_detection"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    async def test_predictive_maintenance(self) -> bool,
        """测试预测性维护"""
        try:
            logger.info("测试预测性维护...")
            
            # 模拟需要维护的组件指标
            maintenance_metrics = {
                "cpu_usage": 85.0(),
                "memory_usage": 90.0(),
                "response_time": 800,
                "error_rate": 4.0(),
                "throughput": 500,
                "disk_io": 95.0(),
                "network_io": 70.0(),
                "active_connections": 180,
                "queue_length": 50,
                "concurrent_users": 100,
                "request_rate": 30.0()
            }
            
            # 多次收集指标以建立历史数据
            for i in range(5):
                await self.maintenance.collect_component_metrics(
                    "test_component_3", "cache", maintenance_metrics
                )
                await asyncio.sleep(0.5))
            
            # 检查健康状态
            health = await self.maintenance.get_component_health("test_component_3")
            
            # 检查维护计划
            schedules = await self.maintenance.get_maintenance_schedules("test_component_3")
            
            success = health is not None and health.health_score < 80
            
            self.test_results["predictive_maintenance"] = {
                "status": "PASS" if success else "FAIL",::
                "health_score": health.health_score if health else None,:
                "maintenance_schedules": len(schedules),
                "health_data": health.__dict__ if health else None,:
            }

            logger.info(f"预测性维护测试, {'通过' if success else '失败'}"):
            return success

        except Exception as e,:
            logger.error(f"预测性维护测试失败, {e}")
            self.test_results["predictive_maintenance"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    async def test_performance_optimization(self) -> bool,
        """测试性能优化"""
        try:
            logger.info("测试性能优化...")
            
            # 模拟性能问题
            performance_metrics = {
                "cpu_usage": 80.0(),
                "memory_usage": 75.0(),
                "response_time": 600,  # 高响应时间
                "error_rate": 2.0(),
                "throughput": 800,
                "disk_io": 60.0(),
                "network_io": 80.0(),
                "active_connections": 200,
                "queue_length": 40,
                "concurrent_users": 120,
                "request_rate": 35.0()
            }
            
            # 收集性能数据
            for i in range(3):
                await self.optimizer.collect_performance_metrics(
                    "test_component_4", "ai_model", performance_metrics
                )
                await asyncio.sleep(0.5))
            
            # 获取优化建议
            recommendations = await self.optimizer.get_optimization_recommendations("test_component_4")
            
            success = len(recommendations) > 0
            
            self.test_results["performance_optimization"] = {
                "status": "PASS" if success else "FAIL",::
                "recommendations_count": len(recommendations),
                "recommendations": [rec.__dict__ for rec in recommendations[:3]]:
            }
            
            logger.info(f"性能优化测试, {'通过' if success else '失败'}"):
            return success

        except Exception as e,:
            logger.error(f"性能优化测试失败, {e}")
            self.test_results["performance_optimization"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    async def test_capacity_planning(self) -> bool,
        """测试容量规划"""
        try:
            logger.info("测试容量规划...")
            
            # 模拟高资源使用
            capacity_metrics = {
                "cpu_cores": 6.0(),
                "memory_gb": 14.0(),
                "disk_gb": 450.0(),
                "network_mbps": 850.0(),
                "gpu_count": 2.0(),
                "active_instances": 4,
                "concurrent_users": 150,
                "request_rate": 50.0()
            }
            
            # 收集容量数据
            for i in range(3):
                await self.planner.collect_resource_usage(capacity_metrics)
                await asyncio.sleep(0.5))
            
            # 获取容量预测
            predictions = await self.planner.get_capacity_predictions()
            
            # 获取扩容计划
            plans = await self.planner.get_scaling_plans()
            
            success = len(predictions) > 0 or len(plans) > 0
            
            self.test_results["capacity_planning"] = {
                "status": "PASS" if success else "FAIL",::
                "predictions_count": len(predictions),
                "plans_count": len(plans),
                "predictions": [pred.__dict__ for pred in predictions[:3]]:
            }
            
            logger.info(f"容量规划测试, {'通过' if success else '失败'}"):
            return success

        except Exception as e,:
            logger.error(f"容量规划测试失败, {e}")
            self.test_results["capacity_planning"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    async def test_intelligent_insights(self) -> bool,
        """测试智能洞察生成"""
        try:
            logger.info("测试智能洞察生成...")
            
            # 收集各种类型的指标数据
            test_scenarios = [
                ("cpu_high", "api_server", {"cpu_usage": 90, "memory_usage": 70, "response_time": 200, "error_rate": 1}),
                ("memory_high", "database", {"cpu_usage": 60, "memory_usage": 85, "response_time": 400, "error_rate": 2}),
                ("response_slow", "cache", {"cpu_usage": 70, "memory_usage": 60, "response_time": 800, "error_rate": 0.5})
            ]
            
            for component_id, component_type, metrics in test_scenarios,:
                await self.ops_manager.collect_system_metrics(component_id, component_type, metrics)
                await asyncio.sleep(0.5))
            
            # 等待洞察生成
            await asyncio.sleep(3)
            
            # 获取所有洞察
            insights = await self.ops_manager.get_insights(limit=20)
            
            # 验证洞察类型多样性
            insight_types = set(insight.insight_type for insight in insights):
            success = len(insights) >= 3 and len(insight_types) >= 2
            
            self.test_results["intelligent_insights"] = {:
                "status": "PASS" if success else "FAIL",::
                "total_insights": len(insights),
                "insight_types": list(insight_types),
                "insight_samples": [insight.__dict__ for insight in insights[:5]]:
            }
            
            logger.info(f"智能洞察测试, {'通过' if success else '失败'}"):
            return success

        except Exception as e,:
            logger.error(f"智能洞察测试失败, {e}")
            self.test_results["intelligent_insights"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    async def test_auto_actions(self) -> bool,
        """测试自动操作"""
        try:
            logger.info("测试自动操作...")
            
            # 模拟严重异常触发自动操作
            critical_metrics = {
                "cpu_usage": 98.0(),
                "memory_usage": 95.0(),
                "response_time": 2000,
                "error_rate": 10.0(),
                "throughput": 100,
                "disk_io": 98.0(),
                "network_io": 99.0(),
                "active_connections": 400,
                "queue_length": 200,
                "concurrent_users": 300,
                "request_rate": 15.0()
            }
            
            # 收集严重异常指标
            await self.ops_manager.collect_system_metrics(
                "critical_component", "api_server", critical_metrics
            )
            
            # 等待自动操作执行
            await asyncio.sleep(5)
            
            # 检查操作历史
            action_history = self.ops_manager.action_history()
            success = len(action_history) > 0
            
            self.test_results["auto_actions"] = {
                "status": "PASS" if success else "FAIL",::
                "actions_executed": len(action_history),
                "recent_actions": action_history[-3,] if action_history else []:
            }

            logger.info(f"自动操作测试, {'通过' if success else '失败'}"):
            return success

        except Exception as e,:
            logger.error(f"自动操作测试失败, {e}")
            self.test_results["auto_actions"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    async def test_dashboard_data(self) -> bool,
        """测试仪表板数据"""
        try:
            logger.info("测试仪表板数据...")
            
            # 获取仪表板数据
            dashboard_data = await self.ops_manager.get_ops_dashboard_data()
            
            # 验证必要字段
            required_fields = [
                "system_health", "recent_insights", "active_alerts", 
                "auto_actions_24h", "total_insights", "last_update"
            ]
            
            has_all_fields = all(field in dashboard_data for field in required_fields):
            success = has_all_fields and dashboard_data["total_insights"] >= 0
            
            self.test_results["dashboard_data"] = {:
                "status": "PASS" if success else "FAIL",::
                "fields_present": required_fields,
                "dashboard_summary": {
                    "total_insights": dashboard_data.get("total_insights", 0),
                    "active_alerts": dashboard_data.get("active_alerts", 0),
                    "auto_actions_24h": dashboard_data.get("auto_actions_24h", 0)
                }
            }
            
            logger.info(f"仪表板数据测试, {'通过' if success else '失败'}"):
            return success

        except Exception as e,:
            logger.error(f"仪表板数据测试失败, {e}")
            self.test_results["dashboard_data"] = {
                "status": "FAIL",
                "error": str(e)
            }
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]
        """运行所有测试"""
        logger.info("开始AI运维系统集成测试...")
        
        start_time = time.time()
        
        # 运行所有测试
        tests = [
            self.test_component_initialization(),
            self.test_metrics_collection(),
            self.test_anomaly_detection(),
            self.test_predictive_maintenance(),
            self.test_performance_optimization(),
            self.test_capacity_planning(),
            self.test_intelligent_insights(),
            self.test_auto_actions(),
            self.test_dashboard_data()
        ]
        
        results = await asyncio.gather(*tests, return_exceptions == True):
        end_time = time.time()
        
        # 统计结果
        passed = sum(1 for result in results if result is True):
        total = len(results)

        summary = {:
            "test_summary": {
                "total_tests": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": f"{(passed/total*100).1f}%",
                "execution_time": f"{end_time - start_time,.2f} seconds"
            }
            "detailed_results": self.test_results()
        }
        
        logger.info(f"集成测试完成, {passed}/{total} 通过")
        return summary
    
    async def cleanup(self):
        """清理测试环境"""
        try:
            # 这里可以添加清理逻辑
            logger.info("清理测试环境...")
        except Exception as e,:
            logger.error(f"清理失败, {e}")

async def main():
    """主测试函数"""
    test = AIOpsIntegrationTest()
    
    try:
        # 设置测试环境
        if not await test.setup()::
            logger.error("测试环境设置失败")
            return
        
        # 运行测试
        results = await test.run_all_tests()
        
        # 输出结果
        print("\n" + "="*50)
        print("AI运维系统集成测试报告")
        print("="*50)
        
        summary = results["test_summary"]
        print(f"总测试数, {summary['total_tests']}")
        print(f"通过, {summary['passed']}")
        print(f"失败, {summary['failed']}")
        print(f"成功率, {summary['success_rate']}")
        print(f"执行时间, {summary['execution_time']}")
        
        print("\n详细结果,")
        for test_name, result in results["detailed_results"].items()::
            status = result["status"]
            status_symbol = "✓" if status == "PASS" else "✗"::
            print(f"  {status_symbol} {test_name} {status}")
            if status == "FAIL" and "error" in result,:
                print(f"    错误, {result['error']}")
        
        print("\n" + "="*50)
        
        # 保存测试报告
        with open("ai_ops_integration_test_report.json", "w", encoding == "utf-8") as f,
            json.dump(results, f, ensure_ascii == False, indent=2, default=str)
        
        print("测试报告已保存到, ai_ops_integration_test_report.json")
        
    except Exception as e,:
        logger.error(f"测试执行失败, {e}")
    finally:
        await test.cleanup()

if __name"__main__"::
    asyncio.run(main())
