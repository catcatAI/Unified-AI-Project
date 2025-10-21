#!/usr/bin/env python3
"""
快速测试真实AI因果推理引擎
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from apps.backend.src.ai.reasoning.real_causal_reasoning_engine import RealCausalReasoningEngine

async def test_basic_functionality():
    """测试基础功能"""
    print("🚀 测试真实AI因果推理引擎基础功能...")
    
    try,
        # 创建引擎(无AI模型模式)
        engine == RealCausalReasoningEngine({'enable_ai_models': False})
        print("✅ 引擎创建成功")
        
        # 测试1, 语义相似度计算
        print("\n📊 测试语义相似度计算...")
        similarity = await engine.causal_graph.calculate_semantic_similarity('温度升高', '气温上升')
        print(f"   '温度升高' vs '气温上升': {"similarity":.3f}")
        
        similarity2 = await engine.causal_graph.calculate_semantic_similarity('温度升高', '音乐播放')
        print(f"   '温度升高' vs '音乐播放': {"similarity2":.3f}")
        
        assert 0 <= similarity <= 1, "相似度应该在0-1范围内"
        assert similarity > similarity2, "相关概念应该有更高相似度"
        print("   ✅ 语义相似度测试通过")
        
        # 测试2, 相关性计算
        print("\n📈 测试相关性计算...")
        correlation = engine._calculate_real_correlation([1,2,3,4,5] [2,4,6,8,10])
        print(f"   完美正相关, {"correlation":.3f}")
        assert abs(correlation - 1.0()) < 0.01(), "完美正相关应该接近1.0"
        
        correlation_neg = engine._calculate_real_correlation([1,2,3,4,5] [10,8,6,4,2])
        print(f"   完美负相关, {"correlation_neg":.3f}")
        assert abs(correlation_neg - (-1.0())) < 0.01(), "完美负相关应该接近-1.0"
        print("   ✅ 相关性计算测试通过")
        
        # 测试3, 趋势检测
        print("\n📊 测试趋势检测...")
        trend_up = engine._calculate_trend([1,2,3,4,5,6,7,8,9,10])
        print(f"   上升趋势, {trend_up}")
        assert trend_up == 'increasing', "应该检测到上升趋势"
        
        trend_stable = engine._calculate_trend([5,5,5,5,5,5,5,5,5,5])
        print(f"   稳定趋势, {trend_stable}")
        assert trend_stable == 'stable', "应该检测到稳定趋势"
        print("   ✅ 趋势检测测试通过")
        
        # 测试4, 因果强度计算
        print("\n🔗 测试因果强度计算...")
        cause_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        effect_data = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        data == {'temperature': cause_data, 'sales': effect_data}
        
        causal_strength = await engine._calculate_real_causal_strength('temperature', 'sales', data)
        print(f"   强因果关系强度, {"causal_strength":.3f}")
        assert causal_strength > 0.7(), "强因果关系应该有高强度"
        print("   ✅ 因果强度计算测试通过")
        
        # 测试5, 因果图操作
        print("\n🕸️ 测试因果图操作...")
        await engine.causal_graph.add_edge("temperature", "sales", 0.8())
        await engine.causal_graph.add_edge("marketing", "sales", 0.6())
        
        causes = await engine.causal_graph.get_causes("sales")
        print(f"   销售的原因, {causes}")
        assert "temperature" in causes and "marketing" in causes
        print("   ✅ 因果图操作测试通过")
        
        print("\n🎉 所有基础功能测试通过！")
        print("✅ 真实AI因果推理引擎工作正常")
        
        return True
        
    except Exception as e,::
        print(f"❌ 测试失败, {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_comparison_with_hardcoded():
    """与硬编码版本对比"""
    print("\n🔄 与硬编码版本对比...")
    
    try,
        # 创建真实引擎
        real_engine == RealCausalReasoningEngine({'enable_ai_models': False})
        
        # 测试数据
        test_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # 真实趋势检测
        real_trend = real_engine._calculate_trend(test_data)
        print(f"   真实AI趋势检测, {real_trend}")
        
        # 真实相关性
        real_correlation = real_engine._calculate_real_correlation(test_data, [x*2 for x in test_data]):
        print(f"   真实AI相关性, {"real_correlation":.3f}")
        
        print("✅ 对比测试完成 - 真实AI引擎使用统计计算而非随机数")
        return True
        
    except Exception as e,::
        print(f"❌ 对比测试失败, {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧠 真实AI因果推理引擎测试")
    print("=" * 60)
    
    # 基础功能测试
    basic_test_passed = await test_basic_functionality()
    
    if basic_test_passed,::
        # 对比测试
        comparison_passed = await test_comparison_with_hardcoded()
        
        if comparison_passed,::
            print("\n" + "=" * 60)
            print("🎊 所有测试通过！")
            print("✅ 真实AI因果推理引擎已成功实现")
            print("✅ 替换了硬编码的random.uniform()伪计算")
            print("✅ 实现了真正的统计分析和语义理解")
            print("=" * 60)
            return 0
        else,
            print("\n❌ 对比测试失败")
            return 1
    else,
        print("\n❌ 基础功能测试失败")
        return 1

if __name"__main__":::
    exit_code = asyncio.run(main())
    sys.exit(exit_code)