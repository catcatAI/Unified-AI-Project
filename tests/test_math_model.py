try:
    from apps.backend.src.tools.math_model.lightweight_math_model import LightweightMathModel
    print("lightweight_math_model imported successfully")
    
    # 测试实例化
    model = LightweightMathModel()
    print("LightweightMathModel instantiated successfully")
    
    # 测试简单表达式
    result = model.evaluate_expression("5 + 3")
    print(f"Simple evaluation result: {result}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()