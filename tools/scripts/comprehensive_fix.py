#!/usr/bin/env python3
"""
全面修复项目中的语法和缩进问题
"""

import re
from pathlib import Path

def fix_advanced_performance_optimizer():
    """修复advanced_performance_optimizer.py文件"""
    file_path = Path("apps/backend/src/core/hsp/advanced_performance_optimizer.py")
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复所有方法定义后的缩进问题
    # 匹配模式：def 方法名(参数): 后跟没有正确缩进的代码行
    pattern = r'(def \w+\([^)]*\):)\n(\s*)([^\s#])'
    content = re.sub(pattern, r'\1\n\2    \3', content)
    
    # 修复类的__init__方法缩进
    pattern = r'(class \w+:.*?def __init__\(.*?\):)\n(\s*)([^\s#])'
    content = re.sub(pattern, r'\1\n\2    \3', content, flags=re.DOTALL)
    
    # 修复所有类方法的缩进
    pattern = r'(class \w+:.*?)\n(\s*)(def \w+\()'
    content = re.sub(pattern, r'\1\n\2    \3', content, flags=re.DOTALL)
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复advanced_performance_optimizer.py文件: {file_path}")
    return True

def fix_extensibility():
    """修复extensibility.py文件"""
    file_path = Path("apps/backend/src/core/hsp/extensibility.py")
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复方法定义后的缩进问题
    pattern = r'(def \w+\([^)]*\):)\n(\s*)([^\s#])'
    content = re.sub(pattern, r'\1\n\2    \3', content)
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复extensibility.py文件: {file_path}")
    return True

def fix_versioning():
    """修复versioning.py文件"""
    file_path = Path("apps/backend/src/core/hsp/versioning.py")
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复方法定义后的缩进问题
    pattern = r'(def \w+\([^)]*\):)\n(\s*)([^\s#])'
    content = re.sub(pattern, r'\1\n\2    \3', content)
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复versioning.py文件: {file_path}")
    return True

def main():
    """主函数"""
    print("开始全面修复项目中的语法和缩进问题...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    import os
    os.chdir(project_root)
    
    # 修复各个文件
    fixes = [
        fix_advanced_performance_optimizer,
        fix_extensibility,
        fix_versioning,
    ]
    
    fixed_count = 0
    for fix_func in fixes:
        try:
            if fix_func():
                fixed_count += 1
        except Exception as e:
            print(f"修复过程中出现错误: {e}")
    
    print(f"修复完成，共修复了 {fixed_count} 个文件。")

if __name__ == "__main__":
    main()