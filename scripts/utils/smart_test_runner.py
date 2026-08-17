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
    """设置环境：确保 src 可导入、PYTHONPATH 就绪。"""
    src = SRC_DIR if SRC_DIR.is_dir() else PROJECT_ROOT / "apps" / "backend" / "src"
    src_str = str(src)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
    root_str = str(PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def detect_test_errors(stderr_output: str, stdout_output: str) -> list:
    """检测测试错误：从 pytest 输出中提取失败/错误行。

    返回 (line_no, severity, message) 三元组列表。
    """
    errors = []
    full_output = (stdout_output or "") + (stderr_output or "")
    for line in full_output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^FAILED\s", stripped) or re.match(r"^ERROR\s", stripped):
            errors.append((len(errors) + 1, "FAIL", stripped))
        elif re.match(r"^PASSED\s", stripped):
            pass  # not an error
        elif "assert" in stripped and "Error" in stripped:
            errors.append((len(errors) + 1, "ASSERT", stripped))
        elif re.search(r"(?:Error|Exception|Traceback):", stripped):
            errors.append((len(errors) + 1, "EXC", stripped[:200]))
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
            detected = detect_test_errors(stderr, stdout)
            if detected:
                print(f"Detected {len(detected)} error(s):")
                for _i, severity, message in detected[:20]:
                    print(f"  [{severity}] {message}")
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