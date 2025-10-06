import os
import sys
import subprocess

def check_syntax(file_path):
    """检查单个Python文件的语法"""
    try:
        # 使用Python的编译功能检查语法
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        compile(source, file_path, 'exec')
        return True, None
    except Exception as e:
        return False, str(e)

def check_project_syntax(root_path, max_checks=50):
    """检查项目中Python文件的语法"""
    error_files = []
    checked_count = 0
    
    for root, dirs, files in os.walk(root_path):
        # 跳过一些不需要检查的目录
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', 'backup_modules']]
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                is_valid, error = check_syntax(file_path)
                
                if not is_valid:
                    error_files.append((file_path, error))
                    print(f"语法错误: {file_path}")
                    print(f"  错误信息: {error}")
                
                checked_count += 1
                if checked_count >= max_checks:
                    print(f"已检查 {checked_count} 个文件，停止检查以节省时间。")
                    return error_files
    
    print(f"检查完成，共检查 {checked_count} 个文件。")
    if not error_files:
        print("未发现语法错误。")
    return error_files

if __name__ == "__main__":
    root_path = "d:\\Projects\\Unified-AI-Project"
    print("开始检查项目Python文件语法...")
    errors = check_project_syntax(root_path, max_checks=500)
    
    if errors:
        print(f"\n发现 {len(errors)} 个文件存在语法错误:")
        for file_path, error in errors:
            print(f"  {file_path}: {error}")
    else:
        print("\n未发现语法错误。")
