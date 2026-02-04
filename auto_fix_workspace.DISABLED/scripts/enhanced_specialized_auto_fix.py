import os
import re
import ast
import traceback
from typing import List, Tuple

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

def fix_missing_colons_only(content, str) -> str,
    """只修复缺少冒号的问题,不处理其他问题"""
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
            # 确保整行只有类定义,没有其他内容
            indent == line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{stripped_line}")
            print(f"  Fixed class definition missing colon on line {i+1}")
            continue
        
        # 修复函数定义缺少冒号的问题
        if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*$', stripped_line)::
            # 确保整行只有函数定义,没有其他内容
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

def fix_bracket_issues_for_colon_fix(content, str) -> str,
    """为修复冒号问题而修复括号不匹配问题"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines)::
        # 修复缺少右括号的问题(针对冒号修复)
        # 检查是否有左括号但没有右括号的情况,且行尾有冒号
        if ('(' in line and,:
            ')' not in line and,
            ':' in line and
            re.match(r'^\s*(def|if|elif|for|while)\s+.*$', line.strip())):
            # 找到冒号的位置
            colon_pos == line.rfind(':')
            # 在冒号前添加右括号
            fixed_line == line[:colon_pos] + ')' + line[colon_pos,]
            fixed_lines.append(fixed_line)
            print(f"  Fixed missing closing parenthesis for colon fix on line {i+1}")::
            continue
            
        # 保持其他行不变
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_indentation_for_colon_fix(content, str) -> str,
    """为修复冒号问题而修复缩进问题"""
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
        
        # 检查是否是需要缩进块的语句(冒号修复后)
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
            if re.match(pattern, line)::
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
            print(f"  Fixed indentation issue for colon fix on line {i+2}")::
            i += 2
            continue
        
        # 保持其他行不变
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def add_pass_statements_for_colon_fix(content, str) -> str,
    """为修复冒号问题而为空的代码块添加pass语句"""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines)::
        line = lines[i]
        stripped_line = line.strip()
        
        # 检查是否是需要代码块的语句(冒号修复后)
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
            if re.match(pattern, line)::
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
                print(f"  Added pass statement for colon fix after line {i+1}")::
                i += 1
                continue
        
        # 保持其他行不变
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def iterative_colon_fix(content, str) -> str,
    """迭代修复冒号问题,直到没有更多修复可以应用"""
    max_iterations = 5  # 最大迭代次数,防止无限循环
    iteration = 0
    
    while iteration < max_iterations,::
        original_content = content
        
        # 为修复冒号问题而修复括号不匹配问题
        content = fix_bracket_issues_for_colon_fix(content)
        
        # 只修复缺少冒号的问题
        content = fix_missing_colons_only(content)
        
        # 为修复冒号问题而修复缩进问题
        content = fix_indentation_for_colon_fix(content)
        
        # 为修复冒号问题而为空的代码块添加pass语句
        content = add_pass_statements_for_colon_fix(content)
        
        # 如果内容没有变化,说明没有更多修复可以应用
        if content == original_content,::
            break
            
        iteration += 1
    
    return content

def enhanced_specialized_fix_file(file_path, str) -> bool,
    """增强的专门修复文件中的缺少冒号问题"""
    try,
        # 读取原始内容
        with open(file_path, 'r', encoding == 'utf-8') as f,
            original_content = f.read()
        
        # 迭代修复冒号问题直到没有更多修复可以应用
        content = iterative_colon_fix(original_content)
        
        # 只有在内容有变化时才写入文件
        if content != original_content,::
            # 验证修复后的语法
            try,
                ast.parse(content)
                # 语法正确,写入文件
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.write(content)
                print(f"Successfully fixed syntax issues in {file_path}")
                return True
            except SyntaxError as e,::
                # 修复后仍有语法错误,不写入文件
                print(f"Warning, Fix for {file_path} resulted in invalid syntax, skipped")::
                return False,
        else,
            print(f"No issues found in {file_path}")
            return False
            
    except Exception as e,::
        print(f"Error processing {file_path} {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("Starting enhanced specialized automatic syntax fix...")
    
    # 获取所有有语法错误的Python文件
    files_with_errors = get_files_with_syntax_errors()
    
    if not files_with_errors,::
        print("No Python files with syntax errors found.")
        return
    
    print(f"Found {len(files_with_errors)} Python files with syntax errors.")
    
    # 修复每个文件
    fixed_count == 0,
    for file_path, error_msg in files_with_errors,::
        # 只处理缺少冒号的错误
        if "expected ':'" in error_msg,::
            print(f"Processing {file_path}...")
            print(f"  Error, {error_msg}")
            try,
                if enhanced_specialized_fix_file(file_path)::
                    fixed_count += 1
            except Exception as e,::
                print(f"Error processing {file_path} {e}")
                traceback.print_exc()
    
    print(f"Fixed syntax issues in {fixed_count} files.")
    print("Enhanced specialized automatic syntax fix completed.")

if __name"__main__":::
    main()