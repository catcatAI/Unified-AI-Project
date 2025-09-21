import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

try:
    from core_services import initialize_services, get_services, shutdown_services
    print('core_services imported successfully')
except ImportError as e:
    print(f'Failed to import core_services: {e}')