import ast
import traceback
import sys

def check_syntax(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        print(f"文件 {file_path} 语法正确")
        return True
    except SyntaxError as e:
        print(f"文件 {file_path} 存在语法错误:")
        print(f"  行 {e.lineno}: {e.text.strip() if e.text else ''}")
        print(f"  错误信息: {e.msg}")
        if e.lineno:
            lines = content.split('\n')
            if e.lineno <= len(lines):
                print(f"  问题行内容: {lines[e.lineno-1]}")
        return False
    except Exception as e:
        print(f"检查文件 {file_path} 时发生错误: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_syntax(sys.argv[1])
    else:
        print("请提供文件路径作为参数")