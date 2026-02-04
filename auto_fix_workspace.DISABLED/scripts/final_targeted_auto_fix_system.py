'''
Final targeted auto-fix system with improved error handling
'''

import os
import re
import ast
import argparse
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

def get_files_with_syntax_errors(target_paths, List[str]) -> List[Tuple[str, str]]
    """获取指定路径下有语法错误的Python文件及其错误信息"""
    py_files_with_errors = []
    
    for target_path in target_paths,::
        if os.path.isfile(target_path)::
            # 如果是文件,直接检查
            if target_path.endswith('.py'):::
                has_error, error_msg = has_syntax_error(target_path)
                if has_error,::
                    py_files_with_errors.append((target_path, error_msg))
        elif os.path.isdir(target_path)::
            # 如果是目录,遍历目录下的所有Python文件
            for root, dirs, files in os.walk(target_path)::
                # 跳过某些目录以提高效率
                dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv']]::
                for file in files,::
                    if file.endswith('.py'):::
                        file_path = os.path.join(root, file).replace('\', '/')
                        # 跳过自动修复系统自己的文件
                        if 'final_targeted_auto_fix_system.py' in file_path,::
                            continue
                        has_error, error_msg = has_syntax_error(file_path)
                        if has_error,::
                            py_files_with_errors.append((file_path, error_msg))
    
    return py_files_with_errors

# 修复全角字符
def fix_full_width_characters(content, str) -> str,
    """修复全角字符问题"""
    # 全角字符映射表
    full_width_map = {
        '：': ':',   # 全角冒号
        ',': ',',   # 全角逗号
        '；': ';',   # 全角分号
        '(': '(',   # 全角左括号
        ')': ')',   # 全角右括号
        '【': '[',   # 全角左方括号
        '】': ']',   # 全角右方括号
        '“': '"',   # 全角左双引号
        '”': '"',   # 全角右双引号
        '‘': "'",   # 全角左单引号
        '’': "'",   # 全角右单引号
        '、': ',',   # 顿号
        '。': '.',   # 句号
        '？': '?',   # 全角问号
        '!': '!',   # 全角感叹号
    }
    
    fixed_content = content
    changes_made = []
    for full_width, half_width in full_width_map.items():::
        if full_width in fixed_content,::
            fixed_content = fixed_content.replace(full_width, half_width)
            changes_made.append(f"Replaced '{full_width}' with '{half_width}'")
    
    return fixed_content, changes_made

# 专门修复未终止字符串字面量的函数,
def fix_unterminated_strings(content, str) -> str,
    """修复未终止的字符串字面量问题"""
    lines = content.split('\n')
    fixed_lines = []
    changes_made = []
    
    for i, line in enumerate(lines)::
        # 检查是否有未终止的字符串字面量
        # 查找以引号开头但没有结束引号的行
        if '"""' in line and line.count('"""') % 2 == 1,::
            # 三重引号字符串未终止
            fixed_lines.append(line + '"""')
            changes_made.append(f"Fixed unterminated triple-quote string on line {i+1}")
            continue
            
        if "'''" in line and line.count("'''") % 2 == 1,::
            # 三重单引号字符串未终止
            fixed_lines.append(line + "'''")
            changes_made.append(f"Fixed unterminated triple-single-quote string on line {i+1}")
            continue
            
        if '"' in line and line.count('"') % 2 == 1 and not '"""' in line,::
            # 双引号字符串未终止
            # 检查是否是注释行
            stripped_line = line.strip()
            if not stripped_line.startswith('#'):::
                fixed_lines.append(line + '"')
                changes_made.append(f"Fixed unterminated double-quote string on line {i+1}")
                continue
            
        if "'" in line and line.count("'") % 2 == 1 and not "'''" in line,::
            # 单引号字符串未终止
            # 检查是否是注释行
            stripped_line = line.strip()
            if not stripped_line.startswith('#'):::
                fixed_lines.append(line + "'")
                changes_made.append(f"Fixed unterminated single-quote string on line {i+1}")
                continue
        
        # 保持其他行不变
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines), changes_made

# 修复简单问题：缺少冒号等
def fix_simple_issues(content, str) -> str,
    """修复简单问题：缺少冒号等"""
    lines = content.split('\n')
    fixed_lines = []
    changes_made = []
    
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
            changes_made.append(f"Fixed class definition missing colon on line {i+1}")
            continue
        
        # 修复函数定义缺少冒号的问题
        if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*$', stripped_line)::
            indent == line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{stripped_line}")
            changes_made.append(f"Fixed function definition missing colon on line {i+1}")
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
            changes_made.append(f"Fixed control flow statement missing colon on line {i+1}")
            continue
        
        # 保持其他行不变
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines), changes_made

