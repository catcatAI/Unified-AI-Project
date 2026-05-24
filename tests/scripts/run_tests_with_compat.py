#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行测试脚本(兼容性版本)
"""

import os
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)


def run_tests_with_compat() -> bool:
    """运行测试并解决兼容性问题"""
    os.environ['TF_USE_LEGACY_KERAS'] = '1'

    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    print("Setting up compatibility environment...")
    print(f"TF_USE_LEGACY_KERAS = {os.environ.get('TF_USE_LEGACY_KERAS', 'not set')}")

    try:
        cmd = [
            sys.executable, "-m", "pytest",
            "apps/backend/tests/",
            "-v",
            "--tb=short"
        ]

        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


if __name__ == "__main__":
    success = run_tests_with_compat()
    sys.exit(0 if success else 1)