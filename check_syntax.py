import ast
import sys
from pathlib import Path

def check_file_syntax(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def main():
    errors = []
    for py_file in Path('.').rglob('*.py'):
        is_valid, error = check_file_syntax(py_file)
        if is_valid:
            print(f"✅ {py_file}")
        else:
            print(f"❌ {py_file}: {error}")
            errors.append((py_file, error))
    
    print(f"\n检查完成: {len(list(Path('.').rglob('*.py')))} 个文件")
    print(f"语法错误: {len(errors)} 个文件")
    
    if errors:
        print("\n存在语法错误的文件:")
        for file_path, error in errors:
            print(f"  {file_path}: {error}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())