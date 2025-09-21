#!/usr/bin/env python3
"""
独立的错误分析模块
负责分析测试结果，识别不同类型的错误并生成修复建议
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ErrorType(Enum):
    ASYNC_WARNING = "异步测试协程警告"
    INIT_ERROR = "对象初始化错误"
    ATTRIBUTE_ERROR = "属性错误"
    ASSERTION_ERROR = "断言失败"
    TIMEOUT_ERROR = "超时错误"
    IMPORT_ERROR = "导入路径错误"
    CONFIG_ERROR = "配置问题"
    CONNECTION_ERROR = "连接错误"
    VALIDATION_ERROR = "数据验证错误"
    UNKNOWN = "未知错误"


@dataclass
class ErrorInfo:
    error_type: ErrorType
    file_path: Optional[str]
    line_number: Optional[int]
    error_message: str
    details: Dict[str, Any]


class ErrorAnalyzer:
    def __init__(self, test_results_file: str = "test_results/latest_test_results.json"):
        self.test_results_file = test_results_file
        self.error_patterns = {
            ErrorType.ASYNC_WARNING: r"RuntimeWarning: coroutine '.*' was never awaited",
            ErrorType.INIT_ERROR: r"TypeError: .*.__init__.* missing .* required positional arguments",
            ErrorType.ATTRIBUTE_ERROR: r"AttributeError: .* object has no attribute .*",
            ErrorType.ASSERTION_ERROR: r"AssertionError: .* != .*",
            ErrorType.TIMEOUT_ERROR: r"(TimeoutError|test timeout exceeded)",
            ErrorType.IMPORT_ERROR: r"(ModuleNotFoundError|No module named|ImportError) .*",
            ErrorType.CONFIG_ERROR: r"(ConfigError|ConfigurationError|Invalid configuration)",
            ErrorType.CONNECTION_ERROR: r"(ConnectionError|Connection failed|Could not connect)",
            ErrorType.VALIDATION_ERROR: r"(ValidationError|Validation failed)",
        }
        
        # 添加更多错误模式以提高识别率，但避免过于宽泛的匹配
        self.additional_error_patterns = {
            ErrorType.TIMEOUT_ERROR: r"(?<!plugin.*)timeout(?!\s+plugin)",  # 避免匹配插件信息
            ErrorType.ASSERTION_ERROR: r"assert.*==",  # 更精确的断言匹配
            ErrorType.ATTRIBUTE_ERROR: r"AttributeError:",  # 更精确的属性错误匹配
            ErrorType.IMPORT_ERROR: r"ImportError:",  # 更精确的导入错误匹配
            ErrorType.CONNECTION_ERROR: r"Connection",  # 更精确的连接错误匹配
            ErrorType.VALIDATION_ERROR: r"ValidationError",  # 更精确的验证错误匹配
        }
    
    def load_test_results(self) -> Dict[str, Any]:
        """加载测试结果文件"""
        try:
            with open(self.test_results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] 测试结果文件 {self.test_results_file} 未找到")
            return {}
        except json.JSONDecodeError as e:
            print(f"[ERROR] 测试结果文件格式错误: {e}")
            return {}
    
    def analyze_errors(self) -> List[ErrorInfo]:
        """分析测试结果中的错误"""
        test_results = self.load_test_results()
        if not test_results:
            return []
        
        errors = []
        stdout = test_results.get("stdout", "")
        stderr = test_results.get("stderr", "")
        combined_output = stdout + "\n" + stderr
        
        # 首先尝试从测试结果中提取具体的失败用例
        errors.extend(self._extract_test_failures(test_results))
        
        # 分析每种错误类型
        for error_type, pattern in self.error_patterns.items():
            matches = re.finditer(pattern, combined_output)
            for match in matches:
                error_info = self._extract_error_details(error_type, match, combined_output)
                # 避免重复添加相同错误
                if error_info not in errors:
                    errors.append(error_info)
        
        # 使用额外的错误模式进行匹配，但避免匹配插件信息
        for error_type, pattern in getattr(self, 'additional_error_patterns', {}).items():
            # 对于超时错误，使用更精确的模式匹配，避免匹配插件信息
            if error_type == ErrorType.TIMEOUT_ERROR:
                # 匹配真正的超时错误，但排除插件信息
                precise_patterns = [
                    r"TimeoutError:",
                    r"test timeout exceeded",
                    r"timeout.*seconds",
                    r"timed out"
                ]
                
                for precise_pattern in precise_patterns:
                    matches = re.finditer(precise_pattern, combined_output, re.IGNORECASE)
                    for match in matches:
                        # 检查匹配的内容是否在插件信息中
                        context = self._get_error_context(match, combined_output, 5)
                        if "plugin" not in context.lower() and "metadata" not in context.lower():
                            error_info = self._extract_error_details(error_type, match, combined_output)
                            # 避免重复添加相同错误
                            if error_info not in errors:
                                errors.append(error_info)
            else:
                matches = re.finditer(pattern, combined_output, re.IGNORECASE)
                for match in matches:
                    error_info = self._extract_error_details(error_type, match, combined_output)
                    # 避免重复添加相同错误
                    if error_info not in errors:
                        errors.append(error_info)
        
        # 如果没有匹配已知错误类型，但测试失败了，则添加未知错误
        if not errors and test_results.get("exit_code", 0) != 0:
            error_info = ErrorInfo(
                error_type=ErrorType.UNKNOWN,
                file_path=None,
                line_number=None,
                error_message="测试失败但未识别具体错误类型",
                details={"exit_code": test_results.get("exit_code")}
            )
            errors.append(error_info)
        
        return errors
    
    def _extract_error_details(self, error_type: ErrorType, match, combined_output: str) -> ErrorInfo:
        """提取错误详细信息"""
        error_message = match.group(0)
        
        # 尝试提取文件路径和行号
        file_path = None
        line_number = None
        
        # 查找错误上下文中的文件信息
        error_context = self._get_error_context(match, combined_output)
        file_line_match = re.search(r"([\w/.\\]+\.py):(\d+)", error_context)
        if file_line_match:
            file_path = file_line_match.group(1)
            line_number = int(file_line_match.group(2))
        
        return ErrorInfo(
            error_type=error_type,
            file_path=file_path,
            line_number=line_number,
            error_message=error_message,
            details={
                "context": error_context,
                "full_match": match.group(0)
            }
        )
    
    def _get_error_context(self, match, combined_output: str, context_lines: int = 3) -> str:
        """获取错误上下文信息"""
        match_start = match.start()
        match_end = match.end()
        
        # 获取匹配位置前后几行的内容
        lines = combined_output.split('\n')
        line_positions = []
        pos = 0
        
        for i, line in enumerate(lines):
            line_positions.append((pos, pos + len(line)))
            pos += len(line) + 1  # +1 for newline
        
        # 找到匹配所在的行
        match_line = -1
        for i, (start, end) in enumerate(line_positions):
            if start <= match_start <= end:
                match_line = i
                break
        
        if match_line == -1:
            return match.group(0)
        
        # 提取上下文
        start_line = max(0, match_line - context_lines)
        end_line = min(len(lines), match_line + context_lines + 1)
        context_lines = lines[start_line:end_line]
        
        return '\n'.join(context_lines)
    
    def _extract_test_failures(self, test_results: Dict[str, Any]) -> List[ErrorInfo]:
        """从测试结果中提取失败的测试用例"""
        errors = []
        stdout = test_results.get("stdout", "")
        
        # 查找失败的测试用例
        failure_pattern = r"FAILED (.*?::.*?) - (.*?)\n"
        matches = re.finditer(failure_pattern, stdout)
        
        for match in matches:
            test_name = match.group(1)
            error_message = match.group(2)
            
            # 确定错误类型
            error_type = ErrorType.UNKNOWN
            if "Timeout" in error_message or "timeout" in error_message:
                error_type = ErrorType.TIMEOUT_ERROR
            elif "Assertion" in error_message:
                error_type = ErrorType.ASSERTION_ERROR
            elif "Attribute" in error_message:
                error_type = ErrorType.ATTRIBUTE_ERROR
            elif "Import" in error_message or "ModuleNotFoundError" in error_message:
                error_type = ErrorType.IMPORT_ERROR
            elif "Connection" in error_message or "connect" in error_message:
                error_type = ErrorType.CONNECTION_ERROR
            elif "Validation" in error_message or "validation" in error_message:
                error_type = ErrorType.VALIDATION_ERROR
            elif "Config" in error_message or "config" in error_message:
                error_type = ErrorType.CONFIG_ERROR
            
            # 尝试提取文件路径
            file_path = None
            line_number = None
            if "::" in test_name:
                # 处理测试名称格式如: tests/hsp/test_hsp_advanced_integration.py::TestHSPAdvancedIntegration::test_hsp_connector_error_recovery_and_retry
                parts = test_name.split("::")
                file_path = parts[0]  # 第一部分是文件路径
                
                # 确保文件路径格式正确
                if not file_path.endswith(".py"):
                    file_path += ".py"
            
            error_info = ErrorInfo(
                error_type=error_type,
                file_path=file_path,
                line_number=line_number,
                error_message=error_message,
                details={"test_name": test_name}
            )
            errors.append(error_info)
        
        # 如果上面的方法没有找到失败用例，尝试另一种方式
        if not errors:
            # 查找测试摘要中的失败信息
            summary_pattern = r"===== (\d+) failed, (\d+) passed, (\d+) skipped, (\d+) warnings in .* ====="
            summary_match = re.search(summary_pattern, stdout)
            if summary_match:
                failed_count = int(summary_match.group(1))
                if failed_count > 0:
                    # 查找具体的失败测试
                    failed_tests = re.findall(r"FAILED (.*?::.*?)\n", stdout)
                    for test in failed_tests:
                        error_info = ErrorInfo(
                            error_type=ErrorType.UNKNOWN,
                            file_path=None,
                            line_number=None,
                            error_message=f"测试 {test} 失败",
                            details={"test_name": test}
                        )
                        errors.append(error_info)
        
        # 如果仍然没有找到错误，但测试结果表明有失败，则添加一个通用错误
        if not errors and test_results.get("exit_code", 0) != 0:
            # 查找具体的错误信息
            error_lines = []
            in_error_section = False
            for line in stdout.split('\n'):
                if "FAILURES" in line:
                    in_error_section = True
                    continue
                elif in_error_section and line.startswith("=") and "failed" in line:
                    break
                elif in_error_section and line.strip():
                    error_lines.append(line)
            
            if error_lines:
                error_message = "\n".join(error_lines[:5])  # 取前5行错误信息
                error_info = ErrorInfo(
                    error_type=ErrorType.UNKNOWN,
                    file_path=None,
                    line_number=None,
                    error_message=error_message,
                    details={"source": "test_failure_summary"}
                )
                errors.append(error_info)
        
        return errors
    
    def generate_error_report(self) -> Dict[str, Any]:
        """生成错误分析报告"""
        errors = self.analyze_errors()
        
        report = {
            "total_errors": len(errors),
            "errors_by_type": {},
            "error_details": []
        }
        
        # 统计各类型错误数量
        for error in errors:
            error_type_name = error.error_type.value
            if error_type_name not in report["errors_by_type"]:
                report["errors_by_type"][error_type_name] = 0
            report["errors_by_type"][error_type_name] += 1
            
            # 添加错误详情
            report["error_details"].append({
                "type": error_type_name,
                "file_path": error.file_path,
                "line_number": error.line_number,
                "message": error.error_message,
                "details": error.details
            })
        
        return report
    
    def save_error_report(self, report_file: str = "error_report.json"):
        """保存错误分析报告到文件"""
        report = self.generate_error_report()
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return report


if __name__ == "__main__":
    analyzer = ErrorAnalyzer()
    report = analyzer.generate_error_report()
    
    print("[ERROR] 错误分析报告")
    print("=" * 50)
    print(f"总错误数: {report['total_errors']}")
    
    if report['total_errors'] > 0:
        print("\n错误类型统计:")
        for error_type, count in report['errors_by_type'].items():
            print(f"  {error_type}: {count}")
        
        print("\n详细错误信息:")
        for error in report['error_details']:
            print(f"  类型: {error['type']}")
            if error['file_path']:
                print(f"    文件: {error['file_path']}")
                if error['line_number']:
                    print(f"    行号: {error['line_number']}")
            print(f"    消息: {error['message']}")
            print()
    
    # 保存报告
    analyzer.save_error_report()
    print(f"[ERROR] 错误报告已保存到 error_report.json")