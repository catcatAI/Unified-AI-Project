#!/usr/bin/env python3
"""
統計文件中的函數數量
"""

import re

def count_functions(filename):
    """統計文件中的頂層函數數量"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有頂層函數定義（不以空格開頭的def）
        functions = re.findall(r'^def\s+\w+.*$', content, re.MULTILINE)
        
        print(f'文件: {filename}')
        print(f'頂層函數數量: {len(functions)}')
        print('\n函數列表:')
        for i, func in enumerate(functions, 1):
            print(f'{i}: {func}')
        
        return len(functions)
    except Exception as e:
        print(f'錯誤: {e}')
        return 0

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('用法: python count_functions.py <文件名>')
        sys.exit(1)
    
    count_functions(sys.argv[1])