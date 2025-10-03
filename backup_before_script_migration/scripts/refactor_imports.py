#!/usr/bin/env python3
"""
自动化重构脚本，用于更新项目中的导入路径
"""

import os
import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 导入路径映射表
IMPORT_MAPPINGS = {
    # BaseAgent 导入更新
    r'from agents\.base_agent import BaseAgent': 'from apps.backend.src.ai.agents.base.base_agent import BaseAgent',
    r'from hsp\.types import ': 'from apps.backend.src.core.hsp.types import ',
    r'from memory\.ham_memory_manager import ': 'from apps.backend.src.ai.memory.ham_memory_manager import ',
    r'from memory\.ham_types import ': 'from apps.backend.src.ai.memory.ham_types import ',
    r'from core_services import ': 'from apps.backend.src.core_services import ',
    r'from managers\.agent_manager import ': 'from apps.backend.src.managers.agent_manager import ',
    r'from ai\.learning\.learning_manager import ': 'from apps.backend.src.ai.learning.learning_manager import ',
    r'from ai\.agents\.base\.base_agent import ': 'from apps.backend.src.ai.agents.base.base_agent import ',
}

def update_imports_in_file(file_path):
    """
    更新单个文件中的导入路径
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 应用所有导入路径更新
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = re.sub(old_import, new_import, content)
        
        # 如果内容有变化，则写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated imports in {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def find_python_files(directory):
    """
    查找目录中的所有Python文件
    """
    python_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过备份目录和隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__' and 'backup' not in d.lower()]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """
    主函数
    """
    print("Starting import path refactoring...")
    
    # 查找所有Python文件
    python_files = find_python_files(PROJECT_ROOT / 'apps' / 'backend' / 'src')
    
    updated_count = 0
    error_count = 0
    
    # 更新每个文件中的导入路径
    for file_path in python_files:
        try:
            if update_imports_in_file(file_path):
                updated_count += 1
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            error_count += 1
    
    print(f"Refactoring complete. Updated {updated_count} files, encountered {error_count} errors.")

if __name__ == '__main__':
    main()