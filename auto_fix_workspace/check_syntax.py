import ast

# 读取并验证文件
with open('test_real_syntax_errors.py', 'r', encoding='utf-8') as f:
    content = f.read()

try:
    ast.parse(content)
    print('文件没有语法错误')
except SyntaxError as e:
    print(f'语法错误: {e}')
except Exception as e:
    print(f'其他错误: {e}')