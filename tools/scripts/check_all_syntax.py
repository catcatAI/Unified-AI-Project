#!/usr/bin/env python3
"""
检查项目中所有Python文件的语法
"""

import os
import sys
import subprocess
from pathlib import Path

def find_python_files(root_path):
    """查找所有Python文件"""
    python_files = []
    exclude_dirs = {
        'node_modules', '__pycache__', '.git', 'venv', 'dist', 'build',
        'backup', 'chroma_db', 'context_storage', 'model_cache',
        'test_reports', 'automation_reports', 'docs', 'scripts/venv',
        'apps/backend/venv', 'apps/desktop-app', 'graphic-launcher', 'packages',
        '.benchmarks', '.crush', '.qoder', 'adaptive_learning_controller',
        'auto_fix_workspace/sandbox', 'backup_before_merge', 'backup_before_refactor',
        'backup_before_script_migration', 'configs', 'context_storage', 'docs',
        'graphic-launcher', 'model_cache', 'packages', 'scripts', 'stubs', 'templates',
        'test_data', 'test_reports', 'tools/modules', 'training'
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
    """检查单个文件的语法"""
    try:
        result = subprocess.run([sys.executable, '-m', 'py_compile', file_path], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, ""
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "检查超时"
    except Exception as e:
        return False, str(e)

def main():
    """主函数"""
    print("=== 检查项目中所有Python文件的语法 ===")
    
    project_root = Path(__file__).parent
    python_files = find_python_files(project_root)
    
    print(f"发现 {len(python_files)} 个Python文件")
    
    error_files = []
    success_count = 0
    
    # 检查每个文件
    for i, file_path in enumerate(python_files, 1):
        if i % 50 == 0:
            print(f"进度: {i}/{len(python_files)}")
            
        is_valid, error = check_syntax(file_path)
        if is_valid:
            success_count += 1
        else:
            error_files.append((file_path, error))
    
    # 输出结果
    print(f"\n检查完成!")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {len(error_files)} 个文件")
    
    if error_files:
        print(f"\n有语法错误的文件:")
        for file_path, error in error_files:
            print(f"  ✗ {file_path}")
            # 只显示错误信息的前200个字符
            error_preview = error[:200] + "..." if len(error) > 200 else error
            print(f"    错误: {error_preview}")
    
    return len(error_files)

if __name__ == "__main__":
    error_count = main()
    sys.exit(0 if error_count == 0 else 1)