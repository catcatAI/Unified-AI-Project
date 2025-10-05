#!/usr/bin/env python3
"""
检查文件中的语法错误
"""

with open('scripts/unified_auto_fix.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(f"Line 110 (index 109): {repr(lines[109])}")
    print(f"Line 110 content: {lines[109]}")