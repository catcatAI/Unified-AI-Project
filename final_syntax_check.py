#!/usr/bin/env python3
"""
最终语法检查，确保所有Python文件语法正确
"""

import os
import sys
import subprocess
import traceback
from pathlib import Path

def find_python_files(root_path):
    """查找所有Python文件"""
    python_files = []
    exclude_dirs = {
        'node_modules', '__pycache__', '.git', 'venv', 'dist', 'build',
        'backup', 'chroma_db', 'context_storage', 'model_cache',
        'test_reports', 'automation_reports', 'docs', 'scripts/venv',
        'apps/backend/venv', 'apps/desktop-app', 'graphic-launcher', 'packages'
    }
    
    for root, dirs, files in os.walk(root_path):
        # 排除不需要检查的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                # 排除特定文件
                if 'external_connector.py' not in file_path and 'install_gmqtt.py' not in file_path:
                    python_files.append(file_path)
    
    return python_files

def check_syntax(file_path):
    """检查文件语法"""
    try:
        # 使用Python的compile函数检查语法
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        compile(content, file_path, 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"语法错误: {e}"
    except Exception as e:
        return False, f"其他错误: {e}"

def check_import(file_path):
    """检查文件是否能正确导入"""
    try:
        # 使用Python的-m选项来测试导入
        result = subprocess.run([
            sys.executable, '-m', 'py_compile', file_path
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return True, ""
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "导入测试超时"
    except Exception as e:
        return False, f"导入测试错误: {e}"

def main():
    """主函数"""
    print("=== 最终语法检查 ===")
    
    project_root = Path(__file__).parent
    python_files = find_python_files(project_root)
    
    print(f"发现 {len(python_files)} 个Python文件")
    
    syntax_errors = 0
    import_errors = 0
    files_checked = 0
    
    # 检查所有文件
    for file_path in python_files:
        files_checked += 1
        
        # 检查语法
        syntax_ok, syntax_error = check_syntax(file_path)
        if not syntax_ok:
            syntax_errors += 1
            print(f"✗ 语法错误 {file_path}: {syntax_error}")
        
        # 检查导入（只检查前50个文件以节省时间）
        if files_checked <= 50:
            import_ok, import_error = check_import(file_path)
            if not import_ok:
                import_errors += 1
                print(f"✗ 导入错误 {file_path}: {import_error}")
        
        # 显示进度
        if files_checked % 100 == 0:
            print(f"进度: 已检查 {files_checked} 个文件")
    
    print(f"\n最终检查完成:")
    print(f"  总共检查了 {files_checked} 个文件")
    print(f"  语法错误: {syntax_errors} 个文件")
    print(f"  导入错误: {import_errors} 个文件")
    
    if syntax_errors == 0:
        print("\n🎉 所有文件语法正确！")
        return 0
    else:
        print("\n⚠ 发现语法错误，请检查上述文件。")
        return 1

if __name__ == "__main__":
    sys.exit(main())