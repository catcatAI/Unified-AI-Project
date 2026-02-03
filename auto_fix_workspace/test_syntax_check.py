import ast
import traceback

def has_syntax_error(file_path: str) -> tuple[bool, str]:
    """检查文件是否有语法错误,如果有则返回错误信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return False, ""
    except SyntaxError as e:
        return True, str(e)
    except Exception as e:
        # 其他错误(如编码错误)
        return True, str(e)

# 测试函数
has_error, error_msg = has_syntax_error('scripts/auto_fix_project.py')
print(f"Has syntax error: {has_error}")
print(f"Error message: {error_msg}")