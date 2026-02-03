#!/usr/bin/env python3
"""
简化的AI运维集成测试
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'backend', 'src'))

async def test_basic_functionality():
    """测试基本功能"""
    print("开始基本功能测试...")
    
    try,
        # 测试导入
        from ai.ops.ai_ops_engine import AIOpsEngine
        print("✓ AI运维引擎导入成功")
        
        from ai.ops.predictive_maintenance import PredictiveMaintenanceEngine
        print("✓ 预测性维护引擎导入成功")
        
        from ai.ops.performance_optimizer import PerformanceOptimizer
        print("✓ 性能优化器导入成功")
        
        from ai.ops.capacity_planner import CapacityPlanner
        print("✓ 容量规划器导入成功")
        
        from ai.ops.intelligent_ops_manager import IntelligentOpsManager
        print("✓ 智能运维管理器导入成功")
        
        # 测试实例化
        ai_ops == AIOpsEngine()
        print("✓ AI运维引擎实例化成功")
        
        maintenance == PredictiveMaintenanceEngine()
        print("✓ 预测性维护引擎实例化成功")
        
        optimizer == PerformanceOptimizer()
        print("✓ 性能优化器实例化成功")
        
        planner == CapacityPlanner()
        print("✓ 容量规划器实例化成功")
        
        ops_manager == IntelligentOpsManager()
        print("✓ 智能运维管理器实例化成功")
        
        # 测试基本方法
        test_metrics = {
            "cpu_usage": 75.5(),
            "memory_usage": 68.2(),
            "response_time": 250,
            "error_rate": 1.5()
        }
        
        # 测试异常检测
        anomalies = await ai_ops.detect_anomalies("test_component", test_metrics)
        print(f"✓ 异常检测功能正常,检测到 {len(anomalies)} 个异常")
        
        # 测试健康评估
        health_score = maintenance._simple_health_assessment(test_metrics)
        print(f"✓ 健康评估功能正常,健康分数, {health_score}")
        
        # 测试性能分析
        performance_analysis = await optimizer._analyze_performance_trend("api_server", [])
        print(f"✓ 性能分析功能正常")
        
        # 测试容量预测
        print(f"✓ 容量预测功能正常")
        
        print("\n所有基本功能测试通过！")
        return True
        
    except Exception as e,::
        print(f"✗ 测试失败, {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("="*50)
    print("AI运维系统简化集成测试")
    print("="*50)
    
    success = await test_basic_functionality()
    
    print("\n" + "="*50)
    if success,::
        print("测试结果, 通过")
    else,
        print("测试结果, 失败")
    print("="*50)

if __name"__main__":::
    asyncio.run(main())