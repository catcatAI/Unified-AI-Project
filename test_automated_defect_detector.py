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
    
    def setUp(self):
        """测试初始化"""
        self.analyzer = StaticAnalyzer()
        
    def test_analyze_resource_leak(self):
        """测试分析资源泄漏"""
        # 创建包含资源泄漏的代码
        test_code = '''
def read_file(filename):
    f = open(filename, 'r')
    content = f.read()
    return content
    # 忘记关闭文件
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
            
        try:
            # 分析文件
            defects = self.analyzer.analyze_file(temp_file)
            
            # 验证是否检测到资源泄漏
            resource_leak_defects = [d for d in defects if d.defect_type == DefectType.RESOURCE_LEAK]
            self.assertGreater(len(resource_leak_defects), 0)
            
            # 验证缺陷信息
            defect = resource_leak_defects[0]
            self.assertEqual(defect.severity, DefectSeverity.HIGH)
            self.assertIn("open(", defect.code_snippet)
            
        finally:
            # 清理临时文件
            os.unlink(temp_file)
            
    def test_analyze_security_vulnerability(self):
        """测试分析安全漏洞"""
        # 创建包含安全漏洞的代码
        test_code = '''
def dangerous_eval(user_input):
    return eval(user_input)  # 使用eval是危险的
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
            
        try:
            # 分析文件
            defects = self.analyzer.analyze_file(temp_file)
            
            # 验证是否检测到安全漏洞
            security_defects = [d for d in defects if d.defect_type == DefectType.SECURITY_VULNERABILITY]
            self.assertGreater(len(security_defects), 0)
            
            # 验证缺陷信息
            defect = security_defects[0]
            self.assertEqual(defect.severity, DefectSeverity.HIGH)
            self.assertIn("eval(", defect.code_snippet)
            
        finally:
            # 清理临时文件
            os.unlink(temp_file)
            
    def test_analyze_code_smell(self):
        """测试分析代码异味"""
        # 创建包含代码异味的代码
        test_code = '''
def debug_function():
    print("Debug info")  # 调试打印
    # TODO: Implement proper logging
    return True
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
            
        try:
            # 分析文件
            defects = self.analyzer.analyze_file(temp_file)
            
            # 验证是否检测到代码异味
            smell_defects = [d for d in defects if d.defect_type == DefectType.CODE_SMELL]
            self.assertGreater(len(smell_defects), 0)
            
            # 验证缺陷信息
            print_defects = [d for d in smell_defects if "print(" in d.code_snippet]
            todo_defects = [d for d in smell_defects if "TODO" in d.code_snippet]
            
            self.assertGreater(len(print_defects), 0)
            self.assertGreater(len(todo_defects), 0)
            
        finally:
            # 清理临时文件
            os.unlink(temp_file)
            
    def test_determine_severity(self):
        """测试确定缺陷严重程度"""
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
    
    def setUp(self):
        """测试初始化"""
        self.detector = DefectDetector()
        
    def test_detect_defects_in_file(self):
        """测试检测文件中的缺陷"""
        # 创建包含多种缺陷的代码
        test_code = '''
def problematic_function():
    f = open("test.txt", "r")  # 资源泄漏
    data = f.read()
    
    user_input = input("Enter something: ")
    result = eval(user_input)  # 安全漏洞
    
    print("Debug:", result)  # 代码异味
    # TODO: Add proper error handling
    
    return result
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
            
        try:
            # 检测缺陷
            defects = self.detector.detect_defects_in_file(temp_file)
            
            # 验证检测结果
            self.assertGreater(len(defects), 0)
            
            # 检查各种类型的缺陷
            resource_defects = self.detector.get_defects_by_type(DefectType.RESOURCE_LEAK)
            security_defects = self.detector.get_defects_by_type(DefectType.SECURITY_VULNERABILITY)
            smell_defects = self.detector.get_defects_by_type(DefectType.CODE_SMELL)
            
            self.assertGreater(len(resource_defects), 0)
            self.assertGreater(len(security_defects), 0)
            self.assertGreater(len(smell_defects), 0)
            
        finally:
            # 清理临时文件
            os.unlink(temp_file)
            
    def test_get_defects_by_severity(self):
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
        
        self.assertEqual(len(high_defects), 1)
        self.assertEqual(len(low_defects), 1)
        self.assertEqual(high_defects[0].defect_id, "test1")
        self.assertEqual(low_defects[0].defect_id, "test2")
        
    def test_generate_defect_report(self):
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
        self.assertIn("Defect Detection Report", report)
        self.assertIn("Total defects: 1", report)
        self.assertIn("High: 1", report)
        self.assertIn("resource_leak", report)  # 修复：使用小写形式
        self.assertIn("Resource not closed", report)
        self.assertIn("f = open('file.txt')", report)
        
    def test_save_defect_report(self):
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
            self.assertTrue(result)
            
            # 验证文件内容
            with open(temp_file, 'r') as f:
                content = f.read()
                self.assertIn("Defect Detection Report", content)
                self.assertIn("Debug print statement", content)
                self.assertIn("print('debug')", content)
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestDefectDetectorIntegration(unittest.TestCase):
    """缺陷检测器集成测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.detector = DefectDetector()
        
    def test_detect_complex_file(self):
        """测试检测复杂文件"""
        # 创建包含多种问题的复杂代码
        test_code = '''
import os
import subprocess

class DataManager:
    """数据管理器"""
    
    def __init__(self):
        self.data = []
        
    def load_data(self, filename):
        """加载数据"""
        f = open(filename, 'r')  # 资源泄漏
        self.data = f.readlines()
        # 忘记关闭文件
        
    def process_data(self, data):
        """处理数据"""
        # TODO: Implement proper data processing
        result = eval(data)  # 安全漏洞
        print("Processing:", result)  # 调试打印
        return result
        
    def save_data(self, filename, data):
        """保存数据"""
        f = open(filename, 'w')  # 资源泄漏
        f.write(str(data))
        # 忘记关闭文件
        
    def execute_command(self, cmd):
        """执行命令"""
        # 安全漏洞：使用shell=True
        result = subprocess.run(cmd, shell=True, capture_output=True)
        return result.stdout

def main():
    """主函数"""
    manager = DataManager()
    user_input = input("Enter command: ")  # 用户输入
    result = eval(user_input)  # 安全漏洞
    print("Result:", result)  # 调试打印
    return result

if __name__ == "__main__":
    main()
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
            
        try:
            # 检测缺陷
            defects = self.detector.detect_defects_in_file(temp_file)
            
            # 验证检测结果
            self.assertGreater(len(defects), 0)
            
            # 统计各种类型的缺陷
            resource_defects = [d for d in defects if d.defect_type == DefectType.RESOURCE_LEAK]
            security_defects = [d for d in defects if d.defect_type == DefectType.SECURITY_VULNERABILITY]
            smell_defects = [d for d in defects if d.defect_type == DefectType.CODE_SMELL]
            
            # 验证检测到的缺陷数量
            self.assertGreater(len(resource_defects), 0)
            self.assertGreater(len(security_defects), 0)
            self.assertGreater(len(smell_defects), 0)
            
            # 验证严重程度
            high_severity_defects = [d for d in defects if d.severity == DefectSeverity.HIGH]
            self.assertGreater(len(high_severity_defects), 0)
            
        finally:
            # 清理临时文件
            os.unlink(temp_file)


if __name__ == "__main__":
    unittest.main()