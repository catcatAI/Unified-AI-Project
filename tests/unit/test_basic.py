"""
简单的测试示例,用于验证测试环境是否正常工作
"""

import logging
import os
import sys

import pytest

logger = logging.getLogger(__name__)


def test_python_version():
    """测试 Python 版本"""
    assert sys.version_info >= (3, 8), "Python 版本应该 >= 3.8"


def test_basic_imports():
    """测试基础导入"""
    import asyncio
    import json

    assert json.dumps({"a": 1}) == '{"a": 1}'
    assert asyncio is not None


def test_project_structure():
    """测试项目结构"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # tests/unit/ 往上兩層才到專案根目錄
    project_dir = os.path.dirname(os.path.dirname(current_dir))

    # 检查关键目录是否存在
    assert os.path.exists(os.path.join(project_dir, "apps")), "apps 目录应该存在"
    assert os.path.exists(os.path.join(project_dir, "tests")), "tests 目录应该存在"


@pytest.mark.slow()
def test_slow_example():
    """慢测试示例,在快速测试模式下会被跳过"""
    import time

    t0 = time.time()
    time.sleep(0.1)  # 模拟耗时操作
    elapsed = time.time() - t0
    assert elapsed >= 0.09, f"Sleep was only {elapsed:.3f}s"


def test_environment_variables():
    """测试环境变量"""
    testing_env = os.getenv("TESTING", "false").lower() == "true"
    assert isinstance(testing_env, bool)


if __name__ == "__main__":
    pytest.main([__file__])
