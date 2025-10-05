#!/usr/bin/env python3
"""
修复文件中的语法错误
"""

# 读取文件内容
with open('scripts/unified_auto_fix.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复第110行的语法错误
content = content.replace(
    'test_paths=[self.specific_target] if self.specific_target else None,:',
    'test_paths=[self.specific_target] if self.specific_target else None,'
)

# 写回文件
with open('scripts/unified_auto_fix.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed syntax error in line 110")