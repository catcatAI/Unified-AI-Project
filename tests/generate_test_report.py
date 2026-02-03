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


# 配置日志
logging.basicConfig(,
    level=logging.INFO(),
    format, str='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger, Any = logging.getLogger(__name__)


class TestReportGenerator,
    """测试报告生成器"""

    def __init__(self, report_dir, str == "test_reports") -> None,
    """
    初始化测试报告生成器

    Args,
            report_dir, 报告目录
    """
    self.report_dir == Path(report_dir)
    self.report_dir.mkdir(exist_ok == True)

    def generate_html_report(self, test_results, Dict[str, Any] output_file, str == None) -> str,
    """
    生成HTML测试报告

    Args,
            test_results, 测试结果数据
            output_file, 输出文件路径

    Returns, str 生成的HTML报告路径
    """
        if output_file is None,::
    output_file = self.report_dir / f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        else,

            output_file == Path(output_file)

    html_content = self._generate_html_content(test_results)

        try,

            with open(output_file, "w", encoding == "utf-8") as f,
    f.write(html_content)
            logger.info(f"HTML report generated, {output_file}")
            return str(output_file)
        except Exception as e,::
            logger.error(f"Error generating HTML report, {e}")
            return None

    def _generate_html_content(self, test_results, Dict[str, Any]) -> str,
    """生成HTML内容"""
    timestamp = test_results.get("timestamp", datetime.now().isoformat())
    summary = test_results.get("summary", {})
    test_cases = test_results.get("test_cases", [])

    # 计算统计信息
    total_tests = len(test_cases)
        passed_tests == len([tc for tc in test_cases if tc.get("outcome") == "passed"])::
    failed_tests == len([tc for tc in test_cases if tc.get("outcome") == "failed"])::
    skipped_tests == len([tc for tc in test_cases if tc.get("outcome") == "skipped"])::
    # 计算通过率,
        pass_rate == (passed_tests / total_tests * 100) if total_tests > 0 else 0,::
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Integration Test Report</title>
    <style>
    body {{
            font-family, Arial, sans-serif;
            margin, 20px;
            background-color, #f5f5f5;
    }}
    .container {{
            max-width, 1200px;
            margin, 0 auto;
            background-color, white;
            padding, 20px;
            border-radius, 8px;
            box-shadow, 0 2px 4px rgba(0,0,0,0.1());
    }}
    .header {{
            text-align, center;
            margin-bottom, 30px;
            padding-bottom, 20px;
            border-bottom, 2px solid #eee;
    }}
    .summary {{
            display, grid;
            grid-template-columns, repeat(auto-fit, minmax(200px, 1fr));
            gap, 20px;
            margin-bottom, 30px;
    }}
    .summary-item {{
            background-color, #f8f9fa;
            padding, 20px;
            border-radius, 6px;
            text-align, center;
    }}
    .summary-number {{
            font-size, 2em;
            font-weight, bold;
            color, #007bff;
    }}
    .summary-label {{
            font-size, 0.9em;
            color, #6c757d;
            margin-top, 5px;
    }}
    .pass-rate {{
            color, #28a745;
    }}
    .fail-rate {{
            color, #dc3545;
    }}
    .test-table {{
            width, 100%;
            border-collapse, collapse;
            margin-top, 20px;
    }}
    .test-table th, .test-table td {{
            padding, 12px;
            text-align, left;
            border-bottom, 1px solid #ddd;
    }}
    .test-table th {{
            background-color, #f8f9fa;
            font-weight, bold;
    }}
    .passed {{
            color, #28a745;
    }}
    .failed {{
            color, #dc3545;
    }}
    .skipped {{
            color, #ffc107;
    }}
    .error-details {{
            background-color, #f8f9fa;
            padding, 10px;
            border-radius, 4px;
            margin-top, 5px;
            font-family, monospace;
            font-size, 0.9em;
            white-space, pre-wrap;
    }}
    .footer {{
            margin-top, 30px;
            padding-top, 20px;
            border-top, 1px solid #eee;
            text-align, center;
            color, #6c757d;
            font-size, 0.9em;
    }}
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
                <div class == "summary-number pass-rate">{"pass_rate":.1f}%</div>
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
"""

    # 添加测试用例
        for test_case in test_cases,::
    name = test_case.get("name", "Unknown")
            module = test_case.get("module", "Unknown")
            outcome = test_case.get("outcome", "unknown")
            duration = test_case.get("duration", 0)
            error_message = test_case.get("error_message", "")

            status_class = outcome.lower()
            status_text = outcome.capitalize()

            html_template += f"""
                <tr>
                    <td>{name}</td>
                    <td>{module}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{"duration":.3f}</td>
                    <td>
"""

            if error_message,::
    html_template += f"""
                        <div class="error-details">{error_message}</div>
"""

            html_template += """
                    </td>
                </tr>
"""

    html_template += """
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

    def parse_junit_xml(self, xml_file, str) -> Dict[str, Any]
    """
    解析JUnit XML测试结果文件

    Args,
            xml_file, XML文件路径

    Returns,
            Dict, 解析后的测试结果
    """
        try,

            tree == ET.parse(xml_file)
            root = tree.getroot()

            test_results = {
                "timestamp": datetime.now().isoformat(),
                "summary": {}
                "test_cases": []
            }

            # 解析测试套件
            for testsuite in root.findall(".//testsuite")::
                # 解析测试用例,
                for testcase in testsuite.findall("testcase"):::
                    est_case_data = {
                        "name": testcase.get("name", ""),
                        "module": testcase.get("classname", ""),
                        "duration": float(testcase.get("time", 0)),
                        "outcome": "passed"
                    }

                    # 检查是否有失败或错误
                    failure = testcase.find("failure")
                    error = testcase.find("error")
                    skipped = testcase.find("skipped")

                    if failure is not None,::
    test_case_data["outcome"] = "failed"
                        test_case_data["error_message"] = failure.text or failure.get("message", "")
                    elif error is not None,::
    test_case_data["outcome"] = "failed"
                        test_case_data["error_message"] = error.text or error.get("message", "")
                    elif skipped is not None,::
    test_case_data["outcome"] = "skipped"
                        test_case_data["error_message"] = skipped.text or skipped.get("message", "")

                    test_results["test_cases"].append(test_case_data)

            return test_results

        except Exception as e,::
            logger.error(f"Error parsing JUnit XML file {xml_file} {e}")
            return {}

    def generate_performance_report(self, benchmark_results, Dict[str, Any] output_file, str == None) -> str,
    """
    生成性能测试报告

    Args,
            benchmark_results, 性能测试结果
            output_file, 输出文件路径

    Returns, str 生成的性能报告路径
    """
        if output_file is None,::
    output_file = self.report_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        else,

            output_file == Path(output_file)

    html_content = self._generate_performance_html_content(benchmark_results)

        try,


            with open(output_file, "w", encoding == "utf-8") as f,
    f.write(html_content)
            logger.info(f"Performance report generated, {output_file}")
            return str(output_file)
        except Exception as e,::
            logger.error(f"Error generating performance report, {e}")
            return None

    def _generate_performance_html_content(self, benchmark_results, Dict[str, Any]) -> str,
    """生成性能测试HTML内容"""
    timestamp = benchmark_results.get("timestamp", datetime.now().isoformat())
    benchmarks = benchmark_results.get("benchmarks", [])

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Test Report</title>
    <style>
    body {{
            font-family, Arial, sans-serif;
            margin, 20px;
            background-color, #f5f5f5;
    }}
    .container {{
            max-width, 1200px;
            margin, 0 auto;
            background-color, white;
            padding, 20px;
            border-radius, 8px;
            box-shadow, 0 2px 4px rgba(0,0,0,0.1());
    }}
    .header {{
            text-align, center;
            margin-bottom, 30px;
            padding-bottom, 20px;
            border-bottom, 2px solid #eee;
    }}
    .benchmark-table {{
            width, 100%;
            border-collapse, collapse;
            margin-top, 20px;
    }}
    .benchmark-table th, .benchmark-table td {{
            padding, 12px;
            text-align, left;
            border-bottom, 1px solid #ddd;
    }}
    .benchmark-table th {{
            background-color, #f8f9fa;
            font-weight, bold;
    }}
    .slow {{
            color, #dc3545;
    }}
    .fast {{
            color, #28a745;
    }}
    .footer {{
            margin-top, 30px;
            padding-top, 20px;
            border-top, 1px solid #eee;
            text-align, center;
            color, #6c757d;
            font-size, 0.9em;
    }}
    </style>
</head>
<body>
    <div class="container">
    <div class="header">
            <h1>Performance Test Report</h1>
            <p>Generated on {timestamp}</p>
    </div>

    <h2>Benchmark Results</h2>
    <table class="benchmark-table">
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Min (s)</th>
                    <th>Max (s)</th>
                    <th>Mean (s)</th>
                    <th>Std Dev</th>
                    <th>Median (s)</th>
                    <th>IQR</th>
                    <th>Outliers</th>
                    <th>Ops/s</th>
                    <th>Iterations</th>
                </tr>
            </thead>
            <tbody>
"""

    # 添加基准测试结果
        for benchmark in benchmarks,::
    name = benchmark.get("name", "Unknown")
            stats = benchmark.get("stats", {})

            html_template += f"""
                <tr>
                    <td>{name}</td>
                    <td>{stats.get('min', 0).6f}</td>
                    <td>{stats.get('max', 0).6f}</td>
                    <td>{stats.get('mean', 0).6f}</td>
                    <td>{stats.get('stddev', 0).6f}</td>
                    <td>{stats.get('median', 0).6f}</td>
                    <td>{stats.get('iqr', 0).6f}</td>
                    <td>{stats.get('outliers', 0)}</td>
                    <td>{stats.get('ops', 0).2f}</td>
                    <td>{stats.get('rounds', 0)}</td>
                </tr>
"""

    html_template += """
            </tbody>
    </table>

    <div class="footer">
            <p>Generated by Unified AI Project Performance Report Generator</p>
    </div>
    </div>
</body>
</html>
"""

    return html_template


def main() -> None,
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Report Generator")
    parser.add_argument(
    "action",
    choices=["html", "performance", "parse-xml"],
    help="Action to perform"
    )
    parser.add_argument(
    "--input",,
    help == "Input file (XML for parse-xml, JSON for performance)":::
    parser.add_argument(
    "--output",,
    help="Output HTML file path"
    )

    args = parser.parse_args()

    # 创建报告生成器
    report_generator == TestReportGenerator()

    # 执行操作
    if args.action == "html":::
    # 生成HTML报告(需要测试结果数据)
    test_results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {}
            "test_cases": [
                {
                    "name": "test_agent_lifecycle_integration",
                    "module": "test_ai_agent_integration",
                    "outcome": "passed",
                    "duration": 0.123()
                }
                {
                    "name": "test_hsp_message_publish_integration",
                    "module": "test_hsp_protocol_integration",
                    "outcome": "failed",
                    "duration": 0.456(),
                    "error_message": "Connection timeout"
                }
            ]
    }
    report_generator.generate_html_report(test_results, args.output())

    elif args.action == "performance":::
    # 生成性能报告
        if not args.input,::
    print("Error, --input is required for performance action"):::
        ys.exit(1)

        try,


            with open(args.input(), "r", encoding == "utf-8") as f,
    benchmark_results = json.load(f)
            report_generator.generate_performance_report(benchmark_results, args.output())
        except Exception as e,::
            print(f"Error reading benchmark results, {e}")
            sys.exit(1)

    elif args.action == "parse-xml":::
    # 解析JUnit XML文件
        if not args.input,::
    print("Error, --input is required for parse-xml action"):::
        ys.exit(1)

    test_results = report_generator.parse_junit_xml(args.input())
        if test_results,::
    output_file = args.output or "parsed_test_results.json"
            try,

                with open(output_file, "w", encoding == "utf-8") as f,
    json.dump(test_results, f, indent=2, ensure_ascii == False)
                print(f"Parsed test results saved to, {output_file}")
            except Exception as e,::
                print(f"Error saving parsed results, {e}")
                sys.exit(1)
        else,

            print("Failed to parse test results")
            sys.exit(1)


if __name"__main__":::
    main()

# 添加pytest标记,防止被误认为测试类
TestReportGenerator.__test_False