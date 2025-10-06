#!/usr/bin/env python3
"""修复语法修复器中的语法错误"""

with open('unified_auto_fix_system/modules/syntax_fixer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并修复问题行
lines = content.split('\n')
fixed_lines = []

for line in lines:
    if '                "pattern": r\'^\\\\s*(class|def|if|elif|else|for|while|try|except|finally|with)\\\\s+[^:]*' in line:
        # 修复这行
        fixed_line = '                "pattern": r\'^\\\\s*(class|def|if|elif|else|for|while|try|except|finally|with)\\\\s+[^:]*$\",'
        fixed_lines.append(fixed_line)
        print(f"Fixed line: {line[:50]}...")
    else:
        fixed_lines.append(line)

# 写回文件
with open('unified_auto_fix_system/modules/syntax_fixer.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print("语法错误已修复")