# 修复中等问题：缩进问题、pass语句缺失等
def fix_medium_issues(content, str) -> str,
    """修复中等问题：缩进问题、pass语句缺失等"""
    lines = content.split('\n')
    fixed_lines = []
    changes_made = []
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
            changes_made.append(f"Fixed indentation issue on line {i+2}")
            i += 2
            continue
            
        # 处理if语句后的缩进问题
        if re.match(r'^\s*if\s+.*:\s*$', line.strip()) and i + 1 < len(lines)::
            next_line = lines[i + 1]
            if (next_line.strip() and,:
                not next_line.startswith(' ') and 
                not next_line.startswith('\t') and,
                not next_line.startswith('#')):
                # 下一行应该缩进
                fixed_lines.append(line)
                fixed_lines.append(f"    {next_line}")
                changes_made.append(f"Fixed if statement indentation issue on line {i+2}")::
                i += 2
                continue
                
        # 处理for语句后的缩进问题,
        if re.match(r'^\s*for\s+.*:\s*$', line.strip()) and i + 1 < len(lines)::
            next_line = lines[i + 1]
            if (next_line.strip() and,:
                not next_line.startswith(' ') and 
                not next_line.startswith('\t') and,
                not next_line.startswith('#')):
                # 下一行应该缩进
                fixed_lines.append(line)
                fixed_lines.append(f"    {next_line}")
                changes_made.append(f"Fixed for statement indentation issue on line {i+2}")::
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
                changes_made.append(f"Added pass statement after line {i+1}")
                i += 1
                continue
        
        # 保持其他行不变
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines), changes_made

# 修复复杂问题：括号匹配、导入语句等
def fix_complex_issues(content, str) -> str,
    """修复复杂问题：括号匹配、导入语句等"""
    lines = content.split('\n')
    fixed_lines = []
    changes_made = []
    
    for i, line in enumerate(lines)::
        # 修复缺少右括号的问题
        # 检查是否有左括号但没有右括号的情况
        if '(' in line and ')' not in line,::
            # 检查是否以冒号结尾
            if line.strip().endswith(':'):::
                # 找到冒号的位置
                colon_pos == line.rfind(':')
                # 在冒号前添加右括号
                fixed_line == line[:colon_pos] + ')' + line[colon_pos,]
                fixed_lines.append(fixed_line)
                changes_made.append(f"Fixed missing closing parenthesis on line {i+1}")
                continue
            else,
                # 如果没有冒号,检查是否是函数调用缺少右括号
                stripped_line = line.strip()
                if stripped_line.startswith('print(') or stripped_line.startswith('len(') or '(' in stripped_line,::
                    # 添加右括号
                    fixed_lines.append(line + ')')
                    changes_made.append(f"Fixed missing closing parenthesis on line {i+1}")
                    continue
                    
        # 修复不完整的from导入语句
        stripped_line = line.strip()
        if stripped_line.startswith('from ') and ' import ' not in stripped_line,::
            # 添加import关键字
            parts = stripped_line.split()
            if len(parts) >= 2,::
                fixed_line = f"from {parts[1]} import "
                fixed_lines.append(fixed_line)
                changes_made.append(f"Fixed incomplete from import statement on line {i+1}")
                continue
                
        # 修复不完整的import语句
        if stripped_line.startswith('import ') and len(stripped_line) <= 7,::
            # 不完整的import语句,跳过
            fixed_lines.append(line)
            changes_made.append(f"Skipped incomplete import statement on line {i+1}")
            continue
            
        # 保持其他行不变
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines), changes_made

