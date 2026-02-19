import sys
import os
import pytest
import logging
logger = logging.getLogger(__name__)

# 添加项目路径到Python路径
project_root, str = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# 运行测试
if __name"__main__":::
    # 改变当前工作目录到项目根目录
    os.chdir(project_root)
    
    # 运行测试
    result = pytest.main([
        '-v', 
        '--tb=short',
        'apps/backend/tests/test_hsp_fixture_fix.py'
    ])
    
    print(f"Test result, {result}")
    sys.exit(result)