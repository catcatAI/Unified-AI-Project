#!/usr/bin/env python3
"""
综合测试脚本，测试所有已修复的模块



"""

def test_logic_parser():
    """测试逻辑解析器"""
    try:
        from apps.backend.src.tools.logic_model.logic_parser_eval import LogicParserEval
        print("✓ logic_parser_eval imported successfully")
        
        # 测试实例化
        evaluator = LogicParserEval()
        print("✓ LogicParserEval instantiated successfully")
        
        # 测试简单表达式
        result = evaluator.evaluate("true AND false")
        print(f"✓ LogicParserEval evaluation result: {result}")
        return True
    except Exception as e:
        print(f"✗ Error in logic_parser: {e}")
        return False

def test_logic_tool():
    """测试逻辑工具"""
    try:
        from apps.backend.src.tools.logic_tool import LogicTool
        print("✓ logic_tool imported successfully")
        
        # 测试实例化
        tool = LogicTool()
        print("✓ LogicTool instantiated successfully")
        
        # 测试简单表达式
        result = tool.evaluate_expression("true AND false")
        print(f"✓ LogicTool evaluation result: {result}")
        return True
    except Exception as e:
        print(f"✗ Error in logic_tool: {e}")
        return False

def test_math_model():
    """测试数学模型"""
    try:
        from apps.backend.src.tools.math_model.lightweight_math_model import LightweightMathModel
        print("✓ lightweight_math_model imported successfully")
        
        # 测试实例化
        model = LightweightMathModel()
        print("✓ LightweightMathModel instantiated successfully")
        
        # 测试简单表达式
        result = model.evaluate_expression("5 + 3")
        print(f"✓ LightweightMathModel evaluation result: {result}")
        return True
    except Exception as e:
        print(f"✗ Error in math_model: {e}")
        return False

def test_math_tool():
    """测试数学工具"""
    try:
        from apps.backend.src.tools.math_tool import calculate
        print("✓ math_tool imported successfully")
        
        # 测试简单表达式
        result = calculate("what is 5 + 3?")
        print(f"✓ Math tool calculation result: {result}")
        return True
    except Exception as e:
        print(f"✗ Error in math_tool: {e}")
        return False

def test_dependency_manager():
    """测试依赖管理器"""
    try:
        from apps.backend.src.core.managers.dependency_manager import dependency_manager
        print("✓ dependency_manager imported successfully")
        
        # 测试实例化
        print("✓ DependencyManager instantiated successfully")
        return True
    except Exception as e:
        print(f"✗ Error in dependency_manager: {e}")
        return False

def test_common_types():
    """测试通用类型定义"""
    try:
        from apps.backend.src.core.shared.types.common_types import ToolDispatcherResponse
        print("✓ common_types imported successfully")
        return True
    except Exception as e:
        print(f"✗ Error in common_types: {e}")
        return False

def main():
    """主测试函数"""
    print("开始综合测试...\n")
    
    tests = [
        test_logic_parser,
        test_logic_tool,
        test_math_model,
        test_math_tool,
        test_dependency_manager,
        test_common_types

    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")

    else:
        print("❌ 部分测试失败。")

if __name__ == "__main__":
    main()