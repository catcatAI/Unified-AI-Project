#!/usr/bin/env python3
"""
集成测试运行脚本
"""

import os
import sys
import argparse
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def run_command(command, cwd=None, capture_output=True):
    """运行命令并返回结果"""
    print(f"Executing: {' '.join(command) if isinstance(command, list) else command}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=False
        )
        return result
    except Exception as e:
        print(f"Error executing command: {e}")
        return None


def setup_test_environment() -> bool:
    """设置测试环境"""
    print("Setting up test environment...")
    project_root = Path(__file__).parent.parent.parent()
    os.chdir(project_root)
    return True


def run_integration_tests(test_type="all", markers=None, parallel=False) -> dict:
    """运行集成测试"""
    print(f"Running integration tests (type: {test_type})...")

    cmd = [sys.executable, "-m", "pytest"]

    if test_type == "all":
        cmd.extend(["tests/integration/", "-v"])
    else:
        cmd.extend([f"tests/integration/test_{test_type}_integration.py", "-v"])

    if markers:
        cmd.extend(["-m", markers])

    if parallel:
        cmd.extend(["-n", "auto"])

    start_time = time.time()
    result = run_command(cmd)
    end_time = time.time()

    return {
        "success": result is not None and result.returncode == 0,
        "return_code": result.returncode if result else -1,
        "execution_time": end_time - start_time,
        "stdout": result.stdout if result else "",
        "stderr": result.stderr if result else ""
    }


def generate_test_report(test_results, output_dir="test_reports") -> None:
    """生成测试报告"""
    print("Generating test report...")

    Path(output_dir).mkdir(exist_ok=True)

    report_data = {
        "timestamp": datetime.now().isoformat(),
        "test_results": test_results,
        "summary": {
            "execution_time": test_results.get("execution_time", 0)
        }
    }

    report_file = Path(output_dir) / f"integration_test_report_{int(time.time())}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"Test report saved to: {report_file}")


def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(description="Run integration tests")
    parser.add_argument("--type", choices=["all", "system", "performance"], default="all")
    parser.add_argument("--markers", help="pytest markers")
    parser.add_argument("--parallel", action="store_true")
    parser.add_argument("--no-setup", action="store_true")

    args = parser.parse_args()

    if not args.no_setup:
        if not setup_test_environment():
            return 1

    test_results = run_integration_tests(
        test_type=args.type,
        markers=args.markers,
        parallel=args.parallel
    )

    generate_test_report(test_results)

    return 0 if test_results.get("success", False) else 1


if __name__ == "__main__":
    sys.exit(main())