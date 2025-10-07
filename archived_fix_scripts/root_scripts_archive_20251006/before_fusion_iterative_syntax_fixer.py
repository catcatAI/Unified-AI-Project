#!/usr/bin/env python3
"""
迭代语法修复脚本
自动修复简单的缩进和语法错误
"""

import subprocess
import sys
import re
from pathlib import Path

def check_syntax(file_path):
    """检查文件语法"""
    result = subprocess.run([sys.executable, '-m', 'py_compile', str(file_path)], 
                          capture_output=True, text=True)
    return result.returncode == 0, result.stderr

def try_auto_fix_indentation(file_path, error_line):
    """尝试自动修复缩进错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if error_line > len(lines):
            return False
        
        line = lines[error_line - 1]
        if not line.strip() or line.startswith('#'):
            return False
        
        # 获取上下文信息
        context_start = max(0, error_line - 5)
        context_end = min(len(lines), error_line + 5)
        
        print(f"错误行上下文（第{error_line}行）:")
        for i in range(context_start, context_end):
            marker = ">>> " if i == error_line - 1 else "    "
            print(f"{marker}{i+1:3d}: {lines[i].rstrip()}")
        
        # 简单的缩进修复策略
        stripped = line.lstrip()
        if not stripped:
            return False
        
        # 基于上下文的缩进修复
        if error_line > 1:
            prev_line = lines[error_line - 2]
            prev_indent = len(prev_line) - len(prev_line.lstrip())
            
            # 如果上一行以冒号结尾，增加缩进
            if prev_line.rstrip().endswith(':'):
                new_indent = ' ' * (prev_indent + 4)
            # 如果是类或函数定义，使用基础缩进
            elif stripped.startswith(('def ', 'class ', 'async def')):
                new_indent = ' ' * (prev_indent if prev_indent >= 4 else 4)
            else:
                # 与上一行保持相同缩进
                new_indent = ' ' * prev_indent
            
            new_line = new_indent + stripped + '\n'
            
            if new_line != line:
                lines[error_line - 1] = new_line
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                print(f"✅ 修复了第{error_line}行的缩进")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ 自动修复失败: {e}")
        return False

def iterative_fix(file_path, max_attempts=20):
    """迭代修复直到语法正确或达到最大尝试次数"""
    file_path = Path(file_path)
    
    print(f"开始迭代修复: {file_path}")
    print("=" * 60)
    
    for attempt in range(max_attempts):
        syntax_ok, error_msg = check_syntax(file_path)
        
        if syntax_ok:
            print(f"🎉 第{attempt+1}次验证: 语法正确！")
            return True
        
        # 提取错误信息
        if 'line' in error_msg:
            try:
                line_match = re.search(r'line (\d+)', error_msg)
                if line_match:
                    error_line = int(line_match.group(1))
                    print(f"第{attempt+1}次验证: 第{error_line}行有语法错误")
                    print(f"错误类型: {error_msg.split('(')[0].strip()}")
                    
                    # 尝试自动修复
                    if try_auto_fix_indentation(file_path, error_line):
                        continue
                    else:
                        print(f"⚠️  第{error_line}行需要手动修复")
                        return False
                        
            except Exception as e:
                print(f"❌ 解析错误信息失败: {e}")
        
        print(f"第{attempt+1}次验证: 需要手动处理")
        return False
    
    print(f"⚠️  达到最大尝试次数({max_attempts})，仍有语法错误")
    return False

def main():
    """主函数"""
    print("迭代语法修复工具")
    print(f"开始时间: {__import__('datetime').datetime.now()}")
    print()
    
    file_path = 'apps/backend/src/core/hsp/connector.py'
    success = iterative_fix(file_path)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 文件语法修复完成！")
    else:
        print("⚠️  文件仍需手动修复")
    
    print(f"完成时间: {__import__('datetime').datetime.now()}")

if __name__ == "__main__":
    main()