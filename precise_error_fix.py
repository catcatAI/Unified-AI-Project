#!/usr/bin/env python3
"""
精确修复脚本 - 修复特定的语法错误模式
"""

import ast
import os
import re
import sys
from pathlib import Path

def fix_specific_syntax_errors(file_path):
    """修复特定的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 保存原始内容用于比较
        original_content = content
        
        # 修复1: 修复错误的赋值操作符用于比较
        # 将 result.status=FixStatus.SUCCESS 替换为 result.status == FixStatus.SUCCESS
        content = re.sub(r'(\w+\.\w+)\s*=\s*([A-Z_][A-Z0-9_]*)', r'\1 == \2', content)
        
        # 修复2: 移除多余的冒号
        # 修复类似 "key": value,: 的语法错误
        content = re.sub(r'(:\s*\n?\s*):', r'\1', content)
        content = re.sub(r'(\w+\s*[,)])\s*:', r'\1', content)
        content = re.sub(r'(\}\s*[,)])\s*:', r'\1', content)
        content = re.sub(r'(\]\s*[,)])\s*:', r'\1', content)
        
        # 修复3: 修复字典字面量语法错误
        # 修复类似 {key: value,} 的语法错误（缺少引号）
        content = re.sub(r'\{(\w+):', r'{"\1":', content)
        
        # 如果内容有变化，则写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已修复文件: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {e}")
        return False

def check_syntax(file_path):
    """检查文件语法是否正确"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True
    except SyntaxError as e:
        return False
    except Exception as e:
        print(f"检查文件 {file_path} 时出错: {e}")
        return False

def fix_project_syntax_errors():
    """修复项目中的语法错误"""
    fixed_count = 0
    error_files = []
    
    # 遍历所有Python文件
    for root, dirs, files in os.walk('.'):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    # 先检查是否有语法错误
                    if not check_syntax(file_path):
                        # 尝试修复
                        if fix_specific_syntax_errors(file_path):
                            fixed_count += 1
                            # 验证修复后是否还有语法错误
                            if not check_syntax(file_path):
                                error_files.append(file_path)
                        else:
                            error_files.append(file_path)
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {e}")
                    error_files.append(file_path)
    
    print(f"\n总共修复了 {fixed_count} 个文件")
    if error_files:
        print(f"\n仍有语法错误的文件 ({len(error_files)} 个):")
        for file_path in error_files[:10]:  # 只显示前10个
            print(f"  {file_path}")
        if len(error_files) > 10:
            print(f"  ... 还有 {len(error_files) - 10} 个文件")
        return 1
    else:
        print("所有文件的语法错误已修复!")
        return 0

if __name__ == "__main__":
    sys.exit(fix_project_syntax_errors())