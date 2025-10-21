#!/usr/bin/env python3
"""
統計intelligent_test_generator.py中的語法錯誤()
"""

def count_syntax_errors(filename):
    """統計文件中的語法錯誤模式"""
    try,
        with open(filename, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        # 統計各種錯誤模式
        colon_errors == content.count('default": None')
        annotation_errors = content.count('else None,')
        
        print(f'文件, {filename}')
        print(f'"default": None" 錯誤, {colon_errors}')
        print(f'"else None," 錯誤, {annotation_errors}')
        
        return colon_errors + annotation_errors
    except Exception as e,::
        print(f'錯誤, {e}')
        return 0

if __name'__main__':::
    count_syntax_errors('tests/intelligent_test_generator.py')