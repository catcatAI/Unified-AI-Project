#!/usr/bin/env python3
"""
最终纠正重复的 '_ = ' 前缀问题
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
                    python_files.append(file_path)
    
    return python_files

def correct_duplicate_prefixes(file_path):
    """纠正重复的 '_ = ' 前缀"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixes_made = []
        modified = False
        
        for i, line in enumerate(lines):
            original_line = line
            
            # 修复重复的 "_ = " 问题
            if '_ = ' in line:
                fixed_line = line.replace('_ = ', '_ = ')
                lines[i] = fixed_line
                fixes_made.append(f"第 {i+1} 行: 修复重复的 '_ = ' 前缀")
                modified = True
                continue
            
            # 修复多个 "_ = " 前缀的问题
            if line.count('_ = ') > 1:
                # 只保留一个 "_ = " 前缀
                fixed_line = re.sub(r'(_ = )+', '_ = ', line)
                lines[i] = fixed_line
                fixes_made.append(f"第 {i+1} 行: 修复多个 '_ = ' 前缀")
                modified = True
                continue
        
        # 如果内容有变化，写入文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True, fixes_made
        else:
            return False, []
            
    except Exception as e:
        print(f"修复文件时出错 {file_path}: {e}")
        return False, []

def main():
    """主函数"""
    print("=== 最终纠正重复的 '_ = ' 前缀问题 ===")
    
    project_root = Path(__file__).parent
    python_files = find_python_files(project_root)
    
    print(f"发现 {len(python_files)} 个Python文件")
    
    files_fixed = 0
    total_fixes = 0
    
    # 处理每个文件
    for file_path in python_files:
        try:
            fixed, fixes_made = correct_duplicate_prefixes(file_path)
            if fixed:
                files_fixed += 1
                total_fixes += len(fixes_made)
                print(f"✓ 最终纠正了文件 {file_path}")
                for fix in fixes_made[:3]:  # 只显示前3个修复
                    print(f"  - {fix}")
                if len(fixes_made) > 3:
                    print(f"  ... 还有 {len(fixes_made) - 3} 个修复")
        except Exception as e:
            print(f"✗ 处理文件 {file_path} 时出错: {e}")
    
    print(f"\n最终纠正统计:")
    print(f"  最终纠正了: {files_fixed} 个文件")
    print(f"  总共纠正: {total_fixes} 处问题")
    
    if files_fixed > 0:
        print("\n🎉 最终纠正完成！")
    else:
        print("\n✅ 未发现需要最终纠正的问题。")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())