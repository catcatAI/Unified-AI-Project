#!/usr/bin/env python3
"""
全面的类型检查脚本，用于识别项目中的所有类型问题
"""

import subprocess
import sys
import os
import json

def run_pyright_on_file(file_path):
    """对单个文件运行pyright并返回结果"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pyright', 
            '--outputjson',
            str(file_path)
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode <= 1:  # pyright返回码<=1表示成功运行
            try:
                output = json.loads(result.stdout)
                return output
            except json.JSONDecodeError:
                print(f"Warning: Could not parse pyright output for {file_path}")
                return None
        else:
            _ = print(f"Error running pyright on {file_path}: {result.stderr}")
            return None
    except Exception as e:
        _ = print(f"Error running pyright on {file_path}: {e}")
        return None

def get_python_files():
    """获取项目中的所有Python文件"""
    python_files = []
    exclude_dirs = {
        'node_modules', '__pycache__', '.git', 'venv', 'dist', 'build',
        'backup', 'chroma_db', 'context_storage', 'model_cache',
        'test_reports', 'automation_reports', 'docs', 'scripts/venv',
        'apps/backend/venv', 'apps/desktop-app', 'graphic-launcher', 'packages'
    }
    
    for root, dirs, files in os.walk('.'):
        # 排除不需要检查的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                # 排除特定文件
                if 'external_connector.py' not in file_path and 'install_gmqtt.py' not in file_path:
                    _ = python_files.append(file_path)
                    
    return python_files

def filter_errors_by_rule(errors, rule_to_filter):
    """根据规则过滤错误"""
    return [error for error in errors if error.get('rule') != rule_to_filter]

def main() -> None:
    """主函数"""
    _ = print("开始全面类型检查...")
    
    # 获取所有Python文件
    python_files = get_python_files()
    _ = print(f"找到 {len(python_files)} 个Python文件")
    
    # 存储所有错误
    all_errors = []
    
    # 对每个文件运行pyright
    for i, file_path in enumerate(python_files):
        if i % 50 == 0:
            _ = print(f"进度: {i}/{len(python_files)} 文件已检查")
            
        result = run_pyright_on_file(file_path)
        if result and 'generalDiagnostics' in result:
            # 过滤掉reportMissingImports错误，因为这些已经在配置文件中处理
            errors = filter_errors_by_rule(result['generalDiagnostics'], 'reportMissingImports')
            _ = all_errors.extend(errors)
    
    # 按文件分组错误
    errors_by_file = {}
    for error in all_errors:
        file_path = error.get('file', 'unknown')
        if file_path not in errors_by_file:
            errors_by_file[file_path] = []
        _ = errors_by_file[file_path].append(error)
    
    # 输出结果
    print(f"\n=== 检查完成，发现 {len(all_errors)} 个类型错误 ===")
    
    if all_errors:
        _ = print("\n详细错误信息:")
        for file_path, errors in errors_by_file.items():
            _ = print(f"\n文件: {file_path}")
            for error in errors:
                message = error.get('message', 'Unknown error')
                rule = error.get('rule', 'Unknown rule')
                range_info = error.get('range', {})
                start_line = range_info.get('start', {}).get('line', 0) + 1
                start_char = range_info.get('start', {}).get('character', 0)
                _ = print(f"  行 {start_line}, 字符 {start_char}: {message} [{rule}]")
    
    # 返回错误数量
    return len(all_errors)

if __name__ == "__main__":
    error_count = main()
    sys.exit(1 if error_count > 0 else 0)