import sys
import os
import pytest

# 添加项目路径
project_root: str = r"D:\Projects\Unified-AI-Project"
# _ = sys.path.insert(0, project_root)
# _ = sys.path.insert(0, os.path.join(project_root, "src"))
# _ = sys.path.insert(0, os.path.join(project_root, "apps", "backend"))
# _ = sys.path.insert(0, os.path.join(project_root, "apps", "backend", "src"))

# 改变当前工作目录
# _ = os.chdir(project_root)

# 运行我们之前创建的验证测试
if __name__ == "__main__":
    result = pytest.main([
        '-v', 
        '--tb=short',
        'apps/backend/tests/test_hsp_fixture_fix.py'
    ])
    
#     _ = print(f"\nTest result: {result}")
#     _ = sys.exit(result)