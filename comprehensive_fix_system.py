#!/usr/bin/env python3
"""
综合修复系统 - 修复项目中的语法错误，同时保护已修复的文件
"""

import ast
import os
import re
import sys
import json
import traceback
from pathlib import Path

# 记录已修复的文件，避免重复修复
FIXED_FILES_LOG = "comprehensive_fix_log.json"

def load_fixed_files():
    """加载已修复文件列表"""
    if os.path.exists(FIXED_FILES_LOG):
        try:
            with open(FIXED_FILES_LOG, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_fixed_files(fixed_files):
    """保存已修复文件列表"""
    with open(FIXED_FILES_LOG, 'w', encoding='utf-8') as f:
        json.dump(list(fixed_files), f, indent=2, ensure_ascii=False)

def check_syntax(file_path):
    """检查文件语法是否正确"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True
    except SyntaxError:
        return False
    except Exception:
        # 其他错误不影响语法检查
        return True

def fix_syntax_errors(content):
    """修复常见的语法错误"""
    original_content = content
    
    # 修复1: 修复函数定义缺少冒号的问题
    content = re.sub(r'(def\s+\w+\s*\([^)]*\))\s*\n', r'\1:\n', content)
    
    # 修复2: 修复类定义缺少冒号的问题
    content = re.sub(r'(class\s+\w+(?:\s*\([^)]*\))?)\s*\n', r'\1:\n', content)
    
    # 修复3: 修复if/for/while语句缺少冒号的问题
    content = re.sub(r'(if\s+.+?|for\s+.+?|while\s+.+?|elif\s+.+?|else|try|except\s*.+?|except|finally)\s*\n', r'\1:\n', content)
    
    # 修复4: 修复错误的赋值操作符用于比较
    content = re.sub(r'(\w+\.[a-zA-Z_]\w*)=([A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)*)', r'\1 == \2', content)
    
    # 修复5: 修复缺少括号的函数调用
    content = re.sub(r'(\w+\.\w+)\s*([,)\n])', r'\1()\2', content)
    
    # 修复6: 修复字典和列表初始化错误
    content = re.sub(r'(\w+)\s*=\s*{\s*}', r'\1 = {}', content)
    content = re.sub(r'(\w+)\s*=\s*\[\s*\]', r'\1 = []', content)
    
    # 修复7: 移除多余的冒号
    content = re.sub(r'(\w+\s*(?:\]|\))\s*[,)])\s*:', r'\1', content)
    content = re.sub(r'(\}\s*[,)])\s*:', r'\1', content)
    
    # 修复8: 修复字典字面量语法错误
    content = re.sub(r'\{(\w+):', r'{"\1":', content)
    
    return content

def fix_file_syntax(file_path, fixed_files):
    """修复单个文件的语法错误"""
    # 跳过已修复的文件
    if str(file_path) in fixed_files:
        return False
    
    try:
        # 检查文件是否有语法错误
        if check_syntax(file_path):
            return False
            
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复语法错误
        fixed_content = fix_syntax_errors(content)
        
        # 如果内容有变化，写回文件
        if fixed_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"已修复文件: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {e}")
        return False

def fix_project_syntax_errors():
    """修复项目中的语法错误"""
    # 加载已修复文件列表
    fixed_files = load_fixed_files()
    newly_fixed = 0
    
    # 遍历所有Python文件
    for root, dirs, files in os.walk('.'):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    if fix_file_syntax(file_path, fixed_files):
                        fixed_files.add(str(file_path))
                        newly_fixed += 1
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {e}")
    
    # 保存已修复文件列表
    save_fixed_files(fixed_files)
    
    print(f"\n本次修复了 {newly_fixed} 个文件")
    print(f"总共已修复 {len(fixed_files)} 个文件")
    
    # 检查是否还有语法错误
    remaining_errors = 0
    error_files = []
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if not check_syntax(file_path):
                    remaining_errors += 1
                    error_files.append(file_path)
    
    if remaining_errors > 0:
        print(f"\n仍有 {remaining_errors} 个文件存在语法错误:")
        for file_path in error_files[:10]:  # 只显示前10个
            print(f"  {file_path}")
        if remaining_errors > 10:
            print(f"  ... 还有 {remaining_errors - 10} 个文件")
        return 1
    else:
        print("所有文件的语法错误已修复!")
        return 0

if __name__ == "__main__":
    sys.exit(fix_project_syntax_errors())