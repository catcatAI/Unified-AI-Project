"""
BaseAgent文件修复脚本 - 修复文件末尾语法错误
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.append(str(project_root / "apps" / "backend" / "src"))

# 读取文件内容
agents_base_agent = project_root / "apps" / "backend" / "src" / "agents" / "base_agent.py"

try:
    with open(agents_base_agent, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"文件总行数: {len(lines)}")
    
    # 检查文件末尾
    print("文件末尾内容:")
    for i in range(len(lines)-10, len(lines)):
        if i >= 0:
            print(f"  {i+1:3d}: {repr(lines[i])}")
    
    # 检查是否有未闭合的括号或引号
    content = ''.join(lines)
    
    # 检查括号匹配
    stack = []
    for i, char in enumerate(content):
        if char == '(':
            stack.append(('(', i))
        elif char == ')':
            if stack and stack[-1][0] == '(':
                stack.pop()
            else:
                stack.append((')', i))
        elif char == '[':
            stack.append(('[', i))
        elif char == ']':
            if stack and stack[-1][0] == '[':
                stack.pop()
            else:
                stack.append((']', i))
        elif char == '{':
            stack.append(('{', i))
        elif char == '}':
            if stack and stack[-1][0] == '{':
                stack.pop()
            else:
                stack.append(('}', i))
    
    if stack:
        print(f"\n未闭合的括号:")
        for bracket, pos in stack:
            print(f"  位置 {pos}: '{bracket}'")
    
    # 检查引号匹配
    quote_stack = []
    i = 0
    while i < len(content):
        if content[i] == '"' and (i == 0 or content[i-1] != '\\'):
            if quote_stack and quote_stack[-1] == '"':
                quote_stack.pop()
            else:
                quote_stack.append('"')
        elif content[i] == "'" and (i == 0 or content[i-1] != '\\'):
            if quote_stack and quote_stack[-1] == "'":
                quote_stack.pop()
            else:
                quote_stack.append("'")
        i += 1
    
    if quote_stack:
        print(f"\n未闭合的引号:")
        for quote in quote_stack:
            print(f"  '{quote}'")
    
    # 检查docstring是否正确闭合
    # 查找所有三引号的位置
    triple_quotes = []
    for i in range(len(content) - 2):
        if content[i:i+3] == '"""':
            triple_quotes.append(i)
    
    print(f"\n三引号位置: {triple_quotes}")
    print(f"三引号数量: {len(triple_quotes)}")
    
    if len(triple_quotes) % 2 != 0:
        print("❌ 三引号数量不匹配")
        # 找到未闭合的三引号
        print("未闭合的三引号在文件末尾")
        
        # 在文件末尾添加闭合的三引号
        lines.append('        """\n')
        lines.append('    }\n')
        lines.append('}\n')
        
        # 写回文件
        with open(agents_base_agent, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ 已在文件末尾添加闭合的三引号和括号")
    else:
        print("✅ 三引号数量匹配")
        
except Exception as e:
    print(f"❌ 处理文件时出错: {e}")
    import traceback
    traceback.print_exc()