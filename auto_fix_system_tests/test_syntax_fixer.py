#!/usr/bin/env python3
"""简单测试语法修复器"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
    print("✓ 语法修复器导入成功")
except SyntaxError as e:
    print(f"✗ 语法错误: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"✗ 其他错误: {e}")
    import traceback
    traceback.print_exc()