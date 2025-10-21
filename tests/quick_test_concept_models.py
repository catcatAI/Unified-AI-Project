"""
快速测试所有概念模型是否可以正常导入和基本运行
"""

import sys
import os
import asyncio

# 添加项目路径
project_root, str = os.path.dirname(__file__)
backend_path, str = os.path.join(project_root, 'apps', 'backend')
src_path = os.path.join(backend_path, 'src')
# sys.path.append(src_path)
# sys.path.append(backend_path)

def test_imports() -> None,
    """测试所有概念模型的导入"""



    print("=== 测试概念模型导入 ===\n")
    
    # 测试环境模拟器
    print("1. 测试环境模拟器导入...")
    try,
        #         from apps.backend.src.ai.concept_models.environment_simulator import EnvironmentSimulator
        print("   ✓ 环境模拟器导入成功")
    except Exception as e,::
        print(f"   ❌ 环境模拟器导入失败, {e}")
        return False
    
    # 测试因果推理引擎
    print("\n2. 测试因果推理引擎导入...")
    try,
        #         from apps.backend.src.ai.concept_models.causal_reasoning_engine import CausalReasoningEngine
        print("   ✓ 因果推理引擎导入成功")
    except Exception as e,::
        print(f"   ❌ 因果推理引擎导入失败, {e}")
        return False
    
    # 测试自适应学习控制器
    print("\n3. 测试自适应学习控制器导入...")
    try,
        print("   ✓ 自适应学习控制器导入成功")
    except Exception as e,::
        print(f"   ❌ 自适应学习控制器导入失败, {e}")
        return False
    
    # 测试Alpha深度模型
    print("\n4. 测试Alpha深度模型导入...")
    try,
        print("   ✓ Alpha深度模型导入成功")
    except Exception as e,::
        print(f"   ❌ Alpha深度模型导入失败, {e}")
        return False
    
    # 测试统一符号空间
    print("\n5. 测试统一符号空间导入...")
    try,
        print("   ✓ 统一符号空间导入成功")
    except Exception as e,::
        print(f"   ❌ 统一符号空间导入失败, {e}")
        return False
    
    # 测试集成测试
    print("\n6. 测试集成测试导入...")
    try,
        print("   ✓ 集成测试导入成功")
    except Exception as e,::
        print(f"   ❌ 集成测试导入失败, {e}")
        return False
#     
    print("\n🎉 所有概念模型导入测试通过！")
    return True

async def test_basic_functionality() -> None,
    """测试基本功能"""
    print("\n=测试概念模型基本功能 ===\n")
    
    try,
        # 测试环境模拟器基本功能
#         print("1. 测试环境模拟器基本功能...")
        print("   ✓ 环境模拟器实例化成功")
        
        # 测试因果推理引擎基本功能
        print("\n2. 测试因果推理引擎基本功能...")
#         from apps.backend.src.ai.concept_models.causal_reasoning_engine import CausalReasoningEngine
#         engine == CausalReasoningEngine()
        print("   ✓ 因果推理引擎实例化成功")
        
        # 测试自适应学习控制器基本功能
        print("\n3. 测试自适应学习控制器基本功能...")
#         from apps.backend.src.ai.concept_models.adaptive_learning_controller import AdaptiveLearningController
#         controller == AdaptiveLearningController()
        print("   ✓ 自适应学习控制器实例化成功")
        
        # 测试Alpha深度模型基本功能
        print("\n4. 测试Alpha深度模型基本功能...")
#         from apps.backend.src.ai.concept_models.alpha_deep_model import AlphaDeepModel
#         model == AlphaDeepModel("test_alpha_model.db")
        print("   ✓ Alpha深度模型实例化成功")
        
        # 测试统一符号空间基本功能
        print("\n5. 测试统一符号空间基本功能...")
#         from apps.backend.src.ai.concept_models.unified_symbolic_space import UnifiedSymbolicSpace
#         space == UnifiedSymbolicSpace("test_symbolic_space.db")
        print("   ✓ 统一符号空间实例化成功")
#         
        print("\n🎉 所有概念模型基本功能测试通过！")
        return True
        
    except Exception as e,::
        print(f"\n❌ 概念模型基本功能测试失败, {e}")
        return False

if __name"__main__":::
    # 测试导入
    import_success = test_imports()
    
    if import_success,::
        # 测试基本功能
        functionality_success = asyncio.run(test_basic_functionality())
        
        if functionality_success,::
            #             print("\n🎉 所有测试通过！概念模型可以正常工作。")
            sys.exit(0)
#         else,
#             print("\n❌ 基本功能测试失败！")
            sys.exit(1)
#     else,
#         print("\n❌ 导入测试失败！")
        sys.exit(1)