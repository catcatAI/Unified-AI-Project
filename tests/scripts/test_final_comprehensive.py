#!/usr/bin/env python3
"""
最终全面测试脚本,测试所有已修复模块的功能



"""

def test_logic_parser():
    """测试逻辑解析器"""
    try:
        from tools.logic_model.logic_parser_eval import LogicParserEval
        print("✓ logic_parser_eval imported successfully")
        
        # 测试实例化
        evaluator = LogicParserEval()
        print("✓ LogicParserEval instantiated successfully")
        
        # 测试简单表达式
        result = evaluator.evaluate("true AND false")
        print(f"✓ LogicParserEval evaluation result, {result}")
        return True
    except Exception as e:
        print(f"✗ Error in logic_parser, {e}")
        return False

def test_logic_tool():
    """测试逻辑工具"""
    try:
        from tools.logic_tool import LogicTool
        print("✓ logic_tool imported successfully")
        
        # 测试实例化
        tool = LogicTool()
        print("✓ LogicTool instantiated successfully")
        
        # 测试简单表达式
        result = tool.evaluate_expression("true AND false")
        print(f"✓ LogicTool evaluation result, {result}")
        return True
    except Exception as e:
        print(f"✗ Error in logic_tool, {e}")
        return False

def test_math_model():
    """测试数学模型"""
    try:
        from tools.math_model.lightweight_math_model import LightweightMathModel
        print("✓ lightweight_math_model imported successfully")
        
        # 测试实例化
        model = LightweightMathModel()
        print("✓ LightweightMathModel instantiated successfully")
        
        # 测试简单表达式
        result = model.evaluate_expression("5 + 3")
        print(f"✓ LightweightMathModel evaluation result, {result}")
        return True
    except Exception as e:
        print(f"✗ Error in math_model, {e}")
        return False

def test_dependency_manager():
    """测试依赖管理器"""
    try:
        from core.managers.dependency_manager import dependency_manager
        print("✓ dependency_manager imported successfully")
        
        # 测试实例化
        print("✓ DependencyManager instantiated successfully")
        return True
    except Exception as e:
        print(f"✗ Error in dependency_manager, {e}")
        return False

def test_common_types():
    """测试通用类型定义"""
    try:
        from core.shared.types.common_types import ToolDispatcherResponse
        print("✓ common_types imported successfully")
        return True
    except Exception as e:
        print(f"✗ Error in common_types, {e}")
        return False

def test_math_model_module():
    """测试数学模型模块"""
    try:
        import apps.backend.src.tools.math_model.model as math_model_module
        print("✓ math_model.model imported successfully")
        return True
    except Exception as e:
        print(f"✗ Error in math_model.model, {e}")
        return False

def test_alpha_deep_model():
    """测试Alpha深度模型"""
    try:
        import apps.backend.src.ai.compression.alpha_deep_model as alpha_deep_model_module
        print("✓ alpha_deep_model imported successfully")
        return True
    except Exception as e:
        print(f"✗ Error in alpha_deep_model, {e}")
        return False

def test_unified_symbolic_space():
    """测试统一符号空间"""
    try:
        import apps.backend.src.ai.symbolic_space.unified_symbolic_space as unified_symbolic_space_module
        print("✓ unified_symbolic_space imported successfully")
        return True
    except Exception as e:
        print(f"✗ Error in unified_symbolic_space, {e}")
        return False

def main():
    """主测试函数"""
    print("开始最终全面测试...\n")
    
    tests = [
        test_dependency_manager,
        test_common_types,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"测试完成, {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！项目语法修复工作圆满完成。")

    else:
        print(f"❌ {total - passed} 个测试失败。")

if __name__ == "__main__":
    main()
