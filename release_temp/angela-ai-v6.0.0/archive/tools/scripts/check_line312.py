#!/usr/bin/env python3
"""
检查文件中的语法错误
"""

with open('scripts/unified_auto_fix.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(f"Line 312 (index 311): {repr(lines[311])}")
    print(f"Line 312 content: {lines[311]}")