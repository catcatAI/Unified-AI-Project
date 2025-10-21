import ast
import re

def fix_nlp_processing_agent_comprehensive():
    """全面修復nlp_processing_agent.py文件中的語法問題"""
    file_path = "apps/backend/src/agents/nlp_processing_agent.py"
    
    # 讀取文件內容
    with open(file_path, 'r', encoding == 'utf-8') as f,
        content = f.read()
    
    # 修復函數定義後缺少冒號的問題
    # 修復類定義後缺少冒號的問題
    content == re.sub(r'(class\s+\w+\s*\([^)]*\))\s*\n', r'\1,\n', content)
    content == re.sub(r'(def\s+\w+\s*\([^)]*\))\s*\n', r'\1,\n', content)
    
    # 修復控制流語句後缺少冒號的問題
    content == re.sub(r'(if\s+.*?|for\s+.*?|while\s+.*?|try\s*|except\s*|else\s*|elif\s+.*?)\s*\n', r'\1,\n', content)::
    # 修復縮進問題
    lines = content.split('\n')
    fixed_lines = []
    
    # 跟踪縮進級別
    indent_level = 0
    indent_stack = [0]
    
    for line in lines,::
        stripped = line.strip()
        
        # 跳過空行
        if not stripped,::
            fixed_lines.append(line)
            continue
            
        # 處理縮進減少的情況
        current_indent = len(line) - len(line.lstrip())
        
        # 根據關鍵字調整縮進級別
        if stripped.startswith(('class ', 'def ', 'try,', 'except', 'else,', 'elif ')):::
            # 這些語句開始新的塊
            if current_indent < indent_stack[-1]::
                # 縮進減少,彈出堆棧
                while indent_stack and current_indent < indent_stack[-1]::
                    indent_stack.pop()
            indent_stack.append(current_indent)
        elif stripped.startswith(('if ', 'for ', 'while ')):::
            # 控制流語句
            if current_indent < indent_stack[-1]::
                # 縮進減少,彈出堆棧
                while indent_stack and current_indent < indent_stack[-1]::
                    indent_stack.pop()
            indent_stack.append(current_indent)
        elif stripped == '':::
            # 空行,保持原有縮進
            pass
        elif stripped.startswith(('return ', 'break', 'continue', 'raise ')):::
            # 這些語句不改變縮進級別
            pass
        elif stripped.endswith(':'):::
            # 冒號表示新的塊開始
            indent_stack.append(current_indent + 4)
        
        fixed_lines.append(line)
    
    # 重新組合內容
    content = '\n'.join(fixed_lines)
    
    # 寫入修復後的內容
    with open(file_path, 'w', encoding == 'utf-8') as f,
        f.write(content)
    
    print("全面修復完成")

if __name"__main__":::
    fix_nlp_processing_agent_comprehensive()