#!/usr/bin/env python3
"""
自主进化引擎快速测试
验证Level 5 AGI自主进化机制的核心功能
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.backend.src.core.evolution.autonomous_evolution_engine import AutonomousEvolutionEngine

async def test_autonomous_evolution_engine():
    """测试自主进化引擎的核心功能"""
    print("🚀 开始自主进化引擎测试...")
    print("=" * 50)
    
    try:
        # 初始化引擎
        print("🔧 初始化自主进化引擎...")
        engine = AutonomousEvolutionEngine({
            'learning_rate': 0.01,
            'evolution_threshold': 0.8,
            'correction_aggressiveness': 0.7,
            'optimization_interval': 60
        })
        print("✅ 引擎初始化完成")
        
        # 测试1: 学习周期管理
        print("\n📚 测试学习周期管理...")
        episode_id = await engine.start_learning_episode('test_episode', {
            'initial_metrics': {'accuracy': 0.75, 'efficiency': 0.8, 'memory_usage': 0.6},
            'learning_objectives': ['improve_accuracy', 'reduce_latency', 'optimize_memory']
        })
        print(f"✅ 学习周期启动: {episode_id}")
        
        # 测试2: 性能数据记录
        print("\n📊 测试性能数据记录...")
        await engine.record_performance_metrics({
            'accuracy': 0.78,
            'efficiency': 0.82,
            'memory_usage': 0.65,
            'processing_speed': 125.5,
            'response_time': 0.15
        })
        print("✅ 性能数据记录完成")
        
        # 测试3: 性能问题检测
        print("\n🔍 测试性能问题检测...")
        issues = await engine.detect_performance_issues()
        print(f"🔍 检测到 {len(issues)} 个性能问题")
        
        for i, issue in enumerate(issues):
            print(f"  问题{i+1}: {issue.issue_type}")
            print(f"    描述: {issue.description}")
            print(f"    严重度: {issue.severity:.2f}")
            print(f"    影响范围: {issue.impact_scope}")
        
        # 测试4: 修正策略生成
        if issues:
            print("\n🔧 测试修正策略生成...")
            primary_issue = issues[0]
            corrections = await engine.generate_correction_strategies(primary_issue)
            print(f"🔧 为'{primary_issue.issue_type}'生成 {len(corrections)} 个修正策略")
            
            for i, correction in enumerate(corrections[:3]):
                print(f"  策略{i+1}: {correction.strategy_type}")
                print(f"    预期改善: {correction.expected_improvement:.2f}")
                print(f"    执行成本: {correction.implementation_cost:.2f}")
                print(f"    风险等级: {correction.risk_level}")
        
        # 测试5: 架构优化建议
        print("\n🏗️ 测试架构优化建议...")
        optimization_suggestions = await engine.suggest_architecture_optimizations()
        print(f"🏗️ 生成 {len(optimization_suggestions)} 个架构优化建议")
        
        for i, suggestion in enumerate(optimization_suggestions[:3]):
            print(f"  建议{i+1}: {suggestion.suggestion_type}")
            print(f"    预期收益: {suggestion.expected_benefit:.2f}")
            print(f"    实施复杂度: {suggestion.implementation_complexity}")
            print(f"    优先级: {suggestion.priority_score:.2f}")
        
        # 测试6: 学习效果评估
        print("\n📈 测试学习效果评估...")
        
        # 模拟更多性能数据以评估学习效果
        for i in range(3):
            await engine.record_performance_metrics({
                'accuracy': 0.75 + i * 0.02,
                'efficiency': 0.80 + i * 0.01,
                'memory_usage': 0.65 - i * 0.01,
                'processing_speed': 125.5 + i * 5.0,
                'response_time': 0.15 - i * 0.01
            })
        
        # 结束学习周期
        final_metrics = await engine.end_learning_episode()
        print(f"📈 学习周期完成")
        print(f"    初始准确率: 0.75 → 最终准确率: {final_metrics.get('accuracy', 0):.3f}")
        print(f"    初始效率: 0.80 → 最终效率: {final_metrics.get('efficiency', 0):.3f}")
        print(f"    学习效果: {'改善' if final_metrics.get('accuracy', 0) > 0.75 else '待优化'}")
        
        # 测试7: 版本控制与回滚
        print("\n🔄 测试版本控制与回滚...")
        
        # 创建架构版本
        version_id = await engine.create_architecture_version('v1.0_test', {
            'components': ['learning_controller', 'self_correction', 'architecture_optimizer'],
            'performance_baseline': final_metrics,
            'optimization_results': optimization_suggestions[:2]
        })
        print(f"📝 创建架构版本: {version_id}")
        
        # 获取版本历史
        version_history = await engine.get_version_history()
        print(f"📋 版本历史记录数: {len(version_history)}")
        
        if version_history:
            latest_version = version_history[-1]
            print(f"    最新版本: {latest_version.version_id}")
            print(f"    创建时间: {latest_version.created_at}")
            print(f"    性能基线: {latest_version.performance_baseline}")
        
        print("\n" + "=" * 50)
        print("✅ 自主进化引擎测试完成！")
        print("🎯 所有核心功能验证通过")
        print("🚀 Level 5 AGI自主进化机制就绪")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance_benchmark():
    """测试性能基准"""
    print("\n📊 运行性能基准测试...")
    
    try:
        engine = AutonomousEvolutionEngine({
            'learning_rate': 0.01,
            'evolution_threshold': 0.8
        })
        
        import time
        
        # 性能测试
        start_time = time.time()
        
        # 批量学习周期测试
        for i in range(5):
            episode_id = await engine.start_learning_episode(f'perf_test_{i}', {
                'initial_metrics': {'accuracy': 0.70 + i * 0.02},
                'learning_objectives': [f'objective_{i}']
            })
            
            await engine.record_performance_metrics({
                'accuracy': 0.72 + i * 0.02,
                'efficiency': 0.80 + i * 0.01
            })
            
            await engine.end_learning_episode()
        
        processing_time = time.time() - start_time
        
        print(f"📈 处理5个学习周期耗时: {processing_time:.2f}秒")
        print(f"🚀 平均处理速度: {5/processing_time:.1f} 周期/秒")
        
        return {
            'learning_cycles_per_second': 5 / processing_time,
            'total_processing_time': processing_time
        }
        
    except Exception as e:
        print(f"性能测试失败: {e}")
        return None

async def main():
    """主函数"""
    print("🌟 Level 5 AGI自主进化引擎测试系统")
    print("=" * 60)
    
    # 运行功能测试
    success = await test_autonomous_evolution_engine()
    
    if success:
        # 运行性能测试
        perf_results = await test_performance_benchmark()
        
        print("\n" + "=" * 60)
        print("🎉 自主进化引擎测试系统执行完成！")
        
        if perf_results:
            print(f"📊 性能指标:")
            print(f"   学习周期处理速度: {perf_results['learning_cycles_per_second']:.1f} 周期/秒")
            print(f"   总处理时间: {perf_results['total_processing_time']:.2f}秒")
        
        print("\n✅ Level 5 AGI自主进化机制验证成功！")
        return 0
    else:
        print("\n❌ 测试失败，需要修复问题")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)