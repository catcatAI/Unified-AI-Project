import sys
import os
import pytest

# 添加项目路径
project_root: str = r"D:\Projects\Unified-AI-Project"
_ = sys.path.insert(0, project_root)
_ = sys.path.insert(0, os.path.join(project_root, "src"))
_ = sys.path.insert(0, os.path.join(project_root, "apps", "backend"))
_ = sys.path.insert(0, os.path.join(project_root, "apps", "backend", "src"))

# 改变当前工作目录
_ = os.chdir(project_root)

# 运行简单的HSP测试
if __name__ == "__main__":
    # 运行test_hsp_connector.py中的简单测试
    result = pytest.main([
        '-v',
        '--tb=short',
        'apps/backend/tests/hsp/test_hsp_connector.py::test_hsp_connector_init'
    ])

    print(f"\nTest result for test_hsp_connector_init: {result}"):
 = sys.exit(result)