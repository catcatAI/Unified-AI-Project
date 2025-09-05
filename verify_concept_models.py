#!/usr/bin/env python3
"""
验证所有概念模型是否可以正常导入
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

def verify_imports():
    """验证所有概念模型的导入"""
    print("=== 验证概念模型导入 ===\n")
    
    # 验证环境模拟器
    print("1. 验证环境模拟器...")
    try:
        from apps.backend.src.ai.concept_models.environment_simulator import EnvironmentSimulator, State, Action
        print("   ✓ 环境模拟器导入成功")
    except Exception as e:
        print(f"   ❌ 环境模拟器导入失败: {e}")
        return False
    
    # 验证因果推理引擎
    print("\n2. 验证因果推理引擎...")
    try:
        from apps.backend.src.ai.concept_models.causal_reasoning_engine import CausalReasoningEngine, Observation, CausalRelationship
        print("   ✓ 因果推理引擎导入成功")
    except Exception as e:
        print(f"   ❌ 因果推理引擎导入失败: {e}")
        return False
    
    # 验证自适应学习控制器
    print("\n3. 验证自适应学习控制器...")
    try:
        from apps.backend.src.ai.concept_models.adaptive_learning_controller import AdaptiveLearningController, TaskContext
        print("   ✓ 自适应学习控制器导入成功")
    except Exception as e:
        print(f"   ❌ 自适应学习控制器导入失败: {e}")
        return False
    
    # 验证Alpha深度模型
    print("\n4. 验证Alpha深度模型...")
    try:
        from apps.backend.src.ai.concept_models.alpha_deep_model import AlphaDeepModel, DeepParameter
        print("   ✓ Alpha深度模型导入成功")
    except Exception as e:
        print(f"   ❌ Alpha深度模型导入失败: {e}")
        return False
    
    # 验证统一符号空间
    print("\n5. 验证统一符号空间...")
    try:
        from apps.backend.src.ai.concept_models.unified_symbolic_space import UnifiedSymbolicSpace, SymbolType
        print("   ✓ 统一符号空间导入成功")
    except Exception as e:
        print(f"   ❌ 统一符号空间导入失败: {e}")
        return False
    
    # 验证集成测试
    print("\n6. 验证集成测试...")
    try:
        from apps.backend.src.ai.concept_models.integration_test import ConceptModelIntegrationTest
        print("   ✓ 集成测试导入成功")
    except Exception as e:
        print(f"   ❌ 集成测试导入失败: {e}")
        return False
    
    print("\n🎉 所有概念模型导入验证通过！")
    return True

if __name__ == "__main__":
    success = verify_imports()
    sys.exit(0 if success else 1)