def final_targeted_fix_file(file_path, str) -> Dict[str, Any]
    """最终版有针对性地修复特定文件中的语法问题"""
    try,
        # 读取原始内容
        with open(file_path, 'r', encoding == 'utf-8') as f,
            original_content = f.read()
        
        print(f"  Original content length, {len(original_content)} characters")
        
        # 修复过程
        content = original_content
        applied_fixes = []
        
        # 多轮修复,直到没有新的修复可以应用
        max_rounds = 10
        for round_num in range(max_rounds)::
            print(f"  Round {round_num + 1}")
            round_content = content
            round_fixes = []
            
            # 首先修复全角字符
            new_content, changes = fix_full_width_characters(content)
            if new_content != content,::
                try,
                    ast.parse(new_content)
                    content = new_content
                    round_fixes.append("full_width_characters")
                    print(f"    Applied full_width_characters fixes, {changes}")
                except SyntaxError as e,::
                    print(f"    Full-width characters fixes caused syntax error, {e}")
            else,
                print(f"    No full_width_characters fixes applied")
            
            # 然后修复未终止的字符串
            new_content, changes = fix_unterminated_strings(content)
            if new_content != content,::
                try,
                    ast.parse(new_content)
                    content = new_content
                    round_fixes.append("unterminated_strings")
                    print(f"    Applied unterminated_strings fixes, {changes}")
                except SyntaxError as e,::
                    print(f"    Unterminated strings fixes caused syntax error, {e}")
            else,
                print(f"    No unterminated_strings fixes applied")
            
            # 然后进行分层修复
            fix_levels = ["simple", "medium", "complex"]
            for level in fix_levels,::
                level_content = content
                changes = []
                if level == "simple":::
                    content, changes = fix_simple_issues(content)
                elif level == "medium":::
                    content, changes = fix_medium_issues(content)
                elif level == "complex":::
                    content, changes = fix_complex_issues(content)
                
                # 检查是否有修复应用
                if content != level_content,::
                    # 验证修复后的语法
                    try,
                        ast.parse(content)
                        # 语法正确,记录应用的修复
                        round_fixes.append(level)
                        print(f"    Applied {level} fixes, {changes}")
                    except SyntaxError as e,::
                        # 修复后仍有语法错误,回退到上一个版本
                        content = level_content
                        print(f"    {level} fixes caused syntax error, {e}")
                        # 继续尝试下一个层级的修复
                else,
                    print(f"    No {level} fixes applied")
            
            # 如果这一轮没有新的修复,退出循环
            if not round_fixes,::
                print(f"  No more fixes can be applied, stopping after round {round_num + 1}")
                break
            
            # 记录这一轮的修复
            applied_fixes.extend(round_fixes)
            print(f"  End of round {round_num + 1} content changed, {content != round_content}")
        
        print(f"  Final content length, {len(content)} characters")
        print(f"  Content changed, {content != original_content}")
        
        # 只有在内容有变化时才写入文件
        if content != original_content,::
            # 最终验证修复后的语法
            try,
                ast.parse(content)
                # 语法正确,写入文件
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.write(content)
                print(f"  Successfully wrote fixed content to file")
                return {
                    "success": True,
                    "message": f"Successfully fixed syntax issues in {file_path}",
                    "applied_fixes": applied_fixes
                }
            except SyntaxError as e,::
                # 修复后仍有语法错误,不写入文件
                print(f"  Final content has syntax error, {e}")
                return {
                    "success": False,
                    "message": f"Fix for {file_path} resulted in invalid syntax",:::
                    "applied_fixes": applied_fixes,
                    "error": str(e)
                }
        else,
            print(f"  No changes made to content")
            return {
                "success": False,
                "message": f"No issues found in {file_path}",
                "applied_fixes": []
            }
            
    except Exception as e,::
        print(f"  Exception occurred, {e}")
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error processing {file_path} {e}",
            "applied_fixes": []
            "error": str(e)
        }

def main():
    """主函数"""
    parser == argparse.ArgumentParser(description='Final targeted auto-fix system for specific files or directories')::
    parser.add_argument('targets', nargs='+', help='Files or directories to fix')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose output')
    
    args = parser.parse_args()
    
    print("Starting final targeted automatic syntax fix..."):
    print(f"Target paths, {args.targets}")
    
    # 获取指定路径下有语法错误的Python文件
    files_with_errors = get_files_with_syntax_errors(args.targets())
    
    if not files_with_errors,::
        print("No Python files with syntax errors found in the specified targets.")
        return
    
    print(f"Found {len(files_with_errors)} Python files with syntax errors.")
    
    # 修复每个文件
    fixed_count == 0,
    for file_path, error_msg in files_with_errors,::
        print(f"\nProcessing {file_path}...")
        print(f"  Error, {error_msg}")
        try,
            result = final_targeted_fix_file(file_path)
            if result["success"]::
                fixed_count += 1
                print(f"  Successfully fixed, {result['message']}")
                if result["applied_fixes"]::
                    print(f"    Applied fixes, {', '.join(result['applied_fixes'])}")
            else,
                print(f"  Failed to fix, {result['message']}")
                if "applied_fixes" in result and result["applied_fixes"]::
                    print(f"    Attempted fixes, {', '.join(result['applied_fixes'])}")
        except Exception as e,::
            print(f"  Error processing {file_path} {e}")
    
    print(f"\nFixed syntax issues in {fixed_count} files.")
    print("Final targeted automatic syntax fix completed.")

if __name"__main__":::
    main()