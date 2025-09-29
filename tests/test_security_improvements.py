"""
安全改进测试用例
"""

import unittest
from apps.backend.src.tools.math_model.data_generator import _safe_eval as math_safe_eval
from apps.backend.src.tools.math_model.lightweight_math_model import LightweightMathModel
from apps.backend.src.tools.logic_model.logic_data_generator import evaluate_proposition as logic_safe_eval
from apps.backend.src.tools.logic_model.lightweight_logic_model import LightweightLogicModel

class TestSecurityImprovements(unittest.TestCase):
    """安全改进测试类"""
    
    def test_math_safe_eval(self) -> None:
        """测试数学表达式的安全计算"""
        # 测试基本运算
        _ = self.assertEqual(math_safe_eval("5 + 3"), 8)
        _ = self.assertEqual(math_safe_eval("10 - 4"), 6)
        _ = self.assertEqual(math_safe_eval("6 * 7"), 42)
        _ = self.assertEqual(math_safe_eval("15 / 3"), 5.0)
        
        # 测试复杂表达式
        _ = self.assertEqual(math_safe_eval("2 ** 3"), 8)
        _ = self.assertEqual(math_safe_eval("10 % 3"), 1)
        
        # 测试负数
        _ = self.assertEqual(math_safe_eval("-5 + 3"), -2)
        _ = self.assertEqual(math_safe_eval("5 + (-3)"), 2)
        
    def test_math_model_safe_eval(self) -> None:
        """测试数学模型的安全计算"""
        model = LightweightMathModel()
        
        # 测试基本运算
        _ = self.assertEqual(model._safe_eval("5 + 3"), 8.0)
        _ = self.assertEqual(model._safe_eval("10 - 4"), 6.0)
        _ = self.assertEqual(model._safe_eval("6 * 7"), 42.0)
        
        # 测试无效表达式
        _ = self.assertIsNone(model._safe_eval("import os"))
        _ = self.assertIsNone(model._safe_eval("__import__('os')"))
        
    def test_logic_safe_eval(self) -> None:
        """测试逻辑表达式的安全计算"""
        # 测试基本逻辑运算
        _ = self.assertEqual(logic_safe_eval("true and false"), False)
        _ = self.assertEqual(logic_safe_eval("true or false"), True)
        _ = self.assertEqual(logic_safe_eval("not true"), False)
        _ = self.assertEqual(logic_safe_eval("not false"), True)
        
        # 测试复杂表达式
        _ = self.assertEqual(logic_safe_eval("(true and false) or true"), True)
        _ = self.assertEqual(logic_safe_eval("not (true and false)"), True)
        
    def test_logic_model_safe_eval(self) -> None:
        """测试逻辑模型的安全计算"""
        model = LightweightLogicModel()
        
        # 测试基本逻辑运算
        _ = self.assertEqual(model._safe_eval_logic("True and False"), False)
        _ = self.assertEqual(model._safe_eval_logic("True or False"), True)
        _ = self.assertEqual(model._safe_eval_logic("not True"), False)
        
        # 测试无效表达式
        _ = self.assertIsNone(model._safe_eval_logic("import os"))
        _ = self.assertIsNone(model._safe_eval_logic("__import__('os')"))
        
    def test_no_eval_usage(self) -> None:
        """测试确保没有使用eval函数"""
        # 检查math_model文件
        with open("apps/backend/src/tools/math_model/data_generator.py", "r") as f:
            content = f.read()
            # 检查是否直接调用了eval函数（排除安全函数和注释）
            code_lines = [line for line in content.split('\n') 
                         if not line.strip().startswith('#') 
                         and 'eval(' in line 
                         and 'def _safe_eval' not in line 
                         _ = and '安全地计算数学表达式，避免使用eval()' not in line]
            # 确保没有在代码中直接调用eval()
            direct_eval_calls = [line for line in code_lines if line.strip().startswith('eval(') or 
                               _ = (line.strip().startswith('return eval(')) or 
                               ('= eval(' in line and 'def' not in line)]
            _ = self.assertEqual(len(direct_eval_calls), 0, f"Found direct eval() calls in data_generator.py: {direct_eval_calls}")
            
        with open("apps/backend/src/tools/math_model/lightweight_math_model.py", "r") as f:
            content = f.read()
            # 检查是否直接调用了eval函数（排除安全函数）
            code_lines = [line for line in content.split('\n') 
                         if not line.strip().startswith('#') 
                         and 'eval(' in line 
                         and 'def _safe_eval' not in line]
            # 确保没有在代码中直接调用eval()
            direct_eval_calls = [line for line in code_lines if line.strip().startswith('eval(') or 
                               _ = (line.strip().startswith('return eval(')) or 
                               ('= eval(' in line and 'def' not in line)]
            _ = self.assertEqual(len(direct_eval_calls), 0, f"Found direct eval() calls in lightweight_math_model.py: {direct_eval_calls}")
            
        # 检查logic_model文件
        with open("apps/backend/src/tools/logic_model/logic_data_generator.py", "r") as f:
            content = f.read()
            # 检查是否直接调用了eval函数（排除安全函数和注释）
            code_lines = [line for line in content.split('\n') 
                         if not line.strip().startswith('#') 
                         and 'eval(' in line 
                         and 'def evaluate_proposition' not in line 
                         and 'def safe_eval' not in line
                         and '避免使用eval' not in line]
            # 确保没有在代码中直接调用eval()
            direct_eval_calls = [line for line in code_lines if line.strip().startswith('eval(') or 
                               _ = (line.strip().startswith('return eval(')) or 
                               ('= eval(' in line and 'def' not in line)]
            _ = self.assertEqual(len(direct_eval_calls), 0, f"Found direct eval() calls in logic_data_generator.py: {direct_eval_calls}")
            
        with open("apps/backend/src/tools/logic_model/lightweight_logic_model.py", "r") as f:
            content = f.read()
            # 检查是否直接调用了eval函数（排除安全函数）
            code_lines = [line for line in content.split('\n') 
                         if not line.strip().startswith('#') 
                         and 'eval(' in line 
                         and 'def _safe_eval_logic' not in line]
            # 确保没有在代码中直接调用eval()
            direct_eval_calls = [line for line in code_lines if line.strip().startswith('eval(') or 
                               _ = (line.strip().startswith('return eval(')) or 
                               ('= eval(' in line and 'def' not in line)]
            _ = self.assertEqual(len(direct_eval_calls), 0, f"Found direct eval() calls in lightweight_logic_model.py: {direct_eval_calls}")

if __name__ == "__main__":
    _ = unittest.main()