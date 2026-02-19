import sys
import os
import pytest
import logging
logger = logging.getLogger(__name__)

# 添加项目路径
project_root, str == r"D,\Projects\Unified-AI-Project"
# sys.path.insert(0, project_root)
# sys.path.insert(0, os.path.join(project_root, "src"))
# sys.path.insert(0, os.path.join(project_root, "apps", "backend"))
# sys.path.insert(0, os.path.join(project_root, "apps", "backend", "src"))

# 改变当前工作目录
# os.chdir(project_root)

# 运行我们之前创建的验证测试
if __name"__main__"::
    result = pytest.main([
        '-v', 
        '--tb=short',
        'apps/backend/tests/test_hsp_fixture_fix.py'
    ])
    
#     print(f"\nTest result, {result}")
#     sys.exit(result)