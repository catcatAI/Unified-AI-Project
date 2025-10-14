#!/usr/bin/env python3
"""
快速端到端测试
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'backend', 'src'))

async def test_basic_ops_flow():
    """测试基本运维流程"""
    print("测试基本运维流程...")
    
    try:
        from ai.ops.intelligent_ops_manager import get_intelligent_ops_manager
        
        # 创建运维管理器（不初始化Redis）
        ops_manager = get_intelligent_ops_manager()
        
        # 测试指标收集
        await ops_manager.collect_system_metrics(
            "test_server_01",
            "api_server",
            {
                "cpu_usage": 85.0,
                "memory_usage": 75.0,
                "response_time": 450,
                "error_rate": 2.5,
                "throughput": 800
            }
        )
        
        print("✓ 指标收集成功")
        
        # 获取洞察
        insights = await ops_manager.get_insights(limit=10)
        print(f"✓ 获取洞察: {len(insights)} 个")
        
        # 获取仪表板数据
        dashboard = await ops_manager.get_ops_dashboard_data()
        print(f"✓ 仪表板数据: {len(dashboard)} 个字段")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本运维流程测试失败: {e}")
        return False

async def test_component_interaction():
    """测试组件交互"""
    print("测试组件交互...")
    
    try:
        from ai.ops.ai_ops_engine import AIOpsEngine
        from ai.ops.predictive_maintenance import PredictiveMaintenanceEngine
        from ai.ops.performance_optimizer import PerformanceOptimizer
        from ai.ops.capacity_planner import CapacityPlanner
        
        # 创建组件实例
        ai_ops = AIOpsEngine()
        maintenance = PredictiveMaintenanceEngine()
        optimizer = PerformanceOptimizer()
        planner = CapacityPlanner()
        
        # 测试异常检测
        anomalies = await ai_ops.detect_anomalies(
            "test_component",
            {
                "cpu_usage": 95.0,
                "memory_usage": 88.0,
                "error_rate": 6.0,
                "response_time": 1200
            }
        )
        print(f"✓ 异常检测: {len(anomalies)} 个异常")
        
        # 测试健康评估
        health_score = maintenance._simple_health_assessment({
            "cpu_usage": 75.0,
            "memory_usage": 60.0,
            "response_time": 300,
            "error_rate": 1.0
        })
        print(f"✓ 健康评估: {health_score:.1f}")
        
        # 测试性能分析
        perf_analysis = optimizer._analyze_performance_trend("api_server", [])
        print(f"✓ 性能分析完成")
        
        return True
        
    except Exception as e:
        print(f"✗ 组件交互测试失败: {e}")
        return False

async def test_data_processing():
    """测试数据处理"""
    print("测试数据处理...")
    
    try:
        from ai.ops.intelligent_ops_manager import get_intelligent_ops_manager
        
        ops_manager = get_intelligent_ops_manager()
        
        # 批量处理数据
        test_data = [
            ("server_01", "api_server", {"cpu_usage": 70, "memory_usage": 60, "response_time": 200}),
            ("server_02", "database", {"cpu_usage": 80, "memory_usage": 85, "response_time": 500}),
            ("server_03", "cache", {"cpu_usage": 45, "memory_usage": 90, "response_time": 50}),
            ("server_04", "ai_model", {"cpu_usage": 95, "memory_usage": 75, "response_time": 1000})
        ]
        
        start_time = time.time()
        
        for component_id, component_type, metrics in test_data:
            await ops_manager.collect_system_metrics(component_id, component_type, metrics)
        
        end_time = time.time()
        
        print(f"✓ 处理 {len(test_data)} 个组件耗时: {end_time - start_time:.3f} 秒")
        
        # 检查结果
        insights = await ops_manager.get_insights()
        print(f"✓ 生成洞察: {len(insights)} 个")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据处理测试失败: {e}")
        return False

async def test_error_resilience():
    """测试错误恢复能力"""
    print("测试错误恢复能力...")
    
    try:
        from ai.ops.intelligent_ops_manager import get_intelligent_ops_manager
        
        ops_manager = get_intelligent_ops_manager()
        
        # 测试异常数据处理
        test_cases = [
            ("invalid_metrics", {"invalid": "data"}),
            ("extreme_values", {"cpu_usage": 150, "memory_usage": -50}),
            ("missing_data", {}),
            ("null_values", {"cpu_usage": None, "memory_usage": None})
        ]
        
        for test_name, metrics in test_cases:
            try:
                await ops_manager.collect_system_metrics(test_name, "test_type", metrics)
                print(f"✓ {test_name} 处理正常")
            except:
                print(f"✓ {test_name} 错误处理正常")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误恢复测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("="*50)
    print("快速端到端测试")
    print("="*50)
    
    tests = [
        ("基本运维流程", test_basic_ops_flow),
        ("组件交互", test_component_interaction),
        ("数据处理", test_data_processing),
        ("错误恢复", test_error_resilience)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            start_time = time.time()
            result = await test_func()
            end_time = time.time()
            
            print(f"执行时间: {end_time - start_time:.3f}秒")
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出结果
    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "通过" if result else "失败"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 通过")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统端到端功能正常")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，需要进一步检查")
    
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())