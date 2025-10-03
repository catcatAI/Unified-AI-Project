"""
Custom fix script for test_real_syntax_errors.py
"""

import os
import re
import ast
import traceback

def fix_test_file():
    """修复test_real_syntax_errors.py文件中的语法错误"""
    file_path = "./test_real_syntax_errors.py"
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"Processing {file_path}...")
        
        # 按行分割内容
        lines = content.split('\n')
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped_line = line.strip()
            
            # 跳过空行和注释行
            if not stripped_line or stripped_line.startswith('#'):
                fixed_lines.append(line)
                i += 1
                continue
            
            # 修复缺少冒号的问题
            if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*$', stripped_line):
                indent = line[:len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}{stripped_line}:")
                print(f"  Fixed function definition missing colon on line {i+1}")
                i += 1
                continue
                
            if re.match(r'^\s*class\s+\w+(?:\s*\([^)]*\))?\s*$', stripped_line):
                indent = line[:len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}{stripped_line}:")
                print(f"  Fixed class definition missing colon on line {i+1}")
                i += 1
                continue
                
            if re.match(r'^\s*if\s+.*$', stripped_line) and not stripped_line.endswith(':'):
                indent = line[:len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}{stripped_line}:")
                print(f"  Fixed if statement missing colon on line {i+1}")
                i += 1
                continue
                
            if re.match(r'^\s*for\s+.*$', stripped_line) and not stripped_line.endswith(':'):
                indent = line[:len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}{stripped_line}:")
                print(f"  Fixed for statement missing colon on line {i+1}")
                i += 1
                continue
            
            # 处理缩进问题
            # 检查是否是需要缩进块的语句
            control_flow_patterns = [
                r'^\s*def\s+\w+\s*\([^)]*\):\s*$',
                r'^\s*class\s+\w+(?:\s*\([^)]*\))?:\s*$',
                r'^\s*if\s+.*:\s*$',
                r'^\s*for\s+.*:\s*$'
            ]
            
            needs_indent_block = False
            for pattern in control_flow_patterns:
                if re.match(pattern, line.strip()):
                    needs_indent_block = True
                    break
            
            # 如果需要缩进块，但下一行没有缩进且不是空行或注释
            if (needs_indent_block and 
                i + 1 < len(lines) and 
                lines[i + 1].strip() and 
                not lines[i + 1].startswith(' ') and 
                not lines[i + 1].startswith('\t') and
                not lines[i + 1].startswith('#')):
                # 下一行应该缩进
                fixed_lines.append(line)
                fixed_lines.append(f"    {lines[i + 1]}")
                print(f"  Fixed indentation issue on line {i+2}")
                i += 2
                continue
            
            # 处理空函数定义
            if re.match(r'^\s*def\s+\w+\s*\([^)]*\):\s*$', line.strip()):
                # 检查下一行是否存在且是否需要添加pass
                add_pass = False
                if i + 1 >= len(lines):
                    # 文件结束
                    add_pass = True
                elif not lines[i + 1].strip():
                    # 下一行是空行，检查下下行
                    if i + 2 >= len(lines) or (
                        lines[i + 2].strip() and 
                        not lines[i + 2].startswith(' ') and 
                        not lines[i + 2].startswith('\t') and
                        not lines[i + 2].startswith('#')):
                        add_pass = True
                elif (
                    lines[i + 1].strip() and 
                    not lines[i + 1].startswith(' ') and 
                    not lines[i + 1].startswith('\t') and
                    not lines[i + 1].startswith('#')):
                    # 下一行是另一个语句
                    add_pass = True
                
                if add_pass:
                    fixed_lines.append(line)
                    indent = line[:len(line) - len(line.lstrip())]
                    fixed_lines.append(f"{indent}    pass")
                    print(f"  Added pass statement after line {i+1}")
                    i += 1
                    continue
            
            # 保持其他行不变
            fixed_lines.append(line)
            i += 1
        
        # 重新组合内容
        fixed_content = '\n'.join(fixed_lines)
        
        # 验证修复后的语法
        try:
            ast.parse(fixed_content)
            # 语法正确，写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Successfully fixed syntax issues in {file_path}")
            return True
        except SyntaxError as e:
            print(f"Failed to fix syntax issues in {file_path}")
            print(f"Syntax error: {e}")
            
            # 即使有语法错误，我们也尝试写入修复后的内容，以便手动检查
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"Fixed content written to {file_path} for manual inspection")
            except Exception as write_error:
                print(f"Failed to write fixed content: {write_error}")
            
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("Starting custom fix for test_real_syntax_errors.py...")
    
    if fix_test_file():
        print("Custom fix completed successfully.")
    else:
        print("Custom fix completed with syntax errors. Please check the file manually.")

if __name__ == "__main__":
    main()