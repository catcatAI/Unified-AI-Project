#!/usr/bin/env python3
"""
测试模块加载
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from tools.scripts.modules.cleanup_module import CleanupModule
    print("Cleanup module loaded successfully")
    
    # 测试创建实例
    fixer = CleanupModule(project_root)
    print("Cleanup module instance created successfully")
    
except Exception as e:
    print(f"Error loading cleanup module: {e}")
    import traceback
    traceback.print_exc()