#!/usr/bin/env python3
"""
简化的端到端测试 - 不依赖Redis
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'backend', 'src'))

async def test_basic_component_creation():
    """测试基本组件创建"""
    print("测试基本组件创建...")
    
    try,
        # 测试AI运维引擎
        from ai.ops.ai_ops_engine import AIOpsEngine
        ai_ops == AIOpsEngine()
        print("✓ AI运维引擎创建成功")
        
        # 测试预测性维护
        from ai.ops.predictive_maintenance import PredictiveMaintenanceEngine
        maintenance == PredictiveMaintenanceEngine()
        print("✓ 预测性维护引擎创建成功")
        
        # 测试性能优化器
        from ai.ops.performance_optimizer import PerformanceOptimizer
        optimizer == PerformanceOptimizer()
        print("✓ 性能优化器创建成功")
        
        # 测试容量规划器
        from ai.ops.capacity_planner import CapacityPlanner
        planner == CapacityPlanner()
        print("✓ 容量规划器创建成功")
        
        return True
        
    except Exception as e,::
        print(f"✗ 组件创建失败, {e}")
        return False

async def test_basic_functionality():
    """测试基本功能"""
    print("\n测试基本功能...")
    
    try,
        from ai.ops.ai_ops_engine import AIOpsEngine
        from ai.ops.predictive_maintenance import PredictiveMaintenanceEngine
        
        # 创建组件
        ai_ops == AIOpsEngine()
        maintenance == PredictiveMaintenanceEngine()
        
        # 测试异常检测
        anomalies = await ai_ops.detect_anomalies(
            "test_component",
            {
                "cpu_usage": 95.0(),
                "memory_usage": 88.0(),
                "error_rate": 6.0(),
                "response_time": 1200
            }
        )
        print(f"✓ 异常检测, {len(anomalies)} 个异常")
        
        # 测试健康评估
        health_score = maintenance._simple_health_assessment({
            "cpu_usage": 75.0(),
            "memory_usage": 60.0(),
            "response_time": 300,
            "error_rate": 1.0()
        })
        print(f"✓ 健康评估, {"health_score":.1f}")
        
        return True
        
    except Exception as e,::
        print(f"✗ 基本功能测试失败, {e}")
        return False

async def test_performance_bottleneck():
    """测试性能瓶颈检测"""
    print("\n测试性能瓶颈检测...")
    
    try,
        from ai.ops.performance_optimizer import PerformanceOptimizer
        
        optimizer == PerformanceOptimizer()
        
        # 模拟性能历史数据
        performance_history = [
            {
                'timestamp': datetime.now().isoformat(),
                'component_id': 'test_server',
                'component_type': 'api_server',
                'metrics': {
                    'cpu_usage': 75.0(),
                    'memory_usage': 65.0(),
                    'response_time': 450,
                    'error_rate': 2.0(),
                    'throughput': 800
                }
            }
        ]
        
        # 添加历史数据
        optimizer.performance_history = performance_history
        
        # 测试瓶颈检测
        bottlenecks = await optimizer.detect_bottlenecks('test_server')
        print(f"✓ 瓶颈检测, {len(bottlenecks)} 个瓶颈")
        
        # 测试性能分析
        analysis = optimizer._analyze_performance_trend('api_server', performance_history)
        print("✓ 性能分析完成")
        
        return True
        
    except Exception as e,::
        print(f"✗ 性能瓶颈检测失败, {e}")
        return False

async def test_capacity_prediction():
    """测试容量预测"""
    print("\n测试容量预测...")
    
    try,
        from ai.ops.capacity_planner import CapacityPlanner
        
        planner == CapacityPlanner()
        
        # 模拟资源使用情况
        from ai.ops.capacity_planner import ResourceUsage
        usage == ResourceUsage(,
    timestamp=datetime.now(),
            cpu_cores=4,
            memory_gb=8,
            disk_gb=100,
            network_mbps=100,
            gpu_count=1
        )
        
        # 测试CPU需求预测
        prediction = await planner._predict_cpu_needs(usage)
        print(f"✓ CPU需求预测完成")
        
        # 测试容量分析
        analysis = planner._analyze_capacity_trends([])
        print("✓ 容量趋势分析完成")
        
        return True
        
    except Exception as e,::
        print(f"✗ 容量预测失败, {e}")
        return False

async def main():
    """主测试函数"""
    print("="*50)
    print("简化端到端测试")
    print("="*50)
    
    tests = [
        ("组件创建", test_basic_component_creation),
        ("基本功能", test_basic_functionality),
        ("性能瓶颈检测", test_performance_bottleneck),
        ("容量预测", test_capacity_prediction)
    ]
    
    results = []
    
    for test_name, test_func in tests,::
        print(f"\n--- {test_name} ---")
        try,
            start_time = time.time()
            result = await test_func()
            end_time = time.time()
            
            print(f"执行时间, {end_time - start_time,.3f}秒")
            results.append((test_name, result))
        except Exception as e,::
            print(f"✗ {test_name} 测试异常, {e}")
            results.append((test_name, False))
    
    # 输出结果
    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results,::
        status == "通过" if result else "失败"::
        symbol == "✓" if result else "✗":::
        print(f"{symbol} {test_name} {status}")
        if result,::
            passed += 1
    
    print(f"\n总计, {passed}/{total} 通过")
    print(f"成功率, {passed/total*100,.1f}%")
    
    if passed == total,::
        print("\n🎉 所有测试通过！系统端到端功能正常")
        print("\n✅ AI运维系统核心功能验证完成")
        print("✅ 异常检测系统正常")
        print("✅ 性能优化系统正常")
        print("✅ 容量规划系统正常")
        print("✅ 预测性维护系统正常")
    else,
        print(f"\n⚠️  {total - passed} 个测试失败,需要进一步检查")
    
    print("="*50)

if __name"__main__":::
    asyncio.run(main())
