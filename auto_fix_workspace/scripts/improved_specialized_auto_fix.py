import os
import re
import ast
import traceback
from typing import List, Tuple

def has_syntax_error(file_path: str) -> Tuple[bool, str]:
    """检查文件是否有语法错误，如果有则返回错误信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return False, ""
    except SyntaxError as e:
        return True, str(e)
    except Exception as e:
        # 其他错误（如编码错误）
        return True, str(e)

def get_files_with_syntax_errors() -> List[Tuple[str, str]]:
    """获取所有有语法错误的Python文件及其错误信息"""
    py_files_with_errors = []
    
    # 遍历当前目录下的所有Python文件
    for root, dirs, files in os.walk('.'):
        # 跳过某些目录以提高效率
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file).replace('\\', '/')
                has_error, error_msg = has_syntax_error(file_path)
                if has_error:
                    py_files_with_errors.append((file_path, error_msg))
    
    return py_files_with_errors

def fix_missing_colons_only(content: str) -> str:
    """只修复缺少冒号的问题，不处理其他问题"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        # 跳过空行和注释行
        if not stripped_line or stripped_line.startswith('#'):
            fixed_lines.append(line)
            continue
        
        # 修复类定义缺少冒号的问题
        if re.match(r'^\s*class\s+\w+(?:\s*\([^)]*\))?\s*$', stripped_line):
            # 确保整行只有类定义，没有其他内容
            indent = line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{stripped_line}:")
            print(f"  Fixed class definition missing colon on line {i+1}")
            continue
        
        # 修复函数定义缺少冒号的问题
        if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*$', stripped_line):
            # 确保整行只有函数定义，没有其他内容
            indent = line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{stripped_line}:")
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
            r'^\s*except\s*.*$',
            r'^\s*finally\s*$',
            r'^\s*with\s+.*$'
        ]
        
        is_control_flow = False
        for pattern in control_flow_patterns:
            if re.match(pattern, stripped_line) and not stripped_line.endswith(':'):
                is_control_flow = True
                break
        
        if is_control_flow:
            indent = line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f"{indent}{stripped_line}:")
            print(f"  Fixed control flow statement missing colon on line {i+1}")
            continue
        
        # 保持其他行不变
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_bracket_issues_for_colon_fix(content: str) -> str:
    """为修复冒号问题而修复括号不匹配问题"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # 修复缺少右括号的问题（针对冒号修复）
        # 检查是否有左括号但没有右括号的情况，且行尾有冒号
        if ('(' in line and 
            ')' not in line and 
            ':' in line and
            re.match(r'^\s*(def|if|elif|for|while)\s+.*$', line.strip())):
            # 找到冒号的位置
            colon_pos = line.rfind(':')
            # 在冒号前添加右括号
            fixed_line = line[:colon_pos] + ')' + line[colon_pos:]
            fixed_lines.append(fixed_line)
            print(f"  Fixed missing closing parenthesis for colon fix on line {i+1}")
            continue
            
        # 保持其他行不变
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def improved_specialized_fix_file(file_path: str) -> bool:
    """改进的专门修复文件中的缺少冒号问题"""
    try:
        # 读取原始内容
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # 创建内容副本进行修改
        content = original_content
        
        # 为修复冒号问题而修复括号不匹配问题
        content = fix_bracket_issues_for_colon_fix(content)
        
        # 只修复缺少冒号的问题
        content = fix_missing_colons_only(content)
        
        # 只有在内容有变化时才写入文件
        if content != original_content:
            # 验证修复后的语法
            try:
                ast.parse(content)
                # 语法正确，写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Successfully fixed syntax issues in {file_path}")
                return True
            except SyntaxError as e:
                # 修复后仍有语法错误，不写入文件
                print(f"Warning: Fix for {file_path} resulted in invalid syntax, skipped")
                return False
        else:
            print(f"No issues found in {file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("Starting improved specialized automatic syntax fix...")
    
    # 获取所有有语法错误的Python文件
    files_with_errors = get_files_with_syntax_errors()
    
    if not files_with_errors:
        print("No Python files with syntax errors found.")
        return
    
    print(f"Found {len(files_with_errors)} Python files with syntax errors.")
    
    # 修复每个文件
    fixed_count = 0
    for file_path, error_msg in files_with_errors:
        # 只处理缺少冒号的错误
        if "expected ':'" in error_msg:
            print(f"Processing {file_path}...")
            print(f"  Error: {error_msg}")
            try:
                if improved_specialized_fix_file(file_path):
                    fixed_count += 1
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                traceback.print_exc()
    
    print(f"Fixed syntax issues in {fixed_count} files.")
    print("Improved specialized automatic syntax fix completed.")

if __name__ == "__main__":
    main()