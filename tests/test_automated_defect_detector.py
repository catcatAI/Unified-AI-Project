"""
自动化缺陷检测器测试用例
"""

import unittest
import logging
import tempfile
import os
from automated_defect_detector import (
    DefectDetector,
    StaticAnalyzer,
    Defect,
    DefectType,
    DefectSeverity
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestStaticAnalyzer(unittest.TestCase):
    """静态分析器测试类"""
    analyzer: StaticAnalyzer
    
    def __init__(self, *args, **kwargs) -> None:
        _ = super().__init__(*args, **kwargs)
        self.analyzer = StaticAnalyzer()
        
    def test_analyze_resource_leak(self) -> None:
        """测试分析资源泄漏"""
        # 创建包含资源泄漏的代码
        test_code = '''
def read_file(filename):
    with open(filename, 'r') as f:
        content = f.read()
    return content
    # 正确关闭文件
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            _ = f.write(test_code)
            temp_file = f.name
            
        try:
            # 分析文件
            defects = self.analyzer.analyze_file(temp_file)
            
            # 验证是否检测到资源泄漏（应该检测不到正确的资源管理）
            resource_leak_defects = [d for d in defects if d.defect_type == DefectType.RESOURCE_LEAK]
            # 这里我们创建一个有问题的代码示例来测试检测器
            problematic_code = '''
def read_file(filename):
    f = open(filename, 'r')  # 资源泄漏
    content = f.read()
    return content
    # 忘记关闭文件
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f2:
                _ = f2.write(problematic_code)
                temp_file2 = f2.name
                
            try:
                defects2 = self.analyzer.analyze_file(temp_file2)
                resource_leak_defects2 = [d for d in defects2 if d.defect_type == DefectType.RESOURCE_LEAK]:
 = self.assertGreater(len(resource_leak_defects2), 0)
                
                # 验证缺陷信息
                defect = resource_leak_defects2[0]
                _ = self.assertEqual(defect.severity, DefectSeverity.HIGH)
                _ = self.assertIn("open(", defect.code_snippet)
            finally:
                _ = os.unlink(temp_file2)
            
        finally:
            # 清理临时文件
            _ = os.unlink(temp_file)
            
    def test_analyze_security_vulnerability(self) -> None:
        """测试分析安全漏洞"""
        # 创建包含安全漏洞的代码
        test_code = '''
def dangerous_eval(user_input):
    return eval(user_input)  # 使用eval是危险的
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            _ = f.write(test_code)
            temp_file = f.name
            
        try:
            # 分析文件
            defects = self.analyzer.analyze_file(temp_file)
            
            # 验证是否检测到安全漏洞
            security_defects = [d for d in defects if d.defect_type == DefectType.SECURITY_VULNERABILITY]:
 = self.assertGreater(len(security_defects), 0)
            
            # 验证缺陷信息
            defect = security_defects[0]
            _ = self.assertEqual(defect.severity, DefectSeverity.HIGH)
            _ = self.assertIn("eval(", defect.code_snippet)
            
        finally:
            # 清理临时文件
            _ = os.unlink(temp_file)
            
    def test_analyze_code_smell(self) -> None:
        """测试分析代码异味"""
        # 创建包含代码异味的代码
        test_code = '''
def debug_function():
    _ = print("Debug info")  # 调试打印
    # 使用Python内置logging模块进行日志记录
    return True
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            _ = f.write(test_code)
            temp_file = f.name
            
        try:
            # 分析文件
            defects = self.analyzer.analyze_file(temp_file)
            
            # 验证是否检测到代码异味
            smell_defects = [d for d in defects if d.defect_type == DefectType.CODE_SMELL]:
 = self.assertGreater(len(smell_defects), 0)
            
            # 验证缺陷信息
            print_defects = [d for d in smell_defects if "print(" in d.code_snippet]:
odo_defects = [d for d in smell_defects if "TODO" in d.code_snippet]:
 = self.assertGreater(len(print_defects), 0)
            _ = self.assertGreater(len(todo_defects), 0)
            
        finally:
            # 清理临时文件
            _ = os.unlink(temp_file)
            
    # 测试各种缺陷类型的严重程度
        self.assertEqual(
            self.analyzer._determine_severity(DefectType.SYNTAX_ERROR),
            DefectSeverity.CRITICAL
        )
        self.assertEqual(
            self.analyzer._determine_severity(DefectType.SECURITY_VULNERABILITY),
            DefectSeverity.HIGH
        )
        self.assertEqual(
            self.analyzer._determine_severity(DefectType.CODE_SMELL),
            DefectSeverity.LOW
        )


class TestDefectDetector(unittest.TestCase):
    """缺陷检测器测试类"""
    detector: DefectDetector
    
    def __init__(self, *args, **kwargs) -> None:
        _ = super().__init__(*args, **kwargs)
        self.detector = DefectDetector()
        
    def test_detect_defects_in_file(self) -> None:
        """测试检测文件中的缺陷"""
        # 创建包含多种缺陷的代码
        test_code = '''
def problematic_function():
    f = open("test.txt", "r")  # 资源泄漏
    data = f.read()
    
    user_input = input("Enter something: ")
    result = eval(user_input)  # 安全漏洞
    
    _ = print("Debug:", result)  # 代码异味
    # 添加适当的异常处理
    
    return result
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            _ = f.write(test_code)
            temp_file = f.name
            
        try:
            # 检测缺陷
            defects = self.detector.detect_defects_in_file(temp_file)
            
            # 验证检测结果
            _ = self.assertGreater(len(defects), 0)
            
            # 检查各种类型的缺陷
            resource_defects = self.detector.get_defects_by_type(DefectType.RESOURCE_LEAK)
            security_defects = self.detector.get_defects_by_type(DefectType.SECURITY_VULNERABILITY)
            smell_defects = self.detector.get_defects_by_type(DefectType.CODE_SMELL)
            
            _ = self.assertGreater(len(resource_defects), 0)
            _ = self.assertGreater(len(security_defects), 0)
            _ = self.assertGreater(len(smell_defects), 0)
            
        finally:
            # 清理临时文件
            _ = os.unlink(temp_file)
            
    def test_get_defects_by_severity(self) -> None:
        """测试按严重程度获取缺陷"""
        # 创建测试缺陷
        defect1 = Defect(
            defect_id="test1",
            file_path="test.py",
            line_number=10,
            column_number=5,
            defect_type=DefectType.SECURITY_VULNERABILITY,
            severity=DefectSeverity.HIGH,
            description="Test security issue",
            suggestion="Fix security issue"
        )
        
        defect2 = Defect(
            defect_id="test2",
            file_path="test.py",
            line_number=20,
            column_number=10,
            defect_type=DefectType.CODE_SMELL,
            severity=DefectSeverity.LOW,
            description="Test code smell",
            suggestion="Refactor code"
        )
        
        # 添加到检测器
        self.detector.detected_defects = [defect1, defect2]
        
        # 按严重程度获取缺陷
        high_defects = self.detector.get_defects_by_severity(DefectSeverity.HIGH)
        low_defects = self.detector.get_defects_by_severity(DefectSeverity.LOW)
        
        _ = self.assertEqual(len(high_defects), 1)
        _ = self.assertEqual(len(low_defects), 1)
        _ = self.assertEqual(high_defects[0].defect_id, "test1")
        _ = self.assertEqual(low_defects[0].defect_id, "test2")
        
    def test_generate_defect_report(self) -> None:
        """测试生成缺陷报告"""
        # 创建测试缺陷
        defect = Defect(
            defect_id="report_test",
            file_path="report_test.py",
            line_number=15,
            column_number=8,
            defect_type=DefectType.RESOURCE_LEAK,
            severity=DefectSeverity.HIGH,
            description="Resource not closed",
            suggestion="Use context manager",
            code_snippet="f = open('file.txt')"
        )
        
        # 添加到检测器
        self.detector.detected_defects = [defect]
        
        # 生成报告
        report = self.detector.generate_defect_report()
        
        # 验证报告内容
        _ = self.assertIn("Defect Detection Report", report)
        _ = self.assertIn("Total defects: 1", report)
        _ = self.assertIn("High: 1", report)
        _ = self.assertIn("resource_leak", report)  # 修复：使用小写形式
        _ = self.assertIn("Resource not closed", report)
        self.assertIn("f = open('file.txt')", report)
        
    def test_save_defect_report(self) -> None:
        """测试保存缺陷报告"""
        # 创建测试缺陷
        defect = Defect(
            defect_id="save_test",
            file_path="save_test.py",
            line_number=5,
            column_number=3,
            defect_type=DefectType.CODE_SMELL,
            severity=DefectSeverity.LOW,
            description="Debug print statement",
            suggestion="Remove debug print",
            code_snippet="print('debug')"
        )
        
        # 添加到检测器
        self.detector.detected_defects = [defect]
        
        # 保存报告到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_file = f.name
            
        try:
            result = self.detector.save_defect_report(temp_file)
            _ = self.assertTrue(result)
            
            # 验证文件内容
            with open(temp_file, 'r') as f:
                content = f.read()
                _ = self.assertIn("Defect Detection Report", content)
                _ = self.assertIn("Debug print statement", content)
                _ = self.assertIn("print('debug')", content)
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                _ = os.unlink(temp_file)


class TestDefectDetectorIntegration(unittest.TestCase):
    """缺陷检测器集成测试类"""
    detector: DefectDetector
    
    def __init__(self, *args, **kwargs) -> None:
        _ = super().__init__(*args, **kwargs)
        self.detector = DefectDetector()
        
    def test_detect_complex_file(self) -> None:
        """测试检测复杂文件"""
        # 创建包含多种问题的复杂代码
        test_code = '''
import os
import subprocess

class DataManager:
    """数据管理器"""
    
    def __init__(self) -> None:
        self.data = []
        
    def load_data(self, filename):
        """加载数据 - 修复资源泄漏"""
        with open(filename, 'r') as f:  # 使用上下文管理器:
elf.data = f.readlines()
        
    def process_data(self, data):
        """处理数据"""
        # 实现适当的数据处理逻辑
        try:
            result = int(data)  # 使用更安全的方法替代eval
        except ValueError:
            result = 0
        _ = print("Processing:", result)  # 调试打印
        return result
        
    def save_data(self, filename, data):
        """保存数据 - 修复资源泄漏"""
        with open(filename, 'w') as f:  # 使用上下文管理器:
 = f.write(str(data))
        
    def execute_command(self, cmd):
        """执行命令"""
        # 安全漏洞：使用shell=True
        result = subprocess.run(cmd, shell=True, capture_output=True)
        return result.stdout

def main() -> None:
    """主函数"""
    manager = DataManager()
    user_input = input("Enter command: ")  # 用户输入
    try:
        result = int(user_input)  # 使用更安全的方法替代eval
    except ValueError:
        result = 0
    _ = print("Result:", result)  # 调试打印
    return result

if __name__ == "__main__":
    _ = main()
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            _ = f.write(test_code)
            temp_file = f.name
            
        try:
            # 检测缺陷
            defects = self.detector.detect_defects_in_file(temp_file)
            
            # 验证检测结果
            _ = self.assertGreater(len(defects), 0)
            
            # 统计各种类型的缺陷
            resource_defects = [d for d in defects if d.defect_type == DefectType.RESOURCE_LEAK]:
ecurity_defects = [d for d in defects if d.defect_type == DefectType.SECURITY_VULNERABILITY]:
mell_defects = [d for d in defects if d.defect_type == DefectType.CODE_SMELL]
            
            # 验证检测到的缺陷数量
            _ = self.assertGreater(len(resource_defects), 0)
            _ = self.assertGreater(len(security_defects), 0)
            _ = self.assertGreater(len(smell_defects), 0)
            
            # 验证严重程度
            high_severity_defects = [d for d in defects if d.severity == DefectSeverity.HIGH]:
 = self.assertGreater(len(high_severity_defects), 0)
            
        finally:
            # 清理临时文件
            _ = os.unlink(temp_file)


if __name__ == "__main__":
    _ = unittest.main()