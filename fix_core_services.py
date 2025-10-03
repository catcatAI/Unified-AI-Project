#!/usr/bin/env python3
"""
修复 core_services.py 中的语法错误
"""

import os
import re

def fix_core_services_syntax():
    """修复 core_services.py 中的语法错误"""
    file_path = "apps/backend/src/core_services.py"
    
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复函数定义缺少冒号的问题
        content = re.sub(r'def get_BaseAgent\(\)', 'def get_BaseAgent():', content)
        content = re.sub(r'def get_AgentManager\(\)', 'def get_AgentManager():', content)
        content = re.sub(r'def get_HAMMemoryManager\(\)', 'def get_HAMMemoryManager():', content)
        
        # 修复 if 语句缺少冒号的问题
        content = re.sub(r'if hsp_connector_instance and learning_manager_instance and :', 
                        'if (hsp_connector_instance and learning_manager_instance and', content)
        
        # 修复其他语法问题
        content = re.sub(r'getattr\(module, \'BaseAgent\'\)\n    except ImportError:', 
                        'getattr(module, \'BaseAgent\')\n    except ImportError:', content)
        
        # 保存修复后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("core_services.py 语法错误修复完成")
        return True
        
    except Exception as e:
        print(f"修复过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    fix_core_services_syntax()