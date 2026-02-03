"""
智能化测试用例生成器测试用例
"""

import unittest
import logging
import tempfile
import os
# from intelligent_test_generator import (
    IntelligentTestGenerator, 
    CodeAnalyzer, 
    TestPatternAnalyzer, 
    TestType, 
    TestCase,
    TestParameter
)

# 配置日志
logging.basicConfig(level=logging.INFO())
logger: Any = logging.getLogger(__name__)


class TestCodeAnalyzer(unittest.TestCase):
    """代码分析器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.analyzer = CodeAnalyzer()
        
    def test_analyze_simple_function(self) -> None:
        """测试分析简单函数"""
        # 创建临时Python文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        try:
            # 分析文件
            result = self.analyzer.analyze_file(temp_file)
            
            # 验证结果
            self.assertIn("functions", result)
            self.assertEqual(len(result["functions"]), 2)
            
            # 验证add函数
            self.assertIn("add", result["functions"])
            add_func = result["functions"]["add"]
            self.assertEqual(add_func["name"], "add")
            self.assertEqual(len(add_func["parameters"]), 2)
            self.assertEqual(add_func["return_type"], "int")
            self.assertEqual(add_func["docstring"], "Add two numbers")
            
            # 验证参数
            params = add_func["parameters"]
            self.assertEqual(params[0]["name"], "a")
            self.assertEqual(params[0]["type_annotation"], "int")
            self.assertEqual(params[1]["name"], "b")
            self.assertEqual(params[1]["type_annotation"], "int")
            
            # 验证greet函数
            self.assertIn("greet", result["functions"])
            greet_func = result["functions"]["greet"]
            self.assertEqual(greet_func["name"], "greet")
            self.assertEqual(len(greet_func["parameters"]), 1)
            self.assertEqual(greet_func["return_type"], "str")
            
            # 验证默认参数
            greet_params = greet_func["parameters"]
            self.assertEqual(greet_params[0]["name"], "name")
            self.assertEqual(greet_params[0]["type_annotation"], "str")
            self.assertEqual(greet_params[0]["default"], "World")
            
        finally:
            # 清理临时文件
            os.unlink(temp_file)
            
    def test_analyze_class(self) -> None:
        """测试分析类"""
        # 创建临时Python文件
        test_code = '''
class Calculator:
    """A simple calculator"""
    
    def __init__(self, precision: int = 2) -> None:
        self.precision = precision
        
    def add(self, a: float, b: float) -> float:
        """Add two numbers"""
        return round(a + b, self.precision)
        
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers"""
        return round(a * b, self.precision)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        try:
            # 分析文件
            result = self.analyzer.analyze_file(temp_file)
            
            # 验证结果
            self.assertIn("classes", result)
            self.assertEqual(len(result["classes"]), 1)
            
            # 验证Calculator类
            self.assertIn("Calculator", result["classes"])
            calculator_class = result["classes"]["Calculator"]
            self.assertEqual(calculator_class["name"], "Calculator")
            self.assertEqual(calculator_class["docstring"], "A simple calculator")
            
            # 验证方法
            methods = calculator_class["methods"]
            self.assertEqual(len(methods), 3)  # __init__, add, multiply
            
            # 验证__init__方法
            self.assertIn("__init__", methods)
            init_method = methods["__init__"]
            self.assertEqual(len(init_method["parameters"]), 2)  # self, precision
            self.assertEqual(init_method["parameters"][1]["name"], "precision")
            self.assertEqual(init_method["parameters"][1]["default"], 2)
            
            # 验证add方法
            self.assertIn("add", methods)
            add_method = methods["add"]
            self.assertEqual(add_method["name"], "add")
            self.assertEqual(len(add_method["parameters"]), 3)  # self, a, b
            self.assertEqual(add_method["return_type"], "float")
            
        finally:
            # 清理临时文件
            os.unlink(temp_file)


