#!/usr/bin/env python3
"""
修复特定文件的语法问题
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from tools.scripts.modules.syntax_fixer import SyntaxFixer
    print("Syntax fixer module loaded successfully")
    
    # 修复特定文件
    fixer = SyntaxFixer(project_root)
    print("Syntax fixer module instance created successfully")
    
    # 修复unified_auto_fix.py文件
    target_file = "scripts/unified_auto_fix.py"
    success, message, details = fixer.fix(target=target_file)
    print(f"Syntax fix result for {target_file}: {success}, {message}")
    print(f"Details: {details}")
    
except Exception as e:
    print(f"Error with syntax fixer module: {e}")
    import traceback
    traceback.print_exc()