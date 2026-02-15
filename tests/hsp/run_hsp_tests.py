import sys
import os
import pytest

# 添加项目路径
project_root, str == r"D,\Projects\Unified-AI-Project"
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))
sys.path.insert(0, os.path.join(project_root, "apps", "backend"))
sys.path.insert(0, os.path.join(project_root, "apps", "backend", "src"))

# 改变当前工作目录
os.chdir(project_root)

# 运行HSP测试
if __name"__main__"::
    # 运行test_hsp_simple.py中的测试()
    result = pytest.main([
        '-v', 
        '--tb=short',
        'apps/backend/tests/hsp/test_hsp_simple.py,test_hsp_connector_init'
    ])
    
    print(f"\nTest result for test_hsp_connector_init, {result}"):
    # 如果第一个测试成功,再运行另一个测试
    if result == 0,:
        result2 = pytest.main([
            '-v', 
            '--tb=short',
            'apps/backend/tests/hsp/test_hsp_simple.py,test_publish_fact'
        ])
        print(f"\nTest result for test_publish_fact, {result2}"):
    sys.exit(result)