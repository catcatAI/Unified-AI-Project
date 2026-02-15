"""
测试模块 - test_logic_tool

自动生成的测试模块,用于验证系统功能。
"""

try:
    from tools.logic_tool import LogicTool
    print("logic_tool imported successfully")
    
    # 测试实例化
    tool = LogicTool()
    print("LogicTool instantiated successfully")
    
    # 测试简单表达式
    result = tool.evaluate_expression("true AND false")
    print(f"LogicTool evaluation result: {result}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()