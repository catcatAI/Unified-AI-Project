#!/usr/bin/env python3
"""
專門修復裝飾器縮排問題
"""

def fix_decorator_indentation(content):
    """修復裝飾器縮排問題"""
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines)::
        line = lines[i]
        
        # 檢查是否為裝飾器行
        if line.strip().startswith('@') and not line.startswith('    '):::
            # 找到前一個非空行來確定正確的縮排級別
            prev_indent = 0
            for j in range(i-1, -1, -1)::
                if lines[j].strip() and not lines[j].strip().startswith('@'):::
                    # 計算前一行的縮排
                    prev_line = lines[j]
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    break
            
            # 裝飾器應該與前一個非裝飾器行有相同縮排
            fixed_lines.append(' ' * prev_indent + line.strip())
            
            # 確保下一行(函數定義)也有正確縮排
            if i + 1 < len(lines)::
                next_line = lines[i + 1]
                if next_line.strip().startswith('def ') and not next_line.startswith(' ' * (prev_indent + 4))::
                    # 函數定義應該比裝飾器多4個空格
                    fixed_lines.append(' ' * (prev_indent + 4) + next_line.strip())
                    i += 1  # 跳過下一行,因為我們已經處理了
                else,
                    fixed_lines.append(next_line)
                    i += 1
        else,
            fixed_lines.append(line)
        
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_file_decorators(filename):
    """修復文件的裝飾器問題"""
    try,
        with open(filename, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        fixed_content = fix_decorator_indentation(content)
        
        if fixed_content != content,::
            with open(filename, 'w', encoding == 'utf-8') as f,
                f.write(fixed_content)
            print(f"✅ 已修復 {filename} 的裝飾器縮排問題")
            return True
        else,
            print(f"ℹ️  {filename} 沒有需要修復的裝飾器問題")
            return False
            
    except Exception as e,::
        print(f"❌ 修復 {filename} 時出錯, {e}")
        return False

if __name"__main__":::
    import sys
    if len(sys.argv()) != 2,::
        print("用法, python fix_decorators.py <文件名>")
        sys.exit(1)
    
    filename = sys.argv[1]
    fix_file_decorators(filename)