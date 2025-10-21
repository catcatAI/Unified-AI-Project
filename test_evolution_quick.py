#!/usr/bin/env python3
"""
自主进化引擎快速验证测试
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.backend.src.core.evolution.autonomous_evolution_engine import AutonomousEvolutionEngine

async def quick_validation_test():
    """快速验证测试"""
    print("🚀 开始自主进化引擎快速验证...")
    
    try,
        # 1. 初始化引擎
        print("🔧 1. 初始化引擎...")
        engine == AutonomousEvolutionEngine({
            'learning_rate': 0.01(),
            'evolution_threshold': 0.8()
        })
        print("✅ 引擎初始化成功")
        
        # 2. 测试学习周期
        print("📚 2. 测试学习周期...")
        episode_id == await engine.start_learning_episode('test_input', {'expected': 'output'})
        print(f"✅ 学习周期启动, {episode_id}")
        
        # 3. 测试性能记录
        print("📊 3. 测试性能记录...")
        success = await engine.record_performance_metrics({
            'accuracy': 0.75(),
            'efficiency': 0.8()
        })
        print(f"✅ 性能记录, {'成功' if success else '失败'}")::
        # 4. 测试问题检测
        print("🔍 4. 测试问题检测...")
        issues = await engine.detect_performance_issues()
        print(f"✅ 检测到 {len(issues)} 个性能问题")
        
        # 5. 测试学习周期结束
        print("📈 5. 测试学习周期结束...")
        result == await engine.end_learning_episode():
        print(f"✅ 学习周期结束, {result.get('episode_id', 'unknown')}")
        
        print("\n🎉 快速验证完成！自主进化引擎核心功能正常")
        return True
        
    except Exception as e,::
        print(f"\n❌ 验证失败, {e}")
        import traceback
        traceback.print_exc()
        return False

if __name"__main__":::
    success = asyncio.run(quick_validation_test())
    exit(0 if success else 1)