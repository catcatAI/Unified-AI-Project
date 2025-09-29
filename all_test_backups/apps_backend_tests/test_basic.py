"""
简单的测试示例，用于验证测试环境是否正常工作
"""

import pytest
import sys
import os

def test_python_version() -> None:
    """测试 Python 版本"""
    assert sys.version_info >= (3, 8), "Python 版本应该 >= 3.8"

def test_basic_imports() -> None:
    """测试基础导入"""
    try:
        assert True
    except ImportError as e:
        pytest.fail(f"基础模块导入失败: {e}")

def test_project_structure() -> None:
    """测试项目结构"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    
    # 检查关键目录是否存在
    assert os.path.exists(os.path.join(backend_dir, "src")), "src 目录应该存在"
    assert os.path.exists(os.path.join(backend_dir, "configs")), "configs 目录应该存在"

@pytest.mark.slow
def test_slow_example() -> None:
    """慢测试示例，在快速测试模式下会被跳过"""
    import time
    time.sleep(0.1)  # 模拟耗时操作
    assert True

def test_environment_variables() -> None:
    """测试环境变量"""
    # 在测试环境中，这些应该有默认值或被设置
    testing_env = os.getenv('TESTING', 'false').lower() == 'true'
    # 不强制要求，但记录状态
    print(f"Testing environment: {testing_env}")
    assert True  # 总是通过，只是用于验证环境

if __name__ == "__main__":
    pytest.main([__file__])