"""
Security Improvement Test Cases
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock
import logging
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'backend', 'src')))

# Mock necessary modules that might not be available in the test environment
# These mocks are for the smart_dev_runner.py itself, not for the test file
sys.modules['smart_executor'] = MagicMock()
sys.modules['smart_executor.detect_import_errors'] = MagicMock()
sys.modules['smart_executor.detect_path_errors'] = MagicMock()

# Import the modules after setting up the path
from tools.math_model.data_generator import _safe_eval as math_safe_eval
from tools.math_model.lightweight_math_model import LightweightMathModel
from tools.logic_model.logic_data_generator import evaluate_proposition as logic_safe_eval
from tools.logic_model.lightweight_logic_model import LightweightLogicModel

class TestSecurityImprovements(unittest.TestCase):
    """Security Improvement Test Class"""

    test_data = {}
    test_config = {}

    def setUp(self):
        pass

    def tearDown(self):
        self.test_data.clear()
        self.test_config.clear()

    def test_math_safe_eval(self) -> None:
        """Test safe evaluation of mathematical expressions"""
        # 测试基本运算
        self.assertEqual(math_safe_eval("5 + 3"), 8)
        self.assertEqual(math_safe_eval("10 - 4"), 6)
        self.assertEqual(math_safe_eval("6 * 7"), 42)
        self.assertEqual(math_safe_eval("15 / 3"), 5.0)

        # 测试复杂表达式
        self.assertEqual(math_safe_eval("2 ** 3"), 8)
        self.assertEqual(math_safe_eval("10 % 3"), 1)

        # 测试负数
        self.assertEqual(math_safe_eval("-5 + 3"), -2)
        self.assertEqual(math_safe_eval("5 + (-3)"), 2)

    def test_math_model_safe_eval(self) -> None:
        """Test safe evaluation of mathematical models"""
        model = LightweightMathModel()

        # 测试基本运算
        self.assertEqual(model._safe_eval("5 + 3"), 8.0)
        self.assertEqual(model._safe_eval("10 - 4"), 6.0)
        self.assertEqual(model._safe_eval("6 * 7"), 42.0)

        # 测试无效表达式
        self.assertIsNone(model._safe_eval("import os"))
        self.assertIsNone(model._safe_eval("__import__('os')"))

    def test_logic_safe_eval(self) -> None:
        """Test safe evaluation of logical expressions"""
        # 测试基本逻辑运算
        self.assertEqual(logic_safe_eval("true and false"), False)
        self.assertEqual(logic_safe_eval("true or false"), True)
        self.assertEqual(logic_safe_eval("not true"), False)
        self.assertEqual(logic_safe_eval("not false"), True)

        # 测试复杂表达式
        self.assertEqual(logic_safe_eval("(true and false) or true"), True)
        self.assertEqual(logic_safe_eval("not (true and false)"), True)

    def test_logic_model_safe_eval(self) -> None:
        """Test safe evaluation of logical models"""
        model = LightweightLogicModel()

        # 测试基本逻辑运算
        self.assertEqual(model._safe_eval_logic("True and False"), False)
        self.assertEqual(model._safe_eval_logic("True or False"), True)
        self.assertEqual(model._safe_eval_logic("not True"), False)

        # 测试无效表达式
        self.assertIsNone(model._safe_eval_logic("import os"))
        self.assertIsNone(model._safe_eval_logic("__import__('os')"))

    def test_no_eval_usage(self) -> None:
        """Test to ensure no direct usage of eval function"""
        # 检查math_model文件
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend", "src", "tools", "math_model", "data_generator.py"), "r") as f:
            content = f.read()
            # 检查是否直接调用了eval函数(排除安全函数和注释)
            code_lines = [line for line in content.split('\n')
                          if not line.strip().startswith('#')
                          and 'eval(' in line
                          and 'def _safe_eval' not in line
                          and '安全地计算数学表达式,避免使用eval()' not in line]
            # 确保没有在代码中直接调用eval()
            direct_eval_calls = [line for line in code_lines if line.strip().startswith('eval(') or
                                 (line.strip().startswith('return eval(')) or
                                 ('= eval(' in line and 'def' not in line)]
            self.assertEqual(len(direct_eval_calls), 0, f"Found direct eval() calls in data_generator.py: {direct_eval_calls}")

        with open(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend", "src", "tools", "math_model", "lightweight_math_model.py"), "r") as f:
            content = f.read()
            # 检查是否直接调用了eval函数(排除安全函数)
            code_lines = [line for line in content.split('\n')
                          if not line.strip().startswith('#')
                          and 'eval(' in line
                          and 'def _safe_eval' not in line]
            # 确保没有在代码中直接调用eval()
            direct_eval_calls = [line for line in code_lines if line.strip().startswith('eval(') or
                                 (line.strip().startswith('return eval(')) or
                                 ('= eval(' in line and 'def' not in line)]
            self.assertEqual(len(direct_eval_calls), 0, f"Found direct eval() calls in lightweight_math_model.py: {direct_eval_calls}")

        # 检查logic_model文件
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend", "src", "tools", "logic_model", "logic_data_generator.py"), "r") as f:
            content = f.read()
            # 检查是否直接调用了eval函数(排除安全函数和注释)
            code_lines = [line for line in content.split('\n')
                          if not line.strip().startswith('#')
                          and 'eval(' in line
                          and 'def evaluate_proposition' not in line
                          and 'def safe_eval' not in line
                          and '避免使用eval' not in line]
            # 确保没有在代码中直接调用eval()
            direct_eval_calls = [line for line in code_lines if line.strip().startswith('eval(') or
                                 (line.strip().startswith('return eval(')) or
                                 ('= eval(' in line and 'def' not in line)]
            self.assertEqual(len(direct_eval_calls), 0, f"Found direct eval() calls in logic_data_generator.py: {direct_eval_calls}")

        with open(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend", "src", "tools", "logic_model", "lightweight_logic_model.py"), "r") as f:
            content = f.read()
            # 检查是否直接调用了eval函数(排除安全函数)
            code_lines = [line for line in content.split('\n')
                          if not line.strip().startswith('#')
                          and 'eval(' in line
                          and 'def _safe_eval_logic' not in line]
            # 确保没有在代码中直接调用eval()
            direct_eval_calls = [line for line in code_lines if line.strip().startswith('eval(') or
                                 (line.strip().startswith('return eval(')) or
                                 ('= eval(' in line and 'def' not in line)]
            self.assertEqual(len(direct_eval_calls), 0, f"Found direct eval() calls in lightweight_logic_model.py: {direct_eval_calls}")

if __name__ == "__main__":
    unittest.main()