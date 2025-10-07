#!/usr/bin/env python3
"""
詳細語法分析器
"""

import ast
import sys

def analyze_syntax(filename):
    """詳細分析文件的語法錯誤"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 嘗試解析AST
        ast.parse(source)
        print(f'✅ {filename} 語法完全正確')
        return True
        
    except SyntaxError as e:
        print(f'❌ {filename} 語法錯誤:')
        print(f'   位置: 第{e.lineno}行')
        print(f'   信息: {e.msg}')
        
        # 顯示上下文
        lines = source.split('\n')
        error_line = e.lineno - 1
        start = max(0, error_line - 2)
        end = min(len(lines), error_line + 3)
        
        print(f'   上下文:')
        for i in range(start, end):
            marker = '>>>' if i == error_line else '   '
            print(f'   {marker} {i+1}: {lines[i]}')
        
        return False
        
    except Exception as e:
        print(f'❌ {filename} 其他錯誤: {e}')
        return False

if __name__ == '__main__':
    analyze_syntax('tests/intelligent_test_generator.py')