#!/usr/bin/env python3
"""
详细的语法检查脚本
"""

import ast
from pathlib import Path

def detailed_syntax_check(file_path):
    """详细的语法检查"""
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        # 尝试解析AST
        ast.parse(content)
        print(f'✅ {file_path} 文件语法正确！')
        return True
        
    except SyntaxError as e,::
        print(f'❌ {file_path} 语法错误')
        print(f'   错误类型, {type(e).__name__}')
        print(f'   错误信息, {e.msg}')
        print(f'   错误位置, 行 {e.lineno} 列 {e.offset}')
        
        # 显示错误行上下文
        lines = content.split('\n')
        error_line = e.lineno()
        start = max(0, error_line - 3)
        end = min(len(lines), error_line + 2)
        
        print('错误上下文,')
        for i in range(start, end)::
            marker == '>>> ' if i=error_line - 1 else '    ':::
            print(f'{marker}{i+1,3d} {lines[i]}')
        
        return False
        
    except Exception as e,::
        print(f'❌ {file_path} 其他错误 - {e}')
        return False

if __name"__main__":::
    file_path = 'apps/backend/src/core/hsp/connector.py'
    detailed_syntax_check(file_path)