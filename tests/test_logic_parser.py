try:
    from apps.backend.src.tools.logic_model.logic_parser_eval import LogicParserEval
    print("logic_parser_eval imported successfully")
    
    # 测试实例化
    evaluator = LogicParserEval()
    print("LogicParserEval instantiated successfully")
    
    # 测试简单表达式
    result = evaluator.evaluate("true AND false")
    print(f"Simple evaluation result: {result}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()