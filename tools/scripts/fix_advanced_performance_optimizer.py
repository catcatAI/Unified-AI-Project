#!/usr/bin/env python3
"""
修复advanced_performance_optimizer.py文件中的缩进问题
"""

import re
from pathlib import Path

def fix_indentation_issues():
    """修复缩进问题"""
    file_path = Path("apps/backend/src/core/hsp/advanced_performance_optimizer.py")
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复缩进问题
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        
        # 检查是否有缩进问题的模式
        if stripped.startswith('def ') and not line.startswith('    '):
            # 这是一个方法定义，但缩进不正确
            fixed_lines.append(line.rstrip() + ':\n')
            i += 1
            # 修复接下来的代码块缩进
            while i < len(lines) and lines[i].strip():
                if not lines[i].startswith('    '):
                    fixed_lines.append('    ' + lines[i])
                else:
                    fixed_lines.append(lines[i])
                i += 1
            # 添加空行
            if i < len(lines) and not lines[i].strip():
                fixed_lines.append(lines[i])
                i += 1
        else:
            fixed_lines.append(line)
            i += 1
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"已修复缩进问题: {file_path}")
    return True

def main():
    """主函数"""
    print("开始修复advanced_performance_optimizer.py文件中的缩进问题...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    import os
    os.chdir(project_root)
    
    # 修复文件
    if fix_indentation_issues():
        print("文件修复完成。")
    else:
        print("文件修复失败。")

if __name__ == "__main__":
    main()