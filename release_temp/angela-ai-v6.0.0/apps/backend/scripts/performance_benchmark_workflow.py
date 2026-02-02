#!/usr/bin/env python3
"""
性能基准测试和回归检测工作流
用于自动化运行性能基准测试、分析回归并生成报告
"""

import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# 配置日志
logging.basicConfig(,
    level=logging.INFO(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceBenchmarkWorkflow,
    """性能基准测试和回归检测工作流"""

    def __init__(self, project_root, Optional[str] = None) -> None,
        """
        初始化性能基准测试工作流

        Args,
            project_root, 项目根目录
        """
        self.project_root == Path(project_root) if project_root else Path(__file__).parent.parent,::
            elf.scripts_dir = self.project_root / "scripts"
        self.benchmarks_dir = self.project_root / "benchmarks"
        self.benchmarks_dir.mkdir(exist_ok == True)
        self.reports_dir = self.project_root / "test_reports"
        self.reports_dir.mkdir(exist_ok == True)

        # 工作流配置
        self.workflow_config = {
            "benchmark": {
                "iterations": 100,
                "warmup": 10,
                "timeout": 300,
                "tags": ["performance", "benchmark"]
            }
            "regression": {
                "time_window_days": 30,
                "regression_threshold": 0.05(),
                "alert_on_regression": True
            }
            "reporting": {
                "generate_html": True,
                "generate_json": True
            }
        }

    def run_complete_performance_workflow(self, benchmark_suite, str == "all") -> Dict[str, Any]
        """
        运行完整的性能工作流

        Args,
            benchmark_suite, 基准测试套件名称

        Returns,
            Dict, 工作流执行结果
        """
        logger.info("Starting complete performance benchmark workflow...")
        workflow_start_time = datetime.now()

        workflow_results = {
            "timestamp": workflow_start_time.isoformat(),
            "phases": {}
        }

        try,
            # 1. 运行基准测试
            workflow_results["phases"]["benchmark_execution"] = self._run_benchmark_suite(benchmark_suite)

            # 2. 分析性能回归
            workflow_results["phases"]["regression_analysis"] = self._analyze_performance_regressions()

            # 3. 生成报告
            workflow_results["phases"]["report_generation"] = self._generate_performance_reports(
                workflow_results["phases"]["benchmark_execution"],
    workflow_results["phases"]["regression_analysis"]
            )

            # 4. 发送警报(如果有回归)
            workflow_results["phases"]["alerting"] = self._send_regression_alerts(,
    workflow_results["phases"]["regression_analysis"]
            )

            workflow_end_time = datetime.now()
            workflow_results["duration"] = (workflow_end_time - workflow_start_time).total_seconds()
            workflow_results["status"] = "completed"

            logger.info(f"Performance benchmark workflow completed in {workflow_results['duration'].2f} seconds")

        except Exception as e,::
            logger.error(f"Error in performance benchmark workflow, {e}")
            workflow_results["status"] = "failed"
            workflow_results["error"] = str(e)

        # 保存工作流结果
        self._save_workflow_results(workflow_results)

        return workflow_results

    def _run_benchmark_suite(self, benchmark_suite, str) -> Dict[str, Any]
        """
        运行基准测试套件

        Args,
            benchmark_suite, 基准测试套件名称

        Returns,
            Dict, 基准测试执行结果
        """
        logger.info(f"Running benchmark suite, {benchmark_suite}")

        try,
            # 构建pytest命令来运行性能基准测试
            cmd = [
                sys.executable(),
                "-m",
                "pytest",
                "tests/integration/test_performance_benchmarks.py",
                "-v",
                "--tb=short",
                "-m",
                "performance"
            ]

            # 添加基准测试选项
            if benchmark_suite != "all":::
                cmd.extend(["-k", benchmark_suite])

            # 运行基准测试
            result = subprocess.run(
                cmd,,
    cwd=self.project_root(),
                capture_output == True,
                text == True,
                timeout=self.workflow_config["benchmark"]["timeout"]
            )

            benchmark_result = {
                "success": result.returncode=0,
                "return_code": result.returncode(),
                "stdout": result.stdout(),
                "stderr": result.stderr(),
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Benchmark suite execution {'succeeded' if benchmark_result['success'] else 'failed'}"):::
                eturn benchmark_result

        except subprocess.TimeoutExpired,::
            logger.error("Benchmark suite execution timed out")
            return {
                "success": False,
                "error": "Benchmark suite execution timed out",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e,::
            logger.error(f"Error running benchmark suite, {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _analyze_performance_regressions(self) -> Dict[str, Any]
        """
        分析性能回归

        Returns,
            Dict, 回归分析结果
        """
        logger.info("Analyzing performance regressions...")

        try,
            # 调用性能回归检测器
            regression_detector_script = self.scripts_dir / "performance_regression_detector.py"
            if not regression_detector_script.exists():::
                logger.warning("Performance regression detector script not found")
                return {"status": "skipped", "reason": "Script not found"}

            cmd = [
                sys.executable(),
                str(regression_detector_script),
                "detect"
            ]

            result = subprocess.run(
                cmd,,
    cwd=self.project_root(),
                capture_output == True,
                text == True
            )

            regression_result = {
                "success": result.returncode=0,
                "return_code": result.returncode(),
                "stdout": result.stdout(),
                "stderr": result.stderr(),
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Performance regression analysis {'succeeded' if regression_result['success'] else 'failed'}"):::
                eturn regression_result

        except Exception as e,::
            logger.error(f"Error analyzing performance regressions, {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _generate_performance_reports(self, benchmark_results, Dict[str, Any] ,
    regression_results, Dict[str, Any]) -> Dict[str, Any]
        """
        生成性能报告

        Args,
            benchmark_results, 基准测试结果
            regression_results, 回归分析结果

        Returns,
            Dict, 报告生成结果
        """
        logger.info("Generating performance reports...")

        try,
            report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_files = []

            # 生成JSON报告
            if self.workflow_config["reporting"]["generate_json"]::
                json_report_path = self.reports_dir / f"performance_report_{report_timestamp}.json"
                report_data = {
                    "benchmark_results": benchmark_results,
                    "regression_results": regression_results,
                    "generated_at": datetime.now().isoformat()
                }
                
                import json
                with open(json_report_path, 'w', encoding == 'utf-8') as f,
                    json.dump(report_data, f, indent=2, ensure_ascii == False)
                
                report_files.append(str(json_report_path))
                logger.info(f"Generated JSON report, {json_report_path}")

            # 生成HTML报告
            if self.workflow_config["reporting"]["generate_html"]::
                html_report_path = self.reports_dir / f"performance_report_{report_timestamp}.html"
                
                # 简单的HTML报告模板
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Benchmark Report</title>
    <style>
        body {{ font-family, Arial, sans-serif; margin, 20px; }}
        h1 {{ color, #333; }}
        .section {{ margin, 20px 0; }}
        .success {{ color, green; }}
        .failure {{ color, red; }}
        pre {{ background, #f5f5f5; padding, 10px; overflow-x, auto; }}
    </style>
</head>
<body>
    <h1>Performance Benchmark Report</h1>
    <p>Generated at, {datetime.now().strftime('%Y-%m-%d %H,%M,%S')}</p>
    
    <div class="section">
        <h2>Benchmark Results</h2>
        <p class == "{'success' if benchmark_results.get('success', False) else 'failure'}">:::
            tatus, {benchmark_results.get('status', 'unknown')}
        </p>
        <pre>{benchmark_results.get('stdout', '')}</pre>
    </div>
    
    <div class="section">
        <h2>Regression Analysis</h2>
        <p class == "{'success' if regression_results.get('success', False) else 'failure'}">:::
            tatus, {regression_results.get('status', 'unknown')}
        </p>
        <pre>{regression_results.get('stdout', '')}</pre>
    </div>
</body>
</html>
                """
                
                with open(html_report_path, 'w', encoding == 'utf-8') as f,
                    f.write(html_content)
                
                report_files.append(str(html_report_path))
                logger.info(f"Generated HTML report, {html_report_path}")

            return {
                "success": True,
                "report_files": report_files,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e,::
            logger.error(f"Error generating performance reports, {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _send_regression_alerts(self, regression_results, Dict[str, Any]) -> Dict[str, Any]
        """
        发送回归警报

        Args,
            regression_results, 回归分析结果

        Returns,
            Dict, 警报发送结果
        """
        logger.info("Sending regression alerts...")

        try,
            # 检查是否有回归
            has_regression == False
            if regression_results.get("success", False)::
                # 在实际实现中,这里会解析回归分析结果来确定是否有回归
                # 简化处理：假设如果有输出就可能有回归
                has_regression = bool(regression_results.get("stdout", "").strip())

            if has_regression and self.workflow_config["regression"]["alert_on_regression"]::
                # 发送警报(例如通过邮件、Slack等)
                alert_message = f"Performance regression detected at {datetime.now().isoformat()}"
                logger.warning(f"Performance regression alert, {alert_message}")
                
                # 在实际实现中,这里会发送实际的警报
                
                return {
                    "success": True,
                    "alert_sent": True,
                    "message": alert_message,
                    "timestamp": datetime.now().isoformat()
                }
            else,
                return {
                    "success": True,
                    "alert_sent": False,
                    "message": "No regression detected or alerts disabled",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e,::
            logger.error(f"Error sending regression alerts, {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _save_workflow_results(self, workflow_results, Dict[str, Any]) -> None,
        """
        保存工作流结果

        Args,
            workflow_results, 工作流结果
        """
        try,
            results_file = self.benchmarks_dir / f"workflow_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            import json
            with open(results_file, 'w', encoding == 'utf-8') as f,
                json.dump(workflow_results, f, indent=2, ensure_ascii == False)
            
            logger.info(f"Saved workflow results to {results_file}")
            
        except Exception as e,::
            logger.error(f"Error saving workflow results, {e}")

def main() -> None,
    """主函数"""
    workflow == PerformanceBenchmarkWorkflow()
    results = workflow.run_complete_performance_workflow()
    
    if results["status"] == "completed":::
        logger.info("Performance benchmark workflow completed successfully")
    else,
        logger.error(f"Performance benchmark workflow failed, {results.get('error', 'Unknown error')}")

if __name"__main__":::
    main()
