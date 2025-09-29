"""
修复Python模块导入路径的脚本
"""

import sys
import os

def fix_import_path():
    """修复Python导入路径以包含项目根目录"""
    # 获取项目根目录路径
    project_root: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 将项目根目录添加到Python路径的开头
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"已将项目根目录添加到Python路径: {project_root}")
    else:
        print(f"项目根目录已在Python路径中: {project_root}")
    
    # 验证是否可以导入apps模块
    try:
        print("成功导入apps.backend.src.services.multi_llm_service")
    except ImportError as e:
        print(f"仍然无法导入apps.backend.src.services.multi_llm_service: {e}")
    
    # 验证是否可以导入MultiLLMService
    try:
        print("成功从apps.backend.src.services.multi_llm_service导入MultiLLMService")
    except ImportError as e:
        print(f"仍然无法从apps.backend.src.services.multi_llm_service导入MultiLLMService: {e}")

if __name__ == "__main__":
    fix_import_path()