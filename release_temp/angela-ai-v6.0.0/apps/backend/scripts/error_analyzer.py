#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的错误分析模块
负责分析测试结果,识别不同类型的错误并生成修复建议
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    SYNTAX_ERROR = "语法错误"
    UNKNOWN = "未知错误"

@dataclass
class ErrorInfo:
    error_type: ErrorType
    file_path: Optional[str]
    line_number: Optional[int]
    error_message: str
    details: Dict[str, Any]

class ErrorAnalyzer:
    def __init__(self, test_results_file: str = "test_results/latest_test_results.json") -> None:
        self.test_results_file = test_results_file
        self.error_patterns = {
            ErrorType.ASYNC_WARNING: r"RuntimeWarning: coroutine '.*' was never awaited",
            ErrorType.INIT_ERROR: r"TypeError: .*__init__.* missing .* required positional arguments",
            ErrorType.ATTRIBUTE_ERROR: r"AttributeError: .* object has no attribute .*",
            ErrorType.ASSERTION_ERROR: r"AssertionError: assert .*",
            ErrorType.TIMEOUT_ERROR: r"(TimeoutError|test timeout exceeded)",
            ErrorType.IMPORT_ERROR: r"(ModuleNotFoundError|No module named|ImportError)",
            ErrorType.SYNTAX_ERROR: r"SyntaxError:",
            ErrorType.CONFIG_ERROR: r"(ConfigError|ConfigurationError|Invalid configuration)",
            ErrorType.CONNECTION_ERROR: r"(ConnectionError|Connection failed|Could not connect)",
            ErrorType.VALIDATION_ERROR: r"(ValidationError|Validation failed)",
        }

    def load_test_results(self) -> Dict[str, Any]:
        """加载测试结果文件"""
        try:
            with open(self.test_results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"[ERROR] 测试结果文件 {self.test_results_file} 未找到")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] 测试结果文件格式错误: {e}")
            return {}

    def analyze_errors(self) -> List[ErrorInfo]:
        """分析测试结果中的错误"""
        test_results = self.load_test_results()
        if not test_results:
            return []

        errors: List[ErrorInfo] = []
        # Use the JSON report from pytest-json-report if available
        if "tests" in test_results:
            for test in test_results["tests"]:
                if test["outcome"] == "failed":
                    call = test.get("call", {})
                    longrepr = call.get("longrepr", "")
                    file_path, line_num, error_msg = self._parse_longrepr(longrepr)
                    
                    error_type = self._determine_error_type(error_msg)
                    
                    error_info = ErrorInfo(
                        error_type=error_type,
                        file_path=file_path,
                        line_number=line_num,
                        error_message=error_msg.split('\n')[0], # First line of error
                        details={"test_name": test["nodeid"], "full_error": error_msg}
                    )
                    errors.append(error_info)
            return errors

        # Fallback to parsing stdout/stderr if json report is not structured
        stdout = test_results.get("stdout", "")
        stderr = test_results.get("stderr", "")
        combined_output = stdout + "\n" + stderr

        if not combined_output.strip():
             if test_results.get("exit_code", 0) != 0:
                errors.append(ErrorInfo(ErrorType.UNKNOWN, None, None, "Test run failed with no output.", {{}}))
             return errors

        for error_type, pattern in self.error_patterns.items():
            matches = re.finditer(pattern, combined_output)
            for match in matches:
                error_info = self._extract_error_details(error_type, match, combined_output)
                if error_info not in errors:
                    errors.append(error_info)
        
        if not errors and test_results.get("exit_code", 0) != 0:
            errors.append(ErrorInfo(
                error_type=ErrorType.UNKNOWN,
                file_path=None,
                line_number=None,
                error_message="测试失败但未识别具体错误类型",
                details={"exit_code": test_results.get("exit_code")}
            ))
        
        return errors
        
    def _parse_longrepr(self, longrepr: str) -> tuple[Optional[str], Optional[int], str]:
        """Parses the 'longrepr' string from pytest-json-report."""
        # Example: "/path/to/test.py:123: AssertionError: assert False"
        match = re.match(r"^(.*):(\d+): (.*)", longrepr, re.DOTALL)
        if match:
            file_path, line_num, error_msg = match.groups()
            return file_path, int(line_num), error_msg
        return None, None, longrepr


    def _determine_error_type(self, error_message: str) -> ErrorType:
        """Determines the error type from an error message."""
        for error_type, pattern in self.error_patterns.items():
            if re.search(pattern, error_message, re.IGNORECASE):
                return error_type
        return ErrorType.UNKNOWN

    def _extract_error_details(self, error_type: ErrorType, match: re.Match, combined_output: str) -> ErrorInfo:
        """提取错误详细信息"""
        error_message = match.group(0)
        
        file_path: Optional[str] = None
        line_number: Optional[int] = None
        
        error_context = self._get_error_context(match, combined_output)
        file_line_match = re.search(r'File "([^"]+)", line (\d+)', error_context)
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

    def _get_error_context(self, match: re.Match, combined_output: str, context_lines: int = 3) -> str:
        """获取错误上下文信息"""
        match_start = match.start()
        
        start_pos = max(0, combined_output.rfind('\n', 0, match_start) - (context_lines * 100)) # Approximate line length
        end_pos = combined_output.find('\n', match.end() + (context_lines * 100)) # Approximate line length
        if end_pos == -1:
            end_pos = len(combined_output)
            
        return combined_output[start_pos:end_pos].strip()

    def generate_error_report(self) -> Dict[str, Any]:
        """生成错误分析报告"""
        errors = self.analyze_errors()
        
        report = {
            "total_errors": len(errors),
            "errors_by_type": {},
            "error_details": []
        }
        
        errors_by_type: Dict[str, int] = {}
        for error in errors:
            error_type_name = error.error_type.value
            errors_by_type[error_type_name] = errors_by_type.get(error_type_name, 0) + 1
            
            report["error_details"].append({
                "type": error_type_name,
                "file_path": error.file_path,
                "line_number": error.line_number,
                "message": error.error_message,
                "details": error.details
            })
        report["errors_by_type"] = errors_by_type
        
        return report

    def save_error_report(self, report_file: str = "error_report.json"):
        """保存错误分析报告到文件"""
        report = self.generate_error_report()
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"错误报告已保存到 {report_file}")
        except IOError as e:
            logger.error(f"保存错误报告失败: {e}")
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
    
    analyzer.save_error_report()
    print(f"[ERROR] 错误报告已保存到 error_report.json")
