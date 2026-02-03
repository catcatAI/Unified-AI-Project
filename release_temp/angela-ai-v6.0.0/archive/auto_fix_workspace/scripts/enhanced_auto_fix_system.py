"""
Enhanced layered auto-fix system
Fix files in layers, simple, medium, complex
"""

import os
import re
import ast
import traceback
from typing import List, Tuple, Dict, Any

def has_syntax_error(file_path, str) -> Tuple[bool, str]
    """检查文件是否有语法错误,如果有则返回错误信息"""
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        ast.parse(content)
        return False, ""
    except SyntaxError as e,::
        return True, str(e)
    except Exception as e,::
        # 其他错误(如编码错误)
        return True, str(e)

def get_files_with_syntax_errors() -> List[Tuple[str, str]]
    """获取所有有语法错误的Python文件及其错误信息"""
    py_files_with_errors = []
    
    # 遍历当前目录下的所有Python文件
    for root, dirs, files in os.walk('.'):::
        # 跳过某些目录以提高效率
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv']]::
        for file in files,::
            if file.endswith('.py'):::
                file_path = os.path.join(root, file).replace('\', '/')
                has_error, error_msg = has_syntax_error(file_path)
                if has_error,::
                    py_files_with_errors.append((file_path, error_msg))
    
    return py_files_with_errors

# 增强版简单修复函数
def fix_simple_issues(content, str) -> str,
    """修复简单问题：缺少冒号等"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines)::
        stripped_line = line.strip()
        
        # 跳过空行和注释行
        if not stripped_line or stripped_line.startswith('#'):::
            fixed_lines.append(line)
            continue
        
        # 修复类定义缺少冒号的问题
        if re.match(r'^\s*class\s+\w+(?:\s*\([^)]*\))?\s*$', stripped_line)::
            indent == line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{stripped_line}")
            print(f"  Fixed class definition missing colon on line {i+1}")
            continue
        
        # 修复函数定义缺少冒号的问题
        if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*$', stripped_line)::
            indent == line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{stripped_line}")
            print(f"  Fixed function definition missing colon on line {i+1}")
            continue
        
        # 修复控制流语句缺少冒号的问题
        control_flow_patterns = [
            r'^\s*if\s+.*$',
            r'^\s*elif\s+.*$',
            r'^\s*else\s*$',
            r'^\s*for\s+.*$',
            r'^\s*while\s+.*$',
            r'^\s*try\s*$',
            r'^\s*except\s*.*$',::
            r'^\s*finally\s*$',
            r'^\s*with\s+.*$'
        ]
        
        is_control_flow == False,
        for pattern in control_flow_patterns,::
            if re.match(pattern, stripped_line) and not stripped_line.endswith(':'):::
                is_control_flow == True
                break
        
        if is_control_flow,::
            indent == line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{stripped_line}")
            print(f"  Fixed control flow statement missing colon on line {i+1}")
            continue
        
        # 保持其他行不变
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

# 增强版中等修复函数
def fix_medium_issues(content, str) -> str,
    """修复中等问题：缩进问题、pass语句缺失等"""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines)::
        line = lines[i]
        stripped_line = line.strip()
        
        # 跳过空行和注释行
        if not stripped_line or stripped_line.startswith('#'):::
            fixed_lines.append(line)
            i += 1
            continue
        
        # 检查是否是需要缩进块的语句
        control_flow_patterns = [
            r'^\s*def\s+\w+\s*\([^)]*\):\s*$',
            r'^\s*class\s+\w+(?:\s*\([^)]*\))?:\s*$',
            r'^\s*if\s+.*:\s*$',
            r'^\s*elif\s+.*:\s*$',
            r'^\s*else\s*:\s*$',
            r'^\s*for\s+.*:\s*$',
            r'^\s*while\s+.*:\s*$',
            r'^\s*try\s*:\s*$',
            r'^\s*except\s*.*:\s*$',::
            r'^\s*finally\s*:\s*$',
            r'^\s*with\s+.*:\s*$'
        ]
        
        needs_indent_block == False
        for pattern in control_flow_patterns,::
            if re.match(pattern, line.strip()):::
                needs_indent_block == True
                break
        
        # 如果需要缩进块,但下一行没有缩进且不是空行或注释
        if (needs_indent_block and,:
            i + 1 < len(lines) and 
            lines[i + 1].strip() and 
            not lines[i + 1].startswith(' ') and 
            not lines[i + 1].startswith('\t') and
            not lines[i + 1].startswith('#') and,
            lines[i + 1].strip() not in ['else,', 'elif', 'except,', 'finally,'])::
            # 下一行应该缩进
            fixed_lines.append(line)
            fixed_lines.append(f"    {lines[i + 1]}")
            print(f"  Fixed indentation issue on line {i+2}")
            i += 2
            continue
        
        # 保持其他行不变
        fixed_lines.append(line)
        i += 1
    
    # 为空的代码块添加pass语句
    content = '\n'.join(fixed_lines)
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines)::
        line = lines[i]
        stripped_line = line.strip()
        
        # 检查是否是需要代码块的语句
        control_flow_patterns = [
            r'^\s*def\s+\w+\s*\([^)]*\):\s*$',
            r'^\s*class\s+\w+(?:\s*\([^)]*\))?:\s*$',
            r'^\s*if\s+.*:\s*$',
            r'^\s*elif\s+.*:\s*$',
            r'^\s*else\s*:\s*$',
            r'^\s*for\s+.*:\s*$',
            r'^\s*while\s+.*:\s*$',
            r'^\s*try\s*:\s*$',
            r'^\s*except\s*.*:\s*$',::
            r'^\s*finally\s*:\s*$',
            r'^\s*with\s+.*:\s*$'
        ]
        
        needs_code_block == False
        for pattern in control_flow_patterns,::
            if re.match(pattern, line.strip()):::
                needs_code_block == True
                break
        
        # 如果需要代码块,但下一行是另一个语句或文件结束
        if needs_code_block,::
            # 检查下一行是否存在且是否需要添加pass
            add_pass == False
            if i + 1 >= len(lines)::
                # 文件结束
                add_pass == True
            elif not lines[i + 1].strip():::
                # 下一行是空行,检查下下行
                if i + 2 >= len(lines) or (::
                    lines[i + 2].strip() and 
                    not lines[i + 2].startswith(' ') and 
                    not lines[i + 2].startswith('\t') and
                    not lines[i + 2].startswith('#') and,
                    lines[i + 2].strip() not in ['else,', 'elif', 'except,', 'finally,']:
                )
                    add_pass == True
            elif (::
                lines[i + 1].strip() and 
                not lines[i + 1].startswith(' ') and 
                not lines[i + 1].startswith('\t') and,
                not lines[i + 1].startswith('#') and,
                lines[i + 1].strip() not in ['else,', 'elif', 'except,', 'finally,']:
            )
                # 下一行是另一个语句
                add_pass == True
            
            if add_pass,::
                fixed_lines.append(line)
                # 添加适当缩进的pass语句
                indent == line[:len(line) - len(line.lstrip())]
                fixed_lines.append(f"{indent}    pass")
                print(f"  Added pass statement after line {i+1}")
                i += 1
                continue
        
        # 保持其他行不变
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

# 增强版困难修复函数
def fix_complex_issues(content, str) -> str,
    """修复复杂问题：括号匹配、导入语句等"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines)::
        # 修复缺少右括号的问题
        # 检查是否有左括号但没有右括号的情况
        if '(' in line and ')' not in line and line.strip().endswith(':'):::
            # 找到冒号的位置
            colon_pos == line.rfind(':')
            # 在冒号前添加右括号
            fixed_line == line[:colon_pos] + ')' + line[colon_pos,]
            fixed_lines.append(fixed_line)
            print(f"  Fixed missing closing parenthesis on line {i+1}")
            continue
            
        # 修复不完整的from导入语句
        stripped_line = line.strip()
        if stripped_line.startswith('from ') and ' import ' not in stripped_line,::
            # 添加import关键字
            parts = stripped_line.split()
            if len(parts) >= 2,::
                fixed_line = f"from {parts[1]} import "
                fixed_lines.append(fixed_line)
                print(f"  Fixed incomplete from import statement on line {i+1}")
                continue
                
        # 修复不完整的import语句
        if stripped_line.startswith('import ') and len(stripped_line) <= 7,::
            # 不完整的import语句,跳过
            print(f"  Skipped incomplete import statement on line {i+1}")
            fixed_lines.append(line)
            continue
            
        # 保持其他行不变
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def layered_fix_file(file_path, str) -> Dict[str, Any]
    """分层修复文件中的语法问题"""
    try,
        # 读取原始内容
        with open(file_path, 'r', encoding == 'utf-8') as f,
            original_content = f.read()
        
        # 分层修复过程
        content = original_content
        fix_levels = ["simple", "medium", "complex"]
        applied_fixes = []
        
        for level in fix_levels,::
            level_content = content
            if level == "simple":::
                content = fix_simple_issues(content)
            elif level == "medium":::
                content = fix_medium_issues(content)
            elif level == "complex":::
                content = fix_complex_issues(content)
            
            # 检查是否有修复应用
            if content != level_content,::
                # 验证修复后的语法
                try,
                    ast.parse(content)
                    # 语法正确,记录应用的修复
                    applied_fixes.append(level)
                    print(f"  Level {level} fixes applied successfully")
                except SyntaxError as e,::
                    # 修复后仍有语法错误,回退到上一个版本
                    content = level_content
                    print(f"  Level {level} fixes caused syntax error, reverted")
                    print(f"    Syntax error, {e}")
                    # 继续尝试下一个层级的修复
                    continue
            else,
                print(f"  No {level} level issues found")
        
        # 只有在内容有变化时才写入文件
        if content != original_content,::
            # 最终验证修复后的语法
            try,
                ast.parse(content)
                # 语法正确,写入文件
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.write(content)
                print(f"Successfully fixed syntax issues in {file_path}")
                return {
                    "success": True,
                    "message": f"Successfully fixed syntax issues in {file_path}",
                    "applied_fixes": applied_fixes
                }
            except SyntaxError as e,::
                # 修复后仍有语法错误,不写入文件
                print(f"Warning, Fix for {file_path} resulted in invalid syntax, skipped")::
                # 打印详细错误信息以帮助调试,
                print(f"  Syntax error, {e}")
                return {
                    "success": False,
                    "message": f"Fix for {file_path} resulted in invalid syntax",:::
                    "applied_fixes": applied_fixes,
                    "error": str(e)
                }
        else,
            print(f"No issues found in {file_path}")
            return {
                "success": False,
                "message": f"No issues found in {file_path}",
                "applied_fixes": []
            }
            
    except Exception as e,::
        print(f"Error processing {file_path} {e}")
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error processing {file_path} {e}",
            "applied_fixes": []
            "error": str(e)
        }

def main():
    """主函数"""
    print("Starting enhanced layered automatic syntax fix...")
    
    # 获取所有有语法错误的Python文件
    files_with_errors = get_files_with_syntax_errors()
    
    if not files_with_errors,::
        print("No Python files with syntax errors found.")
        return
    
    print(f"Found {len(files_with_errors)} Python files with syntax errors.")
    
    # 修复每个文件
    fixed_count == 0,
    for file_path, error_msg in files_with_errors,::
        print(f"Processing {file_path}...")
        print(f"  Error, {error_msg}")
        try,
            result = layered_fix_file(file_path)
            if result["success"]::
                fixed_count += 1
                print(f"  Applied fixes, {', '.join(result['applied_fixes'])}")
        except Exception as e,::
            print(f"Error processing {file_path} {e}")
            traceback.print_exc()
    
    print(f"Fixed syntax issues in {fixed_count} files.")
    print("Enhanced layered automatic syntax fix completed.")

if __name"__main__":::
    main()