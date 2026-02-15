#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行器
用于执行测试套件并生成结果报告
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestRunner:
    """测试运行器"""

    def __init__(self, results_dir: str = "test_results") -> None:
        """
        初始化测试运行器

        Args:
            results_dir: 测试结果目录
        """
        # This script is run from apps/backend, so this path is relative to it.
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)

    def run_tests(self, test_paths: Optional[List[str]] = None, extra_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        运行测试套件

        Args:
            test_paths: 测试路径列表
            extra_args: 额外的pytest参数

        Returns:
            测试结果
        """
        # The CWD for the calling script (workflow_controller) is apps/backend.
        # We should run pytest from the project root for better discovery.
        project_root = Path.cwd().parent.parent
        
        report_file = Path.cwd() / self.results_dir / "latest_test_results.json"

        cmd = [
            sys.executable, 
            "-m", 
            "pytest",
            f"--json-report-file={report_file}",
            "--tb=short",
            "-v",
            "--cache-clear"
        ]

        if test_paths:
            cmd.extend(test_paths)
        else:
            # Only discover tests in the canonical 'tests' directory.
            cmd.append("tests")

        if extra_args:
            cmd.extend(extra_args)

        logger.info(f"Running test command: {' '.join(cmd)}")

        try:
            # Run pytest from the project root directory
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, check=False)

            print("--- PYTEST STDOUT ---")
            print(result.stdout)
            print("--- PYTEST STDERR ---")
            print(result.stderr)
            print("---------------------")

            # The pytest-json-report plugin handles saving the file.
            # We just return the process results.
            test_results = {
                "command": " ".join(cmd),
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            
            # For compatibility with the old logic, let's also save a timestamped copy
            if report_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_filename = Path.cwd() / self.results_dir / f"test_results_{timestamp}.json"
                try:
                    with report_file.open('r', encoding='utf-8') as f_in:
                        with archive_filename.open('w', encoding='utf-8') as f_out:
                            f_out.write(f_in.read())
                    logger.info(f"Test report archived to: {archive_filename}")
                except IOError as e:
                    logger.error(f"Could not archive test report: {e}")


            return test_results
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Add pytest mark to prevent it from being collected as a test
TestRunner.__test__ = False

def main() -> None:
    """主函数 for standalone execution (debugging)"""
    # This main block is for direct execution, assuming CWD is the project root.
    project_root = Path.cwd()
    results_dir = project_root / "test_results"
    runner = TestRunner(results_dir=str(results_dir))
    
    logger.info("Running TestRunner in standalone mode.")
    results = runner.run_tests()
    logger.info(f"Test run finished with exit code: {results.get('exit_code')}")


if __name__ == "__main__":
    main()
