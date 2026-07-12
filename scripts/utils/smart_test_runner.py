#!/usr/bin/env python3
"""
智能測試運行器
"""

import logging
import re
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"


def setup_environment():
    """设置环境"""
    pass


def detect_test_errors(stderr_output: str, stdout_output: str) -> list:
    """检测测试错误"""
    errors = []
    full_output = (stdout_output or "") + (stderr_output or "")
    return errors


def run_tests(pytest_args=None) -> int:
    """运行测试"""
    print("==========================================")
    print("Unified AI Project Smart Test Runner")
    print("==========================================")

    setup_environment()

    cmd = ["python", "-m", "pytest", "--tb=short", "-v"]
    if pytest_args:
        cmd.extend(pytest_args.split())

    print(f"Running: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate()

        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

        if process.returncode != 0:
            print(f"Tests failed (exit code: {process.returncode})")
            return process.returncode
        else:
            print("All tests passed")
            return 0

    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main() -> None:
    """主函数"""
    pytest_args = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    exit_code = run_tests(pytest_args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()