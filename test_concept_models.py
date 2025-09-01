#!/usr/bin/env python3
"""
测试所有概念模型的脚本
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

async def test_concept_models():
    """测试所有概念模型"""
    print("=== Unified AI Project - 概念模型测试 ===\n")
    
    # 测试环境模拟器
    print("1. 测试环境模拟器...")
    try:
        from apps.backend.src.core_ai.concept_models.environment_simulator import EnvironmentSimulator, State, Action
        simulator = EnvironmentSimulator()
        
        # 创建测试数据
        state = State(time_step=0, variables={"temperature": 22.0, "humidity": 50.0})
        action = Action(name="increase_temperature", parameters={"amount": 2.0})
        
        # 运行模拟
        result = await simulator.simulate_action_consequences(state, action)
        print(f"   ✓ 环境模拟器测试通过")
        print(f"   预测温度: {result['predicted_state'].variables.get('temperature', 0):.1f}°C")
        print(f"   不确定性: {result['uncertainty']:.2f}")
    except Exception as e:
        print(f"   ❌ 环境模拟器测试失败: {e}")
        return False
    
    # 测试因果推理引擎
    print("\n2. 测试因果推理引擎...")
    try:
        from apps.backend.src.core_ai.concept_models.causal_reasoning_engine import CausalReasoningEngine, Observation, CausalRelationship
        engine = CausalReasoningEngine()
        
        # 创建测试数据
        observation = Observation(
            id="test_obs",
            variables={"temperature": 22.0, "comfort": 0.7},
            relationships=[CausalRelationship("temperature", "comfort", 0.8, 0.9)],
            timestamp=1.0
        )
        
        # 学习因果关系
        relationships = await engine.learn_causal_relationships([observation])
        print(f"   ✓ 因果推理引擎测试通过")
        print(f"   学习到 {len(relationships)} 个因果关系")
    except Exception as e:
        print(f"   ❌ 因果推理引擎测试失败: {e}")
        return False
    
    # 测试自适应学习控制器
    print("\n3. 测试自适应学习控制器...")
    try:
        from apps.backend.src.core_ai.concept_models.adaptive_learning_controller import AdaptiveLearningController, TaskContext
        controller = AdaptiveLearningController()
        
        # 创建任务上下文
        task_context = TaskContext(
            task_id="test_task",
            complexity_level=0.5,
            domain="test",
            description="Test task"
        )
        
        # 适应学习策略
        strategy = await controller.adapt_learning_strategy(task_context)
        print(f"   ✓ 自适应学习控制器测试通过")
        print(f"   选择策略: {strategy['strategy_name']}")
    except Exception as e:
        print(f"   ❌ 自适应学习控制器测试失败: {e}")
        return False
    
    # 测试Alpha深度模型
    print("\n4. 测试Alpha深度模型...")
    try:
        from apps.backend.src.core_ai.concept_models.alpha_deep_model import AlphaDeepModel, DeepParameter, HAMGist, RelationalContext, Modalities
        model = AlphaDeepModel("test_alpha_model.db")
        
        # 创建深度参数
        deep_param = DeepParameter(
            source_memory_id="test_mem_001",
            timestamp="2025-01-01T00:00:00Z",
            base_gist=HAMGist(summary="Test memory", keywords=["test"], original_length=100),
            relational_context=RelationalContext(entities=["Test"], relationships=[]),
            modalities=Modalities(text_confidence=0.9)
        )
        
        # 学习和压缩
        await model.learn(deep_param)
        compressed = await model.compress(deep_param)
        print(f"   ✓ Alpha深度模型测试通过")
        print(f"   压缩后大小: {len(compressed)} 字节")
    except Exception as e:
        print(f"   ❌ Alpha深度模型测试失败: {e}")
        return False
    
    # 测试统一符号空间
    print("\n5. 测试统一符号空间...")
    try:
        from apps.backend.src.core_ai.concept_models.unified_symbolic_space import UnifiedSymbolicSpace, SymbolType
        space = UnifiedSymbolicSpace("test_symbolic_space.db")
        
        # 添加符号
        symbol_id = await space.add_symbol("TestSymbol", SymbolType.CONCEPT, {"test": True})
        symbol = await space.get_symbol_by_name("TestSymbol")
        print(f"   ✓ 统一符号空间测试通过")
        print(f"   创建符号: {symbol.name if symbol else 'None'}")
    except Exception as e:
        print(f"   ❌ 统一符号空间测试失败: {e}")
        return False
    
    # 运行集成测试
    print("\n6. 运行集成测试...")
    try:
        from apps.backend.src.core_ai.concept_models.integration_test import run_integration_tests
        success = await run_integration_tests()
        if success:
            print("   ✓ 集成测试通过")
        else:
            print("   ❌ 集成测试失败")
            return False
    except Exception as e:
        print(f"   ❌ 集成测试失败: {e}")
        return False
    
    print("\n🎉 所有概念模型测试通过！")
    return True

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_concept_models())
    sys.exit(0 if success else 1)