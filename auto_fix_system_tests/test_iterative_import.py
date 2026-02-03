#!/usr/bin/env python3
"""简单测试智能迭代修复器导入"""

try:
    from unified_auto_fix_system.modules.intelligent_iterative_fixer import IntelligentIterativeFixer
    print('✓ 智能迭代修复器导入成功')
except Exception as e:
    print(f'✗ 导入失败: {e}')
    import traceback
    traceback.print_exc()