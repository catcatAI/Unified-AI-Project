#!/usr/bin/env python3
"""
修复文件中的语法错误
"""

# 读取文件内容
with open('scripts/unified_auto_fix.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复第312行的语法错误
content = content.replace(
    'print(f"总体结果: {\'✓ 成功\' if success else \'✗ 失败\'})":',
    'print(f"总体结果: {\'✓ 成功\' if success else \'✗ 失败\'})"'
)

# 写回文件
with open('scripts/unified_auto_fix.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed syntax error in line 312")