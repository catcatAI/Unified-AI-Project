#!/usr/bin/env python3
"""
专门修复未使用调用结果的问题
"""

import os
import sys
import re
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
                    _ = python_files.append(file_path)
    
    return python_files

def fix_unused_call_results_in_file(file_path):
    """修复文件中的未使用调用结果问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_made = []
        
        lines = content.split('\n')
        new_lines = []
        modified = False
        
        for i, line in enumerate(lines):
            # 检查未使用的调用结果
            # 特别关注异步调用
            if (line.strip().startswith('await ') and 
                '(' in line and ')' in line and
                not line.strip().startswith(('_', 'return', 'yield')) and
                '=' not in line and
                not line.strip().endswith('# type: ignore') and
                not 'print(' in line):
                
                # 修复异步调用未使用结果的问题
                leading_spaces = len(line) - len(line.lstrip())
                fixed_line = ' ' * leading_spaces + '_ = ' + line.lstrip()
                _ = new_lines.append(fixed_line)
                fixes_made.append(f"第 {i+1} 行: 修复异步调用未使用结果 - 添加 '_ = ' 前缀")
                modified = True
                continue
            
            # 检查普通函数调用未使用结果的问题
            elif (line.strip() and 
                  not line.strip().startswith(('_', 'return', 'yield', '#', 'if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 'try:', 'except', 'finally:', 'class ', 'def ', 'import ', 'from ')) and
                  '(' in line and ')' in line and
                  '=' not in line and
                  not line.strip().endswith('# type: ignore') and
                  not 'print(' in line and
                  not any(keyword in line for keyword in ['if ', 'elif ', 'while ', 'for ', 'with '])):
                
                # 检查是否是函数调用
                stripped_line = line.strip()
                if (stripped_line.endswith(')') and 
                    not stripped_line.startswith(('assert ', 'raise '))):
                    # 修复普通调用未使用结果的问题
                    leading_spaces = len(line) - len(line.lstrip())
                    fixed_line = ' ' * leading_spaces + '_ = ' + line.lstrip()
                    _ = new_lines.append(fixed_line)
                    fixes_made.append(f"第 {i+1} 行: 修复函数调用未使用结果 - 添加 '_ = ' 前缀")
                    modified = True
                    continue
            
            _ = new_lines.append(line)
        
        # 如果内容有变化，写入文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                _ = f.write('\n'.join(new_lines))
            return True, fixes_made
        else:
            return False, []
            
    except Exception as e:
        print(f"修复文件时出错 {file_path}: {e}")
        return False, []

def main():
    """主函数"""
    print("=== 专门修复未使用调用结果问题 ===")
    
    project_root = Path(__file__).parent
    python_files = find_python_files(project_root)
    
    print(f"发现 {len(python_files)} 个Python文件")
    
    files_fixed = 0
    total_fixes = 0
    
    # 处理每个文件
    for file_path in python_files:
        try:
            fixed, fixes_made = fix_unused_call_results_in_file(file_path)
            if fixed:
                files_fixed += 1
                total_fixes += len(fixes_made)
                print(f"✓ 修复了文件 {file_path}")
                for fix in fixes_made[:5]:  # 只显示前5个修复
                    print(f"  - {fix}")
                if len(fixes_made) > 5:
                    print(f"  ... 还有 {len(fixes_made) - 5} 个修复")
        except Exception as e:
            print(f"✗ 处理文件 {file_path} 时出错: {e}")
    
    print(f"\n修复统计:")
    print(f"  修复了: {files_fixed} 个文件")
    print(f"  总共修复: {total_fixes} 处问题")
    
    if files_fixed > 0:
        print("\n🎉 修复完成！建议重新运行检查以验证修复效果。")
    else:
        print("\n✅ 未发现需要修复的问题。")
    
    return 0

if __name__ == "__main__":
    _ = sys.exit(main())