#!/usr/bin/env python3
"""
测试报告生成器
用于生成集成测试的详细报告
"""

import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import logging
import argparse
from typing import Any, Dict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestReportGenerator:
    """测试报告生成器"""
    __test__ = False # 防止pytest收集

    def __init__(self, report_dir: str = "test_reports") -> None:
        """
        初始化测试报告生成器

        Args:
            report_dir: 报告目录
        """
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)

    def generate_html_report(self, test_results: Dict[str, Any], output_file: str = None) -> str:
        """
        生成HTML测试报告

        Args:
            test_results: 测试结果数据
            output_file: 输出文件路径

        Returns:
            str: 生成的HTML报告路径
        """
        if output_file is None:
            output_file_path = self.report_dir / f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        else:
            output_file_path = Path(output_file)

        html_content = self._generate_html_content(test_results)

        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"HTML report generated: {output_file_path}")
            return str(output_file_path)
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return None

    def _generate_html_content(self, test_results: Dict[str, Any]) -> str:
        """生成HTML内容"""
        timestamp = test_results.get("timestamp", datetime.now().isoformat())
        summary = test_results.get("summary", {})
        test_cases = test_results.get("test_cases", [])

        # 计算统计信息
        total_tests = len(test_cases)
        passed_tests = len([tc for tc in test_cases if tc.get("outcome") == "passed"])
        failed_tests = len([tc for tc in test_cases if tc.get("outcome") == "failed"])
        skipped_tests = len([tc for tc in test_cases if tc.get("outcome") == "skipped"])
        # 计算通过率
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        test_case_rows = ""
        for test_case in test_cases:
            name = test_case.get("name", "Unknown")
            module = test_case.get("module", "Unknown")
            outcome = test_case.get("outcome", "unknown")
            duration = test_case.get("duration", 0)
            error_message = test_case.get("error_message", "")

            status_class = outcome.lower()
            status_text = outcome.capitalize()
            
            error_html = ""
            if error_message:
                error_html = f'<div class="error-details">{error_message}</div>'

            test_case_rows += f"""
                <tr>
                    <td>{name}</td>
                    <td>{module}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{duration:.3f}</td>
                    <td>{error_html}</td>
                </tr>
            """

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Integration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #eee; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-item {{ background-color: #f8f9fa; padding: 20px; border-radius: 6px; text-align: center; }}
        .summary-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .summary-label {{ font-size: 0.9em; color: #6c757d; margin-top: 5px; }}
        .pass-rate {{ color: #28a745; }}
        .fail-rate {{ color: #dc3545; }}
        .test-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .test-table th, .test-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .test-table th {{ background-color: #f8f9fa; font-weight: bold; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .skipped {{ color: #ffc107; }}
        .error-details {{ background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 5px; font-family: monospace; font-size: 0.9em; white-space: pre-wrap; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #6c757d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Integration Test Report</h1>
            <p>Generated on {timestamp}</p>
        </div>
        <div class="summary">
            <div class="summary-item">
                <div class="summary-number">{total_tests}</div>
                <div class="summary-label">Total Tests</div>
            </div>
            <div class="summary-item">
                <div class="summary-number passed">{passed_tests}</div>
                <div class="summary-label">Passed</div>
            </div>
            <div class="summary-item">
                <div class="summary-number failed">{failed_tests}</div>
                <div class="summary-label">Failed</div>
            </div>
            <div class="summary-item">
                <div class="summary-number skipped">{skipped_tests}</div>
                <div class="summary-label">Skipped</div>
            </div>
            <div class="summary-item">
                <div class="summary-number pass-rate">{pass_rate:.1f}%</div>
                <div class="summary-label">Pass Rate</div>
            </div>
        </div>
        <h2>Test Results</h2>
        <table class="test-table">
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Module</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                {test_case_rows}
            </tbody>
        </table>
        <div class="footer">
            <p>Generated by Unified AI Project Test Report Generator</p>
        </div>
    </div>
</body>
</html>
"""
        return html_template

    def parse_junit_xml(self, xml_file: str) -> Dict[str, Any]:
        """
        解析JUnit XML测试结果文件

        Args:
            xml_file: XML文件路径

        Returns:
            Dict: 解析后的测试结果
        """
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            test_results = {
                "timestamp": datetime.now().isoformat(),
                "summary": {},
                "test_cases": []
            }

            for testsuite in root.findall(".//testsuite"):
                for testcase in testsuite.findall("testcase"):
                    test_case_data = {
                        "name": testcase.get("name", ""),
                        "module": testcase.get("classname", ""),
                        "duration": float(testcase.get("time", 0)),
                        "outcome": "passed"
                    }

                    failure = testcase.find("failure")
                    error = testcase.find("error")
                    skipped = testcase.find("skipped")

                    if failure is not None:
                        test_case_data["outcome"] = "failed"
                        test_case_data["error_message"] = failure.text or failure.get("message", "")
                    elif error is not None:
                        test_case_data["outcome"] = "failed"
                        test_case_data["error_message"] = error.text or error.get("message", "")
                    elif skipped is not None:
                        test_case_data["outcome"] = "skipped"
                        test_case_data["error_message"] = skipped.text or skipped.get("message", "")

                    test_results["test_cases"].append(test_case_data)

            return test_results
        except Exception as e:
            logger.error(f"Error parsing JUnit XML file {xml_file}: {e}")
            return {}

    def generate_performance_report(self, benchmark_results: Dict[str, Any], output_file: str = None) -> str:
        # This method was incomplete in the original file, so I am leaving it as a basic shell.
        # A full implementation would require a similar HTML generation process as the other reports.
        logger.info("Generating performance report (stub).")
        return ""


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="Test Report Generator")
    parser.add_argument(
        "action",
        choices=["html", "performance", "parse-xml"],
        help="Action to perform"
    )
    parser.add_argument(
        "--input",
        help="Input file (XML for parse-xml, JSON for html/performance)"
    )
    parser.add_argument(
        "--output",
        help="Output HTML or JSON file path"
    )

    args = parser.parse_args()
    report_generator = TestReportGenerator()

    if args.action == "html":
        if not args.input:
            print("Error: --input is required for html action")
            sys.exit(1)
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                test_results = json.load(f)
            report_generator.generate_html_report(test_results, args.output)
        except Exception as e:
            print(f"Error reading or processing test results: {e}")
            sys.exit(1)

    elif args.action == "performance":
        if not args.input:
            print("Error: --input is required for performance action")
            sys.exit(1)
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                benchmark_results = json.load(f)
            report_generator.generate_performance_report(benchmark_results, args.output)
        except Exception as e:
            print(f"Error reading benchmark results: {e}")
            sys.exit(1)

    elif args.action == "parse-xml":
        if not args.input:
            print("Error: --input is required for parse-xml action")
            sys.exit(1)
        
        test_results = report_generator.parse_junit_xml(args.input)
        if test_results:
            output_file = args.output or "parsed_test_results.json"
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(test_results, f, indent=2, ensure_ascii=False)
                print(f"Parsed test results saved to: {output_file}")
            except Exception as e:
                print(f"Error saving parsed results: {e}")
                sys.exit(1)
        else:
            print("Failed to parse test results")
            sys.exit(1)


if __name__ == "__main__":
    main()
