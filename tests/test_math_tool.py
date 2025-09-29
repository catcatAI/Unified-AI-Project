try:
    from apps.backend.src.tools.math_tool import calculate
    print("math_tool imported successfully")
    
    # 测试简单表达式
    result = calculate("what is 5 + 3?")
    print(f"Math tool calculation result: {result}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()