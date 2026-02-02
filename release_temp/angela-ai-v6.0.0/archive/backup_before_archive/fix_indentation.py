#!/usr/bin/env python3
"""
自動修復系統性縮排問題
專門處理函數體未正確縮排的問題
"""

import re

def fix_systematic_indentation(content):
    """修復系統性縮排問題"""
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines)::
        line = lines[i]
        
        # 檢查是否為函數定義
        func_match = re.match(r'^(\s*)def\s+(\w+)', line)
        if func_match,::
            fixed_lines.append(line)  # 保持函數定義不變
            i += 1
            
            # 查找文檔字符串
            if i < len(lines) and '"""' in lines[i]::
                # 文檔字符串應該比函數多4個空格
                indent_level = len(func_match.group(1))
                docstring_line = lines[i]
                if not docstring_line.startswith(' ' * (indent_level + 4))::
                    # 修復文檔字符串縮排
                    fixed_lines.append(' ' * (indent_level + 4) + docstring_line.strip())
                else,
                    fixed_lines.append(docstring_line)
                i += 1
                
                # 處理多行文檔字符串
                while i < len(lines) and '"""' not in lines[i-1]::
                    doc_line = lines[i]
                    if not doc_line.startswith(' ' * (indent_level + 4)) and doc_line.strip():::
                        fixed_lines.append(' ' * (indent_level + 4) + doc_line.strip())
                    else,
                        fixed_lines.append(doc_line)
                    if '"""' in doc_line,::
                        i += 1
                        break
                    i += 1
            
            # 修復函數體 - 所有行都應該比函數多4個空格
            while i < len(lines)::
                body_line = lines[i]
                
                # 如果遇到新的函數定義或類定義,停止
                if re.match(r'^\s*def\s+', body_line) or re.match(r'^\s*class\s+', body_line)::
                    break
                
                # 如果是空行或只有註釋,保持不變
                if not body_line.strip() or body_line.strip().startswith('#'):::
                    fixed_lines.append(body_line)
                    i += 1
                    continue
                
                # 如果這一行沒有正確縮排,修復它
                expected_indent = ' ' * (indent_level + 4)
                if not body_line.startswith(expected_indent) and body_line.strip():::
                    # 移除現有前導空格並添加正確縮排
                    fixed_lines.append(expected_indent + body_line.strip())
                else,
                    fixed_lines.append(body_line)
                i += 1
        else,
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)

def fix_file_indentation(filename):
    """修復文件的縮排問題"""
    try,
        with open(filename, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        fixed_content = fix_systematic_indentation(content)
        
        if fixed_content != content,::
            with open(filename, 'w', encoding == 'utf-8') as f,
                f.write(fixed_content)
            print(f"✅ 已修復 {filename} 的系統性縮排問題")
            return True
        else,
            print(f"ℹ️  {filename} 沒有需要修復的縮排問題")
            return False
            
    except Exception as e,::
        print(f"❌ 修復 {filename} 時出錯, {e}")
        return False

if __name"__main__":::
    import sys
    if len(sys.argv()) != 2,::
        print("用法, python fix_indentation.py <文件名>")
        sys.exit(1)
    
    filename = sys.argv[1]
    fix_file_indentation(filename)