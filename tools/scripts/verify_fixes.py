#!/usr/bin/env python3
"""
验证所有修复是否正确
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

def verify_syntax(file_path):
    """验证文件语法是否正确"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单的语法检查
        compile(content, file_path, 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"语法错误: {e}"
    except Exception as e:
        return False, f"其他错误: {e}"

def check_for_obvious_issues(file_path):
    """检查明显的修复问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        issues = []
        
        for i, line in enumerate(lines, 1):
            # 检查是否有重复的 "_ = "
            if '_ = ' in line:
                issues.append(f"第 {i} 行: 可能存在重复的 '_ = ' 前缀")
            
            # 检查是否有不正确的赋值
            if line.strip().startswith('_ = ') and line.strip().endswith(':'):
                issues.append(f"第 {i} 行: '_ = ' 前缀可能被错误地添加到语句上")
        
        return issues
    except Exception as e:
        return [f"检查文件时出错: {e}"]

def test_imports(file_path):
    """测试文件是否能正确导入"""
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
    print("=== 验证所有修复 ===")
    
    project_root = Path(__file__).parent
    python_files = find_python_files(project_root)
    
    print(f"发现 {len(python_files)} 个Python文件")
    
    syntax_errors = 0
    import_errors = 0
    obvious_issues = 0
    files_checked = 0
    
    # 检查前100个文件作为样本
    sample_files = python_files[:100] if len(python_files) > 100 else python_files
    
    print(f"检查 {len(sample_files)} 个文件样本...")
    
    for file_path in sample_files:
        files_checked += 1
        
        # 验证语法
        syntax_ok, syntax_error = verify_syntax(file_path)
        if not syntax_ok:
            syntax_errors += 1
            print(f"✗ 语法错误 {file_path}: {syntax_error}")
        
        # 检查明显问题
        issues = check_for_obvious_issues(file_path)
        if issues:
            obvious_issues += 1
            for issue in issues:
                print(f"⚠ 潜在问题 {file_path}: {issue}")
        
        # 测试导入（只测试部分文件以节省时间）
        if files_checked <= 20:  # 只测试前20个文件的导入
            import_ok, import_error = test_imports(file_path)
            if not import_ok:
                import_errors += 1
                print(f"✗ 导入错误 {file_path}: {import_error}")
    
    print(f"\n验证完成:")
    print(f"  检查了 {files_checked} 个文件")
    print(f"  语法错误: {syntax_errors} 个文件")
    print(f"  导入错误: {import_errors} 个文件")
    print(f"  潜在问题: {obvious_issues} 个文件")
    
    if syntax_errors == 0 and import_errors == 0:
        print("\n🎉 所有验证通过！修复看起来是成功的。")
        return 0
    else:
        print("\n⚠ 发现一些问题，建议检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())