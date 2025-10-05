#!/usr/bin/env python3
"""
查找并修复unified_symbolic_space.py中的语法错误
"""

content = None
with open('apps/backend/src/core_ai/symbolic_space/unified_symbolic_space.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复所有语法错误
fixes = [
    ('conn.commit', 'conn.commit()'),
    ('cursor.fetchone', 'cursor.fetchone()'),
    ('conn.close', 'conn.close()'),
    ('current_props =  if', 'current_props = {} if'),
    ('current_props =  #', 'current_props = {}  #'),
]

fixed_content = content
for old, new in fixes:
    fixed_content = fixed_content.replace(old, new)

# 特殊修复
fixed_content = fixed_content.replace(
    "current_symbol['properties'] if current_symbol else ",
    "current_symbol['properties'] if current_symbol else {}"
)

with open('apps/backend/src/core_ai/symbolic_space/unified_symbolic_space.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("已修复unified_symbolic_space.py中的语法错误")