class TestTestPatternAnalyzer(unittest.TestCase):
    """测试模式分析器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.pattern_analyzer = TestPatternAnalyzer()
        
    def test_identify_validation_patterns(self) -> None:
        """测试识别验证模式"""
        func_info = {
            "name": "validate_email",
            "parameters": [{"name": "email", "type_annotation": "str"}]
        }
        
        patterns = self.pattern_analyzer.identify_function_patterns(func_info)
        self.assertIn("validation", patterns)
        
    def test_identify_calculation_patterns(self) -> None:
        """测试识别计算模式"""
        func_info = {
            "name": "calculate_average",
            "parameters": [{"name": "numbers", "type_annotation": "List[float]"}]
        }
        
        patterns = self.pattern_analyzer.identify_function_patterns(func_info)
        self.assertIn("calculation", patterns)
        
    def test_identify_file_operation_patterns(self) -> None:
        """测试识别文件操作模式"""
        func_info = {
            "name": "read_file",
            "parameters": [{"name": "file_path", "type_annotation": "str"}]
        }
        
        patterns = self.pattern_analyzer.identify_function_patterns(func_info)
        self.assertIn("file_operations", patterns)
        
    def test_identify_authentication_patterns(self) -> None:
        """测试识别认证模式"""
        func_info = {
            "name": "login_user",
            "parameters": [
                {"name": "username", "type_annotation": "str"},
                {"name": "password", "type_annotation": "str"}
            ]
        }
        
        patterns = self.pattern_analyzer.identify_function_patterns(func_info)
        self.assertIn("authentication", patterns)


class TestIntelligentTestGenerator(unittest.TestCase):
    """智能化测试用例生成器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.generator = IntelligentTestGenerator()
        
    def test_generate_basic_function_test(self) -> None:
        """测试生成基本函数测试"""
        func_info = {
            "name": "add_numbers",
            "parameters": [
                {"name": "a", "type_annotation": "int"},
                {"name": "b", "type_annotation": "int"}
            ]
        }
        
        test_case = self.generator._create_basic_function_test(func_info)
        
        # 验证测试用例
        self.assertIsNotNone(test_case)
        self.assertEqual(test_case.name, "test_add_numbers_basic")
        self.assertEqual(test_case.function_name, "add_numbers")
        self.assertEqual(test_case.test_type, TestType.UNIT_TEST)
        self.assertEqual(len(test_case.parameters), 2)
        self.assertEqual(test_case.priority, 3)
        
    def test_generate_pattern_specific_tests(self) -> None:
        """测试生成模式特定测试"""
        func_info = {
            "name": "validate_input",
            "parameters": [{"name": "data", "type_annotation": "str"}]
        }
        
        pattern_tests = self.generator._create_pattern_specific_tests(func_info, "validation")
        
        # 验证生成的测试
        self.assertEqual(len(pattern_tests), 1)
        test_case = pattern_tests[0]
        self.assertEqual(test_case.name, "test_validate_input_invalid_input")
        self.assertEqual(test_case.function_name, "validate_input")
        self.assertEqual(test_case.priority, 4)
        
    def test_generate_test_code(self) -> None:
        """测试生成测试代码"""
        test_case = TestCase(
            name="test_example",
            description="Example test",
            test_type=TestType.UNIT_TEST,
            function_name="example_function",
            parameters=[
                TestParameter(name="param1", type_hint="str"),
                TestParameter(name="param2", type_hint="int")
            ],
            expected_behavior="Function executes without errors",
            priority=3
        )
        
        test_code = self.generator.generate_test_code(test_case)
        
        # 验证生成的代码
        self.assertIn("def test_example() -> None,", test_code)
        self.assertIn("Example test", test_code)
        self.assertIn("param1", test_code)
        self.assertIn("param2", test_code)
        self.assertIn("assert True", test_code)
        
    def test_generate_tests_for_file(self) -> None:
        """测试为文件生成测试用例"""
        # 创建临时Python文件
        test_code = '''
def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two numbers"""
    return a + b

class MathUtils:
    """Math utilities"""
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers"""
        return a * b
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        try:
            # 生成测试用例
            test_cases = self.generator.generate_tests_for_file(temp_file)
            
            # 验证结果
            self.assertGreater(len(test_cases), 0)
            
            # 检查是否生成了函数测试
            func_test_names = [tc.name for tc in test_cases if tc.function_name == "calculate_sum"]
            self.assertGreater(len(func_test_names), 0)
            
            # 检查是否生成了类方法测试
            method_test_names = [tc.name for tc in test_cases if "multiply" in tc.function_name]
            self.assertGreater(len(method_test_names), 0)

        finally:
            # 清理临时文件
            os.unlink(temp_file)
            
    def test_save_generated_tests(self) -> None:
        """测试保存生成的测试用例"""
        # 创建测试用例
        test_case = TestCase(
            name="test_save_example",
            description="Test for saving",
            test_type=TestType.UNIT_TEST,
            function_name="save_function",
            parameters=[],
            expected_behavior="Function saves data",
            priority=3
        )
        self.generator.generated_tests = [test_case]
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_file = f.name
        try:
            result = self.generator.save_generated_tests(temp_file)
            self.assertTrue(result)
            
            # 验证文件内容
            with open(temp_file, 'r') as f:
                content = f.read()
                self.assertIn("test_save_example", content)
                self.assertIn("Test for saving", content)
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    unittest.main()