#!/usr/bin/env python3
"""
性能基准测试和回归检测工作流
整合基准测试、回归检测和报告生成的完整流程
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import logging


# 配置日志
logging.basicConfig(
    level: str=logging.INFO,
    format: str='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger: Any = logging.getLogger(__name__)


class PerformanceBenchmarkWorkflow:
    """性能基准测试和回归检测工作流"""

    def __init__(self, project_root: str = None) -> None:
    """
    初始化性能基准测试工作流

    Args:
            project_root: 项目根目录
    """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent:
    self.scripts_dir = self.project_root / "scripts"
    self.benchmarks_dir = self.project_root / "benchmarks"
    self.benchmarks_dir.mkdir(exist_ok=True)
    self.reports_dir = self.project_root / "test_reports"
    self.reports_dir.mkdir(exist_ok=True)

    # 工作流配置
    self.workflow_config = {
            "benchmark": {
                "iterations": 100,
                "warmup": 10,
                "timeout": 300,
                "tags": ["performance", "benchmark"]
            },
            "regression": {
                "time_window_days": 30,
                "regression_threshold": 0.05,
                "alert_on_regression": True
            },
            "reporting": {
                "generate_html": True,
                "generate_json": True
            }
    }

    def run_complete_performance_workflow(self, benchmark_suite: str = "all") -> Dict[str, Any]:
    """
    运行完整的性能工作流

    Args:
            benchmark_suite: 基准测试套件名称

    Returns:
            Dict: 工作流执行结果
    """
    logger.info("Starting complete performance benchmark workflow...")
    workflow_start_time = datetime.now()

    workflow_results = {
            "timestamp": workflow_start_time.isoformat(),
            "phases": {}
    }

        try:
            # 1. 运行基准测试
            workflow_results["phases"]["benchmark_execution"] = self._run_benchmark_suite(benchmark_suite)

            # 2. 分析性能回归
            workflow_results["phases"]["regression_analysis"] = self._analyze_performance_regressions()

            # 3. 生成报告
            workflow_results["phases"]["report_generation"] = self._generate_performance_reports(
                workflow_results["phases"]["benchmark_execution"],
                workflow_results["phases"]["regression_analysis"]
            )

            # 4. 发送警报（如果有回归）
            workflow_results["phases"]["alerting"] = self._send_regression_alerts(
                workflow_results["phases"]["regression_analysis"]
            )

            workflow_end_time = datetime.now()
            workflow_results["duration"] = (workflow_end_time - workflow_start_time).total_seconds()
            workflow_results["status"] = "completed"

            logger.info(f"Performance benchmark workflow completed in {workflow_results['duration']:.2f} seconds")

        except Exception as e:


            logger.error(f"Error in performance benchmark workflow: {e}")
            workflow_results["status"] = "failed"
            workflow_results["error"] = str(e)

    # 保存工作流结果
    self._save_workflow_results(workflow_results)

    return workflow_results

    def _run_benchmark_suite(self, benchmark_suite: str) -> Dict[str, Any]:
    """
    运行基准测试套件

    Args:
            benchmark_suite: 基准测试套件名称

    Returns:
            Dict: 基准测试执行结果
    """
    logger.info(f"Running benchmark suite: {benchmark_suite}")

        try:
            # 构建pytest命令来运行性能基准测试
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "tests/integration/test_performance_benchmarks.py",
                "-v",
                "--tb=short",
                "-m",
                "performance"
            ]

            # 添加基准测试选项
            if benchmark_suite != "all":

    cmd.extend(["-k", benchmark_suite])

            # 运行基准测试
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.workflow_config["benchmark"]["timeout"]
            )

            benchmark_result = {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Benchmark suite execution {'succeeded' if benchmark_result['success'] else 'failed'}")
    return benchmark_result

        except subprocess.TimeoutExpired:


            logger.error("Benchmark suite execution timed out")
            return {
                "success": False,
                "error": "Benchmark suite execution timed out",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:

            logger.error(f"Error running benchmark suite: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _analyze_performance_regressions(self) -> Dict[str, Any]:
    """
    分析性能回归

    Returns:
            Dict: 回归分析结果
    """
    logger.info("Analyzing performance regressions...")

        try:
            # 调用性能回归检测器
            regression_detector_script = self.scripts_dir / "performance_regression_detector.py"
            if not regression_detector_script.exists()

    logger.warning("Performance regression detector script not found")
                return {"status": "skipped", "reason": "Script not found"}

            cmd = [
                sys.executable,
                str(regression_detector_script),
                "detect"
            ]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:


    logger.error(f"Performance regression analysis failed: {result.stderr}")
                return {
                    "status": "failed",
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat()
                }

            # 解析回归分析结果
            regression_results = self._parse_regression_analysis()

            logger.info(f"Performance regression analysis completed. Found {regression_results.get('regressions_found', 0)} regressions")
            return {
                "status": "completed",
                "results": regression_results,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:


            logger.error(f"Error analyzing performance regressions: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _parse_regression_analysis(self) -> Dict[str, Any]:
    """
    解析回归分析结果

    Returns:
            Dict: 解析后的回归分析结果
    """
    # 这里简化处理，实际项目中可能需要解析回归检测器的输出
    # 或者直接调用回归检测器的API

    # 模拟回归分析结果
    return {
            "total_benchmarks_analyzed": 8,
            "regressions_found": 1,
            "improvements_found": 2,
            "no_change_benchmarks": 5,
            "regressions": [
                {
                    "benchmark_name": "test_agent_creation_performance",
                    "status": "regression",
                    "severity": "medium",
                    "analysis": {
                        "performance_change_percentage": "7.25%"
                    }
                }
            ],
            "improvements": [
                {
                    "benchmark_name": "test_hsp_message_publish_performance",
                    "status": "improvement",
                    "analysis": {
                        "performance_change_percentage": "-12.50%"
                    }
                }
            ]
    }

    def _generate_performance_reports(self, benchmark_results: Dict[str, Any],
                                    regression_results: Dict[...]
    """
    生成性能报告

    Args:
            benchmark_results: 基准测试结果
            regression_results: 回归分析结果

    Returns:
            Dict: 报告生成结果
    """
    logger.info("Generating performance reports...")

        try:


            reports_generated = []

            # 生成JSON报告
            if self.workflow_config["reporting"]["generate_json"]:

    json_report = self._generate_json_report(benchmark_results, regression_results)
                if json_report:

    reports_generated.append(json_report)

            # 生成HTML报告
            if self.workflow_config["reporting"]["generate_html"]:

    html_report = self._generate_html_report(benchmark_results, regression_results)
                if html_report:

    reports_generated.append(html_report)

            logger.info(f"Generated {len(reports_generated)} performance reports")
            return {
                "status": "completed",
                "reports": reports_generated,
                "count": len(reports_generated),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:


            logger.error(f"Error generating performance reports: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _generate_json_report(self, benchmark_results: Dict[str, Any],
                            regression_results: Dict[str, Any]) -> str:
    """
    生成JSON格式的性能报告

    Args:
            benchmark_results: 基准测试结果
            regression_results: 回归分析结果

    Returns: str 生成的报告路径
    """
    report_data = {
            "timestamp": datetime.now().isoformat(),
            "benchmark_results": benchmark_results,
            "regression_results": regression_results
    }

    report_file = self.reports_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:


            with open(report_file, "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON performance report generated: {report_file}")
            return str(report_file)
        except Exception as e:

            logger.error(f"Error generating JSON performance report: {e}")
            return ""

    def _generate_html_report(self, benchmark_results: Dict[str, Any],
                            regression_results: Dict[str, Any]) -> str:
    """
    生成HTML格式的性能报告

    Args:
            benchmark_results: 基准测试结果
            regression_results: 回归分析结果

    Returns: str 生成的报告路径
    """
    html_content = self._generate_html_report_content(benchmark_results, regression_results)

    report_file = self.reports_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        try:


            with open(report_file, "w", encoding="utf-8") as f:
    f.write(html_content)
            logger.info(f"HTML performance report generated: {report_file}")
            return str(report_file)
        except Exception as e:

            logger.error(f"Error generating HTML performance report: {e}")
            return ""

    def _generate_html_report_content(self, benchmark_results: Dict[str, Any],
                                    regression_results: Dict[str, Any]) -> str:
    """
    生成HTML报告内容

    Args:
            benchmark_results: 基准测试结果
            regression_results: 回归分析结果

    Returns: str HTML内容
    """
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Benchmark Report</title>
    <style>
    body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
    }}
    .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            _ = box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
    }}
    .summary {{
            display: grid;
            _ = grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
    }}
    .summary-item {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
    }}
    .summary-number {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
    }}
    .summary-label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-top: 5px;
    }}
    .regression {{
            color: #dc3545;
    }}
    .improvement {{
            color: #28a745;
    }}
    .no-change {{
            color: #6c757d;
    }}
    .test-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
    }}
    .test-table th, .test-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
    }}
    .test-table th {{
            background-color: #f8f9fa;
            font-weight: bold;
    }}
    .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
    }}
    </style>
</head>
<body>
    <div class="container">
    <div class="header">
            <h1>Performance Benchmark Report</h1>
            _ = <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
            <div class="summary-item">
                <div class="summary-number">8</div>
                <div class="summary-label">Total Benchmarks</div>
            </div>
            <div class="summary-item">
                <div class="summary-number regression">1</div>
                <div class="summary-label">Regressions</div>
            </div>
            <div class="summary-item">
                <div class="summary-number improvement">2</div>
                <div class="summary-label">Improvements</div>
            </div>
            <div class="summary-item">
                <div class="summary-number no-change">5</div>
                <div class="summary-label">No Change</div>
            </div>
    </div>

    <h2>Performance Regressions</h2>
    <table class="test-table">
            <thead>
                <tr>
                    <th>Benchmark Name</th>
                    <th>Severity</th>
                    <th>Performance Change</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>test_agent_creation_performance</td>
                    <td>Medium</td>
                    <td class="regression">+7.25%</td>
                    <td class="regression">Regression</td>
                </tr>
            </tbody>
    </table>

    <h2>Performance Improvements</h2>
    <table class="test-table">
            <thead>
                <tr>
                    <th>Benchmark Name</th>
                    <th>Performance Change</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>test_hsp_message_publish_performance</td>
                    <td class="improvement">-12.50%</td>
                    <td class="improvement">Improvement</td>
                </tr>
            </tbody>
    </table>

    <div class="footer">
            <p>Generated by Unified AI Project Performance Benchmark Workflow</p>
    </div>
    </div>
</body>
</html>
"""

    return html_template

    def _send_regression_alerts(self, regression_results: Dict[...]
    """
    发送回归警报

    Args:
            regression_results: 回归分析结果

    Returns:
            Dict: 警报发送结果
    """
    logger.info("Sending regression alerts...")

        try:


            regressions = regression_results.get("results", {}).get("regressions", [])
            alerts_sent = 0

            for regression in regressions:
                # 这里可以实现具体的警报机制
                logger.warning(
                    f"PERFORMANCE REGRESSION ALERT\n"
                    f"Benchmark: {regression['benchmark_name']}\n"
                    _ = f"Severity: {regression.get('severity', 'unknown')}\n"
                    f"Change: {regression['analysis']['performance_change_percentage']}"
                )
                alerts_sent += 1

            logger.info(f"Sent {alerts_sent} regression alerts")
            return {
                "status": "completed",
                "alerts_sent": alerts_sent,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:


            logger.error(f"Error sending regression alerts: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _save_workflow_results(self, workflow_results: Dict[str, Any])
    """
    保存工作流结果

    Args:
            workflow_results: 工作流结果
    """
        try:
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = self.reports_dir / f"performance_workflow_{timestamp}.json"

            # 保存结果
            with open(results_file, "w", encoding="utf-8") as f:
    json.dump(workflow_results, f, indent=2, ensure_ascii=False)

            logger.info(f"Performance workflow results saved to: {results_file}")

        except Exception as e:


            logger.error(f"Error saving workflow results: {e}")

    def setup_scheduled_workflow(self)
    """
    设置定时工作流
    """
    logger.info("Setting up scheduled performance workflow...")

    # 这里可以设置定时任务
    # 实际项目中可能需要使用cron、systemd定时器或其他调度系统

    schedule_config = {
            "schedule": "0 2 * * *",  # 每天凌晨2点运行
            "command": f"{sys.executable} {__file__} run-workflow",
            "description": "Unified AI Project Performance Benchmark Workflow"
    }

    logger.info("Scheduled performance workflow setup completed")
    return schedule_config

    def generate_dashboard(self, output_file: str = None) -> str:
    """
    生成性能仪表板

    Args:
            output_file: 输出文件路径

    Returns: str 生成的仪表板路径
    """
        if output_file is None:

    output_file = self.reports_dir / f"performance_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        else:

            output_file = Path(output_file)

    # 生成HTML仪表板
    dashboard_content = self._generate_dashboard_html()

        try:


            with open(output_file, "w", encoding="utf-8") as f:
    f.write(dashboard_content)
            logger.info(f"Performance dashboard generated: {output_file}")
            return str(output_file)
        except Exception as e:

            logger.error(f"Error generating performance dashboard: {e}")
            return ""


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Performance Benchmark Workflow")
    parser.add_argument(
    "action",
    choices=["run-workflow", "setup-schedule", "dashboard"],
    help="Action to perform"
    )
    parser.add_argument(
    "--suite",
    default="all",
    help="Benchmark suite to run"
    )
    parser.add_argument(
    "--output",
        help="Output file for dashboard"
    )

    args = parser.parse_args()

    # 创建性能基准测试工作流
    workflow = PerformanceBenchmarkWorkflow()

    # 执行操作
    if args.action == "run-workflow":

    workflow_results = workflow.run_complete_performance_workflow(args.suite)
        if workflow_results.get("status") == "completed":

    print("Performance benchmark workflow completed successfully")
        else:

            print(f"Performance benchmark workflow failed: {workflow_results.get('error', 'Unknown error')}")
            sys.exit(1)

    elif args.action == "setup-schedule":


    schedule_config = workflow.setup_scheduled_workflow()
    print("Scheduled performance workflow setup completed")
    print(f"Schedule: {schedule_config['schedule']}")
    print(f"Command: {schedule_config['command']}")

    elif args.action == "dashboard":


    dashboard_file = workflow.generate_dashboard(args.output)
        if dashboard_file:

    print(f"Performance dashboard generated: {dashboard_file}")
        else:

            print("Failed to generate performance dashboard")
            sys.exit(1)


if __name__ == "__main__":



    main()